from __future__ import annotations

import json
import os
from pathlib import Path
import sys

from .constants import CONFIG_FILE_NAME
from .models import AppPaths, PersistedState


def default_user_storage_dir() -> Path:
    app_data = os.getenv("APPDATA")
    if app_data:
        return Path(app_data) / "local_ntp_tool"
    return Path.home() / ".local_ntp_tool"


def default_program_storage_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def build_default_state() -> PersistedState:
    storage_dir = default_program_storage_dir()
    return PersistedState(
        paths=AppPaths(storage_dir=storage_dir, config_path=storage_dir / CONFIG_FILE_NAME)
    )


def load_state(config_path: Path | None = None) -> PersistedState:
    default_state = build_default_state()
    target_path = config_path or default_state.paths.config_path
    if not target_path.exists():
        default_state.paths = AppPaths(storage_dir=target_path.parent, config_path=target_path)
        return default_state
    data = json.loads(target_path.read_text(encoding="utf-8"))
    state = PersistedState.from_dict(data, fallback_storage_dir=target_path.parent)
    state.paths = AppPaths(storage_dir=state.paths.storage_dir, config_path=target_path)
    return state


def save_state(state: PersistedState) -> None:
    if state.paths is None:
        raise ValueError("State paths are required for saving")
    state.paths.storage_dir.mkdir(parents=True, exist_ok=True)
    state.paths.config_path.parent.mkdir(parents=True, exist_ok=True)
    payload = state.to_dict()
    state.paths.config_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
