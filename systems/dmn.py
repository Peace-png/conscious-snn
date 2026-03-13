"""
Default Mode Network (DMN)

Rest state and self-referential processing network.
Distributed across multiple regions, anti-correlated with task networks.

~50M neurons with alpha oscillation (8-12Hz).

Key features:
- Activated at rest, deactivated during tasks
- Self-referential thinking, mind-wandering
- Posterior cingulate hub
- Medial PFC hub
"""

from brian2 import (
    NeuronGroup, Synapses, PoissonGroup, SpikeMonitor, StateMonitor,
    Hz, ms, mV, nA, nS, pA
)
import numpy as np
from core.neurons import AdaptiveExpLIF, OscillatoryNeuron


class DMNSystem:
    """
    Default Mode Network.

    ~50M neurons (abstracted to configurable scale)
    Oscillation: Alpha 8-12Hz at rest

    Subregions:
    - Posterior cingulate cortex (PCC): ~15M (central hub)
    - Medial PFC (mPFC): ~15M (anterior hub)
    - Lateral parietal cortex: ~10M
    - Hippocampal formation: ~10M (memory access)
    """

    # Subregion ratios
    RATIOS = {
        'pcc': 0.30,        # ~15M / 50M - posterior hub
        'mpfc': 0.30,       # ~15M / 50M - anterior hub
        'lateral_parietal': 0.20,  # ~10M / 50M
        'hippocampal': 0.20,        # ~10M / 50M
    }

    def __init__(self, n_neurons: int, name: str = 'dmn'):
        self.n_neurons = n_neurons
        self.name = name

        # Calculate subregion sizes
        self.n_pcc = max(1, int(n_neurons * self.RATIOS['pcc']))
        self.n_mpfc = max(1, int(n_neurons * self.RATIOS['mpfc']))
        self.n_lateral = max(1, int(n_neurons * self.RATIOS['lateral_parietal']))
        self.n_hippocampal = n_neurons - self.n_pcc - self.n_mpfc - self.n_lateral

        # Neuron groups
        self.pcc = None
        self.mpfc = None
        self.lateral_parietal = None
        self.hippocampal = None
        # Inhibitory interneurons
        self.pcc_inhib = None
        self.mpfc_inhib = None
        self.monitors = {}

        # State variables
        self.activation_level = 0.5  # High at rest, low during tasks
        self.mind_wandering = 0.5

    def build(self) -> 'DMNSystem':
        """Build the DMN populations."""

        # Posterior cingulate cortex - central hub
        # Integrates information across DMN
        self.pcc = OscillatoryNeuron.create_group(
            self.n_pcc,
            frequency=10*Hz,  # Alpha rhythm
            name=f'{self.name}_pcc',
            params={
                'A_osc': 35*mV,  # Needs 35mV for tau_m=25ms
                'tau_m': 25*ms,
            }
        )

        # Medial PFC - anterior hub
        # Self-referential processing
        self.mpfc = OscillatoryNeuron.create_group(
            self.n_mpfc,
            frequency=10*Hz,
            name=f'{self.name}_mpfc',
            params={
                'A_osc': 40*mV,  # Needs 40mV for tau_m=30ms
                'tau_m': 30*ms,
            }
        )

        # Lateral parietal cortex - attention/memory
        self.lateral_parietal = AdaptiveExpLIF.create_group(
            self.n_lateral,
            name=f'{self.name}_lateral',
            params={
                'tau_w': 200*ms,
                'a': 2,
                'b': 40*mV,
            }
        )

        # Hippocampal formation component - memory access
        self.hippocampal = OscillatoryNeuron.create_group(
            self.n_hippocampal,
            frequency=8*Hz,  # Theta-alpha border
            name=f'{self.name}_hippocampal',
            params={
                'A_osc': 50*mV,  # Needs 50mV for tau_m=35ms
                'tau_m': 35*ms,
            }
        )

        # Inhibitory interneurons for hub regulation
        # VIP/SST-type interneurons that regulate DMN hub activity
        from core.neurons import InhibitoryInterneuron
        n_pcc_inh = max(1, self.n_pcc // 4)  # ~25% interneurons
        n_mpfc_inh = max(1, self.n_mpfc // 4)

        self.pcc_inhib = InhibitoryInterneuron.create_group(
            n_pcc_inh,
            name=f'{self.name}_pcc_inhib',
            params={
                'tau_m': 10*ms,  # Fast-spiking
                'v_thresh': -50*mV,
            }
        )

        self.mpfc_inhib = InhibitoryInterneuron.create_group(
            n_mpfc_inh,
            name=f'{self.name}_mpfc_inhib',
            params={
                'tau_m': 10*ms,  # Fast-spiking
                'v_thresh': -50*mV,
            }
        )

        # DMN internal connectivity
        # PCC ↔ mPFC (anterior-posterior coupling)
        self.pcc_mpfc = Synapses(
            self.pcc, self.mpfc,
            model='w_syn : volt',
            on_pre='I_exc_post += w_syn',
            delay=10*ms,
            name=f'{self.name}_pcc_mpfc'
        )
        self.pcc_mpfc.connect(p=0.1)
        self.pcc_mpfc.w_syn = 3*mV  # Reduced from 5*mV for stability

        self.mpfc_pcc = Synapses(
            self.mpfc, self.pcc,
            model='w_syn : volt',
            on_pre='I_exc_post += w_syn',
            delay=10*ms,
            name=f'{self.name}_mpfc_pcc'
        )
        self.mpfc_pcc.connect(p=0.1)
        self.mpfc_pcc.w_syn = 3*mV  # Reduced from 5*mV for stability

        # PCC ↔ Lateral parietal
        self.pcc_lateral = Synapses(
            self.pcc, self.lateral_parietal,
            model='w_syn : amp',
            on_pre='I_exc_post += w_syn',
            delay=8*ms,
            name=f'{self.name}_pcc_lateral'
        )
        self.pcc_lateral.connect(p=0.08)
        self.pcc_lateral.w_syn = 0.15*nA  # Reduced from 0.3*nA for stability

        # PCC ↔ Hippocampal (memory access)
        self.pcc_hippocampal = Synapses(
            self.pcc, self.hippocampal,
            model='w_syn : volt',
            on_pre='I_exc_post += w_syn',
            delay=5*ms,
            name=f'{self.name}_pcc_hippo'
        )
        self.pcc_hippocampal.connect(p=0.1)
        self.pcc_hippocampal.w_syn = 2.5*mV  # Reduced from 4*mV for stability

        self.hippocampal_pcc = Synapses(
            self.hippocampal, self.pcc,
            model='w_syn : volt',
            on_pre='I_exc_post += w_syn',
            delay=5*ms,
            name=f'{self.name}_hippo_pcc'
        )
        self.hippocampal_pcc.connect(p=0.1)
        self.hippocampal_pcc.w_syn = 2.5*mV  # Reduced from 4*mV for stability

        # mPFC ↔ Hippocampal (autobiographical memory)
        self.mpfc_hippocampal = Synapses(
            self.mpfc, self.hippocampal,
            model='w_syn : volt',
            on_pre='I_exc_post += w_syn',
            delay=8*ms,
            name=f'{self.name}_mpfc_hippo'
        )
        self.mpfc_hippocampal.connect(p=0.08)
        self.mpfc_hippocampal.w_syn = 2*mV  # Reduced from 3*mV for stability

        # Recurrent connectivity in hubs
        self.pcc_recurrent = Synapses(
            self.pcc, self.pcc,
            model='w_syn : volt',
            on_pre='I_exc_post += w_syn',
            delay=5*ms,
            name=f'{self.name}_pcc_recurrent'
        )
        self.pcc_recurrent.connect(p=0.03)
        self.pcc_recurrent.w_syn = 1*mV  # Reduced from 2*mV for stability

        self.mpfc_recurrent = Synapses(
            self.mpfc, self.mpfc,
            model='w_syn : volt',
            on_pre='I_exc_post += w_syn',
            delay=5*ms,
            name=f'{self.name}_mpfc_recurrent'
        )
        self.mpfc_recurrent.connect(p=0.03)
        self.mpfc_recurrent.w_syn = 1*mV  # Reduced from 2*mV for stability

        # Inhibitory feedback loops for hub stability
        # PCC excitatory → PCC inhibitory (recruit inhibition)
        self.pcc_to_inhib = Synapses(
            self.pcc, self.pcc_inhib,
            model='w_syn : volt',
            on_pre='I_exc_post += w_syn',
            delay=2*ms,
            name=f'{self.name}_pcc_to_inhib'
        )
        self.pcc_to_inhib.connect(p=0.2)
        self.pcc_to_inhib.w_syn = 3*mV

        # PCC inhibitory → PCC excitatory (feedback inhibition)
        self.pcc_inhib_to_pcc = Synapses(
            self.pcc_inhib, self.pcc,
            model='w_syn : volt',
            on_pre='I_inh_post += w_syn',  # INHIBITORY
            delay=1*ms,
            name=f'{self.name}_pcc_inhib_to_pcc'
        )
        self.pcc_inhib_to_pcc.connect(p=0.3)
        self.pcc_inhib_to_pcc.w_syn = 5*mV

        # mPFC excitatory → mPFC inhibitory
        self.mpfc_to_inhib = Synapses(
            self.mpfc, self.mpfc_inhib,
            model='w_syn : volt',
            on_pre='I_exc_post += w_syn',
            delay=2*ms,
            name=f'{self.name}_mpfc_to_inhib'
        )
        self.mpfc_to_inhib.connect(p=0.2)
        self.mpfc_to_inhib.w_syn = 3*mV

        # mPFC inhibitory → mPFC excitatory
        self.mpfc_inhib_to_mpfc = Synapses(
            self.mpfc_inhib, self.mpfc,
            model='w_syn : volt',
            on_pre='I_inh_post += w_syn',  # INHIBITORY
            delay=1*ms,
            name=f'{self.name}_mpfc_inhib_to_mpfc'
        )
        self.mpfc_inhib_to_mpfc.connect(p=0.3)
        self.mpfc_inhib_to_mpfc.w_syn = 5*mV

        # POST-STEP CLAMPING (Critical for NaN prevention)
        self.pcc.run_regularly('''
v = clip(v, -80*mV, -30*mV)
I_osc = clip(I_osc, -20*mV, 30*mV)
I_exc = clip(I_exc, -20*mV, 20*mV)
I_inh = clip(I_inh, -20*mV, 20*mV)
I_ext = clip(I_ext, -10*mV, 10*mV)
''', dt=1*ms)

        self.mpfc.run_regularly('''
v = clip(v, -80*mV, -30*mV)
I_osc = clip(I_osc, -20*mV, 30*mV)
I_exc = clip(I_exc, -20*mV, 20*mV)
I_inh = clip(I_inh, -20*mV, 20*mV)
I_ext = clip(I_ext, -10*mV, 10*mV)
''', dt=1*ms)

        self.lateral_parietal.run_regularly('''
v = clip(v, -75*mV, -30*mV)
w = clip(w, -20*mV, 20*mV)
I_exc = clip(I_exc, -20*mV, 30*mV)
I_inh = clip(I_inh, -25*mV, 10*mV)
I_ext = clip(I_ext, -10*mV, 10*mV)
''', dt=1*ms)

        self.hippocampal.run_regularly('''
v = clip(v, -80*mV, -30*mV)
I_osc = clip(I_osc, -20*mV, 30*mV)
I_exc = clip(I_exc, -20*mV, 20*mV)
I_inh = clip(I_inh, -20*mV, 20*mV)
I_ext = clip(I_ext, -10*mV, 10*mV)
''', dt=1*ms)

        # Inhibitory interneuron clamping
        self.pcc_inhib.run_regularly('''
v = clip(v, -80*mV, -40*mV)
I_exc = clip(I_exc, -20*mV, 30*mV)
I_inh = clip(I_inh, -25*mV, 10*mV)
I_ext = clip(I_ext, -10*mV, 10*mV)
''', dt=1*ms)

        self.mpfc_inhib.run_regularly('''
v = clip(v, -80*mV, -40*mV)
I_exc = clip(I_exc, -20*mV, 30*mV)
I_inh = clip(I_inh, -25*mV, 10*mV)
I_ext = clip(I_ext, -10*mV, 10*mV)
''', dt=1*ms)

        # Add monitors
        self.monitors['pcc_spikes'] = SpikeMonitor(
            self.pcc, name=f'{self.name}_pcc_spikes'
        )
        self.monitors['mpfc_spikes'] = SpikeMonitor(
            self.mpfc, name=f'{self.name}_mpfc_spikes'
        )
        self.monitors['lateral_spikes'] = SpikeMonitor(
            self.lateral_parietal, name=f'{self.name}_lateral_spikes'
        )
        self.monitors['hippocampal_spikes'] = SpikeMonitor(
            self.hippocampal, name=f'{self.name}_hippocampal_spikes'
        )

        return self

    def get_groups(self):
        """Get all neuron groups."""
        return {
            'pcc': self.pcc,
            'mpfc': self.mpfc,
            'lateral_parietal': self.lateral_parietal,
            'hippocampal': self.hippocampal,
            'pcc_inhib': self.pcc_inhib,
            'mpfc_inhib': self.mpfc_inhib,
        }

    def get_monitors(self):
        """Get all monitors."""
        return self.monitors

    def set_activation(self, level: float):
        """
        Set DMN activation level.

        High (0.8-1.0) = rest state, mind-wandering
        Low (0.1-0.3) = task-engaged, focused attention
        """
        self.activation_level = np.clip(level, 0.0, 1.0)

        # Scale oscillation amplitude with activation
        if self.pcc is not None:
            self.pcc.A_osc = f'{10 * level}*mV'
        if self.mpfc is not None:
            self.mpfc.A_osc = f'{8 * level}*mV'
        if self.hippocampal is not None:
            self.hippocampal.A_osc = f'{7 * level}*mV'

    def set_mind_wandering(self, level: float):
        """Set mind-wandering level (0-1)."""
        self.mind_wandering = np.clip(level, 0.0, 1.0)
        # Higher mind-wandering = more PCC-mPFC coupling
        # Would modulate synaptic weights in a full implementation

    def deactivate_for_task(self):
        """Deactivate DMN for task engagement."""
        self.set_activation(0.2)

    def activate_for_rest(self):
        """Activate DMN for rest state."""
        self.set_activation(0.8)
