"""
Coupling Configuration for 8-System Conscious SNN

Based on COUPLED_OSCILLATOR_STABILITY_RESEARCH.md

Implements:
- Distance-based delays
- Competitive normalization
- System-specific connectivity probabilities
- Cross-frequency coupling parameters
"""

import numpy as np
from dataclasses import dataclass
from typing import Dict, Tuple, List

# System oscillation frequencies (Hz)
OSCILLATION_FREQUENCIES = {
    'brainstem': 1.0,      # 0.5-2 Hz autonomic
    'cardiac': 1.0,        # ~1 Hz cardiac rhythm
    'respiratory': 0.25,   # ~0.25 Hz breathing
    'limbic': 6.0,         # 4-8 Hz theta
    'hippocampus': 8.0,    # 4-12 Hz theta
    'prefrontal': 40.0,    # 30-100 Hz gamma
    'thalamus': 10.0,      # 8-12 Hz alpha
    'dmn': 10.0,           # 8-12 Hz alpha
}

# Anatomical distances (arbitrary units, ~mm)
# Based on human brain anatomy
ANATOMICAL_DISTANCES = {
    # Brainstem to other regions (brainstem is central)
    ('brainstem', 'thalamus'): 50,
    ('brainstem', 'cardiac'): 300,      # Vagus nerve path
    ('brainstem', 'respiratory'): 10,   # Local brainstem
    ('brainstem', 'limbic'): 60,
    ('brainstem', 'hippocampus'): 70,
    ('brainstem', 'prefrontal'): 100,
    ('brainstem', 'dmn'): 80,

    # Thalamus connections (relay center)
    ('thalamus', 'prefrontal'): 50,
    ('thalamus', 'limbic'): 40,
    ('thalamus', 'hippocampus'): 50,
    ('thalamus', 'dmn'): 30,
    ('thalamus', 'cardiac'): 250,
    ('thalamus', 'respiratory'): 60,

    # Limbic system
    ('limbic', 'hippocampus'): 20,
    ('limbic', 'prefrontal'): 40,
    ('limbic', 'dmn'): 30,
    ('limbic', 'cardiac'): 200,
    ('limbic', 'respiratory'): 70,

    # Hippocampus
    ('hippocampus', 'prefrontal'): 60,
    ('hippocampus', 'dmn'): 40,
    ('hippocampus', 'cardiac'): 220,
    ('hippocampus', 'respiratory'): 80,

    # Prefrontal
    ('prefrontal', 'dmn'): 30,
    ('prefrontal', 'cardiac'): 250,
    ('prefrontal', 'respiratory'): 90,

    # DMN
    ('dmn', 'cardiac'): 230,
    ('dmn', 'respiratory'): 85,

    # Cardiac/Respiratory feedback
    ('cardiac', 'respiratory'): 50,  # Coupled rhythms
}


@dataclass
class CouplingConfig:
    """Configuration for inter-system coupling."""
    source: str
    target: str
    influence_weight: float
    delay_min_ms: float
    delay_max_ms: float
    connectivity_prob: float
    cross_frequency_coupling: bool = False
    description: str = ""


def compute_delay(distance: float, conduction_velocity: float = 0.2) -> Tuple[float, float]:
    """
    Compute delay range from anatomical distance.

    Args:
        distance: Anatomical distance in arbitrary units
        conduction_velocity: mm/ms (0.2 = 5 m/s, typical for unmyelinated)

    Returns:
        (min_delay_ms, max_delay_ms) tuple
    """
    base_delay = distance * conduction_velocity
    # Add variability: +/- 30%
    min_delay = base_delay * 0.7
    max_delay = base_delay * 1.3
    # Minimum 1ms for synaptic delay
    return max(1.0, min_delay), max(1.5, max_delay)


def get_distance(source: str, target: str) -> float:
    """Get anatomical distance between systems."""
    # Check both orderings
    if (source, target) in ANATOMICAL_DISTANCES:
        return ANATOMICAL_DISTANCES[(source, target)]
    if (target, source) in ANATOMICAL_DISTANCES:
        return ANATOMICAL_DISTANCES[(target, source)]
    # Default: moderate distance
    return 50.0


# System-specific connectivity probabilities
# Based on anatomical projection patterns
CONNECTIVITY_PROB = {
    'brainstem': 0.03,    # Diffuse modulatory projections
    'thalamus': 0.02,     # Specific relay projections
    'hippocampus': 0.015, # Sparse but targeted (Schaffer collaterals)
    'prefrontal': 0.015,  # Highly selective executive connections
    'limbic': 0.02,       # Moderate density
    'dmn': 0.025,         # Hub-like connectivity
    'cardiac': 0.005,     # Very limited CNS projections (vagal afferents)
    'respiratory': 0.005, # Very limited CNS projections
}


def create_coupling_configurations() -> List[CouplingConfig]:
    """
    Create all inter-system coupling configurations.

    Based on biological connectivity patterns and stability analysis.
    """
    configs = []

    # Influence matrix from biological literature
    # (source, target, weight, description)
    CONNECTIONS = [
        # Brainstem outputs (autonomic floor, arousal)
        ('brainstem', 'thalamus', 0.7, 'Ascending arousal to relay'),
        ('brainstem', 'cardiac', 0.8, 'Vagal cardiac control'),
        ('brainstem', 'respiratory', 0.9, 'Respiratory rhythm drive'),
        ('brainstem', 'limbic', 0.5, 'Emotional arousal'),
        ('brainstem', 'prefrontal', 0.4, 'Cortical arousal'),
        ('brainstem', 'hippocampus', 0.3, 'Memory consolidation arousal'),
        ('brainstem', 'dmn', 0.2, 'Wakefulness modulation'),

        # Cardiac feedback (heartbeat -> brain)
        ('cardiac', 'brainstem', 0.3, 'Baroreceptor feedback'),
        ('cardiac', 'limbic', 0.1, 'Heart-brain emotional signaling'),
        ('cardiac', 'insular', 0.2, 'Interoceptive awareness'),

        # Respiratory-brain coupling (breathing rhythm -> cognition)
        ('respiratory', 'brainstem', 0.2, 'Respiratory feedback'),
        ('respiratory', 'hippocampus', 0.5, 'Nasal breathing -> memory'),
        ('respiratory', 'limbic', 0.2, 'Breathing -> emotion'),

        # Limbic system (emotion center)
        ('limbic', 'prefrontal', 0.6, 'Emotional modulation of cognition'),
        ('limbic', 'hippocampus', 0.4, 'Emotional memory encoding'),
        ('limbic', 'brainstem', 0.3, 'Autonomic emotional response'),
        ('limbic', 'dmn', 0.3, 'Self-referential emotion'),
        ('limbic', 'thalamus', 0.2, 'Emotional sensory gating'),

        # Hippocampus (memory center)
        ('hippocampus', 'prefrontal', 0.5, 'Memory-guided behavior'),
        ('hippocampus', 'limbic', 0.3, 'Memory-emotion binding'),
        ('hippocampus', 'thalamus', 0.3, 'Theta coordination'),
        ('hippocampus', 'dmn', 0.2, 'Autobiographical memory'),
        ('hippocampus', 'brainstem', 0.1, 'Memory consolidation state'),

        # Prefrontal cortex (executive center)
        ('prefrontal', 'limbic', 0.8, 'Top-down emotional regulation'),
        ('prefrontal', 'thalamus', 0.4, 'Attentional gating'),
        ('prefrontal', 'hippocampus', 0.3, 'Working memory encoding'),
        ('prefrontal', 'brainstem', 0.2, 'Voluntary autonomic control'),
        ('prefrontal', 'dmn', 0.3, 'Task-positive/DMN switching'),

        # Thalamus (relay center)
        ('thalamus', 'prefrontal', 0.6, 'Cortical relay'),
        ('thalamus', 'dmn', 0.5, 'Alpha coordination'),
        ('thalamus', 'limbic', 0.2, 'Emotional relay'),
        ('thalamus', 'hippocampus', 0.2, 'Memory relay'),
        ('thalamus', 'brainstem', 0.2, 'Arousal relay'),

        # Default Mode Network (rest state)
        ('dmn', 'prefrontal', 0.3, 'Self-referential thought'),
        ('dmn', 'hippocampus', 0.2, 'Autobiographical memory'),
        ('dmn', 'limbic', 0.1, 'Self-related emotion'),
        ('dmn', 'thalamus', 0.3, 'Alpha rhythm coordination'),
        ('dmn', 'brainstem', 0.1, 'Rest-state arousal'),
    ]

    for source, target, weight, desc in CONNECTIONS:
        distance = get_distance(source, target)
        delay_min, delay_max = compute_delay(distance)
        conn_prob = min(CONNECTIVITY_PROB.get(source, 0.02),
                       CONNECTIVITY_PROB.get(target, 0.02))

        # Determine cross-frequency coupling
        freq_source = OSCILLATION_FREQUENCIES.get(source, 10)
        freq_target = OSCILLATION_FREQUENCIES.get(target, 10)
        # Cross-frequency if ratios are approximately 1:2, 1:3, 1:4, etc.
        cfc = False
        if freq_source > 0 and freq_target > 0:
            ratio = max(freq_source, freq_target) / min(freq_source, freq_target)
            cfc = 1.5 < ratio < 5.0  # Theta-gamma, alpha-gamma coupling

        configs.append(CouplingConfig(
            source=source,
            target=target,
            influence_weight=weight,
            delay_min_ms=delay_min,
            delay_max_ms=delay_max,
            connectivity_prob=conn_prob,
            cross_frequency_coupling=cfc,
            description=desc
        ))

    return configs


def compute_stability_metrics(configs: List[CouplingConfig]) -> Dict[str, float]:
    """
    Compute stability metrics for the coupling configuration.

    Returns:
        Dictionary with stability indicators
    """
    metrics = {}

    # Compute per-system loop gain (sum of incoming weights * connectivity)
    systems = set()
    for c in configs:
        systems.add(c.source)
        systems.add(c.target)

    incoming_gain = {s: 0.0 for s in systems}
    outgoing_gain = {s: 0.0 for s in systems}

    for c in configs:
        outgoing_gain[c.source] += c.influence_weight * c.connectivity_prob
        incoming_gain[c.target] += c.influence_weight * c.connectivity_prob

    metrics['incoming_gain'] = incoming_gain
    metrics['outgoing_gain'] = outgoing_gain

    # Maximum loop gain (should be < 1 for stability)
    max_gain = max(incoming_gain.values())
    metrics['max_loop_gain'] = max_gain
    metrics['is_stable'] = max_gain < 1.0

    # Average delay
    avg_delay = np.mean([(c.delay_min_ms + c.delay_max_ms) / 2 for c in configs])
    metrics['average_delay_ms'] = avg_delay

    # Frequency spread
    freqs = list(OSCILLATION_FREQUENCIES.values())
    metrics['frequency_spread_hz'] = max(freqs) - min(freqs)

    # Kuramoto critical coupling estimate
    gamma = np.std(freqs)
    metrics['kuramoto_k_critical'] = 2 * gamma
    metrics['avg_coupling'] = np.mean([c.influence_weight for c in configs])
    metrics['below_critical'] = metrics['avg_coupling'] < metrics['kuramoto_k_critical']

    return metrics


# Pre-computed configurations
COUPLING_CONFIGS = create_coupling_configurations()

# Pre-computed stability metrics
STABILITY_METRICS = compute_stability_metrics(COUPLING_CONFIGS)


if __name__ == '__main__':
    print("=" * 60)
    print("Coupling Configuration Summary")
    print("=" * 60)

    print(f"\nTotal connections: {len(COUPLING_CONFIGS)}")

    print("\nStability Metrics:")
    for key, value in STABILITY_METRICS.items():
        if key in ['incoming_gain', 'outgoing_gain']:
            print(f"  {key}:")
            for sys, gain in sorted(value.items(), key=lambda x: -x[1]):
                print(f"    {sys}: {gain:.3f}")
        elif isinstance(value, bool):
            print(f"  {key}: {value} {'[OK]' if value else '[WARNING]'}")
        else:
            print(f"  {key}: {value:.3f}")

    print("\nSample Connections (sorted by weight):")
    sorted_configs = sorted(COUPLING_CONFIGS, key=lambda c: -c.influence_weight)
    for c in sorted_configs[:10]:
        print(f"  {c.source:15} -> {c.target:15}: w={c.influence_weight:.2f}, "
              f"d=[{c.delay_min_ms:.1f}-{c.delay_max_ms:.1f}]ms, p={c.connectivity_prob:.3f}")
        print(f"    {c.description}")
