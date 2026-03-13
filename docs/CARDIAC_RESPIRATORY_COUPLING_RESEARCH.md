# Cardiac-Respiratory Neural Coupling Research
## Quantitative Parameters for Brian2 SNN Implementation

**Compiled:** 2026-03-13

---

# PART 1: RESPIRATORY SINUS ARRHYTHMIA (RSA)

## 1.1 Core Phenomenon

Heart rate increases during inspiration, decreases during expiration.

| Parameter | Value | Notes |
|-----------|-------|-------|
| **RSA frequency range** | 0.15-0.40 Hz | High-frequency HRV band |
| **RSA amplitude** | 5-25 bpm variation | Young healthy adults |
| **Phase relationship** | HR leads lung volume by ~15° | ~100-150ms advance |
| **Inspiration HR increase** | +5-15% from baseline | Vagal withdrawal |
| **Expiration HR decrease** | -5-10% from baseline | Vagal activation |
| **RSA coupling strength** | 0.3-0.7 (correlation) | Dependent on vagal tone |

## 1.2 RSA Mechanism Chain

```
Inspiration (0-0.5 phase)
    -> Reduced vagal efferent activity
    -> Reduced ACh release at SA node
    -> Faster depolarization
    -> Higher heart rate

Expiration (0.5-1.0 phase)
    -> Increased vagal efferent activity
    -> Increased ACh release
    -> Slower depolarization
    -> Lower heart rate
```

---

# PART 2: BRAINSTEM NUCLEI

## 2.1 Key Nuclei Parameters

| Nucleus | Function | Firing Rate | tau_m (ms) |
|---------|----------|-------------|------------|
| **NTS** | Integration hub | 5-20 Hz | 15-25 |
| **pre-Botzinger** | Respiratory rhythm | 0.25 Hz rhythm | 20-30 |
| **Nucleus Ambiguus** | Vagal efferent | 1-5 Hz tonic | 20-25 |
| **DMN (Dorsal Motor)** | Parasympathetic | 0.5-2 Hz | 25-35 |
| **RVLM** | Sympathetic output | 2-10 Hz | 15-20 |
| **CVLM** | Inhibitory to RVLM | 5-15 Hz | 10-15 |

## 2.2 NTS Integration Parameters

- Receives: Carotid sinus (CN IX), Aortic arch (CN X), Lung stretch receptors
- Projects to: Nucleus ambiguus, DMN, RVLM, Parabrachial nucleus, Amygdala
- Integration time constant: 50-100 ms
- Connection probability to vagal nuclei: 0.3-0.5

---

# PART 3: BARORECEPTOR DYNAMICS

## 3.1 Timing Parameters

| Parameter | Value | Notes |
|-----------|-------|-------|
| **Afferent latency** | 50-100 ms | Nerve conduction to NTS |
| **Central processing** | 100-200 ms | NTS integration |
| **Efferent latency (vagal)** | 200-400 ms | NTS to heart via vagus |
| **Total reflex latency** | 500-800 ms | Complete baroreflex |
| **Sympathetic latency** | 1-3 seconds | Slower due to NE kinetics |
| **Baroreceptor firing timing** | 200-300 ms after R-wave | Peak during systole |

## 3.2 Baroreceptor Signal Characteristics

- Firing pattern: Phase-locked to cardiac cycle
- Rate: 20-100 Hz during systole, near-zero during diastole
- Adaptation: Rapid (50-200 ms) to sustained pressure
- Pulse synchronicity: 1:1 with heartbeat at rest

---

# PART 4: VAGAL PATHWAYS

## 4.1 Afferent vs Efferent

| Parameter | Afferent (80-90%) | Efferent (10-20%) |
|-----------|-------------------|-------------------|
| **Fiber count** | ~150,000 | ~30,000 |
| **Conduction velocity** | 2-20 m/s | 2-15 m/s |
| **Firing rate (rest)** | 20-50 Hz | 1-5 Hz |
| **Firing rate (active)** | 50-150 Hz | 5-15 Hz |

## 4.2 Vagal-Amygdala Communication

- Pathway: Vagal afferents -> NTS -> Parabrachial -> Amygdala (BLA)
- Delay: 100-200 ms from cardiac event to amygdala
- Synaptic weights: 1-3 mV at each synapse
- Connection probability: 0.1-0.3

---

# PART 5: CARDIAC-RESPIRATORY PHASE RELATIONSHIPS

## 5.1 Quantitative Phase Offsets

| Relationship | Phase Offset | Time Offset |
|--------------|--------------|-------------|
| **HR peak vs. Peak inspiration** | +15-30° | +100-200 ms |
| **HR trough vs. Peak expiration** | +15-30° | +100-200 ms |
| **Baroreceptor burst vs. R-wave** | ~90° | ~250 ms |
| **Amygdala response vs. Systole** | 0-45° | 50-150 ms |

## 5.2 Synchronization Ratios

- 4:1 heartbeat:breath (typical at 60 bpm, 15 breaths/min)
- 5:1 heartbeat:breath (slower breathing)
- 3:1 heartbeat:breath (faster breathing)

---

# PART 6: AMYGDALA MODULATION

## 6.1 Cardiac Phase Effects

| Cardiac Phase | Amygdala Activity | Fear Processing |
|---------------|-------------------|-----------------|
| **Systole (0-0.4)** | Enhanced excitability | +30-60% |
| **Diastole (0.4-1.0)** | Baseline/normal | Normal |
| **Early systole** | Peak response | Maximum |

## 6.2 Respiratory Phase Effects

| Respiratory Phase | Amygdala Activity |
|-------------------|-------------------|
| **Inspiration (0-0.5)** | Enhanced coupling |
| **Expiration (0.5-1.0)** | Reduced coupling |
| **Slow breathing (0.1 Hz)** | Reduced reactivity |

---

# PART 7: BRIAN2 IMPLEMENTATION

## 7.1 Complete Parameter Set

```python
# CARDIAC OSCILLATOR
cardiac_freq = 1.0 * Hz           # 60 bpm
cardiac_tau_m = 30 * ms
cardiac_A_osc = 12 * mV
cardiac_tau_osc = 50 * ms

# RESPIRATORY OSCILLATOR
respiratory_freq = 0.25 * Hz      # 15 breaths/min
respiratory_tau_m = 40 * ms
respiratory_A_osc = 15 * mV
respiratory_tau_osc = 100 * ms

# RSA COUPLING
rsa_coupling_strength = 0.4       # 0-1
rsa_phase_advance = 0.05          # HR leads by 5% of cycle
rsa_amplitude = 5 * mV            # HR variation

# BARORECEPTOR
baroreceptor_latency = 250 * ms
baroreceptor_tau = 50 * ms
baroreceptor_gain = 0.3

# NTS
NTS_tau_m = 20 * ms
NTS_connection_prob = 0.3

# VAGAL
vagal_afferent_latency = 150 * ms
vagal_efferent_latency = 200 * ms
vagal_weight = 3 * mV

# AMYGDALA COUPLING
cardiac_amygdala_delay = 150 * ms
respiratory_amygdala_delay = 50 * ms
systole_amygdala_weight = 2 * mV   # Excitatory
diastole_amygdala_weight = -1 * mV  # Inhibitory
```

## 7.2 RSA Implementation

```python
# Respiratory modulation of cardiac oscillator
I_rsa = rsa_coupling_strength * A_rsa * sin(2*pi*f_resp*(t - 0.05/f_resp))

# Vagal modulation
vagal_modulation = base_vagal_tone + 0.3 * sin(2*pi*f_resp*t + pi)

# Baroreceptor firing (during systole)
baroreceptor_firing = (cardiac_phase < 0.4) * baroreceptor_gain * pressure_signal

# Amygdala modulation
amygdala_cardiac_mod = (cardiac_phase < 0.4) * 1.5 * mV
amygdala_resp_mod = (resp_phase < 0.5) * 1.0 * mV
```

---

# REFERENCES

1. Thayer & Lane (2000, 2009) - Neurovisceral Integration Model
2. Zelano et al. 2016 (PMID: 27927961) - Respiratory-limbic entrainment
3. Tort et al. 2018 (PMID: 29691421) - Respiration-coupled oscillations
4. Critchley et al. (2005) - Heart-brain feedback
5. Pfurtscheller et al. 2025 (PMID: 40818329) - Brain-breathing interaction

---

*Compiled for Conscious SNN Project - 2026-03-13*
