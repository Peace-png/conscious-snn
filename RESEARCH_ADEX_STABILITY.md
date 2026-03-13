# Research Report: AdEx Neuron Model Numerical Stability

## Query Analysis

The original query was decomposed into five strategic sub-questions:

1. Why does exp((v - V_T)/delta_T) overflow in numerical implementations?
2. What is the mathematical threshold where exp() produces values too large for float64?
3. What clamping strategies exist for the exponential term in AdEx models?
4. How does Brian2 handle the exponential term internally?
5. What are the formal stability conditions for AdEx differential equations?


## Findings

### 1. Why exp((v - V_T)/delta_T) Overflows

The exponential term in the AdEx model diverges to infinity in finite time - this is **by design**, not a bug. From the Neuronal Dynamics textbook (Gerstner et al.):

> "Once the membrane potential crosses the rheobase threshold, it diverges to infinity in finite time."

The exponential integrate-and-fire model was designed this way to capture the rapid upswing of action potentials. The differential equation is:

```
tau * du/dt = -(u - u_rest) + Delta_T * exp((u - vartheta_rh) / Delta_T) + R*I
```

When membrane potential `u` exceeds the rheobase threshold `vartheta_rh` by several multiples of the slope factor `Delta_T`, the exponential term dominates and grows explosively. This is the mathematical representation of sodium channel activation during spike initiation - it is meant to be explosively nonlinear.

**Key insight**: The overflow is not an implementation error but a consequence of the model faithfully representing the explosive nature of action potential upswing. However, for numerical simulation, we need to stop the integration before the values explode.


### 2. Float64 Overflow Threshold

**Mathematical Limit**: IEEE 754 double-precision (float64) overflow occurs at:

```
exp(709.782712893384) = 1.7976931348623157 x 10^308  (max float64)
exp(710) = INF (overflow)
```

For AdEx parameters typical in neuroscience:
- Delta_T ~ 1-5 mV (slope factor)
- vartheta_rh ~ -50 to -55 mV (rheobase threshold)

The overflow condition becomes critical when:
```
(v - V_T) / Delta_T > 709
```

For Delta_T = 2 mV: overflow when v exceeds V_T by approximately 1418 mV
For Delta_T = 0.5 mV: overflow when v exceeds V_T by approximately 355 mV

**Strategic insight**: Smaller Delta_T values (sharper threshold) lead to overflow at lower voltage deviations. This is a parameter sensitivity issue that affects numerical stability.


### 3. Clamping Strategies for the Exponential Term

Based on computational neuroscience practice and Brian2 conventions, several clamping strategies exist:

#### A. Numerical Threshold (Primary Strategy)
The standard approach uses a **numerical threshold** theta_reset that is "sufficiently high" but below overflow:

> "If the numerical threshold is chosen sufficiently high, theta_reset >> vartheta + Delta_T, its exact value does not play any role. The reason is that the upswing of the action potential for u >> vartheta + Delta_T is so rapid, that it goes to infinity in an incredibly short time."
> -- Neuronal Dynamics, Section 5.2

Recommended threshold: 20-50 mV above rheobase threshold (e.g., if V_T = -50mV, use theta_reset = -30mV to -10mV)

#### B. Exponential Clamping
Clamp the argument to exp() before evaluation:
```python
# Pre-computation clamping
exponent = (v - V_T) / Delta_T
exponent = min(exponent, 50.0)  # exp(50) ~ 5x10^21, still large but finite
spike_drive = Delta_T * exp(exponent)
```

#### C. Voltage Clamping
Directly clamp membrane potential:
```python
v = min(v, V_T + 10 * Delta_T)  # Keep v within 10*Delta_T of threshold
```

#### D. Combined Threshold + Clamping
Best practice combines both:
1. Use a numerical threshold theta_reset at reasonable voltage
2. Add clamping as a safety net for edge cases

```python
# Example implementation
def compute_exp_term(v, V_T, Delta_T, max_exp=50):
    exponent = (v - V_T) / Delta_T
    if exponent > max_exp:
        # Near spike threshold, return large value
        return float('inf')  # Will trigger reset
    return Delta_T * exp(exponent)
```


### 4. Brian2 Handling of Exponential Terms

From Brian2 documentation (v2.8.0.4):

#### Integration Methods
Brian2 supports multiple integration methods with different stability properties:

- **'exact'**: Analytical solutions for linear equations (most stable)
- **'exponential_euler'**: Semi-analytical for exponential terms (recommended for AdEx)
- **'euler'**: Forward Euler (simple but can be unstable)
- **'rk2', 'rk4'**: Runge-Kutta methods (better accuracy)
- **'heun'**: Predictor-corrector (good balance)
- **GSL methods**: GNU Scientific Library integrators

**Critical**: For AdEx models, Brian2 documentation recommends:
1. Use `'exponential_euler'` or `'exact'` when possible
2. Set numerical threshold via `threshold='v > V_threshold'` parameter
3. Use `reset='v = V_reset'` to reset after spike

#### Code Generation
Brian2 generates optimized code for the target backend (numpy, cython, C++). The exponential term is evaluated as-is in the generated code, meaning overflow protection depends on:
1. Proper threshold setting
2. Reasonable time step (dt)
3. Numerical method selection

Brian2 does **not** automatically clamp the exponential term - it relies on the threshold/reset mechanism to prevent overflow before it occurs.


### 5. Formal Stability Conditions for AdEx

From the Neuronal Dynamics textbook and Brette & Gerstner (2005):

#### Fixed Point Analysis
The AdEx model has two equations:

```
tau_m * du/dt = -(u - u_rest) + Delta_T * exp((u - vartheta_rh)/Delta_T) - R*w + R*I
tau_w * dw/dt = a*(u - u_rest) - w
```

**Fixed points** occur when du/dt = 0 and dw/dt = 0.

For I = 0 (no input), there are **two fixed points**:
1. **Stable fixed point**: u ~ u_rest (resting potential)
2. **Unstable fixed point**: u > vartheta_rh (acts as threshold)

#### Stability Conditions

1. **Subthreshold stability**: For u << vartheta_rh - Delta_T, the exponential term is negligible and the system behaves like a leaky integrate-and-fire model (stable).

2. **Threshold crossing**: When u approaches vartheta_rh, the exponential term becomes significant. The condition for spike initiation:
   ```
   df/du = 0  at  u = vartheta_rh
   ```
   This defines the **rheobase threshold**.

3. **Bifurcation point**: For slowly increasing input current, the two fixed points merge at the bifurcation point (saddle-node bifurcation).

4. **Numerical stability conditions**:
   - Time step dt must be small compared to tau_m (typically dt < tau_m/10)
   - For exponential Euler: the method is unconditionally stable for the linear part
   - Reset threshold must be set before numerical overflow (theta_reset << vartheta_rh + 709*Delta_T)


### Strategic Insights

**Second-order effects to consider:**

1. **Parameter sensitivity**: Smaller Delta_T values create sharper thresholds but increase overflow risk. Delta_T ~ 2 mV is typical for cortical pyramidal neurons.

2. **Time step coupling**: Larger dt values can cause voltage to "jump past" the numerical threshold in a single step, leading to overflow before reset can occur.

3. **Adaptation feedback**: The w variable (adaptation current) provides negative feedback that can stabilize voltage trajectories, but requires careful coupling parameter (a, b) selection.

4. **Implementation robustness**: Production implementations should use multiple safety mechanisms:
   - Numerical threshold (primary)
   - Exponential clamping (backup)
   - NaN detection (error recovery)


## Evidence & Citations

1. **Brette R, Gerstner W (2005)**. "Adaptive exponential integrate-and-fire model as an effective description of neuronal activity." *Journal of Neurophysiology*, 94(5):3637-42. DOI:10.1152/jn.00686.2005

2. **Fourcaud-Trocmé N, Hansel D, van Vreeswijk C, Brunel N (2003)**. "How Spike Generation Mechanisms Determine the Neuronal Response to Fluctuating Inputs." *The Journal of Neuroscience*, 23(37):11628-11640. DOI:10.1523/JNEUROSCI.23-37.11628.2003

3. **Badel L, Lefort S, Brette R, Petersen CC, Gerstner W, Richardson MJ (2008)**. "Dynamic I-V curves are reliable predictors of naturalistic pyramidal-neuron voltage traces." *Journal of Neurophysiology*, 99(2):656-66. DOI:10.1152/jn.01107.2007

4. **Naud R, Marcille N, Clopath C, Gerstner W (2008)**. "Firing patterns in the adaptive exponential integrate-and-fire model." *Biological Cybernetics*, 99(4-5):335-47. DOI:10.1007/s00422-008-0264-7

5. **Gerstner W, Kistler WM, Naud R, Paninski L**. *Neuronal Dynamics: From Single Neurons to Networks and Models of Cognition*. Cambridge University Press. Online: https://neuronaldynamics.epfl.ch/online/

6. **Brian2 Documentation v2.8.0.4**. https://brian2.readthedocs.io/

7. **Wikipedia: Exponential integrate-and-fire**. https://en.wikipedia.org/wiki/Exponential_integrate-and-fire


## Recommendations

### For the Conscious SNN Project

1. **Immediate fix**: Set numerical threshold 20-30 mV above rheobase threshold
   ```python
   threshold='v > -20*mV'  # If V_T = -50mV
   ```

2. **Add exponential clamping** in the equations:
   ```python
   # In neuron model definition
   eqs = '''
   dv/dt = (-(v-EL) + DeltaT*exp(min((v-VT)/DeltaT, 50))/tau : volt
   ...
   '''
   ```

3. **Use exponential_euler method**:
   ```python
   neuron_group = NeuronGroup(..., method='exponential_euler')
   ```

4. **Reduce time step** if instability persists:
   ```python
   defaultclock.dt = 0.1*ms  # Smaller dt for stability
   ```

5. **Check parameters**: Ensure Delta_T is in reasonable range (1-5 mV for biological neurons)


## Summary Table

| Issue | Cause | Solution |
|-------|-------|----------|
| NaN in AdEx | exp() overflow | Set numerical threshold below overflow |
| No spikes | Threshold too high | Lower threshold or increase input |
| Thalamus overactive | Wrong target frequency | Adjust oscillatory drive parameters |
| Numerical instability | Large dt or parameters | Use exponential_euler, reduce dt |


---
*Research conducted: 2026-03-13*
*Agent: Ava Sterling (Claude Researcher)*
*Scope: Mathematical foundations of AdEx stability*
