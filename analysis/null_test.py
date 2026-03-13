"""
Phase 5: Null Test with Surrogate Data

Test whether observed PLV values are significantly different
from random by shuffling spike times and recomputing PLV.
"""

import numpy as np
from scipy.ndimage import gaussian_filter1d
from scipy.signal import hilbert, butter, filtfilt
from tqdm import tqdm


# Same bands as Phase 3
SYSTEM_BANDS = {
    'brainstem':    (0.5, 5.0),
    'cardiac':      (0.5, 2.0),
    'respiratory':  (0.1, 0.5),
    'limbic':       (2.0, 8.0),
    'hippocampus':  (4.0, 8.0),
    'thalamus':     (8.0, 12.0),
    'dmn':          (8.0, 12.0),
    'prefrontal':   (0.05, 0.5),
}


def generate_surrogate(spike_times, duration_ms):
    """
    Generate surrogate spike train by shuffling times.

    Preserves total spike count but destroys temporal structure.
    """
    n_spikes = len(spike_times)
    if n_spikes == 0:
        return np.array([])
    return np.sort(np.random.uniform(0, duration_ms, n_spikes))


def spikes_to_rate(spike_times, duration_ms, dt_ms=1.0, sigma_ms=20.0):
    """Convert spike times to smoothed rate signal."""
    n_bins = int(duration_ms / dt_ms) + 1
    bins = np.arange(0, duration_ms + dt_ms, dt_ms)

    counts, _ = np.histogram(spike_times, bins=bins)
    rate = counts * 1000.0 / dt_ms

    sigma_bins = sigma_ms / dt_ms
    return gaussian_filter1d(rate.astype(float), sigma=sigma_bins)


def extract_phase(rate_signal, f_low, f_high, fs=1000.0):
    """Extract phase via Hilbert transform on bandpass-filtered signal."""
    nyq = fs / 2.0

    if f_high >= nyq or f_high <= f_low:
        return np.zeros_like(rate_signal)

    try:
        b, a = butter(4, [f_low/nyq, f_high/nyq], btype='band')
        filtered = filtfilt(b, a, rate_signal)
        analytic = hilbert(filtered)
        return np.angle(analytic)
    except:
        return np.zeros_like(rate_signal)


def run_null_test(
    spike_file='output/spike_trains_60s.npz',
    plv_file='output/plv_matrix_60s.npz',
    output_file='output/null_test_results.npz',
    n_surrogates=100,
    window_ms=500,
    step_ms=50
):
    """
    Compare real PLV against surrogate distribution.

    Parameters
    ----------
    spike_file : str
        Original spike data
    plv_file : str
        Real PLV results
    output_file : str
        Output file for z-scores and p-values
    n_surrogates : int
        Number of surrogate datasets

    Returns
    -------
    z_scores : array (n_pairs,)
    p_values : array (n_pairs,)
    """
    print("=" * 60)
    print("PHASE 5: NULL TEST WITH SURROGATE DATA")
    print("=" * 60)

    # Load real data
    print(f"Loading: {spike_file}")
    spike_data = np.load(spike_file, allow_pickle=True)

    print(f"Loading: {plv_file}")
    plv_data = np.load(plv_file, allow_pickle=True)

    real_plv = plv_data['mean_plv']
    systems = list(plv_data['systems'])
    n_systems = len(systems)
    duration_ms = float(spike_data['duration_ms'])

    print(f"Duration: {duration_ms/1000:.1f}s")
    print(f"Surrogates: {n_surrogates}")
    print(f"Systems: {n_systems}")
    print()

    # Extract original spike trains
    spike_trains = {}
    for key in spike_data.keys():
        if key.endswith('_times'):
            name = key[:-6]
            spike_trains[name] = spike_data[key]

    # Get spike trains for all systems in order
    system_spikes = []
    for sys in systems:
        if sys in spike_trains:
            system_spikes.append(spike_trains[sys])
        else:
            system_spikes.append(np.array([]))

    # Setup PLV computation
    window_samples = 500
    step_samples = 50
    dt_ms = 1.0
    n_bins = int(duration_ms / dt_ms) + 1

    def compute_surrogate_plv(spike_list):
        """Compute PLV matrix from spike list."""
        # Convert to rates
        rates = {}
        for sys, spikes in zip(systems, spike_list):
            rates[sys] = spikes_to_rate(spikes, duration_ms, dt_ms=dt_ms)

        # Extract phases
        phases = {}
        fs = 1000.0
        for sys, rate in rates.items():
            if sys in SYSTEM_BANDS:
                f_low, f_high = SYSTEM_BANDS[sys]
                phases[sys] = extract_phase(rate, f_low, f_high, fs)
            else:
                phases[sys] = np.zeros_like(rate)

        # Compute PLV in windows
        n_samples = len(phases[systems[0]])
        n_windows = (n_samples - window_samples) // step_samples + 1

        plv_matrix = np.zeros((n_windows, n_systems, n_systems))

        for w in range(n_windows):
            start = w * step_samples
            end = start + window_samples

            for i in range(n_systems):
                plv_matrix[w, i, i] = 1.0
                for j in range(i+1, n_systems):
                    phase_i = phases[systems[i]][start:end]
                    phase_j = phases[systems[j]][start:end]
                    plv = np.abs(np.mean(np.exp(1j * (phase_i - phase_j))))
                    plv_matrix[w, i, j] = plv
                    plv_matrix[w, j, i] = plv

        return np.mean(plv_matrix, axis=0)

    # Generate surrogates
    print(f"Generating {n_surrogates} surrogate datasets...")

    surrogate_plvs = []

    for s in tqdm(range(n_surrogates), desc="Surrogates"):
        # Shuffle each system's spike times
        surrogate_spikes = [
            generate_surrogate(spikes, duration_ms)
            for spikes in system_spikes
        ]

        # Compute PLV
        surr_plv = compute_surrogate_plv(surrogate_spikes)
        surrogate_plvs.append(surr_plv)

    surrogate_array = np.array(surrogate_plvs)  # (n_surrogates, n_systems, n_systems)

    # Statistics
    surrogate_mean = np.mean(surrogate_array, axis=0)
    surrogate_std = np.std(surrogate_array, axis=0) + 1e-10

    # Z-scores
    z_scores = (real_plv - surrogate_mean) / surrogate_std

    # P-values (two-tailed)
    from scipy.stats import norm
    p_values = 2 * (1 - norm.cdf(np.abs(z_scores)))

    # Report significant pairs
    print("\n=== SIGNIFICANT PLV PAIRS ===")
    print("(Bonferroni threshold: p < 0.000357 for 28 comparisons)")
    print()

    significant_pairs = []
    for i in range(n_systems):
        for j in range(i + 1, n_systems):
            z = z_scores[i, j]
            p = p_values[i, j]
            real = real_plv[i, j]
            surr_m = surrogate_mean[i, j]
            surr_s = surrogate_std[i, j]

            sig = "***" if p < 0.000357 else ("**" if p < 0.001 else ("*" if p < 0.01 else ""))

            print(f"{systems[i]:12} - {systems[j]:12}: "
                  f"PLV={real:.4f}, surr={surr_m:.4f}±{surr_s:.4f}, "
                  f"z={z:+6.2f}, p={p:.2e} {sig}")

            if p < 0.000357:
                significant_pairs.append((systems[i], systems[j], real, z, p))

    # Save
    save_dict = {
        'z_scores': z_scores,
        'p_values': p_values,
        'surrogate_mean': surrogate_mean,
        'surrogate_std': surrogate_std,
        'real_plv': real_plv,
        'systems': np.array(systems),
        'n_surrogates': n_surrogates,
        'significant_pairs': np.array(significant_pairs) if significant_pairs else np.array([]),
    }

    np.savez(output_file, **save_dict)
    print(f"\nSaved to: {output_file}")

    print(f"\nSignificant pairs (p < 0.000357): {len(significant_pairs)}/28")

    return z_scores, p_values


if __name__ == '__main__':
    run_null_test()
