"""
Phase 2: Rate Signal Extraction

Convert spike trains to continuous population firing rate signals
using Gaussian kernel smoothing.
"""

import numpy as np
from scipy.ndimage import gaussian_filter1d


def extract_rate_signals(
    spike_file='output/spike_trains_60s.npz',
    output_file='output/rate_signals_60s.npz',
    dt_ms=1.0,
    sigma_ms=20.0
):
    """
    Convert spike trains to smoothed population firing rates.

    Parameters
    ----------
    spike_file : str
        Path to spike data from Phase 1
    output_file : str
        Path for output rate signals
    dt_ms : float
        Time resolution in milliseconds
    sigma_ms : float
        Gaussian kernel width for smoothing

    Returns
    -------
    dict
        rates[system_name] = array[Hz] at dt_ms resolution
    """
    print("=" * 60)
    print("PHASE 2: RATE SIGNAL EXTRACTION")
    print("=" * 60)

    # Load spike data
    print(f"Loading: {spike_file}")
    data = np.load(spike_file, allow_pickle=True)

    duration_ms = float(data['duration_ms'])
    systems = list(data['systems'])
    scale_factor = float(data['scale_factor'])

    print(f"Duration: {duration_ms/1000:.1f}s")
    print(f"Systems: {len(systems)}")
    print(f"Smoothing: sigma={sigma_ms}ms, dt={dt_ms}ms")
    print()

    # Create time bins
    n_bins = int(duration_ms / dt_ms) + 1
    bins = np.arange(0, duration_ms + dt_ms, dt_ms)

    # Extract rates for each system
    rate_signals = {}

    for name in systems:
        times_key = f'{name}_times'
        ids_key = f'{name}_ids'

        if times_key not in data:
            print(f"  {name}: No data found")
            continue

        spike_times = data[times_key]
        neuron_ids = data[ids_key]

        if len(spike_times) == 0:
            print(f"  {name}: No spikes")
            rate_signals[name] = np.zeros(n_bins)
            continue

        # Create histogram of spike counts
        counts, _ = np.histogram(spike_times, bins=bins)

        # Convert to firing rate (Hz)
        # rate = counts / (dt_ms / 1000) = counts * 1000 / dt_ms
        rate = counts * 1000.0 / dt_ms

        # Apply Gaussian smoothing
        sigma_bins = sigma_ms / dt_ms
        rate_smooth = gaussian_filter1d(rate.astype(float), sigma=sigma_bins)

        rate_signals[name] = rate_smooth

        mean_rate = np.mean(rate_smooth)
        max_rate = np.max(rate_smooth)
        print(f"  {name}: mean={mean_rate:.2f} Hz, max={max_rate:.2f} Hz")

    # Save
    save_dict = {
        'duration_ms': duration_ms,
        'dt_ms': dt_ms,
        'sigma_ms': sigma_ms,
        'scale_factor': scale_factor,
        'time_bins': bins[:-1],  # n_bins edges → n_bins-1 centers
    }

    for name, rate in rate_signals.items():
        save_dict[f'{name}_rate'] = rate

    np.savez(output_file, **save_dict)
    print(f"\nSaved to: {output_file}")

    return rate_signals


if __name__ == '__main__':
    extract_rate_signals()
