# Neuromodulatory Systems Research
## Comprehensive Parameter Guide for Brian2 SNN Implementation

**Compiled:** 2026-03-13
**Purpose:** Complete quantitative parameters for neuromodulatory tone in consciousness simulation
**Focus:** LC-NE, Raphe-5HT, VTA/SNc-DA, Basal Forebrain-ACh systems

---

# PART 1: LOCUS COERULEUS NOREPINEPHRINE (LC-NE)

## 1.1 LC Neuron Electrophysiology

| Parameter | Value | Unit | Source |
|-----------|-------|------|--------|
| **tau_m (rest)** | 15-30 | ms | Aston-Jones & Cohen 2005 |
| **R_in** | 150-300 | MOhm | Higher than typical neurons |
| **C_m** | 30-50 | pF | Small soma size |
| **V_rest** | -55 to -50 | mV | Relatively depolarized |
| **V_th** | -45 to -40 | mV | Low threshold |
| **V_reset** | -60 to -55 | mV | |
| **AP width** | 0.8-1.5 | ms | Broad spikes |
| **AHP duration** | 50-200 | ms | Prominent afterhyperpolarization |

## 1.2 LC Firing Patterns by Arousal State

| State | Firing Rate (Hz) | Pattern | NE Release | Notes |
|-------|------------------|---------|------------|-------|
| **Deep Sleep (SWS)** | 0-0.5 | Tonic, very slow | Minimal | Delta-dominated |
| **REM Sleep** | 0.5-2 | Variable | Low | Phasic bursts possible |
| **Drowsy** | 1-3 | Tonic | Low | Transition state |
| **Quiet Wake** | 2-4 | Regular tonic | Baseline | Resting alertness |
| **Active Wake** | 4-8 | Tonic + phasic | Moderate | Engaged attention |
| **High Alert** | 8-15 | Phasic bursts | High | Stress/vigilance |
| **Panic/Stress** | 15-25 | Sustained high | Very High | Sympathetic drive |

## 1.3 LC Phasic vs Tonic Modes

**Phasic Mode (Optimal Performance):**
- Brief bursts (50-200 ms) at 10-30 Hz
- Triggered by task-relevant stimuli
- Inter-burst interval: 300-1000 ms
- Improves signal-to-noise ratio
- Associated with good performance

**Tonic Mode (Vigilance):**
- Sustained 2-8 Hz
- Background arousal level
- Higher variability
- Associated with scanning behavior

**Model:** `LC_rate(t) = tonic_baseline + phasic_amplitude * exp(-t/tau_phasic) * stimulus_triggered`

## 1.4 LC Connectivity

| Target | Projection Type | Connection Probability | Functional Effect |
|--------|-----------------|----------------------|-------------------|
| **Prefrontal Cortex** | Diffuse, NE release | 0.05-0.15 | Enhances gain, working memory |
| **Sensory Cortex** | Diffuse | 0.10-0.20 | Increases SNR |
| **Amygdala (BLA)** | Moderate | 0.05-0.10 | Facilitates fear encoding |
| **Hippocampus** | Moderate | 0.05-0.10 | Enhances plasticity |
| **Thalamus** | Dense | 0.15-0.25 | Modulates relay |
| **Brainstem** | Local | 0.20-0.40 | Autonomic integration |

## 1.5 NE Effects on Target Oscillations

| Target System | Baseline Oscillation | NE Effect | Hz Change |
|---------------|---------------------|-----------|-----------|
| **PFC** | Gamma 30-50 Hz | Enhanced gamma power | +20-50% |
| **Sensory Cortex** | Alpha 8-12 Hz | Alpha suppression | -30-50% |
| **Amygdala** | Theta 4-8 Hz | Enhanced theta | +30-60% |
| **Hippocampus** | Theta 6-10 Hz | Enhanced theta, improved LTP | +20-40% |
| **Thalamus** | Alpha 8-12 Hz | Shift to beta/gamma | 8-12 -> 15-25 Hz |

---

# PART 2: RAPHE NUCLEI SEROTONIN (5-HT)

## 2.1 Raphe Neuron Electrophysiology

| Parameter | Dorsal Raphe (DRN) | Median Raphe (MRN) | Unit |
|-----------|-------------------|-------------------|------|
| **tau_m** | 25-45 | 20-35 | ms |
| **R_in** | 200-500 | 150-400 | MOhm |
| **V_rest** | -60 to -55 | -58 to -53 | mV |
| **V_th** | -50 to -45 | -48 to -43 | mV |
| **AP width** | 1.0-2.0 | 1.0-1.8 | ms |
| **AHP** | Prominent, slow | Moderate | |

## 2.2 Raphe Firing Patterns by Behavioral State

| State | DRN Firing (Hz) | MRN Firing (Hz) | Pattern | 5-HT Release |
|-------|-----------------|-----------------|---------|--------------|
| **Active Sleep (REM)** | 0-1 | 0-1 | Silent | Minimal |
| **Slow Wave Sleep** | 0.5-2 | 0.5-1.5 | Slow tonic | Low |
| **Quiet Wake** | 1-3 | 0.5-2 | Regular pacemaker | Baseline |
| **Active Wake** | 2-5 | 1-3 | Regular + bursts | Moderate |
| **Stress** | 3-8 | 2-5 | Irregular | High |
| **Rhythmic Movement** | 2-4 | 1-3 | Phase-locked | Moderate |

## 2.3 Serotonin Pacemaker Properties

Serotonin neurons show intrinsic pacemaker activity:
- **Pacemaker frequency:** 0.5-3 Hz (in vitro)
- **Mechanism:** Ca2+-dependent slow afterhyperpolarization (sAHP)
- **5-HT1A autoreceptor:** Hyperpolarizes, reduces firing (-30 to -50%)
- **Time constant of sAHP:** 1-5 seconds

## 2.4 Raphe Connectivity

| Target | Projection Type | Connection Probability | Effect |
|--------|-----------------|----------------------|--------|
| **Prefrontal Cortex** | Diffuse | 0.05-0.10 | Mood, impulse control |
| **Amygdala** | Moderate | 0.08-0.15 | Anxiety modulation |
| **Hippocampus** | Dense (MRN) | 0.15-0.25 | Memory, neurogenesis |
| **Hypothalamus** | Dense | 0.10-0.20 | Circadian, feeding |
| **Striatum** | Moderate | 0.05-0.12 | Motor, reward |
| **Brainstem** | Local | 0.20-0.40 | Autonomic |

## 2.5 5-HT Effects on Target Oscillations

| Target System | Baseline | 5-HT Effect | Hz/Power Change |
|---------------|----------|-------------|-----------------|
| **PFC** | Theta 4-8 Hz | Reduced theta power | -20-40% |
| **Amygdala** | Theta 4-8 Hz | Reduced anxiety theta | -25-50% |
| **Hippocampus** | Theta 6-10 Hz | Enhanced theta | +10-25% |
| **Sensory Cortex** | Alpha 8-12 Hz | Modest alpha increase | +10-20% |

---

# PART 3: VTA/SNc DOPAMINE (DA)

## 3.1 Dopamine Neuron Electrophysiology

| Parameter | VTA | SNc | Unit |
|-----------|-----|-----|------|
| **tau_m** | 15-35 | 20-40 | ms |
| **R_in** | 100-300 | 150-350 | MOhm |
| **V_rest** | -60 to -55 | -58 to -53 | mV |
| **V_th** | -50 to -45 | -48 to -43 | mV |
| **AP width** | 1.5-2.5 | 1.8-3.0 | ms (broad) |
| **Pacemaker rate** | 2-6 | 1-5 | Hz |
| **Burst rate** | 15-25 | 10-20 | Hz |

## 3.2 DA Neuron Firing Modes

| Mode | Frequency | Pattern | Trigger | DA Release |
|------|-----------|---------|---------|------------|
| **Pacemaker** | 2-6 Hz | Regular tonic | Baseline | Tonic DA |
| **Burst** | 15-25 Hz | 3-8 spikes | Reward prediction | Phasic DA surge |
| **Inhibited** | 0-1 Hz | Suppressed | Punishment/omission | DA dip |

## 3.3 DA Burst Dynamics

**Burst Parameters:**
- **Spikes per burst:** 3-8
- **Intra-burst ISI:** 15-30 ms
- **Inter-burst interval:** 200-1000 ms
- **Burst duration:** 50-200 ms
- **Trigger latency to reward:** 50-150 ms

**Model:** `DA_burst(t) = sum(spike_i * exp(-(t-t_i)/tau_DA))` where `tau_DA = 100-200 ms`

## 3.4 VTA/SNc Connectivity

| Target | Projection Type | Connection Probability | Function |
|--------|-----------------|----------------------|----------|
| **Nucleus Accumbens** | Dense (mesolimbic) | 0.20-0.40 | Reward, motivation |
| **Prefrontal Cortex** | Moderate (mesocortical) | 0.05-0.15 | Working memory, planning |
| **Striatum (dorsal)** | Dense (nigrostriatal) | 0.15-0.30 | Motor control |
| **Amygdala** | Moderate | 0.08-0.15 | Reward-punishment |
| **Hippocampus** | Sparse | 0.02-0.08 | Memory consolidation |

## 3.5 DA Effects on Target Oscillations

| Target System | Baseline | DA Effect | Hz/Power Change |
|---------------|----------|-----------|-----------------|
| **NAc** | Gamma 40-80 Hz | Enhanced gamma | +50-200% |
| **PFC** | Gamma 30-50 Hz | Optimal gamma at moderate DA | Inverted-U |
| **Striatum** | Beta 13-30 Hz | Reduced beta (movement) | -30-50% |
| **Amygdala** | Theta 4-8 Hz | Modulated by valence | Variable |

---

# PART 4: BASAL FOREBRAIN ACETYLCHOLINE (ACh)

## 4.1 BF Cholinergic Neuron Electrophysiology

| Parameter | Value | Unit | Notes |
|-----------|-------|------|-------|
| **tau_m** | 15-40 | ms | Cell-type dependent |
| **R_in** | 100-400 | MOhm | Large range |
| **V_rest** | -60 to -55 | mV | |
| **V_th** | -50 to -45 | mV | |
| **AP width** | 0.8-1.5 | ms | |
| **Firing range** | 1-50 | Hz | Wide dynamic range |

## 4.2 BF ACh Firing by Arousal State

| State | Firing Rate (Hz) | Pattern | ACh Release | Notes |
|-------|------------------|---------|-------------|-------|
| **Deep Sleep (SWS)** | 0-1 | Minimal | Very Low | Cortical slow waves |
| **REM Sleep** | 10-30 | Tonic | High | EEG activation |
| **Quiet Wake** | 5-15 | Tonic | Moderate | Baseline attention |
| **Active Attention** | 15-40 | Tonic + phasic | High | Top-down focus |
| **Learning** | 20-50 | Phasic bursts | Very High | Plasticity window |

## 4.3 BF Subregions and Projections

| BF Subregion | Primary Target | Projection Density | Function |
|--------------|----------------|-------------------|----------|
| **Nucleus Basalis** | Neocortex | Dense, diffuse | Cortical arousal |
| **Medial Septum** | Hippocampus | Dense | Theta generation |
| **Vertical Diagonal Band** | Hippocampus, Olfactory | Moderate | Memory, olfaction |
| **Horizontal Diagonal Band** | Olfactory, Insula | Moderate | Sensory |

## 4.4 BF ACh Connectivity

| Target | Connection Type | Effect on Target |
|--------|-----------------|------------------|
| **Neocortex (all layers)** | Diffuse volume transmission | Depolarizes, enhances SNR |
| **Hippocampus** | Septal-hippocampal pathway | Drives theta rhythm |
| **Amygdala** | Moderate | Enhances plasticity |
| **Thalamus** | Sparse | Arousal relay |

## 4.5 ACh Effects on Target Oscillations

| Target System | Baseline | ACh Effect | Hz/Power Change |
|---------------|----------|------------|-----------------|
| **Neocortex** | Alpha 8-12 Hz | Alpha suppression, gamma increase | -50% alpha, +50% gamma |
| **Hippocampus** | Theta 4-8 Hz | Essential for theta | +50-100% theta power |
| **Sensory Cortex** | Alpha 8-12 Hz | Reduced alpha (attention) | -40-60% |

---

# PART 5: AROUSAL STATE MATRIX

## 5.1 Complete Neuromodulator Profile by State

| State | LC-NE | 5-HT | DA | ACh | EEG Dominant |
|-------|-------|------|----|----|--------------|
| **Deep NREM** | 0-0.5 Hz | 0.5-2 Hz | 0.5-1 Hz | 0-1 Hz | Delta 1-4 Hz |
| **Light NREM** | 0.5-1 Hz | 1-2 Hz | 1-2 Hz | 1-5 Hz | Theta/Spindles |
| **REM Sleep** | 0.5-2 Hz | 0-1 Hz | 2-5 Hz | 15-30 Hz | Theta 4-8 Hz |
| **Drowsy** | 1-2 Hz | 1-3 Hz | 1-3 Hz | 3-8 Hz | Alpha 8-10 Hz |
| **Quiet Wake** | 2-4 Hz | 2-4 Hz | 2-5 Hz | 5-15 Hz | Alpha/Beta |
| **Active Attention** | 4-8 Hz | 2-5 Hz | 5-10 Hz | 15-30 Hz | Beta/Gamma |
| **Stress/Alert** | 10-20 Hz | 4-8 Hz | 5-15 Hz | 20-40 Hz | Beta/Gamma |
| **Reward/Joy** | 4-8 Hz | 3-6 Hz | 15-25 Hz (burst) | 15-30 Hz | Gamma |

## 5.2 State Transition Dynamics

| Transition | Timecourse | Key Neuromodulator | Latency |
|------------|------------|-------------------|---------|
| **Sleep -> Wake** | 1-5 seconds | LC-NE surge | ~500 ms |
| **Wake -> Sleep** | 5-30 minutes | Global reduction | Gradual |
| **Rest -> Attention** | 100-500 ms | ACh + LC-NE | 100-200 ms |
| **Neutral -> Reward** | 50-200 ms | DA burst | 50-150 ms |
| **Safe -> Threat** | 50-200 ms | LC-NE surge | 50-100 ms |

---

# PART 6: NEUROMODULATION EFFECTS ON 8 SYSTEMS

## 6.1 System-Specific Neuromodulatory Effects

### Brainstem (0.5-2 Hz)
| Neuromodulator | Effect | Parameter Change |
|----------------|--------|------------------|
| **NE** | Increases arousal drive | +20-50% firing rate |
| **5-HT** | Mood modulates autonomic | Variable |
| **ACh** | Minimal direct effect | - |

### Cardiac (0.1-0.4 Hz HRV, 1 Hz base)
| Neuromodulator | Effect | Parameter Change |
|----------------|--------|------------------|
| **NE** | Increases HR, decreases HRV | +10-30% HR, -30% HRV |
| **5-HT** | Variable, context-dependent | - |
| **ACh** | Vagal - decreases HR | -10-20% HR, +HRV |

### Respiratory (0.2-0.3 Hz)
| Neuromodulator | Effect | Parameter Change |
|----------------|--------|------------------|
| **NE** | Increases respiratory rate | +10-30% rate |
| **5-HT** | Modulates rhythm | Phase-dependent |
| **ACh** | Minimal direct | - |

### Limbic/Amygdala (4-8 Hz theta)
| Neuromodulator | Effect | Parameter Change |
|----------------|--------|------------------|
| **NE** | Enhances fear encoding | +30-60% theta, facilitates LTP |
| **5-HT** | Anxiolytic at moderate levels | -25-50% anxiety theta |
| **DA** | Valence-dependent | Reward: +gamma, Fear: +theta |
| **ACh** | Enhances plasticity | Facilitates encoding |

### Hippocampus (4-12 Hz theta)
| Neuromodulator | Effect | Parameter Change |
|----------------|--------|------------------|
| **NE** | Enhances LTP | +20-40% theta power |
| **5-HT** | Complex, dose-dependent | +10-25% theta |
| **DA** | Enhances consolidation | Burst: +plasticity |
| **ACh** | ESSENTIAL for theta | +50-100% theta (required) |

### Prefrontal (30-100 Hz gamma)
| Neuromodulator | Effect | Parameter Change |
|----------------|--------|------------------|
| **NE** | Inverted-U: optimal at moderate | +20-50% gamma (optimal) |
| **5-HT** | Modest effect | -10-20% theta |
| **DA** | Inverted-U: optimal at moderate | Optimal gamma at D1/D2 balance |
| **ACh** | Attention, suppresses alpha | -50% alpha, +50% gamma |

### Thalamus (8-12 Hz alpha)
| Neuromodulator | Effect | Parameter Change |
|----------------|--------|------------------|
| **NE** | Shifts alpha to beta | 8-12 -> 15-25 Hz |
| **5-HT** | Modest effect | Slight alpha increase |
| **ACh** | Disrupts alpha rhythm | -40% alpha power |

### DMN (8-12 Hz alpha)
| Neuromodulator | Effect | Parameter Change |
|----------------|--------|------------------|
| **NE** | Deactivates DMN | -30-50% activity |
| **5-HT** | Increases DMN coherence | +20% connectivity |
| **DA** | Context-dependent | Variable |
| **ACh** | Deactivates during attention | -40-60% activity |

---

# PART 7: DIFFUSE PROJECTION PATTERNS

## 7.1 Volume Transmission Model

Unlike point-to-point synapses, neuromodulators use volume transmission:
- **Release sites:** Varicosities along axons
- **Diffusion distance:** 1-20 micrometers
- **Time constant:** 100-1000 ms (slow)
- **Concentration gradient:** [neuromodulator] ~ 1/distance^2

## 7.2 Brian2 Implementation for Diffuse Tone

```python
# ============== NEUROMODULATORY TONE IMPLEMENTATION ==============

# Neuromodulator state variables (global tone)
nm_model = '''
# Neuromodulator concentrations (dimensionless, 0-1 scale)
NE_tone : 1
DA_tone : 1
ACh_tone : 1
HT_tone : 1  # 5-HT (serotonin)

# Target-specific modulation
I_NE = NE_tone * g_NE : volt
I_DA = DA_tone * g_DA : volt
I_ACh = ACh_tone * g_ACh : volt
I_HT = HT_tone * g_HT : volt

g_NE : volt
g_DA : volt
g_ACh : volt
g_HT : volt
'''

# ============== LOCUS COERULEUS ==============
LC_params = {
    'N_neurons': 50,
    'tau_m': 20 * ms,
    'tau_osc': 10 * ms,
    'f_osc': 4 * Hz,  # Tonic rate (variable by state)
    'A_osc': 30 * mV,
    'V_rest': -52 * mV,
    'V_th': -42 * mV,
    'V_reset': -58 * mV,
}

# LC output = NE tone
# NE_tone = LC_mean_firing_rate / 20  # Normalize to 0-1

# ============== RAPHE NUCLEI ==============
raphe_params = {
    'N_neurons': 80,
    'tau_m': 35 * ms,
    'tau_osc': 10 * ms,
    'f_osc': 2 * Hz,  # Pacemaker rate
    'A_osc': 35 * mV,
    'V_rest': -58 * mV,
    'V_th': -48 * mV,
}

# Raphe output = 5-HT tone
# HT_tone = raphe_mean_firing_rate / 5

# ============== VTA DOPAMINE ==============
VTA_params = {
    'N_neurons': 100,
    'tau_m': 25 * ms,
    'tau_osc': 10 * ms,
    'f_osc': 4 * Hz,  # Tonic rate
    'A_osc': 32 * mV,
    'V_rest': -58 * mV,
    'V_th': -48 * mV,
}

# VTA output = DA tone
# DA_tone = VTA_mean_firing_rate / 10

# ============== BASAL FOREBRAIN ==============
BF_params = {
    'N_neurons': 120,
    'tau_m': 25 * ms,
    'tau_osc': 10 * ms,
    'f_osc': 15 * Hz,  # Active wake rate
    'A_osc': 30 * mV,
    'V_rest': -58 * mV,
    'V_th': -48 * mV,
}

# BF output = ACh tone
# ACh_tone = BF_mean_firing_rate / 30
```

## 7.3 State-Dependent Tone Controller

```python
class NeuromodulatoryState:
    """Controls global neuromodulatory tone based on arousal state"""

    states = {
        'deep_sleep': {
            'NE_tone': 0.02, 'DA_tone': 0.05, 'ACh_tone': 0.02, 'HT_tone': 0.10,
            'LC_rate': 0.3, 'raphe_rate': 1.0, 'VTA_rate': 0.5, 'BF_rate': 0.5
        },
        'rem_sleep': {
            'NE_tone': 0.10, 'DA_tone': 0.30, 'ACh_tone': 0.80, 'HT_tone': 0.05,
            'LC_rate': 1.0, 'raphe_rate': 0.5, 'VTA_rate': 3.0, 'BF_rate': 20.0
        },
        'quiet_wake': {
            'NE_tone': 0.30, 'DA_tone': 0.40, 'ACh_tone': 0.40, 'HT_tone': 0.50,
            'LC_rate': 3.0, 'raphe_rate': 2.5, 'VTA_rate': 4.0, 'BF_rate': 10.0
        },
        'active_attention': {
            'NE_tone': 0.60, 'DA_tone': 0.60, 'ACh_tone': 0.70, 'HT_tone': 0.50,
            'LC_rate': 6.0, 'raphe_rate': 3.5, 'VTA_rate': 7.0, 'BF_rate': 25.0
        },
        'stress': {
            'NE_tone': 0.85, 'DA_tone': 0.70, 'ACh_tone': 0.60, 'HT_tone': 0.70,
            'LC_rate': 15.0, 'raphe_rate': 6.0, 'VTA_rate': 10.0, 'BF_rate': 30.0
        },
        'reward': {
            'NE_tone': 0.50, 'DA_tone': 0.90, 'ACh_tone': 0.60, 'HT_tone': 0.50,
            'LC_rate': 5.0, 'raphe_rate': 3.0, 'VTA_rate': 20.0, 'BF_rate': 25.0
        }
    }

    def set_state(self, network, state_name, transition_time=1000*ms):
        """Gradually transition to new neuromodulatory state"""
        state = self.states[state_name]
        network.LC.f_osc = state['LC_rate'] * Hz
        network.raphe.f_osc = state['raphe_rate'] * Hz
        network.VTA.f_osc = state['VTA_rate'] * Hz
        network.BF.f_osc = state['BF_rate'] * Hz
```

## 7.4 Modulatory Effects on Neuron Parameters

```python
def apply_neuromodulation(neuron_group, NE_tone, DA_tone, ACh_tone, HT_tone):
    """Apply neuromodulatory effects to neuron parameters"""

    # NE effect: Increase excitability, enhance oscillation amplitude
    neuron_group.A_osc = neuron_group.A_osc_base * (1 + 0.5 * NE_tone)
    neuron_group.V_th = neuron_group.V_th_base - 3 * mV * NE_tone  # Lower threshold

    # ACh effect: Suppress alpha, enhance gamma
    if neuron_group.region == 'cortex':
        neuron_group.f_osc = neuron_group.f_osc_base * (1 + 0.5 * ACh_tone)

    # DA effect: Inverted-U for PFC
    if neuron_group.region == 'PFC':
        # Optimal DA = 0.5, reduced performance at 0 or 1
        da_effect = 4 * DA_tone * (1 - DA_tone)  # Peak at 0.5
        neuron_group.A_osc = neuron_group.A_osc_base * (1 + 0.3 * da_effect)

    # 5-HT effect: Anxiolytic in amygdala
    if neuron_group.region == 'amygdala':
        neuron_group.A_osc = neuron_group.A_osc_base * (1 - 0.3 * HT_tone)
```

---

# PART 8: SUMMARY TABLES

## 8.1 Neuron Parameter Summary

| System | N (scaled) | tau_m (ms) | f_base (Hz) | A_osc (mV) | V_th (mV) |
|--------|------------|------------|-------------|------------|-----------|
| **LC-NE** | 50 | 20 | 2-10 | 30 | -42 |
| **Raphe-5HT** | 80 | 35 | 1-5 | 35 | -48 |
| **VTA-DA** | 100 | 25 | 2-8 | 32 | -48 |
| **BF-ACh** | 120 | 25 | 5-30 | 30 | -48 |

## 8.2 Diffuse Projection Weights

| Source -> Target | p_conn | Effect | Weight Modifier |
|------------------|--------|--------|-----------------|
| **LC -> Cortex** | 0.10 | Excitatory | +20-50% firing |
| **LC -> Amygdala** | 0.08 | Excitatory | +30-60% theta |
| **Raphe -> Amygdala** | 0.12 | Inhibitory | -25-50% anxiety |
| **Raphe -> Hippocampus** | 0.20 | Excitatory | +10-25% theta |
| **VTA -> NAc** | 0.30 | Excitatory | +50-200% gamma |
| **VTA -> PFC** | 0.10 | Modulatory | Inverted-U |
| **BF -> Cortex** | 0.15 | Excitatory | Alpha suppress |
| **BF -> Hippocampus** | 0.25 | Essential | +50-100% theta |

## 8.3 State Firing Rate Summary (Hz)

| System | Deep Sleep | REM | Quiet Wake | Active | Stress | Reward |
|--------|------------|-----|------------|--------|--------|--------|
| **LC-NE** | 0.3 | 1 | 3 | 6 | 15 | 5 |
| **Raphe-5HT** | 1 | 0.5 | 2.5 | 3.5 | 6 | 3 |
| **VTA-DA** | 0.5 | 3 | 4 | 7 | 10 | 20 |
| **BF-ACh** | 0.5 | 20 | 10 | 25 | 30 | 25 |

---

# PART 9: BRIAN2 COMPLETE IMPLEMENTATION

```python
# ============== COMPLETE NEUROMODULATORY SYSTEM ==============

from brian2 import *

# Neuromodulator neuron model (modified LIF with state-dependent rate)
nm_neuron_model = '''
dv/dt = (V_rest - v + I_osc + I_syn) / tau_m : volt (unless refractory)
dI_osc/dt = (-I_osc + A_osc * sin(2*pi*f_osc*t)) / tau_osc : volt
dI_syn/dt = -I_syn / tau_syn : volt

tau_m : second
tau_osc : second
tau_syn : second
f_osc : Hz
A_osc : volt
V_rest : volt
V_th : volt
V_reset : volt
'''

# Create neuromodulatory populations
def create_neuromodulatory_systems(N_scale=0.01):

    # Locus Coeruleus (NE)
    LC = NeuronGroup(
        int(50 * N_scale),
        nm_neuron_model,
        threshold='v > V_th',
        reset='v = V_reset',
        refractory=5*ms,
        method='euler'
    )
    LC.tau_m = 20 * ms
    LC.tau_osc = 10 * ms
    LC.f_osc = 3 * Hz  # Quiet wake baseline
    LC.A_osc = 30 * mV
    LC.V_rest = -52 * mV
    LC.V_th = -42 * mV
    LC.V_reset = -58 * mV
    LC.v = -52 * mV

    # Dorsal Raphe (5-HT)
    raphe = NeuronGroup(
        int(80 * N_scale),
        nm_neuron_model,
        threshold='v > V_th',
        reset='v = V_reset',
        refractory=5*ms,
        method='euler'
    )
    raphe.tau_m = 35 * ms
    raphe.tau_osc = 10 * ms
    raphe.f_osc = 2.5 * Hz
    raphe.A_osc = 35 * mV
    raphe.V_rest = -58 * mV
    raphe.V_th = -48 * mV
    raphe.V_reset = -62 * mV
    raphe.v = -58 * mV

    # VTA (DA)
    VTA = NeuronGroup(
        int(100 * N_scale),
        nm_neuron_model,
        threshold='v > V_th',
        reset='v = V_reset',
        refractory=5*ms,
        method='euler'
    )
    VTA.tau_m = 25 * ms
    VTA.tau_osc = 10 * ms
    VTA.f_osc = 4 * Hz
    VTA.A_osc = 32 * mV
    VTA.V_rest = -58 * mV
    VTA.V_th = -48 * mV
    VTA.V_reset = -62 * mV
    VTA.v = -58 * mV

    # Basal Forebrain (ACh)
    BF = NeuronGroup(
        int(120 * N_scale),
        nm_neuron_model,
        threshold='v > V_th',
        reset='v = V_reset',
        refractory=5*ms,
        method='euler'
    )
    BF.tau_m = 25 * ms
    BF.tau_osc = 10 * ms
    BF.f_osc = 10 * Hz
    BF.A_osc = 30 * mV
    BF.V_rest = -58 * mV
    BF.V_th = -48 * mV
    BF.V_reset = -62 * mV
    BF.v = -58 * mV

    return {'LC': LC, 'raphe': raphe, 'VTA': VTA, 'BF': BF}


def create_nm_monitors(nm_systems):
    """Create spike monitors for neuromodulatory systems"""
    monitors = {}
    for name, group in nm_systems.items():
        monitors[name + '_spikes'] = SpikeMonitor(group)
        monitors[name + '_rate'] = PopulationRateMonitor(group)
    return monitors


def get_nm_tones(nm_systems, monitors, max_rates):
    """Calculate normalized neuromodulatory tones (0-1)"""
    tones = {}
    for name, group in nm_systems.items():
        rate_monitor = monitors[name + '_rate']
        mean_rate = np.mean(rate_monitor.rate[-100:])  # Last 100 ms
        tones[name] = float(mean_rate / max_rates[name])
        tones[name] = np.clip(tones[name], 0, 1)
    return tones


# Max firing rates for normalization
NM_MAX_RATES = {
    'LC': 20 * Hz,      # Max stress rate
    'raphe': 8 * Hz,    # Max stress rate
    'VTA': 25 * Hz,     # Max burst rate
    'BF': 40 * Hz       # Max active rate
}
```

---

# PART 10: KEY REFERENCES

1. **Aston-Jones & Cohen (2005)** - Adaptive gain theory, LC-NE function
2. **Berridge & Waterhouse (2003)** - LC-NE modulation of cognition
3. **Jacobs & Azmitia (1992)** - Raphe serotonin electrophysiology
4. **Schultz (1998, 2016)** - Dopamine reward prediction error
5. **Hasselmo (1999)** - ACh in memory and attention
6. **Yu & Dayan (2005)** - NE and ACh in attention
7. **Sara (2009)** - LC-NE in cognitive flexibility
8. **Bouret & Sara (2005)** - LC phasic/tonic modes

---

*Research compiled for Conscious SNN Project - 2026-03-13*
*Multi-perspective analysis by Alex Rivera*
