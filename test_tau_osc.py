"""
Test tau_osc effect on oscillation following.
"""
from brian2 import NeuronGroup, SpikeMonitor, run, ms, mV, Hz

# Test different tau_osc values with A_osc=25mV
tau_osc_values = [5, 10, 20, 50, 100]

for tau_osc_ms in tau_osc_values:
    group = NeuronGroup(
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
        refractory=2*ms,
        method='euler',
        namespace={}
    )

    group.tau_m = 15 * ms
    group.tau_osc = tau_osc_ms * ms  # Varying this
    group.f_osc = 10 * Hz
    group.A_osc = 25 * mV  # Known good amplitude
    group.v_rest = -65 * mV
    group.v_thresh = -50 * mV
    group.v = -65 * mV
    group.I_osc = 0 * mV

    monitor = SpikeMonitor(group)
    run(1000 * ms)

    rate = monitor.num_spikes / 10
    print(f"tau_osc = {tau_osc_ms}ms → {rate:.1f} Hz (target: 10 Hz)")
