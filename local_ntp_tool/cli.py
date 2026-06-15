from __future__ import annotations

import argparse
import datetime as dt
from pathlib import Path
import sys
import time

from .client import NtpClient
from .config import load_state, save_state
from .constants import APP_NAME
from .logging_store import LogStore
from .models import BaseTimeMode, ProgressMode, TimeProfile, TimezoneDisplay
from .server import NtpServer
from .time_engine import TimeEngine


def parse_datetime_utc(value: str) -> dt.datetime:
    parsed = dt.datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone.utc)
    return parsed.astimezone(dt.timezone.utc)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=APP_NAME)
    parser.add_argument("--cli", action="store_true", help="Run in CLI mode without GUI")
    parser.add_argument("--config", type=Path, help="Path to the JSON config file")
    parser.add_argument("--host", help="Server bind host")
    parser.add_argument("--port", type=int, help="Server bind port")
    parser.add_argument("--mode", choices=[mode.value for mode in BaseTimeMode], help="Base time mode")
    parser.add_argument(
        "--progress-mode",
        choices=[mode.value for mode in ProgressMode],
        help="Time progress mode",
    )
    parser.add_argument("--target-datetime", help="Fixed datetime in ISO format")
    parser.add_argument("--offset-seconds", type=float, help="Offset seconds")
    parser.add_argument("--rate", type=float, help="Rate multiplier")
    parser.add_argument("--query", help="Query remote host[:port] and exit")
    return parser


def run_cli(args: argparse.Namespace) -> int:
    state = load_state(args.config)
    if args.query:
        logs = LogStore()
        client = NtpClient(logs)
        host, port = split_host_port(args.query, state.client.port)
        result = client.query(host, port, state.client.timeout_seconds)
        print(
            "success={success} target={target} server_time_utc={server_time_utc} "
            "delta_seconds={delta_seconds:.6f} rtt_ms={rtt_ms:.3f}".format(**result)
        )
        return 0

    if args.host:
        state.server.host = args.host
        state.server.allow_all_interfaces = args.host == "0.0.0.0"
    if args.port:
        state.server.port = args.port
    if args.mode:
        state.time_profile.base_mode = BaseTimeMode(args.mode)
    if args.progress_mode:
        state.time_profile.progress_mode = ProgressMode(args.progress_mode)
    if args.target_datetime:
        state.time_profile.target_time_utc = parse_datetime_utc(args.target_datetime)
    if args.offset_seconds is not None:
        state.time_profile.offset_seconds = args.offset_seconds
    if args.rate is not None:
        state.time_profile.rate_multiplier = args.rate
    state.time_profile.timezone_display = TimezoneDisplay.UTC

    logs = LogStore()
    engine = TimeEngine(state.time_profile)
    server = NtpServer(engine, logs, status_callback=print)
    server.start(state.server.host, state.server.port)
    save_state(state)
    print("Press Ctrl+C to stop.")
    try:
        while True:
            time.sleep(1.0)
    except KeyboardInterrupt:
        server.stop()
        return 0


def split_host_port(value: str, default_port: int) -> tuple[str, int]:
    if ":" not in value:
        return value, default_port
    host, raw_port = value.rsplit(":", 1)
    return host, int(raw_port)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.cli:
        return run_cli(args)
    from .gui import launch_gui

    launch_gui(args.config)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
