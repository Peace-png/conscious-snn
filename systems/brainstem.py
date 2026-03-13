"""
Brainstem / Autonomic Floor System

The autonomic floor that maintains basic life functions.
Includes: locus coeruleus (NE), raphe nuclei (5-HT), reticular formation.

This is the foundation - always running, never stops.
"""

from brian2 import (
    NeuronGroup, Synapses, PoissonGroup, PoissonInput, SpikeMonitor, StateMonitor,
    Hz, ms, mV, nA, nS, pA
)
import numpy as np


class BrainstemSystem:
    """
    Brainstem autonomic floor.

    ~100M neurons (abstracted to configurable scale)
    Oscillation: 0.5-2 Hz autonomic rhythm

    Subregions:
    - Locus coeruleus: ~50k NE neurons (arousal, attention)
    - Raphe nuclei: ~300k 5-HT neurons (mood, sleep)
    - Reticular formation: diffuse (consciousness substrate)
    """

    # Subregion ratios
    RATIOS = {
        'locus_coeruleus': 0.0005,    # 50k / 100M
        'raphe': 0.003,               # 300k / 100M
        'reticular': 0.9965,          # Rest
    }

    def __init__(self, n_neurons: int, name: str = 'brainstem'):
        self.n_neurons = n_neurons
        self.name = name

        # Calculate subregion sizes
        self.n_lc = int(n_neurons * self.RATIOS['locus_coeruleus'])
        self.n_raphe = int(n_neurons * self.RATIOS['raphe'])
        self.n_ret = n_neurons - self.n_lc - self.n_raphe

        # Neuron groups
        self.locus_coeruleus = None
        self.raphe = None
        self.reticular = None
        self.monitors = {}

    def build(self) -> 'BrainstemSystem':
        """Build the brainstem populations."""

        # Locus coeruleus - tonic/phasic NE neurons
        # Tonic firing ~2-5 Hz at rest, phasic bursts on salient events
        self.locus_coeruleus = NeuronGroup(
            max(1, self.n_lc),
            model='''
            dv/dt = (v_rest - v + I_tonic + I_phasic - I_adapt + I_exc - I_inh) / tau_m : volt (unless refractory)
            dI_tonic/dt = -I_tonic / (500*ms) : volt
            dI_phasic/dt = -I_phasic / (50*ms) : volt
            dI_adapt/dt = -I_adapt / (2000*ms) : volt
            dI_exc/dt = -I_exc / (5*ms) : volt
            dI_inh/dt = -I_inh / (10*ms) : volt
            NE_release : 1  # Norepinephrine release signal
            tau_m : second
            v_rest : volt
            v_thresh : volt
            ''',
            threshold='v > v_thresh',
            reset='''
            v = v_rest
            I_adapt += 5*mV
            NE_release = 1
            ''',
            refractory=10*ms,
            method='euler',
            name=f'{self.name}_lc'
        )
        self.locus_coeruleus.tau_m = 30*ms
        self.locus_coeruleus.v_rest = -60*mV
        self.locus_coeruleus.v_thresh = -50*mV
        self.locus_coeruleus.v = -60*mV
        # Higher tonic drive to ensure baseline firing at ~2-5 Hz
        self.locus_coeruleus.I_tonic = '8*mV + rand()*2*mV'  # Increased from 2*mV
        self.locus_coeruleus.I_phasic = 0*mV
        self.locus_coeruleus.I_adapt = 0*mV
        self.locus_coeruleus.I_exc = 0*mV
        self.locus_coeruleus.I_inh = 0*mV
        self.locus_coeruleus.NE_release = 0

        # Raphe nuclei - serotonergic neurons
        # Slow regular firing ~0.5-2 Hz
        self.raphe = NeuronGroup(
            max(1, self.n_raphe),
            model='''
            dv/dt = (v_rest - v + I_5ht + I_drive + I_exc - I_inh) / tau_m : volt (unless refractory)
            I_5ht : volt
            I_drive : volt
            dI_exc/dt = -I_exc / (5*ms) : volt
            dI_inh/dt = -I_inh / (10*ms) : volt
            tau_m : second
            v_rest : volt
            v_thresh : volt
            ''',
            threshold='v > v_thresh',
            reset='v = v_rest',
            refractory=100*ms,  # Slow recovery
            method='euler',
            name=f'{self.name}_raphe'
        )
        self.raphe.tau_m = 50*ms
        self.raphe.v_rest = -65*mV
        self.raphe.v_thresh = -50*mV
        self.raphe.v = -65*mV
        # Higher baseline drive for serotonin tone
        self.raphe.I_5ht = '8*mV + rand()*2*mV'  # Increased from 3*mV
        self.raphe.I_drive = 0*mV
        self.raphe.I_exc = 0*mV
        self.raphe.I_inh = 0*mV

        # Reticular formation - diffuse activating system
        # The "consciousness substrate" - background activity
        self.reticular = NeuronGroup(
            self.n_ret,
            model='''
            dv/dt = (v_rest - v + I_bg + I_mod + I_exc - I_inh) / tau_m : volt (unless refractory)
            dI_mod/dt = -I_mod / (50*ms) : volt  # Decaying synaptic-like current
            dI_exc/dt = -I_exc / (5*ms) : volt
            dI_inh/dt = -I_inh / (10*ms) : volt
            I_bg : volt  # Background input
            tau_m : second
            v_rest : volt
            v_thresh : volt
            arousal_state : 1 (shared)  # Global arousal level
            ''',
            threshold='v > v_thresh',
            reset='v = v_rest',
            refractory=5*ms,
            method='euler',
            name=f'{self.name}_reticular'
        )
        self.reticular.tau_m = 20*ms
        self.reticular.v_rest = -65*mV
        self.reticular.v_thresh = -52*mV
        self.reticular.v = -65*mV
        # Higher background activity for consciousness substrate
        self.reticular.I_bg = 'rand() * 4*mV + 8*mV'  # Increased from 2*mV baseline
        self.reticular.I_mod = 0*mV
        self.reticular.I_exc = 0*mV
        self.reticular.I_inh = 0*mV
        self.reticular.arousal_state = 0.5  # Normal baseline

        # Add PoissonInput for background noise (drives activity)
        # REDUCED weights to prevent NaN from accumulation
        # The autonomic floor is ALWAYS active, driving consciousness
        self.poisson_bg = PoissonInput(
            self.reticular, 'I_mod', N=10, rate=500*Hz, weight=3*mV
        )

        # Also add to LC and raphe for completeness
        self.lc_poisson = PoissonInput(
            self.locus_coeruleus, 'I_tonic', N=5, rate=300*Hz, weight=2*mV
        )
        self.raphe_poisson = PoissonInput(
            self.raphe, 'I_drive', N=5, rate=300*Hz, weight=2*mV
        )

        # POST-STEP CLAMPING (Critical for NaN prevention)
        # Brian2's clip() in equations doesn't prevent NaN during integration
        # This clamps AFTER each step, guaranteeing bounded values
        self.locus_coeruleus.run_regularly('''
v = clip(v, -80*mV, -40*mV)
I_exc = clip(I_exc, -15*mV, 15*mV)
I_inh = clip(I_inh, -15*mV, 15*mV)
I_tonic = clip(I_tonic, 0*mV, 20*mV)  # Increased upper bound
I_phasic = clip(I_phasic, 0*mV, 20*mV)
''', dt=1*ms)

        self.raphe.run_regularly('''
v = clip(v, -80*mV, -40*mV)
I_exc = clip(I_exc, -15*mV, 15*mV)
I_inh = clip(I_inh, -15*mV, 15*mV)
I_5ht = clip(I_5ht, 0*mV, 20*mV)  # Increased from I_drive
I_drive = clip(I_drive, 0*mV, 15*mV)
''', dt=1*ms)

        self.reticular.run_regularly('''
v = clip(v, -80*mV, -40*mV)
I_exc = clip(I_exc, -15*mV, 15*mV)
I_inh = clip(I_inh, -15*mV, 15*mV)
I_mod = clip(I_mod, -15*mV, 15*mV)
I_bg = clip(I_bg, 0*mV, 20*mV)  # Increased for background activity
''', dt=1*ms)

        # Add monitors
        self.monitors['lc_spikes'] = SpikeMonitor(
            self.locus_coeruleus, name=f'{self.name}_lc_spikes'
        )
        self.monitors['raphe_spikes'] = SpikeMonitor(
            self.raphe, name=f'{self.name}_raphe_spikes'
        )
        self.monitors['reticular_spikes'] = SpikeMonitor(
            self.reticular, name=f'{self.name}_reticular_spikes'
        )

        return self

    def get_groups(self):
        """Get all neuron groups."""
        return {
            'locus_coeruleus': self.locus_coeruleus,
            'raphe': self.raphe,
            'reticular': self.reticular,
        }

    def get_monitors(self):
        """Get all monitors."""
        return self.monitors

    def get_inputs(self):
        """Get all input objects (PoissonInput, etc.)."""
        return {
            'poisson_bg': self.poisson_bg,
            'lc_poisson': self.lc_poisson,
            'raphe_poisson': self.raphe_poisson,
        }

    def set_arousal(self, level: float):
        """Set global arousal level (0=sleep, 1=high alert)."""
        if self.reticular is not None:
            self.reticular.arousal_state = level
            # Scale background activity
            self.reticular.I_bg = f'rand() * {level*4}*mV + {level*2}*mV'

    def trigger_phasic_burst(self, amplitude: float = 10.0):
        """Trigger phasic burst in LC (simulating salient event)."""
        if self.locus_coeruleus is not None:
            self.locus_coeruleus.I_phasic = f'{amplitude}*mV'
