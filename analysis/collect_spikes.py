"""
Phase 1: Spike Data Collection

Run 60-second simulation and extract spike trains from all 8 systems.
Saves to output/spike_trains_60s.npz for subsequent analysis.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from datetime import datetime
import warnings

def collect_spike_data(duration_ms=60000, scale_factor=0.001, output_dir='output'):
    """
    Run simulation and collect spike trains from all 8 systems.

    Parameters
    ----------
    duration_ms : int
        Simulation duration in milliseconds
    scale_factor : float
        Network scale (0.001 = 0.1% = ~570 neurons)
    output_dir : str
        Output directory for data files

    Returns
    -------
    dict
        spike_trains[system_name] = {'times': array[ms], 'neuron_ids': array[int]}
    """
    from brian2 import ms, start_scope

    # Suppress Brian2 warnings during simulation
    warnings.filterwarnings('ignore')

    print("=" * 60)
    print("PHASE 1: SPIKE DATA COLLECTION")
    print("=" * 60)
    print(f"Duration: {duration_ms/1000:.1f}s")
    print(f"Scale: {scale_factor*100:.2f}%")
    print()

    # Import network components
    from core import ConsciousNetwork, ConsciousSNNConfig, ScaleParams, ComputeConfig

    # Create config
    config = ConsciousSNNConfig(
        scale=ScaleParams(scale_factor=scale_factor),
        compute=ComputeConfig(backend='cython')
    )

    # Build network
    print("Building network...")
    start_scope()
    network = ConsciousNetwork(config)
    network.build()

    # Count neurons and monitors
    total_neurons = 0
    total_monitors = 0
    for name, system in network.systems.items():
        monitors = system.monitors
        n_monitors = len(monitors)
        n_neurons = sum(len(m.source) for m in monitors.values() if hasattr(m, 'source'))
        total_neurons += n_neurons
        total_monitors += n_monitors
        print(f"  {name}: {n_neurons} neurons, {n_monitors} monitors")

    print(f"\nTotal: {total_neurons} neurons, {total_monitors} monitors")

    # Run simulation
    print(f"\nRunning {duration_ms/1000:.1f}s simulation...")
    print(f"Start time: {datetime.now().strftime('%H:%M:%S')}")

    start_time = datetime.now()
    network.brian_network.run(duration_ms * ms)
    elapsed = (datetime.now() - start_time).total_seconds()

    print(f"End time: {datetime.now().strftime('%H:%M:%S')}")
    print(f"Elapsed: {elapsed:.1f}s")

    # Extract spike data
    print("\nExtracting spike trains...")

    spike_trains = {}

    for name, system in network.systems.items():
        monitors = system.monitors

        # Collect all spikes from this system's monitors
        all_times = []
        all_ids = []

        for mon_name, monitor in monitors.items():
            if hasattr(monitor, 't') and hasattr(monitor, 'i'):
                t = np.array(monitor.t / ms)  # Convert to ms
                i = np.array(monitor.i)

                if len(t) > 0:
                    all_times.append(t)
                    all_ids.append(i)

        if all_times:
            times = np.concatenate(all_times)
            ids = np.concatenate(all_ids)

            # Sort by time
            sort_idx = np.argsort(times)
            times = times[sort_idx]
            ids = ids[sort_idx]
        else:
            times = np.array([])
            ids = np.array([])

        spike_trains[name] = {
            'times': times,
            'neuron_ids': ids
        }

        n_spikes = len(times)
        rate = n_spikes / (duration_ms / 1000) if duration_ms > 0 else 0
        print(f"  {name}: {n_spikes} spikes ({rate:.1f} Hz total)")

    # Save to file
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, 'spike_trains_60s.npz')

    # Convert dict of dicts to saveable format
    save_dict = {}
    for name, data in spike_trains.items():
        save_dict[f'{name}_times'] = data['times']
        save_dict[f'{name}_ids'] = data['neuron_ids']

    save_dict['duration_ms'] = duration_ms
    save_dict['scale_factor'] = scale_factor
    save_dict['systems'] = np.array(list(spike_trains.keys()))

    np.savez(output_file, **save_dict)
    print(f"\nSaved to: {output_file}")

    # Summary stats
    total_spikes = sum(len(d['times']) for d in spike_trains.values())
    print(f"\nTotal spikes collected: {total_spikes}")
    print(f"Active systems: {sum(1 for d in spike_trains.values() if len(d['times']) > 0)}/8")

    return spike_trains


if __name__ == '__main__':
    collect_spike_data()
