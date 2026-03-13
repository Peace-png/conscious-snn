"""
Phase 3: Instantaneous Phase Extraction

Extract instantaneous phase from rate signals using Hilbert transform
after bandpass filtering around each system's target frequency band.
"""

import numpy as np
from scipy.signal import hilbert, butter, filtfilt


# Bandpass bounds per system (Hz)
# Based on biological oscillation frequencies
SYSTEM_BANDS = {
    'brainstem':    (0.5, 5.0),    # autonomic tone
    'cardiac':      (0.5, 2.0),    # ~1 Hz pacemaker
    'respiratory':  (0.1, 0.5),    # ~0.25 Hz rhythm
    'limbic':       (2.0, 8.0),    # theta range
    'hippocampus':  (4.0, 8.0),    # theta (4-8 Hz)
    'thalamus':     (8.0, 12.0),   # alpha (8-12 Hz)
    'dmn':          (8.0, 12.0),   # alpha (8-12 Hz)
    'prefrontal':   (0.05, 0.5),   # very slow
}


def extract_phase_signals(
    rate_file='output/rate_signals_60s.npz',
    output_file='output/phase_signals_60s.npz',
    fs=1000.0
):
    """
    Extract instantaneous phase from rate signals via Hilbert transform.

    Parameters
    ----------
    rate_file : str
        Path to rate data from Phase 2
    output_file : str
        Path for output phase signals
    fs : float
        Sampling frequency in Hz (1000 for 1ms resolution)

    Returns
    -------
    dict
        phases[system_name] = array[radians, -π to π]
    """
    print("=" * 60)
    print("PHASE 3: INSTANTANEOUS PHASE EXTRACTION")
    print("=" * 60)

    # Load rate data
    print(f"Loading: {rate_file}")
    data = np.load(rate_file, allow_pickle=True)

    duration_ms = float(data['duration_ms'])
    dt_ms = float(data['dt_ms'])

    # Get rate signals
    rate_signals = {}
    for key in data.keys():
        if key.endswith('_rate'):
            name = key[:-5]  # Remove '_rate'
            rate_signals[name] = data[key]

    print(f"Duration: {duration_ms/1000:.1f}s")
    print(f"Sampling: {fs} Hz")
    print()

    # Extract phases
    phase_signals = {}
    nyq = fs / 2.0

    for name, rate in rate_signals.items():
        if name not in SYSTEM_BANDS:
            print(f"  {name}: No band definition, skipping")
            continue

        f_low, f_high = SYSTEM_BANDS[name]

        # Check if band is valid
        if f_high >= nyq:
            print(f"  {name}: Band too high for sampling rate")
            phase_signals[name] = np.zeros_like(rate)
            continue

        # Check if signal has enough energy
        if np.std(rate) < 1e-6:
            print(f"  {name}: Signal flat, using zeros")
            phase_signals[name] = np.zeros_like(rate)
            continue

        try:
            # Bandpass filter
            b, a = butter(4, [f_low/nyq, f_high/nyq], btype='band')
            filtered = filtfilt(b, a, rate)

            # Hilbert transform
            analytic = hilbert(filtered)
            phase = np.angle(analytic)  # -π to π

            phase_signals[name] = phase

            # Stats
            mean_phase = np.mean(phase)
            phase_std = np.std(phase)
            print(f"  {name}: band=[{f_low}, {f_high}] Hz, phase_std={phase_std:.2f} rad")

        except Exception as e:
            print(f"  {name}: Filter error ({e}), using zeros")
            phase_signals[name] = np.zeros_like(rate)

    # Save
    save_dict = {
        'duration_ms': duration_ms,
        'dt_ms': dt_ms,
        'fs': fs,
        'system_bands': np.array(list(SYSTEM_BANDS.keys())),
        'f_low': np.array([SYSTEM_BANDS[s][0] for s in SYSTEM_BANDS]),
        'f_high': np.array([SYSTEM_BANDS[s][1] for s in SYSTEM_BANDS]),
    }

    for name, phase in phase_signals.items():
        save_dict[f'{name}_phase'] = phase

    np.savez(output_file, **save_dict)
    print(f"\nSaved to: {output_file}")

    return phase_signals


if __name__ == '__main__':
    extract_phase_signals()
