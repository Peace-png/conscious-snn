"""
Test relay nuclei oscillation amplitude directly.
"""
from brian2 import NeuronGroup, SpikeMonitor, run, ms, mV, Hz, start_scope
import numpy as np

start_scope()

# Exactly the thalamus relay_nuclei model
relay = NeuronGroup(
    10,
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
    name='test_relay'
)

# Set parameters exactly as thalamus.py does
relay.tau_m = 20*ms
relay.tau_relay = 15*ms
relay.tau_osc = 10*ms  # Fixed from 50ms
relay.tau_e = 5*ms
relay.tau_i = 10*ms
relay.f_alpha = 10*Hz
relay.A_alpha = 30*mV  # Fixed from 8mV
relay.v_rest = -65*mV
relay.v_thresh = -50*mV
relay.v_burst = -60*mV
relay.v = -65*mV
relay.I_relay = 0*mV
relay.I_osc = 0*mV
relay.I_cortical = 0*mV
relay.I_brainstem = 0*mV
relay.I_exc = 0*mV
relay.I_inh = 0*mV
relay.T_ca = 0*mV
relay.is_bursting = 0
relay.gating = 0.5

monitor = SpikeMonitor(relay)
run(1000*ms)

rate = monitor.num_spikes / 10
print(f"Relay nuclei: {rate:.1f} Hz (target: 10 Hz)")
print(f"A_alpha = {relay.A_alpha}")
print(f"tau_osc = {relay.tau_osc}")
