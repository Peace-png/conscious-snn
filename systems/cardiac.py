"""
Cardiac Nervous System

The intrinsic cardiac nervous system (~40k neurons).
Generates rhythmic activity at ~1Hz with HRV modulation.

Key components:
- Cardiac ganglia: pacemaker and interneurons
- Vagal afferent pathway: heart → brainstem (NTS)
- Vagal efferent pathway: brainstem → heart

80% of vagus fibers are afferent (heart to brain).
"""

from brian2 import (
    NeuronGroup, Synapses, PoissonGroup, PoissonInput, SpikeMonitor, StateMonitor,
    Hz, ms, mV, nA, nS, pA
)
import numpy as np

# Direct import to avoid circular dependency with core/__init__.py
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.neurons import CardiacNeuron


class CardiacSystem:
    """
    Cardiac nervous system.

    ~40,000 neurons in the heart's intrinsic nervous system.
    Oscillation: ~1Hz (60 bpm) with HRV modulation

    Subregions:
    - Atrial ganglia: ~15k neurons
    - Ventricular ganglia: ~20k neurons
    - Vagal afferent neurons: ~5k
    """

    # Subregion ratios
    RATIOS = {
        'atrial': 0.375,       # 15k / 40k
        'ventricular': 0.50,   # 20k / 40k
        'vagal_afferent': 0.125,  # 5k / 40k
    }

    def __init__(self, n_neurons: int, name: str = 'cardiac'):
        self.n_neurons = n_neurons
        self.name = name

        # Calculate subregion sizes
        self.n_atrial = int(n_neurons * self.RATIOS['atrial'])
        self.n_ventricular = int(n_neurons * self.RATIOS['ventricular'])
        self.n_vagal = n_neurons - self.n_atrial - self.n_ventricular

        # Neuron groups
        self.atrial = None
        self.ventricular = None
        self.vagal_afferent = None
        self.monitors = {}

        # State variables
        self.heart_rate = 60.0  # bpm
        self.hrv_amplitude = 0.2

    def build(self) -> 'CardiacSystem':
        """Build the cardiac populations."""

        # Atrial ganglia - primary pacemaker region
        # Fires at ~1Hz, modulated by vagal input
        self.atrial = CardiacNeuron.create_group(
            max(1, self.n_atrial),
            name=f'{self.name}_atrial',
            params={
                'f_card': 1 * Hz,
                'A_card': 12 * mV,
                'hrv_amp': self.hrv_amplitude,
            }
        )

        # Ventricular ganglia - conduction and coordination
        self.ventricular = CardiacNeuron.create_group(
            max(1, self.n_ventricular),
            name=f'{self.name}_ventricular',
            params={
                'f_card': 1 * Hz,
                'A_card': 8 * mV,  # Slightly lower amplitude
                'hrv_amp': self.hrv_amplitude,
            }
        )

        # Add background PoissonInput to drive cardiac activity
        # REDUCED weights to prevent NaN accumulation
        self.atrial_poisson = PoissonInput(
            self.atrial, 'I_vagal', N=3, rate=50*Hz, weight=2*mV
        )
        self.ventricular_poisson = PoissonInput(
            self.ventricular, 'I_vagal', N=2, rate=50*Hz, weight=1.5*mV
        )

        # Vagal afferent neurons - relay to brainstem
        # These encode cardiac timing information to NTS
        self.vagal_afferent = NeuronGroup(
            max(1, self.n_vagal),
            model='''
            dv/dt = (v_rest - v + I_cardiac + I_baroreceptor) / tau_m : volt (unless refractory)
            dI_cardiac/dt = -I_cardiac / tau_card : volt
            dI_baroreceptor/dt = -I_baroreceptor / tau_baro : volt
            tau_m : second
            tau_card : second
            tau_baro : second
            v_rest : volt
            v_thresh : volt
            cardiac_phase : 1 (shared)
            baroreceptor_input : volt (shared)
            ''',
            threshold='v > v_thresh',
            reset='v = v_rest',
            refractory=50*ms,
            method='euler',
            name=f'{self.name}_vagal_afferent'
        )
        self.vagal_afferent.tau_m = 30*ms
        self.vagal_afferent.tau_card = 100*ms
        self.vagal_afferent.tau_baro = 50*ms
        self.vagal_afferent.v_rest = -65*mV
        self.vagal_afferent.v_thresh = -55*mV  # Lowered to close gap
        self.vagal_afferent.v = -65*mV
        self.vagal_afferent.I_cardiac = 0*mV
        self.vagal_afferent.I_baroreceptor = 0*mV
        self.vagal_afferent.cardiac_phase = 0
        self.vagal_afferent.baroreceptor_input = 0*mV

        # Intra-cardiac connectivity
        # Atrial → Ventricular (conduction pathway)
        self.conduction_syn = Synapses(
            self.atrial, self.ventricular,
            model='w_syn : volt',
            on_pre='I_exc_post += w_syn',
            delay=5*ms,
            name=f'{self.name}_conduction'
        )
        self.conduction_syn.connect(p=0.1)
        self.conduction_syn.w_syn = 3*mV

        # Cardiac → Vagal afferent (heart-brain pathway)
        self.cardiac_to_vagal = Synapses(
            self.atrial, self.vagal_afferent,
            model='w_syn : volt',
            on_pre='I_exc_post += w_syn',
            delay=2*ms,
            name=f'{self.name}_cardiac_to_vagal'
        )
        self.cardiac_to_vagal.connect(p=0.2)
        self.cardiac_to_vagal.w_syn = 5*mV

        # POST-STEP CLAMPING (Critical for NaN prevention)
        # Brian2's clip() in equations doesn't prevent NaN during integration
        # This clamps AFTER each step, guaranteeing bounded values
        self.atrial.run_regularly('''
v = clip(v, -80*mV, -30*mV)
I_exc = clip(I_exc, -20*mV, 30*mV)
I_inh = clip(I_inh, -25*mV, 10*mV)
I_pacemaker = clip(I_pacemaker, -10*mV, 35*mV)
I_vagal = clip(I_vagal, -10*mV, 25*mV)
''', dt=1*ms)

        self.ventricular.run_regularly('''
v = clip(v, -80*mV, -30*mV)
I_exc = clip(I_exc, -20*mV, 30*mV)
I_inh = clip(I_inh, -25*mV, 10*mV)
I_pacemaker = clip(I_pacemaker, -10*mV, 30*mV)
I_vagal = clip(I_vagal, -10*mV, 25*mV)
''', dt=1*ms)

        self.vagal_afferent.run_regularly('''
v = clip(v, -80*mV, -40*mV)
I_cardiac = clip(I_cardiac, -20*mV, 30*mV)
I_baroreceptor = clip(I_baroreceptor, -20*mV, 30*mV)
''', dt=1*ms)

        # Add monitors
        self.monitors['atrial_spikes'] = SpikeMonitor(
            self.atrial, name=f'{self.name}_atrial_spikes'
        )
        self.monitors['ventricular_spikes'] = SpikeMonitor(
            self.ventricular, name=f'{self.name}_ventricular_spikes'
        )
        self.monitors['vagal_spikes'] = SpikeMonitor(
            self.vagal_afferent, name=f'{self.name}_vagal_spikes'
        )

        return self

    def get_groups(self):
        """Get all neuron groups."""
        return {
            'atrial': self.atrial,
            'ventricular': self.ventricular,
            'vagal_afferent': self.vagal_afferent,
        }

    def get_monitors(self):
        """Get all monitors."""
        return self.monitors

    def get_inputs(self):
        """Get all input objects (PoissonInput, etc.)."""
        return {
            'atrial_poisson': self.atrial_poisson,
            'ventricular_poisson': self.ventricular_poisson,
        }

    def set_vagal_input(self, vagal_tone: float):
        """
        Set vagal (parasympathetic) input to the heart.

        Higher vagal tone = lower heart rate.
        """
        if self.atrial is not None:
            # Vagal input hyperpolarizes cardiac neurons
            self.atrial.I_vagal = f'-{vagal_tone * 10}*mV'
            self.ventricular.I_vagal = f'-{vagal_tone * 5}*mV'

    def set_baroreceptor_input(self, pressure_signal: float):
        """
        Set baroreceptor input (blood pressure sensing).

        Higher pressure = more baroreceptor firing.
        """
        if self.vagal_afferent is not None:
            self.vagal_afferent.baroreceptor_input = f'{pressure_signal * 10}*mV'

    def get_cardiac_phase(self) -> float:
        """Get current cardiac cycle phase (0-1)."""
        # Phase is computed from time and frequency
        # 1 Hz = 1 cycle per second
        # This is a placeholder - actual phase comes from simulation time
        return 0.0
