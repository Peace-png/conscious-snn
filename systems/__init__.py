"""
Systems Package - All 8 Biological Systems

Each system module defines a complete neural population with:
- Biologically accurate neuron counts (scaled)
- Correct oscillation frequencies
- Internal connectivity
- Inter-system connection interfaces
"""

from .brainstem import BrainstemSystem
from .cardiac import CardiacSystem
from .respiratory import RespiratorySystem
from .limbic import LimbicSystem
from .hippocampus import HippocampusSystem
from .prefrontal import PrefrontalSystem
from .thalamus import ThalamusSystem
from .dmn import DMNSystem

__all__ = [
    'BrainstemSystem',
    'CardiacSystem',
    'RespiratorySystem',
    'LimbicSystem',
    'HippocampusSystem',
    'PrefrontalSystem',
    'ThalamusSystem',
    'DMNSystem',
]

# System configuration summary
SYSTEM_INFO = {
    'brainstem': {
        'class': BrainstemSystem,
        'neurons': 100_000_000,
        'oscillation': '0.5-2 Hz (autonomic)',
        'function': 'Autonomic floor, arousal',
    },
    'cardiac': {
        'class': CardiacSystem,
        'neurons': 40_000,
        'oscillation': '~1 Hz (cardiac rhythm)',
        'function': 'HRV, vagal communication',
    },
    'respiratory': {
        'class': RespiratorySystem,
        'neurons': 10_000,
        'oscillation': '~0.25 Hz (breathing)',
        'function': 'Breathing rhythm',
    },
    'limbic': {
        'class': LimbicSystem,
        'neurons': 130_000_000,
        'oscillation': '4-8 Hz (theta)',
        'function': 'Emotional weighting',
    },
    'hippocampus': {
        'class': HippocampusSystem,
        'neurons': 30_000_000,
        'oscillation': '4-12 Hz (theta)',
        'function': 'Memory consolidation',
    },
    'prefrontal': {
        'class': PrefrontalSystem,
        'neurons': 200_000_000,
        'oscillation': '30-100 Hz (gamma)',
        'function': 'Top-down modulation',
    },
    'thalamus': {
        'class': ThalamusSystem,
        'neurons': 10_000_000,
        'oscillation': '8-12 Hz (alpha)',
        'function': 'Relay, alpha generation',
    },
    'dmn': {
        'class': DMNSystem,
        'neurons': 50_000_000,
        'oscillation': '8-12 Hz (alpha)',
        'function': 'Rest state, default mode',
    },
}
