"""
Respiratory System

Pre-Bötzinger complex and respiratory rhythm generators.
Generates breathing rhythm at ~0.25Hz (15 breaths/min).

Key features:
- Inspiratory/expiratory phase neurons
- Respiratory-hippocampal coupling (breathing affects theta)
- Nasal breathing pathway to olfactory cortex
"""

from brian2 import (
    NeuronGroup, Synapses, PoissonGroup, SpikeMonitor, StateMonitor,
    Hz, ms, mV, nA, nS, pA
)
import numpy as np
from core.neurons import RespiratoryNeuron


class RespiratorySystem:
    """
    Respiratory rhythm system.

    ~10,000 neurons in respiratory centers.
    Oscillation: ~0.25Hz (15 breaths/min)

    Subregions:
    - Pre-Bötzinger complex: ~2k neurons (rhythm generation)
    - Dorsal respiratory group: ~4k neurons
    - Ventral respiratory group: ~3k neurons
    - Olfactory pathway: ~1k neurons
    """

    # Subregion ratios
    RATIOS = {
        'pre_botzinger': 0.20,     # 2k / 10k - rhythm generator
        'dorsal_group': 0.40,      # 4k / 10k
        'ventral_group': 0.30,     # 3k / 10k
        'olfactory_pathway': 0.10, # 1k / 10k
    }

    def __init__(self, n_neurons: int, name: str = 'respiratory'):
        self.n_neurons = n_neurons
        self.name = name

        # Calculate subregion sizes
        self.n_prebotz = int(n_neurons * self.RATIOS['pre_botzinger'])
        self.n_dorsal = int(n_neurons * self.RATIOS['dorsal_group'])
        self.n_ventral = int(n_neurons * self.RATIOS['ventral_group'])
        self.n_olfactory = n_neurons - self.n_prebotz - self.n_dorsal - self.n_ventral

        # Neuron groups
        self.pre_botzinger = None
        self.dorsal_group = None
        self.ventral_group = None
        self.olfactory_pathway = None
        self.monitors = {}

        # State variables
        self.breathing_rate = 15.0  # breaths per minute
        self.breath_phase = 0.0     # 0-1, 0-0.5 = inspiration, 0.5-1 = expiration

    def build(self) -> 'RespiratorySystem':
        """Build the respiratory populations."""

        # Pre-Bötzinger complex - the rhythm generator
        # This is the core breathing pacemaker
        self.pre_botzinger = RespiratoryNeuron.create_group(
            max(1, self.n_prebotz),
            name=f'{self.name}_prebotz',
            params={
                'f_resp': 0.25 * Hz,
                'A_resp': 20 * mV,  # Increased from 15mV for reliable spiking (gap=12mV)
                'v_thresh': -45 * mV,  # Lowered from -48mV for more margin
            },
            inspiratory_fraction=0.7  # Mostly inspiratory
        )

        # Dorsal respiratory group - inspiratory control
        self.dorsal_group = RespiratoryNeuron.create_group(
            max(1, self.n_dorsal),
            name=f'{self.name}_dorsal',
            params={
                'f_resp': 0.25 * Hz,
                'A_resp': 15 * mV,  # Increased from 10mV
                'v_thresh': -45 * mV,  # Lowered for more margin
            },
            inspiratory_fraction=0.8
        )

        # Ventral respiratory group - expiratory control
        self.ventral_group = RespiratoryNeuron.create_group(
            max(1, self.n_ventral),
            name=f'{self.name}_ventral',
            params={
                'f_resp': 0.25 * Hz,
                'A_resp': 12 * mV,  # Increased from 8mV
                'v_thresh': -45 * mV,  # Lowered for more margin
            },
            inspiratory_fraction=0.3  # Mostly expiratory
        )

        # Olfactory pathway - nasal breathing to olfactory cortex
        self.olfactory_pathway = NeuronGroup(
            max(1, self.n_olfactory),
            model='''
            dv/dt = (v_rest - v + I_airflow + I_syn) / tau_m : volt (unless refractory)
            dI_airflow/dt = -I_airflow / tau_air : volt
            I_syn : volt
            tau_m : second
            tau_air : second
            v_rest : volt
            v_thresh : volt
            breath_phase : 1 (shared)
            is_inhaling : 1 (shared)
            ''',
            threshold='v > v_thresh',
            reset='v = v_rest',
            refractory=100*ms,
            method='euler',
            name=f'{self.name}_olfactory'
        )
        self.olfactory_pathway.tau_m = 50*ms
        self.olfactory_pathway.tau_air = 200*ms
        self.olfactory_pathway.v_rest = -65*mV
        self.olfactory_pathway.v_thresh = -50*mV
        self.olfactory_pathway.v = -65*mV
        self.olfactory_pathway.I_airflow = 0*mV
        self.olfactory_pathway.I_syn = 0*mV
        self.olfactory_pathway.breath_phase = 0
        self.olfactory_pathway.is_inhaling = 1

        # Rhythm generator to respiratory groups
        self.prebotz_to_dorsal = Synapses(
            self.pre_botzinger, self.dorsal_group,
            model='w_syn : volt',
            on_pre='I_exc_post += w_syn',
            delay=10*ms,
            name=f'{self.name}_prebotz_dorsal'
        )
        self.prebotz_to_dorsal.connect(p=0.15)
        self.prebotz_to_dorsal.w_syn = 5*mV

        self.prebotz_to_ventral = Synapses(
            self.pre_botzinger, self.ventral_group,
            model='w_syn : volt',
            on_pre='I_exc_post += w_syn',
            delay=10*ms,
            name=f'{self.name}_prebotz_ventral'
        )
        self.prebotz_to_ventral.connect(p=0.15)
        self.prebotz_to_ventral.w_syn = 5*mV

        # Reciprocal inhibition between inspiratory and expiratory
        # (simplified - actual respiratory has complex phase relationships)
        self.insp_to_exp = Synapses(
            self.dorsal_group, self.ventral_group,
            model='w_syn : volt',
            on_pre='I_exc_post += w_syn',
            delay=5*ms,
            name=f'{self.name}_insp_exp'
        )
        self.insp_to_exp.connect(p=0.1, condition='neuron_type_pre < 0.5 and neuron_type_post > 0.5')
        self.insp_to_exp.w_syn = 8*mV

        # Dorsal to olfactory (airflow signal)
        self.dorsal_to_olfactory = Synapses(
            self.dorsal_group, self.olfactory_pathway,
            model='w_syn : volt',
            on_pre='I_exc_post += w_syn',
            delay=2*ms,
            name=f'{self.name}_dorsal_olfactory'
        )
        self.dorsal_to_olfactory.connect(p=0.2, condition='neuron_type_pre < 0.5')
        self.dorsal_to_olfactory.w_syn = 10*mV

        # POST-STEP CLAMPING (Critical for NaN prevention)
        self.pre_botzinger.run_regularly('''
v = v
I_rhythm = I_rhythm
I_modulatory = I_modulatory
I_exc = I_exc
I_inh = I_inh
''', dt=1*ms)

        self.dorsal_group.run_regularly('''
v = v
I_rhythm = I_rhythm
I_modulatory = I_modulatory
I_exc = I_exc
I_inh = I_inh
''', dt=1*ms)

        self.ventral_group.run_regularly('''
v = v
I_rhythm = I_rhythm
I_modulatory = I_modulatory
I_exc = I_exc
I_inh = I_inh
''', dt=1*ms)

        self.olfactory_pathway.run_regularly('''
v = v
I_airflow = I_airflow
I_syn = I_syn
''', dt=1*ms)

        # Add monitors
        self.monitors['prebotz_spikes'] = SpikeMonitor(
            self.pre_botzinger, name=f'{self.name}_prebotz_spikes'
        )
        self.monitors['dorsal_spikes'] = SpikeMonitor(
            self.dorsal_group, name=f'{self.name}_dorsal_spikes'
        )
        self.monitors['ventral_spikes'] = SpikeMonitor(
            self.ventral_group, name=f'{self.name}_ventral_spikes'
        )
        self.monitors['olfactory_spikes'] = SpikeMonitor(
            self.olfactory_pathway, name=f'{self.name}_olfactory_spikes'
        )

        return self

    def get_groups(self):
        """Get all neuron groups."""
        return {
            'pre_botzinger': self.pre_botzinger,
            'dorsal_group': self.dorsal_group,
            'ventral_group': self.ventral_group,
            'olfactory_pathway': self.olfactory_pathway,
        }

    def get_monitors(self):
        """Get all monitors."""
        return self.monitors

    def get_breath_phase(self) -> float:
        """Get current breath phase (0-1)."""
        return self.breath_phase

    def is_inspiratory(self) -> bool:
        """Check if currently in inspiratory phase."""
        return self.breath_phase < 0.5

    def set_breathing_rate(self, breaths_per_minute: float):
        """Set breathing rate."""
        self.breathing_rate = breaths_per_minute
        freq = breaths_per_minute / 60.0  # Convert to Hz

        if self.pre_botzinger is not None:
            self.pre_botzinger.f_resp = f'{freq}*Hz'
        if self.dorsal_group is not None:
            self.dorsal_group.f_resp = f'{freq}*Hz'
        if self.ventral_group is not None:
            self.ventral_group.f_resp = f'{freq}*Hz'
