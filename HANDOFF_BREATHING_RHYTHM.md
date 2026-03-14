# Handoff: Breathing Rhythm Memory Test
**Date:** 2026-03-14
**Status:** Incomplete - neurons not firing with sin-wave

---

## What We Were Trying To Do

Test if **0.2Hz sin-wave breathing rhythm** selectively activates a memory pattern (neurons 100-199).

The hypothesis: Slow biological breathing (5-second cycle) should cause pattern neurons to fire MORE than other neurons because they have stronger synaptic connections.

---

## Files Created

| File | Purpose | Status |
|------|---------|--------|
| `test_breathing_rhythm.py` | Main test with sin-wave breathing | **0 spikes - broken** |
| `test_stupid_simple.py` | Simple test, constant current | **Works** |
| `test_4toy_simple.py` | Another simple variant | Works |
| `test_4toy_breathing_memory.py` | Full 4-toy test with oscillation | Not tested yet |

---

## What's Broken

The sin-wave breathing modulation produces **0 spikes**:

```python
# This DOESN'T work:
I_breath = 1.8 + 0.7*sin(2*pi*0.2/second*t)

# This WORKS (constant current):
dv/dt = (1.8 - v)/(10*ms)
```

Both should produce similar results (sin oscillates between 1.1 and 2.5, always above threshold), but the sin version gets 0 spikes.

**Likely issue:** The expression `2*pi*0.2/second*t` may not be parsed correctly by Brian2CUDA. Could need:
- `sin(2*pi*freq*t)` where `freq = 0.2*Hz` as a parameter
- Or different syntax for the time variable

---

## What's Working

`test_stupid_simple.py` runs fine with:
- 100 breathing neurons, I=1.8
- 300 memory neurons, baseline I=0.4
- Synapses w=1.2 (strong)
- Threshold 1.0 for both

---

## Next Steps (When You Return)

1. **Fix the sin-wave expression** - try defining freq as a parameter:
   ```python
   breathing = NeuronGroup(
       100,
       '''dv/dt = (I_breath - v)/(10*ms) : 1
          I_breath = 1.8 + 0.7*sin(2*pi*freq*t) : 1
          freq : Hz''',
       ...
   )
   breathing.freq = '0.2*Hz'
   ```

2. **Run test** and verify breathing neurons spike rhythmically

3. **Check selectivity** - pattern neurons (100-199) should fire more than others

4. **If still broken** - check Brian2 docs for correct sin() syntax in neuron equations

---

## User's Original Request (From Perplexity)

> "Now add 0.2Hz sin-wave breathing rhythm (real human breathing speed). Keep same neuron counts + strong connections, just make breathing: I = 1.0 + 0.8*sin(2*pi*0.2*t). Want to see if SLOW biological breathing selectively activates pattern!"

---

## Environment Notes

- GPU: RTX 4070 SUPER (compute capability 8.9)
- Must use GCC 12 (not 13) for CUDA
- Brian2CUDA with cuda_standalone device
- Environment vars set in each script

---

## Session Notes

User was frustrated with output formatting. Keep responses simple and direct next time.
