from __future__ import annotations

import datetime as dt
import socket
import threading
from typing import Callable

from .logging_store import LogStore
from .ntp_protocol import build_response, parse_request
from .time_engine import TimeEngine


StatusCallback = Callable[[str], None]


class NtpServer:
    def __init__(
        self,
        time_engine: TimeEngine,
        logs: LogStore,
        status_callback: StatusCallback | None = None,
    ) -> None:
        self._time_engine = time_engine
        self._logs = logs
        self._status_callback = status_callback
        self._socket: socket.socket | None = None
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._lock = threading.RLock()
        self._host = ""
        self._port = 0

    @property
    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    @property
    def endpoint(self) -> tuple[str, int]:
        return self._host, self._port

    def start(self, host: str, port: int) -> None:
        with self._lock:
            if self.is_running:
                raise RuntimeError("Server is already running")
            self._stop_event.clear()
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.bind((host, port))
            sock.settimeout(0.5)
            self._socket = sock
            self._host, self._port = sock.getsockname()
            self._thread = threading.Thread(target=self._serve_forever, daemon=True)
            self._thread.start()
            self._emit_status(f"服务已启动: {self._host}:{self._port}")
            self._logs.add("server", "server_started", host=self._host, port=self._port)

    def stop(self) -> None:
        with self._lock:
            self._stop_event.set()
            if self._socket:
                self._socket.close()
                self._socket = None
            thread = self._thread
            self._thread = None
        if thread:
            thread.join(timeout=1.0)
            self._emit_status("服务已停止")
            self._logs.add("server", "server_stopped")

    def _serve_forever(self) -> None:
        while not self._stop_event.is_set():
            sock = self._socket
            if sock is None:
                return
            try:
                packet, address = sock.recvfrom(1024)
            except socket.timeout:
                continue
            except OSError:
                return

            client_ip, client_port = address[0], address[1]
            try:
                request = parse_request(packet)
                receive_time = self._time_engine.now_utc()
                transmit_time = self._time_engine.now_utc()
                response = build_response(
                    request=request,
                    reference_time_utc=receive_time,
                    receive_time_utc=receive_time,
                    transmit_time_utc=transmit_time,
                )
                sock.sendto(response, address)
                self._logs.add(
                    "service_request",
                    "request_served",
                    client_ip=client_ip,
                    client_port=client_port,
                    returned_time=transmit_time.isoformat(),
                    time_mode=self._time_engine.describe(),
                    success=True,
                )
            except Exception as exc:  # noqa: BLE001
                self._logs.add(
                    "service_request",
                    "request_failed",
                    client_ip=client_ip,
                    client_port=client_port,
                    success=False,
                    error=str(exc),
                )

    def _emit_status(self, message: str) -> None:
        if self._status_callback is not None:
            self._status_callback(message)
