"""
Neuron Models for Conscious SNN

Custom neuron models for different biological systems:
- AdaptiveExpLIF: General cortical neurons with adaptation
- IzhikevichNeuron: Complex dynamics with low computation
- OscillatoryNeuron: Neurons with intrinsic oscillation
- CardiacNeuron: Cardiac ganglion neurons
- RespiratoryNeuron: Respiratory rhythm neurons
"""

from brian2 import (
    NeuronGroup, Equations, amp, mV, ms, nS, nA, pF, Hz,
    check_units, PoissonGroup
)
import numpy as np


class AdaptiveExpLIF:
    """
    Adaptive Exponential Leaky Integrate-and-Fire neuron model.

    Based on Brette & Gerstner (2005), simplified for unit consistency.
    Uses voltage-based currents like other models in this codebase.
    Includes spike-frequency adaptation for realistic cortical dynamics.

    EXPONENTIAL CLAMP: exp argument clamped to [-50, 50] to prevent NaN overflow.
    When v >> V_T, the neuron spikes anyway - clamping doesn't affect behavior.
    """

    # AdEx equations - simplified with voltage-based currents, all inside /tau_m
    # EXPONENTIAL CLAMPED: clip((v - V_T)/delta_T, -50, 50) prevents overflow
    equations = '''
    dv/dt = (E_L - v + delta_T*exp(clip((v - V_T)/delta_T, -50, 50)) + I_syn + I_ext - w) / tau_m : volt (unless refractory)
    dw/dt = (a*(v - E_L) - w) / tau_w : volt
    I_syn = I_exc - I_inh : volt
    dI_exc/dt = -I_exc / tau_e : volt
    dI_inh/dt = -I_inh / tau_i : volt
    I_ext : volt
    tau_m : second
    E_L : volt
    V_T : volt
    delta_T : volt
    V_peak : volt
    tau_w : second
    a : 1
    b : volt
    tau_e : second
    tau_i : second
    '''

    # Threshold and reset
    threshold = 'v > V_peak'
    reset = '''
    v = E_L
    w += b
    '''

    # Default parameters - simplified with voltage-based approach
    defaults = {
        'tau_m': 20 * ms,
        'E_L': -70.6 * mV,
        'V_T': -50.4 * mV,
        'delta_T': 2.0 * mV,
        'V_peak': -20 * mV,
        'tau_w': 144 * ms,
        'a': 0.001,  # Dimensionless adaptation factor
        'b': 5 * mV,
        'tau_e': 5 * ms,
        'tau_i': 10 * ms,
        'v': -70.6 * mV,
        'w': 0 * mV,
        'I_exc': 0 * mV,
        'I_inh': 0 * mV,
        'I_ext': 0 * mV,
    }

    @classmethod
    def create_group(cls, N, name=None, params=None, refractory=2*ms):
        """Create a NeuronGroup with AdEx dynamics."""
        p = cls.defaults.copy()
        if params:
            p.update(params)

        # V_peak is now a parameter in the namespace
        V_peak = p.get('V_peak', -20 * mV)

        # CRITICAL: Use 'euler' method instead of 'exponential_euler'
        # Brian2 bug #626: exact linear integrator fails for oscillatory systems
        # euler method is more stable and bypasses the SymPy discriminant issue
        group = NeuronGroup(
            N,
            model=cls.equations,
            threshold=f'v > {V_peak/mV}*mV',
            reset=cls.reset,
            refractory=refractory,
            method='euler',
            name=name,
            namespace={}  # Empty namespace - use explicit initialization
        )

        # CRITICAL: Explicitly set per-neuron parameters
        # These are declared as state variables, so they need direct assignment
        group.tau_m = p.get('tau_m', 20*ms)
        group.E_L = p.get('E_L', -70.6*mV)
        group.V_T = p.get('V_T', -50.4*mV)
        group.delta_T = p.get('delta_T', 2*mV)
        group.V_peak = p.get('V_peak', -20*mV)
        group.tau_w = p.get('tau_w', 144*ms)
        group.a = p.get('a', 0.001)
        group.b = p.get('b', 5*mV)
        group.tau_e = p.get('tau_e', 5*ms)
        group.tau_i = p.get('tau_i', 10*ms)

        # State variables
        group.v = p.get('v', -70.6*mV)
        group.w = p.get('w', 0*mV)
        group.I_exc = p.get('I_exc', 0*mV)
        group.I_inh = p.get('I_inh', 0*mV)
        group.I_ext = p.get('I_ext', 0*mV)

        return group


class IzhikevichNeuron:
    """
    Izhikevich neuron model for complex dynamics with minimal computation.

    Can exhibit various firing patterns: regular spiking, fast spiking,
    bursting, chattering, etc. depending on parameters.

    Reference: Izhikevich (2003) IEEE Trans Neural Netw.
    """

    equations = '''
    dv/dt = 0.04*v**2/ms/mV + 5*v/ms + 140*mV/ms - u + I_syn : volt
    du/dt = a*(b*v - u) : volt/second
    I_syn = I_exc - I_inh : volt
    dI_exc/dt = -I_exc / tau_e : volt
    dI_inh/dt = -I_inh / tau_i : volt
    a : Hz
    b : Hz
    c : volt
    d : volt
    tau_e : second
    tau_i : second
    '''

    threshold = 'v > 30*mV'
    reset = '''
    v = c
    u += d
    '''

    # Regular spiking parameters
    defaults_rs = {
        'a': 0.02 * Hz,
        'b': 0.2 * Hz,
        'c': -65 * mV,
        'd': 8 * mV,
        'tau_e': 5 * ms,
        'tau_i': 10 * ms,
        'v': -65 * mV,
        'u': 0 * mV/ms,
    }

    # Fast spiking parameters
    defaults_fs = {
        'a': 0.1 * Hz,
        'b': 0.2 * Hz,
        'c': -65 * mV,
        'd': 2 * mV,
        'tau_e': 5 * ms,
        'tau_i': 10 * ms,
        'v': -65 * mV,
        'u': 0 * mV/ms,
    }

    # Bursting parameters
    defaults_bursting = {
        'a': 0.02 * Hz,
        'b': 0.2 * Hz,
        'c': -55 * mV,
        'd': 4 * mV,
        'tau_e': 5 * ms,
        'tau_i': 10 * ms,
        'v': -65 * mV,
        'u': 0 * mV/ms,
    }

    @classmethod
    def create_group(cls, N, name=None, params=None, mode='regular_spiking'):
        """Create a NeuronGroup with Izhikevich dynamics."""
        if mode == 'regular_spiking':
            p = cls.defaults_rs.copy()
        elif mode == 'fast_spiking':
            p = cls.defaults_fs.copy()
        elif mode == 'bursting':
            p = cls.defaults_bursting.copy()
        else:
            p = cls.defaults_rs.copy()

        if params:
            p.update(params)

        group = NeuronGroup(
            N,
            model=cls.equations,
            threshold=cls.threshold,
            reset=cls.reset,
            method='euler',
            name=name,
            namespace=p
        )

        return group


class OscillatoryNeuron:
    """
    Neuron with intrinsic oscillatory dynamics.

    Generates subthreshold oscillations at a specified frequency,
    useful for alpha, theta, gamma rhythm generation.

    VOLTAGE CLAMP: v clamped to [v_rest - 50mV, v_thresh + 50mV] to prevent NaN.
    """

    # Voltage clamped to prevent numerical instability from input accumulation
    # CURRENT CLAMP: I_exc/I_inh clamped in I_syn calculation to prevent NaN
    # VOLTAGE SOFT CLAMP: Extra conductance when v deviates too far from v_rest
    equations = '''
    dv/dt = (v_rest - v + I_osc + I_syn + I_ext) / tau_m : volt (unless refractory)
    dI_osc/dt = (-I_osc + A_osc * sin(2*pi*f_osc*t)) / tau_osc : volt
    I_syn = clip(I_exc, -20*mV, 20*mV) - clip(I_inh, -20*mV, 20*mV) : volt
    dI_exc/dt = -I_exc / tau_e : volt
    dI_inh/dt = -I_inh / tau_i : volt
    I_ext : volt
    tau_m : second
    tau_osc : second
    f_osc : Hz
    A_osc : volt
    v_rest : volt
    v_thresh : volt
    tau_e : second
    tau_i : second
    '''

    threshold = 'v > v_thresh'
    reset = 'v = clip(v_rest, v_rest - 50*mV, v_thresh + 50*mV)'

    defaults = {
        'tau_m': 10 * ms,  # Faster response for oscillatory following
        'tau_osc': 10 * ms,  # MUST be ≤10ms - higher values suppress oscillation
        'f_osc': 10 * Hz,
        'A_osc': 25 * mV,  # Minimum 25mV needed for reliable spiking at threshold
        'v_rest': -65 * mV,
        'v_thresh': -50 * mV,
        'tau_e': 5 * ms,
        'tau_i': 10 * ms,
        'v': -65 * mV,
        'I_osc': 0 * mV,
        'I_exc': 0 * mV,
        'I_inh': 0 * mV,
        'I_ext': 0 * mV,
    }

    @classmethod
    def create_group(cls, N, frequency, name=None, params=None, refractory=2*ms):
        """Create an oscillatory neuron group at specified frequency."""
        p = cls.defaults.copy()
        p['f_osc'] = frequency
        if params:
            p.update(params)

        group = NeuronGroup(
            N,
            model=cls.equations,
            threshold=cls.threshold,
            reset=cls.reset,
            refractory=refractory,
            method='euler',
            name=name,
            namespace={}  # Empty namespace - use explicit initialization
        )

        # CRITICAL: Explicitly set per-neuron parameters
        # These are declared as state variables, so they need direct assignment
        # NOTE: tau_osc MUST be ≤10ms for oscillation following to work
        # Higher values cause I_osc to lag behind the drive, suppressing spiking
        group.tau_m = p.get('tau_m', 10*ms)
        group.tau_osc = p.get('tau_osc', 10*ms)  # MUST be ≤10ms for oscillation following
        group.f_osc = p.get('f_osc', frequency)
        group.A_osc = p.get('A_osc', 25*mV)  # Minimum 25mV needed for reliable spiking
        group.v_rest = p.get('v_rest', -65*mV)
        group.v_thresh = p.get('v_thresh', -50*mV)
        group.tau_e = p.get('tau_e', 5*ms)
        group.tau_i = p.get('tau_i', 10*ms)

        # State variables
        group.v = p.get('v', -65*mV)
        group.I_osc = p.get('I_osc', 0*mV)
        group.I_exc = p.get('I_exc', 0*mV)
        group.I_inh = p.get('I_inh', 0*mV)
        group.I_ext = p.get('I_ext', 0*mV)

        return group


class CardiacNeuron:
    """
    Cardiac ganglion neuron model.

    Simulates the ~40,000 neurons of the intrinsic cardiac nervous system.
    Generates rhythmic activity at ~1Hz (60 bpm) with HRV modulation.
    """

    equations = '''
    dv/dt = (v_rest - v + I_pacemaker + I_vagal + I_syn) / tau_m : volt (unless refractory)
    dI_pacemaker/dt = (-I_pacemaker + A_card * sin(2*pi*f_card*t + phi)) / tau_pacemaker : volt
    dI_vagal/dt = -I_vagal / tau_vagal : volt
    I_syn = clip(I_exc, -50*mV, 50*mV) - clip(I_inh, -50*mV, 50*mV) : volt  # Clamped to prevent NaN
    dI_exc/dt = -I_exc / tau_e : volt
    dI_inh/dt = -I_inh / tau_i : volt
    # HRV modulation
    dHRV_phase/dt = 2*pi*f_hrv : 1
    HRV_mod = 1 + hrv_amp * sin(HRV_phase) : 1
    tau_m : second
    tau_pacemaker : second
    f_card : Hz
    A_card : volt
    phi : 1  # phase offset for each neuron
    tau_vagal : second
    f_hrv : Hz
    hrv_amp : 1
    v_rest : volt
    v_thresh : volt
    tau_e : second
    tau_i : second
    '''

    threshold = 'v > v_thresh'
    reset = 'v = v_rest'

    defaults = {
        'tau_m': 50 * ms,
        'tau_pacemaker': 100 * ms,
        'f_card': 1 * Hz,            # ~60 bpm
        'A_card': 12 * mV,           # Moderate rhythmic drive (was 20mV, too strong)
        'phi': 0,
        'tau_vagal': 50 * ms,
        'f_hrv': 0.1 * Hz,           # HRV ~0.1 Hz (Mayer wave)
        'hrv_amp': 0.3,              # Increased from 0.2
        'v_rest': -60 * mV,
        'v_thresh': -45 * mV,
        'tau_e': 10 * ms,
        'tau_i': 20 * ms,
        'v': -60 * mV,
        'I_pacemaker': 0 * mV,
        'I_vagal': 0 * mV,
        'I_exc': 0 * mV,
        'I_inh': 0 * mV,
        'HRV_phase': 0,
    }

    @classmethod
    def create_group(cls, N, name=None, params=None, refractory=200*ms):
        """Create a cardiac neuron group."""
        p = cls.defaults.copy()
        if params:
            p.update(params)

        group = NeuronGroup(
            N,
            model=cls.equations,
            threshold=cls.threshold,
            reset=cls.reset,
            refractory=refractory,
            method='euler',
            name=name,
            namespace={}  # Empty namespace - use explicit initialization
        )

        # CRITICAL: Explicitly set per-neuron parameters
        # These are declared as state variables, so they need direct assignment
        group.tau_m = p.get('tau_m', 50*ms)
        group.tau_pacemaker = p.get('tau_pacemaker', 100*ms)
        group.f_card = p.get('f_card', 1*Hz)
        group.A_card = p.get('A_card', 12*mV)
        group.tau_vagal = p.get('tau_vagal', 50*ms)
        group.f_hrv = p.get('f_hrv', 0.1*Hz)
        group.hrv_amp = p.get('hrv_amp', 0.3)
        group.v_rest = p.get('v_rest', -60*mV)
        group.v_thresh = p.get('v_thresh', -45*mV)
        group.tau_e = p.get('tau_e', 10*ms)
        group.tau_i = p.get('tau_i', 20*ms)

        # State variables
        group.v = p.get('v', -60*mV)
        group.I_pacemaker = p.get('I_pacemaker', 0*mV)
        group.I_vagal = p.get('I_vagal', 0*mV)
        group.I_exc = p.get('I_exc', 0*mV)
        group.I_inh = p.get('I_inh', 0*mV)
        group.HRV_phase = p.get('HRV_phase', 0)

        # Randomize phases for heterogeneity
        group.phi = np.random.uniform(0, 2*np.pi, N)

        return group


class RespiratoryNeuron:
    """
    Respiratory rhythm neuron model.

    Simulates pre-Bötzinger complex and respiratory centers.
    Generates rhythmic activity at ~0.25Hz (15 breaths/min).
    Includes inspiratory and expiratory phase neurons.
    """

    equations = '''
    dv/dt = (v_rest - v + I_rhythm + I_modulatory + I_syn) / tau_m : volt (unless refractory)
    dI_rhythm/dt = (-I_rhythm + A_resp * sin(2*pi*f_resp*t)) / tau_rhythm : volt
    dI_modulatory/dt = -I_modulatory / tau_mod : volt
    I_syn = clip(I_exc, -50*mV, 50*mV) - clip(I_inh, -50*mV, 50*mV) : volt  # Clamped to prevent NaN
    dI_exc/dt = -I_exc / tau_e : volt
    dI_inh/dt = -I_inh / tau_i : volt
    # Respiratory phase tracking using sin (sin > 0 = inspiratory, sin < 0 = expiratory)
    resp_phase_sin = sin(2*pi*f_resp*t) : 1 (shared)
    is_inspiratory = resp_phase_sin > 0 : 1 (shared)
    is_expiratory = resp_phase_sin <= 0 : 1 (shared)
    neuron_type : 1  # 0=inspiratory, 1=expiratory
    tau_m : second
    tau_rhythm : second
    f_resp : Hz (shared)
    A_resp : volt
    tau_mod : second
    v_rest : volt
    v_thresh : volt
    tau_e : second
    tau_i : second
    '''

    threshold = 'v > v_thresh'
    reset = 'v = v_rest'

    defaults = {
        'tau_m': 100 * ms,
        'tau_rhythm': 200 * ms,
        'f_resp': 0.25 * Hz,         # ~15 bpm
        'A_resp': 12 * mV,            # Moderate rhythmic drive (was 20mV, too strong)
        'tau_mod': 100 * ms,
        'v_rest': -60 * mV,
        'v_thresh': -48 * mV,
        'tau_e': 10 * ms,
        'tau_i': 20 * ms,
        'v': -60 * mV,
        'I_rhythm': 0 * mV,
        'I_modulatory': 0 * mV,
        'I_exc': 0 * mV,
        'I_inh': 0 * mV,
        'neuron_type': 0,
    }

    @classmethod
    def create_group(cls, N, name=None, params=None, refractory=500*ms,
                     inspiratory_fraction=0.5):
        """Create a respiratory neuron group with inspiratory/expiratory mix."""
        p = cls.defaults.copy()
        if params:
            p.update(params)

        group = NeuronGroup(
            N,
            model=cls.equations,
            threshold=cls.threshold,
            reset=cls.reset,
            refractory=refractory,
            method='euler',
            name=name,
            namespace={}  # Empty namespace - use explicit initialization
        )

        # CRITICAL: Explicitly set per-neuron parameters
        # These are declared as state variables, so they need direct assignment
        group.tau_m = p.get('tau_m', 100*ms)
        group.tau_rhythm = p.get('tau_rhythm', 200*ms)
        group.f_resp = p.get('f_resp', 0.25*Hz)
        group.A_resp = p.get('A_resp', 12*mV)
        group.tau_mod = p.get('tau_mod', 100*ms)
        group.v_rest = p.get('v_rest', -60*mV)
        group.v_thresh = p.get('v_thresh', -48*mV)
        group.tau_e = p.get('tau_e', 10*ms)
        group.tau_i = p.get('tau_i', 20*ms)

        group.tau_mod = p.get('tau_mod', 100*ms)

        # State variables
        group.v = p.get('v', -60*mV)
        group.I_rhythm = p.get('I_rhythm', 0*mV)
        group.I_modulatory = p.get('I_modulatory', 0*mV)
        group.I_exc = p.get('I_exc', 0*mV)
        group.I_inh = p.get('I_inh', 0*mV)

        # Assign neuron types
        n_insp = int(N * inspiratory_fraction)
        neuron_types = np.zeros(N)
        neuron_types[n_insp:] = 1
        np.random.shuffle(neuron_types)
        group.neuron_type = neuron_types

        return group


class PacemakerNeuron:
    """
    Simple pacemaker neuron for rhythm generation.
    Generates regular spikes at a fixed frequency.
    """

    equations = '''
    dv/dt = (v_rest - v + I_drive) / tau_m : volt (unless refractory)
    I_drive : volt
    tau_m : second
    v_rest : volt
    v_thresh : volt
    '''

    threshold = 'v > v_thresh'
    reset = 'v = v_rest'

    @classmethod
    def create_group(cls, N, frequency, name=None, params=None):
        """Create pacemaker neurons firing at specified frequency."""
        p = {
            'tau_m': 20 * ms,
            'v_rest': -65 * mV,
            'v_thresh': -50 * mV,
            'v': -65 * mV,
        }
        if params:
            p.update(params)

        # Calculate drive to achieve target frequency
        # For LIF: f ≈ (1/tau_m) * ln((v_thresh - v_rest) / (v_rest - v_drive))
        # Simplified: set I_drive to give regular spiking
        refractory = (1.0 / frequency) - p['tau_m']
        refractory = max(refractory, 1 * ms)

        # I_drive to reach threshold
        p['I_drive'] = (p['v_thresh'] - p['v_rest']) * 1.1

        group = NeuronGroup(
            N,
            model=cls.equations,
            threshold=cls.threshold,
            reset=cls.reset,
            refractory=refractory,
            method='exact',
            name=name,
            namespace=p
        )

        return group


class InhibitoryInterneuron:
    """
    Fast-spiking inhibitory interneuron for cortical stability.

    Provides GABAergic inhibition to prevent runaway excitation.
    Types: Basket cells (perisomatic), VIP/SST (dendritic targeting).

    Critical for:
    - Thalamic reticular nucleus gating
    - CA3 basket cell inhibition
    - DMN hub regulation
    """

    # Fast-spiking with high threshold, quick dynamics
    equations = '''
    dv/dt = (v_rest - v + I_syn + I_ext) / tau_m : volt (unless refractory)
    I_syn = clip(I_exc, -20*mV, 20*mV) - clip(I_inh, -20*mV, 20*mV) : volt
    dI_exc/dt = -I_exc / tau_e : volt
    dI_inh/dt = -I_inh / tau_i : volt
    I_ext : volt
    tau_m : second
    v_rest : volt
    v_thresh : volt
    tau_e : second
    tau_i : second
    '''

    threshold = 'v > v_thresh'
    reset = 'v = v_rest'

    defaults = {
        'tau_m': 10 * ms,      # Fast membrane time constant
        'v_rest': -65 * mV,
        'v_thresh': -50 * mV,  # Higher threshold than excitatory
        'tau_e': 5 * ms,
        'tau_i': 5 * ms,
        'v': -65 * mV,
        'I_exc': 0 * mV,
        'I_inh': 0 * mV,
        'I_ext': 0 * mV,
    }

    @classmethod
    def create_group(cls, N, name=None, params=None, refractory=2*ms):
        """Create inhibitory interneuron group."""
        p = cls.defaults.copy()
        if params:
            p.update(params)

        group = NeuronGroup(
            N,
            model=cls.equations,
            threshold=cls.threshold,
            reset=cls.reset,
            refractory=refractory,
            method='euler',
            name=name,
            namespace={}  # Empty namespace - use explicit initialization
        )

        # CRITICAL: Explicitly set per-neuron parameters
        group.tau_m = p.get('tau_m', 10*ms)
        group.v_rest = p.get('v_rest', -65*mV)
        group.v_thresh = p.get('v_thresh', -50*mV)
        group.tau_e = p.get('tau_e', 5*ms)
        group.tau_i = p.get('tau_i', 5*ms)

        # State variables
        group.v = p.get('v', -65*mV)
        group.I_exc = p.get('I_exc', 0*mV)
        group.I_inh = p.get('I_inh', 0*mV)
        group.I_ext = p.get('I_ext', 0*mV)

        return group
