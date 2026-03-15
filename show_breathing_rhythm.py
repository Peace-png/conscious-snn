#!/usr/bin/env python3
"""Capture respiratory rhythm from full network"""

import sys
sys.path.insert(0, '/home/peace/conscious_snn')

from brian2 import *
import numpy as np
import matplotlib.pyplot as plt

print('Building full network at scale=0.01...')

from core.config import ConsciousSNNConfig, ScaleParams
from core.base import ConsciousNetwork

start_scope()

config = ConsciousSNNConfig(scale=ScaleParams(0.01))
net = ConsciousNetwork(config)
net.build()

print(f'Network built: {len(net.brian_network.objects)} objects')

# Find all spike monitors
spike_mons = [(obj.name, obj) for obj in net.brian_network.objects if hasattr(obj, 'num_spikes')]
print(f'Found {len(spike_mons)} spike monitors')

# Find respiratory monitors
resp_mons = [(name, mon) for name, mon in spike_mons if 'resp' in name.lower() or 'prebotz' in name.lower()]
print(f'Respiratory monitors: {[n for n,m in resp_mons]}')

print('\nRunning 60s simulation...')
import time
t0 = time.time()
net.run(60000)
print(f'Simulation done in {time.time()-t0:.1f}s')

# Get respiratory spikes
for name, mon in resp_mons:
    print(f'{name}: {mon.num_spikes:,} spikes')

# Get prebotz spikes
prebotz_mon = None
for name, mon in spike_mons:
    if 'prebotz' in name.lower():
        prebotz_mon = mon
        break

if prebotz_mon and prebotz_mon.num_spikes > 0:
    spike_times = prebotz_mon.t / second
    print(f'\nPre-Bötzinger spike times (first 20): {spike_times[:20]}')

    # Bin analysis
    bin_width = 0.5
    bins = np.arange(0, 61, bin_width)
    counts, _ = np.histogram(spike_times, bins)
    centers = (bins[:-1] + bins[1:]) / 2

    # FFT
    from scipy import fft
    n = len(counts)
    freqs = fft.fftfreq(n, bin_width)
    spectrum = np.abs(fft.fft(counts - np.mean(counts)))
    pos_freqs = freqs[1:n//2]
    pos_spec = spectrum[1:n//2]
    dom_idx = np.argmax(pos_spec)
    dom_freq = pos_freqs[dom_idx]

    print(f'\nDominant frequency: {dom_freq:.3f} Hz')
    print(f'Expected: 0.25 Hz (15 breaths/min)')
    print(f'Period: {1/dom_freq:.1f}s')

    # Plot
    fig, axes = plt.subplots(2, 1, figsize=(14, 10))

    # Raster
    ax1 = axes[0]
    n_neurons = len(np.unique(prebotz_mon.i))
    for i, neuron_id in enumerate(np.unique(prebotz_mon.i)[:30]):
        spikes = spike_times[prebotz_mon.i == neuron_id]
        ax1.eventplot(spikes, lineoffsets=i, linelengths=0.8, colors='blue')
    ax1.set_xlabel('Time (s)')
    ax1.set_ylabel('Neuron')
    ax1.set_title('Pre-Bötzinger Spike Raster')
    ax1.set_xlim(0, 60)

    # Population rate
    ax2 = axes[1]
    ax2.plot(centers, counts/bin_width, 'b-', lw=1.5, label='Firing Rate')
    ax2.axhline(np.mean(counts/bin_width), color='r', ls='--', alpha=0.7, label='Mean')
    # Mark 4-second intervals (expected breathing)
    for t in range(0, 61, 4):
        ax2.axvline(t, color='g', alpha=0.3, ls=':')
    ax2.set_xlabel('Time (s)', fontsize=12)
    ax2.set_ylabel('Firing Rate (spikes/s)', fontsize=12)
    ax2.set_title(f'Respiratory Rhythm: {dom_freq:.3f} Hz (Period: {1/dom_freq:.1f}s)', fontsize=14)
    ax2.set_xlim(0, 60)
    ax2.legend()

    plt.tight_layout()
    plt.savefig('/home/peace/conscious_snn/docs/breathing_rhythm.png', dpi=150)
    print(f'\nSaved: docs/breathing_rhythm.png')
else:
    print('No prebotz spikes!')

# Also check cardiac
cardiac_mons = [(n, m) for n, m in spike_mons if 'cardiac' in n.lower() or 'atrial' in n.lower()]
print(f'\nCardiac monitors: {[(n, m.num_spikes) for n, m in cardiac_mons]}')
