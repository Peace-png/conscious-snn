"""
Connectivity Module - Inter-system connections and plasticity
"""

from .influence import (
    InfluenceMatrix,
    create_system_connections,
    compute_influence_signature,
)
from .plasticity import (
    STDPRule,
    HomeostaticRule,
    RewardModulatedSTDP,
)

__all__ = [
    'InfluenceMatrix',
    'create_system_connections',
    'compute_influence_signature',
    'STDPRule',
    'HomeostaticRule',
    'RewardModulatedSTDP',
]
