# Brian2 Implementation Research
## Numerical Stability, Integration Methods, and Production Patterns

**Compiled:** 2026-03-13
**Purpose:** Technical implementation guide for Conscious SNN project

---

# PART 1: NaN DEBUGGING IN BRIAN2

## 1.1 Three Critical NaN Sources

| Source | Mechanism | Prevention |
|--------|-----------|------------|
| **Exponential overflow** | exp((v-V_T)/delta_T) > exp(709.78) | Clip argument to [-50, 50] |
| **Current accumulation** | PoissonInput without bounds | Add run_regularly clamping |
| **Integration instability** | exponential_euler with oscillatory terms | Use method='euler' |

## 1.2 Dual-Layer Clamping Strategy (Production Standard)

```python
# Layer 1: Inline clipping in equations (prevents overflow during integration)
model='''
dv/dt = (v_rest - v + Delta_T * exp(clip((v-V_T)/Delta_T, -50, 50)) + I_syn) / tau_m : volt
dI_syn/dt = -I_syn / tau_syn : volt
'''

# Layer 2: Post-step clamping (catches any remaining excursions)
group.run_regularly('''
v = clip(v, -80*mV, -30*mV)
I_syn = clip(I_syn, -20*mV, 20*mV)
''', dt=1*ms)
```

## 1.3 Safe PoissonInput Weight Formula

```python
# Weight scales inversely with input count to prevent accumulation
# Formula: weight = base_weight / (N_inputs * rate * dt)
# Safe range: 1-3 mV maximum

N_inputs = 100
rate = 100 * Hz
dt_sim = 0.1 * ms

safe_weight = 1 * mV / (N_inputs * rate * dt_sim)
safe_weight = min(safe_weight, 3 * mV)  # Cap at 3mV
```

---

# PART 2: INTEGRATION METHODS

## 2.1 Method Comparison

| Method | Order | Stability Region | Cost/Step | Best For |
|--------|-------|------------------|-----------|----------|
| **euler** | 1 | Circle radius 1 | 1x | Simple systems, oscillatory |
| **exponential_euler** | 1 | Exact for linear | 1.2x | AdEx WITHOUT oscillatory drive |
| **rk2** | 2 | Ellipse to ~2i | 2x | Moderate accuracy |
| **rk4** | 4 | Radius ~2.78 | 4x | High accuracy, oscillatory |
| **gsl_rkf45** | 4(5) | Adaptive | 3-10x | Stiff problems, long runs |

## 2.2 Critical Brian2 Bug #626

**Issue:** `exponential_euler` fails with oscillatory driving terms (sin, cos)

**Solution:** Use `method='euler'` for systems with oscillatory drive

**Reference:** https://github.com/brian-team/brian2/issues/626

## 2.3 Method Recommendations by Simulation Duration

| Duration | Primary Method | Backup | dt |
|----------|----------------|--------|-----|
| 1 second | exponential_euler | euler | 0.1 ms |
| 5 seconds | exponential_euler | gsl_rkf45 | 0.05 ms |
| 10 seconds | gsl_rkf45 | exponential_euler | adaptive |

**For conscious_snn:** All systems use oscillatory drive → MUST use `method='euler'`

---

# PART 3: ADEX EXPONENTIAL STABILITY

## 3.1 Overflow Mathematics

```
Float64 overflow: exp(709.78) = infinity
Float32 overflow: exp(88.72) = infinity

For Delta_T = 2 mV, V_T = -50.4 mV:
Overflow at v > V_T + 709.78 * Delta_T = -50.4 + 1419.56 = 1369 mV
```

**Conclusion:** Overflow is far above biological range (-80 to -30 mV). Clipping prevents edge cases.

## 3.2 Safe Delta_T Values

| Delta_T | Overflow Voltage | Stability Risk |
|---------|-----------------|----------------|
| 0.5 mV | v > V_T + 355 mV | HIGH |
| 2.0 mV | v > V_T + 1420 mV | Low (recommended) |
| 5.0 mV | v > V_T + 3549 mV | Very Low |

## 3.3 AdEx Parameters (Safe Ranges)

| Parameter | Safe Range | Notes |
|-----------|------------|-------|
| Delta_T | 1-5 mV | 2 mV optimal |
| V_T | -55 to -45 mV | Threshold |
| V_peak | -30 to -20 mV | Well below overflow |
| tau_m | 10-50 ms | Determines A_osc need |
| exp argument clip | [-50, 50] | Prevents overflow |

---

# PART 4: PRODUCTION CODE PATTERNS

## 4.1 NaN-Proof AdEx Template

```python
from brian2 import NeuronGroup, ms, mV, nA, run

# NaN-proof AdEx implementation
adex_neuron = NeuronGroup(
    N,
    model='''
    dv/dt = (v_rest - v + Delta_T * exp(clip((v-V_T)/Delta_T, -50, 50)) + I_syn + I_osc) / tau_m : volt (unless refractory)
    dI_syn/dt = -I_syn / tau_syn : volt
    dI_osc/dt = (-I_osc + A_osc * sin(2*pi*f_osc*t)) / tau_osc : volt
    Delta_T : volt
    V_T : volt
    tau_m : second
    tau_syn : second
    tau_osc : second
    f_osc : Hz
    A_osc : volt
    v_rest : volt
    ''',
    threshold='v > V_peak',
    reset='v = v_reset',
    refractory=5*ms,
    method='euler',  # MUST use euler for oscillatory systems
    name='adex_population'
)

# Set parameters
adex_neuron.Delta_T = 2 * mV
adex_neuron.V_T = -50.4 * mV
adex_neuron.tau_m = 20 * ms
adex_neuron.tau_syn = 10 * ms
adex_neuron.tau_osc = 10 * ms  # CRITICAL: < 20ms
adex_neuron.f_osc = 10 * Hz
adex_neuron.A_osc = 30 * mV  # Scaled for tau_m=20ms
adex_neuron.v_rest = -65 * mV
adex_neuron.v = -65 * mV
adex_neuron.I_syn = 0 * mV
adex_neuron.I_osc = 0 * mV

# POST-STEP CLAMPING (Critical for NaN prevention)
adex_neuron.run_regularly('''
v = clip(v, -80*mV, -30*mV)
I_syn = clip(I_syn, -20*mV, 20*mV)
I_osc = clip(I_osc, -15*mV, 15*mV)
''', dt=1*ms)
```

## 4.2 Safe Synapse Pattern

```python
from brian2 import Synapses

syn = Synapses(
    source, target,
    model='w_syn : volt',
    on_pre='I_syn_post += w_syn',
    delay=2*ms,
    name='safe_synapse'
)

# Safe weight range
syn.connect(p=0.2)
syn.w_syn = 2 * mV  # 1-5 mV safe range
```

## 4.3 Safe PoissonInput Pattern

```python
from brian2 import PoissonGroup, Synapses

poisson_input = PoissonGroup(N, rate=rate)
poisson_to_neuron = Synapses(
    poisson_input, neuron,
    on_pre='I_syn_post += w_in',
    name='poisson_drive'
)
poisson_to_neuron.connect(p=1.0)

# Safe weight calculation
w_in = min(1 * mV / (N * rate * dt), 3 * mV)
poisson_to_neuron.w_in = w_in
```

---

# PART 5: A_OSC SCALING LAW

## 5.1 Discovery

From testing and production code analysis:

**A_osc scales with tau_m: A_osc ≈ tau_m * 1.5**

| tau_m (ms) | Minimum A_osc (mV) | Recommended A_osc (mV) |
|------------|-------------------|------------------------|
| 10 | 15 | 20 |
| 15 | 22 | 25 |
| 20 | 30 | 30-35 |
| 25 | 37 | 35-40 |
| 30 | 45 | 45-50 |
| 35 | 52 | 50-55 |

## 5.2 tau_osc Constraint

**CRITICAL: tau_osc MUST be < 20ms, preferably 10ms**

| tau_osc (ms) | Result |
|--------------|--------|
| 5 | Works ✅ |
| 10 | Works ✅ |
| 15 | Marginal |
| 20 | Fails ❌ |
| 50 | Fails ❌ |

---

# PART 6: THALAMUS STABILITY

## 6.1 Reticular Inhibition Balance

From testing (DEBUGGING_THALAMUS_20260313.md):

| w_syn | p_conn | Relay Hz | Status |
|-------|--------|----------|--------|
| 8 mV | 0.3 | 1.0 | Suppressed ❌ |
| 8 mV | 0.1 | 4.6 | Partial |
| 4 mV | 0.3 | 1.9 | Partial |
| 2 mV | 0.1 | 10.0 | Correct ✅ |

**Production setting:** w_syn=2mV, p_conn=0.1

## 6.2 Thalamus Parameters (Corrected)

| Population | tau_m | A_osc | f_osc | tau_osc |
|------------|-------|-------|-------|---------|
| Relay nuclei | 20ms | 30mV | 10Hz | 10ms |
| Reticular | 15ms | 25mV | 10Hz | 10ms |
| Intralaminar | 25ms | 35mV | 10Hz | 10ms |

---

# PART 7: RECOMMENDED CHANGES FOR CONSCIOUS_SNN

## 7.1 Integration Method

All neuron groups should use `method='euler'` due to oscillatory drive.

**Status:** Already implemented ✅

## 7.2 tau_osc Values

All systems should have `tau_osc = 10*ms` (not 50ms).

**Status:** Fixed in thalamus.py ✅, verify other systems

## 7.3 A_osc Values

| System | Current | Should Be | Status |
|--------|---------|-----------|--------|
| Thalamus relay | 30mV | 30mV | ✅ |
| Thalamus reticular | 25mV | 25mV | ✅ |
| Thalamus intralaminar | 35mV | 35mV | ✅ |
| Limbic BLA | 35mV | 35-40mV | ⚠️ Check tau_m |
| Hippocampus EC | 30mV | 30mV | ✅ |
| Hippocampus CA1 | 35mV | 40mV | ⚠️ tau_m=30ms |
| DMN PCC | 35mV | 35mV | ✅ |
| DMN mPFC | 40mV | 40mV | ✅ |
| DMN hippocampal | 50mV | 50mV | ✅ |

## 7.4 Clamping

All populations should have `run_regularly` clamping.

**Status:** Implemented in thalamus.py, verify other systems

---

# PART 8: TESTING PATTERNS

## 8.1 Unit Test Template

```python
import pytest
from brian2 import start_scope, run, ms, mV, Hz

@pytest.mark.standalone_compatible
def test_adex_no_nan():
    """Test that AdEx neuron doesn't produce NaN over 1 second."""
    start_scope()

    neuron = create_adex_neuron(N=10)
    monitor = SpikeMonitor(neuron)

    run(1000*ms)

    # Check no NaN in membrane potential
    assert not np.isnan(neuron.v[:]).any()

    # Check firing rate is reasonable
    rate = monitor.num_spikes / 10
    assert 0.1 * Hz < rate < 100 * Hz
```

## 8.2 Isolation Testing

When debugging NaN, test each system in isolation:

```python
# Test thalamus alone
start_scope()
thalamus = ThalamusSystem(n_neurons=100)
thalamus.build()
run(1000*ms)
# Check for NaN, firing rates
```

---

# REFERENCES

1. Brette & Gerstner (2005) - Adaptive Exponential IF Model
2. Brian2 Documentation v2.10.1 - Numerical Integration
3. Brian2 GitHub Issue #626 - exponential_euler with oscillatory terms
4. IEEE 754-2019 - Floating-point overflow thresholds
5. Neuronal Dynamics (Gerstner et al.) - Chapter 5.2
6. Production code: brian-team/brian2, Poirazi-Lab/dendrify

---

*Compiled for Conscious SNN Project - 2026-03-13*
