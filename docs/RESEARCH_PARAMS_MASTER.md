# Conscious SNN - Research Parameters Master Reference
## All quantitative neurophysiological parameters for Brian2 implementation

**Generated:** 2026-03-13
**Purpose:** Single-source-of-truth for simulation parameters

---

# CRITICAL CONSTRAINTS

## 1. tau_osc MUST be ≤ 10ms

| tau_osc | Result |
|---------|--------|
| 5ms | Works ✅ |
| 10ms | Works ✅ (recommended) |
| 20ms | Fails ❌ |
| 50ms | Complete suppression ❌ |

## 2. A_osc Scales with tau_m

**Formula:** A_osc ≈ tau_m × 1.5

| tau_m (ms) | A_osc (mV) |
|------------|------------|
| 10 | 15-20 |
| 15 | 22-25 |
| 20 | 30-35 |
| 25 | 35-40 |
| 30 | 40-50 |
| 35 | 50-55 |

## 3. Integration Method

**Always use `method='euler'` for oscillatory systems**

Brian2 bug #626: `exponential_euler` fails with sin/cos terms.

---

# SYSTEM PARAMETERS

## Brainstem (Autonomic Floor)

| Nucleus | tau_m (ms) | Firing Rate | Function |
|---------|------------|-------------|----------|
| NTS | 15-25 | 5-20 Hz | Integration hub |
| pre-Bötzinger | 20-30 | 0.25 Hz rhythm | Respiratory rhythm |
| Nucleus Ambiguus | 20-25 | 1-5 Hz | Vagal efferent |
| RVLM | 15-20 | 2-10 Hz | Sympathetic |
| CVLM | 10-15 | 5-15 Hz | Inhibitory |

## Cardiac System

| Parameter | Value |
|-----------|-------|
| tau_m | 30ms |
| tau_pacemaker | 100ms |
| f_card | 1.0 Hz (60 bpm) |
| A_card | 12mV |
| tau_vagal | 50ms |
| f_hrv | 0.1 Hz (Mayer wave) |

## Respiratory System

| Parameter | Value |
|-----------|-------|
| tau_m | 100ms |
| tau_rhythm | 200ms |
| f_resp | 0.25 Hz (15 bpm) |
| A_resp | 12mV |

## Thalamus

| Population | tau_m | A_osc | f_osc |
|------------|-------|-------|-------|
| Relay nuclei | 20ms | 30mV | 10Hz (alpha) |
| Reticular | 15ms | 25mV | 10Hz |
| Intralaminar | 25ms | 35mV | 10Hz |

**Reticular inhibition (CRITICAL):**
- Connection probability: 0.1 (NOT 0.3)
- Synaptic weight: 2mV (NOT 8mV)

## Limbic System

| Population | tau_m | A_osc | f_osc |
|------------|-------|-------|-------|
| BLA Pyramidal | 27.8ms | 40mV | 6Hz (theta) |
| BLA Stellate | 14.5ms | 25mV | - |
| BLA Interneuron | 19.0ms | 30mV | - |
| CeA Output | 20ms | 25mV | 5Hz |
| ITC (extinction gate) | 12ms | 20mV | - |

## Hippocampus

| Population | tau_m | A_osc | f_osc |
|------------|-------|-------|-------|
| Entorhinal | 20ms | 30mV | 8Hz |
| CA1 Pyramidal | 30ms | 45mV | 6Hz |
| CA3 Pyramidal | 35ms | 50mV | 6Hz |
| DG Granule | 20ms | 25mV | sparse |

## Prefrontal Cortex

| Population | tau_m | A_osc | f_osc |
|------------|-------|-------|-------|
| dlPFC Pyramidal | 20ms | - | - |
| vlPFC Pyramidal | 20ms | - | - |
| mPFC (gamma) | 15ms | 25mV | 40Hz |
| OFC | 20ms | - | - |

**PING Circuit for Gamma:**
- Pyramidal tau_m: 20ms
- Interneuron tau_m: 10ms
- E/I ratio: 4:1 (800:200)
- w_IE: 2.0nS (stronger than w_EI)
- w_EI: 0.5nS
- tau_GABA: 10ms (critical for gamma timing)

## DMN

| Population | tau_m | A_osc | f_osc |
|------------|-------|-------|-------|
| PCC | 22ms | 30mV | 10Hz (alpha) |
| mPFC | 20ms | 28mV | 9Hz |
| Angular Gyrus | 20ms | 28mV | 10Hz |
| Hippocampal | 30ms | 40mV | 6Hz (theta) |

---

# EMOTIONAL STATE SIGNATURES

## Fear
- Amygdala: 4-8 Hz theta + 40-80 Hz gamma
- Theta amplitude: +200-400%
- Theta-gamma MI: 0.015-0.030
- Phase: 270-315°

## Rage
- Amygdala: 13-30 Hz beta + 30-50 Hz gamma
- Hypothalamus-PAG sync: 4-7 Hz
- Onset: 50-100ms

## Grief
- Amygdala: 8-12 Hz alpha (elevated)
- sgACC theta: 4-8 Hz hyperactivity
- NAc delta: 1-4 Hz (reward deficit)

## Joy
- NAc gamma: 40-80 Hz (+150-300%)
- VTA theta: 4-8 Hz burst
- Phase: 90-180°
- MI: 0.020-0.040

---

# CONNECTIVITY PARAMETERS

## Synaptic Weights (mV)

| Connection Type | Range |
|-----------------|-------|
| Excitatory (weak) | 1-2mV |
| Excitatory (moderate) | 2-4mV |
| Excitatory (strong) | 4-6mV |
| Inhibitory | 3-8mV |

## Connection Probabilities

| Density | p_conn |
|---------|--------|
| Sparse (inter-system) | 0.02-0.05 |
| Moderate | 0.08-0.12 |
| Dense (thalamus-cortex) | 0.15-0.25 |
| Very dense (recurrent) | 0.20-0.40 |

## Anatomical Delays (ms)

| Pathway | Delay |
|---------|-------|
| Brainstem -> Thalamus | 7-13ms |
| Thalamus -> Cortex | 8-15ms |
| Hippocampus -> Prefrontal | 20-30ms |
| Limbic -> Prefrontal | 15-25ms |
| Intra-cortical | 5-10ms |
| Cardiac -> Limbic (baroreceptor) | 150ms |
| Respiratory -> Hippocampus | 50ms |

---

# CARDIAC-RESPIRATORY COUPLING

## RSA (Respiratory Sinus Arrhythmia)

| Parameter | Value |
|-----------|-------|
| RSA frequency | 0.15-0.40 Hz |
| RSA amplitude | 5-25 bpm |
| Phase advance (HR leads breath) | 5% |
| Coupling strength | 0.3-0.7 |

## Baroreceptor

| Parameter | Value |
|-----------|-------|
| Afferent latency | 50-100ms |
| Central processing | 100-200ms |
| Efferent (vagal) | 200-400ms |
| Total reflex | 500-800ms |
| Peak firing | 200-300ms post R-wave |

---

# CROSS-FREQUENCY COUPLING

## Theta-Gamma

| State | Theta Hz | Gamma Hz | Phase | MI |
|-------|----------|----------|-------|-----|
| Fear encoding | 6 | 60-100 | 270-315° | 0.015-0.030 |
| Fear retrieval | 6 | 40-60 | 180-270° | 0.010-0.020 |
| Joy | 8 | 50-80 | 90-180° | 0.020-0.040 |
| Depression | 7 | 30-50 | 0-90° | 0.008-0.015 |

---

# BRIAN2 IMPLEMENTATION CHECKLIST

- [x] tau_osc = 10ms for all oscillatory systems
- [x] A_osc scaled to tau_m (A_osc ≈ tau_m × 1.5)
- [x] method='euler' for oscillatory systems
- [x] Dual-layer clamping (equation + run_regularly)
- [x] Sparse connectivity (p=0.02-0.15)
- [x] Anatomically-based delays
- [x] E/I balance (~4:1)
- [x] Inhibition stronger than excitation

---

# RESEARCH SOURCES

1. Rainnie et al. 1993 (PMID: 8492168) - BLA electrophysiology
2. Wlodarczyk et al. 2013 (PMID: 24399937) - Hippocampal GABA
3. McCormick & Huguenard 1992 (PMID: 1331356) - Thalamocortical
4. Yang et al. 2025 (PMID: 41279575) - Amygdala-thalamic circuit
5. Zelano et al. 2016 (PMID: 27927961) - Respiratory-limbic
6. Lesting et al. 2011 (DOI: 10.1371/journal.pone.0021714) - Theta coupling
7. Brian2 GitHub Issue #626 - exponential_euler bug

---

*This file consolidates all research from 12+ research agent runs on 2026-03-13*
