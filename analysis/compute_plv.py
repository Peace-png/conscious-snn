"""
Phase 4: PLV Matrix Computation

Compute Phase-Locking Value (PLV) between all system pairs
in sliding windows across the full simulation.
"""

import numpy as np


def compute_plv(phase_a, phase_b):
    """
    Compute Phase-Locking Value between two phase signals.

    PLV = |mean(exp(i * (phase_a - phase_b)))|

    Parameters
    ----------
    phase_a : array
        Phase signal in radians (-π to π)
    phase_b : array
        Phase signal in radians (-π to π)

    Returns
    -------
    float
        PLV in [0, 1] (0 = random, 1 = perfectly locked)
    """
    phase_diff = phase_a - phase_b
    plv = np.abs(np.mean(np.exp(1j * phase_diff)))
    return float(plv)


def compute_plv_matrix(
    phase_file='output/phase_signals_60s.npz',
    output_file='output/plv_matrix_60s.npz',
    window_ms=500,
    step_ms=50
):
    """
    Compute PLV for all system pairs in sliding windows.

    Parameters
    ----------
    phase_file : str
        Path to phase data from Phase 3
    output_file : str
        Path for output PLV tensor
    window_ms : int
        Window size in milliseconds
    step_ms : int
        Step size in milliseconds

    Returns
    -------
    plv_tensor : array (n_windows, n_systems, n_systems)
    systems : list
        System names in order
    """
    print("=" * 60)
    print("PHASE 4: PLV MATRIX COMPUTATION")
    print("=" * 60)

    # Load phase data
    print(f"Loading: {phase_file}")
    data = np.load(phase_file, allow_pickle=True)

    duration_ms = float(data['duration_ms'])
    fs = float(data['fs'])
    dt_ms = 1000.0 / fs

    # Extract phase signals
    phase_signals = {}
    systems = []

    for key in data.keys():
        if key.endswith('_phase'):
            name = key[:-6]  # Remove '_phase'
            phase_signals[name] = data[key]
            systems.append(name)

    n_systems = len(systems)
    n_samples = len(phase_signals[systems[0]])

    print(f"Duration: {duration_ms/1000:.1f}s")
    print(f"Systems: {n_systems}")
    print(f"Samples: {n_samples}")
    print(f"Window: {window_ms}ms, Step: {step_ms}ms")
    print()

    # Convert ms to samples
    window_samples = int(window_ms / dt_ms)
    step_samples = int(step_ms / dt_ms)

    # Compute number of windows
    n_windows = (n_samples - window_samples) // step_samples + 1

    print(f"Computing PLV for {n_windows} windows...")

    # Initialize PLV tensor
    plv_tensor = np.zeros((n_windows, n_systems, n_systems))

    # Compute PLV for each window and pair
    for w_idx in range(n_windows):
        w_start = w_idx * step_samples
        w_end = w_start + window_samples

        # Diagonal = 1 (self PLV)
        for i in range(n_systems):
            plv_tensor[w_idx, i, i] = 1.0

        # Off-diagonal pairs
        for i in range(n_systems):
            for j in range(i + 1, n_systems):
                phase_i = phase_signals[systems[i]][w_start:w_end]
                phase_j = phase_signals[systems[j]][w_start:w_end]

                plv = compute_plv(phase_i, phase_j)
                plv_tensor[w_idx, i, j] = plv
                plv_tensor[w_idx, j, i] = plv  # Symmetric

        # Progress
        if (w_idx + 1) % 100 == 0:
            print(f"  Window {w_idx+1}/{n_windows}")

    print(f"  Computed {n_windows} windows, {n_systems*(n_systems-1)//2} pairs each")

    # Compute mean PLV matrix
    mean_plv = np.mean(plv_tensor, axis=0)

    print("\nMean PLV matrix (top 5 pairs):")
    pairs = []
    for i in range(n_systems):
        for j in range(i + 1, n_systems):
            pairs.append((systems[i], systems[j], mean_plv[i, j]))
    pairs.sort(key=lambda x: x[2], reverse=True)

    for sys_a, sys_b, plv in pairs[:5]:
        print(f"  {sys_a} - {sys_b}: {plv:.4f}")

    # Save
    save_dict = {
        'plv_tensor': plv_tensor,
        'mean_plv': mean_plv,
        'systems': np.array(systems),
        'window_ms': window_ms,
        'step_ms': step_ms,
        'n_windows': n_windows,
        'duration_ms': duration_ms,
    }

    np.savez(output_file, **save_dict)
    print(f"\nSaved to: {output_file}")

    return plv_tensor, systems


if __name__ == '__main__':
    compute_plv_matrix()
