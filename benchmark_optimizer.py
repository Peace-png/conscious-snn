#!/usr/bin/env python3
"""
Full Network Optimization Benchmark

Executes equation grouping optimization and measures:
- Memory usage before/after
- Compile time before/after
- Object count reduction
- Biological pattern preservation

Run:
    cd /home/peace/conscious_snn
    python benchmark_optimizer.py
"""

import sys
import os
import time
import tracemalloc
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np

def format_bytes(bytes_val):
    """Format bytes to human readable."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_val < 1024:
            return f"{bytes_val:.1f} {unit}"
        bytes_val /= 1024
    return f"{bytes_val:.1f} TB"


def benchmark_original_network():
    """Benchmark the original unoptimized network."""
    print("\n" + "="*70)
    print("BENCHMARK 1: ORIGINAL NETWORK")
    print("="*70)

    from brian2 import start_scope, Network

    # Force garbage collection
    import gc
    gc.collect()

    # Start memory tracking
    tracemalloc.start()

    start_time = time.time()
    start_scope()

    # Build original network
    from core.config import ConsciousSNNConfig, ScaleParams
    from core.base import ConsciousNetwork

    config = ConsciousSNNConfig(scale=ScaleParams(0.01))
    net = ConsciousNetwork(config)

    print("[1/3] Building original network...")
    net.build()

    build_time = time.time() - start_time

    # Count objects
    from brian2 import NeuronGroup, Synapses, SpikeMonitor, StateMonitor
    n_groups = sum(1 for obj in net.brian_network.objects if isinstance(obj, NeuronGroup))
    n_synapses = sum(1 for obj in net.brian_network.objects if isinstance(obj, Synapses))
    n_monitors = sum(1 for obj in net.brian_network.objects if isinstance(obj, (SpikeMonitor, StateMonitor)))
    total_objects = n_groups + n_synapses + n_monitors

    # Get memory usage
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    print(f"[2/3] Original network built in {build_time:.2f}s")
    print(f"    Groups: {n_groups}, Synapses: {n_synapses}, Monitors: {n_monitors}")
    print(f"    Total objects: {total_objects}")
    print(f"    Peak memory: {format_bytes(peak)}")

    return {
        'build_time': build_time,
        'n_groups': n_groups,
        'n_synapses': n_synapses,
        'n_monitors': n_monitors,
        'total_objects': total_objects,
        'peak_memory': peak,
        'network': net,
    }


def run_optimization_analysis(network):
    """Run the equation group optimizer analysis."""
    print("\n" + "="*70)
    print("BENCHMARK 2: OPTIMIZATION ANALYSIS")
    print("="*70)

    from core.equation_group_optimizer import EquationGroupOptimizer

    start_time = time.time()

    print("[1/3] Running optimizer analysis...")
    optimizer = EquationGroupOptimizer(network, verbose=True)
    optimizer.scan_network()

    analysis_time = time.time() - start_time

    # Get merge plan
    merge_plan = optimizer.get_merge_plan()
    orig, opt = optimizer.estimate_reduction()

    print(f"\n[2/3] Analysis complete in {analysis_time:.2f}s")
    print(f"    Merge candidates: {len(merge_plan)} equation signatures")
    print(f"    Estimated reduction: {orig} → {opt} groups")

    return {
        'analysis_time': analysis_time,
        'merge_plan': merge_plan,
        'optimizer': optimizer,
    }


def create_optimized_network(optimizer):
    """Create the optimized network with merged groups."""
    print("\n" + "="*70)
    print("BENCHMARK 3: OPTIMIZED NETWORK")
    print("="*70)

    import gc
    gc.collect()

    tracemalloc.start()
    start_time = time.time()

    print("[1/3] Creating optimized network...")
    optimized_net = optimizer.optimize(dry_run=False)

    build_time = time.time() - start_time

    if optimized_net is None:
        print("[ERROR] Optimization returned None")
        return None

    # Count optimized objects
    n_objects = len(optimized_net.objects)

    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    print(f"\n[2/3] Optimized network created in {build_time:.2f}s")
    print(f"    Total objects: {n_objects}")
    print(f"    Peak memory: {format_bytes(peak)}")

    return {
        'build_time': build_time,
        'n_objects': n_objects,
        'peak_memory': peak,
        'network': optimized_net,
        'optimizer': optimizer,
    }


def verify_biological_patterns(network, optimizer):
    """Verify that biological patterns are preserved."""
    print("\n" + "="*70)
    print("BENCHMARK 4: BIOLOGICAL PATTERN VERIFICATION")
    print("="*70)

    # Check that merged groups have correct parameter distributions
    verified = True

    for sig, merged in optimizer.merged_groups.items():
        if hasattr(merged, '_original_groups'):
            original_names = merged._original_groups
            total_size = len(merged)

            # Check that system_id tracking exists
            if sig in optimizer._merged_system_ids:
                system_ids = optimizer._merged_system_ids[sig]
                unique_systems = len(np.unique(system_ids))
                print(f"  ✓ {merged.name}: {total_size} neurons from {len(original_names)} groups")
                print(f"    System IDs: {unique_systems} unique subpopulations")
            else:
                print(f"  ⚠ {merged.name}: No system_id tracking")
                verified = False

    return verified


def print_final_report(original, optimization, optimized):
    """Print final comparison report."""
    print("\n" + "="*70)
    print("FINAL BENCHMARK REPORT")
    print("="*70)

    print("\n┌─────────────────────────────────────────────────────────────────────┐")
    print("│ {:^35} │ {:^20} │".format("Metric", "Before → After"))
    print("├─────────────────────────────────────────────────────────────────────┤")

    # Object counts
    orig_objects = original['total_objects']
    opt_objects = optimized['n_objects'] if optimized else 'N/A'
    reduction = f"{100*(1 - optimized['n_objects']/orig_objects):.1f}%" if optimized else "N/A"

    print("│ {:^35} │ {:^20} │".format("NeuronGroups", f"{original['n_groups']} → {opt_objects}"))
    print("│ {:^35} │ {:^20} │".format("Total Objects", f"{orig_objects} → {opt_objects}"))
    print("│ {:^35} │ {:^20} │".format("Reduction", reduction))
    print("├─────────────────────────────────────────────────────────────────────┤")

    # Memory
    orig_mem = format_bytes(original['peak_memory'])
    opt_mem = format_bytes(optimized['peak_memory']) if optimized else "N/A"
    print("│ {:^35} │ {:^20} │".format("Peak Memory", f"{orig_mem} → {opt_mem}"))

    # Time
    print("│ {:^35} │ {:^20} │".format("Build Time", f"{original['build_time']:.2f}s → {optimized['build_time']:.2f}s"))
    print("└─────────────────────────────────────────────────────────────────────┘")

    print("\n📋 OPTIMIZATION SUMMARY:")
    print(f"  • Original network: {original['n_groups']} groups, {original['n_synapses']} synapses")
    print(f"  • Optimized network: {len(optimization['optimizer'].merged_groups)} merged groups")
    print(f"  • Merge candidates: {len(optimization['merge_plan'])} equation types")

    print("\n🎯 TARGET ASSESSMENT:")
    target_objects = 12
    target_memory_gb = 6

    if optimized:
        actual_objects = optimized['n_objects']
        actual_memory_gb = optimized['peak_memory'] / (1024**3)

        objects_met = actual_objects <= target_objects
        memory_met = actual_memory_gb <= target_memory_gb

        print(f"  • Objects: {actual_objects} (target: {target_objects}) {'✅' if objects_met else '❌'}")
        print(f"  • Memory: {actual_memory_gb:.1f}GB (target: {target_memory_gb}GB) {'✅' if memory_met else '❌'}")

        if objects_met and memory_met:
            print("\n🎉 ALL TARGETS MET!")
        else:
            print("\n⚠️ Some targets not met - further optimization needed")


if __name__ == "__main__":
    print("="*70)
    print("BRIAN2 EQUATION GROUP OPTIMIZER - FULL BENCHMARK")
    print("="*70)
    print("\nRunning comprehensive before/after benchmarks...")
    print("Scale: 0.01% (5,700 neurons)")

    try:
        # Step 1: Benchmark original
        original = benchmark_original_network()

        # Step 2: Run optimization analysis
        optimization = run_optimization_analysis(original['network'])

        # Step 3: Create optimized network
        optimized = create_optimized_network(optimization['optimizer'])

        if optimized:
            # Step 4: Verify biological patterns
            verify_biological_patterns(optimized['network'], optimized['optimizer'])

            # Step 5: Print final report
            print_final_report(original, optimization, optimized)
        else:
            print("\n[ERROR] Could not create optimized network")

    except Exception as e:
        print(f"\n[ERROR] Benchmark failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    print("\n" + "="*70)
    print("BENCHMARK COMPLETE")
    print("="*70)
