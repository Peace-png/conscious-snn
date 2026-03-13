# Research Report: Coupled Oscillatory Neural Systems Stability

## Query Analysis

The original query was decomposed into eight strategic sub-questions:

1. How to couple multiple neural populations without causing instability
2. Connection weight scaling laws for inter-system connections
3. Delay parameters for biologically realistic coupling
4. Phase locking and synchronization in coupled oscillators
5. Kuramoto model insights for neural synchronization
6. How many systems can be coupled before instability occurs
7. Feedback loop stability (positive vs negative feedback)
8. Brian2-specific patterns for connecting systems

---

## Findings

### 1. Coupling Multiple Neural Populations Without Instability

The key insight from dynamical systems theory is that **coupling strength must be calibrated against natural frequency dispersion**. From the Master Stability Function (MSF) framework (Pecora & Carroll, 1998), synchronization stability depends on:

```
sigma_min < K * lambda_i < sigma_max
```

Where:
- `K` = coupling strength
- `lambda_i` = eigenvalues of connectivity Laplacian
- `sigma_min/max` = stability window from MSF

**Practical Guidelines for the 8-System Architecture:**

| Strategy | Implementation | Reason |
|----------|---------------|--------|
| Sparse connectivity | p=0.01-0.05 | Reduces eigenvalue spread |
| Heterogeneous delays | 1-15ms range | Desynchronizes transient spikes |
| Weight normalization | Sum of inputs < threshold | Prevents runaway excitation |
| Inhibitory balance | E/I ratio ~4:1 | Maintains homeostasis |
| Frequency separation | Different oscillation bands | Prevents resonant coupling |

**Critical Threshold**: For N coupled oscillators with frequency spread `gamma`, the critical coupling for synchronization is:

```
K_c = 2 * gamma / (pi * g(0))
```

For your 8 systems with frequencies [0.5, 1, 0.25, 6, 8, 50, 10, 10] Hz, the spread is large (gamma ~ 50 Hz). This means **weak coupling is actually preferred** to prevent forced synchronization that would erase system identity.


### 2. Connection Weight Scaling Laws

For networks of coupled oscillators, weight scaling follows **inverse square root of population size** for maintaining stable dynamics:

```
w_ij ~ 1 / sqrt(N_source)
```

**For the Conscious SNN with 8 systems of vastly different sizes:**

| System | N (scaled) | Weight Scale Factor |
|--------|------------|---------------------|
| brainstem | 1,000,000 | 0.001 |
| prefrontal | 2,000,000 | 0.0007 |
| limbic | 1,300,000 | 0.00088 |
| hippocampus | 300,000 | 0.0018 |
| thalamus | 100,000 | 0.0032 |
| dmn | 500,000 | 0.0014 |
| cardiac | 400 | 0.05 |
| respiratory | 100 | 0.10 |

**However**, this biological scaling is for individual neurons. Your system uses population-level coupling where each "neuron" represents a population aggregate. The correct scaling is:

```python
# Population-level coupling (your current approach)
# w_ij should be scaled by influence_matrix, not N
w_effective = influence_weight * base_weight / sqrt(N_target_connections)
```

**Recommended Base Weights:**
```python
BASE_WEIGHT = 0.3 * mV  # Per-synapse contribution
INFLUENCE_SCALE = 0.3   # Max influence produces ~9mV total input

# Total input to neuron = w * N_inputs * influence
# With p=0.02 connectivity and N=1000 source neurons:
# N_inputs ~ 20, Total ~ 0.3mV * 20 = 6mV (safe)
```


### 3. Biologically Realistic Delay Parameters

**Biological Delay Sources:**

| Source | Range | Notes |
|--------|-------|-------|
| Axonal conduction | 0.5-50 ms | Depends on distance, myelination |
| Synaptic transmission | 0.5-2 ms | Chemical vs electrical |
| Dendritic integration | 1-10 ms | Passive cable properties |

**Distance-Based Delay Estimates for Brain Regions:**

| Pathway | Distance | Expected Delay |
|---------|----------|----------------|
| Brainstem -> Thalamus | 5-7 cm | 5-15 ms |
| Thalamus -> Cortex | 3-5 cm | 3-10 ms |
| Hippocampus -> Prefrontal | 8-10 cm | 10-25 ms |
| Cardiac -> Brainstem | 30 cm (vagus) | 50-100 ms |
| Respiratory -> Brainstem | Local | 2-5 ms |
| Limbic -> DMN | 5-8 cm | 5-15 ms |

**Recommended Delay Configuration:**

```python
# Delay matrix (in ms) - based on anatomical distances
DELAYS_MS = {
    ('brainstem', 'thalamus'): 10,
    ('brainstem', 'cardiac'): 50,
    ('brainstem', 'respiratory'): 3,
    ('thalamus', 'prefrontal'): 5,
    ('thalamus', 'dmn'): 8,
    ('hippocampus', 'prefrontal'): 15,
    ('hippocampus', 'dmn'): 10,
    ('limbic', 'prefrontal'): 8,
    ('limbic', 'hippocampus'): 5,
    ('cardiac', 'brainstem'): 30,  # Feedback slower
    ('respiratory', 'hippocampus'): 20,  # Nasal->olfactory->hippocampal
    # ... etc
}
```


### 4. Phase Locking and Synchronization

**Phase Locking Value (PLV):**

```
PLV = |1/N * sum(exp(i * (phi_j - phi_k)))|
```

PLV ranges from 0 (no locking) to 1 (perfect locking).

**Key Conditions for Stable Phase Locking:**

1. **Frequency detuning**: `|omega_i - omega_j| < K` (coupling must exceed frequency difference)
2. **Phase relationship**: Stable fixed points exist when `sin(delta_phi) = delta_omega / K`
3. **Delay effects**: Delays create effective phase shifts: `phi_eff = 2*pi*f*delay`

**For Your 8 Systems:**

The frequency spread is so large (0.25 Hz to 50+ Hz) that **full phase locking is impossible** and undesirable. Instead, aim for:

- **Partial synchronization**: Systems with similar frequencies (thalamus/DMN at 10 Hz, limbic/hippocampus at 6-8 Hz)
- **Frequency coordination**: Cross-frequency coupling (gamma from PFC modulated by theta from hippocampus)
- **Transient coordination**: Brief phase locking during events, not permanent


### 5. Kuramoto Model Insights

The Kuramoto model describes N coupled oscillators:

```
d_theta_i/dt = omega_i + (K/N) * sum(sin(theta_j - theta_i))
```

**Critical Coupling for Synchronization:**

```
K_c = 2 / (pi * g(0))
```

For Gaussian frequency distribution with width `gamma`: `K_c = 2*gamma`

**Insights for Your Architecture:**

1. **With your frequency spread** (gamma ~ 50 Hz for [0.25, 50] range), full synchronization requires K ~ 100 Hz - **impossible with biological weights**

2. **Partial synchronization** emerges naturally in systems with:
   - Similar frequencies (thalamus-DMN at 10 Hz)
   - Strong coupling (brainstem autonomic outputs)

3. **Chimera states** possible: Some systems synchronized while others drift - this is actually **desirable** for consciousness modeling

4. **Order parameter** `r` measures global coherence:
   ```python
   r = |1/N * sum(exp(i*theta_j))|
   # r=0: incoherent, r=1: fully synchronized
   # For consciousness: r ~ 0.3-0.7 is interesting (partial coordination)
   ```


### 6. How Many Systems Before Instability?

**Theoretical Limits:**

From random network theory, stability requires:
```
K * sqrt(N) * <w> < threshold
```

Where `<w>` is average weight and threshold is the stability boundary.

**Practical Findings from Neuroscience:**

| Brain Scale | N Regions | Connectivity | Status |
|-------------|-----------|--------------|--------|
| Macro-scale | ~100 | 20-30% | Stable |
| Mesoscale | ~1000 | 5-10% | Stable |
| Microscale | ~10^5 | 0.1% | Stable |

**For 8 Systems:**

8 systems is **well within stability limits**. The key constraint is not the number of systems but:

1. **Coupling density**: 8x8 = 64 possible connections, but only ~20-30 should be non-zero
2. **Feedback loops**: Avoid long positive feedback chains
3. **Weight balance**: Total excitation must be balanced by inhibition


### 7. Feedback Loop Stability

**Positive Feedback:**
- Amplifies signals
- Creates bistability, oscillations
- Risk: runaway excitation, seizure-like dynamics

**Negative Feedback:**
- Dampens signals
- Promotes stability
- Risk: over-damping, no activity

**Stability Criterion (Routh-Hurwitz):**

For feedback loop with gain G and delay tau:
```
|G| < 1  =>  Stable
|G| = 1  =>  Marginal (oscillations possible)
|G| > 1  =>  Unstable
```

**For Your 8 Systems:**

The architecture should follow **E/I balance** principles:

```
Excitatory loop gain < 1
Inhibitory loop gain < 1
Total loop gain (E - I) ~ 0.5-0.8
```

**Problematic Loops to Avoid:**

```python
# AVOID: Long positive feedback chains
prefrontal -> limbic -> hippocampus -> prefrontal (3-hop, all excitatory)

# PREFER: Intersperse inhibition
prefrontal -> limbic -> (inhibitory interneuron) -> hippocampus -> prefrontal
```


### 8. Brian2-Specific Patterns for Connecting Systems

**Pattern 1: Sparse Random Connectivity with Delays**

```python
from brian2 import Synapses, ms, mV

def create_inter_system_connection(source, target, weight, delay_range, p=0.02):
    syn = Synapses(
        source, target,
        model='w_syn : volt',
        on_pre='I_exc_post += w_syn',
        name=f'syn_{source.name}_to_{target.name}'
    )
    syn.connect(p=p)
    syn.w_syn = weight
    syn.delay = f'{delay_range[0]}*ms + rand()*{delay_range[1]-delay_range[0]}*ms'
    return syn
```

**Pattern 2: Distance-Based Delays**

```python
# Define anatomical distances (arbitrary units, scale to ms)
DISTANCES = {
    ('brainstem', 'thalamus'): 10,
    ('brainstem', 'prefrontal'): 15,
    # ... etc
}

CONDUCTION_VELOCITY = 1.0  # ms per distance unit

def get_delay(source, target):
    key = (source, target)
    dist = DISTANCES.get(key, DISTANCES.get((target, source), 5))
    return dist * CONDUCTION_VELOCITY
```

**Pattern 3: Weight Clamping in Synapses**

```python
# Current approach (in base.py) is good:
on_pre='I_exc_post = clip(I_exc_post + w_syn*0.3*mV, -30*mV, 30*mV)'
```

**Pattern 4: State Monitoring for Stability**

```python
# Monitor for runaway activity
stability_monitor = StateMonitor(
    neuron_group,
    ['v', 'I_exc', 'I_inh'],
    record=True
)

# Check after simulation
if np.any(np.isnan(stability_monitor.v)) or np.any(np.abs(stability_monitor.v) > 100*mV):
    print("WARNING: Numerical instability detected")
```


---

## Strategic Insights

### Second-Order Effects to Consider

1. **Frequency entrainment risk**: Strong coupling can force all systems to oscillate at the dominant frequency (likely brainstem at 0.5-2 Hz), erasing the multi-frequency dynamics essential for consciousness modeling.

2. **Delay-induced instabilities**: Large delays can cause "delayed feedback oscillations" - a system receiving input from its own past output at the wrong phase. This is a real phenomenon in neural systems (e.g., Parkinsonian tremor).

3. **Scale mismatch vulnerability**: The cardiac (400 neurons) and respiratory (100 neurons) systems are orders of magnitude smaller than cortical systems. Without proper scaling, they can be overwhelmed or ignored.

4. **Numerical accumulation**: Each inter-system connection adds to `I_exc` or `I_inh`. With 20+ connections per system, accumulated input can exceed clamping limits.

### Three-Moves-Ahead Analysis

**Move 1 (Current State):** 8 systems with uniform 2% connectivity and 1-6ms delays. Influence matrix defines coupling strengths.

**Move 2 (Immediate Risk):** If all connections are active simultaneously, a single spike storm in brainstem cascades through thalamus -> cortex -> DMN -> back to thalamus, creating a positive feedback loop that destabilizes the simulation.

**Move 3 (Strategic Fix):** Implement **competitive normalization** - inter-system inputs compete for a fixed "attention budget" per system. This prevents cascade failures while preserving information routing.

---

## Recommendations

### For the Conscious SNN Project

#### 1. Implement Competitive Normalization

```python
# In neuron model, add:
dI_inter/dt = -I_inter / tau_inter : volt

# At each timestep, normalize inter-system inputs:
group.run_regularly('''
I_inter_total = I_brainstem + I_cortical + I_thalamic + I_limbic
if I_inter_total > 20*mV:
    scale = 20*mV / I_inter_total
    I_brainstem *= scale
    I_cortical *= scale
    I_thalamic *= scale
    I_limbic *= scale
''', dt=1*ms)
```

#### 2. Use Distance-Based Delays

Replace uniform delays with anatomically-based values:

```python
# In connectivity/influence.py, add:
ANATOMICAL_DELAYS = {
    ('brainstem', 'thalamus'): (8, 15),
    ('brainstem', 'cardiac'): (40, 80),
    ('brainstem', 'respiratory'): (2, 5),
    ('thalamus', 'prefrontal'): (3, 8),
    ('thalamus', 'dmn'): (5, 10),
    ('hippocampus', 'prefrontal'): (10, 20),
    ('limbic', 'prefrontal'): (5, 12),
    ('limbic', 'hippocampus'): (3, 8),
    ('cardiac', 'brainstem'): (30, 50),
    ('respiratory', 'hippocampus'): (15, 25),
    # ... add remaining pairs
}
```

#### 3. Reduce Inter-System Connectivity Probability

Current 2% is appropriate. Consider making it system-specific:

```python
# Systems with more focused projections should have lower p
CONNECTIVITY_PROB = {
    'brainstem': 0.03,    # Diffuse arousal
    'thalamus': 0.02,     # Relay-specific
    'hippocampus': 0.015, # Sparse but targeted
    'prefrontal': 0.01,   # Highly selective
    'limbic': 0.02,       # Moderate
    'dmn': 0.025,         # Hub-like
    'cardiac': 0.01,      # Limited CNS projection
    'respiratory': 0.01,  # Limited CNS projection
}
```

#### 4. Implement Loop Gain Monitoring

```python
def compute_loop_gain(network):
    """Estimate total loop gain for each system."""
    gains = {}
    for name, system in network.systems.items():
        # Sum of incoming weights * connectivity
        incoming = sum(
            network.influence_matrix.get_weight(src, name)
            for src in network.systems.keys()
            if src != name
        )
        gains[name] = incoming * 0.02 * len(system.neuron_group) / 1000
    return gains
```

#### 5. Add Cross-Frequency Coupling Term

```python
# For hippocampus->prefrontal, add theta-gamma coupling:
# Gamma amplitude modulated by theta phase

hippoc_theta_phase = 'sin(2*pi*8*Hz*t)'  # Theta from hippocampus

# In prefrontal neuron model:
I_gamma_modulated = I_gamma * (1 + 0.5 * hippoc_theta_phase)
```

---

## Evidence & Citations

1. **Pecora LM, Carroll TL (1998)**. "Master stability functions for synchronized coupled systems." *Physical Review Letters*, 80(10):2109. DOI:10.1103/PhysRevLett.80.2109

2. **Kuramoto Y (1984)**. *Chemical Oscillations, Waves, and Turbulence*. Springer-Verlag.

3. **Strogatz SH (2000)**. "From Kuramoto to Crawford: exploring the onset of synchronization in populations of coupled oscillators." *Physica D*, 143(1-4):1-20. DOI:10.1016/S0167-2789(00)00094-4

4. **Breakspear M, Heitmann S, Daffertshofer A (2010)**. "Generative models of cortical oscillations: neurobiological implications of the Kuramoto model." *Frontiers in Human Neuroscience*, 4:190. DOI:10.3389/fnhum.2010.00190

5. **Deco G, Jirsa VK, McIntosh AR, Sporns O, Kotter R (2009)**. "Key role of coupling, delay, and noise in resting brain fluctuations." *PNAS*, 106(25):10302-10307. DOI:10.1073/pnas.0901831106

6. **Cabral J, Hugues E, Sporns O, Deco G (2011)**. "Role of local network oscillations in resting-state functional connectivity." *NeuroImage*, 57(1):130-139. DOI:10.1016/j.neuroimage.2011.04.010

7. **Izhikevich EM (1998)**. "Phase models with explicit time delays." *Physical Review E*, 58(1):905. DOI:10.1103/PhysRevE.58.905

8. **Brette R, Gerstner W (2005)**. "Adaptive exponential integrate-and-fire model as an effective description of neuronal activity." *Journal of Neurophysiology*, 94(5):3637-42. DOI:10.1152/jn.00686.2005

9. **Brian2 Documentation v2.8.0.4**. https://brian2.readthedocs.io/

10. **Gerstner W, Kistler WM, Naud R, Paninski L**. *Neuronal Dynamics: From Single Neurons to Networks and Models of Cognition*. Cambridge University Press. https://neuronaldynamics.epfl.ch/


---

## Summary Table

| Topic | Key Finding | Application to Conscious SNN |
|-------|-------------|------------------------------|
| Coupling stability | K < frequency spread | Weak coupling preserves system identity |
| Weight scaling | w ~ 1/sqrt(N) | Scale by target, not source |
| Delays | 2-50 ms based on distance | Use anatomical delay matrix |
| Phase locking | Partial synchronization desirable | Aim for r ~ 0.3-0.7 |
| Kuramoto model | K_c = 2*gamma | Your systems won't fully sync (good) |
| N systems | 8 is stable | Not a limiting factor |
| Feedback | E/I balance, gain < 1 | Add competitive normalization |
| Brian2 patterns | Sparse + clamped + monitored | Already implemented, refine delays |


---

*Research conducted: 2026-03-13*
*Agent: Ava Sterling (Claude Researcher)*
*Scope: Coupled oscillatory neural systems stability for 8-system conscious SNN*
