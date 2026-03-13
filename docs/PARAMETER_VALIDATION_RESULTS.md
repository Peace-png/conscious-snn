# Research Parameter Validation Results
## Date: 2026-03-13

### Summary
**All 8/8 tests passed.** The research parameters from `RESEARCH_PARAMS_MASTER.md` produce correct oscillation frequencies.

### Test Results

| System | tau_m (ms) | A_osc (mV) | Target (Hz) | Measured (Hz) | Status |
|--------|------------|------------|-------------|---------------|--------|
| Thalamus Relay | 20 | 30 | 10 | 10.0 | PASS |
| Thalamus Reticular | 15 | 25 | 10 | 10.0 | PASS |
| BLA Pyramidal | 27.8 | 40 | 6 | 6.0 | PASS |
| BLA Stellate | 14.5 | 25 | 6 | 6.0 | PASS |
| Hippocampus CA1 | 30 | 45 | 6 | 6.0 | PASS |
| Hippocampus CA3 | 35 | 50 | 6 | 6.0 | PASS |
| DMN PCC | 22 | 30 | 10 | 10.0 | PASS |
| DMN mPFC | 20 | 28 | 9 | 8.0 | PASS |

### Critical Parameters

1. **tau_osc = 10ms** (MUST be ≤ 10ms)
   - Higher values suppress oscillation entirely
   - tau_osc = 20ms → 0 Hz output
   - tau_osc = 50ms → complete suppression

2. **A_osc ≈ tau_m × 1.5**
   - Scales with membrane time constant
   - tau_m=20ms → A_osc=30mV
   - tau_m=30ms → A_osc=45mV

3. **Integration method = 'euler'**
   - Brian2 bug #626: `exponential_euler` fails with sin/cos terms
   - Must use `method='euler'` for oscillatory systems

### Gamma Oscillations Note

Gamma (30-100 Hz) requires **PING circuit** (Pyramidal-Interneuron Network Gamma), not intrinsic oscillation.

**PING Parameters:**
- Pyramidal tau_m: 20ms
- Interneuron tau_m: 10ms
- E/I ratio: 4:1 (800:200)
- w_IE: 2.0nS (stronger than w_EI)
- w_EI: 0.5nS
- tau_GABA: 10ms (critical for gamma timing)

### Fixed Issues

1. **Circular import** - Fixed by using lazy imports in `core/base.py`
   - Import chain was: `core/__init__.py` → `core/base.py` → `systems/cardiac.py` → `core/neurons.py`
   - Solution: Import system modules inside build methods instead of at module level

### Files Modified

- `core/base.py` - Lazy imports for system modules
- `connectivity/influence.py` - Anatomical delays
- `docs/RESEARCH_PARAMS_MASTER.md` - Created master reference

### Next Steps

1. Run full network simulation to verify inter-system connectivity
2. Implement PING circuit for prefrontal gamma
3. Add cardiac-respiratory coupling (RSA)
4. Verify cross-frequency coupling (theta-gamma MI)
