# Default Mode Network (DMN) Oscillation Parameters
## Quantitative Parameters for Brian2 SNN Implementation

**Compiled:** 2026-03-13

---

# PART 1: DMN OSCILLATION FREQUENCIES

## 1.1 Core DMN Nodes

| Region | Primary Oscillation | Hz Range | Secondary | Function |
|--------|---------------------|----------|-----------|----------|
| **PCC** | Alpha | 8-12 Hz | Beta 15-25 Hz | Consciousness hub, self-reference |
| **mPFC** | Alpha/Theta | 8-10 Hz / 4-8 Hz | Beta 15-30 Hz | Social cognition, mentalizing |
| **Angular Gyrus** | Alpha | 9-11 Hz | Theta 4-7 Hz | Semantic processing |
| **Hippocampus** | Theta | 4-8 Hz | Gamma 30-100 Hz | Memory encoding/retrieval |
| **IPL** | Alpha | 8-12 Hz | Beta 15-25 Hz | Attention, spatial awareness |

---

# PART 2: NEURON PARAMETERS

## 2.1 Membrane Time Constants

| Region | Cell Type | tau_m (ms) | A_osc (mV) |
|--------|-----------|------------|------------|
| **PCC (Layer 5)** | Pyramidal | 22-28 | 30-35 |
| **PCC (Layer 2/3)** | Pyramidal | 15-20 | 25-30 |
| **mPFC (Layer 5)** | Pyramidal | 20-25 | 28-35 |
| **mPFC (Layer 2/3)** | Pyramidal | 15-20 | 25-30 |
| **Angular Gyrus** | Pyramidal | 18-25 | 28-32 |
| **Hippocampal CA1** | Pyramidal | 25-35 | 35-45 |
| **Hippocampal CA3** | Pyramidal | 30-40 | 45-55 |
| **IPL** | Pyramidal | 18-22 | 28-32 |

## 2.2 Firing Rates

| Region | Resting Rate | Active State |
|--------|-------------|--------------|
| **PCC** | 2-8 Hz | 0.5-3 Hz (deactivated) |
| **mPFC** | 3-10 Hz | 1-5 Hz (deactivated) |
| **Hippocampus CA1** | 1-5 Hz | 5-15 Hz (encoding) |

---

# PART 3: CONNECTIVITY MATRIX

## 3.1 Intrinsic DMN Connectivity

| From -> To | PCC | mPFC | Angular G | Hippo |
|------------|-----|------|-----------|-------|
| **PCC** | - | 0.6-0.8 | 0.5-0.7 | 0.4-0.6 |
| **mPFC** | 0.6-0.8 | - | 0.3-0.5 | 0.3-0.5 |
| **Angular G** | 0.5-0.7 | 0.3-0.5 | - | 0.4-0.6 |
| **Hippocampus** | 0.4-0.6 | 0.3-0.5 | 0.4-0.6 | - |

## 3.2 Synaptic Parameters

| Connection | p_conn | w_syn (mV) | delay (ms) | tau_syn (ms) |
|------------|--------|------------|------------|--------------|
| **PCC <-> mPFC** | 0.15-0.25 | 2-4 | 8-15 | 10-15 |
| **PCC <-> Hippocampus** | 0.10-0.20 | 2-3 | 15-25 | 8-12 |
| **PCC <-> Angular G** | 0.20-0.30 | 2-4 | 5-10 | 10-15 |
| **mPFC <-> Hippocampus** | 0.10-0.15 | 1-3 | 20-30 | 10-15 |

---

# PART 4: ALPHA RHYTHM GENERATION

## 4.1 Mechanisms

1. **Thalamocortical loops** - Pulvinar and MD thalamus provide alpha pacemaking
2. **Cortical inhibition** - GABAergic interneuron networks
3. **PCC intrinsic pacemaker** - Layer V generators

## 4.2 Thalamocortical Alpha

| Component | Parameter | Value |
|-----------|-----------|-------|
| **Pulvinar firing** | f_alpha | 8-12 Hz |
| **MD thalamus** | f_alpha | 8-10 Hz |
| **TRN inhibition** | tau_GABA | 10-20 ms |
| **Cortical feedback delay** | delay | 10-20 ms |

---

# PART 5: DMN DEACTIVATION

## 5.1 Task Engagement Effects

| Mechanism | Timecourse | Magnitude |
|-----------|------------|-----------|
| **PCC suppression** | 200-500 ms | -40 to -60% |
| **mPFC suppression** | 300-600 ms | -30 to -50% |
| **Alpha suppression** | 100-200 ms | -50 to -70% |

## 5.2 Anticorrelation with Task-Positive Network

| DMN Node | Anticorrelated Region | r-value |
|----------|----------------------|---------|
| **PCC** | DLPFC | -0.4 to -0.6 |
| **mPFC** | IPS | -0.3 to -0.5 |

---

# PART 6: DMN-LIMBIC COUPLING

## 6.1 Connectivity

| Pathway | p_conn | w_syn (mV) | delay (ms) |
|---------|--------|------------|------------|
| **mPFC -> BLA** | 0.15-0.25 | 2-4 | 15-25 |
| **BLA -> mPFC** | 0.10-0.20 | 1-3 | 15-25 |
| **Hippocampus -> BLA** | 0.20-0.30 | 2-4 | 5-10 |

## 6.2 Coherence by State

| State | mPFC-BLA | Hippo-BLA |
|-------|----------|-----------|
| **Rest** | 0.3-0.5 | 0.3-0.5 |
| **Fear** | 0.2-0.4 | 0.6-0.8 |
| **Extinction** | 0.5-0.7 | 0.4-0.6 |

---

# PART 7: DMN-THALAMUS COUPLING

## 7.1 Key Thalamic Nuclei

| Nucleus | DMN Target | Frequency |
|---------|------------|-----------|
| **Pulvinar** | PCC, Angular G | 8-12 Hz alpha |
| **MD** | mPFC | 8-10 Hz alpha |
| **TRN** | All cortex | 8-12 Hz gating |

## 7.2 Connectivity

| Pathway | p_conn | w_syn (mV) | delay (ms) |
|---------|--------|------------|------------|
| **Pulvinar -> PCC** | 0.20-0.35 | 3-5 | 8-15 |
| **MD -> mPFC** | 0.15-0.25 | 2-4 | 10-18 |
| **TRN -> Pulvinar** | 0.30-0.50 | -2 to -4 | 2-5 |

---

# PART 8: BRIAN2 IMPLEMENTATION

```python
# ============== DMN PARAMETERS ==============

# PCC (Posterior Cingulate Cortex)
pcc_params = {
    'N_neurons': 100,
    'tau_m': 22 * ms,
    'tau_osc': 10 * ms,        # CRITICAL: < 20ms
    'tau_syn': 12 * ms,
    'f_osc': 10 * Hz,          # Alpha
    'A_osc': 30 * mV,          # For tau_m=22ms
    'V_rest': -65 * mV,
    'V_th': -50 * mV,
    'method': 'euler',
}

# mPFC (Medial Prefrontal Cortex)
mpfc_params = {
    'N_neurons': 80,
    'tau_m': 20 * ms,
    'tau_osc': 10 * ms,
    'f_osc': 9 * Hz,           # Slightly slower alpha
    'A_osc': 28 * mV,
    'V_rest': -65 * mV,
    'V_th': -50 * mV,
    'method': 'euler',
}

# Hippocampus CA1
hippo_ca1_params = {
    'N_neurons': 100,
    'tau_m': 30 * ms,
    'tau_osc': 10 * ms,
    'f_osc': 6 * Hz,           # Theta
    'A_osc': 40 * mV,          # Larger for tau_m=30ms
    'V_rest': -65 * mV,
    'V_th': -50 * mV,
    'method': 'euler',
}

# DMN Connectivity
dmn_connectivity = {
    ('PCC', 'mPFC'): {'p': 0.20, 'w': 3*mV, 'delay': 12*ms},
    ('PCC', 'Hippocampus'): {'p': 0.15, 'w': 2*mV, 'delay': 20*ms},
    ('mPFC', 'Hippocampus'): {'p': 0.12, 'w': 2*mV, 'delay': 25*ms},
}

# Task Modulation
def apply_task_modulation(task_engaged, pcc, mpfc):
    if task_engaged:
        # Alpha suppression
        pcc.A_osc = 12 * mV      # 60% reduction
        mpfc.A_osc = 14 * mV     # 50% reduction
        # Inhibitory current
        pcc.I_task = -15 * mV
        mpfc.I_task = -12 * mV
    else:
        pcc.A_osc = 30 * mV
        mpfc.A_osc = 28 * mV
        pcc.I_task = 0 * mV
        mpfc.I_task = 0 * mV
```

---

# PART 9: SUMMARY TABLE

| Region | tau_m (ms) | A_osc (mV) | f_osc (Hz) | tau_osc (ms) | p_conn |
|--------|------------|------------|------------|--------------|--------|
| **PCC** | 22 | 30 | 10 (alpha) | 10 | 0.20 |
| **mPFC** | 20 | 28 | 9 (alpha) | 10 | 0.16 |
| **Angular G** | 20 | 28 | 10 (alpha) | 10 | 0.24 |
| **Hippocampus** | 30 | 40 | 6 (theta) | 10 | 0.16 |
| **IPL** | 20 | 28 | 10 (alpha) | 10 | 0.20 |

---

*Compiled for Conscious SNN Project - 2026-03-13*
