"""
🐉 Volatility Module - Système Saiyan v0.2

GARCH-based volatility modeling for dynamic position sizing and risk management.
"""

from .garch_model import GARCHVolatilityModel, EGARCHVolatilityModel

__all__ = ['GARCHVolatilityModel', 'EGARCHVolatilityModel']
