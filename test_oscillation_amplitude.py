"""
Test to find the right oscillation amplitude for reliable spiking.
"""
from brian2 import NeuronGroup, SpikeMonitor, run, ms, mV, Hz
import numpy as np

# Test different amplitudes
amplitudes = [8, 10, 15, 18, 20, 25, 30]

for amp_mv in amplitudes:
    # Oscillatory neuron model (simplified)
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

    # Set parameters
    group.tau_m = 15 * ms
    group.tau_osc = 10 * ms
    group.f_osc = 10 * Hz
    group.A_osc = amp_mv * mV
    group.v_rest = -65 * mV
    group.v_thresh = -50 * mV
    group.v = -65 * mV
    group.I_osc = 0 * mV

    monitor = SpikeMonitor(group)
    run(1000 * ms)

    rate = monitor.num_spikes / 10  # spikes per neuron per second
    print(f"A_osc = {amp_mv}mV → {rate:.1f} Hz (target: 10 Hz)")

print("\n--- Now testing with tau_m=20ms (OscillatoryNeuron default) ---")

for amp_mv in amplitudes:
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

    group.tau_m = 10 * ms  # OscillatoryNeuron default
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
    print(f"A_osc = {amp_mv}mV → {rate:.1f} Hz (target: 10 Hz)")
