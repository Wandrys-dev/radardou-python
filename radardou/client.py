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

    Exemplo:
        from radardou import RadarDOU
        with RadarDOU(api_key="sua_api_key") as client:
            resultados = client.buscar(date_from="2026-01-01")
            pub = client.obter_publicacao("12345")
    """

    DEFAULT_BASE_URL = "https://www.radar-dou.com/api/v1"

    def __init__(self, api_key, base_url=None, timeout=30, auto_session=True):
        if not api_key:
            raise AuthenticationError(
                "API Key e obrigatoria. Obtenha em https://www.radar-dou.com/api-keys",
                code="API_KEY_REQUIRED"
            )
        self._api_key = api_key
        self._base_url = (base_url or self.DEFAULT_BASE_URL).rstrip("/")
        self._timeout = timeout
        self._sdk_version = __version__
        self._session_manager = SessionManager(self)
        self._http_session = requests.Session()
        self._http_session.headers.update({
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
            "User-Agent": f"RadarDOU-Python/{self._sdk_version}",
            "X-SDK-Version": self._sdk_version,
        })
        if auto_session:
            try:
                self._session_manager.start_session()
            except SessionConflictError:
                raise
            except Exception:
                pass

    def _request(self, method, endpoint, params=None, json=None, **kwargs):
        url = urljoin(self._base_url + "/", endpoint.lstrip("/"))
        try:
            response = self._http_session.request(
                method=method, url=url, params=params, json=json,
                timeout=self._timeout, **kwargs
            )
        except requests.exceptions.Timeout:
            raise APIError("Timeout na requisicao.", code="TIMEOUT")
        except requests.exceptions.ConnectionError:
            raise APIError("Erro de conexao.", code="CONNECTION_ERROR")
        return self._handle_response(response)

    def _handle_response(self, response):
        try:
            data = response.json()
        except ValueError:
            data = {"error": response.text}
        if response.status_code in (200, 201):
            return data
        error_message = data.get("error") or data.get("message") or "Erro desconhecido"
        error_code = data.get("code", "UNKNOWN_ERROR")
        if response.status_code == 400:
            raise APIError(error_message, code=error_code, status_code=400, details=data.get("details"))
        if response.status_code == 401:
            raise AuthenticationError(error_message, code=error_code, details=data.get("details"))
        if response.status_code == 403:
            if error_code == "SESSION_CONFLICT":
                raise SessionConflictError(
                    error_message, code=error_code,
                    active_ip=data.get("active_ip"), details=data.get("details")
                )
            raise AuthenticationError(error_message, code=error_code, details=data.get("details"))
        if response.status_code == 429:
            raise RateLimitError(
                error_message, code=error_code,
                limit=data.get("limit"), reset_at=data.get("reset_at"),
                details=data.get("details")
            )
        raise APIError(error_message, code=error_code,
                       status_code=response.status_code, details=data.get("details"))

    # ---------- Publicacoes ----------

    def buscar(self, query=None, date_from=None, date_to=None,
               secao=None, tipo=None, orgao=None, page=1, limit=20):
        """Busca publicacoes. Pelo menos um filtro e obrigatorio."""
        if not any([query, date_from, date_to, secao, tipo, orgao]):
            raise APIError(
                "Pelo menos um filtro e obrigatorio: query, date_from, date_to, secao, tipo ou orgao.",
                code="FILTER_REQUIRED"
            )
        params = {"page": page, "limit": min(limit, 100)}
        if query:     params["query"] = query
        if date_from: params["date_from"] = date_from
        if date_to:   params["date_to"] = date_to
        if secao:     params["secao"] = secao
        if tipo:      params["tipo"] = tipo
        if orgao:     params["orgao"] = orgao
        return self._request("GET", "/publications", params=params)

    def obter_publicacao(self, id):
        """Detalhes completos da publicacao (texto_html e texto_puro inclusos)."""
        return self._request("GET", f"/publications/{id}")

    # ---------- Alertas ----------

    def listar_alertas(self, page=1, limit=20, active_only=False):
        params = {"page": page, "limit": min(limit, 100)}
        if active_only:
            params["active"] = "true"
        return self._request("GET", "/alerts", params=params)

    def criar_alerta(self, name, search_criteria, description=None,
                     frequency="daily", email_notification=True, sound_alert=False):
        data = {
            "name": name,
            "searchCriteria": search_criteria,
            "frequency": frequency,
            "emailNotification": email_notification,
            "soundAlert": sound_alert,
        }
        if description:
            data["description"] = description
        return self._request("POST", "/alerts", json=data)

    # ---------- Favoritos, Colecoes, Vocabulario ----------

    def listar_favoritos(self, page=1, limit=20):
        return self._request("GET", "/favorites",
                             params={"page": page, "limit": min(limit, 100)})

    def adicionar_favorito(self, publication_id, notes=None):
        data = {"publicationId": publication_id}
        if notes:
            data["notes"] = notes
        return self._request("POST", "/favorites", json=data)

    def remover_favorito(self, publication_id):
        return self._request("DELETE", "/favorites",
                             params={"publicationId": publication_id})

    def listar_colecoes(self):
        return self._request("GET", "/collections")

    def criar_colecao(self, name, description=None):
        data = {"name": name}
        if description:
            data["description"] = description
        return self._request("POST", "/collections", json=data)

    def vocabulario(self):
        return self._request("GET", "/vocabulary")

    # ---------- Sessao ----------

    def validar_sessao(self):
        return self._session_manager.validate_session()

    def close(self):
        self._session_manager.end_session()
        self._http_session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass
