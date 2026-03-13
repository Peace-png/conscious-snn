"""
Test thalamus relay_nuclei with and without reticular inhibition.
"""
from brian2 import NeuronGroup, Synapses, SpikeMonitor, run, ms, mV, Hz, start_scope
import numpy as np

start_scope()

print("=== Without reticular inhibition (A_osc=30mV, tau_osc=10ms) ===")
relay = NeuronGroup(
    10,
    model='''
    dv/dt = (v_rest - v + I_osc) / tau_m : volt (unless refractory)
    dI_osc/dt = (-I_osc + A_osc * sin(2*pi*f_osc*t)) / tau_osc : volt
    tau_m : second
    tau_osc : second
    f_osc : Hz
    A_osc : volt
    v_rest : volt
    v_thresh : volt
    ''',
    threshold='v > v_thresh',
    reset='v = v_rest',
    refractory=5*ms,
    method='euler',
    name='test_relay_no_inhibit'
)
relay.tau_m = 20*ms
relay.tau_osc = 10*ms
relay.f_osc = 10*Hz
relay.A_osc = 30*mV  # Correct for tau_m=20ms
relay.v_rest = -65*mV
relay.v_thresh = -50*mV
relay.v = -65*mV
relay.I_osc = 0*mV

monitor = SpikeMonitor(relay)
run(1000*ms)
print(f"Relay (no inhibition): {monitor.num_spikes / 10:.1f} Hz")

# Now test WITH reticular inhibition
print("\n=== With reticular inhibition (reticular at 10Hz, w_syn=8mV) ===")
start_scope()

# Relay nuclei
relay = NeuronGroup(
    10,
    model='''
    dv/dt = (v_rest - v + I_osc - I_inh) / tau_m : volt (unless refractory)
    dI_osc/dt = (-I_osc + A_osc * sin(2*pi*f_osc*t)) / tau_osc : volt
    dI_inh/dt = -I_inh / (10*ms) : volt
    tau_m : second
    tau_osc : second
    f_osc : Hz
    A_osc : volt
    v_rest : volt
    v_thresh : volt
    ''',
    threshold='v > v_thresh',
    reset='v = v_rest',
    refractory=5*ms,
    method='euler',
    name='test_relay_with_inhibit'
)
relay.tau_m = 20*ms
relay.tau_osc = 10*ms
relay.f_osc = 10*Hz
relay.A_osc = 30*mV
relay.v_rest = -65*mV
relay.v_thresh = -50*mV
relay.v = -65*mV
relay.I_osc = 0*mV
relay.I_inh = 0*mV

# Reticular nucleus
reticular = NeuronGroup(
    10,
    model='''
    dv/dt = (v_rest - v + I_osc) / tau_m : volt (unless refractory)
    dI_osc/dt = (-I_osc + A_ret * sin(2*pi*f_ret*t)) / tau_osc : volt
    tau_m : second
    tau_osc : second
    f_ret : Hz
    A_ret : volt
    v_rest : volt
    v_thresh : volt
    ''',
    threshold='v > v_thresh',
    reset='v = v_rest',
    refractory=1*ms,
    method='euler',
    name='test_reticular'
)
reticular.tau_m = 15*ms
reticular.tau_osc = 10*ms
reticular.f_ret = 10*Hz
reticular.A_ret = 25*mV  # Correct for tau_m=15ms
reticular.v_rest = -65*mV
reticular.v_thresh = -52*mV
reticular.v = -65*mV
reticular.I_osc = 0*mV

# Connect reticular to relay (inhibition)
syn = Synapses(
    reticular, relay,
    model='w_syn : volt',
    on_pre='I_inh_post += w_syn',
    delay=3*ms,
    name='ret_to_relay'
)
syn.connect(p=0.3)
syn.w_syn = 8*mV

# Monitors
monitor_relay = SpikeMonitor(relay)
monitor_ret = SpikeMonitor(reticular)

run(1000*ms)

print(f"Relay (with inhibition): {monitor_relay.num_spikes / 10:.1f} Hz")
print(f"Reticular: {monitor_ret.num_spikes / 10:.1f} Hz")
