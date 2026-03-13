"""
Limbic System

Emotional processing and valuation system.
Includes amygdala, anterior cingulate cortex (ACC).

~130M neurons with theta oscillation (4-8Hz).

Key features:
- Emotional valence encoding
- Amygdala-PFC bidirectional connection
- Threat/reward processing
"""

from brian2 import (
    NeuronGroup, Synapses, PoissonGroup, PoissonInput, SpikeMonitor, StateMonitor,
    Hz, ms, mV, nA, nS, pA
)
import numpy as np
from core.neurons import AdaptiveExpLIF, OscillatoryNeuron


class LimbicSystem:
    """
    Limbic system for emotional processing.

    ~130M neurons (abstracted to configurable scale)
    Oscillation: Theta 4-8Hz

    Subregions:
    - Basolateral amygdala: ~8M neurons (sensory integration)
    - Central amygdala: ~1M neurons (output to brainstem)
    - Anterior cingulate cortex: ~120M neurons (evaluation, conflict)
    """

    # Subregion ratios
    RATIOS = {
        'basolateral_amygdala': 0.07,  # ~8M / 130M
        'central_amygdala': 0.008,     # ~1M / 130M
        'acc': 0.922,                  # ~120M / 130M
    }

    def __init__(self, n_neurons: int, name: str = 'limbic'):
        self.n_neurons = n_neurons
        self.name = name

        # Calculate subregion sizes
        self.n_bl_amygdala = max(1, int(n_neurons * self.RATIOS['basolateral_amygdala']))
        self.n_ce_amygdala = max(1, int(n_neurons * self.RATIOS['central_amygdala']))
        self.n_acc = n_neurons - self.n_bl_amygdala - self.n_ce_amygdala

        # Neuron groups
        self.basolateral_amygdala = None
        self.central_amygdala = None
        self.acc = None
        self.monitors = {}

        # State variables
        self.emotional_valence = 0.0  # -1 (negative) to +1 (positive)
        self.arousal_level = 0.5

    def build(self) -> 'LimbicSystem':
        """Build the limbic populations."""

        # Basolateral amygdala - sensory integration and emotional learning
        # Receives sensory input, assigns emotional significance
        self.basolateral_amygdala = OscillatoryNeuron.create_group(
            self.n_bl_amygdala,
            frequency=6*Hz,  # Theta rhythm
            name=f'{self.name}_bl_amygdala',
            params={
                'A_osc': 35*mV,  # Needs 35mV for tau_m=25ms
                'tau_m': 25*ms,
            }
        )

        # Central amygdala - output to autonomic/behavioral systems
        # Generates fear responses, autonomic outputs
        self.central_amygdala = NeuronGroup(
            self.n_ce_amygdala,
            model='''
            dv/dt = (v_rest - v + I_bl + I_pfc + I_osc) / tau_m : volt (unless refractory)
            dI_bl/dt = -I_bl / (20*ms) : volt
            dI_pfc/dt = -I_pfc / (30*ms) : volt
            I_osc = A_osc * sin(2*pi*f_theta*t) : volt
            tau_m : second
            v_rest : volt
            v_thresh : volt
            A_osc : volt
            f_theta : Hz
            emotional_output : 1 (shared)
            ''',
            threshold='v > v_thresh',
            reset='v = v_rest',
            refractory=10*ms,
            method='euler',
            name=f'{self.name}_ce_amygdala'
        )
        self.central_amygdala.tau_m = 30*ms
        self.central_amygdala.v_rest = -65*mV
        self.central_amygdala.v_thresh = -50*mV
        self.central_amygdala.v = -65*mV
        self.central_amygdala.A_osc = 5*mV
        self.central_amygdala.f_theta = 6*Hz
        self.central_amygdala.I_bl = 0*mV
        self.central_amygdala.I_pfc = 0*mV
        self.central_amygdala.emotional_output = 0

        # Anterior cingulate cortex - evaluation, conflict monitoring
        # Higher cognitive aspects of emotion
        self.acc = AdaptiveExpLIF.create_group(
            self.n_acc,
            name=f'{self.name}_acc',
            params={
                'tau_w': 200*ms,
                'a': 2,
                'b': 50*mV,
            }
        )

        # CRITICAL: Add spontaneous background drive to ACC
        # ACC has no intrinsic drive - needs background noise
        self.acc_noise = PoissonInput(
            self.acc, 'I_ext', N=10, rate=200*Hz, weight=1.5*mV
        )

        # Amygdala internal connectivity
        # BL → CE (fear conditioning pathway)
        self.bl_to_ce = Synapses(
            self.basolateral_amygdala, self.central_amygdala,
            model='w_syn : volt',
            on_pre='I_exc_post += w_syn',
            delay=5*ms,
            name=f'{self.name}_bl_ce'
        )
        self.bl_to_ce.connect(p=0.2)
        self.bl_to_ce.w_syn = 5*mV  # Reduced from 8*mV for stability

        # ACC ↔ Amygdala bidirectional
        # ACC modulates amygdala (top-down emotional regulation)
        self.acc_to_bl = Synapses(
            self.acc, self.basolateral_amygdala,
            model='w_syn : volt',
            on_pre='I_exc_post += w_syn',
            delay=10*ms,
            name=f'{self.name}_acc_bl'
        )
        self.acc_to_bl.connect(p=0.05)
        self.acc_to_bl.w_syn = 2*mV  # Reduced from 3*mV for stability

        # Amygdala → ACC (emotional input to cognition)
        self.bl_to_acc = Synapses(
            self.basolateral_amygdala, self.acc,
            model='w_syn : amp',
            on_pre='I_exc_post += w_syn',
            delay=8*ms,
            name=f'{self.name}_bl_acc'
        )
        self.bl_to_acc.connect(p=0.03)
        self.bl_to_acc.w_syn = 0.3*nA  # Reduced from 0.5*nA for stability

        # ACC recurrent connectivity (working memory-like)
        self.acc_recurrent = Synapses(
            self.acc, self.acc,
            model='w_syn : amp',
            on_pre='I_exc_post += w_syn',
            delay=5*ms,
            name=f'{self.name}_acc_recurrent'
        )
        self.acc_recurrent.connect(p=0.02)
        self.acc_recurrent.w_syn = 0.1*nA  # Reduced from 0.2*nA for stability

        # POST-STEP CLAMPING (Critical for NaN prevention)
        self.basolateral_amygdala.run_regularly('''
v = clip(v, -75*mV, -40*mV)
I_osc = clip(I_osc, -5*mV, 40*mV)
I_exc = clip(I_exc, -20*mV, 30*mV)
I_inh = clip(I_inh, -25*mV, 10*mV)
I_ext = clip(I_ext, -5*mV, 35*mV)
''', dt=1*ms)

        self.central_amygdala.run_regularly('''
v = clip(v, -75*mV, -40*mV)
I_bl = clip(I_bl, -20*mV, 30*mV)
I_pfc = clip(I_pfc, -20*mV, 30*mV)
''', dt=1*ms)

        self.acc.run_regularly('''
v = clip(v, -75*mV, -30*mV)
w = clip(w, -20*mV, 20*mV)
I_exc = clip(I_exc, -20*mV, 30*mV)
I_inh = clip(I_inh, -25*mV, 10*mV)
I_ext = clip(I_ext, -5*mV, 35*mV)
''', dt=1*ms)

        # Add monitors
        self.monitors['bl_spikes'] = SpikeMonitor(
            self.basolateral_amygdala, name=f'{self.name}_bl_spikes'
        )
        self.monitors['ce_spikes'] = SpikeMonitor(
            self.central_amygdala, name=f'{self.name}_ce_spikes'
        )
        self.monitors['acc_spikes'] = SpikeMonitor(
            self.acc, name=f'{self.name}_acc_spikes'
        )

        return self

    def get_groups(self):
        """Get all neuron groups."""
        return {
            'basolateral_amygdala': self.basolateral_amygdala,
            'central_amygdala': self.central_amygdala,
            'acc': self.acc,
        }

    def get_monitors(self):
        """Get all monitors."""
        return self.monitors

    def get_inputs(self):
        """Get all input objects (PoissonInput, etc.)."""
        return {
            'acc_noise': self.acc_noise,
        }

    def set_emotional_valence(self, valence: float):
        """Set emotional valence (-1 negative to +1 positive)."""
        self.emotional_valence = np.clip(valence, -1.0, 1.0)

        # Modulate BL amygdala activity based on valence
        if self.basolateral_amygdala is not None:
            if valence > 0:
                # Positive: moderate increase in I_ext
                self.basolateral_amygdala.I_exc = f'{valence * 2}*mV'
            else:
                # Negative: stronger response (negativity bias)
                self.basolateral_amygdala.I_exc = f'{-valence * 3}*mV'

    def set_arousal(self, level: float):
        """Set arousal level (0=calm, 1=highly aroused)."""
        self.arousal_level = np.clip(level, 0.0, 1.0)

        # Increase oscillation amplitude with arousal
        if self.central_amygdala is not None:
            self.central_amygdala.A_osc = f'{5 + level * 10}*mV'

    def get_emotional_output(self) -> float:
        """Get current emotional output level."""
        if self.central_amygdala is not None:
            return float(self.central_amygdala.emotional_output)
        return 0.0
