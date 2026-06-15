from __future__ import annotations

import datetime as dt
import socket
import time

from .constants import DEFAULT_TIMEOUT_SECONDS
from .logging_store import LogStore
from .ntp_protocol import build_client_request, parse_server_response


class NtpClient:
    def __init__(self, logs: LogStore) -> None:
        self._logs = logs

    def query(self, host: str, port: int, timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS) -> dict[str, object]:
        request = build_client_request()
        started = time.perf_counter()
        request_started_utc = dt.datetime.now(dt.timezone.utc)
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.settimeout(timeout_seconds)
            sock.sendto(request, (host, port))
            packet, _ = sock.recvfrom(1024)
        ended = time.perf_counter()
        local_receive_time_utc = dt.datetime.now(dt.timezone.utc)
        response = parse_server_response(packet)
        rtt_ms = (ended - started) * 1000.0
        offset_seconds = (response.transmit_time_utc - local_receive_time_utc).total_seconds()
        result = {
            "target": f"{host}:{port}",
            "success": True,
            "server_time_utc": response.transmit_time_utc,
            "local_request_time_utc": request_started_utc,
            "local_receive_time_utc": local_receive_time_utc,
            "delta_seconds": offset_seconds,
            "rtt_ms": rtt_ms,
            "reference_time_utc": response.reference_time_utc,
            "receive_time_utc": response.receive_time_utc,
        }
        self._logs.add(
            "client_test",
            "client_query_succeeded",
            target=result["target"],
            server_time=response.transmit_time_utc.isoformat(),
            delta_seconds=f"{offset_seconds:.6f}",
            rtt_ms=f"{rtt_ms:.3f}",
            success=True,
        )
        return result
