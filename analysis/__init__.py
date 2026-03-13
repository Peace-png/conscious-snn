"""
Phase Coherence Analysis Package

Tools for measuring cross-system phase relationships in the conscious SNN.
"""

from .collect_spikes import collect_spike_data
from .extract_rates import extract_rate_signals
from .extract_phases import extract_phase_signals
from .compute_plv import compute_plv_matrix
from .null_test import run_null_test
from .predict_prefrontal import predict_prefrontal_state

__all__ = [
    'collect_spike_data',
    'extract_rate_signals',
    'extract_phase_signals',
    'compute_plv_matrix',
    'run_null_test',
    'predict_prefrontal_state',
]
