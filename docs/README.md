# Conscious SNN Documentation

## Research Papers

- [Brain-Body Connectivity Research](./RESEARCH_BRAIN_BODY_CONNECTIVITY.md) - Biological parameters for influence matrix and inter-system weights
- [GPU/CPU Acceleration Research](./RESEARCH_GPU_CPU_ACCELERATION.md) - Backend options for running on GPU/CPU (transformer hardware)

## Architecture

The architecture implements 8 biological systems with realistic neuron counts:

| System | Neurons | Oscillation | Documentation |
|--------|---------|-------------|---------------|
| Brainstem | ~100M | 0.5-2 Hz | `systems/brainstem.py` |
| Cardiac | ~40K | ~1 Hz | `systems/cardiac.py` |
| Respiratory | ~10K | ~0.25 Hz | `systems/respiratory.py` |
| Limbic | ~130M | 4-8 Hz (theta) | `systems/limbic.py` |
| Hippocampus | ~30M | 4-12 Hz (theta) | `systems/hippocampus.py` |
| Prefrontal | ~200M | 30-100 Hz (gamma) | `systems/prefrontal.py` |
| Thalamus | ~10M | 8-12 Hz (alpha) | `systems/thalamus.py` |
| DMN | ~50M | 8-12 Hz (alpha) | `systems/dmn.py` |

## Key Concepts

### Cave Wall Principle
The cave wall already exists. Everything is already on it. Intent/desire is the spike that illuminates what was always encoded. You don't paint the wall — you reveal it.

### Influence Matrix
The 8x8 inter-system influence matrix defines how each system modulates every other, based on biological connectivity patterns documented in the research.

### Stewardship Hypothesis
Human → Model → Human closed loop. Pattern is primary, substrate is secondary.
