"""
Hippocampus

Memory consolidation and spatial navigation system.
~30M neurons with theta oscillation (4-12Hz).

Key features:
- Trisynaptic circuit: EC → DG → CA3 → CA1
- Theta rhythm (4-12Hz)
- Sharp wave ripples during rest
- Respiratory-hippocampal coupling
"""

from brian2 import (
    NeuronGroup, Synapses, PoissonGroup, PoissonInput, SpikeMonitor, StateMonitor,
    Hz, ms, mV, nA, nS, pA
)
import numpy as np
from core.neurons import AdaptiveExpLIF, OscillatoryNeuron, InhibitoryInterneuron


class HippocampusSystem:
    """
    Hippocampal formation.

    ~30M neurons (abstracted to configurable scale)
    Oscillation: Theta 4-12Hz, Sharp waves during rest

    Subregions:
    - Dentate gyrus: ~10M granule cells (pattern separation)
    - CA3: ~3M pyramidal cells (autoassociation)
    - CA1: ~5M pyramidal cells (output, temporal coding)
    - Entorhinal cortex input: ~12M (cortical gateway)
    """

    # Subregion ratios
    RATIOS = {
        'dentate_gyrus': 0.33,     # ~10M / 30M
        'ca3': 0.10,               # ~3M / 30M
        'ca1': 0.17,               # ~5M / 30M
        'entorhinal_input': 0.40,  # ~12M / 30M
    }

    def __init__(self, n_neurons: int, name: str = 'hippocampus'):
        self.n_neurons = n_neurons
        self.name = name

        # Calculate subregion sizes
        self.n_dg = max(1, int(n_neurons * self.RATIOS['dentate_gyrus']))
        self.n_ca3 = max(1, int(n_neurons * self.RATIOS['ca3']))
        self.n_ca1 = max(1, int(n_neurons * self.RATIOS['ca1']))
        self.n_ec = n_neurons - self.n_dg - self.n_ca3 - self.n_ca1

        # Neuron groups
        self.dentate_gyrus = None
        self.ca3 = None
        self.ca1 = None
        self.entorhinal = None
        self.monitors = {}

        # State variables
        self.theta_phase = 0.0
        self.theta_power = 1.0
        self.memory_consolidation_mode = False

    def build(self) -> 'HippocampusSystem':
        """Build the hippocampal populations."""

        # Entorhinal cortex - input layer (grid cells, cortical gateway)
        self.entorhinal = OscillatoryNeuron.create_group(
            self.n_ec,
            frequency=8*Hz,  # Theta rhythm
            name=f'{self.name}_ec',
            params={
                'A_osc': 30*mV,  # Needs 30mV for tau_m=20ms
                'tau_m': 20*ms,
            }
        )

        # Dentate gyrus - pattern separation (sparse coding)
        # Many granule cells, sparse activation
        self.dentate_gyrus = AdaptiveExpLIF.create_group(
            self.n_dg,
            name=f'{self.name}_dg',
            params={
                'tau_w': 100*ms,
                'a': 1,
                'b': 30*mV,
                'v_thresh': -50*mV,  # Lowered for activity (was -45mV)
            }
        )

        # CA3 - autoassociative memory
        # Recurrent collaterals for pattern completion
        self.ca3 = AdaptiveExpLIF.create_group(
            self.n_ca3,
            name=f'{self.name}_ca3',
            params={
                'tau_w': 150*ms,
                'a': 3,
                'b': 60*mV,
            }
        )

        # CA3 basket cells - inhibitory interneurons for stability
        # These provide feedback inhibition to prevent runaway excitation
        from core.neurons import InhibitoryInterneuron
        n_basket = max(1, self.n_ca3 // 5)  # ~20% interneurons (biological ratio)
        self.ca3_basket = InhibitoryInterneuron.create_group(
            n_basket,
            name=f'{self.name}_ca3_basket',
            params={
                'tau_m': 10*ms,  # Fast-spiking
                'v_thresh': -50*mV,
            }
        )

        # CA1 - temporal coding, output
        # Receives from CA3 and EC (direct path)
        self.ca1 = OscillatoryNeuron.create_group(
            self.n_ca1,
            frequency=6*Hz,  # Theta
            name=f'{self.name}_ca1',
            params={
                'A_osc': 35*mV,  # Needs 35mV for tau_m=25ms
                'tau_m': 25*ms,
            }
        )

        # CRITICAL: Add spontaneous background drive to AdaptiveExpLIF populations
        # DG and CA3 have no intrinsic drive - they need background noise
        # Biologically, this represents ongoing synaptic noise from background activity
        self.dg_noise = PoissonInput(
            self.dentate_gyrus, 'I_ext', N=8, rate=150*Hz, weight=1.0*mV
        )
        self.ca3_noise = PoissonInput(
            self.ca3, 'I_ext', N=8, rate=150*Hz, weight=1.0*mV
        )

        # Trisynaptic pathway: EC → DG → CA3 → CA1
        self.ec_to_dg = Synapses(
            self.entorhinal, self.dentate_gyrus,
            model='w_syn : amp',
            on_pre='I_exc_post += w_syn',
            delay=3*ms,
            name=f'{self.name}_ec_dg'
        )
        self.ec_to_dg.connect(p=0.1)
        self.ec_to_dg.w_syn = 0.4*nA  # Reduced from 0.8*nA for stability

        self.dg_to_ca3 = Synapses(
            self.dentate_gyrus, self.ca3,
            model='w_syn : amp',
            on_pre='I_exc_post += w_syn',
            delay=2*ms,
            name=f'{self.name}_dg_ca3'
        )
        self.dg_to_ca3.connect(p=0.3)
        self.dg_to_ca3.w_syn = 0.6*nA  # Reduced from 1.2*nA for stability

        self.ca3_to_ca1 = Synapses(
            self.ca3, self.ca1,
            model='w_syn : volt',
            on_pre='I_exc_post += w_syn',
            delay=5*ms,
            name=f'{self.name}_ca3_ca1'
        )
        self.ca3_to_ca1.connect(p=0.2)
        self.ca3_to_ca1.w_syn = 4*mV  # Reduced from 6*mV for stability

        # Direct EC → CA1 pathway (temporal input)
        self.ec_to_ca1 = Synapses(
            self.entorhinal, self.ca1,
            model='w_syn : volt',
            on_pre='I_exc_post += w_syn',
            delay=5*ms,
            name=f'{self.name}_ec_ca1'
        )
        self.ec_to_ca1.connect(p=0.05)
        self.ec_to_ca1.w_syn = 3*mV  # Reduced from 4*mV for stability

        # CA3 recurrent collaterals (autoassociation)
        self.ca3_recurrent = Synapses(
            self.ca3, self.ca3,
            model='''
            w_syn : amp
            dapre/dt = -apre/tau_pre : 1 (event-driven)
            dapost/dt = -apost/tau_post : 1 (event-driven)
            ''',
            on_pre='''
            I_exc_post += w_syn
            apre += A_pre
            w_syn = clip(w_syn + apost*0.1*nA, 0, w_max)
            ''',
            on_post='''
            apost += A_post
            w_syn = clip(w_syn + apre*0.1*nA, 0, w_max)
            ''',
            delay=3*ms,
            name=f'{self.name}_ca3_recurrent',
            namespace={
                'tau_pre': 20*ms,
                'tau_post': 20*ms,
                'A_pre': 0.005,
                'A_post': -0.00525,
                'w_max': 0.5*nA,  # Reduced from 1*nA
            }
        )
        self.ca3_recurrent.connect(p=0.1)
        self.ca3_recurrent.w_syn = 0.15*nA  # Reduced from 0.3*nA for stability

        # CA3 → Basket cells (excitation - CA3 recruits inhibition)
        self.ca3_to_basket = Synapses(
            self.ca3, self.ca3_basket,
            model='w_syn : volt',
            on_pre='I_exc_post += w_syn',
            delay=1*ms,
            name=f'{self.name}_ca3_basket'
        )
        self.ca3_to_basket.connect(p=0.2)
        self.ca3_to_basket.w_syn = 4*mV

        # Basket → CA3 (inhibition - feedback control)
        self.basket_to_ca3 = Synapses(
            self.ca3_basket, self.ca3,
            model='w_syn : volt',
            on_pre='I_inh_post += w_syn',  # INHIBITORY
            delay=1*ms,
            name=f'{self.name}_basket_ca3'
        )
        self.basket_to_ca3.connect(p=0.3)
        self.basket_to_ca3.w_syn = 6*mV  # Strong inhibition

        # POST-STEP CLAMPING (Critical for NaN prevention)
        self.entorhinal.run_regularly('''
v = clip(v, -80*mV, -30*mV)
I_osc = clip(I_osc, -5*mV, 40*mV)
I_exc = clip(I_exc, -20*mV, 20*mV)
I_inh = clip(I_inh, -20*mV, 20*mV)
I_ext = clip(I_ext, -5*mV, 35*mV)
''', dt=1*ms)

        self.dentate_gyrus.run_regularly('''
v = clip(v, -75*mV, -30*mV)
w = clip(w, -20*mV, 20*mV)
I_exc = clip(I_exc, -20*mV, 30*mV)
I_inh = clip(I_inh, -25*mV, 10*mV)
I_ext = clip(I_ext, -5*mV, 35*mV)
''', dt=1*ms)

        self.ca3.run_regularly('''
v = clip(v, -75*mV, -30*mV)
w = clip(w, -20*mV, 20*mV)
I_exc = clip(I_exc, -20*mV, 30*mV)
I_inh = clip(I_inh, -25*mV, 10*mV)
I_ext = clip(I_ext, -5*mV, 35*mV)
''', dt=1*ms)

        self.ca1.run_regularly('''
v = clip(v, -80*mV, -30*mV)
I_osc = clip(I_osc, -5*mV, 40*mV)
I_exc = clip(I_exc, -20*mV, 20*mV)
I_inh = clip(I_inh, -20*mV, 20*mV)
I_ext = clip(I_ext, -5*mV, 35*mV)
''', dt=1*ms)

        # CA3 basket cells clamping
        self.ca3_basket.run_regularly('''
v = clip(v, -80*mV, -40*mV)
I_exc = clip(I_exc, -20*mV, 30*mV)
I_inh = clip(I_inh, -25*mV, 10*mV)
I_ext = clip(I_ext, -5*mV, 35*mV)
''', dt=1*ms)

        # Add monitors
        self.monitors['ec_spikes'] = SpikeMonitor(
            self.entorhinal, name=f'{self.name}_ec_spikes'
        )
        self.monitors['dg_spikes'] = SpikeMonitor(
            self.dentate_gyrus, name=f'{self.name}_dg_spikes'
        )
        self.monitors['ca3_spikes'] = SpikeMonitor(
            self.ca3, name=f'{self.name}_ca3_spikes'
        )
        self.monitors['ca1_spikes'] = SpikeMonitor(
            self.ca1, name=f'{self.name}_ca1_spikes'
        )

        return self

    def get_groups(self):
        """Get all neuron groups."""
        return {
            'entorhinal': self.entorhinal,
            'dentate_gyrus': self.dentate_gyrus,
            'ca3': self.ca3,
            'ca1': self.ca1,
        }

    def get_monitors(self):
        """Get all monitors."""
        return self.monitors

    def get_inputs(self):
        """Get all input objects (PoissonInput, etc.)."""
        return {
            'dg_noise': self.dg_noise,
            'ca3_noise': self.ca3_noise,
        }

    def set_theta_power(self, power: float):
        """Set theta oscillation power (0-1)."""
        self.theta_power = np.clip(power, 0.0, 1.0)

        # Scale oscillation amplitudes
        if self.entorhinal is not None:
            self.entorhinal.A_osc = f'{10 * power}*mV'
        if self.ca1 is not None:
            self.ca1.A_osc = f'{8 * power}*mV'

    def enable_consolidation_mode(self):
        """Enable sharp wave ripple mode for memory consolidation."""
        self.memory_consolidation_mode = True
        # In reality, this would switch from theta to sharp wave rhythms
        # Simplified: increase CA3 recurrent activity
        if self.ca3_recurrent is not None:
            self.ca3_recurrent.w_syn = self.ca3_recurrent.w * 1.5

    def disable_consolidation_mode(self):
        """Return to normal theta mode."""
        self.memory_consolidation_mode = False
        if self.ca3_recurrent is not None:
            self.ca3_recurrent.w_syn = self.ca3_recurrent.w / 1.5

    def set_respiratory_coupling(self, breath_phase: float):
        """
        Set respiratory coupling to hippocampus.

        Research shows breathing phase affects theta power and memory.
        Peak inspiration → enhanced encoding.
        """
        # Modulate theta power based on breath phase
        # Inspiration (0-0.5) enhances, expiration (0.5-1) reduces slightly
        coupling_factor = 1.0 + 0.2 * np.cos(breath_phase * 2 * np.pi)
        self.set_theta_power(self.theta_power * coupling_factor)
