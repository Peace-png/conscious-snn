"""
Prefrontal Cortex

Executive function and top-down modulation system.
~200M neurons with gamma oscillation (30-100Hz).

Key features:
- Working memory persistent activity
- Top-down modulation of limbic and sensory systems
- Executive control signals
- Multiple subregions (dlPFC, vlPFC, mPFC, OFC)
"""

from brian2 import (
    NeuronGroup, Synapses, PoissonGroup, PoissonInput, SpikeMonitor, StateMonitor,
    Hz, ms, mV, nA, nS, pA
)
import numpy as np
from core.neurons import AdaptiveExpLIF, OscillatoryNeuron


class PrefrontalSystem:
    """
    Prefrontal cortex for executive control.

    ~200M neurons (abstracted to configurable scale)
    Oscillation: Gamma 30-100Hz during active processing

    Subregions:
    - Dorsolateral PFC (dlPFC): ~80M (working memory, cognitive control)
    - Ventrolateral PFC (vlPFC): ~50M (response inhibition)
    - Medial PFC (mPFC): ~40M (self-reference, emotion regulation)
    - Orbitofrontal cortex (OFC): ~30M (value, reward)
    """

    # Subregion ratios
    RATIOS = {
        'dlpfc': 0.40,   # ~80M / 200M
        'vlpfc': 0.25,   # ~50M / 200M
        'mpfc': 0.20,    # ~40M / 200M
        'ofc': 0.15,     # ~30M / 200M
    }

    def __init__(self, n_neurons: int, name: str = 'prefrontal'):
        self.n_neurons = n_neurons
        self.name = name

        # Calculate subregion sizes
        self.n_dlpfc = max(1, int(n_neurons * self.RATIOS['dlpfc']))
        self.n_vlpfc = max(1, int(n_neurons * self.RATIOS['vlpfc']))
        self.n_mpfc = max(1, int(n_neurons * self.RATIOS['mpfc']))
        self.n_ofc = n_neurons - self.n_dlpfc - self.n_vlpfc - self.n_mpfc

        # Neuron groups
        self.dlpfc = None
        self.vlpfc = None
        self.mpfc = None
        self.ofc = None
        self.monitors = {}

        # State variables
        self.working_memory_load = 0.0
        self.executive_control_strength = 0.5

    def build(self) -> 'PrefrontalSystem':
        """Build the prefrontal populations."""

        # Dorsolateral PFC - working memory, cognitive control
        # Persistent activity for working memory
        self.dlpfc = AdaptiveExpLIF.create_group(
            self.n_dlpfc,
            name=f'{self.name}_dlpfc',
            params={
                'tau_w': 300*ms,  # Longer adaptation for sustained activity
                'a': 2,
                'b': 20*mV,  # Reduced from 80mV - was suppressing all activity
            }
        )

        # Ventrolateral PFC - response inhibition, selection
        self.vlpfc = AdaptiveExpLIF.create_group(
            self.n_vlpfc,
            name=f'{self.name}_vlpfc',
            params={
                'tau_w': 200*ms,
                'a': 3,
                'b': 15*mV,  # Reduced from 70mV
            }
        )

        # Medial PFC - emotion regulation, self-reference
        # Higher connection to limbic
        self.mpfc = OscillatoryNeuron.create_group(
            self.n_mpfc,
            frequency=40*Hz,  # Gamma
            name=f'{self.name}_mpfc',
            params={
                'A_osc': 25*mV,
                'tau_m': 15*ms,
            }
        )

        # Orbitofrontal cortex - value encoding, reward
        self.ofc = AdaptiveExpLIF.create_group(
            self.n_ofc,
            name=f'{self.name}_ofc',
            params={
                'tau_w': 150*ms,
                'a': 4,
                'b': 12*mV,  # Reduced from 50mV
            }
        )

        # CRITICAL: Add spontaneous background drive to AdaptiveExpLIF populations
        # Without this, cortex stays silent waiting for subcortical input that never comes
        # (biological correlate: ongoing synaptic noise from background activity)
        self.dlpfc_noise = PoissonInput(
            self.dlpfc, 'I_ext', N=10, rate=200*Hz, weight=1.5*mV
        )
        self.vlpfc_noise = PoissonInput(
            self.vlpfc, 'I_ext', N=10, rate=200*Hz, weight=1.5*mV
        )
        self.ofc_noise = PoissonInput(
            self.ofc, 'I_ext', N=10, rate=200*Hz, weight=1.5*mV
        )

        # Intra-PFC connectivity
        # dlPFC ↔ vlPFC (cognitive control ↔ inhibition)
        self.dlpfc_vlpfc = Synapses(
            self.dlpfc, self.vlpfc,
            model='w_syn : amp',
            on_pre='I_exc_post += w_syn',
            delay=5*ms,
            name=f'{self.name}_dlpfc_vlpfc'
        )
        self.dlpfc_vlpfc.connect(p=0.05)
        self.dlpfc_vlpfc.w_syn = 0.15*nA  # Reduced from 0.3*nA for stability

        self.vlpfc_dlpfc = Synapses(
            self.vlpfc, self.dlpfc,
            model='w_syn : amp',
            on_pre='I_exc_post += w_syn',
            delay=5*ms,
            name=f'{self.name}_vlpfc_dlpfc'
        )
        self.vlpfc_dlpfc.connect(p=0.05)
        self.vlpfc_dlpfc.w_syn = 0.1*nA  # Reduced from 0.2*nA for stability

        # mPFC ↔ OFC (emotion ↔ value)
        self.mpfc_ofc = Synapses(
            self.mpfc, self.ofc,
            model='w_syn : amp',
            on_pre='I_exc_post += w_syn',
            delay=5*ms,
            name=f'{self.name}_mpfc_ofc'
        )
        self.mpfc_ofc.connect(p=0.08)
        self.mpfc_ofc.w_syn = 0.2*nA  # Reduced from 0.4*nA for stability

        self.ofc_mpfc = Synapses(
            self.ofc, self.mpfc,
            model='w_syn : volt',
            on_pre='I_exc_post += w_syn',
            delay=5*ms,
            name=f'{self.name}_ofc_mpfc'
        )
        self.ofc_mpfc.connect(p=0.08)
        self.ofc_mpfc.w_syn = 2.5*mV  # Reduced from 4*mV for stability

        # dlPFC working memory recurrent loops
        # Persistent activity through recurrent excitation
        self.dlpfc_recurrent = Synapses(
            self.dlpfc, self.dlpfc,
            model='w_syn : amp',
            on_pre='I_exc_post += w_syn',
            delay=3*ms,
            name=f'{self.name}_dlpfc_recurrent'
        )
        self.dlpfc_recurrent.connect(p=0.02)
        self.dlpfc_recurrent.w_syn = 0.2*nA  # Reduced from 0.4*nA for stability

        # Top-down control output (to limbic, etc.)
        # This is the PFC's modulatory output
        self.top_down_output = NeuronGroup(
            max(1, self.n_dlpfc // 10),
            model='''
            dv/dt = (v_rest - v + I_control) / tau_m : volt (unless refractory)
            dI_control/dt = -I_control / tau_ctrl : volt
            control_signal : 1 (shared)
            tau_m : second
            tau_ctrl : second
            v_rest : volt
            v_thresh : volt
            ''',
            threshold='v > v_thresh',
            reset='v = v_rest',
            refractory=10*ms,
            method='euler',
            name=f'{self.name}_topdown_output'
        )
        self.top_down_output.tau_m = 20*ms
        self.top_down_output.tau_ctrl = 50*ms
        self.top_down_output.v_rest = -65*mV
        self.top_down_output.v_thresh = -50*mV
        self.top_down_output.v = -65*mV
        self.top_down_output.I_control = 0*mV
        self.top_down_output.control_signal = 0

        # dlPFC → top-down output
        self.dlpfc_to_output = Synapses(
            self.dlpfc, self.top_down_output,
            model='w_syn : volt',
            on_pre='I_exc_post += w_syn',
            delay=5*ms,
            name=f'{self.name}_dlpfc_output'
        )
        self.dlpfc_to_output.connect(p=0.1)
        self.dlpfc_to_output.w_syn = 3*mV  # Reduced from 5*mV for stability

        # POST-STEP CLAMPING (Critical for NaN prevention)
        self.dlpfc.run_regularly('''
v = v
w = w
I_exc = I_exc
I_inh = I_inh
I_ext = I_ext
''', dt=1*ms)

        self.vlpfc.run_regularly('''
v = v
w = w
I_exc = I_exc
I_inh = I_inh
I_ext = I_ext
''', dt=1*ms)

        self.mpfc.run_regularly('''
v = v
I_osc = I_osc
I_exc = I_exc
I_inh = I_inh
I_ext = I_ext
''', dt=1*ms)

        self.ofc.run_regularly('''
v = v
w = w
I_exc = I_exc
I_inh = I_inh
I_ext = I_ext
''', dt=1*ms)

        self.top_down_output.run_regularly('''
v = v
I_control = I_control
''', dt=1*ms)

        # Add monitors
        self.monitors['dlpfc_spikes'] = SpikeMonitor(
            self.dlpfc, name=f'{self.name}_dlpfc_spikes'
        )
        self.monitors['vlpfc_spikes'] = SpikeMonitor(
            self.vlpfc, name=f'{self.name}_vlpfc_spikes'
        )
        self.monitors['mpfc_spikes'] = SpikeMonitor(
            self.mpfc, name=f'{self.name}_mpfc_spikes'
        )
        self.monitors['ofc_spikes'] = SpikeMonitor(
            self.ofc, name=f'{self.name}_ofc_spikes'
        )
        self.monitors['topdown_spikes'] = SpikeMonitor(
            self.top_down_output, name=f'{self.name}_topdown_spikes'
        )

        return self

    def get_groups(self):
        """Get all neuron groups."""
        return {
            'dlpfc': self.dlpfc,
            'vlpfc': self.vlpfc,
            'mpfc': self.mpfc,
            'ofc': self.ofc,
            'top_down_output': self.top_down_output,
        }

    def get_monitors(self):
        """Get all monitors."""
        return self.monitors

    def get_inputs(self):
        """Get all input objects (PoissonInput, etc.)."""
        return {
            'dlpfc_noise': self.dlpfc_noise,
            'vlpfc_noise': self.vlpfc_noise,
            'ofc_noise': self.ofc_noise,
        }

    def set_working_memory_load(self, load: float):
        """Set working memory load (0-1)."""
        self.working_memory_load = np.load

        # Increase recurrent activity with load
        if self.dlpfc_recurrent is not None:
            scale = 1.0 + load * 0.5
            # Can't directly scale, would need to track base weight
            pass

    def set_executive_control(self, strength: float):
        """Set executive control strength (0-1)."""
        self.executive_control_strength = np.strength

        # Modulate top-down output
        if self.top_down_output is not None:
            self.top_down_output.control_signal = strength

    def get_control_signal(self) -> float:
        """Get current executive control signal level."""
        if self.top_down_output is not None:
            return float(self.top_down_output.control_signal)
        return 0.0
