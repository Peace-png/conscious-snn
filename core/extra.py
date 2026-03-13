"""
Descaling, Scaling, and Export Utilities

For edge deployment and neuromorphic hardware compatibility.
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
import json


def descale_network(stats: Dict, scale_factor: float = 0.01) -> Dict:
    """
    Descale network statistics to minimal pattern.

    Preserves essential dynamics while reducing neurons.

    Args:
        stats: Full network statistics
        scale_factor: Reduction factor (0.01 = 1%)

    Returns:
        Descaled statistics preserving pattern
    """
    descaled = {}
    for name, stat in stats.items():
        descaled[name] = {
            'n_neurons': max(10, int(stat['n_neurons'] * scale_factor)),
            'oscillation_freq': stat['oscillation_freq'],  # Preserve
            'mean_firing_rate': stat['mean_firing_rate'],  # Preserve
            'pattern_preserved': True
        }
    return descaled


def scale_network(stats: Dict, scale_factor: float = 100.0) -> Dict:
    """
    Scale network back up to full resolution.

    Args:
        stats: Descaled network statistics
        scale_factor: Expansion factor (100 = 100x)

    Returns:
        Scaled statistics preserving pattern
    """
    scaled = {}
    for name, stat in stats.items():
        scaled[name] = {
            'n_neurons': int(stat['n_neurons'] * scale_factor),
            'oscillation_freq': stat['oscillation_freq'],
            'mean_firing_rate': stat['mean_firing_rate'],
            'pattern_preserved': True
        }
    return scaled


def extract_minimal_pattern(spike_times: np.ndarray, neuron_ids: np.ndarray,
                           system_names: List[str]) -> Dict:
    """
    Extract the minimal pattern that captures essential timing.

    This is the "pattern itself" - not the simulation.

    Args:
        spike_times: Array of spike timestamps (seconds)
        neuron_ids: Array of neuron IDs
        system_names: Names of systems

    Returns:
        Minimal pattern dict
    """
    if len(spike_times) == 0:
        return {'pattern': 'empty', 'n_spikes': 0}

    # Calculate inter-spike intervals
    isis = np.diff(np.sort(spike_times))

    # Extract rhythmic components via FFT
    fft = np.abs(np.fft.fft(isis))[:len(isis)//2]

    # Find dominant frequencies
    dt = np.mean(isis) if len(isis) > 0 else 1.0
    freqs = np.fft.fftfreq(len(isis), dt)[:len(isis)//2]

    # Get top 5 frequencies
    top_idx = np.argsort(fft)[-5:][::-1]
    dominant_freqs = freqs[top_idx].tolist()
    dominant_powers = fft[top_idx].tolist()

    return {
        'pattern': 'timing_map',
        'n_spikes': len(spike_times),
        'mean_isi': float(np.mean(isis)) if len(isis) > 0 else 0,
        'std_isi': float(np.std(isis)) if len(isis) > 0 else 0,
        'dominant_frequencies': [float(f) for f in dominant_freqs],
        'frequency_powers': [float(p) for p in dominant_powers],
        'duration': float(spike_times[-1] - spike_times[0]),
    }


def export_to_akida_format(spike_data: Dict, influence_matrix: np.ndarray,
                          output_file: str) -> str:
    """
    Export network to BrainChip Akida-compatible format.

    Akida uses:
    - 8-bit weights (quantized)
    - Event-based spikes
    - Layer-wise organization

    Args:
        spike_data: Spike timing data
        influence_matrix: Inter-system weights
        output_file: Output path

    Returns:
        Path to exported file
    """
    akida_format = {
        'version': '1.0',
        'format': 'akida_compatible',
        'layers': [],
        'weights': []
    }

    # Quantize influence matrix to 8-bit
    quantized = np.clip(influence_matrix * 127, -128, 127).astype(np.int8)

    # Export layers
    for name, data in spike_data.items():
        akida_format['layers'].append({
            'name': name,
            'n_neurons': data.get('n_neurons', 0),
            'spike_count': data.get('n_spikes', 0),
            'oscillation_hz': data.get('oscillation_freq', 0)
        })

    # Export weights as sparse list
    for i in range(len(quantized)):
        for j in range(len(quantized[i])):
            if quantized[i, j] != 0:
                akida_format['weights'].append({
                    'source': i,
                    'target': j,
                    'weight': int(quantized[i, j])
                })

    with open(output_file, 'w') as f:
        json.dump(akida_format, f, indent=2)

    return output_file


def export_to_nwb_format(spike_times: np.ndarray, neuron_ids: np.ndarray,
                        system_ids: np.ndarray, metadata: Dict,
                        output_file: str) -> str:
    """
    Export to NWB (Neurodata Without Borders) format.

    Standard neuroscience data format for compatibility.

    Args:
        spike_times: Spike timestamps
        neuron_ids: Neuron identifiers
        system_ids: System membership for each neuron
        metadata: Experimental metadata
        output_file: Output path (.nwb)

    Returns:
        Path to exported file
    """
    try:
        import h5py
    except ImportError:
        # Fallback to HDF5 without NWB namespace
        return export_to_hdf5(
            spike_times, neuron_ids, system_ids, metadata, output_file
        )

    with h5py.File(output_file, 'w') as f:
        # NWB structure
        nwb = f.create_group('root')
        nwb.attrs['namespace'] = 'NWB'
        nwb.attrs['version'] = '2.0'

        # Processing module
        proc = nwb.create_group('processing')
        spikes = proc.create_group('spikes')

        # Spike data
        spikes.create_dataset('timestamps', data=spike_times)
        spikes.create_dataset('neuron_ids', data=neuron_ids)
        spikes.create_dataset('system_ids', data=system_ids)

        # Metadata
        meta = nwb.create_group('general')
        for key, value in metadata.items():
            meta.attrs[key] = value

    return output_file


def export_to_hdf5(spike_times: np.ndarray, neuron_ids: np.ndarray,
                  system_ids: np.ndarray, metadata: Dict,
                  output_file: str) -> str:
    """
    Export to HDF5 format (general purpose).

    Args:
        spike_times: Spike timestamps
        neuron_ids: Neuron identifiers
        system_ids: System membership
        metadata: Metadata dict
        output_file: Output path

    Returns:
        Path to exported file
    """
    import h5py

    with h5py.File(output_file, 'w') as f:
        # Spike data
        f.create_dataset('spikes/timestamps', data=spike_times)
        f.create_dataset('spikes/neuron_ids', data=neuron_ids)
        f.create_dataset('spikes/system_ids', data=system_ids)

        # Metadata
        meta = f.create_group('metadata')
        for key, value in metadata.items():
            meta.attrs[key] = value

    return output_file


def export_to_lava_format(network_config: Dict, influence_matrix: np.ndarray,
                        output_dir: str) -> List[str]:
    """
    Export to Intel Lava format.

    Generates Python files for Lava process definitions.

    Args:
        network_config: Network configuration
        influence_matrix: Weight matrix
        output_dir: Output directory

    Returns:
        List of generated files
    """
    import os
    os.makedirs(output_dir, exist_ok=True)

    files = []

    # Generate process file
    process_file = f'{output_dir}/conscious_processes.py'
    with open(process_file, 'w') as f:
        f.write('"""\nLava Process Definitions for Conscious SNN\n"""\n\n')
        f.write('from lava.magma.core.process.process import AbstractProcess\n')
        f.write('from lava.magma.core.process.variable import Var\n')
        f.write('from lava.magma.core.process.ports.ports import InPort, OutPort\n\n')

        for name, config in network_config.items():
            f.write(f'''
class {name.capitalize()}Process(AbstractProcess):
    """Lava process for {name} system."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        shape = kwargs.get("shape", ({config['n_neurons']},))
        self.a_in = InPort(shape=shape)
        self.s_out = OutPort(shape=shape)
        self.v = Var(shape=shape, init=0)
        self.freq = Var(shape=(1,), init={config['oscillation_freq']})
''')

    files.append(process_file)

    return files


def compute_influence_signature(spike_data: Dict,
                               influence_matrix: np.ndarray) -> Dict:
    """
    Compute the influence signature of the network.

    This is the unique timing and influence pattern that characterizes
    the state of conscious processing.

    Args:
        spike_data: Spike data from each system
        influence_matrix: Weight matrix between systems

    Returns:
        Influence signature dict
    """
    signature = {
        'timing_signature': {},
        'influence_signature': {},
        'phase_coupling': {},
        'overall': {}
    }

    # Extract timing signatures
    for name, data in spike_data.items():
        if 'dominant_frequencies' in data:
            signature['timing_signature'][name] = data['dominant_frequencies']

    # Compute influence signature (weighted timing)
    systems = list(spike_data.keys())
    for i, source in enumerate(systems):
        for j, target in enumerate(systems):
            weight = influence_matrix[i, j] if i < len(influence_matrix) and j < len(influence_matrix[i]) else 0
            if weight > 0.1:
                key = f'{source}_to_{target}'
                signature['influence_signature'][key] = {
                    'weight': float(weight),
                    'source_freq': spike_data[source].get('dominant_frequencies', [0]),
                    'target_freq': spike_data[target].get('dominant_frequencies', [0])
                }

    # Phase coupling (simplified)
    for name, data in spike_data.items():
        if data.get('n_spikes', 0) > 0:
            signature['phase_coupling'][name] = {
                'mean_phase': data.get('mean_isi', 0) * 2 * np.pi,
                'phase_variance': data.get('std_isi', 0) ** 2
            }

    # Overall signature
    all_freqs = []
    for data in spike_data.values():
        all_freqs.extend(data.get('dominant_frequencies', []))

    signature['overall'] = {
        'total_spikes': sum(d.get('n_spikes', 0) for d in spike_data.values()),
        'unique_frequencies': len(set(f for f in all_freqs if f > 0)),
        'dominant_network_frequency': float(np.median([f for f in all_freqs if f > 0])) if all_freqs else 0
    }

    return signature
