"""
Gerenciamento de sessão e validação de IP.

Este módulo é responsável por:
- Registrar e validar sessões
- Detectar uso compartilhado de API Key
- Gerenciar heartbeat para manter sessão ativa
"""

import hashlib
import platform
import socket
import threading
import time
import uuid
from typing import Optional, Dict, Any


class SessionManager:
    """
    Gerenciador de sessão para controle de uso da API Key.

    Implementa:
    - Registro de sessão com fingerprint do dispositivo
    - Heartbeat automático para manter sessão ativa
    - Validação de sessão antes de cada requisição
    """

    def __init__(self, api_client):
        self._client = api_client
        self._session_id: Optional[str] = None
        self._device_fingerprint: Optional[str] = None
        self._heartbeat_thread: Optional[threading.Thread] = None
        self._heartbeat_running = False
        self._heartbeat_interval = 30  # segundos

    def _generate_device_fingerprint(self) -> str:
        """
        Gera um fingerprint único do dispositivo.

        Combina informações do sistema para criar um identificador único
        que permite detectar uso compartilhado da API Key.
        """
        components = [
            platform.node(),  # hostname
            platform.system(),  # OS
            platform.machine(),  # arquitetura
            platform.processor(),  # processador
            str(uuid.getnode()),  # MAC address
        ]

        fingerprint_string = "|".join(components)
        return hashlib.sha256(fingerprint_string.encode()).hexdigest()[:32]

    def _get_local_ip(self) -> str:
        """Obtém o IP local do dispositivo."""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "unknown"

    def start_session(self) -> Dict[str, Any]:
        """
        Inicia uma nova sessão com a API.

        Returns:
            Dict com informações da sessão criada

        Raises:
            SessionConflictError: Se outro dispositivo já está usando a API Key
            AuthenticationError: Se a API Key é inválida
        """
        self._device_fingerprint = self._generate_device_fingerprint()

        response = self._client._request(
            "POST",
            "/session/start",
            json={
                "device_fingerprint": self._device_fingerprint,
                "device_info": {
                    "hostname": platform.node(),
                    "os": platform.system(),
                    "os_version": platform.version(),
                    "python_version": platform.python_version(),
                    "sdk_version": self._client._sdk_version,
                    "local_ip": self._get_local_ip()
                }
            }
        )

        self._session_id = response.get("session_id")
        self._start_heartbeat()

        return response

    def validate_session(self) -> bool:
        """
        Valida se a sessão atual ainda é válida.

        Returns:
            True se a sessão é válida

        Raises:
            SessionConflictError: Se a sessão foi invalidada por outro dispositivo
        """
        if not self._session_id:
            return False

        response = self._client._request(
            "POST",
            "/session/validate",
            json={
                "session_id": self._session_id,
                "device_fingerprint": self._device_fingerprint
            }
        )

        return response.get("valid", False)

    def end_session(self) -> None:
        """Encerra a sessão atual."""
        self._stop_heartbeat()

        if self._session_id:
            try:
                self._client._request(
                    "POST",
                    "/session/end",
                    json={"session_id": self._session_id}
                )
            except Exception:
                pass  # Ignora erros ao encerrar sessão

            self._session_id = None

    def _start_heartbeat(self) -> None:
        """Inicia o thread de heartbeat."""
        if self._heartbeat_running:
            return

        self._heartbeat_running = True
        self._heartbeat_thread = threading.Thread(
            target=self._heartbeat_loop,
            daemon=True
        )
        self._heartbeat_thread.start()

    def _stop_heartbeat(self) -> None:
        """Para o thread de heartbeat."""
        self._heartbeat_running = False
        if self._heartbeat_thread:
            self._heartbeat_thread.join(timeout=2)
            self._heartbeat_thread = None

    def _heartbeat_loop(self) -> None:
        """Loop de heartbeat para manter a sessão ativa."""
        while self._heartbeat_running:
            time.sleep(self._heartbeat_interval)

            if not self._heartbeat_running:
                break

            try:
                self._client._request(
                    "POST",
                    "/session/heartbeat",
                    json={
                        "session_id": self._session_id,
                        "device_fingerprint": self._device_fingerprint
                    }
                )
            except Exception:
                # Se falhar o heartbeat, tenta reconectar na próxima requisição
                pass

    @property
    def session_id(self) -> Optional[str]:
        """Retorna o ID da sessão atual."""
        return self._session_id

    @property
    def is_active(self) -> bool:
        """Verifica se há uma sessão ativa."""
        return self._session_id is not None
