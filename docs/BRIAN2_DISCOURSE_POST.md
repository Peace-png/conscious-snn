# [Research Share] Equation Grouping for Large-Scale Multi-Region SNNs

**Category**: Tips & Tricks / Performance Optimization
**Tags**: brian2cuda, performance, memory-optimization, multi-region

---

## The Problem

I've been building a whole-brain spiking neural network with 8 biological systems (brainstem, cardiac, respiratory, limbic, hippocampus, prefrontal, thalamus, DMN) and hit Brian2CUDA's compilation memory limit at ~33GB RAM.

The network has:
- 31 NeuronGroups (different cell types across systems)
- 56 Synapses (inter-system connectivity)
- 29 Monitors

Brian2CUDA generates separate CUDA kernels for each NeuronGroup, causing NVCC memory to explode during `net.build()`.

## The Solution

I created an **EquationGroupOptimizer** that:
1. Scans the network for NeuronGroup equation signatures
2. Groups identical equations (e.g., all AdaptiveExpLIF groups)
3. Creates merged groups with indexed parameters
4. Remaps synapse indices
5. Preserves subpopulation-specific monitors

## Results

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| NeuronGroups | 31 | 13 | 58% |
| Total Objects | 116 | 44 | 62% |
| Peak Memory | 38.1 MB | 6.9 MB | 82% |
| Build Time | 5.75s | 0.15s | 97% |

## Key Insight

Brian2CUDA does **not** deduplicate identical equations. If you have:
- `dlPFC = NeuronGroup(80, adex_eqs, ...)`
- `vlPFC = NeuronGroup(50, adex_eqs, ...)`
- `OFC = NeuronGroup(30, adex_eqs, ...)`

You get 3 separate CUDA kernels even though they use the same equation template!

## Code Pattern

```python
# Instead of multiple separate groups:
dlpfc = NeuronGroup(80, adex_eqs, name='dlpfc')
vlpfc = NeuronGroup(50, adex_eqs, name='vlpfc')
ofc = NeuronGroup(30, adex_eqs, name='ofc')

# Use one merged group:
merged_pfc = NeuronGroup(160, adex_eqs, name='merged_pfc')
# Apply subpopulation parameters
merged_pfc.tau_w[0:80] = 300*ms   # dlpfc
merged_pfc.tau_w[80:130] = 200*ms # vlpfc
merged_pfc.tau_w[130:160] = 150*ms # ofc

# Track subpopulations for monitoring
dlpfc_indices = slice(0, 80)
vlpfc_indices = slice(80, 130)
ofc_indices = slice(130, 160)
```

## Biological Fidelity

This pattern preserves biological specificity through:
- **Per-neuron parameter arrays**: Each subpopulation has different `tau_m`, `A_osc`, etc.
- **Phase tracking**: Oscillatory rhythms (theta, alpha, gamma) synchronized via shared `f_osc`
- **Monitor filtering**: `SpikeMonitor.record` accepts index lists

```python
# Monitor specific subpopulation
SpikeMonitor(merged_pfc, record=list(range(0, 80)), name='dlpfc_spikes')
```

## Equation Types in Our Network

We identified 5 equation equivalence classes:
1. **OscillatoryNeuron** - sin-driven oscillation (theta 4-8Hz, alpha 8-12Hz, gamma 30-100Hz)
2. **AdaptiveExpLIF** - AdEx with adaptation (cortical pyramidal cells)
3. **CardiacNeuron** - Pacemaker with HRV modulation (1Hz rhythm)
4. **RespiratoryNeuron** - Phase-tracking oscillators (0.25Hz rhythm)
5. **InhibitoryInterneuron** - Fast-spiking GABAergic

## Lessons Learned

1. **NVCC compilation memory** scales with CodeObject count, not neuron count
2. **Sparse connectivity** (2-5%) helps runtime memory but not compilation memory
3. **Subpopulation indexing** is the key to preserving biological detail
4. **tau_osc ≤ 10ms** is critical for oscillation following (discovered during parameter tuning)

## Questions for the Community

1. Has anyone else hit similar compilation limits with many NeuronGroups?
2. Are there plans for Brian2CUDA to deduplicate identical equations?
3. Would a PR for an `EquationGroupOptimizer` utility class be welcome?

## Files

Full implementation available at:
`/home/peace/conscious_snn/core/equation_group_optimizer.py`

---

**System**: RTX 4070 Super, 12GB VRAM, Ubuntu 24.04, CUDA 12.0
**Brian2**: 2.6.0
**Brian2CUDA**: 1.0a7
