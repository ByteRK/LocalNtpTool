from __future__ import annotations

import datetime as dt
import time
import unittest

from local_ntp_tool.models import BaseTimeMode, ProgressMode, TimeProfile
from local_ntp_tool.time_engine import TimeEngine


class TimeEngineTests(unittest.TestCase):
    def test_fixed_frozen_time_is_constant(self) -> None:
        target = dt.datetime(2026, 6, 15, 12, 0, 0, tzinfo=dt.timezone.utc)
        engine = TimeEngine(
            TimeProfile(
                base_mode=BaseTimeMode.FIXED,
                progress_mode=ProgressMode.FROZEN,
                target_time_utc=target,
            )
        )
        first = engine.now_utc()
        time.sleep(0.02)
        second = engine.now_utc()
        self.assertEqual(first, second)

    def test_running_time_advances_with_rate(self) -> None:
        target = dt.datetime(2026, 6, 15, 12, 0, 0, tzinfo=dt.timezone.utc)
        engine = TimeEngine(
            TimeProfile(
                base_mode=BaseTimeMode.FIXED,
                progress_mode=ProgressMode.RUNNING,
                target_time_utc=target,
                rate_multiplier=10.0,
            )
        )
        first = engine.now_utc()
        time.sleep(0.03)
        second = engine.now_utc()
        self.assertGreater((second - first).total_seconds(), 0.2)

    def test_system_time_applies_offset(self) -> None:
        engine = TimeEngine(
            TimeProfile(
                base_mode=BaseTimeMode.SYSTEM,
                progress_mode=ProgressMode.RUNNING,
                offset_seconds=3600,
            )
        )
        delta = engine.now_utc() - dt.datetime.now(dt.timezone.utc)
        self.assertAlmostEqual(delta.total_seconds(), 3600, delta=0.5)


if __name__ == "__main__":
    unittest.main()
