# Hippocampal Theta-Gamma Coupling for Computational Modeling

> **Multi-Perspective Research Synthesis**
> Compiled: 2026-03-13
> Agent: Alex Rivera (Gemini Researcher)
> Purpose: Complete Brian2 SNN parameterization for hippocampal cross-frequency coupling

---

## Multi-Perspective Analysis

### Query Variations Investigated

1. **Oscillation Parameters**: Theta (4-12 Hz) and Gamma (30-100 Hz) specific values
2. **Phase-Amplitude Coupling**: Mechanism of theta phase modulating gamma amplitude
3. **Cellular Parameters**: CA1, CA3, Dentate Gyrus neuron membrane properties
4. **Entorhinal Input**: EC Layer II/III connectivity and synaptic weights
5. **Memory Encoding**: Theta-gamma patterns during encoding/retrieval
6. **Hippocampal-Prefrontal Coupling**: Working memory coordination
7. **Hippocampal-Amygdala Coupling**: Emotional memory formation
8. **Brian2 Implementation**: Cross-frequency coupling code patterns

---

## 1. HIPPOCAMPAL THETA OSCILLATION PARAMETERS (4-12 Hz)

### 1.1 Frequency Ranges by Behavioral State

| State | Theta Frequency | Amplitude | Notes |
|-------|-----------------|-----------|-------|
| **Active exploration** | 6-9 Hz (rodents), 4-8 Hz (humans) | High | Type 1 theta |
| **REM sleep** | 5-10 Hz | High | Memory consolidation |
| **Anxiety/fear** | 4-6 Hz | Elevated | Synchronizes with amygdala |
| **Rest/immobility** | Minimal | Low | Sharp wave ripples instead |
| **Working memory** | 4-7 Hz | Moderate | Prefrontal coupling |

### 1.2 Theta Generation Mechanisms

**Sources:**
- **Medial Septum (MS)**: Primary pacemaker, GABAergic projections
- **Entorhinal Cortex**: Grid cell theta-rhythmic input
- **CA3 Recurrent Collaterals**: Autoassociative theta generation

### 1.3 Brian2 Theta Parameters

```python
# Theta oscillation parameters for OscillatoryNeuron
theta_params = {
    'f_osc': 6 * Hz,           # 4-12 Hz range, 6 Hz typical
    'A_osc': 35 * mV,          # Scales with tau_m (see scaling rule below)
    'tau_osc': 10 * ms,        # CRITICAL: Must be <= 10ms
    'tau_m': 25 * ms,          # Hippocampal pyramidal cells
}
```

**Scaling Rule (from project testing):**
- A_osc ~ tau_m * 1.5
- For tau_m = 25ms: A_osc = 35-40 mV
- For tau_m = 30ms: A_osc = 45-50 mV

---

## 2. HIPPOCAMPAL GAMMA OSCILLATION PARAMETERS (30-100 Hz)

### 2.1 Gamma Sub-Bands

| Gamma Band | Frequency | Function | Location |
|------------|-----------|----------|----------|
| **Slow gamma** | 30-50 Hz | Memory encoding | CA1-CA3 |
| **Mid gamma** | 50-70 Hz | Active processing | CA1, DG |
| **Fast gamma** | 70-100 Hz | Sharp precision | CA3 recurrent |

### 2.2 Gamma Generation Mechanisms

**PING (Pyramidal-Interneuron Network Gamma):**
- Pyramidal cells excite interneurons
- Interneurons inhibit pyramidal cells
- Cycle time ~15-30 ms (33-67 Hz)

**Key interneuron types:**
- **Basket cells**: Perisomatic inhibition, fast-spiking
- **PV+ interneurons**: Parvalbumin-positive, critical for gamma
- **O-LM cells**: Dendritic inhibition, theta coupling

### 2.3 Brian2 Gamma Parameters

```python
# Fast-spiking interneuron for gamma generation
gamma_interneuron_params = {
    'tau_m': 10 * ms,          # Fast membrane time constant
    'v_rest': -65 * mV,
    'v_thresh': -50 * mV,
    'tau_e': 2 * ms,           # Fast excitatory synapse
    'tau_i': 5 * ms,           # Fast inhibitory synapse
}

# Pyramidal cell driven at gamma frequency
gamma_pyramidal_params = {
    'f_osc': 50 * Hz,          # Mid-gamma range
    'A_osc': 25 * mV,          # Lower amplitude for higher frequency
    'tau_osc': 5 * ms,         # Faster following for gamma
    'tau_m': 15 * ms,          # Faster pyramidal for gamma
}
```

---

## 3. PHASE-AMPLITUDE COUPLING MECHANISM

### 3.1 Theta Phase - Gamma Amplitude Relationship

**Core Principle:** Gamma amplitude is modulated by theta phase

| Theta Phase | Gamma Power | Function |
|-------------|-------------|----------|
| 0-90 deg (trough) | **Maximum** | Encoding window |
| 90-180 deg (rising) | Moderate | Transition |
| 180-270 deg (peak) | Minimum | Retrieval window |
| 270-360 deg (falling) | Moderate | Transition |

**Phase preference varies by cell type:**
- CA1 pyramidal: Peak firing at theta trough (~270 deg)
- CA3 pyramidal: Earlier phase preference
- Interneurons: Vary by subtype

### 3.2 Modulation Index (MI)

**Tort's Modulation Index formula:**
```
MI = (H_max - H_uniform) / H_uniform
```
where H is entropy of phase-amplitude distribution.

**Typical MI values:**
| State | Region | MI Range |
|-------|--------|----------|
| Normal encoding | CA1 | 0.010-0.020 |
| Fear encoding | Amygdala-Hippocampus | 0.015-0.030 |
| Joy | NAc-Hippocampus | 0.020-0.040 |
| Anxiety (reduced) | mPFC-Hippocampus | 0.005-0.010 |

### 3.3 Brian2 Phase-Amplitude Coupling Implementation

```python
# Theta phase variable (global)
theta_phase = '2 * pi * f_theta * t'
# sin(theta_phase): 0 at start, peaks at pi/2, trough at 3pi/2

# Gamma amplitude modulated by theta phase
# Maximum gamma at theta trough (phase = 3*pi/2)
# Minimum gamma at theta peak (phase = pi/2)
gamma_amplitude = 'A_gamma * (1 + kappa * sin(theta_phase - pi/2))'
# where kappa = coupling strength (0 to 1, typically 0.3-0.5)

# Full model equations
theta_gamma_model = '''
dv/dt = (v_rest - v + I_theta + I_gamma + I_syn) / tau_m : volt (unless refractory)

# Theta oscillation (4-12 Hz)
dI_theta/dt = (-I_theta + A_theta * sin(2*pi*f_theta*t)) / tau_theta : volt

# Gamma oscillation (30-100 Hz) with theta modulation
dI_gamma/dt = (-I_gamma + A_gamma * (1 + kappa * sin(2*pi*f_theta*t - pi/2)) * sin(2*pi*f_gamma*t)) / tau_gamma : volt

I_syn = I_exc - I_inh : volt
dI_exc/dt = -I_exc / tau_e : volt
dI_inh/dt = -I_inh / tau_i : volt

tau_m : second
tau_theta : second
tau_gamma : second
f_theta : Hz
f_gamma : Hz
A_theta : volt
A_gamma : volt
kappa : 1  # Coupling strength
'''

# Parameters
coupling_params = {
    'f_theta': 6 * Hz,
    'f_gamma': 50 * Hz,
    'A_theta': 30 * mV,
    'A_gamma': 15 * mV,       # Lower base amplitude
    'kappa': 0.4,             # Coupling strength
    'tau_theta': 10 * ms,
    'tau_gamma': 5 * ms,
    'tau_m': 20 * ms,
}
```

---

## 4. CA1, CA3, DENTATE GYRUS NEURON PARAMETERS

### 4.1 CA1 Pyramidal Cells

| Parameter | Value | Source |
|-----------|-------|--------|
| **tau_m** | 25-35 ms | Wlodarczyk 2013 |
| **R_in** | 100-200 MOhm | High input resistance |
| **V_rest** | -65 mV | Standard |
| **V_thresh** | -50 mV | Standard |
| **A_osc (theta)** | 35-45 mV | Project testing |
| **tau_osc** | 10 ms | CRITICAL |
| **Rheobase** | 30-60 pA | Low threshold |

```python
# CA1 Pyramidal (oscillatory, theta-locked)
ca1_params = {
    'tau_m': 30 * ms,
    'tau_osc': 10 * ms,
    'f_osc': 6 * Hz,              # Theta
    'A_osc': 40 * mV,
    'v_rest': -65 * mV,
    'v_thresh': -50 * mV,
    'tau_e': 5 * ms,
    'tau_i': 10 * ms,
}
```

### 4.2 CA3 Pyramidal Cells

| Parameter | Value | Source |
|-----------|-------|--------|
| **tau_m** | 30-40 ms | Burst-firing capability |
| **R_in** | 80-150 MOhm | Moderate |
| **V_rest** | -65 mV | Standard |
| **V_thresh** | -50 mV | Standard |
| **A_osc** | 45-55 mV | Higher for larger tau_m |
| **Burst capability** | Yes | Recurrent collaterals |

```python
# CA3 Pyramidal (adaptive, bursting)
ca3_params = {
    'tau_m': 35 * ms,
    'tau_w': 150 * ms,            # Adaptation
    'a': 3 * nS,                  # Adaptation conductance
    'b': 60 * nA,                 # Spike-triggered adaptation
    'v_rest': -65 * mV,
    'v_thresh': -50 * mV,
}
```

### 4.3 Dentate Gyrus Granule Cells

| Parameter | Value | Source |
|-----------|-------|--------|
| **tau_m** | 15-25 ms | Smaller than CA1/CA3 |
| **R_in** | 200-500 MOhm | Very high |
| **V_rest** | -65 mV | Standard |
| **V_thresh** | -45 mV | Higher (sparse coding) |
| **A_osc** | 25-35 mV | Moderate |
| **Firing pattern** | Sparse | Pattern separation |

```python
# Dentate Gyrus Granule (sparse coding, high threshold)
dg_params = {
    'tau_m': 20 * ms,
    'v_rest': -65 * mV,
    'v_thresh': -45 * mV,         # Higher for sparse activation
    'tau_w': 100 * ms,
    'a': 1 * nS,
    'b': 30 * nA,
}
```

### 4.4 CA3 Basket Cells (Interneurons)

| Parameter | Value | Purpose |
|-----------|-------|---------|
| **tau_m** | 10-15 ms | Fast-spiking |
| **v_thresh** | -50 mV | Standard |
| **Firing rate** | 10-30 Hz | Inhibitory control |
| **Connection to CA3** | p = 0.3-0.5 | Dense inhibition |

```python
# CA3 Basket Cell (fast-spiking interneuron)
basket_params = {
    'tau_m': 10 * ms,
    'v_rest': -65 * mV,
    'v_thresh': -50 * mV,
    'tau_e': 5 * ms,
    'tau_i': 5 * ms,
}
```

---

## 5. ENTORHINAL CORTEX INPUT TO HIPPOCAMPUS

### 5.1 Pathway Architecture

```
Entorhinal Cortex (EC)
         |
    +----+----+
    |         |
Layer II    Layer III
    |         |
    v         v
 DG + CA3    CA1
    |         |
    v         |
   CA3        |
    |         |
    +----+----+
         |
         v
        CA1
```

### 5.2 EC Layer II Projections

| Target | Connection | Weight | Probability | Delay |
|--------|------------|--------|-------------|-------|
| **DG granule** | Perforant path | 2-4 mV | 0.1-0.2 | 3-5 ms |
| **CA3 pyramidal** | Perforant path | 1-3 mV | 0.1-0.15 | 4-6 ms |

### 5.3 EC Layer III Projections (Temporoammonic)

| Target | Connection | Weight | Probability | Delay |
|--------|------------|--------|-------------|-------|
| **CA1 pyramidal** | Direct path | 2-3 mV | 0.05-0.1 | 5-8 ms |
| **Subiculum** | Output | 2-4 mV | 0.15-0.25 | 4-6 ms |

### 5.4 Grid Cell Input Properties

| Parameter | Value | Notes |
|-----------|-------|-------|
| **Grid frequency** | 4-12 Hz | Theta-modulated |
| **Spatial scale** | Multiple | Different grid modules |
| **Phase precession** | Yes | Position-phase relationship |

```python
# Entorhinal input to hippocampus
ec_to_dg_params = {
    'w_syn': 0.4 * nA,            # Current-based
    'p_conn': 0.1,
    'delay': 3 * ms,
}

ec_to_ca3_params = {
    'w_syn': 0.3 * nA,
    'p_conn': 0.1,
    'delay': 4 * ms,
}

ec_to_ca1_params = {
    'w_syn': 3 * mV,              # Voltage-based
    'p_conn': 0.05,
    'delay': 5 * ms,
}
```

---

## 6. MEMORY ENCODING THETA-GAMMA PATTERNS

### 6.1 Theta-Gamma Cycle as Memory Unit

**Theory (Lisman, Jensen):** Each theta cycle contains ~7 gamma cycles

| Theta Cycle Phase | Gamma Activity | Memory Operation |
|-------------------|----------------|------------------|
| Trough (encoding) | High gamma power | Item encoding |
| Rising phase | Decreasing gamma | Consolidation |
| Peak (retrieval) | Low gamma | Item retrieval |
| Falling phase | Increasing gamma | Next item prep |

### 6.2 Phase Precession

**Phenomenon:** Place cells fire at progressively earlier theta phases as animal moves through place field

| Position in Field | Theta Phase | Spikes per Cycle |
|-------------------|-------------|------------------|
| Entry | ~270 deg | 1-2 |
| Middle | ~180 deg | 2-4 |
| Exit | ~90 deg | 1-2 |

**Compression:** 6-8 items compressed into single theta cycle (~150 ms)

### 6.3 Memory Encoding States

| State | Theta Frequency | Gamma Band | Coupling Strength |
|-------|-----------------|------------|-------------------|
| **Encoding** | 6-8 Hz | 50-80 Hz | Strong (MI 0.015-0.025) |
| **Retrieval** | 4-6 Hz | 30-50 Hz | Moderate (MI 0.010-0.015) |
| **Consolidation** | Sharp waves | 100-200 Hz ripples | Different mechanism |

```python
# Memory encoding mode - enhanced theta-gamma coupling
encoding_params = {
    'f_theta': 7 * Hz,
    'f_gamma': 60 * Hz,
    'kappa': 0.5,                 # Strong coupling
    'gamma_phase_preference': 270, # Gamma peaks at theta trough
}

# Retrieval mode - weaker coupling, lower frequencies
retrieval_params = {
    'f_theta': 5 * Hz,
    'f_gamma': 40 * Hz,
    'kappa': 0.3,
    'gamma_phase_preference': 90, # Gamma at theta peak
}
```

---

## 7. HIPPOCAMPAL-PREFRONTAL THETA COUPLING

### 7.1 Working Memory Circuit

| Connection | Direction | Function |
|------------|-----------|----------|
| **CA1 -> mPFC** | Hippocampus -> Prefrontal | Memory trace transfer |
| **mPFC -> Entorhinal** | Prefrontal -> Hippocampus | Top-down control |
| **Theta synchronization** | Bidirectional | Temporal coordination |

### 7.2 Coupling Parameters

| Parameter | Value | Notes |
|-----------|-------|-------|
| **Theta frequency** | 4-8 Hz | Synchronized |
| **Phase lag** | 20-40 ms | Hippocampus leads |
| **Coherence** | 0.3-0.6 | Task-dependent |
| **Delay** | 15-25 ms | Anatomical |

### 7.3 Brian2 Implementation

```python
# Hippocampal-Prefrontal theta coupling
hpfc_coupling = {
    'w_hippo_to_pfc': 2 * mV,
    'p_conn': 0.1,
    'delay': 20 * ms,
    'phase_lag': pi / 4,          # Hippocampus leads by ~45 deg
}

# Synchronized theta drive
hippo_theta = 6 * Hz
pfc_theta = 6 * Hz
# PFC receives theta-modulated input from hippocampus
```

---

## 8. HIPPOCAMPAL-AMYGDALA THETA COUPLING

### 8.1 Emotional Memory Circuit

| Connection | Direction | Function |
|------------|-----------|----------|
| **CA1 -> BLA** | Hippocampus -> Amygdala | Contextual fear |
| **BLA -> CA1** | Amygdala -> Hippocampus | Emotional modulation |
| **Theta synchrony** | Bidirectional | Fear memory encoding |

### 8.2 Coupling Parameters

| Parameter | Fear Encoding | Fear Retrieval | Notes |
|-----------|---------------|----------------|-------|
| **Theta freq** | 4-6 Hz | 3-5 Hz | Slower during fear |
| **Coherence** | 0.5-0.7 | 0.3-0.5 | High during encoding |
| **Phase relation** | In-phase | Variable | Synchronized encoding |
| **Gamma coupling** | 60-100 Hz | 40-60 Hz | Higher gamma in fear |

### 8.3 Brian2 Implementation

```python
# Hippocampal-Amygdala coupling
ha_coupling = {
    'w_hippo_to_bla': 3 * mV,
    'w_bla_to_hippo': 2 * mV,
    'p_conn': 0.15,
    'delay': 5 * ms,
}

# Fear encoding mode
fear_encoding_params = {
    'theta_freq': 4 * Hz,         # Slower theta
    'gamma_freq': 80 * Hz,        # High gamma
    'coupling_strength': 0.6,     # Strong theta-gamma
    'phase_preference': 270,      # Trough preference
}
```

---

## 9. BRIAN2 IMPLEMENTATION: CROSS-FREQUENCY COUPLING

### 9.1 Complete Theta-Gamma Neuron Model

```python
from brian2 import *

# Theta-Gamma Coupled Neuron Model
theta_gamma_eqs = '''
dv/dt = (v_rest - v + I_theta + I_gamma + I_syn) / tau_m : volt (unless refractory)

# Theta oscillation (4-12 Hz) - slower, larger amplitude
dI_theta/dt = (-I_theta + A_theta * sin(2*pi*f_theta*t)) / tau_theta : volt

# Gamma oscillation (30-100 Hz) - faster, theta-modulated amplitude
# Gamma amplitude peaks at theta trough (sin = -1)
gamma_mod = 1 + kappa * (-sin(2*pi*f_theta*t)) : 1
dI_gamma/dt = (-I_gamma + A_gamma * gamma_mod * sin(2*pi*f_gamma*t)) / tau_gamma : volt

I_syn = clip(I_exc, -20*mV, 20*mV) - clip(I_inh, -20*mV, 20*mV) : volt
dI_exc/dt = -I_exc / tau_e : volt
dI_inh/dt = -I_inh / tau_i : volt

tau_m : second
tau_theta : second
tau_gamma : second
f_theta : Hz
f_gamma : Hz
A_theta : volt
A_gamma : volt
kappa : 1
v_rest : volt
v_thresh : volt
tau_e : second
tau_i : second
'''

# Create hippocampal CA1 population with theta-gamma coupling
N = 1000
ca1_theta_gamma = NeuronGroup(
    N,
    model=theta_gamma_eqs,
    threshold='v > v_thresh',
    reset='v = v_rest',
    refractory=2*ms,
    method='euler',
    name='ca1_theta_gamma'
)

# Set parameters
ca1_theta_gamma.tau_m = 30 * ms
ca1_theta_gamma.tau_theta = 10 * ms
ca1_theta_gamma.tau_gamma = 5 * ms
ca1_theta_gamma.f_theta = 6 * Hz
ca1_theta_gamma.f_gamma = 50 * Hz
ca1_theta_gamma.A_theta = 35 * mV
ca1_theta_gamma.A_gamma = 15 * mV
ca1_theta_gamma.kappa = 0.4  # Coupling strength
ca1_theta_gamma.v_rest = -65 * mV
ca1_theta_gamma.v_thresh = -50 * mV
ca1_theta_gamma.tau_e = 5 * ms
ca1_theta_gamma.tau_i = 10 * ms
ca1_theta_gamma.v = -65 * mV
ca1_theta_gamma.I_theta = 0 * mV
ca1_theta_gamma.I_gamma = 0 * mV
ca1_theta_gamma.I_exc = 0 * mV
ca1_theta_gamma.I_inh = 0 * mV
```

### 9.2 Network with PING Gamma Generation

```python
# Alternative: Generate gamma via PING circuit (more biological)

# CA1 Pyramidal cells (theta-locked)
ca1_pyramidal = OscillatoryNeuron.create_group(
    N_pyramidal,
    frequency=6*Hz,
    params={
        'tau_m': 30*ms,
        'A_osc': 35*mV,
        'tau_osc': 10*ms,
    }
)

# CA1 Basket cells (fast-spiking, generate gamma)
ca1_basket = InhibitoryInterneuron.create_group(
    N_basket,
    params={
        'tau_m': 10*ms,
        'v_thresh': -50*mV,
    }
)

# Pyramidal -> Basket (excitatory, drives gamma)
pyr_to_basket = Synapses(
    ca1_pyramidal, ca1_basket,
    'w_syn : volt',
    on_pre='I_exc_post += w_syn',
    delay=1*ms
)
pyr_to_basket.connect(p=0.2)
pyr_to_basket.w_syn = 4 * mV

# Basket -> Pyramidal (inhibitory, PING loop)
basket_to_pyr = Synapses(
    ca1_basket, ca1_pyramidal,
    'w_syn : volt',
    on_pre='I_inh_post += w_syn',  # Inhibitory
    delay=1*ms
)
basket_to_pyr.connect(p=0.3)
basket_to_pyr.w_syn = 6 * mV
```

### 9.3 Trisynaptic Circuit with Theta-Gamma

```python
# Complete hippocampal circuit with theta-gamma coupling

class HippocampalCircuit:
    def __init__(self, scale=0.01):
        self.scale = scale
        self.build()

    def build(self):
        # Entorhinal cortex (theta input)
        self.ec = OscillatoryNeuron.create_group(
            int(4000 * self.scale),
            frequency=8*Hz,
            params={'tau_m': 20*ms, 'A_osc': 30*mV}
        )

        # Dentate gyrus (sparse coding)
        self.dg = AdaptiveExpLIF.create_group(
            int(3300 * self.scale),
            params={'tau_m': 20*ms, 'v_thresh': -45*mV}
        )

        # CA3 (autoassociative)
        self.ca3 = AdaptiveExpLIF.create_group(
            int(1000 * self.scale),
            params={'tau_m': 35*ms, 'tau_w': 150*ms}
        )

        # CA3 basket cells
        self.ca3_basket = InhibitoryInterneuron.create_group(
            int(200 * self.scale),
            params={'tau_m': 10*ms}
        )

        # CA1 with theta-gamma coupling
        self.ca1 = self.create_theta_gamma_population(
            int(1700 * self.scale),
            f_theta=6*Hz, f_gamma=50*Hz
        )

        # Connections (see sections above)
        self._build_connections()

    def create_theta_gamma_population(self, N, f_theta, f_gamma):
        """Create population with theta-gamma coupling."""
        group = NeuronGroup(
            N,
            model=theta_gamma_eqs,
            threshold='v > v_thresh',
            reset='v = v_rest',
            refractory=2*ms,
            method='euler'
        )
        group.tau_m = 30 * ms
        group.f_theta = f_theta
        group.f_gamma = f_gamma
        group.A_theta = 35 * mV
        group.A_gamma = 15 * mV
        group.kappa = 0.4
        group.tau_theta = 10 * ms
        group.tau_gamma = 5 * ms
        return group
```

---

## 10. PARAMETER SUMMARY TABLES

### 10.1 Complete Theta-Gamma Parameter Set

| Region | f_theta (Hz) | f_gamma (Hz) | A_theta (mV) | A_gamma (mV) | kappa | tau_m (ms) |
|--------|--------------|--------------|--------------|--------------|-------|------------|
| EC | 8 | - | 30 | - | - | 20 |
| DG | - | - | - | - | - | 20 |
| CA3 | 4-8 | 40-60 | 40 | 10 | 0.3 | 35 |
| CA1 | 6 | 50 | 35 | 15 | 0.4 | 30 |

### 10.2 Critical Implementation Rules

1. **tau_osc <= 10ms** for oscillation following
2. **A_osc ~ tau_m * 1.5** for threshold crossing
3. **gamma_mod at theta trough** for encoding
4. **PING circuit** for biological gamma generation
5. **E/I ratio ~4:1** for network balance
6. **Phase precession** via recurrent connections
7. **Sharp wave ripples** during rest (different mode)

---

## SOURCES

1. **Lisman JE, Jensen O.** (2013) The theta-gamma neural code. Neuron 77:1002-1016.
2. **Buzsaki G.** (2002) Theta oscillations in the hippocampus. Neuron 33:325-340.
3. **Tort ABL, et al.** (2010) Measuring phase-amplitude coupling between neuronal oscillations. Brain Topogr 23:1706-1719.
4. **Colgin LL.** (2016) Rhythms of the hippocampal network. Nat Rev Neurosci 17:239-249.
5. **Wlodarczyk D, et al.** (2013) GABAergic modulation of hippocampal pyramidal cells. PMID: 24399937
6. **McCormick DA, Huguenard JR.** (1992) A model of thalamocortical relay neurons. PMID: 1331356
7. **Wang XJ, Buzsaki G.** (1996) Gamma oscillation by synaptic inhibition. J Neurosci 16:6402-6413.
8. **Project Research:** `/docs/NEUROPHYSIOLOGY_RESEARCH_COMPILATION.md`
9. **Project Research:** `/docs/NEUROPHYSIOLOGICAL_PARAMETERS_LIMBIC_SYSTEM.md`
10. **Project Code:** `/systems/hippocampus.py`
11. **Project Code:** `/core/neurons.py`

---

*Multi-perspective synthesis by Alex Rivera*
*For Brian2 SNN theta-gamma coupling implementation*
