"""
Cliente principal do SDK RadarDOU.
"""

import requests
from typing import Optional, Dict, Any, List
from urllib.parse import urljoin

from .exceptions import (
    AuthenticationError,
    SessionConflictError,
    RateLimitError,
    APIError
)
from .session import SessionManager
from .version import __version__


class RadarDOU:
    """
    Cliente oficial para a API do Radar DOU.

    Exemplo de uso:
        from radardou import RadarDOU

        client = RadarDOU(api_key="sua_api_key")

        # Buscar publicações
        resultados = client.buscar("licitação")

        # Buscar por órgão específico
        resultados = client.buscar("contrato", orgao="Ministério da Saúde")

        # Ao finalizar, encerre a sessão
        client.close()

    Ou usando context manager:
        with RadarDOU(api_key="sua_api_key") as client:
            resultados = client.buscar("licitação")
    """

    DEFAULT_BASE_URL = "https://api.radar-dou.com/v1"

    def __init__(
        self,
        api_key: str,
        base_url: str = None,
        timeout: int = 30,
        auto_session: bool = True
    ):
        """
        Inicializa o cliente RadarDOU.

        Args:
            api_key: Sua API Key de assinante do Radar DOU
            base_url: URL base da API (opcional, padrão: https://api.radar-dou.com/v1)
            timeout: Timeout para requisições em segundos (padrão: 30)
            auto_session: Se True, inicia sessão automaticamente (padrão: True)

        Raises:
            AuthenticationError: Se a API Key não for fornecida
        """
        if not api_key:
            raise AuthenticationError(
                "API Key é obrigatória. Obtenha sua chave em https://radar-dou.com/api-keys",
                code="API_KEY_REQUIRED"
            )

        self._api_key = api_key
        self._base_url = (base_url or self.DEFAULT_BASE_URL).rstrip("/")
        self._timeout = timeout
        self._sdk_version = __version__
        self._session_manager = SessionManager(self)
        self._http_session = requests.Session()

        # Configura headers padrão
        self._http_session.headers.update({
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
            "User-Agent": f"RadarDOU-Python/{self._sdk_version}",
            "X-SDK-Version": self._sdk_version
        })

        # Inicia sessão automaticamente se configurado
        if auto_session:
            self._start_session()

    def _start_session(self) -> None:
        """Inicia a sessão com validação de IP."""
        try:
            self._session_manager.start_session()
        except SessionConflictError:
            raise
        except Exception as e:
            # Se falhar ao iniciar sessão, ainda permite uso (fallback)
            pass

    def _request(
        self,
        method: str,
        endpoint: str,
        params: Dict[str, Any] = None,
        json: Dict[str, Any] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Faz uma requisição para a API.

        Args:
            method: Método HTTP (GET, POST, etc.)
            endpoint: Endpoint da API (ex: /search)
            params: Parâmetros de query string
            json: Body da requisição em JSON

        Returns:
            Resposta da API em formato dict

        Raises:
            AuthenticationError: Se a API Key é inválida
            SessionConflictError: Se há conflito de sessão/IP
            RateLimitError: Se o limite de requisições foi atingido
            APIError: Para outros erros da API
        """
        url = urljoin(self._base_url + "/", endpoint.lstrip("/"))

        # Adiciona session_id se disponível
        if self._session_manager.session_id:
            if json is None:
                json = {}
            if isinstance(json, dict) and "session_id" not in json:
                json["_session_id"] = self._session_manager.session_id

        try:
            response = self._http_session.request(
                method=method,
                url=url,
                params=params,
                json=json,
                timeout=self._timeout,
                **kwargs
            )
        except requests.exceptions.Timeout:
            raise APIError(
                "Timeout na requisição. Tente novamente.",
                code="TIMEOUT"
            )
        except requests.exceptions.ConnectionError:
            raise APIError(
                "Erro de conexão. Verifique sua internet.",
                code="CONNECTION_ERROR"
            )

        return self._handle_response(response)

    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """Processa a resposta da API e trata erros."""
        try:
            data = response.json()
        except ValueError:
            data = {"message": response.text}

        if response.status_code == 200:
            return data

        error_message = data.get("message", "Erro desconhecido")
        error_code = data.get("code", "UNKNOWN_ERROR")

        if response.status_code == 401:
            raise AuthenticationError(
                error_message,
                code=error_code,
                details=data.get("details")
            )

        if response.status_code == 403:
            if error_code == "SESSION_CONFLICT":
                raise SessionConflictError(
                    error_message,
                    code=error_code,
                    active_ip=data.get("active_ip"),
                    details=data.get("details")
                )
            raise AuthenticationError(
                error_message,
                code=error_code,
                details=data.get("details")
            )

        if response.status_code == 429:
            raise RateLimitError(
                error_message,
                code=error_code,
                limit=data.get("limit"),
                reset_at=data.get("reset_at"),
                details=data.get("details")
            )

        raise APIError(
            error_message,
            code=error_code,
            status_code=response.status_code,
            details=data.get("details")
        )

    # ========================================
    # Métodos de Busca
    # ========================================

    def buscar(
        self,
        termo: str,
        data_inicio: str = None,
        data_fim: str = None,
        orgao: str = None,
        tipo: str = None,
        secao: int = None,
        pagina: int = 1,
        limite: int = 20
    ) -> Dict[str, Any]:
        """
        Busca publicações no DOU.

        Args:
            termo: Termo de busca
            data_inicio: Data inicial no formato YYYY-MM-DD
            data_fim: Data final no formato YYYY-MM-DD
            orgao: Filtrar por órgão específico
            tipo: Tipo de publicação (ato, portaria, edital, etc.)
            secao: Seção do DOU (1, 2, 3 ou None para todas)
            pagina: Número da página (padrão: 1)
            limite: Quantidade de resultados por página (padrão: 20, máx: 100)

        Returns:
            Dict com resultados da busca

        Example:
            >>> client.buscar("licitação", orgao="Ministério da Saúde")
            {
                "resultados": [...],
                "total": 150,
                "pagina": 1,
                "total_paginas": 8
            }
        """
        params = {
            "q": termo,
            "pagina": pagina,
            "limite": min(limite, 100)
        }

        if data_inicio:
            params["data_inicio"] = data_inicio
        if data_fim:
            params["data_fim"] = data_fim
        if orgao:
            params["orgao"] = orgao
        if tipo:
            params["tipo"] = tipo
        if secao:
            params["secao"] = secao

        return self._request("GET", "/search", params=params)

    def obter_publicacao(self, id: str) -> Dict[str, Any]:
        """
        Obtém detalhes de uma publicação específica.

        Args:
            id: ID da publicação

        Returns:
            Dict com detalhes da publicação
        """
        return self._request("GET", f"/publicacoes/{id}")

    def listar_edicoes(
        self,
        data: str = None,
        secao: int = None,
        pagina: int = 1,
        limite: int = 20
    ) -> Dict[str, Any]:
        """
        Lista edições do DOU.

        Args:
            data: Data específica no formato YYYY-MM-DD
            secao: Seção do DOU (1, 2 ou 3)
            pagina: Número da página
            limite: Quantidade por página

        Returns:
            Dict com lista de edições
        """
        params = {"pagina": pagina, "limite": limite}

        if data:
            params["data"] = data
        if secao:
            params["secao"] = secao

        return self._request("GET", "/edicoes", params=params)

    # ========================================
    # Métodos de Alertas
    # ========================================

    def listar_alertas(self) -> Dict[str, Any]:
        """
        Lista todos os alertas configurados.

        Returns:
            Dict com lista de alertas
        """
        return self._request("GET", "/alertas")

    def criar_alerta(
        self,
        nome: str,
        termos: List[str],
        orgaos: List[str] = None,
        tipos: List[str] = None,
        secoes: List[int] = None,
        email_notificacao: bool = True
    ) -> Dict[str, Any]:
        """
        Cria um novo alerta de monitoramento.

        Args:
            nome: Nome do alerta
            termos: Lista de termos para monitorar
            orgaos: Lista de órgãos para filtrar (opcional)
            tipos: Lista de tipos de publicação (opcional)
            secoes: Lista de seções do DOU (opcional)
            email_notificacao: Receber notificação por email (padrão: True)

        Returns:
            Dict com dados do alerta criado
        """
        data = {
            "nome": nome,
            "termos": termos,
            "email_notificacao": email_notificacao
        }

        if orgaos:
            data["orgaos"] = orgaos
        if tipos:
            data["tipos"] = tipos
        if secoes:
            data["secoes"] = secoes

        return self._request("POST", "/alertas", json=data)

    def atualizar_alerta(self, id: str, **kwargs) -> Dict[str, Any]:
        """
        Atualiza um alerta existente.

        Args:
            id: ID do alerta
            **kwargs: Campos a serem atualizados

        Returns:
            Dict com dados do alerta atualizado
        """
        return self._request("PATCH", f"/alertas/{id}", json=kwargs)

    def excluir_alerta(self, id: str) -> Dict[str, Any]:
        """
        Exclui um alerta.

        Args:
            id: ID do alerta

        Returns:
            Dict com confirmação de exclusão
        """
        return self._request("DELETE", f"/alertas/{id}")

    # ========================================
    # Métodos de Conta e Uso
    # ========================================

    def obter_uso(self) -> Dict[str, Any]:
        """
        Obtém informações de uso da API.

        Returns:
            Dict com estatísticas de uso:
            - requisicoes_hoje: Número de requisições hoje
            - requisicoes_mes: Número de requisições no mês
            - limite_hora: Limite de requisições por hora do plano
            - limite_mes: Limite mensal do plano
            - plano: Nome do plano atual
        """
        return self._request("GET", "/uso")

    def obter_conta(self) -> Dict[str, Any]:
        """
        Obtém informações da conta.

        Returns:
            Dict com dados da conta e plano
        """
        return self._request("GET", "/conta")

    # ========================================
    # Gerenciamento de Sessão
    # ========================================

    def validar_sessao(self) -> bool:
        """
        Valida se a sessão atual ainda é válida.

        Returns:
            True se a sessão é válida
        """
        return self._session_manager.validate_session()

    def close(self) -> None:
        """
        Encerra a sessão e libera recursos.

        Deve ser chamado ao finalizar o uso do cliente.
        """
        self._session_manager.end_session()
        self._http_session.close()

    # ========================================
    # Context Manager
    # ========================================

    def __enter__(self) -> "RadarDOU":
        """Permite uso com 'with' statement."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Encerra sessão ao sair do context."""
        self.close()

    def __del__(self) -> None:
        """Cleanup ao destruir o objeto."""
        try:
            self.close()
        except Exception:
            pass
