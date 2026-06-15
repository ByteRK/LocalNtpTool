from __future__ import annotations

import socket


def list_ipv4_addresses() -> list[str]:
    host_name = socket.gethostname()
    discovered = {"127.0.0.1"}
    try:
        for result in socket.getaddrinfo(host_name, None, socket.AF_INET, socket.SOCK_DGRAM):
            address = result[4][0]
            discovered.add(address)
    except OSError:
        pass
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as probe:
            probe.connect(("8.8.8.8", 80))
            discovered.add(probe.getsockname()[0])
    except OSError:
        pass
    return sorted(discovered)
