"""
Exceções customizadas do SDK RadarDOU.
"""


class RadarDOUError(Exception):
    """Exceção base para todos os erros do RadarDOU SDK."""

    def __init__(self, message: str, code: str = None, details: dict = None):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)


class AuthenticationError(RadarDOUError):
    """
    Erro de autenticação.

    Ocorre quando:
    - API Key não fornecida
    - API Key inválida
    - API Key expirada
    - Assinatura não ativa
    """
    pass


class SessionConflictError(RadarDOUError):
    """
    Erro de conflito de sessão.

    Ocorre quando:
    - Outro IP já está usando esta API Key
    - Limite de usuários simultâneos atingido
    - Tentativa de uso compartilhado detectada
    """

    def __init__(self, message: str, active_ip: str = None, **kwargs):
        super().__init__(message, **kwargs)
        self.active_ip = active_ip


class RateLimitError(RadarDOUError):
    """
    Erro de limite de requisições.

    Ocorre quando o limite de requisições do plano foi atingido.
    """

    def __init__(self, message: str, limit: int = None, reset_at: str = None, **kwargs):
        super().__init__(message, **kwargs)
        self.limit = limit
        self.reset_at = reset_at


class APIError(RadarDOUError):
    """
    Erro genérico da API.

    Ocorre para outros erros não categorizados.
    """

    def __init__(self, message: str, status_code: int = None, **kwargs):
        super().__init__(message, **kwargs)
        self.status_code = status_code
