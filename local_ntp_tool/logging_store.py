from __future__ import annotations

import csv
import datetime as dt
from pathlib import Path
import threading
from typing import Iterable

from .models import LogEntry


class LogStore:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._entries: list[LogEntry] = []

    def add(self, category: str, message: str, **details: object) -> LogEntry:
        entry = LogEntry(
            category=category,
            timestamp=dt.datetime.now(dt.timezone.utc),
            message=message,
            details={key: value for key, value in details.items()},
        )
        with self._lock:
            self._entries.append(entry)
        return entry

    def list_entries(self, category: str | None = None) -> list[LogEntry]:
        with self._lock:
            if category is None:
                return list(self._entries)
            return [entry for entry in self._entries if entry.category == category]

    def export_csv(self, path: Path, entries: Iterable[LogEntry]) -> None:
        rows = [entry.to_row() for entry in entries]
        path.parent.mkdir(parents=True, exist_ok=True)
        if not rows:
            path.write_text("", encoding="utf-8")
            return
        fieldnames: list[str] = []
        for row in rows:
            for key in row:
                if key not in fieldnames:
                    fieldnames.append(key)
        with path.open("w", newline="", encoding="utf-8-sig") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
