"""
Fuel Efficiency Hypothesis Validator using Brian2 Oscillator Dynamics

Maps fuel efficiency hypotheses to oscillator models and validates them
through 10s simulations with stability metric extraction.

Physics Constraints:
- 4E-FE engine: ~1300-160 HP
- Tyre pressure: 29-35 PSI
- Driving RPM sweet spot: 2000-2500
- Speed reduction: realistic 0-15% savings at highway speeds
"""

import json
import numpy as np
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
from scipy import signal
from scipy.fft import fft, fftfreq

from brian2 import (
    NeuronGroup, Network, SpikeMonitor, StateMonitor,
    run, start_scope, ms, mV, Hz, defaultclock
)


@dataclass
class Hypothesis:
    """Represents a fuel efficiency hypothesis."""
    id: str
    description: str
    category: str  # driving, maintenance, modification
    expected_savings_pct: float
    rpm_band: Tuple[float, float]  # (min_rpm, max_rpm) where effect is strongest
    oscillator_freq_hz: float  # Mapped oscillator frequency
    mechanism: str  # How it affects engine/vehicle dynamics


# Define hypotheses from the research
HYPOTHESES = [
    Hypothesis(
        id="H1",
        description="Smooth acceleration vs aggressive driving saves 10-40%",
        category="driving",
        expected_savings_pct=25.0,
        rpm_band=(2000, 2500),
        oscillator_freq_hz=0.5,  # Low frequency - smooth transitions
        mechanism="Reduced throttle oscillations lead to stable fuel delivery"
    ),
    Hypothesis(
        id="H2",
        description="Highway speed reduction (100 vs 110 km/h) saves 10-15%",
        category="driving",
        expected_savings_pct=12.5,
        rpm_band=(2200, 2800),  # Lower RPM at lower speed
        oscillator_freq_hz=0.7,  # Air drag ~ v^2 relationship
        mechanism="Quadratic drag reduction creates stable operating point"
    ),
    Hypothesis(
        id="H3",
        description="Correct tyre pressure (29-35 PSI) saves up to 3%",
        category="maintenance",
        expected_savings_pct=3.0,
        rpm_band=(2000, 3000),  # Affects all RPM
        oscillator_freq_hz=2.0,  # Rolling resistance frequency
        mechanism="Optimal contact patch reduces rolling resistance harmonics"
    ),
    Hypothesis(
        id="H4",
        description="Shift at optimal RPM (2000-2200) saves 5-15%",
        category="driving",
        expected_savings_pct=10.0,
        rpm_band=(2000, 2200),
        oscillator_freq_hz=1.0,  # Gear change frequency
        mechanism="Engine operates at peak thermal efficiency band"
    ),
    Hypothesis(
        id="H5",
        description="Anticipate stops (coast early) saves 5-10%",
        category="driving",
        expected_savings_pct=7.5,
        rpm_band=(1000, 2000),  # Lower RPM during coasting
        oscillator_freq_hz=0.3,  # Infrequent braking events
        mechanism="Reduced kinetic energy dissipation creates stable momentum"
    ),
    Hypothesis(
        id="H6",
        description="Oxygen sensor replacement (if failed) saves up to 40%",
        category="maintenance",
        expected_savings_pct=40.0,
        rpm_band=(2000, 4000),  # Affects all operating points
        oscillator_freq_hz=5.0,  # O2 sensor sampling rate
        mechanism="Closed-loop fuel control maintains optimal AFR"
    ),
    Hypothesis(
        id="H7",
        description="Low rolling resistance tyres save 2-5%",
        category="modification",
        expected_savings_pct=3.5,
        rpm_band=(2000, 3000),
        oscillator_freq_hz=3.0,  # Tyre vibration frequency
        mechanism="Reduced hysteresis in tyre compound"
    ),
    Hypothesis(
        id="H8",
        description="Remove roof rack saves 1-5%",
        category="modification",
        expected_savings_pct=3.0,
        rpm_band=(2500, 3500),  # Highway speeds
        oscillator_freq_hz=1.5,  # Aerodynamic turbulence
        mechanism="Reduced aerodynamic drag coefficient"
    ),
]


class OscillatorValidator:
    """
    Validates hypotheses using Brian2 oscillator dynamics.

    Maps each hypothesis to an oscillator model:
    - Oscillation frequency represents the underlying physical frequency
    - Stability indicates whether the hypothesis creates a stable operating regime
    - Phase coherence indicates how well the behavior aligns with optimal engine operation
    """

    # Brian2 oscillator equations - subthreshold oscillation with phase tracking
    OSCILLATOR_EQUATIONS = '''
    dv/dt = (v_rest - v + I_osc + I_drive + I_syn) / tau_m : volt (unless refractory)
    dI_osc/dt = (-I_osc + A_osc * sin(2*pi*f_osc*t + phi)) / tau_osc : volt
    dI_drive/dt = -I_drive / tau_drive : volt
    dI_syn/dt = -I_syn / tau_syn : volt
    dphi/dt = 2*pi*df : 1  # Phase drift
    tau_m : second
    tau_osc : second
    tau_drive : second
    tau_syn : second
    f_osc : Hz
    A_osc : volt
    df : Hz  # Frequency drift
    v_rest : volt
    v_thresh : volt
    '''

    THRESHOLD = 'v > v_thresh'
    RESET = 'v = v_rest'

    # Engine RPM frequency mapping: 2000-2500 RPM corresponds to 33-42 Hz rotation
    # But we model the SYSTEM dynamics at a lower frequency (0.1-10 Hz)

    def __init__(self, duration_ms: float = 10000):
        """Initialize validator with simulation duration."""
        self.duration_ms = duration_ms
        self.results = []

    def create_oscillator_group(self, hypothesis: Hypothesis, n_neurons: int = 100) -> NeuronGroup:
        """
        Create an oscillator group representing a hypothesis.

        The oscillator frequency maps to the physical mechanism frequency.
        The amplitude and stability characteristics represent the hypothesis validity.
        """
        # Map hypothesis to oscillator parameters
        # Higher expected savings -> higher amplitude (stronger effect)
        A_osc = (hypothesis.expected_savings_pct / 40.0) * 15 * mV  # Scale to 0-15mV

        # RPM band mapping to frequency modulation
        # RPM band centered in sweet spot (2000-2500) -> more stable
        rpm_center = (hypothesis.rpm_band[0] + hypothesis.rpm_band[1]) / 2
        sweet_spot_distance = abs(rpm_center - 2250) / 1000  # Distance from 2250 RPM

        # Closer to sweet spot = lower frequency drift (more stable)
        df = sweet_spot_distance * 0.1 * Hz  # Frequency drift

        group = NeuronGroup(
            n_neurons,
            model=self.OSCILLATOR_EQUATIONS,
            threshold=self.THRESHOLD,
            reset=self.RESET,
            refractory=5*ms,
            method='euler',
            name=f'osc_{hypothesis.id}',
            namespace={}
        )

        # Set parameters
        group.tau_m = 20*ms
        group.tau_osc = 10*ms
        group.tau_drive = 100*ms
        group.tau_syn = 50*ms
        group.f_osc = hypothesis.oscillator_freq_hz * Hz
        group.A_osc = A_osc
        group.df = df
        group.v_rest = -65*mV
        group.v_thresh = -50*mV

        # Random initial conditions
        group.v = -65*mV + np.random.randn(n_neurons) * 2*mV
        group.I_osc = 0*mV
        group.I_drive = 0*mV
        group.I_syn = 0*mV
        group.phi = np.random.uniform(0, 2*np.pi, n_neurons)

        return group

    def apply_rpm_driving(self, group: NeuronGroup, rpm_band: Tuple[float, float]):
        """
        Apply driving input representing engine RPM.

        Simulates the RPM as a driving force on the oscillator.
        """
        # Map RPM to voltage drive
        # Sweet spot (2000-2500 RPM) = optimal drive
        rpm_center = (rpm_band[0] + rpm_band[1]) / 2

        # Calculate drive strength (max at 2250 RPM)
        optimal_rpm = 2250
        drive_strength = 1.0 - abs(rpm_center - optimal_rpm) / 1500
        drive_strength = max(0.2, min(1.0, drive_strength))

        group.I_drive = drive_strength * 10*mV

    def calculate_lyapunov_exponent(self, voltage_trace: np.ndarray, dt: float) -> float:
        """
        Estimate the Lyapunov exponent from voltage trace.

        Positive = chaotic/unstable
        Negative = stable limit cycle
        Near zero = marginally stable

        Uses Rosenstein's algorithm (simplified).
        """
        n = len(voltage_trace)
        if n < 100:
            return 0.0

        # Normalize
        trace = (voltage_trace - np.mean(voltage_trace)) / (np.std(voltage_trace) + 1e-10)

        # Find nearest neighbor distances over time
        # Simplified: measure divergence rate
        m = 10  # Embedding dimension
        tau = int(0.1 / dt)  # Delay

        divergences = []
        for i in range(n - m * tau - 10):
            # Find nearest neighbor
            min_dist = float('inf')
            min_j = i + 1
            for j in range(i + 1, min(i + 100, n - m * tau)):
                dist = np.sum((trace[i:i+m*tau:tau] - trace[j:j+m*tau:tau])**2)
                if dist < min_dist and dist > 0:
                    min_dist = dist
                    min_j = j

            # Measure divergence after 10 steps
            if min_j + 10 < n - m * tau:
                future_dist = np.sqrt(np.sum((trace[i+10:i+10+m*tau:tau] -
                                               trace[min_j+10:min_j+10+m*tau:tau])**2))
                if future_dist > 0 and min_dist > 0:
                    divergences.append(np.log(future_dist / np.sqrt(min_dist)))

        if len(divergences) == 0:
            return 0.0

        # Lyapunov exponent is the average divergence rate
        lyap = np.mean(divergences) / (10 * dt)
        return lyap

    def calculate_phase_coherence(self, voltage_trace: np.ndarray, target_freq: float, dt: float) -> float:
        """
        Calculate phase coherence with target frequency.

        High coherence (>0.8) = oscillator locks to expected frequency
        Low coherence (<0.4) = oscillator drifts or is unstable
        """
        n = len(voltage_trace)
        if n < 100:
            return 0.0

        # Normalize
        trace = (voltage_trace - np.mean(voltage_trace)) / (np.std(voltage_trace) + 1e-10)

        # Compute analytic signal (Hilbert transform)
        analytic = signal.hilbert(trace)
        instantaneous_phase = np.unwrap(np.angle(analytic))

        # Compute expected phase based on target frequency
        time = np.arange(n) * dt
        expected_phase = 2 * np.pi * target_freq * time

        # Phase difference
        phase_diff = instantaneous_phase - expected_phase

        # Wrap to [-pi, pi]
        phase_diff = np.mod(phase_diff + np.pi, 2*np.pi) - np.pi

        # Coherence: 1 - normalized phase variance
        phase_variance = np.var(phase_diff)
        coherence = 1.0 - min(1.0, phase_variance / (np.pi**2 / 3))  # Uniform dist variance

        return max(0.0, coherence)

    def calculate_frequency_match(self, voltage_trace: np.ndarray, target_freq: float, dt: float) -> Tuple[float, float]:
        """
        Calculate the dominant frequency and how well it matches target.

        Returns (dominant_freq, match_score)
        """
        n = len(voltage_trace)
        if n < 100:
            return 0.0, 0.0

        # FFT
        yf = fft(voltage_trace - np.mean(voltage_trace))
        xf = fftfreq(n, dt)

        # Find dominant frequency (positive frequencies only)
        pos_mask = xf > 0
        xf_pos = xf[pos_mask]
        yf_pos = np.abs(yf[pos_mask])

        if len(xf_pos) == 0:
            return 0.0, 0.0

        # Find peak
        peak_idx = np.argmax(yf_pos)
        dominant_freq = xf_pos[peak_idx]

        # Match score: how close is dominant to target
        freq_ratio = min(dominant_freq, target_freq) / max(dominant_freq, target_freq, 1e-10)
        match_score = freq_ratio if freq_ratio > 0 else 0.0

        return float(dominant_freq), float(match_score)

    def validate_hypothesis(self, hypothesis: Hypothesis) -> Dict:
        """
        Run a 10s simulation and extract stability metrics.

        Returns dict with:
        - hypothesis: description
        - stable: boolean
        - confidence: float (0-1)
        - lyapunov_exponent: float
        - phase_coherence: float
        - frequency_match: float
        - dominant_freq: float
        """
        start_scope()

        # Create oscillator network
        n_neurons = 100
        group = self.create_oscillator_group(hypothesis, n_neurons)

        # Apply driving force (simulating engine RPM)
        self.apply_rpm_driving(group, hypothesis.rpm_band)

        # Monitors
        spike_mon = SpikeMonitor(group, name='spikes')
        state_mon = StateMonitor(group, ['v', 'I_osc'], record=range(10), name='states')

        # Build network
        net = Network(group, spike_mon, state_mon)

        # Run simulation
        duration_sec = self.duration_ms / 1000.0
        net.run(duration_sec * 1000 * ms)

        # Extract traces (mean across recorded neurons)
        v_trace = np.mean(state_mon.v / mV, axis=0)
        t_trace = np.array(state_mon.t / ms)
        dt = t_trace[1] - t_trace[0] if len(t_trace) > 1 else 0.001

        # Convert dt to seconds
        dt_sec = dt / 1000.0

        # Calculate metrics
        lyap = self.calculate_lyapunov_exponent(v_trace, dt_sec)
        coherence = self.calculate_phase_coherence(v_trace, hypothesis.oscillator_freq_hz, dt_sec)
        dom_freq, freq_match = self.calculate_frequency_match(v_trace, hypothesis.oscillator_freq_hz, dt_sec)

        # Determine stability
        # Negative Lyapunov + high coherence = stable
        # Positive Lyapunov = chaotic/unstable
        # Low coherence = doesn't lock to expected behavior

        is_stable = False
        confidence = 0.0

        if lyap < 0 and coherence > 0.6:
            is_stable = True
            confidence = min(1.0, 0.5 + coherence * 0.3 + min(0.2, -lyap * 0.1))
        elif lyap < 0 and coherence > 0.4:
            is_stable = True
            confidence = 0.4 + coherence * 0.2
        elif lyap > 0.1:
            is_stable = False
            confidence = min(1.0, 0.3 + lyap * 0.5)  # High lyap = confidently unstable
        else:
            # Inconclusive
            is_stable = None
            confidence = 0.3

        # Spike statistics
        spike_count = len(spike_mon.t)
        mean_firing_rate = spike_count / (n_neurons * duration_sec) if duration_sec > 0 else 0

        return {
            "hypothesis_id": hypothesis.id,
            "hypothesis": hypothesis.description,
            "category": hypothesis.category,
            "expected_savings_pct": hypothesis.expected_savings_pct,
            "stable": "STABLE" if is_stable is True else ("UNSTABLE" if is_stable is False else "INCONCLUSIVE"),
            "confidence": round(confidence, 3),
            "metrics": {
                "lyapunov_exponent": round(lyap, 4),
                "phase_coherence": round(coherence, 4),
                "dominant_frequency_hz": round(dom_freq, 4),
                "frequency_match_score": round(freq_match, 4),
                "mean_firing_rate_hz": round(mean_firing_rate, 2),
                "total_spikes": spike_count
            },
            "physics_validation": {
                "rpm_band": hypothesis.rpm_band,
                "in_sweet_spot": 2000 <= hypothesis.rpm_band[0] <= 2500 or
                                  2000 <= hypothesis.rpm_band[1] <= 2500,
                "oscillator_freq_physical": hypothesis.oscillator_freq_hz,
                "mechanism": hypothesis.mechanism
            }
        }

    def run_all_hypotheses(self) -> List[Dict]:
        """Validate all hypotheses and return results."""
        results = []

        print("=" * 60)
        print("FUEL EFFICIENCY HYPOTHESIS VALIDATION")
        print("=" * 60)
        print(f"Simulation duration: {self.duration_ms}ms")
        print(f"Number of hypotheses: {len(HYPOTHESES)}")
        print()

        for i, hyp in enumerate(HYPOTHESES):
            print(f"[{i+1}/{len(HYPOTHESES)}] Validating {hyp.id}: {hyp.description[:50]}...")

            result = self.validate_hypothesis(hyp)
            results.append(result)

            print(f"    Status: {result['stable']}")
            print(f"    Confidence: {result['confidence']:.2f}")
            print(f"    Lyapunov: {result['metrics']['lyapunov_exponent']:.4f}")
            print(f"    Coherence: {result['metrics']['phase_coherence']:.4f}")
            print()

        return results


def main():
    """Run hypothesis validation and output results."""
    validator = OscillatorValidator(duration_ms=10000)
    results = validator.run_all_hypotheses()

    # Output JSON
    output = {
        "simulation_results": results,
        "metadata": {
            "duration_ms": 10000,
            "n_neurons_per_hypothesis": 100,
            "physics_constraints": {
                "engine": "4E-FE 1.3L",
                "power_hp": "130-160",
                "tyre_pressure_psi": "29-35",
                "optimal_rpm_band": [2000, 2500],
                "realistic_savings_range_pct": [0, 15]
            }
        }
    }

    # Write to file
    output_path = "/home/peace/conscious_snn/research-toyota-starlet-fuel-efficiency/simulation_results.json"
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)

    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)

    stable_count = sum(1 for r in results if r['stable'] == 'STABLE')
    unstable_count = sum(1 for r in results if r['stable'] == 'UNSTABLE')
    inconclusive_count = sum(1 for r in results if r['stable'] == 'INCONCLUSIVE')

    print(f"STABLE: {stable_count}/{len(results)}")
    print(f"UNSTABLE: {unstable_count}/{len(results)}")
    print(f"INCONCLUSIVE: {inconclusive_count}/{len(results)}")
    print()

    # Show top hypotheses by confidence
    sorted_results = sorted(results, key=lambda x: x['confidence'], reverse=True)
    print("Top hypotheses by confidence:")
    for r in sorted_results[:3]:
        print(f"  {r['hypothesis_id']}: {r['hypothesis'][:40]}...")
        print(f"    Confidence: {r['confidence']:.2f}, Status: {r['stable']}")

    print()
    print(f"Results written to: {output_path}")

    return output


if __name__ == "__main__":
    main()
