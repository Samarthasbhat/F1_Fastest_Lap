import os 

import fastf1
import fastf1.plotting
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D

YEAR = 2022
SESSION_MODE = "race"
EVENT="Azerbaijan"
TEST_NUMBER = 2
DAY = 1
DRIVER = "LEC"

CACHA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                         "cache" )

FUEL_EFFECT_S_PER_LAP = 0.05
FUEL_SENSITIVITY = (0.03, 0.05, 0.07)
USE_FUEL_CORRECTION = True

FALLBACK_COLORS = {"SOFT": "red", "MEDIUM": "yellow", "HARD": "white", 
                   "INTERMEDIATE": "green", "WET": "blue"}

def setup_cache():
    os.makedirs(CACHA_DIR, exist_ok=True)
    fastf1.Cache.enable_cache(CACHA_DIR)

setup_cache()

def list_testing_events():
    schedule = fastf1.get_event_schedule(YEAR, include_testing=True)
    print(schedule[schedule["EventFormat"]== "testing"][["RoundNumber", 
                                                         "EventName", "EventDate"]])

def load_session():
    if SESSION_MODE == "race":
        session = fastf1.get_session(YEAR, EVENT, "R")
    else:
        session = fastf1.get_session(YEAR, TEST_NUMBER, DAY)
    session.load(telemetry=False, weather=False, messages=False)
    return session

def session_label():
    if SESSION_MODE == "race":
        return f"{YEAR} {EVENT} GP Race"
    return f"{YEAR} Testing Day {DAY} - Test {TEST_NUMBER}"

def add_fuel_correction(laps, effect=FUEL_EFFECT_S_PER_LAP):
    laps=laps.copy()

    laps["StintLap"] = laps["LapNumber"] - laps.groupby("Stint")["LapNumber"].transform("min")
    laps["LapTimeCorr"] =laps["LapTimeSec"] + effect * laps["StintLap"]
    return laps

def load_laps():
    session = load_session()
    laps = session.laps.pick_drivers(DRIVER).pick_quicklaps().pick_wo_box()
    if SESSION_MODE == "race" and "TrackStatus" in laps.columns:
        laps = laps.pick_track_status("1", how="equals")

    before = len(laps)
    laps = laps.dropna(subset=["TyreLife", "LapTime"])
    if len(laps) < before:
        print(f"Dropped {before-len(laps)} laps due to missing TyreLife or LapTime")
    if laps.empty:
        raise SystemExit("No valid laps found for the specified driver and session.")

    laps=laps.copy()
    laps["LapTimeSec"] = laps["LapTime"].dt.total_seconds()
    laps = add_fuel_correction(laps)
    return session, laps

def compound_color(compound, session):
    try:
        return fastf1.plotting.get_compound_color(compound, session=session)
    except (KeyError, ValueError, TypeError):
        return FALLBACK_COLORS.get(compound, "gray")

def print_slopes(laps, min_laps=5):
    header = "  ".join(f"@{e:.2f}" for e in FUEL_SENSITIVITY)
    print(f"Slopes in s/lap. Raw first, then fuel-corrected at assumed effect: {header}")
    for stint_no, stint in laps.groupby("Stint"):
        if len(stint) < min_laps:
            continue
        raw = np.polyfit(stint["TyreLife"], stint["LapTimeSec"], 1)[0]
        corrected = []
        for effect in FUEL_SENSITIVITY:
            stint_corr = add_fuel_correction(stint, effect=effect)
            corrected.append(np.polyfit(stint_corr["TyreLife"], stint_corr["LapTimeSec"], 1)[0])
        lap_range = f"laps {int(stint['LapNumber'].min())}-{int(stint['LapNumber'].max())}"
        corr_text = "  ".join(f"{c:.3f}" for c in corrected)
        print(f"S{int(stint_no)} ({stint['Compound'].iloc[0]}, {lap_range}, {len(stint)} laps): "
              f"raw {raw:+.3f} | corrected {corr_text}")

def plot_stints(session, laps):
    y_col = "LapTimeCorr" if USE_FUEL_CORRECTION else "LapTimeSec"
    fig, ax = plt.subplots(figsize=(12, 6))
    seen = {}

    for stint_no, stint in laps.groupby("Stint"):
        compound = stint["Compound"].iloc[0]
        color = compound_color(compound, session)
        seen[compound] = color

        ax.plot(stint["TyreLife"], stint[y_col], color = "lightgray", zorder=1)
        ax.scatter(stint["TyreLife"], stint[y_col], color=color, edgecolors='black',s=45, zorder=2)

        first = stint.iloc[0]
        offset = (-10,8) if int(stint_no) % 2 else (8,-14)
        ax.annotate(f"S{int(stint_no)}", 
                    xy = (first["TyreLife"], first[y_col]),
                    xytext = offset, textcoords="offset points",
                    fontsize=9, fontweight="bold",
                    arrowprops=dict(arrowstyle="-", color="gray", lw=0.8))

        handles = [Line2D([0], [0], marker="o", linestyle="", markerfacecolor=c,
                      markeredgecolor="black", label=str(k).replace("_", " ").title())
               for k, c in seen.items()]
    ax.legend(handles=handles, title="Tyre compound", loc="best", framealpha=0.5)
 
    if USE_FUEL_CORRECTION:
        subtitle = f"Fuel-corrected, assumed {FUEL_EFFECT_S_PER_LAP:.2f} s/lap (estimate)"
    else:
        subtitle = "Uncorrected for fuel load"
    ax.set_title(f"{DRIVER}: lap time vs tyre life ({session_label()})\n{subtitle}")
    ax.set_xlabel("Tyre life (laps)")
    ax.set_ylabel("Lap time (s)")
    ax.grid(alpha=0.3)
    plt.show()
 
 
if __name__ == "__main__":
    # list_testing_events()   # run once to find TEST_NUMBER, then leave commented
    session, laps = load_laps()
    print_slopes(laps)
    plot_stints(session, laps)
 
        