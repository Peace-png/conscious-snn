# Research Report: AdEx Numerical Stability - Quantitative Analysis

## Query Analysis

This research addresses eight strategic sub-questions:

1. Mathematical analysis of exp() overflow in AdEx models
2. Clamping strategies for exponential term: exp((v-VT)/DeltaT)
3. Maximum safe values for DeltaT parameter
4. Threshold for overflow: what v values cause exp() to exceed float limits
5. Comparative stability of different integration methods for AdEx
6. Papers on AdEx implementation stability (Brette & Gerstner 2005 follow-ups)
7. Production AdEx code from neuroscience labs
8. Alternative formulations that avoid exponential overflow

---

## Findings

### 1. Mathematical Analysis of exp() Overflow

**The overflow is BY DESIGN, not a bug.**

From the Neuronal Dynamics textbook (Gerstner et al., EPFL):

> "Once the membrane potential crosses the rheobase threshold, it diverges to infinity in finite time."

The AdEx differential equation:

```
tau_m * du/dt = -(u - u_rest) + Delta_T * exp((u - vartheta_rh) / Delta_T) + R*I
```

**Key insight**: The exponential term dominates when `u >> vartheta_rh + Delta_T`, causing explosive growth that represents sodium channel activation during spike initiation. This is the mathematical representation of action potential upswing.

---

### 2. Quantitative Overflow Thresholds

**IEEE 754 Float64 Limits:**

| Precision | Overflow Threshold | Underflow Threshold |
|-----------|-------------------|---------------------|
| float64 | `exp(709.7827...)` | `exp(-745.15...)` |
| float32 | `exp(88.72...)` | `exp(-103.97...)` |

**Critical values for AdEx:**

```python
# Float64 overflow
exp(709.782712893384) = 1.7976931348623157e+308  # max float64
exp(710) = INF  # overflow

# Float32 overflow
exp(88.72) = 3.4028235e+38  # max float32
exp(89) = INF  # overflow
```

**For your conscious_snn parameters:**
- V_T (rheobase) = -50.4 mV
- Delta_T = 2.0 mV

**Overflow condition:**
```
(v - V_T) / Delta_T > 709.78
```

For Delta_T = 2 mV:
```
v > V_T + 709.78 * Delta_T
v > -50.4 + 1419.56 = 1369 mV
```

For Delta_T = 0.5 mV (sharper threshold):
```
v > -50.4 + 354.89 = 304 mV
```

**Strategic insight**: Smaller Delta_T creates sharper biological thresholds but increases overflow risk at lower voltage deviations.

---

### 3. Maximum Safe Values for DeltaT Parameter

**Biological range**: 0.5 - 5 mV for cortical neurons

**Stability recommendations:**

| Delta_T | Overflow Voltage | Biological Accuracy | Stability Risk |
|---------|-----------------|---------------------|----------------|
| 0.5 mV | v > V_T + 355 mV | Very sharp threshold | HIGH - overflow at lower v |
| 1.0 mV | v > V_T + 710 mV | Sharp threshold | Medium |
| 2.0 mV | v > V_T + 1420 mV | Typical cortical | Low |
| 5.0 mV | v > V_T + 3549 mV | Gradual threshold | Very Low |

**Recommendation**: Use Delta_T = 2.0 mV (your current value) for optimal balance of biological accuracy and numerical stability.

---

### 4. Clamping Strategies

#### A. Exponential Argument Clamping (Your Current Approach)

Your current implementation in `/home/peace/conscious_snn/core/neurons.py`:

```python
# Line 34: exp argument clamped to [-50, 50]
dv/dt = (E_L - v + delta_T*exp(clip((v - V_T)/delta_T, -50, 50)) + I_syn + I_ext - w) / tau_m : volt
```

**Analysis**:
- `exp(50)` = 5.18e+21 (well below overflow)
- `exp(-50)` = 1.93e-22 (well above underflow)
- **This is SAFE and CORRECT**

#### B. Numerical Threshold (Primary Strategy from Neuronal Dynamics)

From the textbook:

> "If the numerical threshold is chosen sufficiently high, theta_reset >> vartheta + Delta_T, its exact value does not play any role."

Your current settings:
- V_peak = -20 mV (numerical threshold)
- V_T = -50.4 mV (rheobase)
- Delta_T = 2.0 mV

Gap: 30.4 mV = 15.2 * Delta_T

**Recommendation**: This is excellent. The spike occurs well before overflow risk.

#### C. Current Clamping (Also Implemented)

Your OscillatoryNeuron implementation:

```python
# Lines 215-216: Current clamping
I_syn = clip(I_exc, -20*mV, 20*mV) - clip(I_inh, -20*mV, 20*mV) : volt
```

This prevents current accumulation from causing voltage excursions.

---

### 5. Integration Method Stability

**Brian2 Integration Methods:**

| Method | Stability | Accuracy | Recommended For |
|--------|-----------|----------|-----------------|
| `exact` | Highest | Exact | Linear equations only |
| `exponential_euler` | High | Good | AdEx with exponential terms |
| `euler` | Medium | O(dt) | General use, your current choice |
| `rk2`, `rk4` | High | O(dt^2), O(dt^4) | High accuracy needs |
| `heun` | High | O(dt^2) | Stiff systems |

**Your Current Implementation** (line 91 in neurons.py):
```python
method='euler'  # Used for all neuron types
```

**Note**: The comment on lines 88-90 explains why:
> "CRITICAL: Use 'euler' method instead of 'exponential_euler'. Brian2 bug #626: exact linear integrator fails for oscillatory systems. euler method is more stable and bypasses the SymPy discriminant issue."

This is a valid workaround for Brian2's handling of oscillatory driving terms.

---

### 6. Production AdEx Implementations

#### Brian2 AdEx Example (Canonical)

```python
from brian2 import *

# AdEx parameters (Brette & Gerstner 2005)
C = 281 * pF
gL = 30 * nS
EL = -70.6 * mV
VT = -50.4 * mV
DeltaT = 2 * mV
tauw = 144 * ms
a = 4 * nS
b = 0.0805 * nA
Vr = -48.5 * mV
Vcut = 20 * mV  # Numerical threshold (NOT overflow limit)

eqs = '''
dv/dt = (gL*(EL-v) + gL*DeltaT*exp((v-VT)/DeltaT) - w + I)/C : volt
dw/dt = (a*(v-EL) - w)/tauw : amp
I : amp
'''

G = NeuronGroup(N, eqs,
                threshold='v > Vcut',  # Numerical threshold
                reset='v = Vr; w += b',
                method='exponential_euler')
```

**Key observation**: Brian2's canonical example does NOT use clamping because the numerical threshold (`Vcut`) is set well below overflow limits.

#### NEST Simulator Approach

NEST uses `aeif_cond_exp` model with built-in spike detection:
- Checks for `v > V_peak` before exponential evaluation
- Uses implicit reset mechanism
- Time step adaptation near threshold

---

### 7. Alternative Formulations

#### A. Log-Sum-Exp Trick (Numerical Stability)

For computing with exponentials safely:

```python
# Instead of: exp(x) / sum(exp(x_i))
# Use: exp(x - max(x)) / sum(exp(x_i - max(x)))

# For AdEx, this doesn't directly apply but the principle is:
# Keep the argument bounded
```

#### B. Piecewise Approximation

```python
# For large positive arguments, use asymptotic approximation
def safe_exp_adex(v, VT, DeltaT, max_exp=50):
    exponent = (v - VT) / DeltaT
    if exponent > max_exp:
        # Linear approximation in spike region
        # exp(x) ~ infinity, neuron will spike anyway
        return DeltaT * float('inf')  # Triggers reset
    return DeltaT * np.exp(exponent)
```

#### C. Quadratic Integrate-and-Fire (QIF)

Alternative model without exponential:

```
tau * du/dt = (u - u_rest) * (u - u_thresh) + R*I
```

No overflow risk, but different dynamics.

---

### 8. Your Current Implementation Assessment

**Status**: Your implementation is CORRECT and SAFE.

**Evidence**:

1. **Exponential clamping**: `clip((v - V_T)/delta_T, -50, 50)`
   - Prevents overflow at all parameter values
   - Does not affect biological behavior (neuron spikes anyway when v >> V_T)

2. **Numerical threshold**: `v > V_peak` where V_peak = -20 mV
   - Well below overflow limit (1369 mV for your parameters)
   - Follows Neuronal Dynamics recommendations

3. **Current clamping**: `clip(I_exc, -20*mV, 20*mV)`
   - Prevents current accumulation issues

4. **Integration method**: `euler` instead of `exponential_euler`
   - Workaround for Brian2 bug #626
   - Valid choice for oscillatory systems

---

## Quantitative Thresholds Summary

| Parameter | Value | Overflow Risk | Your Setting |
|-----------|-------|---------------|--------------|
| Float64 exp overflow | x > 709.78 | Direct | N/A |
| Float32 exp overflow | x > 88.72 | Direct | N/A |
| Your Delta_T | 2.0 mV | Low | 2.0 mV |
| Your overflow v (Delta_T=2) | v > 1369 mV | Very Low | N/A |
| Your clamping limit | exp(50) | None | clip to 50 |
| Your V_peak | -20 mV | None | -20 mV |
| Your V_T | -50.4 mV | N/A | -50.4 mV |

---

## Recommendations

### For Conscious SNN Project

1. **Current implementation is stable** - no changes needed for overflow prevention

2. **If NaN occurs**, check:
   - Input current magnitudes (I_ext, I_syn)
   - Synaptic weight scaling
   - Time step size (dt)

3. **Alternative for better accuracy** (if euler causes issues):
   ```python
   method='heun'  # Better for nonlinear systems
   ```

4. **Debug NaN issues** by adding monitors:
   ```python
   # Check for NaN before they propagate
   @network_operation(dt=1*ms)
   def check_nan():
       if np.any(np.isnan(G.v[:])):
           print(f"NaN detected at t={defaultclock.t}")
   ```

---

## Evidence & Citations

1. **Brette R, Gerstner W (2005)**. "Adaptive exponential integrate-and-fire model as an effective description of neuronal activity." *Journal of Neurophysiology*, 94(5):3637-42. DOI:10.1152/jn.00686.2005

2. **Neuronal Dynamics** (Gerstner et al.). Section 5.2: Exponential Integrate-and-Fire Model. https://neuronaldynamics.epfl.ch/online/Ch5.S2.html

3. **Brian2 Documentation v2.10.1**. Models and neuron groups. https://brian2.readthedocs.io/en/stable/user/models.html

4. **IEEE 754-2019**. Standard for Floating-Point Arithmetic. Overflow thresholds for float64/float32.

5. **Fourcaud-Trocmé N, et al. (2003)**. "How Spike Generation Mechanisms Determine the Neuronal Response to Fluctuating Inputs." *J. Neuroscience*, 23(37):11628-11640.

---

## Code Examples

### Complete Safe AdEx Implementation (Brian2)

```python
from brian2 import *

# Parameters
C = 281 * pF
gL = 30 * nS
EL = -70.6 * mV
VT = -50.4 * mV
DeltaT = 2 * mV
tauw = 144 * ms
a = 4 * nS
b = 0.0805 * nA
Vr = -48.5 * mV
Vcut = -20 * mV  # Numerical threshold

# Safe AdEx with clamping
eqs = '''
dv/dt = (gL*(EL-v) + gL*DeltaT*exp(clip((v-VT)/DeltaT, -50, 50)) - w + I)/C : volt
dw/dt = (a*(v-EL) - w)/tauw : amp
I : amp
'''

G = NeuronGroup(10, eqs,
                threshold='v > Vcut',
                reset='v = Vr; w += b',
                method='euler',
                refractory=2*ms)

# Initialize
G.v = EL
G.w = a * (G.v - EL)
G.I = 1 * nA

# Monitor
M = StateMonitor(G, 'v', record=True)
S = SpikeMonitor(G)

run(1000*ms)
```

### NaN Detection and Recovery

```python
from brian2 import *
import numpy as np

class SafeAdExGroup:
    """AdEx group with automatic NaN detection and recovery."""

    def __init__(self, N, params):
        self.N = N
        self.params = params

        # Create neuron group
        self.group = NeuronGroup(
            N,
            '''dv/dt = (gL*(EL-v) + gL*DeltaT*exp(clip((v-VT)/DeltaT, -50, 50))
                       - w + I)/C : volt
               dw/dt = (a*(v-EL) - w)/tauw : amp
               I : amp''',
            threshold='v > Vcut',
            reset='v = Vr; w += b',
            method='euler'
        )

        # NaN detection
        self.nan_detected = False

    def check_nan(self):
        """Check for NaN values and reset affected neurons."""
        v_array = self.group.v[:]
        nan_mask = np.isnan(v_array)

        if np.any(nan_mask):
            n_nan = np.sum(nan_mask)
            print(f"Warning: {n_nan} neurons have NaN voltage, resetting...")

            # Reset NaN neurons
            self.group.v[nan_mask] = self.params['EL']
            self.group.w[nan_mask] = self.params['a'] * (self.params['EL'] - self.params['EL'])
            self.nan_detected = True

        return nan_mask
```

---

*Research completed: 2026-03-13*
*Agent: Ava Sterling (Claude Researcher)*
*Scope: DEEP - Quantitative analysis with code examples*
