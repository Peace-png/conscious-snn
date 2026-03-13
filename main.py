"""
Conscious SNN - Main Entry Point

A complete Brian2 architecture for human conscious processing.

Usage:
    python main.py --duration 10000 --scale 0.01

This will:
1. Build the network at all biological systems
2. Run simulation
3. Export spike data and influence matrix
4. Generate visualizations
"""

import argparse
from datetime import datetime
import numpy as np
import sys
import os

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from brian2 import ms, mV, Hz

from core import (
    ConsciousNetwork,
    ConsciousSNNConfig,
    ScaleParams,
    ComputeConfig
)
from core.neurons import AdaptiveExpLIF


def create_parser():
    parser = argparse.ArgumentParser(description='Run Conscious SNN')
    parser.add_argument('--duration', type=float, default=10000,
                        help='Simulation duration in ms')
    parser.add_argument('--scale', type=float, default=0.01,
                        help='Scale factor (0.01 = 1%% neurons)')
    parser.add_argument('--output', type=str, default='./output',
                        help='Output directory')
    parser.add_argument('--seed', type=int, default=42,
                        help='Random seed')
    parser.add_argument('--plot', action='store_true',
                        help='Generate plots')
    # Backend selection
    parser.add_argument('--backend', type=str, default='cpp_standalone',
                        choices=['cpp_standalone', 'cuda_standalone', 'genn', 'cython'],
                        help='Compute backend (default: cpp_standalone)')
    parser.add_argument('--threads', type=int, default=8,
                        help='OpenMP threads for cpp_standalone backend')
    return parser.parse_args()


def setup_compute(config: ComputeConfig):
    """Set up Brian2 compute backend.

    Based on RESEARCH_GPU_CPU_ACCELERATION.md:
    - C++ standalone with OpenMP: Recommended for CPU
    - CUDA standalone: NVIDIA GPU via Brian2CUDA
    - GeNN: NVIDIA GPU via Brian2GeNN
    - Cython: Runtime mode (slower, for development)
    """
    from brian2 import set_device, prefs

    backend = config.backend

    if backend == 'cpp_standalone':
        # C++ standalone with OpenMP multi-threading
        set_device('cpp_standalone',
                   directory=config.output_directory,
                   build_on_run=config.build_on_run)
        prefs.devices.cpp_standalone.openmp_threads = config.openmp_threads

        # Compiler optimizations
        prefs.codegen.cpp.extra_compile_args_gcc = config.extra_compile_args

        print(f"Backend: C++ standalone with {config.openmp_threads} OpenMP threads")

    elif backend == 'cuda_standalone':
        # NVIDIA GPU via Brian2CUDA
        try:
            import brian2cuda
            set_device('cuda_standalone',
                       directory=config.output_directory)
            print("Backend: CUDA standalone (NVIDIA GPU)")
        except ImportError:
            raise ImportError(
                "brian2cuda not installed. Install with: pip install brian2cuda"
            )

    elif backend == 'genn':
        # NVIDIA GPU via GeNN
        try:
            import brian2genn
            set_device('genn')
            print("Backend: GeNN (NVIDIA GPU)")
        except ImportError:
            raise ImportError(
                "brian2genn not installed. Install with: pip install brian2genn"
            )

    elif backend == 'cython':
        # Runtime mode with Cython (slower, for development)
        prefs.codegen.target = 'cython'
        print("Backend: Cython runtime (development mode)")

    return backend


def main():
    args = create_parser()

    print("=" * 60)
    print("CONSCIOUS SNN - Brian2 Architecture for Human Conscious Processing")
    print("=" * 60)
    print(f"\nScale: {args.scale * 100:.0%}")
    print(f"Duration: {args.duration}ms")
    print(f"Backend: {args.backend}")
    print(f"Output: {args.output}")
    print()

    # Create compute config
    compute_config = ComputeConfig(
        backend=args.backend,
        openmp_threads=args.threads,
        output_directory=args.output
    )

    # Setup backend BEFORE creating network
    setup_compute(compute_config)

    # Create config
    config = ConsciousSNNConfig(
        dt=0.1,
        duration=args.duration,
        seed=args.seed,
        output_dir=args.output,
        scale=ScaleParams(scale_factor=args.scale),
        compute=compute_config
    )

    # Build network
    print("Building network...")
    network = ConsciousNetwork(config)
    network.build()

    print(f"\nSystems created:")
    for name, system in network.systems.items():
        n = len(system.neuron_group)
        freq = system.oscillation_freq
        print(f"  {name}: {n} neurons, {freq} Hz oscillation")

    print("\nInter-system connectivity:")
    n_connections = len(network.influence_matrix._synapses)
    print(f"  {n_connections} connections between systems")

    # Run simulation
    print(f"\nRunning simulation for {args.duration}ms...")
    start = datetime.now()
    network.run()
    elapsed = (datetime.now() - start).total_seconds()
    print(f"\nSimulation completed in {elapsed:.2f}s")

    # Get stats
    print("\nSystem statistics:")
    stats = network.get_system_stats()
    for name, stat in stats.items():
        print(f"  {name}:")
        print(f"    Neurons: {stat['n_neurons']}")
        print(f"    Mean rate: {stat['mean_firing_rate']:.2f} Hz")
        print(f"    Target freq: {stat['oscillation_freq']} Hz")

    # Export data
    import os
    os.makedirs(args.output, exist_ok=True)

    spikes_file = network.export_spikes()
    print(f"\nExported spikes to: {spikes_file}")

    matrix_file = network.export_influence_matrix()
    print(f"Exported influence matrix to: {matrix_file}")

    # Generate plots
    if args.plot:
        print("\nGenerating visualizations...")
        generate_plots(network, args.output)

    print("\n" + "=" * 60)
    print("COMPLETE")
    print("=" * 60)


def generate_plots(network, output_dir):
    """Generate visualization plots."""
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib not installed - skipping plots")
        return

    # Raster plot
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    # Spike raster
    ax = axes[0, 0]
    for name, system in network.systems.items():
        t, i = system.get_spike_times()
        if t is not None:
            ax.scatter(t / ms, i, s=1, alpha=0.5, label=name)
    ax.set_xlabel('Time (ms)')
    ax.set_ylabel('Neuron ID')
    ax.set_title('Spike Raster Plot')
    ax.legend()

    # Firing rates
    ax = axes[0, 1]
    for name, system in network.systems.items():
        t, rate = system.get_firing_rate()
        if t is not None:
            ax.plot(t * 1000, rate, label=name, alpha=0.7)
    ax.set_xlabel('Time (s)')
    ax.set_ylabel('Firing Rate (Hz/neuron)')
    ax.set_title('Population Firing Rates')
    ax.legend()

    # Influence matrix
    ax = axes[1, 0]
    matrix = network.influence_matrix.export_matrix()
    im = ax.imshow(matrix, cmap='viridis', aspect='auto')
    ax.set_title('Inter-System Influence Matrix')
    ax.set_xticks(range(len(network.systems)))
    ax.set_yticks(range(len(network.systems)))
    ax.set_xticklabels(list(network.systems.keys()), rotation=45, ha='right')
    ax.set_yticklabels(list(network.systems.keys()))

    # Oscillation power spectrum
    ax = axes[1, 1]
    for name, system in network.systems.items():
        t, rate = system.get_firing_rate()
        if t is not None and len(rate) > 10:
            # Simple FFT
            dt = (t[1] - t[0])
            fft = np.abs(np.fft.fft(rate))[:len(rate)//2]
            freqs = np.fft.fftfreq(len(rate), dt)[:len(rate)//2]
            ax.plot(freqs, fft, label=name, alpha=0.7)
    ax.set_xlabel('Frequency (Hz)')
    ax.set_ylabel('Power')
    ax.set_title('Power Spectrum')
    ax.set_xlim(0, 100)
    ax.legend()

    plt.tight_layout()
    plt.savefig(f'{output_dir}/analysis.png', dpi=150)
    print(f"Saved plots to: {output_dir}/analysis.png")


if __name__ == '__main__':
    main()
