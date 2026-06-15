from __future__ import annotations

import datetime as dt

NTP_EPOCH = dt.datetime(1900, 1, 1, tzinfo=dt.timezone.utc)
DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 123
DEFAULT_TIMEOUT_SECONDS = 3.0
DEFAULT_POLL_INTERVAL_MS = 1000
DEFAULT_LOG_EXPORT_PREFIX = "ntp_tool_log"
CONFIG_FILE_NAME = "ntp_tool_config.json"
SERVER_LOG_FILE_NAME = "service_requests.csv"
CLIENT_LOG_FILE_NAME = "client_tests.csv"
APP_NAME = "Local NTP Test Tool"
REFERENCE_ID = b"LOCL"
