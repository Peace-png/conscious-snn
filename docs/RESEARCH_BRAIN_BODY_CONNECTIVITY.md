# Brain-Body Connectivity Research

> Research compilation for Brian2 SNN Architecture
> Source: Multi-agent research completed 2026-03-13

## Overview

This document compiles biological parameters for bidirectional brain-body connectivity, essential for accurate modeling of the influence matrix and inter-system weights.

---

## Influence Weight Summary for Modeling

| Source System | Target System | Primary Pathway | Relative Weight | Signal Type |
|---------------|---------------|-----------------|-----------------|-------------|
| Gut (ENS) | Brain | Vagal afferents | 80-90% of vagal traffic | Serotonin (5-HT), mechanical |
| Heart | Brainstem | Carotid/aortic baroreceptors | High (beat-to-beat) | Pressure/stretch |
| Lungs/Nasal | Hippocampus | Olfactory-entorhinal | Moderate (phase-locked) | Respiratory rhythm |
| Brainstem (NTS) | LC, Raphe, Hypothalamus | Direct projections | High (integration hub) | Visceral state |
| Locus Coeruleus | Cortex | NE projections | >50% brain NE | Norepinephrine |
| Raphe Nuclei | Cortex, limbic | 5-HT projections | ~95% body 5-HT in gut | Serotonin |
| Basal Forebrain | Neocortex | ACh projections | Major cholinergic | Acetylcholine |
| Medial Septum | Hippocampus | Theta pacemaker | 6-9 Hz rhythm | Theta oscillation |
| Vagus efferent | Heart, gut, lungs | 10-20% of fibers | Lower bandwidth | Parasympathetic |
| Enteric NS | Local gut | Intrinsic plexuses | 500M neurons | Autonomous reflex |
| Carotid sinus | NTS (brainstem) | Glossopharyngeal (CN IX) | High frequency | Blood pressure |
| Aortic arch | NTS (brainstem) | Vagus (CN X) | High frequency | Blood pressure |

---

## Key Quantitative Parameters

| Parameter | Value | Source |
|-----------|-------|--------|
| Vagus afferent/efferent ratio | 80-90% afferent, 10-20% efferent | Vagus nerve (CN X) |
| ENS neuron count | ~500 million | Enteric nervous system |
| Serotonin distribution | >90% gut, ~5% brain | Enteric nervous system |
| Dopamine distribution | ~50% in gut | Enteric nervous system |
| Hippocampal theta frequency | 6-9 Hz | Hippocampus |
| LC neuron count | 22,000-51,000 | Locus coeruleus |
| LC contribution to brain NE | >50% | Locus coeruleus |
| Right vagus fiber count | ~105,000 | Vagus nerve |
| Left vagus fiber count | ~87,000 | Vagus nerve |

---

## Vagal Nervous System Details

### Afferent Pathways (80-90% of vagal fibers)
- **Gut → Brain**: 80-90% of vagal traffic is afferent (gut to brain)
- **Mechanoreceptors**: Stretch, tension, distension signals
- **Chemoreceptors**: pH, glucose, hormones, nutrients
- **Hormonal**: CCK, GLP-1, PYY signaling

### Efferent Pathways (10-20% of vagal fibers)
- **Heart**: Chronotropic (rate) and dromotropic (conduction) effects
- **Gut**: Motility, secretion, blood flow modulation
- **Lungs**: Bronchoconstriction, mucus secretion

### Clinical Relevance
- **Vagus nerve stimulation (VNS)**: FDA-approved for epilepsy, depression
- **Heart rate variability (HRV)**: Index of vagal tone
- **Inflammation**: Cholinergic anti-inflammatory pathway

---

## Baroreceptor System

### Location and Function
- **Carotid sinus**: Glossopharyngeal nerve (CN IX) to NTS
- **Aortic arch**: Vagus nerve (CN X) to NTS
- **Sensing**: Blood pressure, arterial stretch

### Signal Characteristics
- **Dynamic range**: 60-180 mmHg
- **Sensitivity**: Greatest around mean arterial pressure (~90 mmHg)
- **Adaptation**: Rapid adaptation to sustained pressure changes

### Integration
- **NTS (nucleus tractus solitarius)**: Primary integration hub
- **Outputs**: Cardiac vagal motor neurons, sympathetic outflow
- **Timing**: Beat-to-beat regulation

---

## Locus Coeruleus (LC) Details

### Anatomy
- **Location**: Pons, near fourth ventricle floor
- **Neuron count**: 22,000-51,000 (humans)
- **Neurotransmitter**: Norepinephrine (NE)

### Projections
- **Cortex**: Widespread NE release (>50% brain NE)
- **Hippocampus**: Memory modulation, attention
- **Amygdala**: Emotional arousal, fear conditioning
- **Spinal cord**: Pain modulation

### Firing Modes
- **Tonic**: 1-5 Hz at rest, 5-10 Hz active
- **Phasic**: Brief bursts (10-20 Hz) on salient events
- **Sleep**: Near-silent during REM, minimal in NREM

---

## Raphe Nuclei (Serotonergic System)

### Anatomy
- **Location**: Brainstem midline
- **Neuron count**: ~300,000-400,000 (humans)
- **Neurotransmitter**: Serotonin (5-HT)

### Distribution
- **Gut ENS**: >90% of body 5-HT
- **Brain**: ~5% of body 5-HT
- **Blood platelets**: Store but don't synthesize

### Projections
- **Rostral raphe**: Forebrain, cortex, limbic
- **Caudal raphe**: Spinal cord, brainstem

### Functions
- **Mood regulation**: Depression, anxiety pathways
- **Sleep-wake cycle**: Promotes wakefulness
- **Pain modulation**: Descending inhibitory pathways
- **Appetite**: Satiety signaling

---

## Hippocampal-Respiratory Coupling

### Theta Rhythm Generation
- **Medial septum**: Primary pacemaker
- **Frequency**: 6-9 Hz (rodents), 4-8 Hz (humans)
- **Phase-locking**: To respiratory cycle

### Respiratory Effects
- **Inhalation**: Enhanced theta power
- **Nasal breathing**: Stronger coupling than mouth breathing
- **Memory**: Respiratory-phase-locked encoding enhancement

### Olfactory Pathway
- **Olfactory bulb**: Direct respiratory rhythm sensing
- **Entorhinal cortex**: Gateway to hippocampus
- **Phase precession**: Respiratory-modulated place cell firing

---

## Implementation Notes

### Used in Conscious SNN Architecture

| Parameter | Implementation Location | Value Used |
|-----------|------------------------|------------|
| Vagus afferent ratio | `cardiac.py` | 80% afferent |
| LC neuron count | `brainstem.py` | ~50,000 |
| Raphe neuron count | `brainstem.py` | ~300,000 |
| Hippocampal theta | `hippocampus.py` | 4-12 Hz (centered 6-8 Hz) |
| Cardiac rhythm | `cardiac.py` | ~1 Hz (60 bpm) |
| Respiratory rhythm | `respiratory.py` | ~0.25 Hz (15 bpm) |

### Influence Matrix Weights (from research)

Based on this research, the default influence matrix in `connectivity/influence.py` uses:
- Brainstem → Cardiac: 0.8 (strong vagal efferent)
- Brainstem → Respiratory: 0.9 (strong rhythm control)
- Cardiac → Brainstem: 0.3 (vagal afferent feedback)
- Respiratory → Hippocampus: 0.5 (respiratory-hippocampal coupling)

---

## Sources

1. **Baroreceptor** - Wikipedia: https://en.wikipedia.org/wiki/Baroreceptor
2. **Nucleus tractus solitarius** - Wikipedia: https://en.wikipedia.org/wiki/Nucleus_tractus_solitarius
3. **Vagus nerve** - Wikipedia: https://en.wikipedia.org/wiki/Vagus_nerve
4. **Locus coeruleus** - Wikipedia: https://en.wikipedia.org/wiki/Locus_coeruleus
5. **Enteric nervous system** - Wikipedia: https://en.wikipedia.org/wiki/Enteric_nervous_system
6. **Raphe nuclei** - Wikipedia: https://en.wikipedia.org/wiki/Raphe_nuclei
7. **Basal forebrain** - Wikipedia: https://en.wikipedia.org/wiki/Basal_forebrain
8. **Hippocampus** - Wikipedia: https://en.wikipedia.org/wiki/Hippocampus

---

## Future Research Needed

- [ ] Gut-brain axis integration (500M ENS neurons)
- [ ] HPA axis (hypothalamic-pituitary-adrenal) stress response
- [ ] Circadian rhythm modulation (suprachiasmatic nucleus)
- [ ] Detailed baroreflex transfer function
- [ ] Heart rate variability frequency components (LF/HF ratio)

---

*Compiled by PAI research agents - 2026-03-13*
