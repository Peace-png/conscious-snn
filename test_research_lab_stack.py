#!/usr/bin/env python3
"""
Test Research Lab Stack - FLOW HEALTH (not phase sync)

Key insight: Research agents DON'T need to be in phase sync.
They need FLOW HEALTH - does the research question propagate correctly?

Measures:
1. PROPAGATION: Does Director signal reach all agents?
2. LATENCY: How long for wave to reach Publisher?
3. INTEGRITY: Does signal degrade through the chain?
"""

import numpy as np

N_AGENTS = 14
agent_names = [
    'Director', 'Scientist', 'Skeptic', 'Ideologist', 'Experimenter',
    'Historian', 'Philosopher', 'Explainer', 'Artist', 'Archivist',
    'Synthesiser', 'Publisher', 'GroundTruth', 'Simulator'
]

# Execution flow waves
WAVE_MEMBERSHIP = {
    0: [0],           # Wave 0: Director
    1: [1, 2, 5],    # Wave 1: Scientist, Skeptic, Historian
    2: [4, 6, 7],    # Wave 2: Experimenter, Philosopher, Explainer
    3: [3, 13, 12],   # Wave 3: Ideologist, Simulator, GroundTruth
    4: [8, 9],         # Wave 4: Artist, Archivist
    5: [10],           # Wave 5: Synthesiser
    6: [11],           # Wave 6: Publisher
}

# Agent roles
ROLE_TYPE = {
    'Director': 'ORCHESTRATOR',
    'Scientist': 'EXCITATORY',
    'Skeptic': 'INHIBITORY',
    'Ideologist': 'EXCITATORY',  # Generates NEW ideas
    'Experimenter': 'EXCITATORY',
    'Historian': 'EXCITATORY',
    'Philosopher': 'EXCITATORY',
    'Explainer': 'EXCITATORY',
    'Artist': 'EXCITATORY',
    'Archivist': 'NEUTRAL',
    'Synthesiser': 'NEUTRAL',
    'Publisher': 'NEUTRAL',
    'GroundTruth': 'INHIBITORY',  # Validates (inhibits false claims)
    'Simulator': 'NEUTRAL',  # Tests without bias
}

# Signal propagation simulation
# Each agent has a "signal strength" that propagates through waves

np.random.seed(42)

def simulate_research_flow(research_question_complexity=0.5, skeptic_strength=0.5):
    """
    Simulate how a research question flows through the stack.

    research_question_complexity: 0-1, higher = harder to process
    skeptic_strength: 0-1, higher = more likely to HALT

    Returns: (success, path_integrity, bottleneck_agent)
    """
    # Initial signal from Director
    signal = 1.0 - research_question_complexity * 0.3

    # Track per-agent signal
    agent_signal = np.zeros(N_AGENTS)
    agent_signal[0] = signal  # Director starts with full signal

    # Wave-by-wave propagation
    for wave in range(1, 7):
        members = WAVE_MEMBERSHIP[wave]
        for agent_idx in members:
            name = agent_names[agent_idx]
            role = ROLE_TYPE[name]

            # Find who feeds this agent (incoming connections)
            incoming = []
            if wave == 1:
                incoming = [0]  # From Director
            elif wave == 2:
                incoming = [1, 2, 5]  # From Wave 1
            elif wave == 3:
                if agent_idx == 3:  # Ideologist
                    incoming = [4]  # From Experimenter
                elif agent_idx == 13:  # Simulator
                    incoming = [3, 4]  # From Ideologist + Experimenter
                elif agent_idx == 12:  # GroundTruth
                    incoming = [1]  # From Scientist
            elif wave == 4:
                if agent_idx == 8:  # Artist
                    incoming = [13]  # From Simulator
                elif agent_idx == 9:  # Archivist
                    incoming = list(range(N_AGENTS))  # From all
            elif wave == 5:
                incoming = [9]  # From Archivist
            elif wave == 6:
                incoming = [13, 12]  # From Simulator + GroundTruth

            # Compute incoming signal
            if not incoming:
                incoming_signal = signal * 0.5
            else:
                incoming_signal = np.mean([agent_signal[i] for i in incoming if i < len(agent_signal)])

            # Apply role-based modulation
            if role == 'EXCITATORY':
                output = incoming_signal * 0.95  # Slight boost
            elif role == 'INHIBITORY':
                # Skeptic/GroundTruth can HALT if signal too low
                if name == 'Skeptic':
                    output = incoming_signal * (1 - skeptic_strength * 0.5)
                    if output < 0.3:
                        return False, 0.0, name  # HALT
                else:  # GroundTruth
                    output = incoming_signal * 0.9
                    if output < 0.2:
                        return False, 0.0, name  # HALT
            else:  # NEUTRAL
                output = incoming_signal * 0.98

            agent_signal[agent_idx] = max(0, output)

    # Final: Publisher signal
    final_signal = agent_signal[11]
    success = final_signal > 0.1
    path_integrity = np.mean(agent_signal)

    return success, path_integrity, agent_signal


# === RUN MULTIPLE SCENARIOS ===
print("\n" + "="*60)
print("RESEARCH LAB STACK - FLOW HEALTH TEST")
print("="*60)

scenarios = [
    ("Simple question", 0.2, 0.3),
    ("Standard research", 0.5, 0.5),
    ("Complex question", 0.8, 0.5),
    ("Adversarial (strong skeptic)", 0.5, 0.8),
    ("Maximum difficulty", 0.9, 0.9),
]

results = []
print(f"\n{'Scenario':<25} {'Success':>8} {'Integrity':>10} {'Final Signal':>12} {'Status':<15}")
print("-"*60)

for name, complexity, skeptic in scenarios:
    success, integrity, signals = simulate_research_flow(complexity, skeptic)
    status = "✅ PASS" if success else "❌ HALT"
    print(f"{name:<25} {str(success):>8} {integrity:>10.4f} {signals[11]:>12.4f} {status}")
    results.append((name, success, integrity))

# Agent contribution analysis
print("\n" + "-"*60)
print("AGENT SIGNAL CONTRIBUTION (Standard Scenario)")
print("-"*60)

_, _, standard_signals = simulate_research_flow(0.5, 0.5)
print(f"{'Agent':<15} {'Role':>12} {'Signal':>10} {'Health':<12}")
print("-"*60)

for i, name in enumerate(agent_names):
    sig = standard_signals[i]
    role = ROLE_TYPE[name]
    if sig > 0.7:
        health = "STRONG"
    elif sig > 0.4:
        health = "MODERATE"
    elif sig > 0.1:
        health = "WEAK"
    else:
        health = "DEAD"
    print(f"{name:<15} {role:>12} {sig:>10.4f} {health}")

# Verdict
print("\n" + "="*60)
print("VERDICT")
print("="*60)
pass_count = sum(1 for _, s, _ in results if s)
print(f"Pass Rate: {pass_count}/{len(scenarios)} scenarios")

if pass_count >= 4:
    print("✅ STACK IS HEALTHY - Flow propagates correctly")
    print("   Ideologist → Simulator loop maintains research focus")
elif pass_count >= 2:
    print("⚠️ STACK MODERATE - Some scenarios fail")
    print("   Consider: reduce skeptic strength for complex topics")
else:
    print("❌ STACK UNHEALTHY - High failure rate")
    print("   Check: coupling weights, skeptic threshold")
print("="*60)

# === FLOW BOTTLENECK ANALYSIS ===
print("\n" + "-"*60)
print("BOTTLENECK ANALYSIS")
print("-"*60)

# Find weakest links
_, _, sig = simulate_research_flow(0.5, 0.5)
agent_health = [(agent_names[i], sig[i]) for i in range(N_AGENTS)]
agent_health.sort(key=lambda x: x[1])

print("Weakest signals (potential bottlenecks):")
for name, signal in agent_health[:5]:
    print(f"  {name}: {signal:.4f}")

print("\nStrongest signals:")
for name, signal in agent_health[-3:]:
    print(f"  {name}: {signal:.4f}")
