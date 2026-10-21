import os
import sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))

from tyre_deg import add_fuel_correction

def make_stint(stint, first_lap, n, base, per_lap_change):
    return pd.DataFrame({
        "Stint": [stint] * n,
        "LapNumber": list(range(first_lap, first_lap + n)),
        "TyreLife": list(range(1, n + 1)),
        "LapTimeSec": [base + per_lap_change * i for i in range(n)],
    })

def slope(df, column):
    return np.polyfit(df["LapNumber"], df[column], 1)[0]

def test_pure_fuel_burn_gives_zero_corrected_slope():
    laps = make_stint(1, 1, 10, base=95.0, per_lap_change=-0.05)
    out = add_fuel_correction(laps, effect=0.05)
    assert abs(slope(out, "LapTimeSec") - (-0.05)) < 1e-9
    assert abs(slope(out, "LapTimeCorr")) < 1e-9

def test_wear_is_recovered_after_correction():
    laps = make_stint(1, 1, 10, base=95.0, per_lap_change=-0.05)
    out = add_fuel_correction(laps, effect=0.05)
    assert abs(slope(out, "LapTimeSec") - (-0.05)) < 1e-9
    assert abs(slope(out, "LapTimeCorr")) < 1e-9

def test_first_lap_of_each_stint_is_unchanged():
    laps = pd.concat([make_stint(1, 5, 6, 95.0, 0.0), make_stint(2, 30, 6, 96.0, 0.0)],
                     ignore_index=True)
    out = add_fuel_correction(laps, effect=0.05)
    for _, stint in out.groupby("Stint"):
        first = stint.iloc[0]
        assert first["StintLap"] == 0
        assert first["LapTimeCorr"] == first["LapTimeSec"]
 
 
def test_stints_are_corrected_independently():
    # Stint 2 starts much later in the session; only laps since ITS start should matter
    laps = pd.concat([make_stint(1, 5, 6, 95.0, 0.0), make_stint(2, 40, 6, 95.0, 0.0)],
                     ignore_index=True)
    out = add_fuel_correction(laps, effect=0.05)
    s2 = out[out["Stint"] == 2]
    assert list(s2["StintLap"]) == [0, 1, 2, 3, 4, 5]
 
 
def test_removed_laps_still_count_as_burned_fuel():
    # Laps 12 and 13 were filtered out (e.g. slow laps). Fuel was still burned during them.
    laps = make_stint(1, 10, 6, 95.0, 0.0)
    laps = laps[~laps["LapNumber"].isin([12, 13])]
    out = add_fuel_correction(laps, effect=0.05)
    assert list(out["StintLap"]) == [0, 1, 4, 5]
 
 
def test_input_is_not_modified():
    laps = make_stint(1, 10, 5, 95.0, 0.0)
    add_fuel_correction(laps, effect=0.05)
    assert "LapTimeCorr" not in laps.columns
 

