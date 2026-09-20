# FlyWire Escape Circuit Simulator

A browser-based neural circuit simulator powered by **real connectome data** from the [FlyWire](https://codex.flywire.ai/) project (FAFB v783).

Extracts the fruit fly's escape-response circuit — the same neurons a real fly uses to detect a looming predator and trigger an escape takeoff — and simulates it with a leaky integrate-and-fire model running at 1kHz in your browser.

## Quick Start

### 1. Extract the circuit (requires internet)

```bash
python3 extract_circuit.py
```

This downloads real cell type and connection data from the FlyWire Codex API, filters for the escape circuit (~400-700 neurons), and outputs `data/circuit.json`.

No pip installs needed — uses only Python standard library.

### 2. Open the simulator

```bash
# Any local server works:
python3 -m http.server 8000
# Then open http://localhost:8000
```

Or just open `index.html` in a browser (the simulator includes a fallback demo circuit if `circuit.json` isn't found).

## What's in the circuit?

| Neuron Type | Role | Count |
|---|---|---|
| LC4 | Looming detector (visual) | ~80-104 |
| LPLC2 | Looming detector (visual) | ~60-210 |
| DNp01 (Giant Fiber) | Escape command neuron | 2 |
| DNa01/DNa02 | Steering | 4 |
| DNp09 | Forward walking | 2 |
| DNg11 | Grooming | 6 |
| MDN | Backward walking | 4 |
| DNp02/04/11 | Escape wing maneuvers | 6 |
| Partners | Strongest connected neurons | ~330 |

All neuron identities, synaptic connections, synapse counts, and neurotransmitter predictions come from the FlyWire FAFB v783 dataset.

## How it works

- **Leaky Integrate-and-Fire (LIF)** model: each neuron has a membrane potential that leaks toward rest (-70mV), receives current from synaptic inputs, and fires a spike when it crosses threshold (-55mV).
- **Synapses are signed**: acetylcholine = excitatory (+), GABA/glutamate = inhibitory (-), based on FlyWire neurotransmitter predictions.
- **Click "Simulate Loom"** to inject current into the looming detectors. Watch the signal cascade through real synaptic pathways. When the Giant Fiber spikes — ESCAPE!

## Data Source

- **FlyWire Consortium**: Dorkenwald, S. et al. "Neuronal wiring diagram of an adult brain." *Nature* (2024). [DOI: 10.1038/s41586-024-07558-y](https://doi.org/10.1038/s41586-024-07558-y)
- Data accessed via [Codex](https://codex.flywire.ai/) under CC-BY 4.0.
- Inspired by [DesktopFly](https://github.com/DenisSergeevitch/desktop-fly) by Denis Shiryaev.

## License

Code: MIT. Connectome data: CC-BY 4.0 (FlyWire Consortium).
