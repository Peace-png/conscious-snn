"""
Can higher amplitude compensate for higher tau_m?
"""
from brian2 import NeuronGroup, SpikeMonitor, run, ms, mV, Hz, start_scope

print("Testing amplitude compensation for high tau_m...")
print("-" * 60)

for tau_m_ms in [20, 25, 30, 35]:
    print(f"\ntau_m = {tau_m_ms}ms:")
    for amp_mv in [25, 30, 35, 40, 50]:
        start_scope()
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
        )
        group.tau_m = tau_m_ms * ms
        group.tau_osc = 10 * ms
        group.f_osc = 10 * Hz
        group.A_osc = amp_mv * mV
        group.v_rest = -65 * mV
        group.v_thresh = -50 * mV
        group.v = -65 * mV
        group.I_osc = 0 * mV

        monitor = SpikeMonitor(group)
        run(1000 * ms)
        rate = monitor.num_spikes / 10
        status = "✅" if 8 <= rate <= 12 else ""
        print(f"  A_osc = {amp_mv}mV → {rate:5.1f} Hz {status}")
