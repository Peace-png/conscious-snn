"""
Test thalamus with reduced reticular inhibition.
"""
from brian2 import NeuronGroup, Synapses, SpikeMonitor, run, ms, mV, Hz, start_scope
import numpy as np

# Test different inhibition strengths
print("=== Testing different inhibition strengths ===")

for w_inh_mv in [8, 4, 2, 1]:
    for p_conn in [0.3, 0.1]:
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
            name=f'test_relay_w{w_inh_mv}_p{int(p_conn*10)}'
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
        reticular.A_ret = 25*mV
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
        syn.connect(p=p_conn)
        syn.w_syn = w_inh_mv * mV

        # Monitors
        monitor_relay = SpikeMonitor(relay)
        monitor_ret = SpikeMonitor(reticular)

        run(1000*ms)

        rate_relay = monitor_relay.num_spikes / 10
        rate_ret = monitor_ret.num_spikes / 10
        status = "✅" if 8 <= rate_relay <= 12 else ("⚠️" if rate_relay > 0 else "❌")
        print(f"w={w_inh_mv}mV, p={p_conn}: Relay={rate_relay:.1f}Hz, Reticular={rate_ret:.1f}Hz {status}")

print("\n=== Recommendation: Use w_syn=2-2mV, p=0.1-0.2 ===")
