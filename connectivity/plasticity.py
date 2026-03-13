"""
Plasticity Rules for Inter-System Connections

Implements various forms of synaptic plasticity:
- STDP (Spike Timing Dependent Plasticity)
- Homeostatic plasticity
- Reward-modulated plasticity
"""

import numpy as np
from brian2 import Synapses, ms, mV, nA, Hz, pA
from typing import Optional, Dict


class STDPRule:
    """
    Spike Timing Dependent Plasticity.

    Implements asymmetric Hebbian learning based on spike timing.
    Pre before post → LTP (strengthen)
    Post before pre → LTD (weaken)
    """

    # STDP parameters
    MODEL = '''
    w : 1
    dapre/dt = -apre/tau_pre : 1 (event-driven)
    dapost/dt = -apost/tau_post : 1 (event-driven)
    '''

    ON_PRE = '''
    I_exc_post += w*nA
    apre += A_pre
    w = clip(w + apost, 0, w_max)
    '''

    ON_POST = '''
    apost += A_post
    w = clip(w + apre, 0, w_max)
    '''

    DEFAULT_PARAMS = {
        'tau_pre': 20 * ms,
        'tau_post': 20 * ms,
        'A_pre': 0.01,
        'A_post': -0.0105,
        'w_max': 1.0,
        'w_min': 0.0,
    }

    @classmethod
    def create(cls, source, target, initial_weight: float = 0.5,
               params: Dict = None, name: str = None):
        """
        Create STDP synapses between groups.

        Args:
            source: Source neuron group
            target: Target neuron group
            initial_weight: Initial synaptic weight
            params: Custom STDP parameters
            name: Synapse name

        Returns:
            Brian2 Synapses object with STDP
        """
        p = cls.DEFAULT_PARAMS.copy()
        if params:
            p.update(params)

        syn = Synapses(
            source, target,
            model=cls.MODEL,
            on_pre=cls.ON_PRE,
            on_post=cls.ON_POST,
            name=name or 'stdp_synapses',
            namespace=p
        )

        return syn, p

    @classmethod
    def asymmetric_window(cls, tau_ltp: float = 20*ms,
                         tau_ltd: float = 40*ms,
                         A_ltp: float = 0.01,
                         A_ltd: float = -0.0105):
        """
        Create asymmetric STDP window (typical for cortex).

        LTD window is wider than LTP window.
        """
        return {
            'tau_pre': tau_ltp,
            'tau_post': tau_ltd,
            'A_pre': A_ltp,
            'A_post': A_ltd,
            'w_max': 1.0,
        }

    @classmethod
    def symmetric_window(cls, tau: float = 20*ms, A: float = 0.01):
        """Create symmetric STDP window."""
        return {
            'tau_pre': tau,
            'tau_post': tau,
            'A_pre': A,
            'A_post': -A,
            'w_max': 1.0,
        }


class HomeostaticRule:
    """
    Homeostatic plasticity for firing rate stability.

    Scales synaptic weights to maintain target firing rate.
    This prevents runaway excitation or silence.
    """

    MODEL = '''
    w : 1
    target_rate : Hz
    activity_trace : 1
    '''

    # Update activity trace and scale weights
    # (typically done on a slower timescale)

    @staticmethod
    def scale_weights(synapses, target_rate: float = 5*Hz,
                      current_rate: float = None,
                      learning_rate: float = 0.01):
        """
        Apply homeostatic scaling.

        Args:
            synapses: Synapses object
            target_rate: Target firing rate
            current_rate: Current average firing rate
            learning_rate: Scaling rate
        """
        if current_rate is None:
            return

        # Compute scaling factor
        if current_rate > 0:
            scale = 1 + learning_rate * (target_rate / current_rate - 1)
            scale = np.clip(scale, 0.9, 1.1)  # Limit scaling

            synapses.w = np.clip(synapses.w * scale, 0, 1)

    @staticmethod
    def create_intrinsic_plasticity(group, target_rate: float = 5*Hz,
                                    tau_ip: float = 10000*ms):
        """
        Create intrinsic plasticity rule.

        Adjusts neuron excitability to maintain target rate.
        """
        model = '''
        threshold : volt
        dthreshold/dt = (threshold_rest - threshold + ip_mod) / tau_ip : volt
        threshold_rest : volt
        ip_mod = alpha * (rate_estimate - target_rate) : volt
        rate_estimate : Hz
        target_rate : Hz
        alpha : volt * second
        '''

        return model


class RewardModulatedSTDP:
    """
    Reward-modulated STDP (three-factor learning).

    Combines spike timing with dopamine-like reward signal.
    Used in reinforcement learning scenarios.

    Δw = R(t) × STDP(pre, post)

    where R(t) is the reward signal.
    """

    MODEL = '''
    w : 1
    dapre/dt = -apre/tau_pre : 1 (event-driven)
    dapost/dt = -apost/tau_post : 1 (event-driven)
    eligibility : 1
    reward : 1 (shared)
    '''

    ON_PRE = '''
    I_exc_post += w*nA
    apre += A_pre
    eligibility += apre
    '''

    ON_POST = '''
    apost += A_post
    eligibility += apost
    '''

    # Weight update happens on reward delivery
    ON_REWARD = '''
    w = clip(w + reward * eligibility, w_min, w_max)
    eligibility = 0
    '''

    DEFAULT_PARAMS = {
        'tau_pre': 20 * ms,
        'tau_post': 20 * ms,
        'A_pre': 0.01,
        'A_post': -0.0105,
        'w_max': 1.0,
        'w_min': 0.0,
    }

    @classmethod
    def create(cls, source, target, params: Dict = None,
               name: str = 'reward_modulated_stdp'):
        """
        Create reward-modulated STDP synapses.

        Args:
            source: Source neuron group
            target: Target neuron group
            params: Custom parameters
            name: Synapse name

        Returns:
            Synapses object with reward-modulated plasticity
        """
        p = cls.DEFAULT_PARAMS.copy()
        if params:
            p.update(params)

        syn = Synapses(
            source, target,
            model=cls.MODEL,
            on_pre=cls.ON_PRE,
            on_post=cls.ON_POST,
            name=name,
            namespace=p
        )

        return syn, p

    @staticmethod
    def deliver_reward(synapses, reward_value: float):
        """Deliver reward signal to modulate weight updates."""
        synapses.reward = reward_value
        # Weight update happens via ON_REWARD


class StructuralPlasticity:
    """
    Structural plasticity - formation and elimination of synapses.

    This is a placeholder for more advanced structural plasticity.
    In Brian2, this requires custom run functions.
    """

    @staticmethod
    def sprout_synapses(synapses, probability: float = 0.01):
        """
        Create new synapses (placeholder).

        In practice, this requires modifying connectivity during simulation.
        """
        pass

    @staticmethod
    def prune_synapses(synapses, threshold: float = 0.01):
        """
        Remove weak synapses (placeholder).
        """
        pass


# Default plasticity configurations for each system
SYSTEM_PLASTICITY_CONFIG = {
    'hippocampus': {
        'stdp': True,
        'type': 'asymmetric',
        'tau_ltp': 20 * ms,
        'tau_ltd': 40 * ms,
        'homeostatic': True,
        'target_rate': 5 * Hz,
    },
    'prefrontal': {
        'stdp': True,
        'type': 'asymmetric',
        'tau_ltp': 15 * ms,
        'tau_ltd': 30 * ms,
        'homeostatic': True,
        'target_rate': 10 * Hz,
        'reward_modulated': True,
    },
    'limbic': {
        'stdp': True,
        'type': 'asymmetric',
        'tau_ltp': 25 * ms,
        'tau_ltd': 50 * ms,
        'homeostatic': True,
        'target_rate': 8 * Hz,
    },
    'thalamus': {
        'stdp': False,  # Relay, less plastic
        'homeostatic': True,
        'target_rate': 5 * Hz,
    },
    'brainstem': {
        'stdp': False,  # Stable autonomic
        'homeostatic': True,
        'target_rate': 2 * Hz,
    },
    'cardiac': {
        'stdp': False,  # Very stable
        'homeostatic': False,
    },
    'respiratory': {
        'stdp': False,  # Very stable rhythm
        'homeostatic': False,
    },
    'dmn': {
        'stdp': True,
        'type': 'symmetric',
        'tau': 30 * ms,
        'homeostatic': True,
        'target_rate': 3 * Hz,
    },
}
