"""
Equation Group Optimizer for Brian2 SNNs

Reduces CUDA kernel count by merging NeuronGroups with identical equations.
Target: 84 objects → 12 objects, 40GB compile → 6GB RAM

Strategy:
1. Compute equation signature (hash of model + threshold + reset)
2. Group NeuronGroups by equivalence class
3. Create merged groups with indexed parameters
4. Remap synapse indices
5. Preserve biological specificity via per-subgroup parameters

Author: Andrew Hagan / PAI
Date: 2026-03-14
"""

from brian2 import (
    NeuronGroup, Synapses, SpikeMonitor, StateMonitor,
    Network, Hz, ms, mV, second, Equations
)
import numpy as np
import hashlib
from typing import Dict, List, Tuple, Optional, Any, Set
from dataclasses import dataclass, field


# Standard equation templates indexed by signature
# These are the canonical equation strings from core/neurons.py
EQUATION_TEMPLATES = {
    # OscillatoryNeuron
    'oscillatory': '''
    dv/dt = (v_rest - v + I_osc + I_syn + I_ext) / tau_m : volt (unless refractory)
    dI_osc/dt = (-I_osc + A_osc * sin(2*pi*f_osc*t)) / tau_osc : volt
    I_syn = I_exc - I_inh : volt
    dI_exc/dt = -I_exc / tau_e : volt
    dI_inh/dt = -I_inh / tau_i : volt
    I_ext : volt
    tau_m : second
    tau_osc : second
    f_osc : Hz
    A_osc : volt
    v_rest : volt
    v_thresh : volt
    tau_e : second
    tau_i : second
    ''',

    # AdaptiveExpLIF
    'adex': '''
    dv/dt = (E_L - v + delta_T*exp((v - V_T)/delta_T) + I_syn + I_ext - w) / tau_m : volt (unless refractory)
    dw/dt = (a*(v - E_L) - w) / tau_w : volt
    I_syn = I_exc - I_inh : volt
    dI_exc/dt = -I_exc / tau_e : volt
    dI_inh/dt = -I_inh / tau_i : volt
    I_ext : volt
    tau_m : second
    E_L : volt
    V_T : volt
    delta_T : volt
    V_peak : volt
    tau_w : second
    a : 1
    b : volt
    tau_e : second
    tau_i : second
    ''',

    # CardiacNeuron
    'cardiac': '''
    dv/dt = (v_rest - v + I_pacemaker + I_vagal + I_syn) / tau_m : volt (unless refractory)
    dI_pacemaker/dt = (-I_pacemaker + A_card * sin(2*pi*f_card*t + phi)) / tau_pacemaker : volt
    dI_vagal/dt = -I_vagal / tau_vagal : volt
    I_syn = I_exc - I_inh : volt
    dI_exc/dt = -I_exc / tau_e : volt
    dI_inh/dt = -I_inh / tau_i : volt
    dHRV_phase/dt = 2*pi*f_hrv : 1
    HRV_mod = 1 + hrv_amp * sin(HRV_phase) : 1
    tau_m : second
    tau_pacemaker : second
    f_card : Hz
    A_card : volt
    phi : 1
    tau_vagal : second
    f_hrv : Hz
    hrv_amp : 1
    v_rest : volt
    v_thresh : volt
    tau_e : second
    tau_i : second
    ''',

    # RespiratoryNeuron
    'respiratory': '''
    dv/dt = (v_rest - v + I_rhythm + I_modulatory + I_syn) / tau_m : volt (unless refractory)
    dI_rhythm/dt = (-I_rhythm + A_resp * sin(2*pi*f_resp*t)) / tau_rhythm : volt
    dI_modulatory/dt = -I_modulatory / tau_mod : volt
    I_syn = I_exc - I_inh : volt
    dI_exc/dt = -I_exc / tau_e : volt
    dI_inh/dt = -I_inh / tau_i : volt
    resp_phase_sin = sin(2*pi*f_resp*t) : 1 (shared)
    is_inspiratory = resp_phase_sin > 0 : 1 (shared)
    is_expiratory = resp_phase_sin <= 0 : 1 (shared)
    neuron_type : 1
    tau_m : second
    tau_rhythm : second
    f_resp : Hz (shared)
    A_resp : volt
    tau_mod : second
    v_rest : volt
    v_thresh : volt
    tau_e : second
    tau_i : second
    ''',

    # InhibitoryInterneuron
    'inhibitory': '''
    dv/dt = (v_rest - v + I_syn + I_ext) / tau_m : volt (unless refractory)
    I_syn = I_exc - I_inh : volt
    dI_exc/dt = -I_exc / tau_e : volt
    dI_inh/dt = -I_inh / tau_i : volt
    I_ext : volt
    tau_m : second
    v_rest : volt
    v_thresh : volt
    tau_e : second
    tau_i : second
    ''',
}

# Threshold/reset templates
THRESHOLD_RESET = {
    'oscillatory': ('v > v_thresh', 'v = v_rest'),
    'adex': ('v > V_peak', 'v = E_L\nw += b'),
    'cardiac': ('v > v_thresh', 'v = v_rest'),
    'respiratory': ('v > v_thresh', 'v = v_rest'),
    'inhibitory': ('v > v_thresh', 'v = v_rest'),
}


def detect_equation_type(group: NeuronGroup) -> Optional[str]:
    """
    Detect the equation type of a NeuronGroup by examining its variables.

    Returns the equation type key or None if unknown.
    """
    # Get variable names
    var_names = set()
    if hasattr(group, 'variables'):
        var_names = set(group.variables.keys())

    # Check for characteristic variables of each type
    if 'I_osc' in var_names and 'f_osc' in var_names:
        return 'oscillatory'
    elif 'w' in var_names and 'delta_T' in var_names:
        return 'adex'
    elif 'I_pacemaker' in var_names and 'HRV_phase' in var_names:
        return 'cardiac'
    elif 'I_rhythm' in var_names and 'neuron_type' in var_names:
        return 'respiratory'
    elif 'I_ext' in var_names and len(var_names) < 15:  # Simple model
        return 'inhibitory'

    return None


@dataclass
class GroupMetadata:
    """Metadata for a NeuronGroup to enable merging."""
    name: str
    equation_signature: str
    equation_type: str  # 'oscillatory', 'adex', etc.
    size: int
    equations: str
    threshold: str
    reset: str
    method: str
    refractory: second
    params: Dict[str, Any] = field(default_factory=dict)
    state_vars: Dict[str, Any] = field(default_factory=dict)
    system_name: str = ""
    original_group: NeuronGroup = None

    # Index range in merged group
    start_idx: int = 0
    end_idx: int = 0


@dataclass
class SynapseMetadata:
    """Metadata for a Synapse to enable remapping."""
    name: str
    source_name: str
    target_name: str
    source_indices: np.ndarray = None
    target_indices: np.ndarray = None
    delays: np.ndarray = None
    weights: np.ndarray = None
    on_pre: str = ""
    model: str = ""
    original_synapse: Synapses = None


class EquationGroupOptimizer:
    """
    Optimizes Brian2 networks by merging NeuronGroups with identical equations.

    The core insight: Brian2CUDA generates one CUDA kernel per unique equation.
    By merging groups with the same equation but different parameters, we reduce
    kernel count from ~32 to ~8, dramatically reducing compile memory.

    Usage:
        optimizer = EquationGroupOptimizer(network)
        optimized_net = optimizer.optimize()
        print(f"Objects: {optimizer.original_count} → {optimizer.optimized_count}")
    """

    def __init__(self, network: Network = None, verbose: bool = True):
        """
        Initialize the optimizer.

        Args:
            network: Brian2 Network to optimize (can also pass ConsciousNetwork)
            verbose: Print progress information
        """
        # Handle both Network and ConsciousNetwork
        if hasattr(network, 'brian_network'):
            self.network = network.brian_network
            self.conscious_network = network
        else:
            self.network = network
            self.conscious_network = None

        self.verbose = verbose

        # Tracking
        self.group_metadata: Dict[str, GroupMetadata] = {}
        self.synapse_metadata: Dict[str, SynapseMetadata] = {}
        self.equivalence_classes: Dict[str, List[str]] = {}  # signature -> group names
        self.merged_groups: Dict[str, NeuronGroup] = {}
        self.remapped_synapses: Dict[str, Synapses] = {}
        self.monitors: Dict[str, Any] = {}

        # Index remapping
        self.index_map: Dict[str, Tuple[int, int]] = {}  # group_name -> (start, end)

        # Merged group tracking
        self._merged_system_ids: Dict[str, np.ndarray] = {}  # merged_name -> system_id array
        self._merged_original_groups: Dict[str, List[str]] = {}  # merged_name -> original group names

        # Stats
        self.original_count = 0
        self.optimized_count = 0

    def _log(self, msg: str):
        """Print if verbose mode."""
        if self.verbose:
            print(f"[EquationGroupOptimizer] {msg}")

    def _compute_equation_signature(self, group: NeuronGroup) -> str:
        """
        Compute a hash signature for a NeuronGroup's equations.

        Two groups with identical signatures can be safely merged.
        """
        eq_type = detect_equation_type(group)
        if eq_type:
            return f"type_{eq_type}"

        # Fallback: hash the equation string
        if hasattr(group, 'equations') and group.equations is not None:
            eqs_str = str(group.equations)
        else:
            eqs_str = ""

        threshold = str(getattr(group, 'threshold', ''))
        reset = str(getattr(group, 'reset', ''))

        # Normalize whitespace
        eqs_str = ' '.join(eqs_str.split())
        threshold = ' '.join(threshold.split())
        reset = ' '.join(reset.split())

        combined = f"{eqs_str}||{threshold}||{reset}"
        return hashlib.md5(combined.encode()).hexdigest()[:16]

    def _extract_group_metadata(self, group: NeuronGroup, system_name: str = "") -> GroupMetadata:
        """Extract all metadata from a NeuronGroup for later reconstruction."""
        eq_type = detect_equation_type(group)

        # Get canonical equations if type detected
        if eq_type and eq_type in EQUATION_TEMPLATES:
            equations = EQUATION_TEMPLATES[eq_type]
            threshold, reset = THRESHOLD_RESET[eq_type]
        else:
            # Fallback: extract actual equations from the group
            # Brian2 stores equations in different ways
            if hasattr(group, 'equations') and group.equations is not None:
                equations = str(group.equations)
            elif hasattr(group, '_equations') and group._equations is not None:
                equations = str(group._equations)
            else:
                # Last resort: use a generic LIF model
                equations = '''
                dv/dt = (v_rest - v + I_syn) / tau_m : volt (unless refractory)
                I_syn = I_exc - I_inh : volt
                dI_exc/dt = -I_exc / tau_e : volt
                dI_inh/dt = -I_inh / tau_i : volt
                I_ext : volt
                tau_m : second
                v_rest : volt
                v_thresh : volt
                tau_e : second
                tau_i : second
                '''
            # Normalize units: Brian2 requires full unit names
            # V -> volt, s -> second, etc.
            equations = equations.replace(' : V\n', ' : volt\n')
            equations = equations.replace(' : V ', ' : volt ')
            equations = equations.replace(' : s\n', ' : second\n')
            equations = equations.replace(' : s ', ' : second ')
            equations = equations.replace('(shared)', ': 1 (shared)')
            threshold = str(getattr(group, 'threshold', 'v > v_thresh'))
            reset = str(getattr(group, 'reset', 'v = v_rest'))

        method = getattr(group, 'method', 'euler')
        refractory = getattr(group, 'refractory', 2*ms)

        # Extract current parameter values
        params = {}
        state_vars = {}

        if hasattr(group, 'variables'):
            for var_name in group.variables:
                try:
                    val = getattr(group, var_name, None)
                    if val is not None:
                        # Get unit from variable object for later reconstruction
                        var_obj = group.variables.get(var_name)
                        unit = getattr(var_obj, 'unit', None) if var_obj else None

                        # Get actual array value from VariableView
                        if hasattr(val, '__array__'):
                            val = np.array(val)
                        elif hasattr(val, '_data'):
                            val = np.array(val._data)

                        # Check if it's an array (per-neuron) or scalar parameter
                        if isinstance(val, np.ndarray) and len(val) == len(group):
                            # Store with unit for proper reconstruction
                            state_vars[var_name] = (val, unit)
                        elif isinstance(val, np.ndarray) and len(val) == 1:
                            # Scalar stored as 1-element array
                            params[var_name] = (val[0], unit)
                        elif not isinstance(val, np.ndarray):
                            params[var_name] = (val, unit)
                except Exception:
                    pass

        return GroupMetadata(
            name=group.name,
            equation_signature=self._compute_equation_signature(group),
            equation_type=eq_type or 'unknown',
            size=len(group),
            equations=equations,
            threshold=threshold,
            reset=reset,
            method=method,
            refractory=refractory,
            params=params,
            state_vars=state_vars,
            system_name=system_name,
            original_group=group
        )

    def _extract_synapse_metadata(self, synapse: Synapses) -> SynapseMetadata:
        """Extract metadata from a Synapse for remapping."""
        source_name = synapse.source.name
        target_name = synapse.target.name

        try:
            source_indices = np.array(synapse.i[:])
            target_indices = np.array(synapse.j[:])
        except Exception:
            source_indices = np.array([])
            target_indices = np.array([])

        delays = None
        weights = None
        try:
            if hasattr(synapse, 'delay'):
                delays = np.array(synapse.delay[:])
            if hasattr(synapse, 'w_syn'):
                weights = np.array(synapse.w_syn[:])
        except Exception:
            pass

        on_pre = getattr(synapse, 'on_pre', '')
        model = getattr(synapse, 'model', '')

        return SynapseMetadata(
            name=synapse.name,
            source_name=source_name,
            target_name=target_name,
            source_indices=source_indices,
            target_indices=target_indices,
            delays=delays,
            weights=weights,
            on_pre=str(on_pre),
            model=str(model),
            original_synapse=synapse
        )

    def scan_network(self):
        """Scan the network and collect all group/synapse metadata."""
        self._log("Scanning network for objects...")

        if self.network is None:
            self._log("ERROR: No network provided")
            return

        for obj in self.network.objects:
            if isinstance(obj, NeuronGroup):
                meta = self._extract_group_metadata(obj)
                self.group_metadata[obj.name] = meta

                sig = meta.equation_signature
                if sig not in self.equivalence_classes:
                    self.equivalence_classes[sig] = []
                self.equivalence_classes[sig].append(obj.name)

            elif isinstance(obj, Synapses):
                meta = self._extract_synapse_metadata(obj)
                self.synapse_metadata[obj.name] = meta

        self.original_count = len(self.group_metadata) + len(self.synapse_metadata)
        self._log(f"Found {len(self.group_metadata)} NeuronGroups")
        self._log(f"Found {len(self.synapse_metadata)} Synapses")
        self._log(f"Found {len(self.equivalence_classes)} unique equation signatures")

        for sig, groups in self.equivalence_classes.items():
            if len(groups) > 1:
                names = [self.group_metadata[g].name for g in groups]
                self._log(f"  Merge candidate: {len(groups)} groups -> {sig}")
                self._log(f"    {', '.join(names[:5])}{'...' if len(names) > 5 else ''}")

    def get_merge_plan(self) -> Dict[str, List[str]]:
        """Get the planned merge operations."""
        plan = {}
        for sig, groups in self.equivalence_classes.items():
            if len(groups) > 1:
                plan[sig] = groups
        return plan

    def estimate_reduction(self) -> Tuple[int, int]:
        """Estimate the reduction in object count."""
        n_groups = len(self.group_metadata)
        n_equiv = len([g for g in self.equivalence_classes.values() if len(g) > 1])
        estimated = n_equiv + len([g for g in self.equivalence_classes.values() if len(g) == 1])
        return (n_groups, estimated)

    def create_merged_group(self, signature: str, group_names: List[str]) -> NeuronGroup:
        """Create a merged NeuronGroup from multiple groups with identical equations."""
        if not group_names:
            raise ValueError("Cannot merge empty list of groups")

        first_meta = self.group_metadata[group_names[0]]
        total_size = sum(self.group_metadata[name].size for name in group_names)

        indexed_params = {}
        indexed_units = {}
        system_ids = np.zeros(total_size, dtype=int)

        # Track which params are homogeneous (same across all groups)
        homogeneous_params = {}
        homogeneous_units = {}

        current_idx = 0
        for sys_id, name in enumerate(group_names):
            meta = self.group_metadata[name]
            meta.start_idx = current_idx
            meta.end_idx = current_idx + meta.size
            self.index_map[name] = (meta.start_idx, meta.end_idx)

            system_ids[meta.start_idx:meta.end_idx] = sys_id

            for param_name, param_tuple in meta.state_vars.items():
                # Unpack (value, unit) tuple
                if isinstance(param_tuple, tuple):
                    param_val, unit = param_tuple
                else:
                    param_val = param_tuple
                    unit = None

                if isinstance(param_val, np.ndarray):
                    # Check if all values are the array are the same (homogeneous)
                    unique_vals = np.unique(param_val)
                    is_homogeneous = len(unique_vals) == 1

                    if is_homogeneous:
                        # All neurons have same value - treat as homogeneous scalar
                        scalar_val = unique_vals[0]
                        if param_name not in homogeneous_params:
                            homogeneous_params[param_name] = scalar_val
                            homogeneous_units[param_name] = unit
                        # Check if all groups have same value
                        elif homogeneous_params[param_name] != scalar_val:
                            # Different across groups - need to index
                            if param_name not in indexed_params:
                                indexed_params[param_name] = np.full(total_size, homogeneous_params[param_name], dtype=type(scalar_val))
                                indexed_units[param_name] = homogeneous_units[param_name]
                            indexed_params[param_name][meta.start_idx:meta.end_idx] = scalar_val
                    else:
                        # Per-neuron parameter with varying values - add to indexed array
                        if param_name not in indexed_params:
                            indexed_params[param_name] = np.zeros(total_size, dtype=type(param_val[0]) if len(param_val) > 0 else float)
                            indexed_units[param_name] = unit
                        indexed_params[param_name][meta.start_idx:meta.end_idx] = param_val

            current_idx += meta.size

        merged_name = f"merged_{signature.replace('type_', '')}"
        self._log(f"Creating merged group '{merged_name}' with {total_size} neurons from {len(group_names)} groups")

        merged = NeuronGroup(
            total_size,
            model=first_meta.equations,
            threshold=first_meta.threshold,
            reset=first_meta.reset,
            refractory=first_meta.refractory,
            method=first_meta.method,
            name=merged_name,
            namespace={}
        )

        # Initialize homogeneous (scalar) parameters - same for all neurons
        for param_name, param_val in homogeneous_params.items():
            if hasattr(merged, param_name):
                try:
                    # Apply unit if available
                    unit = homogeneous_units.get(param_name)
                    if unit is not None:
                        param_val = param_val * unit
                    setattr(merged, param_name, param_val)
                except Exception as e:
                    self._log(f"Warning: Could not set homogeneous {param_name}: {e}")

        # Initialize indexed parameters (per-neuron values that vary across subpopulations)
        for param_name, param_vals in indexed_params.items():
            if hasattr(merged, param_name):
                try:
                    # Apply unit if available
                    unit = indexed_units.get(param_name)
                    if unit is not None:
                        param_vals = param_vals * unit
                    setattr(merged, param_name, param_vals)
                except Exception as e:
                    self._log(f"Warning: Could not set indexed {param_name}: {e}")

        # Store mapping info in optimizer (not on Brian2 object)
        self._merged_system_ids[merged_name] = system_ids
        self._merged_original_groups[merged_name] = group_names

        return merged

    def remap_synapse(self, syn_meta: SynapseMetadata) -> Optional[Synapses]:
        """Remap a synapse to use merged group indices."""
        source_start, source_end = self.index_map.get(syn_meta.source_name, (0, 0))
        target_start, target_end = self.index_map.get(syn_meta.target_name, (0, 0))

        if source_start == source_end or target_start == target_end:
            self._log(f"Warning: Synapse '{syn_meta.name}' has unmapped source/target")
            return None

        source_merged = None
        target_merged = None
        for sig, merged in self.merged_groups.items():
            if syn_meta.source_name in getattr(merged, '_original_groups', []):
                source_merged = merged
            if syn_meta.target_name in getattr(merged, '_original_groups', []):
                target_merged = merged

        if source_merged is None or target_merged is None:
            return None

        self._log(f"Remapping synapse '{syn_meta.name}'")

        new_source_indices = syn_meta.source_indices + source_start
        new_target_indices = syn_meta.target_indices + target_start

        new_syn = Synapses(
            source_merged, target_merged,
            model=syn_meta.model if syn_meta.model else 'w_syn : 1',
            on_pre=syn_meta.on_pre if syn_meta.on_pre else 'I_exc_post += w_syn*0.1*mV',
            name=f"remapped_{syn_meta.name}"
        )

        if len(new_source_indices) > 0:
            new_syn.connect(i=new_source_indices, j=new_target_indices)

        if syn_meta.delays is not None and len(syn_meta.delays) > 0:
            new_syn.delay = syn_meta.delays
        if syn_meta.weights is not None and len(syn_meta.weights) > 0:
            new_syn.w_syn = syn_meta.weights

        return new_syn

    def create_monitors(self, merged_group: NeuronGroup, original_names: List[str]) -> Dict[str, SpikeMonitor]:
        """Create SpikeMonitors for each original subgroup."""
        monitors = {}

        for name in original_names:
            if name not in self.index_map:
                continue
            start, end = self.index_map[name]

            mon = SpikeMonitor(
                merged_group,
                name=f"mon_{name}",
                record=list(range(start, end))  # Use list instead of numpy array
            )
            monitors[name] = mon

        return monitors

    def optimize(self, dry_run: bool = False) -> 'Network':
        """Perform the full optimization."""
        self._log("=" * 50)
        self._log("Starting optimization")
        self._log("=" * 50)

        self.scan_network()

        merge_plan = self.get_merge_plan()
        orig, opt = self.estimate_reduction()

        self._log(f"\nMerge plan: {orig} groups -> ~{opt} groups")

        if dry_run:
            self._log("\n[DRY RUN] Would perform the following merges:")
            for sig, groups in merge_plan.items():
                self._log(f"  {sig}: {len(groups)} groups")
            return None

        self._log("\nCreating merged groups...")
        for sig, group_names in merge_plan.items():
            # Skip unknown equation types - they can't be safely merged
            first_meta = self.group_metadata.get(group_names[0])
            if first_meta and first_meta.equation_type == 'unknown':
                self._log(f"  Keeping separate {sig}: unknown equation type ({len(group_names)} groups)")
                # Add groups individually instead of merging
                for name in group_names:
                    meta = self.group_metadata[name]
                    self.index_map[name] = (0, meta.size)
                    self.merged_groups[f"unmerged_{name}"] = meta.original_group
                continue
            merged = self.create_merged_group(sig, group_names)
            self.merged_groups[sig] = merged

            monitors = self.create_monitors(merged, group_names)
            self.monitors.update(monitors)

        for sig, group_names in self.equivalence_classes.items():
            if len(group_names) == 1:
                name = group_names[0]
                meta = self.group_metadata[name]
                self.index_map[name] = (0, meta.size)
                self.merged_groups[f"single_{name}"] = meta.original_group

        self._log("\nRemapping synapses...")
        for syn_name, syn_meta in self.synapse_metadata.items():
            new_syn = self.remap_synapse(syn_meta)
            if new_syn is not None:
                self.remapped_synapses[syn_name] = new_syn

        self._log("\nBuilding optimized network...")
        optimized = Network(name='optimized_snn')

        for merged in self.merged_groups.values():
            optimized.add(merged)

        for mon in self.monitors.values():
            optimized.add(mon)

        for syn in self.remapped_synapses.values():
            optimized.add(syn)

        self.optimized_count = len(self.merged_groups) + len(self.remapped_synapses)

        self._log("\n" + "=" * 50)
        self._log(f"Optimization complete!")
        self._log(f"  Original: {self.original_count} objects")
        self._log(f"  Optimized: {self.optimized_count} objects")
        self._log(f"  Reduction: {100*(1-self.optimized_count/self.original_count):.1f}%")
        self._log("=" * 50)

        return optimized

    def get_benchmark_data(self) -> Dict[str, Any]:
        """Get benchmark data for before/after comparison."""
        return {
            'original_group_count': len(self.group_metadata),
            'original_synapse_count': len(self.synapse_metadata),
            'original_total': self.original_count,
            'equivalence_class_count': len(self.equivalence_classes),
            'merged_group_count': len(self.merged_groups),
            'remapped_synapse_count': len(self.remapped_synapses),
            'optimized_total': self.optimized_count,
            'reduction_percent': 100*(1-self.optimized_count/self.original_count) if self.original_count > 0 else 0,
            'merge_plan': {sig: len(groups) for sig, groups in self.get_merge_plan().items()},
        }


def analyze_network(network: Network) -> Dict[str, Any]:
    """Quick analysis function to understand network structure."""
    optimizer = EquationGroupOptimizer(network, verbose=False)
    optimizer.scan_network()

    return {
        'group_count': len(optimizer.group_metadata),
        'synapse_count': len(optimizer.synapse_metadata),
        'unique_equations': len(optimizer.equivalence_classes),
        'merge_candidates': {sig: len(groups) for sig, groups in optimizer.get_merge_plan().items()},
        'estimated_reduction': optimizer.estimate_reduction(),
    }
