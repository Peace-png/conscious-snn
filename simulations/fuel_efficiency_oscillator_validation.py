"""
Fuel Efficiency Hypothesis Validation via Brian2 Coupled Oscillators

Maps automotive parameters to oscillator dynamics:
- Engine RPM -> Primary oscillator frequency (normalized)
- Tire pressure -> Damping coefficient (higher PSI = less damping)
- Driving behavior (smooth vs aggressive) -> Coupling strength

Three testable hypotheses:
1. H1: Optimal RPM Band (2000-2500) yields maximum efficiency oscillation
2. H2: Higher tire pressure (40 PSI vs 32 PSI) reduces energy loss (lower damping)
3. H3: Smooth driving (strong coupling) maintains stable oscillation vs aggressive (weak coupling)

Validation via spike count and oscillation stability metrics.
"""

import numpy as np
from brian2 import (
    Network, NeuronGroup, Synapses, SpikeMonitor, StateMonitor,
    Hz, ms, mV, nA, run, start_scope, defaultclock
)
from pathlib import Path


class FuelEfficiencyOscillatorNetwork:
    """
    Coupled oscillator network to validate fuel efficiency hypotheses.

    Domain mapping:
    - Engine RPM / 1000 -> oscillator frequency (Hz)
    - 2000 RPM = 2 Hz, 2500 RPM = 2.5 Hz
    - Tire pressure -> damping (tau_osc): higher PSI = faster tau = less energy loss
    - Driving smoothness -> coupling weight: smooth = 0.8, aggressive = 0.2
    """

    # Normalized parameters
    # RPM 2000-2500 maps to 2.0-2.5 Hz (optimal band)
    # Damping: tau_osc lower = less energy loss (maps to higher tire pressure)
    # Coupling: higher = more synchronized/efficient

    def __init__(self, n_neurons=100):
        self.n_neurons = n_neurons
        self.network = None
        self.peak_efficiency_rpm_low = 2.0  # Hz (represents 2000 RPM)
        self.peak_efficiency_rpm_high = 2.5  # Hz (represents 2500 RPM)

    def build(self, rpm_freq, tire_pressure_psi, coupling_strength):
        """
        Build the oscillator network with given parameters.

        Args:
            rpm_freq: Oscillator frequency in Hz (represents RPM/1000)
            tire_pressure_psi: Tire pressure (32-45 PSI range)
            coupling_strength: 0.0-1.0 (smooth=0.8, aggressive=0.2)
        """
        start_scope()

        # Map tire pressure to damping time constant
        # Higher pressure = faster response = less energy loss
        # 32 PSI -> tau = 15ms (high damping)
        # 40 PSI -> tau = 8ms (low damping)
        base_tau = 20  # ms at minimum pressure
        tau_osc = (base_tau - (tire_pressure_psi - 28) * 0.5) * ms
        tau_osc = max(tau_osc, 5*ms)  # Floor at 5ms

        # Oscillator neuron equations
        equations = '''
        dv/dt = (v_rest - v + I_osc + I_syn + I_ext) / tau_m : volt (unless refractory)
        dI_osc/dt = (-I_osc + A_osc * sin(2*pi*f_osc*t)) / tau_osc : volt
        I_syn = I_exc - I_inh : volt
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

        # Create neuron group
        self.neurons = NeuronGroup(
            self.n_neurons,
            model=equations,
            threshold='v > v_thresh',
            reset='v = v_rest',
            refractory=2*ms,
            method='euler',
            name='efficiency_oscillators'
        )

        # Set parameters
        self.neurons.tau_m = 10*ms
        self.neurons.tau_osc = tau_osc
        self.neurons.f_osc = rpm_freq * Hz
        self.neurons.A_osc = 25*mV  # Oscillation amplitude
        self.neurons.v_rest = -65*mV
        self.neurons.v_thresh = -50*mV
        self.neurons.tau_e = 5*ms
        self.neurons.tau_i = 10*ms

        # Initial conditions
        self.neurons.v = -65*mV
        self.neurons.I_osc = 0*mV
        self.neurons.I_exc = 0*mV
        self.neurons.I_inh = 0*mV
        self.neurons.I_ext = 0*mV

        # Add coupling between neurons (represents driving smoothness)
        self.synapses = Synapses(
            self.neurons, self.neurons,
            model='w : 1',
            on_pre='I_exc_post += w*5*mV',
            name='coupling'
        )
        self.synapses.connect(p=0.1)  # 10% connectivity
        self.synapses.w = coupling_strength

        # Monitors
        self.spike_monitor = SpikeMonitor(self.neurons, name='spikes')
        self.state_monitor = StateMonitor(
            self.neurons, ['v', 'I_osc'],
            record=[0, 1, 2],  # Record first 3 neurons
            name='states'
        )

        # Build network
        self.network = Network([
            self.neurons,
            self.synapses,
            self.spike_monitor,
            self.state_monitor
        ])

        return self

    def run(self, duration_ms=5000):
        """Run simulation for specified duration."""
        self.network.run(duration_ms * ms)
        return self

    def compute_efficiency_metrics(self):
        """
        Compute efficiency metrics from simulation results.

        Returns:
            dict with:
            - spike_count: Total spikes (lower = more efficient energy use)
            - mean_firing_rate: Average Hz per neuron
            - oscillation_coherence: How well neurons synchronize (0-1)
            - energy_efficiency: Higher = better (normalized)
        """
        spikes = self.spike_monitor
        n_spikes = len(spikes.t)

        # Mean firing rate - convert Brian2 quantities to floats
        duration_s = float(spikes.t[-1]) if len(spikes.t) > 0 else 1.0
        mean_rate = n_spikes / (self.n_neurons * duration_s)

        # Oscillation coherence (variance of inter-spike intervals)
        # Convert to float to avoid Brian2 unit issues
        if len(spikes.t) > 10:
            all_isis = np.array([float(x) for x in np.diff(np.sort(spikes.t))])
            isi_std = float(np.std(all_isis))
            isi_mean = float(np.mean(all_isis))
            coherence = 1.0 / (1.0 + isi_std / (isi_mean + 1e-9))
        else:
            coherence = 0.0

        # Energy efficiency: inverse of spike count, normalized
        # Lower spikes for same task = more efficient
        energy_efficiency = 1.0 / (1.0 + n_spikes / 1000)

        return {
            'spike_count': n_spikes,
            'mean_firing_rate': float(mean_rate),
            'oscillation_coherence': float(coherence),
            'energy_efficiency': float(energy_efficiency),
            'duration_s': duration_s
        }


def hypothesis_1_optimal_rpm():
    """
    H1: Peak efficiency at 2000-2500 RPM

    Test multiple RPM values and measure efficiency.
    Expected: Highest efficiency in optimal band.
    """
    print("=" * 60)
    print("HYPOTHESIS 1: Optimal RPM Band (2000-2500)")
    print("=" * 60)

    # Test RPM frequencies (RPM/1000)
    rpm_values = [1.5, 1.8, 2.0, 2.2, 2.5, 2.8, 3.0, 3.5, 4.0]

    results = []
    for rpm in rpm_values:
        net = FuelEfficiencyOscillatorNetwork(n_neurons=50)
        net.build(rpm_freq=rpm, tire_pressure_psi=35, coupling_strength=0.5)
        net.run(duration_ms=2000)
        metrics = net.compute_efficiency_metrics()

        result = {
            'rpm': rpm,
            **metrics
        }
        results.append(result)
        print(f"  RPM {rpm*1000:.0f}: efficiency={metrics['energy_efficiency']:.3f}, "
              f"coherence={metrics['oscillation_coherence']:.3f}, "
              f"spikes={metrics['spike_count']}")

    # Find peak efficiency
    best = max(results, key=lambda x: x['energy_efficiency'])
    print(f"\n  BEST RPM: {best['rpm']*1000:.0f} (efficiency={best['energy_efficiency']:.3f})")

    # Check if peak is in optimal band
    in_optimal = 2.0 <= best['rpm'] <= 2.5
    verdict = "VALIDATED" if in_optimal else "REJECTED"
    print(f"\n  VERDICT: {verdict}")
    print(f"  Peak at {best['rpm']*1000:.0f} RPM, optimal band is 2000-2500 RPM")

    return results, verdict


def hypothesis_2_tire_pressure():
    """
    H2: Higher tire pressure (40 PSI) improves efficiency

    Test multiple pressures and measure energy loss via damping.
    Expected: Lower damping (higher PSI) = better efficiency.
    """
    print("\n" + "=" * 60)
    print("HYPOTHESIS 2: Tire Pressure Effect")
    print("=" * 60)

    # Test tire pressures
    psi_values = [28, 30, 32, 35, 38, 40, 42, 44]

    results = []
    for psi in psi_values:
        net = FuelEfficiencyOscillatorNetwork(n_neurons=50)
        net.build(rpm_freq=2.2, tire_pressure_psi=psi, coupling_strength=0.5)
        net.run(duration_ms=2000)
        metrics = net.compute_efficiency_metrics()

        result = {
            'psi': psi,
            **metrics
        }
        results.append(result)
        print(f"  PSI {psi}: efficiency={metrics['energy_efficiency']:.3f}, "
              f"coherence={metrics['oscillation_coherence']:.3f}, "
              f"spikes={metrics['spike_count']}")

    # Check trend: higher PSI should have higher efficiency
    low_psi_eff = np.mean([r['energy_efficiency'] for r in results[:3]])
    high_psi_eff = np.mean([r['energy_efficiency'] for r in results[-3:]])

    improvement = (high_psi_eff - low_psi_eff) / low_psi_eff * 100

    print(f"\n  Low PSI (28-32) avg efficiency: {low_psi_eff:.3f}")
    print(f"  High PSI (40-44) avg efficiency: {high_psi_eff:.3f}")
    print(f"  Improvement: {improvement:.1f}%")

    verdict = "VALIDATED" if improvement > 0 else "REJECTED"
    print(f"\n  VERDICT: {verdict}")

    return results, verdict


def hypothesis_3_driving_behavior():
    """
    H3: Smooth driving (strong coupling) vs aggressive (weak coupling)

    Strong coupling = neurons synchronized = efficient oscillation
    Weak coupling = neurons desynchronized = energy waste
    """
    print("\n" + "=" * 60)
    print("HYPOTHESIS 3: Driving Behavior (Smooth vs Aggressive)")
    print("=" * 60)

    # Test coupling strengths
    # 0.8 = smooth (high coherence)
    # 0.2 = aggressive (low coherence)
    coupling_values = [0.1, 0.2, 0.3, 0.5, 0.7, 0.8, 0.9]

    results = []
    for coupling in coupling_values:
        net = FuelEfficiencyOscillatorNetwork(n_neurons=50)
        net.build(rpm_freq=2.2, tire_pressure_psi=35, coupling_strength=coupling)
        net.run(duration_ms=2000)
        metrics = net.compute_efficiency_metrics()

        # Label for output
        if coupling >= 0.7:
            label = "smooth"
        elif coupling >= 0.4:
            label = "moderate"
        else:
            label = "aggressive"

        result = {
            'coupling': coupling,
            'label': label,
            **metrics
        }
        results.append(result)
        print(f"  Coupling {coupling:.1f} ({label}): efficiency={metrics['energy_efficiency']:.3f}, "
              f"coherence={metrics['oscillation_coherence']:.3f}")

    # Compare smooth vs aggressive
    smooth_eff = np.mean([r['energy_efficiency'] for r in results if r['coupling'] >= 0.7])
    aggressive_eff = np.mean([r['energy_efficiency'] for r in results if r['coupling'] <= 0.3])

    improvement = (smooth_eff - aggressive_eff) / aggressive_eff * 100

    print(f"\n  Aggressive (0.1-0.3) avg efficiency: {aggressive_eff:.3f}")
    print(f"  Smooth (0.7-0.9) avg efficiency: {smooth_eff:.3f}")
    print(f"  Smooth driving improvement: {improvement:.1f}%")

    verdict = "VALIDATED" if improvement > 0 else "REJECTED"
    print(f"\n  VERDICT: {verdict}")

    return results, verdict


def combined_analysis():
    """
    Run all hypotheses and provide combined verdict.
    """
    print("\n" + "#" * 60)
    print("# FUEL EFFICIENCY HYPOTHESIS VALIDATION")
    print("# Brian2 Coupled Oscillator Simulation")
    print("#" * 60)

    r1, v1 = hypothesis_1_optimal_rpm()
    r2, v2 = hypothesis_2_tire_pressure()
    r3, v3 = hypothesis_3_driving_behavior()

    print("\n" + "#" * 60)
    print("# FINAL VERDICTS")
    print("#" * 60)

    validated = 0
    if v1 == "VALIDATED":
        validated += 1
    if v2 == "VALIDATED":
        validated += 1
    if v3 == "VALIDATED":
        validated += 1

    print(f"\n  H1 (Optimal RPM 2000-2500): {v1}")
    print(f"  H2 (Higher PSI = better): {v2}")
    print(f"  H3 (Smooth > aggressive): {v3}")

    print(f"\n  TOTAL: {validated}/3 hypotheses validated")

    # Recommendations based on results
    print("\n" + "#" * 60)
    print("# PRACTICAL RECOMMENDATIONS")
    print("#" * 60)

    if v1 == "VALIDATED":
        print("  1. Keep RPM in 2000-2500 range for highway driving")
    if v2 == "VALIDATED":
        print("  2. Inflate tires to 40 PSI (check sidewall max)")
    if v3 == "VALIDATED":
        print("  3. Accelerate smoothly, coast to stops")

    return {
        'h1_verdict': v1,
        'h2_verdict': v2,
        'h3_verdict': v3,
        'validated_count': validated
    }


if __name__ == "__main__":
    results = combined_analysis()
