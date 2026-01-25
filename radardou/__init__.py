"""
RadarDOU SDK - Cliente Python para a API do Radar DOU
======================================================

SDK oficial para integração com a API do Radar DOU.
Requer uma API Key válida de assinante para funcionamento.

Uso básico:
    from radardou import RadarDOU

    client = RadarDOU(api_key="sua_api_key")
    resultado = client.buscar("licitação")
"""

from .client import RadarDOU
from .exceptions import (
    RadarDOUError,
    AuthenticationError,
    SessionConflictError,
    RateLimitError,
    APIError
)
from .version import __version__

__all__ = [
    "RadarDOU",
    "RadarDOUError",
    "AuthenticationError",
    "SessionConflictError",
    "RateLimitError",
    "APIError",
    "__version__"
]
