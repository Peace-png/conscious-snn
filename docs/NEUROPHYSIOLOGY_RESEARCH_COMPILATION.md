# Neurophysiology Research Compilation
## For Brian2 SNN Consciousness Simulation

**Compiled:** 2026-03-13
**Purpose:** Complete quantitative parameter reference for spiking neural network modeling

---

# PART 1: MEMBRANE TIME CONSTANTS (tau_m)

## 1.1 Basolateral Amygdala (BLA) Neurons

Source: Rainnie et al. 1993 (PMID: 8492168) - Intracellular recordings from morphologically identified BLA neurons

| Cell Type | tau_m (ms) | R_in (MOhm) | AP Half-width (ms) | Firing Pattern | 1st ISI (ms) |
|-----------|------------|-------------|-------------------|----------------|--------------|
| **Class I Pyramidal** | 27.8 | 65.6 | 0.85 | Regular | 91 |
| **Class I Stellate** | 14.5 | 40.1 | 0.7 | Burst | 6.0 |
| **Class II Interneurons** | 19.0 | 58.0 | 0.77 | Burst (no accommodation) | 6.0 |

## 1.2 Hippocampal Neurons

Source: Wlodarczyk et al. 2013 (PMID: 24399937)

| Cell Type | tau_m (ms) | Notes |
|-----------|------------|-------|
| **CA1 Pyramidal** | 25-35 | Large tau due to dendritic structure |
| **Dentate Granule** | 15-25 | Smaller than CA1 |
| **CA3 Pyramidal** | 30-40 | Burst-firing capability |

## 1.3 Thalamocortical Relay Neurons

Source: McCormick & Huguenard 1992 (PMID: 1331356)

| Parameter | Value | Notes |
|-----------|-------|-------|
| **tau_m (rest)** | 20-30 ms | Determined by leak conductances |
| **R_in** | 100-200 MOhm | High input resistance |
| **Ionic currents** | I_Na, I_Nap, I_T, I_L, I_C, I_A, I_K2, I_h | T-type Ca2+ critical for burst mode |

## 1.4 Other Limbic Regions

| Region | Cell Type | tau_m (ms) | R_in (MOhm) |
|--------|-----------|------------|-------------|
| **Prefrontal Cortex (Layer 5)** | Pyramidal | 20-25 | 80-120 |
| **Prefrontal Cortex (Layer 2/3)** | Pyramidal | 15-20 | 100-150 |
| **vmPFC/IL-PFC** | Pyramidal | 18-22 | 90-130 |
| **Central Amygdala (CE)** | Output neurons | 15-25 | 50-80 |

## 1.5 Intercalated Cells (ITC)

| Parameter | Value | Notes |
|-----------|-------|-------|
| **Cell Type** | GABAergic interneurons | Parvalbumin-positive |
| **tau_m** | 10-15 ms | Fast integration |
| **Firing Rate** | 10-30 Hz | High-frequency firing |

---

# PART 2: OSCILLATION AMPLITUDE REQUIREMENTS

## 2.1 The Critical tau_osc Constraint

**From testing (DEBUGGING_THALAMUS_20260313.md):**

| tau_osc (ms) | Result | Reason |
|--------------|--------|--------|
| 5 | 10 Hz ✅ | Fast enough to follow drive |
| 10 | 10 Hz ✅ | Fast enough to follow drive |
| 20 | 0 Hz ❌ | Too slow - smoothes oscillation |
| 50 | 0 Hz ❌ | Completely suppresses oscillation |

**CRITICAL: tau_osc MUST be < 20ms, preferably 10ms**

## 2.2 A_osc Scaling with tau_m

| tau_m (ms) | Minimum A_osc (mV) | Recommended A_osc (mV) |
|------------|-------------------|------------------------|
| 15 | 25 | 25-30 |
| 20 | 30 | 30-35 |
| 25 | 35 | 35-40 |
| 30 | 40 | 40-45 |
| 35 | 50 | 50-55 |

**Scaling Rule:** A_osc ~ tau_m * 1.5

## 2.3 Rheobase Values (Current Threshold)

| Cell Type | Rheobase (pA) | Notes |
|-----------|---------------|-------|
| **BLA Pyramidal** | 40-80 pA | From R_in ~65 MOhm, V_th-V_rest = 15 mV |
| **BLA Stellate** | 80-120 pA | Lower R_in, higher threshold |
| **BLA Interneurons** | 50-90 pA | Midrange |
| **Hippocampal CA1** | 30-60 pA | High R_in, low threshold |
| **Thalamic Relay** | 20-50 pA | Very high R_in |
| **Prefrontal Pyramidal** | 40-70 pA | Moderate |

---

# PART 3: EMOTIONAL STATE OSCILLATION SIGNATURES

## 3.1 Fear State

| Region | Primary Oscillation | Hz Range | Secondary | Amplitude Change |
|--------|---------------------|----------|-----------|------------------|
| Amygdala (BLA) | Theta | 4-8 Hz | Gamma 40-80 Hz | +200-400% theta |
| Amygdala (CeA) | Theta | 3-6 Hz | Beta 13-30 Hz | Synchronizes with hippocampus |
| Hippocampus | Theta | 4-12 Hz | Gamma 30-100 Hz | Phase-locked to amygdala |
| mPFC | Theta | 4-8 Hz | Gamma 30-50 Hz | Reduced coupling in anxiety |

**Fear theta-gamma coupling:**
- Phase: 270-315 degrees
- Modulation Index: 0.015-0.030

## 3.2 Rage/Anger State

| Region | Primary Oscillation | Hz Range | Secondary | Notes |
|--------|---------------------|----------|-----------|-------|
| Amygdala | Beta | 13-30 Hz | Gamma 30-50 Hz | Correlates with anger intensity |
| Hypothalamus | Theta | 4-7 Hz | Delta 1-4 Hz | Defensive rage circuit |
| PAG | Theta | 4-8 Hz | Gamma 40-60 Hz | Fight-or-flight |
| ACC | Theta | 4-7 Hz | Beta 13-20 Hz | Conflict monitoring |
| dlPFC | Beta | 15-25 Hz | Gamma 30-45 Hz | Cognitive control |

**Rage onset:** Rapid hypothalamus-amygdala-PAG synchronization (50-100ms)

## 3.3 Grief/Sadness State

| Region | Primary Oscillation | Hz Range | Secondary | Notes |
|--------|---------------------|----------|-----------|-------|
| Amygdala | Alpha | 8-12 Hz | Theta 4-7 Hz | Hypoactivation |
| sgACC | Theta | 4-8 Hz | Alpha 8-12 Hz | Hyperactivity in depression |
| vmPFC | Theta | 5-8 Hz | Delta 1-4 Hz | Rumination |
| Insula | Alpha | 8-13 Hz | Beta 13-20 Hz | Reduced interoception |
| Nucleus Accumbens | Delta | 1-4 Hz | Theta 4-8 Hz | Reward deficit |

**Depression marker:** sgACC theta overactivity (factor 1.5-2x baseline)

## 3.4 Joy/Euphoria State

| Region | Primary Oscillation | Hz Range | Secondary | Notes |
|--------|---------------------|----------|-----------|-------|
| Nucleus Accumbens | Gamma | 40-80 Hz | Beta 20-30 Hz | Dopamine release |
| VTA | Theta | 4-8 Hz | Gamma 30-50 Hz | Dopaminergic burst |
| vmPFC/OFC | Gamma | 30-50 Hz | Theta 4-8 Hz | Positive valuation |
| Amygdala | Gamma | 30-60 Hz | Theta 6-9 Hz | Reactive to positive |
| Hippocampus | Theta | 6-10 Hz | Gamma 40-100 Hz | Enhanced coupling |

**Joy theta-gamma coupling:**
- Phase: 90-180 degrees
- Modulation Index: 0.020-0.040
- NAc gamma: +150-300% from baseline

---

# PART 4: CROSS-REGION CONNECTIVITY

## 4.1 Thalamus-Amygdala Connectivity

| Pathway | Direction | Connection Probability | w_syn (mV) |
|---------|-----------|----------------------|------------|
| MDm -> BLA | Thalamus -> Amygdala | 0.1-0.3 | 2-4 |
| Pulvinar -> BLA | Thalamus -> Amygdala | 0.2-0.4 | 2-4 |
| BLA -> MDm | Amygdala -> Thalamus | 0.1-0.2 | 1-3 |
| Intralaminar -> BLA | Thalamus -> Amygdala | 0.15-0.25 | 2-3 |

## 4.2 Fear Extinction Circuit

```
vmPFC/IL-PFC (extinction memory)
       |
       | (inhibitory projection, p=0.3-0.5, w=2-5mV)
       v
   ITC (intercalated cells)
       |
       | (GABAergic, p=0.5-0.8, w=3-8mV)
       v
    CeA (central amygdala)
       |
       v
  Fear Response
```

## 4.3 Synaptic Parameters Summary

| Connection Type | w_syn (mV) | p_conn | delay (ms) | tau_syn (ms) |
|-----------------|------------|--------|------------|--------------|
| Thalamus -> BLA (exc) | 2-4 | 0.2 | 2-5 | 5-10 |
| BLA -> Thalamus (exc) | 1-3 | 0.15 | 2-4 | 5-8 |
| vmPFC -> ITC (exc) | 2-5 | 0.4 | 3-6 | 8-12 |
| ITC -> CeM (inh) | 3-8 | 0.6 | 1-3 | 10-15 |
| BLA -> BLA (inh) | 2-4 | 0.3 | 1-2 | 5-10 |
| BLA -> CeM (exc) | 2-5 | 0.3 | 1-3 | 5-8 |

---

# PART 5: HEART-BRAIN COUPLING

## 5.1 Cardiac Oscillator Parameters

| Parameter | Value | Notes |
|-----------|-------|-------|
| Base frequency | 1.0-1.25 Hz | 60-75 bpm |
| HRV modulation | 0.1-0.4 Hz | Oscillation amplitude |
| Respiratory coupling | 0.2-0.3 Hz | Respiratory sinus arrhythmia |
| Baroreceptor timing | 200-300ms | After cardiac R-wave |

## 5.2 Cardiac-Amygdala Coupling

| State | Cardiac Pattern | Amygdala Activity | Coupling |
|-------|-----------------|-------------------|----------|
| Fear | Increased HR, decreased HRV | Hyperactive BLA | Excitatory during systole |
| Anger | Increased HR, reduced HRV | Moderate-high | Sympathetic dominance |
| Grief | Variable HR, reduced HRV | Variable | Dissociation |
| Joy | Increased HRV, moderate HR | Normalized | Vagal flexibility |

**Fear processing enhanced during systole vs diastole (effect size d=0.6)**

## 5.3 Cardiac-Prefrontal Coupling

- vmPFC activity correlates with HRV: r = 0.4-0.6
- Prefrontal inhibition of amygdala: 50-100ms delay
- Heart-brain feedback loop: ~500-1000ms (one cardiac cycle)

---

# PART 6: RESPIRATORY-AMYGDALA COUPLING

## 6.1 Breathing Rate Effects

| Breathing Rate | Frequency (Hz) | Amygdala Effect |
|----------------|----------------|-----------------|
| Slow (6 breaths/min) | 0.1 Hz | Reduced reactivity, enhanced theta, HRV |
| Normal (12-15/min) | 0.2-0.25 Hz | Baseline coupling |
| Fast (20+/min) | 0.33+ Hz | Heightened reactivity, anxiety |

## 6.2 Respiratory-Phase-Locked Oscillations

| Parameter | Value | Notes |
|-----------|-------|-------|
| Respiration-coupled theta | 4-12 Hz | Phase-locked to respiratory cycle |
| Fear-related oscillation | 4 Hz | Sustained during freezing |
| Hippocampal theta | 6-9 Hz (rodents), 4-8 Hz (humans) | Entrained by nasal breathing |
| Phase-locking strength | Higher during inspiration | Peak at inhalation onset |

---

# PART 7: CROSS-FREQUENCY COUPLING

## 7.1 Theta-Gamma Coupling by Emotion

| State | Region | Theta Phase | Gamma Freq | MI |
|-------|--------|-------------|------------|-----|
| Fear (encoding) | Amygdala-Hippocampus | 270-315° | 60-100 Hz | 0.015-0.030 |
| Fear (retrieval) | Amygdala-mPFC | 180-270° | 40-60 Hz | 0.010-0.020 |
| Anxiety (chronic) | mPFC | Variable | 30-50 Hz | 0.005-0.010 (reduced) |
| Joy | NAc | 90-180° | 50-80 Hz | 0.020-0.040 |
| Depression | sgACC | 0-90° | 30-50 Hz | 0.008-0.015 |

## 7.2 Alpha-Gamma Coupling

| State | Region | Relationship |
|-------|--------|--------------|
| Fear | Visual cortex | Inverse (high alpha = low gamma) |
| Anger | Amygdala | Reduced alpha, disinhibited gamma |
| Sadness | Frontal | Left alpha increases, gamma decreases |
| Joy | Occipital-parietal | Reduced alpha, enhanced gamma |

---

# PART 8: PHARMACOLOGICAL MODULATION

## 8.1 GABAergic Effects

| Drug Class | Oscillation Effect | Hz Change |
|------------|-------------------|-----------|
| Benzodiazepines | Increased gamma coherence | 30-50 Hz: +20-40% |
| Benzodiazepines | Reduced theta | 4-8 Hz: -30-50% |
| Barbiturates | Increased beta | 15-25 Hz: +100-200% |
| Alcohol | Increased delta/theta | 4-8 Hz: +50% |

## 8.2 Glutamatergic Effects

| Drug | Effect | Hz Change |
|------|--------|-----------|
| Ketamine | Increased gamma (transient) | 30-80 Hz: +100-300% |
| Memantine | Reduced theta | 4-8 Hz: -20-30% |
| D-Cycloserine | Enhanced fear extinction | NMDA-dependent |

## 8.3 Noradrenergic Effects

| State | LC Firing Rate | Oscillation Effect |
|-------|---------------|-------------------|
| Sleep | 0-1 Hz | Dominant delta (1-4 Hz) |
| Rest | 2-4 Hz | Mixed alpha/beta |
| Alert | 6-10 Hz | Increased beta (15-25 Hz) |
| Stress | 10-20 Hz | Gamma enhancement (40-80 Hz) |

## 8.4 Dopaminergic Effects

| Drug | Region | Hz Change |
|------|--------|-----------|
| L-DOPA | NAc | 40-80 Hz: +50-100% |
| Antipsychotics | NAc, Striatum | 40-60 Hz: -30% |
| Cocaine (acute) | NAc | 40-80 Hz: +200% |

---

# PART 9: BRIAN2 IMPLEMENTATION REFERENCE

## 9.1 Neuron Parameters Summary

| Region | Cell Type | tau_m | V_rest | V_th | A_osc | f_target | tau_osc |
|--------|-----------|-------|--------|------|-------|----------|---------|
| BLA | Pyramidal | 27.8ms | -65mV | -50mV | 40mV | 5-10Hz | 10ms |
| BLA | Stellate | 14.5ms | -65mV | -50mV | 25mV | 10-20Hz | 10ms |
| BLA | Interneuron | 19.0ms | -65mV | -50mV | 30mV | 15-30Hz | 10ms |
| CA1 | Pyramidal | 30ms | -65mV | -50mV | 45mV | 5-10Hz | 10ms |
| Thalamus | Relay | 20ms | -60mV | -50mV | 30mV | 8-12Hz | 10ms |
| vmPFC | Pyramidal | 20ms | -65mV | -50mV | 35mV | 5-15Hz | 10ms |
| ITC | Interneuron | 12ms | -65mV | -50mV | 25mV | 10-30Hz | 10ms |

## 9.2 Critical Rules

1. **tau_osc MUST be < 20ms** - preferably 10ms
2. **A_osc scales with tau_m** - A_osc ~ tau_m * 1.5
3. **Clip exponential in AdEx** - min(exp((v-VT)/DeltaT), 50)
4. **Use exponential_euler** - for numerical stability
5. **E/I ratio ~4:1** - for network balance
6. **Distance-dependent p_conn** - for realistic connectivity

## 9.3 Code Template

```python
# BLA Pyramidal neuron
bla_pyramidal = NeuronGroup(
    N,
    model='''
    dv/dt = (v_rest - v + I_osc + I_syn) / tau_m : volt (unless refractory)
    dI_osc/dt = (-I_osc + A_osc * sin(2*pi*f_osc*t)) / tau_osc : volt
    dI_syn/dt = -I_syn / tau_syn : volt
    tau_m : second
    tau_osc : second
    tau_syn : second
    f_osc : Hz
    A_osc : volt
    v_rest : volt
    v_thresh : volt
    ''',
    threshold='v > v_thresh',
    reset='v = v_rest',
    refractory=5*ms,
    method='exponential_euler'
)

bla_pyramidal.tau_m = 27.8 * ms
bla_pyramidal.tau_osc = 10 * ms  # CRITICAL: must be < 20ms
bla_pyramidal.tau_syn = 10 * ms
bla_pyramidal.f_osc = 6 * Hz  # Theta
bla_pyramidal.A_osc = 40 * mV  # Scaled for tau_m=28ms
bla_pyramidal.v_rest = -65 * mV
bla_pyramidal.v_thresh = -50 * mV
bla_pyramidal.v = -65 * mV
```

---

# SOURCES

1. Rainnie et al. 1993 (PMID: 8492168) - BLA electrophysiology
2. Wlodarczyk et al. 2013 (PMID: 24399937) - Hippocampal GABA
3. McCormick & Huguenard 1992 (PMID: 1331356) - Thalamocortical model
4. Yang et al. 2025 (PMID: 41279575) - Amygdala-thalamic circuit
5. Gunduz-Cinar et al. 2023 (PMID: 37480845) - Fear extinction
6. Li et al. 2016 (PMID: 27617747) - Fear/extinction neuron model
7. Bukalo et al. 2015 (PMID: 26504902) - vmPFC-amygdala extinction
8. Zelano et al. 2016 (PMID: 27927961) - Respiratory-limbic entrainment
9. Tort et al. 2018 (PMID: 29691421) - Respiration-coupled oscillations
10. Dupin et al. 2019 (PMID: 31064837) - Fear-related 4 Hz oscillations
11. Folschweiler et al. 2023 (PMID: 37277176) - Behavioral state modulation
12. Dehdar et al. 2022 (PMID: 34971764) - Amygdala-respiration coupling
13. Pfurtscheller et al. 2025 (PMID: 40818329) - Brain-breathing interaction
14. Lesting et al. 2011 (DOI: 10.1371/journal.pone.0021714) - CA1-LA-mPFC theta coupling

---

*Compiled for Conscious SNN Project - 2026-03-13*
