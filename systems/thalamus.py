"""
Thalamus

Sensory relay and thalamocortical loop system.
~10M neurons with alpha rhythm generation (8-12Hz).

Key features:
- Thalamocortical relay
- Alpha rhythm generation
- Reticular thalamic nucleus (inhibitory gating)
- Sensory relay to cortex
"""

from brian2 import (
    NeuronGroup, Synapses, PoissonGroup, SpikeMonitor, StateMonitor,
    Hz, ms, mV, nA, nS, pA
)
import numpy as np
from core.neurons import OscillatoryNeuron


class ThalamusSystem:
    """
    Thalamic system for relay and rhythm generation.

    ~10M neurons (abstracted to configurable scale)
    Oscillation: Alpha 8-12Hz

    Subregions:
    - Relay nuclei: ~6M (sensory relay)
    - Reticular nucleus: ~2M (inhibitory, gating)
    - Intralaminar nuclei: ~2M (arousal, attention)
    """

    # Subregion ratios
    RATIOS = {
        'relay_nuclei': 0.60,      # ~6M / 10M
        'reticular_nucleus': 0.20, # ~2M / 10M
        'intralaminar': 0.20,      # ~2M / 10M
    }

    def __init__(self, n_neurons: int, name: str = 'thalamus'):
        self.n_neurons = n_neurons
        self.name = name

        # Calculate subregion sizes
        self.n_relay = max(1, int(n_neurons * self.RATIOS['relay_nuclei']))
        self.n_reticular = max(1, int(n_neurons * self.RATIOS['reticular_nucleus']))
        self.n_intralaminar = n_neurons - self.n_relay - self.n_reticular

        # Neuron groups
        self.relay_nuclei = None
        self.reticular_nucleus = None
        self.intralaminar = None
        self.monitors = {}

        # State variables
        self.alpha_power = 1.0
        self.gating_state = 0.5  # 0=closed, 1=open

    def build(self) -> 'ThalamusSystem':
        """Build the thalamic populations."""

        # Relay nuclei - thalamocortical relay neurons
        # Burst firing and tonic firing modes
        self.relay_nuclei = NeuronGroup(
            self.n_relay,
            model='''
            dv/dt = (v_rest - v + I_relay + I_osc + I_cortical + I_brainstem + I_exc - I_inh) / tau_m : volt (unless refractory)
            dI_relay/dt = -I_relay / tau_relay : volt
            dI_osc/dt = (-I_osc + A_alpha * sin(2*pi*f_alpha*t)) / tau_osc : volt
            dI_cortical/dt = -I_cortical / (30*ms) : volt
            dI_brainstem/dt = -I_brainstem / (50*ms) : volt
            dI_exc/dt = -I_exc / tau_e : volt
            dI_inh/dt = -I_inh / tau_i : volt
            dT_ca/dt = -T_ca / (100*ms) : volt  # Low-threshold Ca current
            tau_m : second
            tau_relay : second
            tau_osc : second
            tau_e : second
            tau_i : second
            f_alpha : Hz
            A_alpha : volt
            v_rest : volt
            v_thresh : volt
            v_burst : volt  # Burst threshold
            is_bursting : 1
            gating : 1 (shared)
            ''',
            threshold='v > v_thresh',
            reset='''
            v = v_rest
            T_ca = 10*mV
            ''',
            refractory=5*ms,
            method='euler',
            name=f'{self.name}_relay'
        )
        self.relay_nuclei.tau_m = 20*ms
        self.relay_nuclei.tau_relay = 15*ms
        self.relay_nuclei.tau_osc = 10*ms  # MUST be ≤10ms for oscillation following
        self.relay_nuclei.tau_e = 5*ms
        self.relay_nuclei.tau_i = 10*ms
        self.relay_nuclei.f_alpha = 10*Hz
        self.relay_nuclei.A_alpha = 30*mV  # Needs 30mV for tau_m=20ms
        self.relay_nuclei.v_rest = -65*mV
        self.relay_nuclei.v_thresh = -50*mV
        self.relay_nuclei.v_burst = -60*mV
        self.relay_nuclei.v = -65*mV
        self.relay_nuclei.I_relay = 0*mV
        self.relay_nuclei.I_osc = 0*mV
        self.relay_nuclei.I_cortical = 0*mV
        self.relay_nuclei.I_brainstem = 0*mV
        self.relay_nuclei.I_exc = 0*mV
        self.relay_nuclei.I_inh = 0*mV
        self.relay_nuclei.T_ca = 0*mV
        self.relay_nuclei.is_bursting = 0
        self.relay_nuclei.gating = 0.5

        # Reticular nucleus - GABAergic inhibitory neurons
        # Gating thalamocortical transmission
        self.reticular_nucleus = OscillatoryNeuron.create_group(
            self.n_reticular,
            frequency=10*Hz,  # Alpha rhythm
            name=f'{self.name}_reticular',
            params={
                'A_osc': 25*mV,  # Reduced from 10*mV for stability
                'tau_m': 15*ms,
                'v_thresh': -52*mV,
            }
        )

        # Intralaminar nuclei - arousal, attention modulation
        self.intralaminar = OscillatoryNeuron.create_group(
            self.n_intralaminar,
            frequency=10*Hz,
            name=f'{self.name}_intralaminar',
            params={
                'A_osc': 35*mV,  # Needs 35mV for tau_m=25ms
                'tau_m': 25*ms,
            }
        )

        # Thalamocortical loop connectivity
        # Relay → Reticular (excitation)
        self.relay_to_reticular = Synapses(
            self.relay_nuclei, self.reticular_nucleus,
            model='w_syn : volt',
            on_pre='I_exc_post += w_syn',
            delay=2*ms,
            name=f'{self.name}_relay_ret'
        )
        self.relay_to_reticular.connect(p=0.2)
        self.relay_to_reticular.w_syn = 6*mV

        # Reticular → Relay (inhibition - GABA)
        # CRITICAL: Uses I_inh_post (not I_exc_post) - reticular is GABAergic
        # NOTE: Inhibition must be weak enough to allow oscillation-driven spiking
        # Too strong inhibition (w=8mV, p=0.3) suppresses relay completely
        self.reticular_to_relay = Synapses(
            self.reticular_nucleus, self.relay_nuclei,
            model='w_syn : volt',
            on_pre='I_inh_post += w_syn',  # INHIBITORY - GABA synapses
            delay=3*ms,
            name=f'{self.name}_ret_relay'
        )
        self.reticular_to_relay.connect(p=0.1)  # Reduced from 0.3
        self.reticular_to_relay.w_syn = 2*mV  # Reduced from 8mV for balanced inhibition

        # Intralaminar → Relay (diffuse arousal)
        self.intralaminar_to_relay = Synapses(
            self.intralaminar, self.relay_nuclei,
            model='w_syn : volt',
            on_pre='I_exc_post += w_syn',
            delay=5*ms,
            name=f'{self.name}_intra_relay'
        )
        self.intralaminar_to_relay.connect(p=0.1)
        self.intralaminar_to_relay.w_syn = 4*mV

        # Relay recurrent (for alpha generation)
        self.relay_recurrent = Synapses(
            self.relay_nuclei, self.relay_nuclei,
            model='w_syn : volt',
            on_pre='I_exc_post += w_syn',
            delay=5*ms,
            name=f'{self.name}_relay_recurrent'
        )
        self.relay_recurrent.connect(p=0.05)
        self.relay_recurrent.w_syn = 2*mV

        # POST-STEP CLAMPING (Critical for NaN prevention)
        self.relay_nuclei.run_regularly('''
v = clip(v, -80*mV, -30*mV)
I_relay = clip(I_relay, -20*mV, 30*mV)
I_osc = clip(I_osc, -20*mV, 30*mV)
I_cortical = clip(I_cortical, -20*mV, 30*mV)
I_brainstem = clip(I_brainstem, -20*mV, 30*mV)
I_exc = clip(I_exc, -20*mV, 20*mV)
I_inh = clip(I_inh, -20*mV, 20*mV)
T_ca = clip(T_ca, 0*mV, 15*mV)
''', dt=1*ms)

        self.reticular_nucleus.run_regularly('''
v = clip(v, -80*mV, -30*mV)
I_osc = clip(I_osc, -20*mV, 30*mV)
I_exc = clip(I_exc, -20*mV, 20*mV)
I_inh = clip(I_inh, -20*mV, 20*mV)
I_ext = clip(I_ext, -10*mV, 10*mV)
''', dt=1*ms)

        self.intralaminar.run_regularly('''
v = clip(v, -80*mV, -30*mV)
I_osc = clip(I_osc, -20*mV, 30*mV)
I_exc = clip(I_exc, -20*mV, 20*mV)
I_inh = clip(I_inh, -20*mV, 20*mV)
I_ext = clip(I_ext, -10*mV, 10*mV)
''', dt=1*ms)

        # Add monitors
        self.monitors['relay_spikes'] = SpikeMonitor(
            self.relay_nuclei, name=f'{self.name}_relay_spikes'
        )
        self.monitors['reticular_spikes'] = SpikeMonitor(
            self.reticular_nucleus, name=f'{self.name}_reticular_spikes'
        )
        self.monitors['intralaminar_spikes'] = SpikeMonitor(
            self.intralaminar, name=f'{self.name}_intralaminar_spikes'
        )

        return self

    def get_groups(self):
        """Get all neuron groups."""
        return {
            'relay_nuclei': self.relay_nuclei,
            'reticular_nucleus': self.reticular_nucleus,
            'intralaminar': self.intralaminar,
        }

    def get_monitors(self):
        """Get all monitors."""
        return self.monitors

    def set_alpha_power(self, power: float):
        """Set alpha rhythm power (0-1)."""
        self.alpha_power = np.clip(power, 0.0, 1.0)

        # Scale oscillation amplitude
        # relay_nuclei.A_alpha = 30*mV at power=1.0 (30mV for tau_m=20ms needs this)
        if self.relay_nuclei is not None:
            self.relay_nuclei.A_alpha = f'{30 * power}*mV'
        # Note: A_osc is set directly in build() to correct value for oscillation
        # Do not override here - A_osc=18*mV is suitable for tau_m=15ms

    def set_gating(self, gating: float):
        """Set thalamic gating state (0=closed, 1=open)."""
        self.gating_state = np.clip(gating, 0.0, 1.0)

        if self.relay_nuclei is not None:
            self.relay_nuclei.gating = self.gating_state

    def receive_cortical_input(self, input_strength: float):
        """Receive cortical feedback input."""
        if self.relay_nuclei is not None:
            self.relay_nuclei.I_cortical = f'{input_strength * 10}*mV'

    def receive_brainstem_input(self, arousal: float):
        """Receive arousal input from brainstem."""
        if self.relay_nuclei is not None:
            self.relay_nuclei.I_brainstem = f'{arousal * 8}*mV'
        if self.intralaminar is not None:
            self.intralaminar.I_exc = f'{arousal * 5}*mV'
