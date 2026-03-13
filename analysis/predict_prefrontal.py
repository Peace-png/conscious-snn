"""
Phase 6: Prefrontal State Prediction

Test whether thalamo-hippocampal PLV predicts prefrontal activation
better than firing rates alone.
"""

import numpy as np
from scipy.ndimage import gaussian_filter1d
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_score, LeaveOneOut
from sklearn.metrics import roc_auc_score


def predict_prefrontal_state(
    plv_file='output/plv_matrix_60s.npz',
    rate_file='output/rate_signals_60s.npz',
    output_file='output/prefrontal_prediction.npz'
):
    """
    Compare rate vs PLV predictors for prefrontal state.

    Tests:
    1. Thalamus rate alone
    2. Hippocampus rate alone
    3. Thalamus + Hippocampus rates
    4. Thalamus-Hippocampus PLV
    5. All 28 PLV pairs

    Parameters
    ----------
    plv_file : str
        PLV tensor from Phase 4
    rate_file : str
        Rate signals from Phase 2
    output_file : str
        Output file for prediction results

    Returns
    -------
    dict
        AUC scores for each predictor
    """
    print("=" * 60)
    print("PHASE 6: PREFRONTAL STATE PREDICTION")
    print("=" * 60)

    # Load PLV data
    print(f"Loading: {plv_file}")
    plv_data = np.load(plv_file, allow_pickle=True)

    plv_tensor = plv_data['plv_tensor']
    systems = list(plv_data['systems'])
    window_ms = int(plv_data['window_ms'])
    step_ms = int(plv_data['step_ms'])
    n_windows = int(plv_data['n_windows'])

    # Load rate data
    print(f"Loading: {rate_file}")
    rate_data = np.load(rate_file, allow_pickle=True)

    duration_ms = float(rate_data['duration_ms'])
    dt_ms = float(rate_data['dt_ms'])

    # Get system indices
    try:
        thal_idx = systems.index('thalamus')
        hipp_idx = systems.index('hippocampus')
        pfc_idx = systems.index('prefrontal')
    except ValueError as e:
        print(f"Error: Missing required system - {e}")
        return None

    print(f"Systems: thalamus={thal_idx}, hippocampus={hippoc_idx}, prefrontal={pfc_idx}")
    print(f"Windows: {n_windows}")
    print()

    # Extract rate signals in windows
    def get_rate_in_windows(rate_signal, n_windows, window_ms, step_ms, dt_ms):
        """Get mean rate in each window."""
        window_samples = int(window_ms / dt_ms)
        step_samples = int(step_ms / dt_ms)

        rates = np.zeros(n_windows)
        for w in range(n_windows):
            start = w * step_samples
            end = start + window_samples
            rates[w] = np.mean(rate_signal[start:end])
        return rates

    # Get rate predictors
    thal_rate = get_rate_in_windows(
        rate_data['thalamus_rate'], n_windows, window_ms, step_ms, dt_ms
    )
    hipp_rate = get_rate_in_windows(
        rate_data['hippocampus_rate'], n_windows, window_ms, step_ms, dt_ms
    )
    pfc_rate = get_rate_in_windows(
        rate_data['prefrontal_rate'], n_windows, window_ms, step_ms, dt_ms
    )

    # Get PLV predictors
    thal_hipp_plv = plv_tensor[:, thal_idx, hipp_idx]

    # Define prefrontal state: active vs inactive
    # Use median as threshold
    threshold = np.median(pfc_rate)
    pfc_state = (pfc_rate > threshold).astype(int)

    print(f"Prefrontal states: {np.sum(pfc_state==0)} inactive, {np.sum(pfc_state==1)} active")
    print(f"Threshold: {threshold:.4f} Hz")
    print()

    # Prepare predictors
    predictors = {
        'thalamus_rate': thal_rate.reshape(-1, 1),
        'hippocampus_rate': hipp_rate.reshape(-1, 1),
        'both_rates': np.column_stack([thal_rate, hipp_rate]),
        'thal_hipp_plv': thal_hipp_plv.reshape(-1, 1),
        'all_plv': plv_tensor.reshape(n_windows, -1),  # All 64 values (8x8)
    }

    # Cross-validated AUC scores
    results = {}

    print("=== PREDICTION RESULTS (5-fold CV) ===")
    print()

    for name, X in predictors.items():
        try:
            # Handle NaN/inf
            X = np.nan_to_num(X, nan=0, posinf=0, neginf=0)

            # Logistic regression with 5-fold CV
            clf = LogisticRegression(max_iter=1000, solver='lbfgs')
            scores = cross_val_score(clf, X, pfc_state, cv=5, scoring='roc_auc')
            mean_auc = np.mean(scores)
            std_auc = np.std(scores)

            results[name] = {
                'auc_mean': mean_auc,
                'auc_std': std_auc,
                'scores': scores,
            }

            print(f"{name:20}: AUC = {mean_auc:.3f} ± {std_auc:.3f}")

        except Exception as e:
            print(f"{name:20}: ERROR - {e}")
            results[name] = {'auc_mean': 0, 'auc_std': 0, 'scores': []}

    # Compare best rate vs best PLV
    print()
    print("=== COMPARISON ===")

    best_rate_auc = max(
        results['thalamus_rate']['auc_mean'],
        results['hippocampus_rate']['auc_mean'],
        results['both_rates']['auc_mean']
    )
    plv_auc = results['thal_hipp_plv']['auc_mean']
    all_plv_auc = results['all_plv']['auc_mean']

    print(f"Best rate predictor AUC:     {best_rate_auc:.3f}")
    print(f"Thalamo-hippocampal PLV AUC: {plv_auc:.3f}")
    print(f"All PLV pairs AUC:           {all_plv_auc:.3f}")
    print()

    if all_plv_auc > best_rate_auc + 0.05:
        print("CONCLUSION: PLV carries MORE information than rate alone")
        conclusion = "PLV_SUPERIOR"
    elif all_plv_auc > best_rate_auc:
        print("CONCLUSION: PLV carries SOME additional information")
        conclusion = "PLV_BETTER"
    elif best_rate_auc > all_plv_auc + 0.05:
        print("CONCLUSION: Rate carries MORE information than PLV")
        conclusion = "RATE_SUPERIOR"
    else:
        print("CONCLUSION: Rate and PLV carry SIMILAR information")
        conclusion = "EQUIVALENT"

    # Save results
    save_dict = {
        'predictor_names': np.array(list(results.keys())),
        'auc_means': np.array([results[n]['auc_mean'] for n in results]),
        'auc_stds': np.array([results[n]['auc_std'] for n in results]),
        'pfc_state': pfc_state,
        'threshold': threshold,
        'conclusion': conclusion,
        'best_rate_auc': best_rate_auc,
        'all_plv_auc': all_plv_auc,
    }

    np.savez(output_file, **save_dict)
    print(f"\nSaved to: {output_file}")

    return results


if __name__ == '__main__':
    predict_prefrontal_state()
