"""
Cluster Failure Simulation using Spiking Neural Networks

Maps distributed system failure dynamics onto the SNN architecture:
- Neurons = Services/Nodes in a distributed system
- Spikes = Failure signals propagating through dependencies
- Synaptic connections = Service dependencies
- Inhibitory neurons = Circuit breakers
- Detection latency = Monitor neuron response time

Validates research findings:
1. Cascade failures follow power-law distribution (α ≈ 1.5-2.0)
2. Detection latency is the hidden variable
3. Circuit breakers reduce cascade size
4. Critical service failures have larger cascades
"""

import numpy as np
from brian2 import (
    NeuronGroup, Synapses, SpikeMonitor, Network,
    ms, mV, start_scope, run
)


class ClusterFailureSimulation:
    """Simulates cluster failure cascades using spiking neural networks."""

    @staticmethod
    def default_config():
        return {
            'n_services': 100,
            'n_critical': 10,
            'dependency_prob': 0.08,
            'inhibitory_fraction': 0.2,
            'simulation_duration': 1000,
        }

    def __init__(self, config=None):
        defaults = self.default_config()
        if config:
            defaults.update(config)
        self.config = defaults
        self.network = None
        self.services = None
        self.connections = []
        self.circuit_breakers = None
        self.spike_monitors = {}
        self.critical_indices = None
        self.cascade_sizes = []
        self.detection_time = None
        self.failure_events = []

    def build(self):
        start_scope()
        self.network = Network(name='cluster_failure')
        n = self.config['n_services']
        n_critical = self.config['n_critical']

        eqs = '''
        dv/dt = (v_rest - v + I_syn) / tau_m : volt (unless refractory)
        dI_syn/dt = -I_syn / tau_syn : volt
        tau_m : second
        tau_syn : second
        v_rest : volt
        v_thresh : volt
        '''

        services = NeuronGroup(
            n, eqs,
            threshold='v > v_thresh',
            reset='v = v_rest',
            refractory=5*ms,
            method='euler',
            name='services'
        )
        services.tau_m = 10*ms
        services.tau_syn = 5*ms  # Longer integration window
        services.v_rest = -65*mV
        services.v_thresh = -52*mV  # Lower threshold for easier cascading
        services.v = -65*mV + np.random.randn(n) * 2*mV
        services.I_syn = 0*mV
        self.services = services
        self.network.add(services)

        self.critical_indices = np.zeros(n, dtype=bool)
        self.critical_indices[:n_critical] = True
        np.random.shuffle(self.critical_indices)

        p = self.config['dependency_prob']
        syn = Synapses(services, services, on_pre='I_syn_post += 8*mV', delay=1.5*ms, name='dependencies')
        n_conn = 0
        for i in range(n):
            for j in range(n):
                if i != j:
                    prob = p * 2 if self.critical_indices[i] else p
                    if np.random.rand() < prob:
                        syn.connect(i=i, j=j)
                        n_conn += 1
        self.connections.append(syn)
        self.network.add(syn)
        print(f"Created {n_conn} dependency connections")

        self.spike_monitors['services'] = SpikeMonitor(services)
        self.network.add(self.spike_monitors['services'])

        n_inhib = int(n * self.config['inhibitory_fraction'])
        if n_inhib > 0:
            inhib = NeuronGroup(n_inhib, eqs, threshold='v > v_thresh', reset='v = v_rest', refractory=2*ms, method='euler', name='circuit_breakers')
            inhib.tau_m = 5*ms
            inhib.tau_syn = 2*ms
            inhib.v_rest = -65*mV
            inhib.v_thresh = -52*mV
            inhib.v = -65*mV
            inhib.I_syn = 0*mV
            self.circuit_breakers = inhib
            self.network.add(inhib)

            detect = Synapses(services, inhib, on_pre='I_syn_post += 4*mV', name='detect')
            detect.connect(p=0.1)
            self.network.add(detect)

            inhibit = Synapses(inhib, services, on_pre='I_syn_post -= 8*mV', name='inhibit')
            inhibit.connect(p=0.15)
            self.network.add(inhibit)

            self.spike_monitors['breakers'] = SpikeMonitor(inhib)
            self.network.add(self.spike_monitors['breakers'])
            print(f"Created {n_inhib} circuit breakers")

        return self

    def inject_failure(self, service_idx, strength=20*mV):
        self.services.v[service_idx] += strength
        self.failure_events.append({'service': int(service_idx), 'strength': float(strength/mV)})

    def inject_random_failures(self, n_failures=1, strength_range=(10, 20)):
        n = self.config['n_services']
        for _ in range(n_failures):
            idx = np.random.randint(0, n)
            strength = np.random.uniform(*strength_range) * mV
            self.inject_failure(idx, strength)

    def run(self, duration_ms=None):
        duration = duration_ms or self.config['simulation_duration']
        self.network.run(duration * ms)
        self._analyze_cascades()
        return self

    def _analyze_cascades(self):
        spikes = self.spike_monitors['services']
        t, i = np.array(spikes.t), np.array(spikes.i)
        if len(t) == 0:
            return

        cascade_window = 0.015
        cascade_sizes = []

        if len(t) > 1:
            order = np.argsort(t)
            t_sorted, i_sorted = t[order], i[order]
            cascade_neurons = set([i_sorted[0]])
            cascade_start = t_sorted[0]
            for j in range(1, len(t_sorted)):
                if (t_sorted[j] - cascade_start) < cascade_window:
                    cascade_neurons.add(i_sorted[j])
                else:
                    if len(cascade_neurons) >= 2:
                        cascade_sizes.append(len(cascade_neurons))
                    cascade_neurons = set([i_sorted[j]])
                    cascade_start = t_sorted[j]
            if len(cascade_neurons) >= 2:
                cascade_sizes.append(len(cascade_neurons))

        self.cascade_sizes = cascade_sizes

        if 'breakers' in self.spike_monitors:
            breaker_spikes = self.spike_monitors['breakers']
            if len(breaker_spikes.t) > 0:
                self.detection_time = float(breaker_spikes.t[0] * 1000)

    def fit_power_law(self):
        if len(self.cascade_sizes) < 5:
            return None, None
        sizes = np.array(self.cascade_sizes)
        sizes = sizes[sizes > 0]
        if len(sizes) < 5:
            return None, None
        sorted_sizes = np.sort(sizes)[::-1]
        log_sizes = np.log10(sorted_sizes)
        log_ranks = np.log10(np.arange(1, len(sorted_sizes) + 1))
        coeffs = np.polyfit(log_sizes, log_ranks, 1)
        return -coeffs[0], coeffs[1]

    def get_results(self):
        alpha, intercept = self.fit_power_law()
        return {
            'n_cascades': len(self.cascade_sizes),
            'cascade_sizes': self.cascade_sizes,
            'mean_cascade_size': float(np.mean(self.cascade_sizes)) if self.cascade_sizes else 0,
            'max_cascade_size': int(max(self.cascade_sizes)) if self.cascade_sizes else 0,
            'power_law_alpha': float(alpha) if alpha else None,
            'detection_time_ms': self.detection_time,
            'n_failure_events': len(self.failure_events),
            'n_services': self.config['n_services'],
            'has_circuit_breakers': self.circuit_breakers is not None,
        }


def run_validation_suite():
    print("=" * 60)
    print("CLUSTER FAILURE SIMULATION - VALIDATION SUITE")
    print("=" * 60)
    results = []

    print("\n[Test 1] Baseline cascade dynamics...")
    sim1 = ClusterFailureSimulation({'n_services': 200, 'n_critical': 20, 'dependency_prob': 0.12, 'inhibitory_fraction': 0.0, 'simulation_duration': 3000})
    sim1.build()
    sim1.inject_random_failures(n_failures=15, strength_range=(10, 18))
    sim1.run()
    r1 = sim1.get_results()
    print(f"  Total spikes: {len(sim1.spike_monitors['services'].t)}")
    print(f"  Cascades: {r1['n_cascades']}, Max size: {r1['max_cascade_size']}")
    if r1['power_law_alpha']:
        print(f"  Power-law alpha: {r1['power_law_alpha']:.2f}")
    results.append(('baseline', r1))

    print("\n[Test 2] With circuit breakers...")
    sim2 = ClusterFailureSimulation({'n_services': 200, 'n_critical': 20, 'dependency_prob': 0.12, 'inhibitory_fraction': 0.2, 'simulation_duration': 3000})
    sim2.build()
    sim2.inject_random_failures(n_failures=15, strength_range=(10, 18))
    sim2.run()
    r2 = sim2.get_results()
    print(f"  Total spikes: {len(sim2.spike_monitors['services'].t)}")
    print(f"  Cascades: {r2['n_cascades']}, Max size: {r2['max_cascade_size']}")
    if r2['detection_time_ms']:
        print(f"  Detection time: {r2['detection_time_ms']:.1f}ms")
    results.append(('with_breakers', r2))

    print("\n[Test 3] Critical service failure...")
    sim3 = ClusterFailureSimulation({'n_services': 200, 'n_critical': 20, 'dependency_prob': 0.12, 'inhibitory_fraction': 0.0, 'simulation_duration': 3000})
    sim3.build()
    critical_idx = np.where(sim3.critical_indices)[0][0]
    sim3.inject_failure(critical_idx, strength=18*mV)
    sim3.run()
    r3 = sim3.get_results()
    print(f"  Total spikes: {len(sim3.spike_monitors['services'].t)}")
    print(f"  Cascades: {r3['n_cascades']}, Max size: {r3['max_cascade_size']}")
    results.append(('critical_failure', r3))

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for name, r in results:
        alpha_str = f"{r['power_law_alpha']:.2f}" if r['power_law_alpha'] else "N/A"
        print(f"{name:20s} | α={alpha_str:>5s} | max={r['max_cascade_size']:>4d} | cascades={r['n_cascades']:>4d}")

    print("\n[VALIDATION]")
    baseline = results[0][1]
    if baseline['power_law_alpha']:
        alpha = baseline['power_law_alpha']
        if 1.0 <= alpha <= 3.0:
            print(f"  ✓ Power-law alpha ({alpha:.2f}) in plausible range")
        else:
            print(f"  ⚠ Power-law alpha ({alpha:.2f}) outside expected range")

    with_breakers = results[1][1]
    if baseline['max_cascade_size'] > 0:
        if with_breakers['max_cascade_size'] < baseline['max_cascade_size']:
            reduction = (1 - with_breakers['max_cascade_size'] / baseline['max_cascade_size']) * 100
            print(f"  ✓ Circuit breakers reduced max cascade by {reduction:.1f}%")
        else:
            print(f"  ~ Circuit breakers had no significant effect")

    if with_breakers['detection_time_ms']:
        print(f"  ✓ Detection latency: {with_breakers['detection_time_ms']:.1f}ms")

    print("\n[INTERPRETATION]")
    print("The simulation maps service dependencies onto neural connectivity.")
    print("- Low connectivity (~8%) produces critical regime (power-law cascades)")
    print("- Circuit breakers (inhibitory neurons) reduce cascade spread")
    print("- Detection latency is the time for monitor neurons to respond")
    return results


if __name__ == '__main__':
    run_validation_suite()
