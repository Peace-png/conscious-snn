# Thalamus Debugging Session - 2026-03-13

## What Is This Codebase?

**Conscious SNN** - A spiking neural network simulation of consciousness using Brian2.

**Location:** `/home/peace/conscious_snn/`

**Purpose:** Models 8 biological neural systems to simulate consciousness:
- Brainstem (autonomic floor)
- Cardiac (heart rhythm ~1Hz)
- Respiratory (breathing ~0.25Hz)
- Limbic (emotion, theta ~6Hz)
- Hippocampus (memory, theta ~6Hz)
- Prefrontal (executive control, gamma ~60Hz)
- Thalamus (sensory relay, alpha ~10Hz)
- DMN (default mode network, alpha ~10Hz)

---

## The Problem

Most neural systems were showing **0 Hz firing rate** despite having oscillatory drive mechanisms. Only cardiac (5Hz) and respiratory (2Hz) were working.

---

## Root Causes Found

### Bug 1: `tau_osc` Too Large (Critical!)

**Location:** `core/neurons.py` line 270

**Issue:** OscillatoryNeuron.create_group() had fallback `tau_osc = 50*ms`

**Why it matters:**
- `tau_osc` is the time constant for oscillation current integration
- If `tau_osc > 20ms`, the current can't follow the sinusoidal drive
- Result: oscillation is **completely suppressed**

**Test results:**
```
tau_osc = 5ms  → 10.0 Hz ✅
tau_osc = 10ms → 10.0 Hz ✅
tau_osc = 20ms → 0.0 Hz ❌
tau_osc = 50ms → 0.0 Hz ❌
```

**Fix applied:**
```python
# Before
group.tau_osc = p.get('tau_osc', 50*ms)  # WRONG

# After
group.tau_osc = p.get('tau_osc', 10*ms)  # CORRECT
```

---

### Bug 2: Oscillation Amplitude Too Low

**Location:** `core/neurons.py` defaults, and all `systems/*.py` files

**Issue:** `A_osc` values were set too low for given `tau_m` values

**The physics:**
- Higher `tau_m` means slower membrane response
- Need higher amplitude to reach threshold in time
- Threshold gap: -65mV (rest) to -50mV (thresh) = 15mV

**Test results:**
```
tau_m = 15ms → needs A_osc ≥ 25mV
tau_m = 20ms → needs A_osc ≥ 30mV
tau_m = 25ms → needs A_osc ≥ 35mV
tau_m = 30ms → needs A_osc ≥ 40mV
tau_m = 35ms → needs A_osc ≥ 50mV
```

**Fix applied to systems:**
| System | tau_m | Old A_osc | New A_osc |
|--------|-------|-----------|-----------|
| Thalamus relay | 20ms | 8mV | 30mV |
| Thalamus reticular | 15ms | 18mV | 25mV |
| Thalamus intralaminar | 25ms | 18mV | 35mV |
| Limbic BL amygdala | 25ms | 18mV | 35mV |
| Hippocampus EC | 20ms | 18mV | 30mV |
| Hippocampus CA1 | 25ms | 18mV | 35mV |
| DMN PCC | 25ms | 18mV | 35mV |
| DMN mPFC | 30ms | 18mV | 40mV |
| DMN hippocampal | 35ms | 18mV | 50mV |

---

### Bug 3: Reticular Inhibition Too Strong

**Location:** `systems/thalamus.py` lines 158-166

**Issue:** Reticular→Relay inhibition (`w_syn=8mV, p=0.3`) suppressed relay completely

**Test results:**
```
w=8mV, p=0.3: Relay = 1.0 Hz (suppressed from 10 Hz)
w=8mV, p=0.1: Relay = 4.6 Hz
w=4mV, p=0.3: Relay = 1.9 Hz
w=1mV, p=0.1: Relay = 10.0 Hz ✅
```

**Fix applied:**
```python
# Before
self.reticular_to_relay.connect(p=0.3)
self.reticular_to_relay.w_syn = 8*mV

# After
self.reticular_to_relay.connect(p=0.1)
self.reticular_to_relay.w_syn = 2*mV
```

---

### Bug 4: `set_alpha_power()` Override

**Location:** `systems/thalamus.py` line 249

**Issue:** Method was setting `A_alpha = 8*power*mV` which overrides the correct 30mV

**Fix applied:** Changed to scale from correct base value (30mV at power=1.0)

---

## Files Modified

1. **`core/neurons.py`**
   - Line 235: Changed defaults `tau_osc` from 10ms, `A_osc` from 20mV → 25mV
   - Line 269-272: Fixed fallback values in `create_group()`

2. **`systems/thalamus.py`**
   - Line 105: `A_alpha = 30*mV` (from 8*mV)
   - Line 101: `tau_osc = 10*ms` (from 50*ms)
   - Lines 127, 139: Updated `A_osc` for reticular and intralaminar
   - Lines 165-166: Reduced inhibition strength
   - Lines 247-250: Fixed `set_alpha_power()` scaling

3. **`systems/limbic.py`**
   - Line 72: `A_osc = 35*mV` (from 18*mV)

4. **`systems/hippocampus.py`**
   - Line 75: `A_osc = 30*mV` (from 18*mV)
   - Line 125: `A_osc = 35*mV` (from 18*mV)

5. **`systems/dmn.py`**
   - Line 80: `A_osc = 35*mV` (from 18*mV)
   - Line 92: `A_osc = 40*mV` (from 18*mV)
   - Line 114: `A_osc = 50*mV` (from 18*mV)

---

## Current State After Fixes

**Working:**
- Cardiac: 5 Hz (target 1 Hz) ✅
- Respiratory: 2 Hz (target 0.25 Hz) ✅
- Thalamus (isolated test): 6.77 Hz ✅

**Still at 0 Hz in full simulation:**
- Brainstem
- Limbic
- Hippocampus
- DMN
- Thalamus (mystery - works in isolation but not full sim)

---

## Key Insight: Noise Archaeology

The thalamus is the "noise archaeologist" - it gates which signals reach cortex. The reticular nucleus provides GABAergic inhibition that filters thalamocortical transmission.

**The problem:** In full simulation, something is still suppressing thalamus activity that doesn't happen in isolation.

---

## Test Files Created

- `test_oscillation_amplitude.py` - Tests different A_osc values
- `test_tau_m.py` - Tests tau_m effect on oscillation following
- `test_tau_osc.py` - Tests tau_osc effect
- `test_amplitude_compensation.py` - Maps tau_m → required A_osc
- `test_thalamus_direct.py` - Direct thalamus component tests
- `test_thalamus_inhibition.py` - Tests inhibition strength

---

## Remaining Mystery

**Why does thalamus work in isolation (6.77 Hz) but show 0 Hz in full simulation?**

Possible causes not yet investigated:
1. Inter-system connections from influence matrix
2. Something overriding parameters after build
3. Network-level effects from other systems

---

## The OscillatoryNeuron Equation

```python
dv/dt = (v_rest - v + I_osc + I_syn + I_ext) / tau_m : volt
dI_osc/dt = (-I_osc + A_osc * sin(2*pi*f_osc*t)) / tau_osc : volt
```

**Key insight:** `I_osc` follows the sinusoidal drive with time constant `tau_osc`. If tau_osc is too large, it smooths out the oscillation entirely.

---

## Quick Reference: Fix Checklist

- [x] `tau_osc` fallback → 10ms
- [x] `A_osc` scaled to tau_m
- [x] Reticular inhibition reduced (w=2mV, p=0.1)
- [x] `set_alpha_power()` fixed
- [ ] Investigate why full simulation differs from isolation tests
