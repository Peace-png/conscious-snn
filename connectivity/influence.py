"""
Inter-System Influence Matrix

Defines connectivity weights between all 8 systems.
Based on biological connectivity patterns.

The influence matrix is the core of the architecture -
it defines how each system modulates every other.
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


# Anatomically-based delays (from neurophysiology research)
# Distance-based: ~1.5-2.5 m/s conduction velocity for unmyelinated
# ~5-15 m/s for myelinated fibers
ANATOMICAL_DELAYS = {
    # Brainstem connections
    ('brainstem', 'thalamus'): 10.0,  # ms, ~50mm distance
    ('brainstem', 'cardiac'): 60.0,   # ms, ~300mm vagal
    ('brainstem', 'respiratory'): 20.0,  # ms, local brainstem
    ('brainstem', 'limbic'): 15.0,    # ms, ~75mm
    ('brainstem', 'prefrontal'): 25.0,  # ms, ~125mm

    # Thalamus connections
    ('thalamus', 'prefrontal'): 12.0,  # ms, ~60mm
    ('thalamus', 'limbic'): 15.0,     # ms, ~75mm
    ('thalamus', 'hippocampus'): 18.0,  # ms, ~90mm
    ('thalamus', 'dmn'): 12.0,        # ms, ~60mm

    # Limbic connections
    ('limbic', 'prefrontal'): 20.0,   # ms, vmPFC regulation
    ('limbic', 'hippocampus'): 8.0,   # ms, ~40mm
    ('limbic', 'thalamus'): 15.0,     # ms

    # Hippocampus connections
    ('hippocampus', 'prefrontal'): 25.0,  # ms, ~125mm
    ('hippocampus', 'limbic'): 8.0,   # ms
    ('hippocampus', 'dmn'): 20.0,     # ms

    # Prefrontal connections
    ('prefrontal', 'limbic'): 20.0,   # ms, top-down regulation
    ('prefrontal', 'thalamus'): 12.0,  # ms
    ('prefrontal', 'dmn'): 14.0,      # ms, ~70mm

    # DMN connections
    ('dmn', 'thalamus'): 12.0,        # ms
    ('dmn', 'hippocampus'): 20.0,     # ms
    ('dmn', 'prefrontal'): 14.0,      # ms

    # Cardiac/Respiratory (autonomic)
    ('cardiac', 'brainstem'): 60.0,   # ms, afferent
    ('respiratory', 'brainstem'): 20.0,  # ms
    ('cardiac', 'limbic'): 150.0,     # ms, baroreceptor -> NTS -> amygdala
    ('respiratory', 'hippocampus'): 50.0,  # ms, nasal -> olfactory -> entorhinal
}

# Connection probability ranges from research
CONNECTION_PROBABILITIES = {
    'sparse': 0.02,        # Most inter-system connections
    'moderate': 0.08,      # Medium density
    'dense': 0.15,         # Thalamus-cortex, strong pathways
    'very_dense': 0.25,    # Within-system recurrent
}


@dataclass
class SystemConnection:
    """A connection between two systems."""
    source: str
    target: str
    weight: float
    delay_ms: float = 5.0
    plastic: bool = False
    description: str = ""


class InfluenceMatrix:
    """
    Inter-system influence matrix.

    8x8 matrix defining influence weights between systems.
    Diagonal is zero (no self-influence via this mechanism).

    Systems:
    0: brainstem
    1: cardiac
    2: respiratory
    3: limbic
    4: hippocampus
    5: prefrontal
    6: thalamus
    7: dmn
    """

    # Default influence matrix based on biological literature
    DEFAULT_MATRIX = np.array([
        #brain  cardi  resp   limbic hippo  pfc    thal   dmn
        [0.0,   0.8,   0.9,   0.5,   0.3,   0.4,   0.7,   0.2],  # brainstem
        [0.3,   0.0,   0.2,   0.1,   0.1,   0.2,   0.1,   0.1],  # cardiac
        [0.2,   0.1,   0.0,   0.2,   0.5,   0.1,   0.1,   0.1],  # respiratory
        [0.3,   0.1,   0.1,   0.3,   0.4,   0.6,   0.2,   0.3],  # limbic
        [0.1,   0.1,   0.2,   0.3,   0.2,   0.5,   0.3,   0.2],  # hippocampus
        [0.2,   0.1,   0.1,   0.8,   0.3,   0.2,   0.4,   0.3],  # prefrontal
        [0.2,   0.1,   0.1,   0.2,   0.2,   0.6,   0.1,   0.5],  # thalamus
        [0.1,   0.1,   0.1,   0.1,   0.1,   0.3,   0.3,   0.2],  # dmn
    ])

    SYSTEM_NAMES = [
        'brainstem', 'cardiac', 'respiratory', 'limbic',
        'hippocampus', 'prefrontal', 'thalamus', 'dmn'
    ]

    def __init__(self, matrix: np.ndarray = None):
        """
        Initialize influence matrix.

        Args:
            matrix: 8x8 influence weights (0-1)
        """
        self.matrix = matrix.copy() if matrix is not None else self.DEFAULT_MATRIX.copy()
        self.connections: Dict[Tuple[str, str], SystemConnection] = {}

    def get_weight(self, source: str, target: str) -> float:
        """Get influence weight from source to target system."""
        i = self.SYSTEM_NAMES.index(source)
        j = self.SYSTEM_NAMES.index(target)
        return self.matrix[i, j]

    def set_weight(self, source: str, target: str, weight: float):
        """Set influence weight from source to target system."""
        i = self.SYSTEM_NAMES.index(source)
        j = self.SYSTEM_NAMES.index(target)
        self.matrix[i, j] = np.weight

    def get_strongest_pathways(self, n: int = 5) -> List[Tuple[str, str, float]]:
        """
        Get the N strongest inter-system pathways.

        Returns:
            List of (source, target, weight) tuples
        """
        # Flatten and sort
        flat_idx = np.argsort(self.matrix.flatten())[::-1]

        pathways = []
        for idx in flat_idx:
            i, j = divmod(idx, 8)
            if i != j and self.matrix[i, j] > 0:  # Skip diagonal
                pathways.append((
                    self.SYSTEM_NAMES[i],
                    self.SYSTEM_NAMES[j],
                    float(self.matrix[i, j])
                ))
            if len(pathways) >= n:
                break

        return pathways

    def get_system_influence(self, system: str) -> Dict[str, float]:
        """Get all outgoing influence weights for a system."""
        i = self.SYSTEM_NAMES.index(system)
        influences = {}
        for j, target in enumerate(self.SYSTEM_NAMES):
            if i != j and self.matrix[i, j] > 0:
                influences[target] = float(self.matrix[i, j])
        return influences

    def get_system_susceptibility(self, system: str) -> Dict[str, float]:
        """Get all incoming influence weights for a system."""
        j = self.SYSTEM_NAMES.index(system)
        susceptibilities = {}
        for i, source in enumerate(self.SYSTEM_NAMES):
            if i != j and self.matrix[i, j] > 0:
                susceptibilities[source] = float(self.matrix[i, j])
        return susceptibilities

    def export_matrix(self) -> np.ndarray:
        """Export matrix as numpy array."""
        return self.matrix.copy()

    def to_dict(self) -> dict:
        """Export as dictionary."""
        return {
            'system_names': self.SYSTEM_NAMES,
            'matrix': self.matrix.tolist(),
            'strongest_pathways': [
                {'source': s, 'target': t, 'weight': w}
                for s, t, w in self.get_strongest_pathways(20)
            ]
        }


def create_system_connections(source_pop, target_pop,
                              influence_weight: float,
                              connection_prob: float = 0.05,
                              delay_range: Tuple[float, float] = (1.0, 6.0),
                              plastic: bool = False):
    """
    Create synaptic connections between two systems.

    DELAY RECOMMENDATIONS (from anatomical research):
    - brainstem -> thalamus: 7-13ms
    - thalamus -> cortex: 8-15ms
    - hippocampus -> prefrontal: 20-30ms
    - limbic -> prefrontal: 15-25ms
    - intra-cortical: 5-10ms

    CONNECTION PROBABILITY:
    - Sparse connectivity: 0.02-0.10 for inter-system
    - Higher for thalamus-cortex: 0.15-0.25
    """
    """
    Create synaptic connections between two systems.

    This is a factory function that returns Brian2 Synapses.

    Args:
        source_pop: Source neuron group
        target_pop: Target neuron group
        influence_weight: Connection strength (0-1)
        connection_prob: Probability of connection
        delay_range: (min, max) delay in ms
        plastic: Whether to include STDP

    Returns:
        Brian2 Synapses object
    """
    from brian2 import Synapses, ms

    if influence_weight < 0.01:
        return None

    # Synapse model
    if plastic:
        model = '''
        w : 1
        dapre/dt = -apre/tau_pre : 1 (event-driven)
        dapost/dt = -apost/tau_post : 1 (event-driven)
        '''
        on_pre = '''
        I_exc_post += w*nA
        apre += A_pre
        w = w + apost
        '''
        on_post = '''
        apost += A_post
        w = w + apre
        '''
    else:
        model = 'w : 1'
        on_pre = 'I_exc_post += w*nA'

    syn = Synapses(
        source_pop,
        target_pop,
        model=model,
        on_pre=on_pre,
        name=f'syn_{source_pop.name}_to_{target_pop.name}'
    )

    # Connect with probability
    syn.connect(p=connection_prob)

    # Set weights
    syn.w = influence_weight

    # Set delays (random within range)
    min_delay, max_delay = delay_range
    syn.delay = f'{min_delay}*ms + rand()*({max_delay-min_delay})*ms'

    return syn


def compute_influence_signature(spike_times: Dict[str, np.ndarray],
                                influence_matrix: InfluenceMatrix) -> Dict:
    """
    Compute the influence signature from spike data.

    This is the unique timing/influence pattern that characterizes
    the state of conscious processing at a given moment.

    Args:
        spike_times: Dict mapping system name to spike timestamps
        influence_matrix: Inter-system influence weights

    Returns:
        Influence signature dictionary
    """
    signature = {
        'timing': {},
        'cross_correlations': {},
        'phase_coupling': {},
        'dominant_frequencies': {}
    }

    # Per-system timing signature
    for name, times in spike_times.items():
        if len(times) > 10:
            isis = np.diff(np.sort(times))
            signature['timing'][name] = {
                'mean_isi': float(np.mean(isis)),
                'cv_isi': float(np.std(isis) / np.mean(isis)) if np.mean(isis) > 0 else 0,
                'n_spikes': len(times)
            }

    # Cross-correlations between systems
    system_names = influence_matrix.SYSTEM_NAMES
    for i, source in enumerate(system_names):
        for j, target in enumerate(system_names):
            if source in spike_times and target in spike_times:
                weight = influence_matrix.get_weight(source, target)
                if weight > 0.1:
                    # Simplified cross-correlation
                    source_spikes = spike_times[source]
                    target_spikes = spike_times[target]

                    if len(source_spikes) > 0 and len(target_spikes) > 0:
                        # Count coincidences within window
                        window = 0.05  # 50ms
                        coincidences = 0
                        for ts in source_spikes:
                            for tt in target_spikes:
                                if abs(ts - tt) < window:
                                    coincidences += 1

                        total = len(source_spikes) * len(target_spikes)
                        correlation = coincidences / total if total > 0 else 0

                        key = f'{source}_to_{target}'
                        signature['cross_correlations'][key] = {
                            'weight': float(weight),
                            'correlation': float(correlation)
                        }

    return signature
