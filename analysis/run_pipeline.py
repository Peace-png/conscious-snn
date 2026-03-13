"""
Run Full Phase Coherence Analysis Pipeline

Executes all 6 phases in sequence:
1. Spike data collection
2. Rate signal extraction
3. Phase extraction
4. PLV computation
5. Null test
6. Prefrontal prediction

Each phase saves output for resume capability.
"""

import sys
import os
import numpy as np
from datetime import datetime
import warnings

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Suppress warnings during simulation
warnings.filterwarnings('ignore')


def run_full_pipeline(
    duration_ms=60000,
    scale_factor=0.001,
    n_surrogates=50,  # Reduced for speed
    output_dir='output'
):
    """
    Run complete phase coherence analysis.

    Parameters
    ----------
    duration_ms : int
        Simulation duration (default 60s)
    scale_factor : float
        Network scale (default 0.001 = 0.1%)
    n_surrogates : int
        Number of surrogate datasets
    output_dir : str
        Output directory

    Returns
    -------
    dict
        Summary of all results
    """
    os.makedirs(output_dir, exist_ok=True)

    print("=" * 70)
    print("PHASE COHERENCE ANALYSIS - FULL PIPELINE")
    print("=" * 70)
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Duration: {duration_ms/1000:.1f}s")
    print(f"Scale: {scale_factor*100:.2f}%")
    print(f"Surrogates: {n_surrogates}")
    print("=" * 70)
    print()

    results = {}

    # Phase 1: Spike Collection
    print("\n" + "=" * 70)
    print("PHASE 1: SPIKE DATA COLLECTION")
    print("=" * 70)

    from analysis.collect_spikes import collect_spike_data

    spike_trains = collect_spike_data(
        duration_ms=duration_ms,
        scale_factor=scale_factor,
        output_dir=output_dir
    )

    results['spike_trains'] = {
        name: len(data['times'])
        for name, data in spike_trains.items()
    }

    # Phase 2: Rate Extraction
    print("\n" + "=" * 70)
    print("PHASE 2: RATE SIGNAL EXTRACTION")
    print("=" * 70)

    from analysis.extract_rates import extract_rate_signals

    rate_signals = extract_rate_signals(
        spike_file=f'{output_dir}/spike_trains_60s.npz',
        output_file=f'{output_dir}/rate_signals_60s.npz'
    )

    results['rate_signals'] = {
        name: np.mean(rate)
        for name, rate in rate_signals.items()
    }

    # Phase 3: Phase Extraction
    print("\n" + "=" * 70)
    print("PHASE 3: PHASE EXTRACTION")
    print("=" * 70)

    from analysis.extract_phases import extract_phase_signals

    phase_signals = extract_phase_signals(
        rate_file=f'{output_dir}/rate_signals_60s.npz',
        output_file=f'{output_dir}/phase_signals_60s.npz'
    )

    # Phase 4: PLV Computation
    print("\n" + "=" * 70)
    print("PHASE 4: PLV MATRIX COMPUTATION")
    print("=" * 70)

    from analysis.compute_plv import compute_plv_matrix

    plv_tensor, systems = compute_plv_matrix(
        phase_file=f'{output_dir}/phase_signals_60s.npz',
        output_file=f'{output_dir}/plv_matrix_60s.npz'
    )

    results['n_windows'] = plv_tensor.shape[0]
    results['systems'] = systems

    # Phase 5: Null Test
    print("\n" + "=" * 70)
    print("PHASE 5: NULL TEST")
    print("=" * 70)

    from analysis.null_test import run_null_test

    z_scores, p_values = run_null_test(
        spike_file=f'{output_dir}/spike_trains_60s.npz',
        plv_file=f'{output_dir}/plv_matrix_60s.npz',
        output_file=f'{output_dir}/null_test_results.npz',
        n_surrogates=n_surrogates
    )

    # Count significant pairs
    n_sig = np.sum(p_values < 0.000357) // 2  # Upper triangle only
    results['significant_pairs'] = n_sig

    # Phase 6: Prefrontal Prediction
    print("\n" + "=" * 70)
    print("PHASE 6: PREFRONTAL PREDICTION")
    print("=" * 70)

    from analysis.predict_prefrontal import predict_prefrontal_state

    pred_results = predict_prefrontal_state(
        plv_file=f'{output_dir}/plv_matrix_60s.npz',
        rate_file=f'{output_dir}/rate_signals_60s.npz',
        output_file=f'{output_dir}/prefrontal_prediction.npz'
    )

    if pred_results:
        results['prediction'] = pred_results

    # Summary
    print("\n" + "=" * 70)
    print("PIPELINE COMPLETE")
    print("=" * 70)
    print(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("OUTPUT FILES:")
    print(f"  {output_dir}/spike_trains_60s.npz")
    print(f"  {output_dir}/rate_signals_60s.npz")
    print(f"  {output_dir}/phase_signals_60s.npz")
    print(f"  {output_dir}/plv_matrix_60s.npz")
    print(f"  {output_dir}/null_test_results.npz")
    print(f"  {output_dir}/prefrontal_prediction.npz")
    print()

    # Quick summary
    total_spikes = sum(results['spike_trains'].values())
    print(f"Total spikes: {total_spikes}")
    print(f"Significant PLV pairs: {n_sig}/28")

    return results


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Run phase coherence analysis')
    parser.add_argument('--duration', type=int, default=60000, help='Duration in ms')
    parser.add_argument('--scale', type=float, default=0.001, help='Scale factor')
    parser.add_argument('--surrogates', type=int, default=50, help='N surrogates')
    parser.add_argument('--output', type=str, default='output', help='Output dir')

    args = parser.parse_args()

    run_full_pipeline(
        duration_ms=args.duration,
        scale_factor=args.scale,
        n_surrogates=args.surrogates,
        output_dir=args.output
    )
