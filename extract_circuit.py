#!/usr/bin/env python3
"""Extract a real escape-response neural circuit from the FlyWire FAFB v783 connectome.

Downloads cell type annotations and synaptic connection data from the FlyWire
Codex public API, filters for the escape/locomotion circuit (LC4, LPLC2, Giant
Fiber, steering, grooming, walking neurons + strongest partners), signs
synapses by neurotransmitter type, and outputs a compact circuit.json.

Uses only Python stdlib -- no pip installs required.

Data source: FlyWire Codex FAFB v783
  https://codex.flywire.ai/api/download?dataset=fafb
License: CC-BY 4.0 (FlyWire Consortium)
"""

import urllib.request
import gzip
import csv
import json
import os
from collections import defaultdict
from io import TextIOWrapper

CODEX_BASE = "https://codex.flywire.ai/api/download_resource"
DATASET = "fafb"
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

CORE_TYPES = {
    "LC4":    "lc4",
    "LPLC2":  "lplc2",
    "DNp01":  "gf",
    "DNp02":  "escw",
    "DNp04":  "escw",
    "DNp11":  "escw",
    "DNp09":  "walk",
    "DNa01":  "steer",
    "DNa02":  "steer",
    "DNg11":  "groom",
    "MDN":    "mdn",
}

NT_SIGN = {
    "ACH":   1.0,
    "GLUT": -1.0,
    "GABA": -1.0,
    "DA":    1.0,
    "OCT":   1.0,
    "SER":   1.0,
    "":      1.0,
}

TOP_PARTNERS = 330


def fetch_csv(data_product):
    """Stream a gzipped CSV from Codex and yield rows as dicts."""
    url = f"{CODEX_BASE}?data_product={data_product}&dataset={DATASET}"
    print(f"  Downloading {data_product}...")
    req = urllib.request.Request(url, headers={"Accept-Encoding": "gzip"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        raw = resp.read()

    decompressed = gzip.decompress(raw).decode("utf-8")
    reader = csv.DictReader(decompressed.splitlines())
    return list(reader)


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("=== FlyWire Escape Circuit Extractor ===\n")

    print("[1/5] Downloading cell types...")
    cell_rows = fetch_csv("consolidated_cell_types")
    print(f"  {len(cell_rows):,} cell type annotations loaded.\n")

    print("[2/5] Identifying core circuit neurons...")
    core = {}
    type_of = {}
    for row in cell_rows:
        rid = row.get("root_id", "").strip()
        ptype = row.get("primary_type", "").strip()
        if not rid or not ptype:
            continue
        role = CORE_TYPES.get(ptype)
        if role:
            core[rid] = role
            type_of[rid] = ptype

    print(f"  Core neurons found: {len(core)}")
    for role in sorted(set(core.values())):
        count = sum(1 for v in core.values() if v == role)
        print(f"    {role}: {count}")
    print()

    print("[3/5] Downloading connections...")
    conn_rows = fetch_csv("connections_princeton")
    print(f"  {len(conn_rows):,} connections loaded.\n")

    print("[4/5] Selecting strongest partners...")
    partner_strength = defaultdict(int)
    strength_by_role = defaultdict(lambda: defaultdict(int))

    for row in conn_rows:
        pre = row.get("pre_root_id", "").strip()
        post = row.get("post_root_id", "").strip()
        syn = int(row.get("syn_count", "0"))
        pre_core = pre in core
        post_core = post in core

        if pre_core and not post_core:
            partner_strength[post] += syn
            strength_by_role[core[pre]][post] += syn
        elif post_core and not pre_core:
            partner_strength[pre] += syn
            strength_by_role[core[post]][pre] += syn

    ranked = sorted(partner_strength.items(), key=lambda x: -x[1])
    partners = {rid for rid, _ in ranked[:TOP_PARTNERS]}
    print(f"  Top {TOP_PARTNERS} partners selected (by total synapse count).\n")

    all_members = set(core.keys()) | partners
    member_list = sorted(all_members)
    member_idx = {rid: i for i, rid in enumerate(member_list)}

    print("[5/5] Building circuit graph...")
    edges = []
    nt_missing = 0
    for row in conn_rows:
        pre = row.get("pre_root_id", "").strip()
        post = row.get("post_root_id", "").strip()
        i = member_idx.get(pre)
        j = member_idx.get(post)
        if i is None or j is None:
            continue
        syn = int(row.get("syn_count", "0"))
        nt = row.get("nt_type", "").strip().upper()
        sign = NT_SIGN.get(nt)
        if sign is None:
            sign = 1.0
            nt_missing += 1
        edges.append([i, j, round(syn * sign, 1)])

    neurons = []
    for rid in member_list:
        role = core.get(rid, "partner")
        ntype = type_of.get(rid, "")

        x = hash(rid + "x") % 10000 / 10000.0
        y = hash(rid + "y") % 10000 / 10000.0
        z = hash(rid + "z") % 10000 / 10000.0

        if role == "lc4":
            x, y = 0.15 + x * 0.15, 0.2 + y * 0.2
        elif role == "lplc2":
            x, y = 0.15 + x * 0.15, 0.5 + y * 0.2
        elif role == "gf":
            x, y = 0.45 + x * 0.1, 0.4 + y * 0.2
        elif role in ("steer", "walk", "mdn", "escw", "groom"):
            x, y = 0.7 + x * 0.2, 0.2 + y * 0.6
        else:
            x, y = 0.3 + x * 0.4, 0.1 + y * 0.8

        neurons.append({
            "id": rid,
            "type": ntype,
            "role": role,
            "pos": [round(x, 4), round(y, 4), round(z, 4)],
        })

    circuit = {
        "source": "FlyWire Codex FAFB v783 (escape-response circuit)",
        "neuron_count": len(neurons),
        "edge_count": len(edges),
        "neurons": neurons,
        "edges": edges,
    }

    out_path = os.path.join(OUTPUT_DIR, "circuit.json")
    with open(out_path, "w") as f:
        json.dump(circuit, f)

    print(f"\n=== Done ===")
    print(f"  Neurons: {len(neurons)}")
    print(f"  Edges:   {len(edges)}")
    print(f"  NT predictions missing: {nt_missing}")
    print(f"  Output:  {out_path}")
    print(f"  Size:    {os.path.getsize(out_path) / 1024:.1f} KB")


if __name__ == "__main__":
    main()
