"""
Conscious SNN - Brian2 Architecture for Human Conscious Processing

Based on the Stewardship Hypothesis: mapping the complete biological signature
of conscious function as a timing and influence map.

The Cave Wall Principle: Pattern always present, spike reveals it.
Intent is external input that illuminates specific layers on demand.
"""

from .config import ConsciousSNNConfig, ScaleParams, ComputeConfig
from .neurons import (
    AdaptiveExpLIF,
    IzhikevichNeuron,
    OscillatoryNeuron,
    CardiacNeuron,
    RespiratoryNeuron,
    InhibitoryInterneuron
)
from .base import (
    SystemPopulation,
    ConsciousNetwork,
    IntentInput,
    InfluenceMatrix
)

__version__ = "0.1.0"
__author__ = "Stewardship Hypothesis Project"

# Default configuration
DEFAULT_CONFIG = ConsciousSNNConfig()

# System neuron counts (biological estimates)
SYSTEM_NEURON_COUNTS = {
    'brainstem': 100_000_000,      # ~100M (autonomic floor)
    'cardiac': 40_000,              # ~40k (intrinsic cardiac)
    'respiratory': 10_000,          # ~10k (pre-Bötzinger + centers)
    'limbic': 130_000_000,          # ~130M (amygdala, cingulate)
    'hippocampus': 30_000_000,      # ~30M (CA1, CA3, DG)
    'prefrontal': 200_000_000,      # ~200M (dlPFC, vlPFC, mPFC, OFC)
    'thalamus': 10_000_000,         # ~10M (relay + reticular)
    'dmn': 50_000_000,              # ~50M distributed (PCC, mPFC, parietal)
}

# Key oscillation frequencies (Hz)
OSCILLATION_FREQUENCIES = {
    'autonomic': 0.5,      # Brainstem autonomic rhythm
    'cardiac': 1.0,        # ~60 bpm
    'respiratory': 0.25,   # ~15 breaths/min
    'theta': 6.0,          # Hippocampal theta (4-12 Hz)
    'alpha': 10.0,         # Thalamocortical alpha (8-12 Hz)
    'beta': 20.0,          # Motor/cognitive beta (13-30 Hz)
    'gamma': 60.0,         # Conscious processing gamma (30-100 Hz)
}

# Phase relationship offsets (radians)
PHASE_OFFSETS = {
    'cardiac_to_cortex': 0.0,          # Heart beat aligned
    'respiratory_to_hippocampus': 0.5, # Breathing gates theta
    'theta_to_gamma': 0.0,             # Theta-gamma coupling
    'alpha_to_dmn': 0.0,               # Alpha in DMN
}

__all__ = [
    'ConsciousSNNConfig',
    'ScaleParams',
    'ComputeConfig',
    'AdaptiveExpLIF',
    'IzhikevichNeuron',
    'OscillatoryNeuron',
    'CardiacNeuron',
    'RespiratoryNeuron',
    'SystemPopulation',
    'ConsciousNetwork',
    'IntentInput',
    'InfluenceMatrix',
    'DEFAULT_CONFIG',
    'SYSTEM_NEURON_COUNTS',
    'OSCILLATION_FREQUENCIES',
    'PHASE_OFFSETS',
]
