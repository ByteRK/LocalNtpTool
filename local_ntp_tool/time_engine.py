from __future__ import annotations

import datetime as dt
import threading
import time

from .models import BaseTimeMode, ProgressMode, TimeProfile


def _ensure_utc(value: dt.datetime) -> dt.datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=dt.timezone.utc)
    return value.astimezone(dt.timezone.utc)


class TimeEngine:
    def __init__(self, profile: TimeProfile | None = None) -> None:
        self._lock = threading.RLock()
        self._profile = profile or TimeProfile()
        self._anchor_monotonic = time.monotonic()
        self._anchor_time_utc = dt.datetime.now(dt.timezone.utc)
        self.apply_profile(self._profile)

    @property
    def profile(self) -> TimeProfile:
        with self._lock:
            return TimeProfile(
                base_mode=self._profile.base_mode,
                progress_mode=self._profile.progress_mode,
                timezone_display=self._profile.timezone_display,
                target_time_utc=self._profile.target_time_utc,
                offset_seconds=self._profile.offset_seconds,
                rate_multiplier=self._profile.rate_multiplier,
            )

    def apply_profile(self, profile: TimeProfile) -> None:
        with self._lock:
            now_utc = dt.datetime.now(dt.timezone.utc)
            base_time = self._resolve_base_time(profile, now_utc)
            self._profile = profile
            self._anchor_monotonic = time.monotonic()
            self._anchor_time_utc = base_time + dt.timedelta(seconds=profile.offset_seconds)

    def now_utc(self) -> dt.datetime:
        with self._lock:
            if self._profile.progress_mode == ProgressMode.FROZEN:
                return self._anchor_time_utc

            elapsed_seconds = time.monotonic() - self._anchor_monotonic
            advanced = elapsed_seconds * self._profile.rate_multiplier
            return self._anchor_time_utc + dt.timedelta(seconds=advanced)

    def describe(self) -> str:
        profile = self.profile
        base = "本机时间" if profile.base_mode == BaseTimeMode.SYSTEM else "自定义时间"
        flow = "冻结" if profile.progress_mode == ProgressMode.FROZEN else "连续走时"
        return (
            f"{base} / {flow} / 偏移 {profile.offset_seconds:.3f}s / "
            f"倍率 {profile.rate_multiplier:.3f}x"
        )

    @staticmethod
    def _resolve_base_time(profile: TimeProfile, now_utc: dt.datetime) -> dt.datetime:
        if profile.base_mode == BaseTimeMode.SYSTEM:
            return now_utc

        if profile.target_time_utc is None:
            raise ValueError("Fixed time mode requires target_time_utc")
        return _ensure_utc(profile.target_time_utc)
