"""Tests for the lap-by-lap StintMonitor in live_monitor.py.

Run from the project root:  pytest
"""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from live_monitor import StintMonitor  # noqa: E402

FUEL = 0.05


def lap(i, seconds, stint=1, **extra):
    """One synthetic completed lap; i is the lap index within the stint."""
    row = dict(Stint=stint, LapNumber=10 + i, TyreLife=i + 1, Compound="MEDIUM",
               LapTimeSec=seconds, PitInTime=pd.NaT, PitOutTime=pd.NaT, TrackStatus="1")
    row.update(extra)
    return row


def wear_time(i, wear=0.10):
    # raw lap time = real wear minus fuel gain; the monitor should recover `wear`
    return 95.0 + (wear - FUEL) * i


def test_recovers_known_wear_rate():
    m = StintMonitor(FUEL)
    for i in range(10):
        m.update(lap(i, wear_time(i)))
    st = m.stints[1]
    fitted = np.polyfit(st["life"], st["corr"], 1)[0]
    assert abs(fitted - 0.10) < 1e-9


def test_pit_laps_are_ignored():
    m = StintMonitor(FUEL)
    assert m.update(lap(0, 95.0, PitOutTime=pd.Timedelta(seconds=1))) is None
    assert m.update(lap(1, 95.0, PitInTime=pd.Timedelta(seconds=1))) is None
    assert 1 not in m.stints


def test_safety_car_laps_are_ignored():
    m = StintMonitor(FUEL)
    assert m.update(lap(0, 95.0)) is not None
    assert m.update(lap(1, 96.0, TrackStatus="14")) is None
    assert len(m.stints[1]["life"]) == 1


def test_very_slow_laps_are_ignored():
    m = StintMonitor(FUEL)
    m.update(lap(0, 95.0))
    assert m.update(lap(1, 110.0)) is None   # > 107% of the best lap seen so far


def test_missing_data_is_ignored():
    m = StintMonitor(FUEL)
    assert m.update(lap(0, float("nan"))) is None
    assert m.update(lap(0, 95.0, TyreLife=float("nan"))) is None


def test_single_slow_lap_does_not_raise_cliff_alert():
    m = StintMonitor(FUEL)
    for i in range(12):
        m.update(lap(i, wear_time(i)))
    msg = m.update(lap(12, wear_time(12) + 1.2))   # one bad lap, e.g. traffic
    assert "ALERT" not in msg


def test_two_consecutive_slow_laps_raise_cliff_alert():
    m = StintMonitor(FUEL)
    for i in range(12):
        m.update(lap(i, wear_time(i)))
    first = m.update(lap(12, wear_time(12) + 1.2))
    second = m.update(lap(13, wear_time(13) + 1.2))
    assert "ALERT" not in first
    assert "ALERT" in second


def test_no_alert_on_steady_degradation():
    m = StintMonitor(FUEL)
    for i in range(15):
        msg = m.update(lap(i, wear_time(i)))
        assert "ALERT" not in msg