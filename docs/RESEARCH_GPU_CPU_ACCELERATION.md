# Brian2 GPU/CPU Acceleration Research

> Research for running Conscious SNN on GPU/CPU (transformer hardware)
> Compiled: 2026-03-13

## Overview

Brian2 has multiple backends for acceleration on GPU and multi-core CPU. This document covers the options for running the Conscious SNN architecture efficiently.

---

## Backend Options

### 1. C++ Standalone Mode (CPU, Recommended Default)

**Best for:** General use, reproducibility, large networks

```python
from brian2 import *
set_device('cpp_standalone', directory='output')
```

**Features:**
- Generates standalone C++ code
- Compiles to native binary
- **OpenMP multi-threading** available
- Eliminates Python overhead per timestep
- 10-100x speedup for complex synapses (STDP)

**OpenMP Configuration:**
```python
# Enable multi-threading (XX = number of threads)
prefs.devices.cpp_standalone.openmp_threads = 8
```

**Requirements:**
- C++ compiler (gcc/clang on Linux, MSVC on Windows)
- OpenMP support

### 2. Brian2CUDA (NVIDIA GPU)

**Best for:** Very large networks, NVIDIA GPU available

```python
from brian2 import *
import brian2cuda
set_device('cuda_standalone')
```

**Installation:**
```bash
pip install brian2cuda
```

**Features:**
- Generates CUDA code from Brian2 models
- Runs on NVIDIA GPUs
- Part of official Brian2 ecosystem
- Citation: Alevi et al. (2022) Frontiers in Neuroinformatics

**Requirements:**
- NVIDIA GPU with CUDA support
- CUDA toolkit installed
- Compatible CUDA version

**GitHub:** https://github.com/brian-team/brian2cuda

### 3. Brian2GeNN (NVIDIA GPU via GeNN)

**Best for:** Optimized GPU simulation, large networks

```python
from brian2 import *
import brian2genn
set_device('genn')
```

**Installation:**
```bash
pip install brian2genn
```

**Features:**
- Interface to GeNN (GPU enhanced Neural Networks)
- Optimized code generation for spiking models
- Good performance on complex neuron models

**Citation:** Stimberg et al. (2020) Scientific Reports

**GitHub:** https://github.com/brian-team/brian2genn

### 4. Cython Runtime (CPU, Default)

**Best for:** Development, debugging, smaller networks

```python
from brian2 import *
# Automatic - cython is default if available
prefs.codegen.target = 'cython'
```

**Features:**
- Compiles to Cython/C during runtime
- Caches compiled code
- Can combine with arbitrary Python code
- Python overhead per timestep remains

### 5. NumPy Fallback (CPU, Slowest)

**Best for:** When no compiler available

```python
prefs.codegen.target = 'numpy'
```

**Note:** Only use if no C++ compiler available. Much slower.

---

## Performance Comparison

| Backend | Hardware | Relative Speed | Use Case |
|---------|----------|----------------|----------|
| NumPy | CPU | 1x | Fallback only |
| Cython | CPU | 10-50x | Development |
| C++ Standalone | CPU | 50-200x | Production |
| C++ + OpenMP | Multi-core CPU | 100-500x | Large networks |
| Brian2CUDA | NVIDIA GPU | 200-1000x | Very large networks |
| Brian2GeNN | NVIDIA GPU | 200-1000x | Very large networks |

*Speedups depend heavily on network structure and simulation parameters*

---

## Recommended Configuration for Conscious SNN

### For CPU (Most Compatible)

```python
from brian2 import *

# Enable C++ standalone with OpenMP
set_device('cpp_standalone', directory='output')

# Multi-threading (adjust to your CPU)
prefs.devices.cpp_standalone.openmp_threads = 8

# Compiler optimizations
prefs.codegen.cpp.extra_compile_args_gcc = ['-O3', '-march=native', '-ffast-math']
```

### For NVIDIA GPU (Best Performance)

```python
from brian2 import *
import brian2cuda

# Enable CUDA backend
set_device('cuda_standalone', directory='output')
```

### For Development/Testing

```python
from brian2 import *

# Runtime mode with Cython (default)
prefs.codegen.target = 'cython'

# Smaller scale for testing
config.scale.scale_factor = 0.001  # 0.1% scale
```

---

## Memory Considerations

### Large Network Scaling

At 500M+ neurons, memory is the primary constraint:

| Scale | Neurons | Est. Memory | Backend |
|-------|---------|-------------|---------|
| 0.1% | 570K | ~1 GB | Any |
| 1% | 5.7M | ~10 GB | C++/GPU |
| 10% | 57M | ~100 GB | C++ + OpenMP |
| 100% | 570M | ~1 TB | GPU cluster |

### Memory Optimization Strategies

1. **Sparse Connectivity** - Already implemented (5-10% density)
2. **Reduced Precision** - Use float32 instead of float64
3. **Monitor Selection** - Only record necessary variables
4. **Chunked Simulation** - Run in segments, save intermediate results

---

## Multi-Run Simulations

For parameter sweeps and batch simulations:

```python
set_device('cpp_standalone', build_on_run=False)

# ... build network ...

run(100*ms)  # First run
device.build(run=False)  # Compile once

# Multiple runs without recompiling
for param in param_range:
    device.run(run_args={group.tau: param})
    # Process results
```

---

## Parallel Simulations

For running multiple independent simulations:

```python
import multiprocessing

class SimWrapper:
    def __init__(self):
        # Build network once
        set_device('cpp_standalone', build_on_run=False)
        # ... network definition ...
        run(100*ms)
        device.build(run=False)
        self.device = get_device()

    def do_run(self, result_dir):
        device.run(results_directory=result_dir)
        return results

if __name__ == '__main__':
    sim = SimWrapper()
    with multiprocessing.Pool() as p:
        results = p.map(sim.do_run, [f'result_{i}' for i in range(10)])
```

---

## Implementation in Conscious SNN

### config.py Additions

```python
class ComputeConfig:
    """Compute backend configuration."""

    backend: str = 'cpp_standalone'  # 'cpp_standalone', 'cuda_standalone', 'cython'
    openmp_threads: int = 8
    output_directory: str = 'output'
    build_on_run: bool = True

    # Compiler settings
    extra_compile_args: List[str] = field(default_factory=lambda: [
        '-O3', '-march=native', '-ffast-math'
    ])
```

### main.py Integration

```python
def setup_compute(config):
    """Set up compute backend."""
    from brian2 import set_device, prefs

    if config.compute.backend == 'cpp_standalone':
        set_device('cpp_standalone',
                   directory=config.compute.output_directory,
                   build_on_run=config.compute.build_on_run)
        prefs.devices.cpp_standalone.openmp_threads = config.compute.openmp_threads

    elif config.compute.backend == 'cuda_standalone':
        import brian2cuda
        set_device('cuda_standalone',
                   directory=config.compute.output_directory)

    elif config.compute.backend == 'cython':
        prefs.codegen.target = 'cython'
```

---

## Benchmarking Commands

```bash
# Test C++ standalone
python main.py --backend cpp_standalone --duration 10000 --scale 0.01

# Test with OpenMP
python main.py --backend cpp_standalone --threads 8 --duration 10000 --scale 0.01

# Test CUDA (if available)
python main.py --backend cuda_standalone --duration 10000 --scale 0.01
```

---

## Sources

1. Brian2 Computational Methods Documentation: https://brian2.readthedocs.io/en/stable/user/computation.html
2. Brian2CUDA GitHub: https://github.com/brian-team/brian2cuda
3. Brian2GeNN GitHub: https://github.com/brian-team/brian2genn
4. Alevi et al. (2022) "Brian2CUDA: flexible and efficient simulation of spiking neural network models on GPUs" Frontiers in Neuroinformatics
5. Stimberg et al. (2020) "Brian2GeNN: Accelerating Spiking Neural Network Simulations with Graphics Hardware" Scientific Reports

---

## Next Steps

1. [x] Add ComputeConfig to config.py
2. [x] Add backend selection to main.py CLI
3. [ ] Test C++ standalone with OpenMP
4. [ ] Benchmark at different scales
5. [ ] Document performance results
