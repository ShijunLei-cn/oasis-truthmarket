"""
OASIS Market Simulation Framework
Common module library providing core functionality for market simulation
"""

from .database import MarketDatabase
from .agents import AgentManager
from .logging import ActionLogger, SimulationLogger
from .phases import (
    MarketPhase,
    SellerListingPhase,
    BuyerPurchasePhase,
    BuyerRatingPhase,
    CommunicationPhase
)
from .simulation import MarketSimulation, run_single_simulation

__version__ = '1.0.0'

__all__ = [
    'MarketDatabase',
    'AgentManager',
    'ActionLogger',
    'SimulationLogger',
    'MarketPhase',
    'SellerListingPhase',
    'BuyerPurchasePhase',
    'BuyerRatingPhase',
    'CommunicationPhase',
    'MarketSimulation',
    'run_single_simulation'
]