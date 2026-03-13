"""
Configuration for Conscious SNN Architecture

Biological parameters derived from neuroscience literature.
All parameters are scaled for simulation efficiency while preserving
essential dynamics (the pattern, not the simulation).
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
import numpy as np


@dataclass
class NeuronParams:
    """Base neuron parameters"""
    # Membrane parameters
    tau_m: float = 20.0          # ms, membrane time constant
    tau_e: float = 5.0           # ms, excitatory synaptic time constant
    tau_i: float = 10.0          # ms, inhibitory synaptic time constant

    # Threshold and reset
    v_thresh: float = -50.0      # mV, spike threshold
    v_reset: float = -65.0       # mV, reset potential
    v_rest: float = -65.0        # mV, resting potential

    # Refractory period
    tau_refrac: float = 2.0      # ms, absolute refractory

    # Adaptation (for AdEx)
    a: float = 0.0               # nS, adaptation coupling
    b: float = 0.08              # nA, spike-triggered adaptation
    tau_w: float = 100.0         # ms, adaptation time constant


@dataclass
class AdExParams(NeuronParams):
    """Adaptive Exponential LIF parameters"""
    # Delta_T for exponential
    delta_T: float = 2.0         # mV, slope factor

    # Izhikevich-equivalent parameters
    C: float = 281.0             # pF, membrane capacitance
    g_L: float = 30.0            # nS, leak conductance


@dataclass
class OscillationParams:
    """Parameters for oscillatory dynamics"""
    frequency: float             # Hz, target frequency
    phase_offset: float = 0.0    # radians, phase offset
    amplitude: float = 1.0       # relative amplitude
    coupling_strength: float = 0.1  # coupling to other systems
    entrainment_rate: float = 0.05  # how fast it locks to external drive


@dataclass
class PlasticityParams:
    """STDP and homeostatic plasticity parameters"""
    # STDP timing
    tau_stdp_pre: float = 20.0   # ms, pre-before-post window
    tau_stdp_post: float = 20.0  # ms, post-before-pre window

    # STDP amplitudes
    A_pre: float = 0.01          # LTP amplitude (pre before post)
    A_post: float = -0.0105      # LTD amplitude (post before pre)

    # Weight bounds
    w_max: float = 1.0           # maximum synaptic weight
    w_min: float = 0.0           # minimum synaptic weight

    # Homeostatic
    target_rate: float = 5.0     # Hz, target firing rate
    tau_homeo: float = 10000.0   # ms, homeostatic timescale


@dataclass
class ConnectivityParams:
    """Inter-system connectivity parameters"""
    connection_prob: float       # probability of connection
    weight_mean: float           # mean synaptic weight
    weight_std: float            # std of synaptic weight
    delay_mean: float            # ms, mean delay
    delay_std: float             # ms, std of delay

    # Sparse connectivity
    sparse: bool = True          # use sparse matrices


@dataclass
class ScaleParams:
    """Descaling/scaling parameters"""
    scale_factor: float = 1.0    # 1.0 = full scale, 0.01 = 1%
    preserve_oscillations: bool = True
    preserve_connectivity: bool = True
    min_neurons_per_pop: int = 10  # minimum neurons in any population


@dataclass
class ComputeConfig:
    """Compute backend configuration for Brian2 acceleration.

    Based on RESEARCH_GPU_CPU_ACCELERATION.md:
    - cpp_standalone: CPU with OpenMP multi-threading (recommended)
    - cuda_standalone: NVIDIA GPU via Brian2CUDA
    - genn: NVIDIA GPU via GeNN
    - cython: Runtime compilation (default, slower)
    """
    backend: str = 'cpp_standalone'  # 'cpp_standalone', 'cuda_standalone', 'genn', 'cython'
    openmp_threads: int = 8
    output_directory: str = 'output'
    build_on_run: bool = True

    # Compiler optimization flags
    extra_compile_args: List[str] = field(default_factory=lambda: [
        '-O3', '-march=native', '-ffast-math'
    ])

    def validate(self) -> bool:
        """Validate backend selection."""
        valid = ['cpp_standalone', 'cuda_standalone', 'genn', 'cython']
        return self.backend in valid


@dataclass
class ConsciousSNNConfig:
    """Main configuration class"""

    # Simulation parameters
    dt: float = 0.1              # ms, simulation timestep
    duration: float = 10000.0    # ms, default simulation duration

    # Random seed
    seed: int = 42

    # Output settings
    record_spikes: bool = True
    record_states: bool = True
    output_dir: str = "./output"

    # Scale
    scale: ScaleParams = field(default_factory=ScaleParams)

    # Compute backend
    compute: ComputeConfig = field(default_factory=ComputeConfig)

    # Neuron parameters by system
    neuron_params: Dict[str, NeuronParams] = field(default_factory=lambda: {
        'brainstem': NeuronParams(tau_m=30.0, v_thresh=-48.0),
        'cardiac': NeuronParams(tau_m=100.0, v_thresh=-45.0, tau_refrac=200.0),
        'respiratory': NeuronParams(tau_m=200.0, v_thresh=-50.0, tau_refrac=500.0),
        'limbic': NeuronParams(tau_m=15.0, v_thresh=-52.0),
        'hippocampus': NeuronParams(tau_m=20.0, v_thresh=-50.0),
        'prefrontal': NeuronParams(tau_m=20.0, v_thresh=-50.0),
        'thalamus': NeuronParams(tau_m=25.0, v_thresh=-50.0),
        'dmn': NeuronParams(tau_m=25.0, v_thresh=-50.0),
    })

    # Oscillation parameters by system
    oscillation_params: Dict[str, OscillationParams] = field(default_factory=lambda: {
        'brainstem': OscillationParams(frequency=0.5, amplitude=0.5),
        'cardiac': OscillationParams(frequency=1.0, amplitude=1.0),
        'respiratory': OscillationParams(frequency=0.25, amplitude=0.8),
        'limbic': OscillationParams(frequency=6.0, amplitude=0.7),
        'hippocampus': OscillationParams(frequency=6.0, amplitude=0.9),
        'prefrontal': OscillationParams(frequency=60.0, amplitude=0.6),
        'thalamus': OscillationParams(frequency=10.0, amplitude=0.8),
        'dmn': OscillationParams(frequency=10.0, amplitude=0.7),
    })

    # Plasticity settings
    plasticity: PlasticityParams = field(default_factory=PlasticityParams)

    # Connectivity matrix (influence weights between systems)
    # Rows: source, Columns: target
    # Systems: brainstem, cardiac, respiratory, limbic, hippocampus, prefrontal, thalamus, dmn
    # REDUCED weights globally for numerical stability
    influence_matrix: np.ndarray = field(default_factory=lambda: np.array([
        # brain  cardi  resp   limbic hippo  pfc    thal   dmn
        [0.0,    0.5,   0.6,   0.3,   0.2,   0.2,   0.1,   0.1],  # brainstem -> *
        [0.2,    0.0,   0.1,   0.05,  0.05,  0.1,   0.03,  0.05], # cardiac -> *
        [0.1,    0.05,  0.0,   0.1,   0.3,   0.05,  0.03,  0.05], # respiratory -> *
        [0.2,    0.05,  0.05,  0.2,   0.25,  0.4,   0.05,  0.2],  # limbic -> *
        [0.05,   0.05,  0.1,   0.2,   0.1,   0.3,   0.05,  0.1],  # hippocampus -> *
        [0.1,    0.05,  0.05,  0.5,   0.2,   0.1,   0.05,  0.2],  # prefrontal -> *
        [0.1,    0.05,  0.05,  0.1,   0.1,   0.4,   0.05,  0.3],  # thalamus -> *
        [0.05,   0.05,  0.05,  0.05,  0.05,  0.2,   0.05,  0.1],  # dmn -> *
    ]))

    # System names for indexing
    system_names: List[str] = field(default_factory=lambda: [
        'brainstem', 'cardiac', 'respiratory', 'limbic',
        'hippocampus', 'prefrontal', 'thalamus', 'dmn'
    ])

    # Neuron counts (can be scaled)
    neuron_counts: Dict[str, int] = field(default_factory=lambda: {
        'brainstem': 100_000,
        'cardiac': 40_000,
        'respiratory': 10_000,
        'limbic': 130_000,
        'hippocampus': 30_000,
        'prefrontal': 200_000,
        'thalamus': 10_000,
        'dmn': 50_000,
    })

    def get_scaled_counts(self) -> Dict[str, int]:
        """Get neuron counts scaled by scale_factor"""
        scale = self.scale.scale_factor
        min_n = self.scale.min_neurons_per_pop
        return {
            name: max(min_n, int(count * scale))
            for name, count in self.neuron_counts.items()
        }

    def get_influence(self, source: str, target: str) -> float:
        """Get influence weight between two systems"""
        i = self.system_names.index(source)
        j = self.system_names.index(target)
        return self.influence_matrix[i, j]

    def to_dict(self) -> dict:
        """Export configuration as dictionary"""
        return {
            'dt': self.dt,
            'duration': self.duration,
            'seed': self.seed,
            'scale_factor': self.scale.scale_factor,
            'compute_backend': self.compute.backend,
            'openmp_threads': self.compute.openmp_threads,
            'neuron_counts': self.get_scaled_counts(),
            'oscillation_params': {
                k: {'frequency': v.frequency, 'phase_offset': v.phase_offset}
                for k, v in self.oscillation_params.items()
            },
            'influence_matrix': self.influence_matrix.tolist(),
            'system_names': self.system_names,
        }
