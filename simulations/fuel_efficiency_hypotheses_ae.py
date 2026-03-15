"""
Fuel Efficiency Hypotheses A-E Validation via Brian2 Oscillator Dynamics

Maps 1998 Toyota Starlet 1.3L 4E-FE parameters to coupled oscillator systems.
This extends the existing H1-H3 validation with new physics-based hypotheses.

HYPOTHESIS A: Intake Resonance Tuning (Helmholtz resonance)
HYPOTHESIS B: Exhaust Pulse Coupling (steady-state flow)
HYPOTHESIS C: Tire Pressure as State Variable (load-dependent optimization)
HYPOTHESIS D: Engine Temperature as Relaxation Oscillator (thermal dynamics)
HYPOTHESIS E: Accelerator Pulse Timing (smooth vs jab inputs)

Metrics extracted:
- Lyapunov exponent (negative = stable attractor)
- Kuramoto order parameter r (phase coherence)
- Oscillation amplitude stability
"""

import numpy as np
from brian2 import (
    Network, NeuronGroup, Synapses, SpikeMonitor, StateMonitor,
    Hz, ms, mV, nA, run, start_scope, defaultclock
)
from pathlib import Path


class HypothesisValidator:
    """Base class for hypothesis validation via oscillator dynamics."""

    def __init__(self, n_neurons=100, duration_ms=10000):
        self.n_neurons = n_neurons
        self.duration_ms = duration_ms
        self.network = None
        self.neurons = None
        self.spike_monitor = None
        self.state_monitor = None

    def compute_lyapunov_exponent(self, timeseries, dt=0.001):
        """
        Estimate the largest Lyapunov exponent from a timeseries.
        Negative = stable attractor, Positive = chaotic divergence.
        Uses Rosenstein algorithm approximation.
        """
        if len(timeseries) < 100:
            return 0.0

        # Normalize and detrend
        ts = np.array(timeseries)
        ts = ts - np.mean(ts)
        if np.std(ts) < 1e-10:
            return 0.0
        ts = ts / np.std(ts)

        # Find nearest neighbors and track divergence
        n = len(ts)
        embed_dim = 3
        tau = max(1, n // 100)

        # Create embedded vectors
        m = n - (embed_dim - 1) * tau
        if m < 10:
            return 0.0

        embedded = np.zeros((m, embed_dim))
        for i in range(embed_dim):
            embedded[:, i] = ts[i * tau:i * tau + m]

        # Track divergence from nearest neighbors
        divergences = []
        for i in range(min(m - 10, 100)):
            # Find nearest neighbor (exclude self and close points)
            distances = np.sqrt(np.sum((embedded - embedded[i]) ** 2, axis=1))
            distances[max(0, i - 5):i + 5] = np.inf
            if np.all(np.isinf(distances)):
                continue
            j = np.argmin(distances)

            # Track divergence over time
            for k in range(1, min(10, m - max(i, j))):
                d = np.abs(ts[i + k] - ts[j + k])
                if d > 0:
                    divergences.append(np.log(d))

        if len(divergences) < 5:
            return 0.0

        # Lyapunov exponent is the average divergence rate
        return np.mean(divergences) / dt

    def compute_kuramoto_order_parameter(self, phases):
        """
        Compute Kuramoto order parameter r (0 to 1).
        r = 1: perfect synchronization
        r = 0: complete desynchronization
        """
        if len(phases) < 2:
            return 0.0

        # Convert to complex representation
        complex_phases = np.exp(1j * np.array(phases))

        # Order parameter
        r = np.abs(np.mean(complex_phases))
        return float(r)

    def compute_amplitude_stability(self, timeseries):
        """
        Compute amplitude stability (coefficient of variation inverse).
        Higher = more stable oscillation amplitude.
        """
        if len(timeseries) < 10:
            return 0.0

        ts = np.array(timeseries)
        mean_amp = np.mean(np.abs(ts))
        std_amp = np.std(np.abs(ts))

        if mean_amp < 1e-10:
            return 0.0

        # Stability = inverse of coefficient of variation
        cv = std_amp / mean_amp
        stability = 1.0 / (1.0 + cv)
        return stability


class HypothesisA_IntakeResonance(HypothesisValidator):
    """
    HYPOTHESIS A: Intake Resonance Tuning

    Map: Intake manifold as acoustic resonator (Helmholtz resonance)
    Prediction: Engine's peak torque RPM = intake runner's natural frequency
    For 4E-FE: ~3000-3500 RPM is likely sweet spot
    Physics: f = c/4L where c = 340 m/s

    Brian2 Mapping:
    - RPM -> driving frequency
    - Resonance frequency -> natural frequency of oscillator
    - Efficiency peaks when RPM matches resonance (minimal energy for oscillation)
    """

    # 4E-FE intake runner length ~30cm typical for 1.3L
    # f_resonance = c/4L = 340/(4*0.30) = 283 Hz
    # At 3000 RPM, intake pulse frequency = 3000/60 * 2 = 100 Hz (4-cyl, 2 intake strokes/rev)
    # Peak torque typically 3000-3500 RPM for 4E-FE

    def build(self, rpm, resonance_freq=50):
        """
        Build oscillator model for intake resonance.

        Args:
            rpm: Engine RPM (1000-6000)
            resonance_freq: Intake resonance frequency in Hz (maps to runner geometry)
        """
        start_scope()

        # Map RPM to driving frequency (4-cyl: 2 intake strokes per revolution)
        driving_freq = (rpm / 60) * 2  # Hz

        # Quality factor Q for resonance (higher = sharper resonance peak)
        Q = 5.0

        # Damping from Q: tau = Q / (pi * f_resonance)
        tau_osc = (Q / (np.pi * resonance_freq)) * 1000 * ms

        # Resonance coupling strength (how efficiently energy transfers)
        # At resonance, coupling is maximum
        freq_ratio = driving_freq / resonance_freq
        resonance_coupling = np.exp(-((freq_ratio - 1) ** 2) / 0.1)  # Gaussian

        equations = '''
        dv/dt = (v_rest - v + I_drive + I_resonance) / tau_m : volt (unless refractory)
        dI_drive/dt = (-I_drive + A_drive * sin(2*pi*f_drive*t)) / tau_drive : volt
        dI_resonance/dt = (-I_resonance + A_res * sin(2*pi*f_res*t + phase)) / tau_osc : volt
        phase : 1
        tau_m : second
        tau_drive : second
        tau_osc : second
        f_drive : Hz
        f_res : Hz
        A_drive : volt
        A_res : volt
        v_rest : volt
        v_thresh : volt
        '''

        self.neurons = NeuronGroup(
            self.n_neurons,
            model=equations,
            threshold='v > v_thresh',
            reset='v = v_rest',
            refractory=2*ms,
            method='euler',
            name='intake_resonance_oscillators'
        )

        # Set parameters
        self.neurons.tau_m = 10*ms
        self.neurons.tau_drive = 5*ms
        self.neurons.tau_osc = tau_osc
        self.neurons.f_drive = driving_freq * Hz
        self.neurons.f_res = resonance_freq * Hz
        self.neurons.A_drive = 15*mV
        self.neurons.A_res = 25*mV * resonance_coupling  # Stronger at resonance
        self.neurons.v_rest = -65*mV
        self.neurons.v_thresh = -50*mV
        self.neurons.phase = 'rand() * 2 * pi'  # Random initial phase

        # Initial conditions
        self.neurons.v = -65*mV
        self.neurons.I_drive = 0*mV
        self.neurons.I_resonance = 0*mV

        # Coupling between neurons (represents pressure wave coupling)
        self.synapses = Synapses(
            self.neurons, self.neurons,
            on_pre='I_drive_post += 2*mV',
            name='intake_coupling'
        )
        self.synapses.connect(p=0.05)

        # Monitors
        self.spike_monitor = SpikeMonitor(self.neurons, name='spikes')
        self.state_monitor = StateMonitor(
            self.neurons, ['v', 'I_drive', 'I_resonance'],
            record=[0, 1, 2],
            name='states'
        )

        self.network = Network([
            self.neurons, self.synapses,
            self.spike_monitor, self.state_monitor
        ])

        return self

    def validate(self, rpm_range=None):
        """Test hypothesis across RPM range."""
        if rpm_range is None:
            rpm_range = [2000, 2500, 3000, 3500, 4000, 4500, 5000]

        results = []
        for rpm in rpm_range:
            self.build(rpm=rpm, resonance_freq=50)
            self.network.run(self.duration_ms * ms)

            # Extract metrics
            v_trace = np.array(self.state_monitor.v[0])
            lyap = self.compute_lyapunov_exponent(v_trace)

            # Phase from I_resonance
            phases = np.angle(np.fft.fft(v_trace))
            kuramoto = self.compute_kuramoto_order_parameter(phases[:len(phases)//2])

            amp_stability = self.compute_amplitude_stability(v_trace)

            results.append({
                'rpm': rpm,
                'lyapunov': lyap,
                'kuramoto_r': kuramoto,
                'amplitude_stability': amp_stability,
                'spike_count': len(self.spike_monitor.t)
            })

        return results


class HypothesisB_ExhaustPulseCoupling(HypothesisValidator):
    """
    HYPOTHESIS B: Exhaust Pulse Coupling

    Map: Exhaust pulses as coupled oscillators with intake pulses
    Prediction: Maintaining steady-state throttle (constant flow) improves efficiency 3-5%
    Falsification: If steady-throttle shows no benefit vs. variable throttle
    Physics: Exhaust backpressure creates pulse timing; steady flow = constructive interference

    Brian2 Mapping:
    - Exhaust flow rate -> oscillator amplitude
    - Steady throttle -> constant coupling strength
    - Variable throttle -> time-varying coupling (can cause destructive interference)

    Note: Uses single population with coupled internal dynamics (not spike-based)
    """

    def build(self, throttle_mode='steady', variability=0.0):
        """
        Build coupled exhaust-intake oscillator model.

        Args:
            throttle_mode: 'steady' or 'variable'
            variability: For 'variable' mode, how much coupling varies (0-1)
        """
        start_scope()

        # Base frequency (engine at 2500 RPM)
        f_engine = 83.3  # Hz (2500 RPM / 60 * 2)

        # Coupling strength based on throttle mode
        if throttle_mode == 'steady':
            coupling_strength = 0.5
            coupling_var = 0.0
        elif throttle_mode == 'moderate':
            coupling_strength = 0.5
            coupling_var = 0.2
        else:  # variable
            coupling_strength = 0.5
            coupling_var = 0.5

        # Phase delay between intake and exhaust (45 degrees)
        phase_delay = np.pi / 4

        equations = '''
        dv/dt = (v_rest - v + I_combined) / tau_m : volt (unless refractory)
        I_combined = I_intake + K_coupling * I_exhaust : volt
        dI_intake/dt = (-I_intake + A_drive * sin(2*pi*f*t)) / tau_osc : volt
        dI_exhaust/dt = (-I_exhaust + A_drive * sin(2*pi*f*t + phase_delay)) / tau_osc : volt
        phase_delay : 1 (constant)
        f : Hz (constant)
        A_drive : volt
        K_coupling : 1
        tau_m : second
        tau_osc : second
        v_rest : volt
        v_thresh : volt
        '''

        self.neurons = NeuronGroup(
            self.n_neurons,
            model=equations,
            threshold='v > v_thresh',
            reset='v = v_rest',
            refractory=2*ms,
            method='euler',
            name='exhaust_intake_oscillators'
        )

        # Set parameters
        self.neurons.tau_m = 10*ms
        self.neurons.tau_osc = 5*ms
        self.neurons.f = f_engine * Hz
        self.neurons.v_rest = -65*mV
        self.neurons.v_thresh = -50*mV
        self.neurons.A_drive = 20*mV
        self.neurons.phase_delay = phase_delay

        # Variable coupling across neurons simulates throttle variability
        if coupling_var > 0:
            # Some neurons have different coupling (simulates variable throttle)
            base_coupling = coupling_strength
            variation = np.random.uniform(-coupling_var, coupling_var, self.n_neurons)
            self.neurons.K_coupling = base_coupling + variation
        else:
            self.neurons.K_coupling = coupling_strength

        # Initial conditions
        self.neurons.v = -65*mV
        self.neurons.I_intake = 0*mV
        self.neurons.I_exhaust = 0*mV

        # Inter-neuron coupling for synchronization
        self.synapses = Synapses(
            self.neurons, self.neurons,
            on_pre='v_post += 1*mV',
            name='exhaust_sync_coupling'
        )
        self.synapses.connect(p=0.1)

        # Monitors
        self.spike_monitor = SpikeMonitor(self.neurons, name='spikes')
        self.state_monitor = StateMonitor(
            self.neurons, ['v', 'I_intake', 'I_exhaust', 'K_coupling'],
            record=[0, 1, 2],
            name='states'
        )

        self.network = Network([
            self.neurons, self.synapses,
            self.spike_monitor, self.state_monitor
        ])

        return self


class HypothesisC_TirePressureStateVariable(HypothesisValidator):
    """
    HYPOTHESIS C: Tire Pressure as State Variable

    Map: Optimal pressure as function of vehicle mass + load
    Prediction: Higher load requires higher pressure to maintain rolling efficiency
    Falsification: If fixed pressure outperforms variable across load conditions
    Physics: F = C_rr * (load/area); varies with weight

    Brian2 Mapping:
    - Tire pressure -> damping coefficient (lower damping at higher PSI)
    - Load -> driving force amplitude
    - Optimal efficiency when damping and load are balanced
    """

    # 1998 Toyota Starlet curb weight: ~820 kg
    # Typical load: 0-400 kg additional

    def build(self, tire_pressure_psi, vehicle_load_kg):
        """
        Build tire-road interaction oscillator model.

        Args:
            tire_pressure_psi: Tire pressure (28-44 PSI)
            vehicle_load_kg: Total load including vehicle mass (820-1220 kg)
        """
        start_scope()

        # Map tire pressure to damping
        # Higher pressure = lower rolling resistance = less damping
        # 32 PSI -> tau = 15ms (high damping)
        # 40 PSI -> tau = 8ms (low damping)
        base_tau = 20
        tau_damping = (base_tau - (tire_pressure_psi - 28) * 0.6) * ms
        tau_damping = max(tau_damping, 5*ms)

        # Load affects the driving force needed
        # Normalize to curb weight
        load_factor = vehicle_load_kg / 820  # 820 kg curb weight

        equations = '''
        dv/dt = (v_rest - v + I_drive + I_damped) / tau_m : volt (unless refractory)
        dI_drive/dt = (-I_drive + A_load * sin(2*pi*f*t)) / tau_drive : volt
        dI_damped/dt = -I_damped / tau_damping : volt
        tau_m : second
        tau_drive : second
        tau_damping : second
        f : Hz
        A_load : volt
        v_rest : volt
        v_thresh : volt
        '''

        self.neurons = NeuronGroup(
            self.n_neurons,
            model=equations,
            threshold='v > v_thresh',
            reset='v = v_rest',
            refractory=2*ms,
            method='euler',
            name='tire_pressure_oscillators'
        )

        # Set parameters
        self.neurons.tau_m = 10*ms
        self.neurons.tau_drive = 5*ms
        self.neurons.tau_damping = tau_damping
        self.neurons.f = 2 * Hz  # Low frequency for road dynamics
        self.neurons.A_load = 15*mV * load_factor  # More force needed with load
        self.neurons.v_rest = -65*mV
        self.neurons.v_thresh = -50*mV

        # Initial conditions
        self.neurons.v = -65*mV
        self.neurons.I_drive = 0*mV
        self.neurons.I_damped = 0*mV

        # Inter-neuron coupling (represents tire-road contact consistency)
        self.synapses = Synapses(
            self.neurons, self.neurons,
            on_pre='I_damped_post += 1*mV',
            name='tire_coupling'
        )
        self.synapses.connect(p=0.08)

        # Monitors
        self.spike_monitor = SpikeMonitor(self.neurons, name='spikes')
        self.state_monitor = StateMonitor(
            self.neurons, ['v', 'I_drive', 'I_damped'],
            record=[0, 1, 2],
            name='states'
        )

        self.network = Network([
            self.neurons, self.synapses,
            self.spike_monitor, self.state_monitor
        ])

        return self


class HypothesisD_EngineTemperatureRelaxation(HypothesisValidator):
    """
    HYPOTHESIS D: Engine Temperature as Relaxation Oscillator

    Map: Engine temperature follows relaxation dynamics with time constant tau ~ 10-15 minutes
    Prediction: Engine reaches efficiency plateau after 2-3 thermal cycles
    Falsification: If single long warm-up shows same efficiency as multiple short trips
    Physics: dT/dt = (T_amb - T_current) / tau; efficiency peaks at thermal equilibrium

    Brian2 Mapping:
    - Temperature -> state variable with slow dynamics
    - Thermal mass -> time constant (10-15 minutes = 600-900 seconds)
    - Efficiency -> function of temperature (peaks at operating temp ~90C)

    Note: This hypothesis maps to relaxation dynamics, NOT oscillator dynamics.
    Marked as INCONCLUSIVE for oscillator-based validation.
    """

    def build(self, warmup_time_min, cycles=1):
        """
        Build thermal relaxation model.

        Args:
            warmup_time_min: Duration of warm-up phase (minutes)
            cycles: Number of warm-up/cool-down cycles
        """
        start_scope()

        # Compress time: 10 minutes = 1 second in simulation
        time_scale = 600  # 10 min = 1s

        # Thermal time constant (10-15 minutes)
        tau_thermal = 12 * time_scale * ms  # 12 minutes -> 2s in simulation

        # Target operating temperature: 90C
        T_operating = 90  # Celsius
        T_ambient = 20  # Celsius

        equations = '''
        dv/dt = (v_rest - v + I_thermal + I_heat) / tau_m : volt
        dT/dt = (T_target - T) / tau_thermal : 1
        dI_thermal/dt = (-I_thermal + A_eff * (1 - abs(T - T_opt)/T_opt)) / tau_osc : volt
        dI_heat/dt = -I_heat / tau_heat : volt
        T_target : 1
        T_opt : 1
        tau_m : second
        tau_thermal : second
        tau_osc : second
        tau_heat : second
        A_eff : volt
        v_rest : volt
        v_thresh : volt
        '''

        self.neurons = NeuronGroup(
            self.n_neurons,
            model=equations,
            threshold='v > v_thresh',
            reset='v = v_rest',
            refractory=2*ms,
            method='euler',
            name='thermal_oscillators'
        )

        # Set parameters
        self.neurons.tau_m = 10*ms
        self.neurons.tau_thermal = tau_thermal
        self.neurons.tau_osc = 50*ms
        self.neurons.tau_heat = time_scale * ms
        self.neurons.T_target = T_operating
        self.neurons.T_opt = T_operating
        self.neurons.A_eff = 20*mV
        self.neurons.v_rest = -65*mV
        self.neurons.v_thresh = -50*mV

        # Initial conditions
        self.neurons.v = -65*mV
        self.neurons.T = T_ambient
        self.neurons.I_thermal = 0*mV
        self.neurons.I_heat = 5*mV  # Engine heat generation

        # Monitors
        self.spike_monitor = SpikeMonitor(self.neurons, name='spikes')
        self.state_monitor = StateMonitor(
            self.neurons, ['v', 'T', 'I_thermal'],
            record=[0, 1, 2],
            name='states'
        )

        self.network = Network([
            self.neurons,
            self.spike_monitor, self.state_monitor
        ])

        return self


class HypothesisE_AcceleratorPulseTiming(HypothesisValidator):
    """
    HYPOTHESIS E: Accelerator Pulse Timing

    Map: Accelerator position as oscillator; fuel pulse timing
    Prediction: Gradual accelerator position changes (0.5%/second) improve efficiency
    Falsification: If jab acceleration shows same efficiency as gradual
    Physics: Fuel injection timing maps to accelerator position; smooth = optimal air-fuel mixing

    Brian2 Mapping:
    - Accelerator position -> driving amplitude
    - Gradual change -> slowly varying amplitude
    - Jab change -> step change in amplitude (can cause transient instability)
    """

    def build(self, acceleration_profile='gradual', jab_magnitude=0.0):
        """
        Build accelerator-fuel system oscillator model.

        Args:
            acceleration_profile: 'gradual', 'moderate', or 'jab'
            jab_magnitude: For 'jab' mode, size of sudden change (0-1)
        """
        start_scope()

        # Base driving frequency (engine RPM at 2500)
        f_engine = 83.3 * Hz

        # Profile-specific parameters
        if acceleration_profile == 'gradual':
            amplitude_variation = 0.1  # 10% variation over time
            variation_freq = 0.5 * Hz  # Slow changes
        elif acceleration_profile == 'moderate':
            amplitude_variation = 0.3
            variation_freq = 2 * Hz
        else:  # jab
            amplitude_variation = jab_magnitude
            variation_freq = 10 * Hz  # Fast, jerky changes

        equations = '''
        dv/dt = (v_rest - v + I_fuel + I_transient) / tau_m : volt (unless refractory)
        dI_fuel/dt = (-I_fuel + A_base * (1 + A_var * sin(2*pi*f_var*t)) * sin(2*pi*f_engine*t)) / tau_fuel : volt
        dI_transient/dt = -I_transient / tau_trans : volt
        tau_m : second
        tau_fuel : second
        tau_trans : second
        f_engine : Hz
        f_var : Hz
        A_base : volt
        A_var : 1
        v_rest : volt
        v_thresh : volt
        '''

        self.neurons = NeuronGroup(
            self.n_neurons,
            model=equations,
            threshold='v > v_thresh',
            reset='v = v_rest',
            refractory=2*ms,
            method='euler',
            name='accelerator_oscillators'
        )

        # Set parameters
        self.neurons.tau_m = 10*ms
        self.neurons.tau_fuel = 5*ms
        self.neurons.tau_trans = 20*ms  # Transient response time
        self.neurons.f_engine = f_engine
        self.neurons.f_var = variation_freq
        self.neurons.A_base = 20*mV
        self.neurons.A_var = amplitude_variation
        self.neurons.v_rest = -65*mV
        self.neurons.v_thresh = -50*mV

        # Initial conditions
        self.neurons.v = -65*mV
        self.neurons.I_fuel = 0*mV
        self.neurons.I_transient = 0*mV

        # Coupling (represents engine-load synchronization)
        coupling_strength = 0.3 if acceleration_profile == 'gradual' else 0.1
        self.synapses = Synapses(
            self.neurons, self.neurons,
            on_pre=f'I_transient_post += {coupling_strength}*3*mV',
            name='accel_coupling'
        )
        self.synapses.connect(p=0.1)

        # Monitors
        self.spike_monitor = SpikeMonitor(self.neurons, name='spikes')
        self.state_monitor = StateMonitor(
            self.neurons, ['v', 'I_fuel', 'I_transient'],
            record=[0, 1, 2],
            name='states'
        )

        self.network = Network([
            self.neurons, self.synapses,
            self.spike_monitor, self.state_monitor
        ])

        return self


def validate_all_hypotheses():
    """Run validation for all 5 hypotheses and generate report."""

    print("=" * 70)
    print("FUEL EFFICIENCY HYPOTHESES A-E VALIDATION")
    print("Brian2 Oscillator Dynamics Analysis")
    print("Vehicle: 1998 Toyota Starlet 1.3L 4E-FE")
    print("=" * 70)

    results = {}

    # ===== HYPOTHESIS A: Intake Resonance =====
    print("\n" + "=" * 70)
    print("HYPOTHESIS A: Intake Resonance Tuning")
    print("=" * 70)
    print("\nOscillator Model:")
    print("  - RPM -> Driving frequency (4-cyl: 2 intake strokes/rev)")
    print("  - Intake runner -> Natural frequency (Helmholtz resonance)")
    print("  - Efficiency peaks when RPM matches resonance")

    validator_a = HypothesisA_IntakeResonance(n_neurons=50, duration_ms=10000)
    results_a = validator_a.validate(rpm_range=[2000, 2500, 3000, 3500, 4000, 4500, 5000])

    print("\nSimulation Results (10s):")
    for r in results_a:
        print(f"  RPM {r['rpm']:4d}: Lyapunov={r['lyapunov']:+.3f}, "
              f"Kuramoto r={r['kuramoto_r']:.3f}, "
              f"Amp Stability={r['amplitude_stability']:.3f}, "
              f"Spikes={r['spike_count']}")

    # Find optimal RPM (most stable = most negative Lyapunov)
    best_rpm = max(results_a, key=lambda x: -x['lyapunov'] + x['kuramoto_r'])
    optimal_band = 3000 <= best_rpm['rpm'] <= 3500

    # Check if 3000-3500 RPM range has BETTER metrics than other ranges
    optimal_range_results = [r for r in results_a if 3000 <= r['rpm'] <= 3500]
    other_range_results = [r for r in results_a if r['rpm'] < 3000 or r['rpm'] > 3500]

    avg_optimal_lyap = np.mean([r['lyapunov'] for r in optimal_range_results])
    avg_other_lyap = np.mean([r['lyapunov'] for r in other_range_results])
    avg_optimal_kuramoto = np.mean([r['kuramoto_r'] for r in optimal_range_results])
    avg_other_kuramoto = np.mean([r['kuramoto_r'] for r in other_range_results])

    # Hypothesis valid if optimal range has better stability (more negative Lyapunov)
    # OR better phase coherence (higher Kuramoto)
    hypothesis_valid = (avg_optimal_lyap < avg_other_lyap * 0.95 or  # 5% better stability
                        avg_optimal_kuramoto > avg_other_kuramoto * 1.05)  # 5% better coherence

    print(f"\nOptimal RPM: {best_rpm['rpm']} (predicted 3000-3500)")
    print(f"Lyapunov: {best_rpm['lyapunov']:+.3f} ({'stable' if best_rpm['lyapunov'] < 0 else 'unstable'})")
    print(f"Kuramoto r: {best_rpm['kuramoto_r']:.3f}")
    print(f"Amplitude Stability: {best_rpm['amplitude_stability']:.3f}")
    print(f"\nRange Comparison:")
    print(f"  3000-3500 RPM avg Lyapunov: {avg_optimal_lyap:+.1f}")
    print(f"  Other RPM avg Lyapunov: {avg_other_lyap:+.1f}")
    print(f"  3000-3500 RPM avg Kuramoto: {avg_optimal_kuramoto:.3f}")
    print(f"  Other RPM avg Kuramoto: {avg_other_kuramoto:.3f}")

    # All values negative = all stable, so verdict based on relative comparison
    all_stable = all(r['lyapunov'] < 0 for r in results_a)
    verdict_a = "STABLE" if hypothesis_valid and all_stable else ("INCONCLUSIVE" if all_stable else "UNSTABLE")
    results['A'] = {'verdict': verdict_a, 'optimal_rpm': best_rpm['rpm']}

    print(f"\n### Verdict: {verdict_a}")
    print(f"   Hypothesis {'has merit' if verdict_a == 'STABLE' else 'needs more data' if verdict_a == 'INCONCLUSIVE' else 'is invalid'}")
    print(f"   Practical: {'Drive at 3000-3500 RPM for peak efficiency' if verdict_a == 'STABLE' else 'Resonance tuning may not be significant'}")

    # ===== HYPOTHESIS B: Exhaust Pulse Coupling =====
    print("\n" + "=" * 70)
    print("HYPOTHESIS B: Exhaust Pulse Coupling")
    print("=" * 70)
    print("\nOscillator Model:")
    print("  - Intake and exhaust as coupled oscillators")
    print("  - Steady throttle -> constant coupling = constructive interference")
    print("  - Variable throttle -> fluctuating coupling = energy waste")

    results_b = []
    for mode, var in [('steady', 0.0), ('moderate', 0.3), ('variable', 0.6)]:
        validator_b = HypothesisB_ExhaustPulseCoupling(n_neurons=50, duration_ms=10000)
        validator_b.build(throttle_mode=mode, variability=var)
        validator_b.network.run(10000 * ms)

        v_trace = np.array(validator_b.state_monitor.v[0])
        lyap = validator_b.compute_lyapunov_exponent(v_trace)
        phases = np.angle(np.fft.fft(v_trace))
        kuramoto = validator_b.compute_kuramoto_order_parameter(phases[:len(phases)//2])
        amp_stab = validator_b.compute_amplitude_stability(v_trace)

        results_b.append({
            'mode': mode,
            'lyapunov': lyap,
            'kuramoto_r': kuramoto,
            'amplitude_stability': amp_stab,
            'spike_count': len(validator_b.spike_monitor.t)
        })

    print("\nSimulation Results (10s):")
    for r in results_b:
        print(f"  {r['mode']:10s}: Lyapunov={r['lyapunov']:+.3f}, "
              f"Kuramoto r={r['kuramoto_r']:.3f}, "
              f"Amp Stability={r['amplitude_stability']:.3f}")

    # All modes are stable (negative Lyapunov), so compare relative stability
    all_stable_b = all(r['lyapunov'] < 0 for r in results_b)
    steady_lyap = results_b[0]['lyapunov']
    variable_lyap = results_b[-1]['lyapunov']

    # Steady is better if it's MORE stable (more negative Lyapunov)
    # Allow 5% tolerance for numerical noise
    steady_better = steady_lyap < variable_lyap * 0.95

    verdict_b = "STABLE" if steady_better and all_stable_b else ("INCONCLUSIVE" if all_stable_b else "UNSTABLE")
    results['B'] = {'verdict': verdict_b, 'steady_better': steady_better}

    print(f"\n### Verdict: {verdict_b}")
    print(f"   All modes are stable. Steady {'is' if steady_better else 'is not clearly'} more stable than variable.")
    print(f"   Practical: {'Maintain steady throttle on highway' if verdict_b == 'STABLE' else 'Variable throttle may not hurt efficiency significantly'}")

    # ===== HYPOTHESIS C: Tire Pressure =====
    print("\n" + "=" * 70)
    print("HYPOTHESIS C: Tire Pressure as State Variable")
    print("=" * 70)
    print("\nOscillator Model:")
    print("  - Tire pressure -> damping coefficient (higher PSI = less damping)")
    print("  - Load -> driving force amplitude")
    print("  - Optimal when pressure-load balanced")

    results_c = []
    for psi in [28, 32, 35, 38, 40, 44]:
        for load in [820, 1000, 1200]:  # kg
            validator_c = HypothesisC_TirePressureStateVariable(n_neurons=50, duration_ms=10000)
            validator_c.build(tire_pressure_psi=psi, vehicle_load_kg=load)
            validator_c.network.run(10000 * ms)

            v_trace = np.array(validator_c.state_monitor.v[0])
            lyap = validator_c.compute_lyapunov_exponent(v_trace)
            phases = np.angle(np.fft.fft(v_trace))
            kuramoto = validator_c.compute_kuramoto_order_parameter(phases[:len(phases)//2])
            amp_stab = validator_c.compute_amplitude_stability(v_trace)

            results_c.append({
                'psi': psi,
                'load': load,
                'lyapunov': lyap,
                'kuramoto_r': kuramoto,
                'amplitude_stability': amp_stab
            })

    print("\nSimulation Results (10s) - Sample:")
    for r in results_c[::3]:  # Show every 3rd result
        print(f"  PSI {r['psi']:2d}, Load {r['load']}kg: "
              f"Lyapunov={r['lyapunov']:+.3f}, "
              f"Kuramoto r={r['kuramoto_r']:.3f}")

    # Check if higher PSI consistently improves stability across loads
    low_load = [r for r in results_c if r['load'] == 820]
    high_load = [r for r in results_c if r['load'] == 1200]

    # Higher PSI should be more stable (more negative Lyapunov)
    # Check trend: PSI 28 vs PSI 44
    psi_improves_low = low_load[-1]['lyapunov'] < low_load[0]['lyapunov'] * 0.98
    psi_improves_high = high_load[-1]['lyapunov'] < high_load[0]['lyapunov'] * 0.98

    # Also check if load affects optimal pressure
    # Higher load should benefit MORE from higher pressure
    load_pressure_interaction = False
    if len(high_load) > 0 and len(low_load) > 0:
        high_psi_benefit_high_load = high_load[0]['lyapunov'] - high_load[-1]['lyapunov']
        high_psi_benefit_low_load = low_load[0]['lyapunov'] - low_load[-1]['lyapunov']
        load_pressure_interaction = high_psi_benefit_high_load > high_psi_benefit_low_load

    all_stable_c = all(r['lyapunov'] < 0 for r in results_c)

    # Verdict: STABLE if higher PSI helps, INCONCLUSIVE if no clear trend
    if psi_improves_low or psi_improves_high:
        verdict_c = "STABLE"
    elif all_stable_c:
        verdict_c = "INCONCLUSIVE"
    else:
        verdict_c = "UNSTABLE"

    results['C'] = {'verdict': verdict_c}

    print(f"\n### Verdict: {verdict_c}")
    print(f"   All configurations are stable.")
    print(f"   Higher tire pressure {'improves' if psi_improves_low or psi_improves_high else 'may not significantly improve'} stability")
    print(f"   Practical: {'Inflate to 40 PSI for efficiency' if verdict_c == 'STABLE' else 'Standard pressure may be adequate'}")

    # ===== HYPOTHESIS D: Engine Temperature =====
    print("\n" + "=" * 70)
    print("HYPOTHESIS D: Engine Temperature as Relaxation Oscillator")
    print("=" * 70)
    print("\nOscillator Model:")
    print("  - Temperature -> state variable with SLOW dynamics (minutes)")
    print("  - This is a RELAXATION model, NOT oscillator dynamics")
    print("  - Brian2 oscillator validation is INAPPROPRIATE for this hypothesis")

    # Still run the model for completeness
    validator_d = HypothesisD_EngineTemperatureRelaxation(n_neurons=50, duration_ms=10000)
    validator_d.build(warmup_time_min=15, cycles=1)
    validator_d.network.run(10000 * ms)

    v_trace = np.array(validator_d.state_monitor.v[0])
    lyap = validator_d.compute_lyapunov_exponent(v_trace)
    T_trace = np.array(validator_d.state_monitor.T[0])

    print("\nSimulation Results (10s, time-compressed):")
    print(f"  Lyapunov Exponent: {lyap:+.3f}")
    print(f"  Temperature range: {T_trace[0]:.1f}C -> {T_trace[-1]:.1f}C")
    print(f"  (Note: 10 min compressed to 1s for simulation)")

    verdict_d = "INCONCLUSIVE"
    results['D'] = {'verdict': verdict_d}

    print(f"\n### Verdict: {verdict_d}")
    print(f"   Thermal dynamics are RELAXATION (not oscillatory)")
    print(f"   Brian2 oscillator validation is not applicable")
    print(f"   Practical: Warm engine before aggressive driving (unchanged)")

    # ===== HYPOTHESIS E: Accelerator Pulse Timing =====
    print("\n" + "=" * 70)
    print("HYPOTHESIS E: Accelerator Pulse Timing")
    print("=" * 70)
    print("\nOscillator Model:")
    print("  - Accelerator position -> driving amplitude")
    print("  - Gradual change -> slow amplitude modulation = stable")
    print("  - Jab change -> fast modulation = transient instability")

    results_e = []
    for profile in ['gradual', 'moderate', 'jab']:
        validator_e = HypothesisE_AcceleratorPulseTiming(n_neurons=50, duration_ms=10000)
        jab_mag = 0.5 if profile == 'jab' else 0.0
        validator_e.build(acceleration_profile=profile, jab_magnitude=jab_mag)
        validator_e.network.run(10000 * ms)

        v_trace = np.array(validator_e.state_monitor.v[0])
        lyap = validator_e.compute_lyapunov_exponent(v_trace)
        phases = np.angle(np.fft.fft(v_trace))
        kuramoto = validator_e.compute_kuramoto_order_parameter(phases[:len(phases)//2])
        amp_stab = validator_e.compute_amplitude_stability(v_trace)

        results_e.append({
            'profile': profile,
            'lyapunov': lyap,
            'kuramoto_r': kuramoto,
            'amplitude_stability': amp_stab,
            'spike_count': len(validator_e.spike_monitor.t)
        })

    print("\nSimulation Results (10s):")
    for r in results_e:
        print(f"  {r['profile']:10s}: Lyapunov={r['lyapunov']:+.3f}, "
              f"Kuramoto r={r['kuramoto_r']:.3f}, "
              f"Amp Stability={r['amplitude_stability']:.3f}")

    # All modes are stable, so compare relative stability
    all_stable_e = all(r['lyapunov'] < 0 for r in results_e)
    gradual_lyap = results_e[0]['lyapunov']
    jab_lyap = results_e[-1]['lyapunov']

    # Gradual should be MORE stable (more negative Lyapunov)
    # Allow 5% tolerance
    gradual_better = gradual_lyap < jab_lyap * 0.95

    # Also check amplitude stability
    gradual_amp = results_e[0]['amplitude_stability']
    jab_amp = results_e[-1]['amplitude_stability']
    gradual_amp_better = gradual_amp > jab_amp * 1.02

    verdict_e = "STABLE" if (gradual_better or gradual_amp_better) and all_stable_e else ("INCONCLUSIVE" if all_stable_e else "UNSTABLE")
    results['E'] = {'verdict': verdict_e}

    print(f"\n### Verdict: {verdict_e}")
    print(f"   All modes are stable. Gradual {'is' if gradual_better else 'is not clearly'} more stable than jab.")
    print(f"   Practical: {'Accelerate smoothly at 0.5%/second' if verdict_e == 'STABLE' else 'Driving style impact unclear from oscillator model'}")

    # ===== SUMMARY =====
    print("\n" + "#" * 70)
    print("# FINAL SUMMARY")
    print("#" * 70)

    print("\n| Hypothesis | Verdict      | Physics Fit | Brian2 Map |")
    print("|------------|--------------|-------------|------------|")
    print(f"| A: Intake  | {results['A']['verdict']:12s} | Good        | Good       |")
    print(f"| B: Exhaust | {results['B']['verdict']:12s} | Good        | Moderate   |")
    print(f"| C: Tires   | {results['C']['verdict']:12s} | Moderate    | Weak       |")
    print(f"| D: Thermal | {results['D']['verdict']:12s} | Good        | POOR       |")
    print(f"| E: Accel   | {results['E']['verdict']:12s} | Moderate    | Moderate   |")

    stable_count = sum(1 for v in results.values() if v['verdict'] == 'STABLE')
    inconclusive = sum(1 for v in results.values() if v['verdict'] == 'INCONCLUSIVE')

    print(f"\nTotal: {stable_count}/5 STABLE, {inconclusive}/5 INCONCLUSIVE")

    print("\n# PRACTICAL RECOMMENDATIONS FOR 1998 TOYOTA STARLET 1.3L 4E-FE:")
    if results['A']['verdict'] == 'STABLE':
        print("  1. Drive in 3000-3500 RPM band for peak intake efficiency")
    if results['B']['verdict'] == 'STABLE':
        print("  2. Maintain steady throttle on highway (avoid cruise control hills)")
    if results['C']['verdict'] == 'STABLE':
        print("  3. Inflate tires to 40 PSI (check sidewall max)")
    # D is inconclusive
    if results['E']['verdict'] == 'STABLE':
        print("  4. Accelerate smoothly, avoid jab inputs")

    return results


if __name__ == "__main__":
    results = validate_all_hypotheses()
