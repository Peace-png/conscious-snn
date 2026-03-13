"""
Direct test of thalamus oscillatory components.
"""
from brian2 import NeuronGroup, SpikeMonitor, run, ms, mV, Hz, start_scope
from core.neurons import OscillatoryNeuron

start_scope()

# Test reticular nucleus with same params
print("Testing reticular nucleus with A_osc=25mV, tau_m=15ms...")
reticular = OscillatoryNeuron.create_group(
    10,
    frequency=10*Hz,
    name='test_reticular',
    params={
        'A_osc': 25*mV,
        'tau_m': 15*ms,
        'v_thresh': -52*mV,
    }
)

monitor_ret = SpikeMonitor(reticular)
run(1000*ms)
rate_ret = monitor_ret.num_spikes / 10
print(f"Reticular: {rate_ret:.1f} Hz (target: 10 Hz)")

# Check actual param values
print(f"  tau_m = {reticular.tau_m}")
print(f"  tau_osc = {reticular.tau_osc}")
print(f"  A_osc = {reticular.A_osc}")

print("\nTesting intralaminar with A_osc=25mV, tau_m=25ms...")
start_scope()
intralaminar = OscillatoryNeuron.create_group(
    10,
    frequency=10*Hz,
    name='test_intralaminar',
    params={
        'A_osc': 25*mV,
        'tau_m': 25*ms,
    }
)

monitor_intra = SpikeMonitor(intralaminar)
run(1000*ms)
rate_intra = monitor_intra.num_spikes / 10
print(f"Intralaminar: {rate_intra:.1f} Hz (target: 10 Hz)")

print(f"  tau_m = {intralaminar.tau_m}")
print(f"  tau_osc = {intralaminar.tau_osc}")
print(f"  A_osc = {intralaminar.A_osc}")

print("\nTesting relay nuclei with A_alpha=25mV, tau_osc=10ms...")
start_scope()
relay = NeuronGroup(
    10,
    model='''
    dv/dt = (v_rest - v + I_osc) / tau_m : volt (unless refractory)
    dI_osc/dt = (-I_osc + A_alpha * sin(2*pi*f_alpha*t)) / tau_osc : volt
    tau_m : second
    tau_osc : second
    f_alpha : Hz
    A_alpha : volt
    v_rest : volt
    v_thresh : volt
    ''',
    threshold='v > v_thresh',
    reset='v = v_rest',
    refractory=5*ms,
    method='euler',
    name='test_relay'
)
relay.tau_m = 20*ms
relay.tau_osc = 10*ms
relay.f_alpha = 10*Hz
relay.A_alpha = 25*mV
relay.v_rest = -65*mV
relay.v_thresh = -50*mV
relay.v = -65*mV
relay.I_osc = 0*mV

monitor_relay = SpikeMonitor(relay)
run(1000*ms)
rate_relay = monitor_relay.num_spikes / 10
print(f"Relay: {rate_relay:.1f} Hz (target: 10 Hz)")
print(f"  tau_m = {relay.tau_m}")
print(f"  tau_osc = {relay.tau_osc}")
print(f"  A_alpha = {relay.A_alpha}")
