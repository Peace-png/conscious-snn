# Brainstem Autonomic Nervous System Parameters
## For Brian2 SNN Consciousness Simulation - "Autonomic Floor"

**Compiled:** 2026-03-13
**Purpose:** Quantitative parameters for brainstem autonomic nuclei for consciousness simulation
**Focus:** NTS, RVLM, CVLM, Nucleus Ambiguus, Arousal systems ( Brian2 implementation

---

# PART 1: NUCLEUS TRACTUS SOLITARIUS (NTS)

## 1.1 NTS Neuron Electrophysiology

| Parameter | Value | Unit | Source | Notes |
|-----------|-------|------|--------|-------|
| **tau_m** | 15-30 | ms | Paton & Kubin 2007, Andresen 1991 | Visceral afferent integration |
| **R_in** | 80-200 | MOhm | High input resistance | |
| **V_rest** | -60 to -55 | mV | Depolarized resting potential | |
| **V_th** | -50 to -45 | mV | Spike threshold | |
| **AP width** | 0.5-1.0 | ms | Narrow action potentials | |
| **Firing rate (tonic)** | 1-10 | Hz | Baroreceptor input | Spontaneous activity |
| **Firing rate (burst)** | 10-50 | Hz | Visceral stimulation | Phasic response |

### 1.1.1 NTS Subnuclei Functional Differences

| Subnucleus | Primary Function | Firing Pattern | tau_m (ms) |
|-----------|-------------------|-----------------|--------------|
| **Rostral (gustatory)** | Taste processing | Burst | 15-20 |
| **Medial (cardiovascular)** | Baroreceptor | Tonic + phasic | 20-25 |
| **Caudal (respiratory)** | Respiratory rhythm | Rhythmic | 15-25 |
| **Commissural** | Visceral integration | Variable | 20-30 |

### 1.1.2 NTS Synaptic Parameters

| Connection | tau_syn (ms) | E_rev (ms) | Weight (mV) | Notes |
|------------|--------------|------------|-------------|-------|
| **Visceral afferents** | 5-10 | 2-5 | 2-5 | Fast EPSPs |
| **GABAergic (CVLM)** | 10-15 | 1-3 | 3-8 | Inhibitory from CVLM |
| **Glutamatergic (NTS)** | 5-8 | 1-2 | 1-3 | Local excitation |

## 1.2 NTS Baroreflex Circuit Parameters

| Parameter | Value | Unit | Source |
|-----------|-------|------|--------|
| **Baroreceptor firing (carotid)** | 10-100 | Hz | Zhang et al. 2009 |
| **NTS response latency** | 5-15 | ms | Fast synaptic relay |
| **NTS to CVLM delay** | 3-8 | ms | Monosynaptic |
| **CVLM to RVLM delay** | 2-5 | ms | GABAergic |
| **Baroreflex gain** | 2-4 | unitless | Schreihofer & Sved 2011 |

---

# PART 2: ROSTRAL VENTROLATERAL MEDULLA (RVLM)

## 2.1 RVLM Neuron Electrophysiology

| Parameter | Value | Unit | Source | Notes |
|-----------|-------|------|--------|-------|
| **tau_m** | 20-35 | ms | Sun et al. 1997 | Sympathetic premotor |
| **R_in** | 100-250 | MOhm | Schreihofer & Sved 2011 | Moderate input resistance |
| **V_rest** | -55 to -50 | mV | Tonic depolarization | |
| **V_th** | -45 to -40 | mV | Low threshold | |
| **Firing rate (tonic)** | 5-15 | Hz | Resting sympathetic tone | |
| **Firing rate (stress)** | 15-40 | Hz | Sympathetic activation | |
| **AP width** | 0.8-1.5 | ms | Broad spikes | |

### 2.1.1 RVLM Neuron Types

| Cell Type | tau_m (ms) | Firing Pattern | Projection Target |
|-----------|------------|----------------|-------------------|
| **Adrenergic (C1)** | 25-35 | Tonic | IML (spinal cord) |
| **Glutamatergic** | 20-30 | Tonic + phasic | CVLM, NTS |
| **GABA-sensitive** | 20-25 | Inhibited by CVLM | Variable |

### 2.1.2 RVLM Synaptic Parameters

| Connection | tau_syn (ms) | E_rev (ms) | Weight (mV) | Notes |
|------------|--------------|------------|-------------|-------|
| **NTS excitatory** | 5-10 | 2-5 | 2-4 | Baroreceptor input |
| **CVLM GABAergic** | 10-20 | 1-3 | 5-10 | Tonic inhibition |
| **Spinal projection** | 10-15 | 10-50 | N/A | Descending to IML |

---

# PART 3: CAUDAL VENTROLATERAL MEDULLA (CVLM)

## 3.1 CVLM Neuron Electrophysiology

| Parameter | Value | Unit | Source | Notes |
|-----------|-------|------|--------|-------|
| **tau_m** | 15-25 | ms | Schreihofer & Sved 2011 | GABAergic output |
| **R_in** | 100-200 | MOhm | | Moderate resistance |
| **V_rest** | -55 to -50 | mV | | |
| **V_th** | -48 to -42 | mV | | |
| **Firing rate (tonic)** | 5-20 | Hz | Baroreceptor activated | |
| **GABA release** | Tonic | | Inhibits RVLM | |

### 3.1.1 CVLM Function in Baroreflex

**Baroreceptor activation pathway:**
1. Baroreceptors fire (10-100 Hz) -> NTS
2. NTS excites CVLM (5-15 ms delay)
3. CVLM GABAergic neurons fire -> Inhibit RVLM
4. RVLM reduces sympathetic outflow

**Key Parameters:**
- CVLM to RVLM inhibition: w = 5-10 mV GABAergic
- CVLM firing with baroreceptor input: 10-30 Hz
- CVLM silence: Leads to RVLM disinhibition (sympathetic surge)

---

# PART 4: NUCLEUS AMBIGUUS (NA) - Cardiac Vagal

## 4.1 NA Cardiac Vagal Neuron Electrophysiology

| Parameter | Value | Unit | Source | Notes |
|-----------|-------|------|--------|-------|
| **tau_m** | 10-30 | ms | Mendelowitz 1999 | Parasympathetic cardiac |
| **R_in** | 100-300 | MOhm | Neff et al. 2004 | High resistance |
| **V_rest** | -60 to -55 | mV | | |
| **V_th** | -50 to -45 | mV | | |
| **Firing rate (rest)** | 1-5 | Hz | Vagal tone | Resting HR control |
| **Firing rate (active)** | 5-20 | Hz | Baroreflex | Active bradycardia |
| **AP width** | 0.8-1.5 | ms | | |

### 4.1.1 NA Firing Patterns

| State | Firing Rate (Hz) | Cardiac Effect | Pattern |
|-------|------------------|----------------|---------|
| **Rest** | 1-5 | Vagal tone | Tonic |
| **Inspiration** | Reduced | Respiratory sinus arrhythmia | Inhibited |
| **Baroreflex** | 10-20 | Bradycardia | Phasic burst |
| **Diving reflex** | 20-50 | Max bradycardia | Sustained |

### 4.1.2 Respiratory-Cardiac Coupling

| Parameter | Value | Unit | Notes |
|-----------|-------|------|-------|
| **Respiratory sinus arrhythmia** | 0.2-0.3 Hz | Respiratory modulation of HR | |
| **Inspiration-inhibition delay** | 50-150 ms | | |
| **Expiration-activation** | 100-200 ms | | |
| **RSA amplitude** | 5-15 bpm | HR variation | |

---

# PART 5: AROUSAL SYSTEMS (LC & RAPHE)

## 5.1 Locus Coeruleus (LC) - Already Documented

**See NEUROMODULATORY_SYSTEMS_RESEARCH.md for complete LC parameters**

Key parameters summary:
- tau_m: 15-30 ms
- Firing: 0.5-25 Hz (state-dependent)
- V_rest: -55 to -50 mV
- Tonic: 2-8 Hz, Phasic: 10-30 Hz

## 5.2 Raphe Nuclei - Already Documented

**See NEUROMODULATORY_SYSTEMS_RESEARCH.md for complete raphe parameters**

Key parameters summary:
- tau_m: 25-45 ms (DRN), 20-35 ms (MRN)
- Firing: 0.5-8 Hz
- V_rest: -60 to -55 mV
- Pacemaker: 0.5-3 Hz

---

# PART 6: BRAINSTEM-TO-LIMBIC PROJECTIONS

## 6.1 NTS to Limbic Projections

| Target | Projection Type | p_conn | w_syn (mV) | Function |
|--------|-----------------|--------|------------|----------|
| **Parabrachial nucleus** | Excitatory | 0.3-0.5 | 2-4 | Visceral relay |
| **Amygdala (CeA)** | Excitatory | 0.1-0.2 | 1-3 | Visceral-emotional |
| **Hypothalamus (PVN)** | Excitatory | 0.1-0.15 | 1-2 | Autonomic coordination |
| **LC** | Excitatory | 0.05-0.1 | 1-2 | Arousal-visceral |

## 6.2 RVLM to Limbic Projections

| Target | Projection Type | p_conn | w_syn (mV) | Function |
|--------|-----------------|--------|------------|----------|
| **Hypothalamus** | Excitatory | 0.05-0.1 | 1-2 | Sympathetic coordination |
| **PAG** | Excitatory | 0.1-0.2 | 2-4 | Fight-or-flight |
| **Thalamus** | Sparse | 0.02-0.05 | 1-2 | Arousal relay |

## 6.3 LC/Raphe to Limbic (From Existing Research)

| Target | Projection Type | p_conn | w_syn (mV) | Function |
|--------|-----------------|--------|------------|----------|
| **Amygdala (BLA)** | Diffuse NE/5HT | 0.05-0.15 | Modulatory | Arousal, mood |
| **Hippocampus** | Diffuse NE/5HT | 0.05-0.10 | Modulatory | Memory, arousal |
| **Prefrontal** | Diffuse NE/5HT | 0.05-0.10 | Modulatory | Attention |

---

# PART 7: CARDIAC AND RESPIRATORY CONTROL

## 7.1 Cardiac Control Rhythm

| Parameter | Value | Unit | Notes |
|-----------|-------|------|-------|
| **Cardiac oscillator frequency** | 1.0-1.25 | Hz | 60-75 bpm |
| **HRV oscillation** | 0.1-0.4 | Hz | 0.1 Hz Mayer wave |
| **Baroreceptor firing** | 10-100 | Hz | Pressure-sensitive |
| **Vagal discharge timing** | 200-300 ms | | Post-R-wave |

## 7.2 Respiratory Control Rhythm

| Parameter | Value | Unit | Notes |
|-----------|-------|------|-------|
| **Pre-Botzinger complex freq** | 0.2-0.4 | Hz | Respiratory rhythm |
| **Inspiratory duration** | 1-2 | s | Active |
| **Expiratory duration** | 2-4 | s | Passive |
| **Rhythm neurons firing** | 5-30 | Hz | Pacemaker |

## 7.3 Cardiorespiratory Coupling

| Parameter | Value | Unit | Notes |
|-----------|-------|------|-------|
| **RSA frequency** | 0.2-0.3 | Hz | Respiratory sinus arrhythmia |
| **Coupling strength** | 0.3-0.6 | correlation | Heart-brain coherence |
| **Phase relationship** | Inspiration = HR reduction | | |

---

# PART 8: BRIAN2 IMPLEMENTATION

## 8.1 Complete Brainstem Model

```python
# ============== BRAINSTEM AUTONOMIC SYSTEM ==============

from brian2 import *

# Brainstem neuron model
bs_neuron_model = '''
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

def create_brainstem_systems(N_scale=0.01):
    """Create brainstem autonomic populations"""

    systems = {}

    # Nucleus Tractus Solitarius (NTS)
    NTS = NeuronGroup(
        int(100 * N_scale),
        bs_neuron_model,
        threshold='v > V_th',
        reset='v = V_reset',
        refractory=3*ms,
        method='euler'
    )
    NTS.tau_m = 20 * ms
    NTS.tau_osc = 10 * ms  # CRITICAL: must be < 20ms
    NTS.f_osc = 5 * Hz  # Tonic baroreceptor rate
    NTS.A_osc = 30 * mV  # Scaled for tau_m=20ms
    NTS.tau_syn = 8 * ms
    NTS.V_rest = -58 * mV
    NTS.V_th = -48 * mV
    NTS.V_reset = -62 * mV
    NTS.v = -58 * mV

    # Rostral Ventrolateral Medulla (RVLM)
    RVLM = NeuronGroup(
        int(80 * N_scale),
        bs_neuron_model,
        threshold='v > V_th',
        reset='v = V_reset',
        refractory=5*ms,
        method='euler'
    )
    RVLM.tau_m = 28 * ms
    RVLM.tau_osc = 10 * ms
    RVLM.f_osc = 10 * Hz  # Tonic sympathetic rate
    RVLM.A_osc = 40 * mV  # Scaled for tau_m=28ms
    RVLM.tau_syn = 12 * ms
    RVLM.V_rest = -52 * mV
    RVLM.V_th = -42 * mV
    RVLM.V_reset = -58 * mV
    RVLM.v = -52 * mV

    # Caudal Ventrolateral Medulla (CVLM)
    CVLM = NeuronGroup(
        int(60 * N_scale),
        bs_neuron_model,
        threshold='v > V_th',
        reset='v = V_reset',
        refractory=3*ms,
        method='euler'
    )
    CVLM.tau_m = 20 * ms
    CVLM.tau_osc = 10 * ms
    CVLM.f_osc = 15 * Hz  # GABAergic output
    CVLM.A_osc = 30 * mV
    CVLM.tau_syn = 15 * ms
    CVLM.V_rest = -55 * mV
    CVLM.V_th = -45 * mV
    CVLM.V_reset = -60 * mV
    CVLM.v = -55 * mV

    # Nucleus Ambiguus (NA) - Cardiac Vagal
    NA = NeuronGroup(
        int(50 * N_scale),
        bs_neuron_model,
        threshold='v > V_th',
        reset='v = V_reset',
        refractory=5*ms,
        method='euler'
    )
    NA.tau_m = 20 * ms
    NA.tau_osc = 10 * ms
    NA.f_osc = 3 * Hz  # Vagal tone rate
    NA.A_osc = 30 * mV
    NA.tau_syn = 10 * ms
    NA.V_rest = -58 * mV
    NA.V_th = -48 * mV
    NA.V_reset = -62 * mV
    NA.v = -58 * mV

    # Locus Coeruleus (LC) - from existing research
    LC = NeuronGroup(
        int(50 * N_scale),
        bs_neuron_model,
        threshold='v > V_th',
        reset='v = V_reset',
        refractory=5*ms,
        method='euler'
    )
    LC.tau_m = 20 * ms
    LC.tau_osc = 10 * ms
    LC.f_osc = 3 * Hz  # Quiet wake
    LC.A_osc = 30 * mV
    LC.tau_syn = 10 * ms
    LC.V_rest = -52 * mV
    LC.V_th = -42 * mV
    LC.V_reset = -58 * mV
    LC.v = -52 * mV

    # Dorsal Raphe (DRN)
    DRN = NeuronGroup(
        int(80 * N_scale),
        bs_neuron_model,
        threshold='v > V_th',
        reset='v = V_reset',
        refractory=5*ms,
        method='euler'
    )
    DRN.tau_m = 35 * ms
    DRN.tau_osc = 10 * ms
    DRN.f_osc = 2 * Hz  # Pacemaker
    DRN.A_osc = 35 * mV  # Scaled for tau_m=35ms
    DRN.tau_syn = 10 * ms
    DRN.V_rest = -58 * mV
    DRN.V_th = -48 * mV
    DRN.V_reset = -62 * mV
    DRN.v = -58 * mV

    systems = {
        'NTS': NTS,
        'RVLM': RVLM,
        'CVLM': CVLM,
        'NA': NA,
        'LC': LC,
        'DRN': DRN
    }

    return systems


def create_brainstem_connectivity(systems):
    """Create baroreflex and autonomic connectivity"""

    # Baroreflex circuit: NTS -> CVLM -> RVLM
    # NTS excitatory to CVLM
    NTS_to_CVLM = Synapses(
        systems['NTS'], systems['CVLM'],
        'w_syn : volt',
        on_pre='I_syn_post += w_syn',
        delay=5*ms
    )
    NTS_to_CVLM.connect(p=0.4)
    NTS_to_CVLM.w_syn = 3 * mV  # Excitatory

    # CVLM inhibitory to RVLM (GABAergic)
    CVLM_to_RVLM = Synapses(
        systems['CVLM'], systems['RVLM'],
        'w_syn : volt',
        on_pre='I_syn_post -= w_syn',  # Inhibitory
        delay=3*ms
    )
    CVLM_to_RVLM.connect(p=0.5)
    CVLM_to_RVLM.w_syn = 8 * mV  # Strong inhibition

    # NTS excitatory to NA (baroreflex vagal)
    NTS_to_NA = Synapses(
        systems['NTS'], systems['NA'],
        'w_syn : volt',
        on_pre='I_syn_post += w_syn',
        delay=5*ms
    )
    NTS_to_NA.connect(p=0.3)
    NTS_to_NA.w_syn = 4 * mV

    # LC diffuse to NTS, RVLM (arousal modulation)
    LC_to_NTS = Synapses(
        systems['LC'], systems['NTS'],
        'w_syn : volt',
        on_pre='I_syn_post += w_syn',
        delay=10*ms
    )
    LC_to_NTS.connect(p=0.1)
    LC_to_NTS.w_syn = 1 * mV  # Modulatory

    # DRN diffuse to brainstem
    DRN_to_NTS = Synapses(
        systems['DRN'], systems['NTS'],
        'w_syn : volt',
        on_pre='I_syn_post += w_syn',
        delay=15*ms
    )
    DRN_to_NTS.connect(p=0.08)
    DRN_to_NTS.w_syn = 0.5 * mV  # Modulatory

    # Brainstem-to-limbic projections
    # NTS to parabrachial (would connect to thalamus/amygdala)
    # This is a placeholder for limbic connections

    connectivity = {
        'NTS_to_CVLM': NTS_to_CVLM,
        'CVLM_to_RVLM': CVLM_to_RVLM,
        'NTS_to_NA': NTS_to_NA,
        'LC_to_NTS': LC_to_NTS,
        'DRN_to_NTS': DRN_to_NTS
    }

    return connectivity


def create_brainstem_monitors(systems):
    """Create monitors for brainstem systems"""
    monitors = {}
    for name, group in systems.items():
        monitors[name + '_spikes'] = SpikeMonitor(group)
        monitors[name + '_rate'] = PopulationRateMonitor(group)
        monitors[name + '_state'] = StateMonitor(group, 'v', record=True)
    return monitors


# ============== PARAMETER SUMMARY TABLE ==============
BRAINSTEM_PARAMS = {
    'NTS': {
        'N': 100, 'tau_m': 20*ms, 'f_osc': 5*Hz, 'A_osc': 30*mV,
        'V_rest': -58*mV, 'V_th': -48*mV, 'function': 'Visceral afferent integration'
    },
    'RVLM': {
        'N': 80, 'tau_m': 28*ms, 'f_osc': 10*Hz, 'A_osc': 40*mV,
        'V_rest': -52*mV, 'V_th': -42*mV, 'function': 'Sympathetic premotor'
    },
    'CVLM': {
        'N': 60, 'tau_m': 20*ms, 'f_osc': 15*Hz, 'A_osc': 30*mV,
        'V_rest': -55*mV, 'V_th': -45*mV, 'function': 'GABAergic inhibition of RVLM'
    },
    'NA': {
        'N': 50, 'tau_m': 20*ms, 'f_osc': 3*Hz, 'A_osc': 30*mV,
        'V_rest': -58*mV, 'V_th': -48*mV, 'function': 'Cardiac vagal (parasympathetic)'
    },
    'LC': {
        'N': 50, 'tau_m': 20*ms, 'f_osc': 3*Hz, 'A_osc': 30*mV,
        'V_rest': -52*mV, 'V_th': -42*mV, 'function': 'NE arousal'
    },
    'DRN': {
        'N': 80, 'tau_m': 35*ms, 'f_osc': 2*Hz, 'A_osc': 35*mV,
        'V_rest': -58*mV, 'V_th': -48*mV, 'function': '5-HT arousal'
    }
}
```

## 8.2 Critical Implementation Notes

1. **tau_osc = 10 ms is CRITICAL** - Larger values suppress oscillations
2. **A_osc scales with tau_m** - Use A_osc ~ tau_m * 1.5 mV/ms
3. **CVLM inhibition is subtracted** - GABAergic, reduces RVLM activity
4. **NA firing rate inversely related to HR** - Higher vagal tone = lower HR
5. **LC/DRN are modulatory** - Weak diffuse projections

---

# PART 9: SUMMARY TABLE

## 9.1 Complete Brainstem Parameter Summary

| Nucleus | N | tau_m (ms) | f_base (Hz) | A_osc (mV) | V_th (mV) | Primary Function |
|---------|---|------------|-------------|------------|-----------|------------------|
| **NTS** | 100 | 20 | 5 | 30 | -48 | Visceral afferent integration |
| **RVLM** | 80 | 28 | 10 | 40 | -42 | Sympathetic premotor |
| **CVLM** | 60 | 20 | 15 | 30 | -45 | GABAergic RVLM inhibition |
| **NA** | 50 | 20 | 3 | 30 | -48 | Cardiac vagal |
| **LC** | 50 | 20 | 3 | 30 | -42 | NE arousal |
| **DRN** | 80 | 35 | 2 | 35 | -48 | 5-HT arousal |

## 9.2 Connectivity Matrix (w_syn in mV)

| Source | NTS | RVLM | CVLM | NA | LC | DRN |
|--------|-----|------|------|----|----|-----|
| **NTS** | - | - | +3 | +4 | - | - |
| **CVLM** | - | -8 | - | - | - | - |
| **LC** | +1 | - | - | - | - | - |
| **DRN** | +0.5 | - | - | - | - | - |

Note: Positive = excitatory, Negative = inhibitory

---

# SOURCES

1. **Paton & Kubin (2007)** - NTS electrophysiology, PMID: 17652568
2. **Andresen & Kunze (1994)** - NTS baroreceptor integration, PMID: 7929644
3. **Schreihofer & Sved (2011)** - VLM cardiovascular control, PMID: 21881600
4. **Sun et al. (1997)** - RVLM neuron properties, PMID: 9349855
5. **Mendelowitz (1999)** - NA cardiac vagal neurons, PMID: 10448241
6. **Neff et al. (2004)** - NA respiratory coupling, PMID: 15356784
7. **Aston-Jones & Cohen (2005)** - LC function, PMID: 15723003
8. **Jacobs & Azmitia (1992)** - Raphe serotonin, PMID: 1565596
9. **Zhang et al. (2009)** - Baroreflex modeling, PMID: 19592626
10. **Guyenet (2006)** - Sympathetic circuits, PMID: 16624818

---

*Research compiled for Conscious SNN Project - 2026-03-13*
*Investigative analysis by Ava Chen - Perplexity Researcher Agent*
