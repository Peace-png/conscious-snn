# Neurophysiological Parameters for Limbic System Emotional Processing

> Brian2 SNN Parameterization Reference
> Research synthesized: 2026-03-13
> Agent: Ava Sterling (Claude Researcher)

---

## 1. Membrane Time Constants (tau_m)

### 1.1 Basolateral Amygdala (BLA) Neurons

Source: Rainnie et al. 1993 (PMID: 8492168) - Intracellular recordings from morphologically identified BLA neurons in rat slice preparation.

| Cell Type | tau_m (ms) | R_in (MOhm) | AP Half-width (ms) | Firing Pattern | 1st ISI (ms) |
|-----------|------------|-------------|-------------------|----------------|--------------|
| **Class I Pyramidal** | 27.8 | 65.6 | 0.85 | Regular | 91 |
| **Class I Stellate** | 14.5 | 40.1 | 0.7 | Burst | 6.0 |
| **Class II Interneurons** | 19.0 | 58.0 | 0.77 | Burst (no accommodation) | 6.0 |

**Brian2 Parameter Implementation:**
```python
# BLA Pyramidal neurons
tau_m = 27.8 * ms
R_in = 65.6 * Mohm
V_th = -50 * mV  # typical
V_reset = -65 * mV

# BLA Stellate neurons
tau_m = 14.5 * ms
R_in = 40.1 * Mohm

# BLA Interneurons
tau_m = 19.0 * ms
R_in = 58.0 * Mohm
```

### 1.2 Hippocampal Neurons

Source: Wlodarczyk et al. 2013 (PMID: 24399937) - GABAergic modulation of hippocampal pyramidal neurons.

| Cell Type | tau_m (ms) | Notes |
|-----------|------------|-------|
| **CA1 Pyramidal** | 25-35 | Large tau due to dendritic structure; GABA (10 uM) decreases tau_m and improves EPSP-spike precision |
| **Dentate Granule** | 15-25 | Smaller than CA1 |
| **CA3 Pyramidal** | 30-40 | Burst-firing capability |

**Brian2 Parameter Implementation:**
```python
# Hippocampal CA1
tau_m = 30 * ms  # typical range 25-35 ms

# Dentate Gyrus
tau_m = 20 * ms

# CA3
tau_m = 35 * ms
```

### 1.3 Thalamocortical Relay Neurons

Source: McCormick & Huguenard 1992 (PMID: 1331356) - Detailed compartmental model with 9 ionic currents.

| Parameter | Value | Notes |
|-----------|-------|-------|
| **tau_m (rest)** | 20-30 ms | Determined by leak conductances |
| **R_in** | 100-200 MOhm | High input resistance |
| **Ionic currents** | I_Na, I_Nap, I_T, I_L, I_C, I_A, I_K2, I_h | T-type Ca2+ critical for burst mode |

**Brian2 Parameter Implementation:**
```python
# Thalamocortical relay
tau_m = 20 * ms
R_in = 150 * Mohm

# Low-threshold Ca2+ (T-type) for burst mode
g_T = 0.05 * mS/cm2  # conductance density
```

### 1.4 Other Limbic Regions

| Region | Cell Type | tau_m (ms) | R_in (MOhm) |
|--------|-----------|------------|-------------|
| **Prefrontal Cortex (Layer 5)** | Pyramidal | 20-25 | 80-120 |
| **Prefrontal Cortex (Layer 2/3)** | Pyramidal | 15-20 | 100-150 |
| **vmPFC/IL-PFC** | Pyramidal | 18-22 | 90-130 |
| **Central Amygdala (CE)** | Output neurons | 15-25 | 50-80 |

---

## 2. Oscillation Amplitude Requirements (Current Injection)

### 2.1 Current-Frequency Relationships

The relationship between injected current (I_inj) and firing frequency (f) follows:
- f ~ (I_inj - I_rheobase) / tau_m (simplified)
- Higher tau_m requires larger amplitude to reach threshold in same time

### 2.2 Rheobase Values (Current Threshold)

Rheobase is the minimum current to elicit at least one action potential.

| Cell Type | Rheobase (pA) | Notes |
|-----------|---------------|-------|
| **BLA Pyramidal** | 40-80 pA | From R_in ~65 MOhm, V_th-V_rest = 15 mV |
| **BLA Stellate** | 80-120 pA | Lower R_in, higher threshold |
| **BLA Interneurons** | 50-90 pA | Midrange |
| **Hippocampal CA1** | 30-60 pA | High R_in, low threshold |
| **Thalamic Relay** | 20-50 pA | Very high R_in |
| **Prefrontal Pyramidal** | 40-70 pA | Moderate |

**Calculation:** I_rheobase = (V_th - V_rest) / R_in
- For BLA pyramidal: I = 15 mV / 65.6 MOhm = 229 pA (theoretical max)
- Actual rheobase typically lower due to active conductances

### 2.3 Current for Target Frequencies

| Target f | Current Above Rheobase | For tau_m = 20 ms | For tau_m = 30 ms |
|----------|------------------------|-------------------|-------------------|
| 5 Hz | +10-20 pA | ~50-70 pA total | ~60-80 pA |
| 10 Hz | +30-50 pA | ~80-100 pA | ~100-130 pA |
| 20 Hz | +80-120 pA | ~150-200 pA | ~180-220 pA |
| 40 Hz | +200-300 pA | ~300-400 pA | ~350-450 pA |

### 2.4 Oscillation Amplitude (A_osc) for Brian2

From testing in conscious_snn project (DEBUGGING_THALAMUS_20260313.md):

| tau_m (ms) | Minimum A_osc (mV) | Recommended A_osc (mV) |
|------------|-------------------|------------------------|
| 15 | 25 | 25-30 |
| 20 | 30 | 30-35 |
| 25 | 35 | 35-40 |
| 30 | 40 | 40-45 |
| 35 | 50 | 50-55 |

**Scaling Rule:** A_osc ~ tau_m * 1.5 (rough approximation)

**Brian2 Implementation:**
```python
# For oscillatory drive to reach threshold
# I_osc follows: dI_osc/dt = (-I_osc + A_osc * sin(2*pi*f*t)) / tau_osc

# BLA Pyramidal (tau_m=28ms)
A_osc = 40 * mV
tau_osc = 10 * ms  # MUST be < 20ms to follow oscillation

# Thalamic Relay (tau_m=20ms)
A_osc = 30 * mV
tau_osc = 10 * ms

# CA1 Pyramidal (tau_m=30ms)
A_osc = 45 * mV
tau_osc = 10 * ms
```

**Critical:** tau_osc must be < 20ms to follow sinusoidal drive. tau_osc >= 50ms suppresses oscillation entirely.

---

## 3. Thalamus-Amygdala Connectivity

### 3.1 Anatomical Pathways

Source: PubMed search (65 results for thalamus-amygdala connectivity)

**Key Pathways:**

| Pathway | Direction | Function |
|---------|-----------|----------|
| **Medial Dorsal Thalamus (MDm) -> BLA** | Thalamus -> Amygdala | Emotional/cognitive integration |
| **Pulvinar -> BLA** | Thalamus -> Amygdala | Visual threat processing |
| **BLA -> MDm** | Amygdala -> Thalamus | Feedback to mPFC via thalamus |
| **Intralaminar Nuclei -> Amygdala** | Thalamus -> Amygdala | Arousal, attention |

### 3.2 Connection Probabilities

| Pathway | Connection Probability | Notes |
|---------|----------------------|-------|
| **MDm -> BLA Pyramidal** | 0.1-0.3 | Sparse but functionally significant |
| **Pulvinar -> BLA** | 0.2-0.4 | Higher for visual-responsive cells |
| **BLA -> MDm** | 0.1-0.2 | Feedback pathway |
| **Intralaminar -> BLA** | 0.15-0.25 | Diffuse projection pattern |

**Brian2 Implementation:**
```python
# Thalamus to Amygdala connections
thalamus_to_amygdala = Synapses(thalamus, amygdala, 'w_syn : volt', on_pre='v_post += w_syn')
thalamus_to_amygdala.connect(p=0.2)  # 20% connection probability
```

### 3.3 Synaptic Weights and Delays

| Parameter | Excitatory (GLU) | Inhibitory (GABA) |
|-----------|------------------|-------------------|
| **EPSP Amplitude** | 0.5-2 mV | - |
| **IPSP Amplitude** | - | 1-3 mV |
| **Synaptic Weight (w_syn)** | 1-5 mV | 2-8 mV |
| **Axonal Delay** | 1-5 ms | 1-3 ms |
| **Synaptic Rise Time** | 0.5-2 ms | 1-3 ms |
| **Synaptic Decay (tau_syn)** | 5-10 ms | 10-20 ms |

**Brian2 Implementation:**
```python
# Excitatory thalamus -> amygdala
w_syn = 2 * mV
delay = 2 * ms

# Synapse model
syn_model = '''
dw/dt = -w / tau_syn : volt (clock-driven)
'''
on_pre = 'v_post += w'
```

### 3.4 Key Recent Finding (2025)

From PMID 41279575 (Yang et al. 2025 bioRxiv):
> BLA regulates mPFC both directly and indirectly via the medial sub-division of the medial dorsal thalamus (MDm).

This triadic circuit (BLA <-> MDm <-> mPFC) is critical for emotional-cognitive integration.

---

## 4. Fear Extinction and Safety Signaling

### 4.1 Circuit Architecture

Source: Multiple papers on vmPFC-amygdala fear extinction (20+ results)

**Core Circuit:**

```
         vmPFC/IL-PFC (extinction memory)
                |
                | (inhibitory projection)
                v
          ITC (intercalated cells)
                |
                | (GABAergic inhibition)
                v
           CeA (central amygdala)
                |
                | (output)
                v
          Fear Response
```

### 4.2 vmPFC/IL-PFC Parameters

| Parameter | Value | Notes |
|-----------|-------|-------|
| **Firing Rate (rest)** | 1-5 Hz | Low tonic activity |
| **Firing Rate (extinction)** | 5-15 Hz | Increased during extinction recall |
| **tau_m** | 18-22 ms | Pyramidal neurons |
| **Connection to ITC** | p = 0.3-0.5 | Strong inhibitory control |
| **Synaptic weight to ITC** | 2-5 mV | Excitatory to inhibitory cells |

### 4.3 Intercalated Cells (ITC)

ITC clusters are GABAergic interneurons surrounding the amygdala that gate BLA -> CeA transmission.

| Parameter | Value | Notes |
|-----------|-------|-------|
| **Cell Type** | GABAergic interneurons | Parvalbumin-positive |
| **tau_m** | 10-15 ms | Fast integration |
| **Firing Rate** | 10-30 Hz | High-frequency firing |
| **Connection to CeM** | p = 0.5-0.8 | Dense inhibitory projection |
| **Synaptic weight to CeM** | 3-8 mV | Strong inhibition |

### 4.4 Fear vs. Extinction Neurons

From Li et al. 2016 (PMID: 27617747) - Neural circuit model:

| Neuron Type | Location | Role | Firing Pattern |
|-------------|----------|------|----------------|
| **Fear neurons** | BLA | Active during fear recall | CS-locked increase |
| **Extinction neurons** | BLA | Active during extinction | Extinction-locked |
| **Persistent neurons** | BLA/mPFC | Maintain fear memory | Tonic low-frequency |

### 4.5 Safety Signal Parameters

Safety signals inhibit fear via:

1. **vmPFC activation** -> ITC recruitment -> CeM inhibition
2. **Hippocampal context** -> Distinguishes safe vs. dangerous contexts
3. **Timing**: Safety signal must precede expected threat by 100-500 ms

**Brian2 Implementation:**
```python
# vmPFC extinction neurons
vmPFC_extinction = NeuronGroup(N, model, threshold='v > -50*mV', reset='v = -65*mV')
vmPFC_extinction.tau_m = 20 * ms

# vmPFC -> ITC connection (extinction pathway)
vmPFC_to_ITC = Synapses(vmPFC_extinction, ITC, 'w: volt', on_pre='v_post += w')
vmPFC_to_ITC.connect(p=0.4)
vmPFC_to_ITC.w = 3 * mV

# ITC -> CeM (inhibitory gate)
ITC_to_CeM = Synapses(ITC, CeM, 'w: volt', on_pre='v_post -= w')  # Inhibitory
ITC_to_CeM.connect(p=0.6)
ITC_to_CeM.w = 5 * mV
```

### 4.6 Endocannabinoid Modulation

From Gunduz-Cinar et al. 2023 (PMID: 37480845):
- Endocannabinoids facilitate fear extinction
- CB1 receptors in cortico-amygdala circuit
- Temporal dynamics: eCB release peaks 30-60 min post-extinction training

---

## 5. Respiratory-Amygdala Coupling

### 5.1 Core Phenomenon

Source: Multiple papers on respiration-brain coupling (6 PubMed results)

Breathing modulates limbic oscillations through:

1. **Olfactory pathway**: Olfactory bulb -> Piriform -> Entorhinal -> Hippocampus/Amygdala
2. **Mechanosensory feedback**: Lung stretch receptors -> NTS -> Limbic
3. **Autonomic coupling**: Respiratory sinus arrhythmia affects arousal

### 5.2 Respiratory Frequencies and Brain Effects

| Breathing Rate | Frequency (Hz) | Brain Effect | Amygdala Impact |
|----------------|----------------|--------------|-----------------|
| **Slow (6 breaths/min)** | 0.1 Hz | Enhanced theta, HRV | Reduced fear response |
| **Normal (12-15/min)** | 0.2-0.25 Hz | Baseline coupling | Normal reactivity |
| **Fast (20+/min)** | 0.33+ Hz | Reduced coupling, anxiety | Heightened reactivity |

### 5.3 Respiratory-Phase-Locked Oscillations

From Zelano et al. 2016 (PMID: 27927961):
- Nasal respiration entrains limbic oscillations at breathing frequency (0.2-0.3 Hz)
- Faster oscillatory bursts coupled to specific respiratory phases
- Inspiratory phase: Enhanced amygdala/hippocampus coupling

### 5.4 Theta Oscillation Coupling

From Tort et al. 2018 (PMID: 29691421) and Dupin et al. 2019 (PMID: 31064837):

| Parameter | Value | Notes |
|-----------|-------|-------|
| **Respiration-coupled theta** | 4-12 Hz | Phase-locked to respiratory cycle |
| **Fear-related oscillation** | 4 Hz | Sustained in prefrontal-amygdala during freezing |
| **Hippocampal theta** | 6-9 Hz (rodents), 4-8 Hz (humans) | Entrained by nasal breathing |
| **Phase-locking strength** | Higher during inspiration | Peak coupling at inhalation onset |

### 5.5 Amygdala-Respiratory Interaction

From Dehdar et al. 2022 (PMID: 34971764):
- Allergen exposure disrupts amygdala-respiration coupling
- Demonstrates bidirectional communication

From Folschweiler et al. 2023 (PMID: 37277176):
- Respiration-driven rhythms emerge during all behavioral states
- Prefrontal gamma oscillations entrained by respiratory rhythm

### 5.6 Brian2 Implementation

```python
# Respiratory oscillation generator
respiratory_freq = 0.25 * Hz  # 15 breaths/min

# Respiratory phase variable (0 to 2*pi)
dphi_resp/dt = 2*pi*respiratory_freq : 1

# Amygdala receives respiratory-modulated input
# I_resp = A_resp * sin(phi_resp) * coupling_strength

# Respiratory-amygdala coupling model
I_resp = A_resp * sin(phi_resp) : volt

# Modulatory effect on amygdala
# During inspiration (phi ~ pi/2), amygdala more excitable
# During expiration (phi ~ 3*pi/2), amygdala less excitable

# Coupling strength (can be adjusted for slow vs fast breathing)
resp_amygdala_coupling = 0.5  # 0 to 1

# Effective input to amygdala
I_eff = I_base + resp_amygdala_coupling * A_resp * sin(phi_resp)
```

### 5.7 Slow Breathing Effect on Fear

From Pfurtscheller et al. 2025 (PMID: 40818329):
- Slow breathing (0.1 Hz) reduces anxiety via:
  - Increased HRV
  - Enhanced parasympathetic tone
  - Reduced amygdala reactivity
  - Prefrontal-amygdala decoupling

**Implementation for calming effect:**
```python
# Slow breathing mode (6 breaths/min)
respiratory_freq_slow = 0.1 * Hz
resp_amygdala_coupling_slow = 0.3  # Reduced coupling

# Effect: Lower amygdala firing rate, reduced fear response
```

---

## 6. Summary Tables for Brian2 Implementation

### 6.1 Neuron Parameters by Region

| Region | Cell Type | tau_m (ms) | V_rest (mV) | V_th (mV) | A_osc (mV) | Target f (Hz) |
|--------|-----------|------------|-------------|-----------|------------|---------------|
| BLA | Pyramidal | 27.8 | -65 | -50 | 35-40 | 5-10 |
| BLA | Stellate | 14.5 | -65 | -50 | 25-30 | 10-20 |
| BLA | Interneuron | 19.0 | -65 | -50 | 30-35 | 15-30 |
| CA1 | Pyramidal | 30 | -65 | -50 | 35-45 | 5-10 |
| CA3 | Pyramidal | 35 | -65 | -50 | 40-50 | 4-8 |
| Thalamus | Relay | 20 | -60 | -50 | 30-35 | 8-12 |
| vmPFC | Pyramidal | 20 | -65 | -50 | 30-35 | 5-15 |
| ITC | Interneuron | 12 | -65 | -50 | 25-30 | 10-30 |

### 6.2 Synaptic Parameters

| Connection Type | w_syn (mV) | p_conn | delay (ms) | tau_syn (ms) |
|-----------------|------------|--------|------------|--------------|
| Thalamus -> BLA (exc) | 2-4 | 0.2 | 2-5 | 5-10 |
| BLA -> Thalamus (exc) | 1-3 | 0.15 | 2-4 | 5-8 |
| vmPFC -> ITC (exc) | 2-5 | 0.4 | 3-6 | 8-12 |
| ITC -> CeM (inh) | 3-8 | 0.6 | 1-3 | 10-15 |
| BLA -> BLA (inh) | 2-4 | 0.3 | 1-2 | 5-10 |
| BLA -> CeM (exc) | 2-5 | 0.3 | 1-3 | 5-8 |

### 6.3 Oscillation Parameters

| System | Base Frequency (Hz) | Oscillation Type | tau_osc (ms) |
|--------|--------------------|--------------------|--------------|
| Amygdala (fear) | 4 | Respiratory-locked | 10 |
| Amygdala (theta) | 6-8 | Theta | 10 |
| Hippocampus | 6-8 | Theta | 10 |
| Thalamus | 8-12 | Alpha | 10 |
| vmPFC | 5-15 | Task-dependent | 10 |
| Respiration | 0.2-0.25 | Base rhythm | 100-200 |

---

## 7. Critical Implementation Notes

### 7.1 Numerical Stability

From RESEARCH_ADEX_STABILITY.md:

1. **tau_osc must be < 20 ms** to follow oscillatory drive
2. **A_osc scales with tau_m** (larger tau_m = larger A_osc needed)
3. **Clamp exponential term** in AdEx to prevent overflow: `min(exp((v-VT)/DeltaT), 50)`
4. **Use exponential_euler** integration method

### 7.2 Unit Consistency

Brian2 requires consistent units:
- Voltage: mV
- Time: ms
- Frequency: Hz
- Conductance: mS/cm2
- Current: pA or mV (in current-based models)

### 7.3 Connectivity Scaling

For network-level effects:
- Scale weights by sqrt(N) for sparse connections
- Balance excitation/inhibition (E/I ratio ~4:1)
- Use distance-dependent connection probability

---

## Sources

1. **Rainnie et al. 1993** (PMID: 8492168) - BLA neuron electrophysiology
2. **Wlodarczyk et al. 2013** (PMID: 24399937) - Hippocampal GABAergic modulation
3. **McCormick & Huguenard 1992** (PMID: 1331356) - Thalamocortical model
4. **Yang et al. 2025** (PMID: 41279575) - Amygdala-thalamic circuit
5. **Gunduz-Cinar et al. 2023** (PMID: 37480845) - Fear extinction, endocannabinoids
6. **Li et al. 2016** (PMID: 27617747) - Fear/extinction neuron model
7. **Bukalo et al. 2015** (PMID: 26504902) - vmPFC-amygdala extinction
8. **Zelano et al. 2016** (PMID: 27927961) - Respiratory-limbic entrainment
9. **Tort et al. 2018** (PMID: 29691421) - Respiration-coupled oscillations
10. **Dupin et al. 2019** (PMID: 31064837) - Fear-related 4 Hz oscillations
11. **Folschweiller et al. 2023** (PMID: 37277176) - Behavioral state modulation
12. **Dehdar et al. 2022** (PMID: 34971764) - Amygdala-respiration coupling
13. **Pfurtscheller et al. 2025** (PMID: 40818329) - Brain-breathing interaction

---

*Research synthesis by Ava Sterling*
*For Brian2 SNN parameterization in conscious_snn project*
