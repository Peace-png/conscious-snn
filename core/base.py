"""
Base Classes for Conscious SNN Architecture

SystemPopulation: Base class for biological system populations
ConsciousNetwork: Main network container
IntentInput: External intent input system
InfluenceMatrix: Inter-system influence weights

Uses detailed system modules from the systems/ package.
"""

from brian2 import (
    Network, NeuronGroup, Synapses, SpikeMonitor, StateMonitor,
    PoissonGroup, PoissonInput, TimedArray, Hz, ms, mV, nA,
    run, start_scope, defaultclock, collect, store, restore,
    profiling_summary
)
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
import json

from .config import ConsciousSNNConfig, NeuronParams
from .neurons import (
    AdaptiveExpLIF, IzhikevichNeuron, OscillatoryNeuron,
    CardiacNeuron, RespiratoryNeuron, PacemakerNeuron
)

# System modules imported lazily in methods to avoid circular import
# The import chain was: core/__init__.py -> core/base.py -> systems/cardiac.py -> core/neurons.py


@dataclass
class SystemPopulation:
    """
    Represents a biological system (e.g., brainstem, hippocampus).

    Attributes:
        name: System identifier
        neuron_group: Brian2 NeuronGroup
        monitors: Recording monitors
        params: Neuron parameters
        oscillation_freq: Target oscillation frequency (Hz)
    """
    name: str
    neuron_group: NeuronGroup
    monitors: Dict[str, Any] = field(default_factory=dict)
    params: NeuronParams = None
    oscillation_freq: float = 0.0
    scale_factor: float = 1.0

    def get_spike_times(self):
        """Get all spike times from this population."""
        # Look for any spike monitor (e.g., 'spikes', 'lc_spikes', etc.)
        for key, monitor in self.monitors.items():
            if 'spike' in key.lower() and hasattr(monitor, 't'):
                return np.array(monitor.t), np.array(monitor.i)
        return None, None

    def get_state(self, variable: str):
        """Get state variable trajectory."""
        if variable in self.monitors:
            return self.monitors[variable].t, self.monitors[variable][variable]
        return None, None

    def get_firing_rate(self, window_ms: float = 100.0):
        """Calculate population firing rate over time."""
        spike_t, spike_i = self.get_spike_times()
        if spike_t is None or len(spike_t) == 0:
            return None, None

        # Bin spikes
        N = len(self.neuron_group)
        duration = float(spike_t[-1])
        if duration <= 0:
            return None, None
        bin_size = window_ms / 1000.0
        n_bins = max(1, int(duration / bin_size))

        rates = []
        times = []
        for i in range(n_bins):
            t_start = i * bin_size
            t_end = (i + 1) * bin_size
            n_spikes = np.sum((spike_t >= t_start) & (spike_t < t_end))
            rate = n_spikes / (N * bin_size)  # Hz per neuron
            rates.append(rate)
            times.append((t_start + t_end) / 2)

        return np.array(times), np.array(rates)


class IntentInput:
    """
    External intent input system.

    Models intent as external spike input that illuminates specific layers.
    Implements the Cave Wall Principle: pattern always present, spike reveals it.
    """

    def __init__(self, network: 'ConsciousNetwork', config: ConsciousSNNConfig):
        self.network = network
        self.config = config
        self.intent_sources: Dict[str, PoissonGroup] = {}
        self.intent_connections: Dict[str, Synapses] = {}
        self.active_intents: Dict[str, float] = {}  # intent_name -> strength

    def create_intent(self, name: str, target_system: str,
                      connection_strength: float = 0.5,
                      n_sources: int = 100):
        """
        Create a new intent input source.

        Args:
            name: Intent identifier
            target_system: Which system to activate
            connection_strength: Synaptic weight to target
            n_sources: Number of Poisson sources
        """
        # Create Poisson input group (starts at 0 Hz)
        source = PoissonGroup(n_sources, rates=0*Hz, name=f'intent_{name}')
        self.intent_sources[name] = source

        # Connect to target system
        target_pop = self.network.systems.get(target_system)
        if target_pop:
            conn = Synapses(
                source,
                target_pop.neuron_group,
                on_pre=f'I_exc_post += {connection_strength}*nA',
                name=f'intent_{name}_to_{target_system}'
            )
            conn.connect(p=0.1)  # Sparse connectivity
            self.intent_connections[name] = conn

        # Add to network
        self.network.brian_network.add(source)
        if name in self.intent_connections:
            self.network.brian_network.add(self.intent_connections[name])

    def activate_intent(self, name: str, strength: float = 1.0,
                        duration_ms: float = None):
        """
        Activate an intent by setting firing rate.

        Args:
            name: Intent to activate
            strength: Activation strength (0-1, scales firing rate)
            duration_ms: Duration (None = until deactivated)
        """
        if name not in self.intent_sources:
            raise ValueError(f"Intent '{name}' not found")

        # Scale rate by strength (max ~200 Hz per source)
        base_rate = 50 * Hz  # Base rate
        rate = base_rate * strength * 4  # Up to 200 Hz

        self.intent_sources[name].rates = rate
        self.active_intents[name] = strength

        # TODO: Schedule deactivation if duration specified

    def deactivate_intent(self, name: str):
        """Deactivate an intent."""
        if name in self.intent_sources:
            self.intent_sources[name].rates = 0 * Hz
            del self.active_intents[name]

    def get_active_intents(self) -> Dict[str, float]:
        """Get currently active intents and their strengths."""
        return self.active_intents.copy()


class InfluenceMatrix:
    """
    Inter-system influence weight matrix.

    Defines how each system modulates every other system.
    Based on biological connectivity patterns.
    """

    def __init__(self, config: ConsciousSNNConfig):
        self.config = config
        self.matrix = config.influence_matrix.copy()
        self.system_names = config.system_names
        self._synapses: Dict[Tuple[str, str], Synapses] = {}

    def get_weight(self, source: str, target: str) -> float:
        """Get influence weight between systems."""
        i = self.system_names.index(source)
        j = self.system_names.index(target)
        return self.matrix[i, j]

    def set_weight(self, source: str, target: str, weight: float):
        """Set influence weight between systems."""
        i = self.system_names.index(source)
        j = self.system_names.index(target)
        self.matrix[i, j] = max(0.0, min(1.0, weight))

    def create_connection(self, source_pop: SystemPopulation,
                         target_pop: SystemPopulation,
                         connection_prob: float = 0.1) -> Synapses:
        """
        Create synaptic connection between two systems.

        Uses sparse random connectivity with weights from influence matrix.
        """
        source_name = source_pop.name
        target_name = target_pop.name
        weight = self.get_weight(source_name, target_name)

        if weight < 0.01:
            return None  # Skip very weak connections

        syn = Synapses(
            source_pop.neuron_group,
            target_pop.neuron_group,
            model='w_syn : 1',
            on_pre='I_exc_post += w_syn*0.3*mV',  # Simple addition - CUDA parallelizable
            name=f'syn_{source_name}_to_{target_name}'
        )
        syn.connect(p=connection_prob)
        syn.w_syn = weight
        syn.delay = 'rand() * 5*ms + 1*ms'  # 1-6ms random delay

        self._synapses[(source_name, target_name)] = syn
        return syn

    def export_matrix(self) -> np.ndarray:
        """Export influence matrix as numpy array."""
        return self.matrix.copy()

    def to_dict(self) -> dict:
        """Export as dictionary for serialization."""
        return {
            'system_names': self.system_names,
            'matrix': self.matrix.tolist(),
        }


class ConsciousNetwork:
    """
    Main network container for the Conscious SNN.

    Contains all biological systems, their interconnections,
    and the intent input system.

    Implements the full architecture:
    - 8 biological systems (brainstem, cardiac, respiratory, limbic,
      hippocampus, prefrontal, thalamus, dmn)
    - Inter-system connectivity via influence matrix
    - Intent input system (cave wall principle)
    - Recording and export infrastructure
    """

    def __init__(self, config: ConsciousSNNConfig = None):
        self.config = config or ConsciousSNNConfig()
        self.systems: Dict[str, SystemPopulation] = {}
        self.influence_matrix: InfluenceMatrix = None
        self.intent_system: IntentInput = None
        self.brian_network: Network = None

        # Monitors
        self.global_spike_monitor = None

        # State
        self._built = False
        self._running = False

    def build(self):
        """Build the complete network."""
        start_scope()

        # Create network
        self.brian_network = Network(name='conscious_snn')

        # Build all systems
        self._build_brainstem()
        self._build_cardiac()
        self._build_respiratory()
        self._build_limbic()
        self._build_hippocampus()
        self._build_prefrontal()
        self._build_thalamus()
        self._build_dmn()

        # Build inter-system connectivity
        self._build_connectivity()

        # Build intent system
        self.intent_system = IntentInput(self, self.config)

        # Add all to network
        for system in self.systems.values():
            self.brian_network.add(system.neuron_group)
            for monitor in system.monitors.values():
                self.brian_network.add(monitor)

        # Note: Global spike monitor removed - using per-system monitors instead
        # SpikeMonitor doesn't accept a list of groups directly

        self._built = True
        return self

    def _build_brainstem(self):
        """Build brainstem autonomic floor (~100M neurons abstracted)."""
        from systems.brainstem import BrainstemSystem
        counts = self.config.get_scaled_counts()
        N = counts['brainstem']

        # Use detailed BrainstemSystem
        brainstem = BrainstemSystem(n_neurons=N, name='brainstem')
        brainstem.build()

        # Get main population for compatibility
        groups = brainstem.get_groups()
        main_group = groups['reticular']  # Main population

        osc = self.config.oscillation_params['brainstem']
        system = SystemPopulation(
            name='brainstem',
            neuron_group=main_group,
            params=self.config.neuron_params['brainstem'],
            oscillation_freq=osc.frequency,
            scale_factor=self.config.scale.scale_factor
        )

        # Store detailed system reference
        system.detailed_system = brainstem

        # Add all monitors from detailed system
        system.monitors.update(brainstem.get_monitors())

        self.systems['brainstem'] = system

        # Add all groups to network
        for group in groups.values():
            self.brian_network.add(group)
        for monitor in brainstem.get_monitors().values():
            self.brian_network.add(monitor)
        # Add PoissonInput objects
        if hasattr(brainstem, 'get_inputs'):
            for inp in brainstem.get_inputs().values():
                self.brian_network.add(inp)

    def _build_cardiac(self):
        """Build intrinsic cardiac nervous system (~40k neurons)."""
        from systems.cardiac import CardiacSystem
        counts = self.config.get_scaled_counts()
        N = counts['cardiac']

        # Use detailed CardiacSystem
        cardiac = CardiacSystem(n_neurons=N, name='cardiac')
        cardiac.build()

        groups = cardiac.get_groups()
        main_group = groups['atrial']  # Main population

        osc = self.config.oscillation_params['cardiac']
        system = SystemPopulation(
            name='cardiac',
            neuron_group=main_group,
            params=self.config.neuron_params['cardiac'],
            oscillation_freq=osc.frequency
        )
        system.detailed_system = cardiac
        system.monitors.update(cardiac.get_monitors())

        self.systems['cardiac'] = system

        for group in groups.values():
            self.brian_network.add(group)
        for monitor in cardiac.get_monitors().values():
            self.brian_network.add(monitor)
        # Add PoissonInput objects
        if hasattr(cardiac, 'get_inputs'):
            for inp in cardiac.get_inputs().values():
                self.brian_network.add(inp)

    def _build_respiratory(self):
        """Build respiratory rhythm centers (~10k neurons)."""
        from systems.respiratory import RespiratorySystem
        counts = self.config.get_scaled_counts()
        N = counts['respiratory']

        # Use detailed RespiratorySystem
        respiratory = RespiratorySystem(n_neurons=N, name='respiratory')
        respiratory.build()

        groups = respiratory.get_groups()
        main_group = groups['pre_botzinger']  # Main rhythm generator

        osc = self.config.oscillation_params['respiratory']
        system = SystemPopulation(
            name='respiratory',
            neuron_group=main_group,
            params=self.config.neuron_params['respiratory'],
            oscillation_freq=osc.frequency
        )
        system.detailed_system = respiratory
        system.monitors.update(respiratory.get_monitors())

        self.systems['respiratory'] = system

        for group in groups.values():
            self.brian_network.add(group)
        for monitor in respiratory.get_monitors().values():
            self.brian_network.add(monitor)

    def _build_limbic(self):
        """Build limbic system (~130M neurons abstracted)."""
        from systems.limbic import LimbicSystem
        counts = self.config.get_scaled_counts()
        N = counts['limbic']

        # Use detailed LimbicSystem
        limbic = LimbicSystem(n_neurons=N, name='limbic')
        limbic.build()

        groups = limbic.get_groups()
        main_group = groups['acc']  # ACC is largest

        osc = self.config.oscillation_params['limbic']
        system = SystemPopulation(
            name='limbic',
            neuron_group=main_group,
            params=self.config.neuron_params['limbic'],
            oscillation_freq=osc.frequency
        )
        system.detailed_system = limbic
        system.monitors.update(limbic.get_monitors())

        self.systems['limbic'] = system

        for group in groups.values():
            self.brian_network.add(group)
        for monitor in limbic.get_monitors().values():
            self.brian_network.add(monitor)
        # Add PoissonInput objects
        if hasattr(limbic, 'get_inputs'):
            for inp in limbic.get_inputs().values():
                self.brian_network.add(inp)

    def _build_hippocampus(self):
        """Build hippocampus (~30M neurons: CA1, CA3, DG)."""
        from systems.hippocampus import HippocampusSystem
        counts = self.config.get_scaled_counts()
        N = counts['hippocampus']

        # Use detailed HippocampusSystem
        hippocampus = HippocampusSystem(n_neurons=N, name='hippocampus')
        hippocampus.build()

        groups = hippocampus.get_groups()
        main_group = groups['ca1']  # CA1 is output

        osc = self.config.oscillation_params['hippocampus']
        system = SystemPopulation(
            name='hippocampus',
            neuron_group=main_group,
            params=self.config.neuron_params['hippocampus'],
            oscillation_freq=osc.frequency
        )
        system.detailed_system = hippocampus
        system.monitors.update(hippocampus.get_monitors())

        self.systems['hippocampus'] = system

        for group in groups.values():
            self.brian_network.add(group)
        for monitor in hippocampus.get_monitors().values():
            self.brian_network.add(monitor)
        # Add PoissonInput objects
        if hasattr(hippocampus, 'get_inputs'):
            for inp in hippocampus.get_inputs().values():
                self.brian_network.add(inp)

    def _build_prefrontal(self):
        """Build prefrontal cortex (~200M neurons)."""
        from systems.prefrontal import PrefrontalSystem
        counts = self.config.get_scaled_counts()
        N = counts['prefrontal']

        # Use detailed PrefrontalSystem
        prefrontal = PrefrontalSystem(n_neurons=N, name='prefrontal')
        prefrontal.build()

        groups = prefrontal.get_groups()
        main_group = groups['dlpfc']  # dlPFC is core executive

        osc = self.config.oscillation_params['prefrontal']
        system = SystemPopulation(
            name='prefrontal',
            neuron_group=main_group,
            params=self.config.neuron_params['prefrontal'],
            oscillation_freq=osc.frequency
        )
        system.detailed_system = prefrontal
        system.monitors.update(prefrontal.get_monitors())

        self.systems['prefrontal'] = system

        for group in groups.values():
            self.brian_network.add(group)
        for monitor in prefrontal.get_monitors().values():
            self.brian_network.add(monitor)
        # Add PoissonInput objects
        if hasattr(prefrontal, 'get_inputs'):
            for inp in prefrontal.get_inputs().values():
                self.brian_network.add(inp)

    def _build_thalamus(self):
        """Build thalamus (~10M neurons, alpha rhythm generator)."""
        from systems.thalamus import ThalamusSystem
        counts = self.config.get_scaled_counts()
        N = counts['thalamus']

        # Use detailed ThalamusSystem
        thalamus = ThalamusSystem(n_neurons=N, name='thalamus')
        thalamus.build()

        groups = thalamus.get_groups()
        main_group = groups['relay_nuclei']  # Relay nuclei are core

        osc = self.config.oscillation_params['thalamus']
        system = SystemPopulation(
            name='thalamus',
            neuron_group=main_group,
            params=self.config.neuron_params['thalamus'],
            oscillation_freq=osc.frequency
        )
        system.detailed_system = thalamus
        system.monitors.update(thalamus.get_monitors())

        self.systems['thalamus'] = system

        for group in groups.values():
            self.brian_network.add(group)
        for monitor in thalamus.get_monitors().values():
            self.brian_network.add(monitor)

    def _build_dmn(self):
        """Build default mode network (distributed)."""
        from systems.dmn import DMNSystem
        counts = self.config.get_scaled_counts()
        N = counts['dmn']

        # Use detailed DMNSystem
        dmn = DMNSystem(n_neurons=N, name='dmn')
        dmn.build()

        groups = dmn.get_groups()
        main_group = groups['pcc']  # PCC is central hub

        osc = self.config.oscillation_params['dmn']
        system = SystemPopulation(
            name='dmn',
            neuron_group=main_group,
            params=self.config.neuron_params['dmn'],
            oscillation_freq=osc.frequency
        )
        system.detailed_system = dmn
        system.monitors.update(dmn.get_monitors())

        self.systems['dmn'] = system

        for group in groups.values():
            self.brian_network.add(group)
        for monitor in dmn.get_monitors().values():
            self.brian_network.add(monitor)

    def _build_connectivity(self):
        """Build inter-system connectivity based on influence matrix."""
        self.influence_matrix = InfluenceMatrix(self.config)

        for source_name, source_pop in self.systems.items():
            for target_name, target_pop in self.systems.items():
                if source_name != target_name:
                    syn = self.influence_matrix.create_connection(
                        source_pop, target_pop,
                        connection_prob=0.02  # 2% connectivity (reduced from 5%)
                    )
                    if syn is not None:
                        self.brian_network.add(syn)

    def run(self, duration_ms: float = None):
        """
        Run the simulation.

        Args:
            duration_ms: Duration in milliseconds (default from config)
        """
        if not self._built:
            self.build()

        duration = duration_ms or self.config.duration
        duration_sec = duration / 1000.0

        self._running = True
        # IMPORTANT: Run the explicit brian_network, not the magic network!
        self.brian_network.run(duration_sec * 1000 * ms)
        self._running = False

        return self

    def export_spikes(self, filename: str = None):
        """Export all spike data."""
        import h5py

        if filename is None:
            filename = f'{self.config.output_dir}/spikes.h5'

        with h5py.File(filename, 'w') as f:
            for name, system in self.systems.items():
                t, i = system.get_spike_times()
                if t is not None:
                    grp = f.create_group(name)
                    grp.create_dataset('timestamps', data=np.array(t))
                    grp.create_dataset('neuron_ids', data=np.array(i))
                    grp.attrs['n_neurons'] = len(system.neuron_group)
                    grp.attrs['oscillation_freq'] = system.oscillation_freq

        return filename

    def export_influence_matrix(self, filename: str = None):
        """Export influence matrix."""
        if filename is None:
            filename = f'{self.config.output_dir}/influence_matrix.json'

        with open(filename, 'w') as f:
            json.dump(self.influence_matrix.to_dict(), f, indent=2)

        return filename

    def get_system_stats(self) -> Dict[str, Dict]:
        """Get statistics for each system."""
        stats = {}
        for name, system in self.systems.items():
            t, rates = system.get_firing_rate()
            stats[name] = {
                'n_neurons': len(system.neuron_group),
                'oscillation_freq': system.oscillation_freq,
                'mean_firing_rate': float(np.mean(rates)) if rates is not None else 0,
                'std_firing_rate': float(np.std(rates)) if rates is not None else 0,
            }
        return stats
