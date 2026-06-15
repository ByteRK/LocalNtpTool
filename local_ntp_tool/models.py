from __future__ import annotations

from dataclasses import asdict, dataclass, field
import datetime as dt
from enum import Enum
from pathlib import Path
from typing import Any

from .constants import CONFIG_FILE_NAME, DEFAULT_HOST, DEFAULT_PORT


class BaseTimeMode(str, Enum):
    SYSTEM = "system"
    FIXED = "fixed"


class ProgressMode(str, Enum):
    RUNNING = "running"
    FROZEN = "frozen"


class TimezoneDisplay(str, Enum):
    LOCAL = "local"
    UTC = "utc"


@dataclass(slots=True)
class TimeProfile:
    base_mode: BaseTimeMode = BaseTimeMode.SYSTEM
    progress_mode: ProgressMode = ProgressMode.RUNNING
    timezone_display: TimezoneDisplay = TimezoneDisplay.LOCAL
    target_time_utc: dt.datetime | None = None
    offset_seconds: float = 0.0
    rate_multiplier: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        if self.target_time_utc is not None:
            data["target_time_utc"] = self.target_time_utc.astimezone(dt.timezone.utc).isoformat()
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TimeProfile":
        target_raw = data.get("target_time_utc")
        target_time = None
        if target_raw:
            target_time = dt.datetime.fromisoformat(target_raw).astimezone(dt.timezone.utc)
        return cls(
            base_mode=BaseTimeMode(data.get("base_mode", BaseTimeMode.SYSTEM.value)),
            progress_mode=ProgressMode(data.get("progress_mode", ProgressMode.RUNNING.value)),
            timezone_display=TimezoneDisplay(data.get("timezone_display", TimezoneDisplay.LOCAL.value)),
            target_time_utc=target_time,
            offset_seconds=float(data.get("offset_seconds", 0.0)),
            rate_multiplier=float(data.get("rate_multiplier", 1.0)),
        )


@dataclass(slots=True)
class AppPaths:
    storage_dir: Path
    config_path: Path

    def to_dict(self) -> dict[str, str]:
        return {
            "storage_dir": str(self.storage_dir),
            "config_path": str(self.config_path),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any], fallback_storage_dir: Path) -> "AppPaths":
        storage_dir = Path(data.get("storage_dir", fallback_storage_dir))
        config_path = Path(data.get("config_path", storage_dir / CONFIG_FILE_NAME))
        return cls(storage_dir=storage_dir, config_path=config_path)


@dataclass(slots=True)
class ServerSettings:
    host: str = DEFAULT_HOST
    port: int = DEFAULT_PORT
    auto_start: bool = False
    allow_all_interfaces: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ServerSettings":
        return cls(
            host=data.get("host", DEFAULT_HOST),
            port=int(data.get("port", DEFAULT_PORT)),
            auto_start=bool(data.get("auto_start", False)),
            allow_all_interfaces=bool(data.get("allow_all_interfaces", True)),
        )


@dataclass(slots=True)
class ClientSettings:
    host: str = "127.0.0.1"
    port: int = DEFAULT_PORT
    timeout_seconds: float = 3.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ClientSettings":
        return cls(
            host=data.get("host", "127.0.0.1"),
            port=int(data.get("port", DEFAULT_PORT)),
            timeout_seconds=float(data.get("timeout_seconds", 3.0)),
        )


@dataclass(slots=True)
class PersistedState:
    server: ServerSettings = field(default_factory=ServerSettings)
    client: ClientSettings = field(default_factory=ClientSettings)
    time_profile: TimeProfile = field(default_factory=TimeProfile)
    paths: AppPaths | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "server": self.server.to_dict(),
            "client": self.client.to_dict(),
            "time_profile": self.time_profile.to_dict(),
            "paths": self.paths.to_dict() if self.paths else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any], fallback_storage_dir: Path) -> "PersistedState":
        return cls(
            server=ServerSettings.from_dict(data.get("server", {})),
            client=ClientSettings.from_dict(data.get("client", {})),
            time_profile=TimeProfile.from_dict(data.get("time_profile", {})),
            paths=AppPaths.from_dict(data.get("paths") or {}, fallback_storage_dir),
        )


@dataclass(slots=True)
class LogEntry:
    category: str
    timestamp: dt.datetime
    message: str
    details: dict[str, Any] = field(default_factory=dict)

    def to_row(self) -> dict[str, str]:
        row = {
            "category": self.category,
            "timestamp": self.timestamp.astimezone(dt.timezone.utc).isoformat(),
            "message": self.message,
        }
        for key, value in self.details.items():
            row[key] = str(value)
        return row
