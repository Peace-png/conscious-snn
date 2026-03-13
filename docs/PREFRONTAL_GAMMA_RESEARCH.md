# Prefrontal Gamma Oscillations Research
## PING Mechanism and Brian2 Implementation

**Compiled:** 2026-03-13

---

# PART 1: GAMMA FREQUENCY RANGES

| Band | Frequency | Mechanism | Function |
|------|-----------|-----------|----------|
| **Low Gamma** | 30-50 Hz | GABA-A mediated | Working memory maintenance |
| **High Gamma** | 50-100 Hz | May involve gap junctions | Feature binding, attention |

---

# PART 2: PING MECHANISM

## 2.1 Core Circuit

```
Pyramidal cells --[AMPA/NMDA]--> Interneurons --[GABA-A]--> Pyramidal cells
```

## 2.2 Temporal Dynamics

1. Pyramidal cells fire, excite interneurons
2. Interneurons activate after ~1-2 ms delay
3. GABA-A inhibition suppresses pyramidal cells for 10-20 ms
4. Pyramidal cells recover, fire again
5. Cycle repeats at gamma frequency

## 2.3 Frequency Determination

```
f_gamma ≈ 1 / (2 * tau_GABA) where tau_GABA = 5-10 ms
```

---

# PART 3: NEURON PARAMETERS

## 3.1 Pyramidal Neurons (Layer 2/3 and Layer 5)

| Parameter | Value | Unit | Notes |
|-----------|-------|------|-------|
| **tau_m** | 15-30 | ms | Higher than sensory cortex |
| **C_m** | 200-300 | pF | |
| **g_L** | 5-15 | nS | |
| **E_L** | -70 to -65 | mV | |
| **V_th** | -50 to -45 | mV | |
| **V_reset** | -65 to -60 | mV | |
| **tau_ref** | 2-3 | ms | |
| **Adaptation tau** | 50-200 | ms | Strong in PFC |

## 3.2 Fast-Spiking PV+ Interneurons

| Parameter | Value | Unit | Notes |
|-----------|-------|------|-------|
| **tau_m** | 5-15 | ms | Much faster than pyramidal |
| **C_m** | 100-200 | pF | Smaller cells |
| **g_L** | 10-30 | nS | Higher conductance |
| **V_th** | -52 to -48 | mV | Lower threshold |
| **V_reset** | -65 to -55 | mV | |
| **tau_ref** | 0.5-2 | ms | Very short |
| **No adaptation** | -- | -- | PV cells show little |

---

# PART 4: SYNAPTIC PARAMETERS

## 4.1 GABAergic Synapses

| Parameter | Value | Unit |
|-----------|-------|------|
| **E_GABA** | -75 to -70 | mV |
| **tau_rise_GABA** | 0.5-1.0 | ms |
| **tau_decay_GABA** | 5-10 | ms |
| **g_GABA_max** | 1-5 | nS |

## 4.2 AMPA Synapses

| Parameter | Value | Unit |
|-----------|-------|------|
| **E_AMPA** | 0 | mV |
| **tau_rise_AMPA** | 0.2-0.5 | ms |
| **tau_decay_AMPA** | 2-5 | ms |
| **g_AMPA_max** | 0.5-2 | nS |

---

# PART 5: WORKING MEMORY GAMMA

| Measure | Value | Notes |
|---------|-------|-------|
| **Gamma power increase** | 30-100% | During maintenance |
| **Load-dependent increase** | Linear with items | Up to capacity |
| **Memory capacity** | 4-7 items | Correlates with gamma |
| **Delay duration** | 1-10 seconds | Sustained gamma |

---

# PART 6: THETA-GAMMA COUPLING

## 6.1 Phase-Amplitude Coupling

| Parameter | Value |
|-----------|-------|
| **Theta frequency** | 4-8 Hz |
| **Gamma frequency** | 30-100 Hz |
| **Preferred theta phase** | 120-180 degrees |
| **Modulation Index** | 0.01-0.1 |

## 6.2 Implementation

```python
Gamma_power(t) = Gamma_base * (1 + MI * cos(2*pi*f_theta*t + phi))
```

---

# PART 7: BRIAN2 IMPLEMENTATION

```python
# ============== PREFRONTAL PING PARAMETERS ==============

# Pyramidal neurons
N_E = 800
tau_m_E = 20*ms
C_m_E = 250*pF
g_L_E = C_m_E / tau_m_E
E_L_E = -70*mV
V_th_E = -50*mV
V_reset_E = -60*mV
tau_ref_E = 2*ms

# Interneurons
N_I = 200
tau_m_I = 10*ms
C_m_I = 150*pF
g_L_I = C_m_I / tau_m_I
E_L_I = -70*mV
V_th_I = -50*mV
V_reset_I = -55*mV
tau_ref_I = 1*ms

# Synapse parameters (CRITICAL for gamma timing)
tau_AMPA = 5*ms
tau_GABA = 10*ms         # Key for gamma frequency
E_AMPA = 0*mV
E_GABA = -75*mV

# Connectivity
p_EI = 0.5               # E to I
p_IE = 0.5               # I to E
p_EE = 0.1               # E to E (weak)
p_II = 0.3               # I to I

# Synaptic weights (ASYYMMETRIC - critical for PING)
w_EI = 0.5*nS            # E to I
w_IE = 2.0*nS            # I to E (STRONGER)
w_EE = 0.1*nS            # E to E (weak)
w_II = 0.5*nS            # I to I

# E/I ratio
# 800 pyramidal : 200 interneurons = 4:1

# Connectivity implementation
S_EI = Synapses(P, I, 'w: siemens', on_pre='I_AMPA_post += w')
S_EI.connect(p=p_EI)
S_EI.w = w_EI

S_IE = Synapses(I, P, 'w: siemens', on_pre='I_GABA_post += w')
S_IE.connect(p=p_IE)
S_IE.w = w_IE            # STRONGER for gamma generation
```

---

# PART 8: KEY INSIGHTS

1. **GABA tau 5-10 ms is CRITICAL** - determines gamma frequency
2. **Asymmetric weights** - w_IE >> w_EI (4x stronger inhibition)
3. **E/I ratio ~4:1** - 800 E to 200 I
4. **Network size** - 1000+ neurons for clean oscillations
5. **Add adaptation** to PFC pyramidal cells to prevent runaway

---

*Compiled for Conscious SNN Project - 2026-03-13*
