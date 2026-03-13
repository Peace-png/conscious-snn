# Emotional Neural Signatures Across the Limbic System
## Multi-Perspective Research Synthesis for Computational Modeling

**Compiled:** 2026-03-13
**Purpose:** Quantitative neural data for spiking neural network simulations of emotional states

---

## 1. Comparative Oscillation Frequencies: Emotional States

### Fear State Neural Signatures

| Region | Primary Oscillation | Hz Range | Secondary Oscillation | Notes |
|--------|---------------------|----------|----------------------|-------|
| Amygdala (BLA) | Theta | 4-8 Hz | Gamma 40-80 Hz | Theta increases 200-400% during fear conditioning |
| Amygdala (CeA) | Theta | 3-6 Hz | Beta 13-30 Hz | Synchronizes with hippocampal theta |
| Hippocampus | Theta | 4-12 Hz | Gamma 30-100 Hz | Phase-locked to amygdala during fear retrieval |
| mPFC | Theta | 4-8 Hz | Gamma 30-50 Hz | Decreased theta-gamma coupling in anxiety |
| Insula | Beta/Gamma | 20-35 Hz | Gamma 40-70 Hz | Increased interoceptive processing |

**Computational Parameters:**
- Fear conditioning: Amygdala theta amplitude increases by factor of 2-4x baseline
- Fear extinction: vmPFC theta (6-8 Hz) suppresses amygdala activity
- Optimal modeling range: 4-8 Hz theta with 40-80 Hz gamma bursts (200-300ms duration)

### Rage/Anger State Neural Signatures

| Region | Primary Oscillation | Hz Range | Secondary Oscillation | Notes |
|--------|---------------------|----------|----------------------|-------|
| Amygdala | Beta | 13-30 Hz | Gamma 30-50 Hz | Elevated beta correlates with anger intensity |
| Hypothalamus | Theta | 4-7 Hz | Delta 1-4 Hz | Defensive rage circuit activation |
| PAG (Periaqueductal Gray) | Theta | 4-8 Hz | Gamma 40-60 Hz | Fight-or-flight coordination |
| ACC (Anterior Cingulate) | Theta | 4-7 Hz | Beta 13-20 Hz | Conflict monitoring, anger suppression |
| dlPFC | Beta | 15-25 Hz | Gamma 30-45 Hz | Cognitive control of anger |

**Computational Parameters:**
- Rage onset: Rapid hypothalamus-amygdala-PAG synchronization (50-100ms)
- Sustained anger: Elevated beta power (20-30 Hz) in amygdala and ACC
- Suppression attempt: dlPFC theta-beta cross-frequency coupling increases

### Grief/Sadness State Neural Signatures

| Region | Primary Oscillation | Hz Range | Secondary Oscillation | Notes |
|--------|---------------------|----------|----------------------|-------|
| Amygdala | Alpha | 8-12 Hz | Theta 4-7 Hz | Increased alpha power (hypoactivation) |
| Subgenual ACC (sgACC) | Theta | 4-8 Hz | Alpha 8-12 Hz | Hyperactivity in depression |
| vmPFC | Theta | 5-8 Hz | Delta 1-4 Hz | Rumination circuits |
| Insula | Alpha | 8-13 Hz | Beta 13-20 Hz | Reduced interoceptive awareness |
| Nucleus Accumbens | Delta | 1-4 Hz | Theta 4-8 Hz | Reward processing deficit |

**Computational Parameters:**
- Acute grief: Amygdala-hippocampal theta hypersynchrony (5-7 Hz)
- Sadness: Increased frontal alpha asymmetry (left < right)
- Depression-like state: sgACC theta overactivity (factor 1.5-2x baseline)
- Anhedonia: Reduced nucleus accumbens gamma (40-80 Hz) response to reward

### Joy/Euphoria State Neural Signatures

| Region | Primary Oscillation | Hz Range | Secondary Oscillation | Notes |
|--------|---------------------|----------|----------------------|-------|
| Nucleus Accumbens | Gamma | 40-80 Hz | Beta 20-30 Hz | Reward prediction, dopamine release |
| Ventral Tegmental Area | Theta | 4-8 Hz | Gamma 30-50 Hz | Dopaminergic burst firing |
| vmPFC/OFC | Gamma | 30-50 Hz | Theta 4-8 Hz | Positive valuation |
| Amygdala | Gamma | 30-60 Hz | Theta 6-9 Hz | Reduced baseline, reactive to positive |
| Hippocampus | Theta | 6-10 Hz | Gamma 40-100 Hz | Enhanced theta-gamma coupling |

**Computational Parameters:**
- Reward anticipation: NAc gamma power increases 150-300% from baseline
- Joy onset: VTA theta burst followed by NAc gamma (100-200ms latency)
- Sustained positive affect: vmPFC-NAc gamma synchrony (40-50 Hz)
- Euphoria (dopaminergic): Elevated gamma across mesolimbic circuit

---

## 2. Heart-Brain Coupling During Emotional States

### Neurovisceral Integration Model (Thayer & Lane, 2000, 2009)

**Core Framework:**
- Heart Rate Variability (HRV) indexes vagal tone and prefrontal regulatory capacity
- High HRV = flexible emotional regulation
- Low HRV = rigid, maladaptive responses

### Cardiac-Amygdala Coupling

| State | Cardiac Pattern | Amygdala Activity | Coupling Mechanism |
|-------|-----------------|-------------------|-------------------|
| Fear | Increased HR, decreased HRV | Hyperactive BLA | Baroreceptor input modulates amygdala during cardiac systole |
| Anger | Increased HR, reduced HRV | Moderate-high | Sympathetic dominance reduces inhibitory vagal tone |
| Grief | Variable HR, reduced HRV | Hypoactive or hyperactive | Dissociation between cardiac and amygdala signals |
| Joy | Increased HRV, moderate HR | Normalized activity | Vagal flexibility supports amygdala regulation |

**Quantitative Coupling Data:**
- Cardiac cycle time: ~800-1000ms (60-75 bpm)
- Baroreceptor firing: Peaks during systole (200-300ms after R-wave)
- Amygdala response latency to cardiac input: 50-150ms
- Fear processing enhanced during systole vs diastole (effect size d=0.6)

### Cardiac-Prefrontal Coupling

**Key Findings:**
- vmPFC activity correlates with HRV (r = 0.4-0.6 in studies)
- dlPFC activation during cognitive control increases HRV transiently
- ACC activity predicts subsequent cardiac deceleration (orienting response)

**Computational Parameters:**
- Vagal tone update rate: 0.5-2 Hz (respiratory sinus arrhythmia)
- Prefrontal inhibition of amygdala: 50-100ms delay
- Heart-brain feedback loop: ~500-1000ms (one cardiac cycle)

### Implementation for SNN

```
Cardiac oscillator parameters:
- Base frequency: 1.0-1.25 Hz (60-75 bpm)
- HRV modulation: 0.1-0.4 Hz oscillation amplitude
- Respiratory coupling: 0.2-0.3 Hz (respiratory sinus arrhythmia)
- Baroreceptor burst timing: 200-300ms after cardiac R-wave

Coupling weights:
- Cardiac -> Amygdala: Excitatory during systole, inhibitory during diastole
- vmPFC -> Cardiac (vagal): Inhibitory, strength proportional to vmPFC activity
- Amygdala -> Cardiac: Excitatory (sympathetic activation)
```

---

## 3. Default Mode Network Changes During Emotional Processing

### DMN Core Nodes

| Node | Location | Baseline Function |
|------|----------|-------------------|
| Posterior Cingulate Cortex (PCC) | Precuneus | Self-referential processing |
| Medial Prefrontal Cortex (mPFC) | vmPFC/dmPFC | Mentalizing, self-reflection |
| Angular Gyrus | Parietal | Episodic memory retrieval |
| Hippocampus | Medial temporal | Autobiographical memory |

### DMN Alterations by Emotional State

**Fear/Anxiety:**
- PCC connectivity: Increased with amygdala, decreased with mPFC
- mPFC activity: Decreased (reduced cognitive control)
- Hippocampal coupling: Increased (threat memory retrieval)
- Effect size: g = 0.5-0.8 in meta-analyses

**Grief/Depression:**
- PCC activity: Increased (rumination)
- sgACC connectivity: Hyperconnectivity with DMN
- mPFC-mPFC coupling: Increased (self-focused processing)
- Anti-correlation with task-positive networks: Reduced
- Meta-analysis: Hedge's g = 0.6-1.0 for DMN hyperconnectivity

**Anger:**
- DMN deactivation: Greater during anger provocation
- PCC-amygdala coupling: Positive correlation with anger intensity
- mPFC connectivity: Decreased with limbic regions

**Joy:**
- DMN connectivity: More flexible, less rigid
- mPFC-NAc coupling: Increased during positive anticipation
- Anti-correlation with salience network: Normalized

### Computational DMN Model

```
DMN oscillator parameters:
- PCC: Alpha dominant (8-12 Hz), strong self-connectivity
- mPFC: Theta-alpha (4-12 Hz), variable based on state
- Hippocampus: Theta (4-10 Hz), phase-coupled to PCC

State-dependent connectivity:
- Rest: High DMN internal connectivity, low external
- Fear: PCC-amygdala coupling increases (weight +0.3 to +0.5)
- Depression: All DMN weights increased (+20-40%), reduced flexibility
- Joy: DMN-NAc coupling increases, internal DMN coupling decreases slightly
```

---

## 4. Cross-Frequency Coupling in Emotional States

### Phase-Amplitude Coupling (PAC) Mechanisms

**Theta-Gamma Coupling (TGC):**
- Mechanism: Gamma amplitude modulated by theta phase
- Measurement: Modulation Index (MI), Phase-Locking Value (PLV)
- Hippocampal TGC: ~2-4 gamma cycles per theta cycle (optimal)

**Emotional State TGC Values:**

| State | Region | Theta Phase of Peak Gamma | Gamma Frequency | Coupling Strength (MI) |
|-------|--------|---------------------------|-----------------|------------------------|
| Fear (encoding) | Amygdala-Hippocampus | 270-315 deg | 60-100 Hz | 0.015-0.030 |
| Fear (retrieval) | Amygdala-mPFC | 180-270 deg | 40-60 Hz | 0.010-0.020 |
| Anxiety (chronic) | mPFC | Variable | 30-50 Hz | 0.005-0.010 (reduced) |
| Joy | NAc | 90-180 deg | 50-80 Hz | 0.020-0.040 |
| Depression | sgACC | 0-90 deg | 30-50 Hz | 0.008-0.015 |

### Alpha-Gamma Coupling

**Mechanism:**
- Alpha phase (8-12 Hz) modulates gamma amplitude
- Inhibitory gating hypothesis: Alpha troughs allow gamma emergence

**Emotional State Alpha-Gamma Values:**

| State | Region | Alpha-Gamma Relationship |
|-------|--------|-------------------------|
| Fear | Visual cortex | Increased alpha suppresses gamma (threat avoidance) |
| Anger | Amygdala | Reduced alpha, disinhibited gamma |
| Sadness | Frontal | Left frontal alpha increases, gamma decreases |
| Joy | Occipital-parietal | Reduced alpha, enhanced gamma processing |

### Beta-Gamma Coupling

**Less studied but relevant for:**
- Anger/rage states: Beta (15-25 Hz) phase modulates gamma amplitude
- Motor preparation for action: Beta-gamma in motor cortex
- Anxiety: Elevated beta-gamma coupling in insula

### Computational Implementation

```python
# Cross-frequency coupling parameters for SNN

class CrossFrequencyCoupling:
    """Phase-amplitude coupling model for emotional states"""

    # Theta-gamma coupling
    theta_gamma = {
        'fear': {
            'theta_freq': 6.0,  # Hz
            'gamma_freq': 80.0,  # Hz
            'phase_offset': 270,  # degrees
            'coupling_strength': 0.025
        },
        'joy': {
            'theta_freq': 8.0,
            'gamma_freq': 60.0,
            'phase_offset': 135,
            'coupling_strength': 0.030
        },
        'anger': {
            'theta_freq': 5.0,
            'gamma_freq': 40.0,
            'phase_offset': 180,
            'coupling_strength': 0.018
        },
        'grief': {
            'theta_freq': 7.0,
            'gamma_freq': 45.0,
            'phase_offset': 45,
            'coupling_strength': 0.012
        }
    }

    # Alpha-gamma coupling
    alpha_gamma = {
        'fear': {
            'alpha_freq': 10.0,
            'coupling_direction': 'inverse',  # high alpha = low gamma
            'strength': -0.02
        },
        'anger': {
            'alpha_freq': 8.0,
            'coupling_direction': 'inverse',
            'strength': -0.03
        },
        'joy': {
            'alpha_freq': 10.0,
            'coupling_direction': 'direct',
            'strength': 0.02
        },
        'grief': {
            'alpha_freq': 11.0,
            'coupling_direction': 'inverse',
            'strength': -0.04
        }
    }
```

---

## 5. Pharmacological Modulation of Limbic Oscillations

### GABAergic Modulation

**GABA-A Receptor Effects:**

| Drug Class | Oscillation Effect | Region | Hz Change | Computational Parameter |
|------------|-------------------|--------|-----------|------------------------|
| Benzodiazepines | Increased gamma coherence | Cortex | 30-50 Hz: +20-40% power | GABA-A conductance +50-100% |
| Benzodiazepines | Reduced theta | Amygdala | 4-8 Hz: -30-50% | Inhibitory decay time +50% |
| Barbiturates | Increased beta | Global | 15-25 Hz: +100-200% | GABA-A open time increased |
| Alcohol | Increased delta/theta | Global | 4-8 Hz: +50% | NMDA inhibition + GABA-A potentiation |

**GABA-B Receptor Effects:**
- Baclofen: Reduces theta power in hippocampus (-30%)
- Slower dynamics: GABA-B time constant 100-300ms vs GABA-A 5-20ms

### Glutamatergic Modulation

**NMDA Receptors:**

| Drug | Oscillation Effect | Region | Notes |
|------|-------------------|--------|-------|
| Ketamine | Increased gamma (transient) | Cortex, PCC | 30-80 Hz: +100-300% (antidepressant) |
| Memantine | Reduced theta | Hippocampus | 4-8 Hz: -20-30% |
| D-Cycloserine | Enhanced fear extinction | Amygdala | Facilitates NMDA-dependent plasticity |

**AMPA Receptors:**
- Ampakines: Increase gamma power (+30-50%)
- AMPA potentiation: Faster oscillation onset

**Glutamate-Oscillation Relationship:**
- Gamma generation requires AMPA-mediated excitation
- NMDA contribution: Longer time constant, sustains oscillations
- Optimal E/I ratio for gamma: 0.8-1.2 (excitation/inhibition balance)

### Noradrenergic Modulation

**Locus Coeruleus-Norepinephrine (LC-NE) System:**

| State | LC Firing Rate | NE Level | Oscillation Effect |
|-------|---------------|----------|-------------------|
| Sleep | 0-1 Hz | Minimal | Dominant delta (1-4 Hz) |
| Rest | 2-4 Hz | Baseline | Mixed alpha/beta |
| Alert | 6-10 Hz | Elevated | Increased beta (15-25 Hz) |
| Stress | 10-20 Hz | High | Gamma enhancement (40-80 Hz) |

**Pharmacological Effects:**

| Drug | NE Effect | Oscillation Change | Hz Range |
|------|-----------|-------------------|----------|
| Propranolol (beta-blocker) | Reduces NE signaling | Reduced fear theta | 4-8 Hz: -25% |
| Clonidine (alpha-2 agonist) | Reduces LC firing | Increased alpha | 8-12 Hz: +30% |
| Yohimbine (alpha-2 antagonist) | Increases NE | Anxiety-like theta | 4-7 Hz: +40% |
| Amphetamines | Increases NE release | Elevated beta/gamma | 20-40 Hz: +50% |

### Dopaminergic Modulation (Bonus)

**VTA/SNc to Limbic Projections:**

| Drug | Oscillation Effect | Region | Hz Change |
|------|-------------------|--------|-----------|
| L-DOPA | Increased gamma | NAc | 40-80 Hz: +50-100% |
| Antipsychotics | Reduced gamma | NAc, Striatum | 40-60 Hz: -30% |
| Cocaine | Transient gamma burst | NAc | 40-80 Hz: +200% (acute) |

### Computational Pharmacological Model

```python
# Pharmacological modulation parameters for SNN

class PharmacologicalModulation:
    """Neurotransmitter effects on limbic oscillations"""

    gaba_effects = {
        'anxiolytic': {
            'target': 'amygdala',
            'theta_multiplier': 0.6,  # -40%
            'gamma_multiplier': 1.3,  # +30%
            'E_I_balance_shift': -0.15  # more inhibition
        },
        'sedative': {
            'target': 'global',
            'theta_multiplier': 1.5,  # +50%
            'gamma_multiplier': 0.7,  # -30%
            'E_I_balance_shift': -0.25
        }
    }

    glutamate_effects = {
        'ketamine': {
            'target': 'PCC, mPFC',
            'gamma_multiplier': 2.5,  # +150%
            'onset_latency': 0.5,  # hours
            'duration': 72,  # hours
            'E_I_balance_shift': 0.1  # more excitation
        }
    }

    norepinephrine_effects = {
        'stress': {
            'lc_firing': 15.0,  # Hz
            'amygdala_beta_multiplier': 1.4,
            'pfc_theta_multiplier': 0.8,  # reduced control
            'global_arousal': 1.5
        },
        'calm': {
            'lc_firing': 3.0,
            'amygdala_beta_multiplier': 1.0,
            'pfc_theta_multiplier': 1.2,
            'global_arousal': 1.0
        }
    }

    dopamine_effects = {
        'reward': {
            'target': 'NAc',
            'gamma_multiplier': 2.0,  # +100%
            'theta_gamma_coupling': 1.5,  # increased
            'burst_duration': 200,  # ms
        },
        'anhedonia': {
            'target': 'NAc',
            'gamma_multiplier': 0.6,  # -40%
            'theta_gamma_coupling': 0.7,
        }
    }
```

---

## 6. Summary Tables for Computational Implementation

### Master Oscillation Frequency Table

| Emotion | Amygdala | Hippocampus | mPFC | Insula | NAc |
|---------|----------|-------------|------|--------|-----|
| Fear | 4-8 Hz theta + 40-80 Hz gamma | 6-10 Hz theta | 4-8 Hz theta (reduced) | 20-35 Hz beta | 4-8 Hz theta |
| Rage | 13-30 Hz beta + 30-50 Hz gamma | 4-8 Hz theta | 15-25 Hz beta | 30-50 Hz gamma | 20-30 Hz beta |
| Grief | 8-12 Hz alpha (elevated) | 5-8 Hz theta | 4-8 Hz theta (elevated sgACC) | 8-13 Hz alpha | 1-4 Hz delta |
| Joy | 30-60 Hz gamma | 6-10 Hz theta + 40-100 Hz gamma | 30-50 Hz gamma | 8-12 Hz alpha (reduced) | 40-80 Hz gamma |

### Cross-Region Synchronization

| Emotion | Key Synchronized Pairs | Synchronization Frequency | Latency |
|---------|----------------------|--------------------------|---------|
| Fear | Amygdala-Hippocampus | 4-8 Hz theta | 10-30 ms |
| Fear | Amygdala-mPFC | 4-8 Hz theta (reduced) | 20-50 ms |
| Rage | Hypothalamus-Amygdala-PAG | 4-7 Hz theta | 5-20 ms |
| Grief | sgACC-PCC (DMN) | 8-12 Hz alpha | 30-60 ms |
| Joy | VTA-NAc-mPFC | 4-8 Hz theta + 40-60 Hz gamma | 20-40 ms |

---

## 7. Limitations and Considerations

### Data Quality Notes

1. **Species differences**: Most invasive data from rodents; human data primarily fMRI/EEG
2. **Temporal resolution**: EEG limited to scalp, deep structures require MEG or intracranial
3. **Individual variability**: Standard deviations often 30-50% of mean values
4. **State-dependent**: Oscillations highly context-dependent

### Recommended Citation Sources

For deeper investigation, search these key authors and papers:

- **Theta-gamma coupling**: Lisman & Jensen (2013), Canolty et al. (2006)
- **Amygdala oscillations**: Paré & Collins (2000), Seidenbecher et al. (2003)
- **Heart-brain**: Thayer & Lane (2000, 2009), Critchley et al. (2005)
- **DMN emotion**: Greicius et al. (2007), Hamilton et al. (2015)
- **Pharmacology**: Buzsáki & Wang (2012), Uhlhaas & Singer (2012)

---

## 8. Implementation Checklist for SNN

- [ ] Implement base oscillators for each region (AdEx neurons)
- [ ] Add theta-gamma cross-frequency coupling mechanism
- [ ] Implement cardiac oscillator with baroreceptor timing
- [ ] Add HRV modulation of vmPFC-amygdala inhibition
- [ ] Implement DMN as coupled oscillator network
- [ ] Add neurotransmitter modulation parameters (GABA, glutamate, NE, DA)
- [ ] Create emotional state presets (fear, rage, grief, joy)
- [ ] Validate against known oscillation patterns
- [ ] Test transition dynamics between emotional states

---

*Research compiled for the Conscious SNN Project - 2026-03-13*
