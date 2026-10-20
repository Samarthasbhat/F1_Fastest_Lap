# F1 Tyre Degradation Analyzer

A Python tool that loads Formula 1 timing data, cleans and fuel-corrects lap times, estimates tyre degradation for each stint, and flags possible tyre "cliffs". Results can be viewed as a static chart or as a lap-by-lap replay dashboard.

Built with [FastF1](https://github.com/theOehrly/Fast-F1). **The analysis uses data from the 2021 and 2022 seasons only.**

![Dashboard](Streamlit/image.png)


## Problem statement

Raw F1 lap times mix tyre wear with fuel burn, traffic, safety cars and pit laps, so it is hard to tell how quickly a tyre is actually degrading during a run.

## Data scope

- **Seasons:** 2021 and 2022 only, loaded through FastF1.
- **Sessions:** races are the main use case (`SESSION_MODE = "race"`). Testing sessions can be loaded with `SESSION_MODE = "testing"` for years where FastF1 provides them.
- **Do not pool the two seasons.** 2022 brought a major regulation change (new cars and 18-inch tyres), so tyre behaviour in 2021 and 2022 is not directly comparable. Analyse each season on its own.

## What it does

- **Cleans the data:** removes in-laps, out-laps, unusually slow laps and (in race mode) safety car, virtual safety car and yellow-flag laps.
- **Corrects for fuel burn:** adds back the time a car gains as it gets lighter, so tyre wear is not hidden.
- **Estimates degradation:** fits a straight line per stint and reports the slope in seconds lost per lap.
- **Shows sensitivity:** prints corrected slopes for three assumed fuel effects (0.03, 0.05 and 0.07 s/lap) so you see a range instead of one falsely precise number.
- **Flags possible tyre cliffs:** raises an alert when two laps in a row are well off the stint's trend.
- **Replays a session lap by lap** in a dashboard window, where the monitor only uses laps that have already happened.

## Project structure

| File | Purpose |
|---|---|
| `tyre_deg.py` | Settings, data loading, fuel correction, stint slopes and the static chart |
| `live_monitor.py` | `StintMonitor` class: lap-by-lap filtering, slope updates and cliff alerts (terminal replay) |
| `live_window.py` | Replay dashboard: live chart on the left, status log on the right |
| `tests/` | Unit tests for the fuel correction and the stint monitor |

Keep the three scripts in the same folder. `live_monitor.py` and `live_window.py` import their settings from `tyre_deg.py`.

## Installation

```bash
git clone <your-repo-url>
cd <your-repo-folder>

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

`requirements.txt`:

```
fastf1>=3.8.3
matplotlib
numpy
```

## Usage

Edit the settings at the top of `tyre_deg.py`. Use a 2021 or 2022 season:

```python
YEAR = 2022                # 2021 or 2022
SESSION_MODE = "race"      # "race" or "testing"
EVENT = "Azerbaijan"       # race mode: event name or round number
TEST_NUMBER = 2            # testing mode only
DAY = 1                    # testing mode only
DRIVER = "LEC"             # three-letter driver code
```

Then run one of:

```bash
python tyre_deg.py       # static chart + slope table
python live_window.py    # replay dashboard (adjust REPLAY_DELAY_S to change speed)
python live_monitor.py   # replay printed in the terminal
```

The first run downloads data and can take a few minutes. Later runs use the local `cache` folder.

To run the tests:

```bash
pip install pytest
pytest
```

## How it works

1. **Load:** FastF1 loads the session. Telemetry, weather and messages are skipped because only lap data is needed.
2. **Filter:** quick laps only, no in/out laps, and (race mode) green-flag laps only.
3. **Fuel-correct:** for each stint, `corrected time = lap time + fuel effect × laps since the stint's first lap`. Only the burn rate matters, because each stint is compared with its own first lap.
4. **Fit:** a straight line of corrected lap time against tyre life gives the slope in seconds per lap. Stints with fewer than 5 laps are skipped.
5. **Alert:** in the replay, a lap far above the trend predicted from the stint's earlier laps counts as a cliff candidate, and two in a row raise an alert.

## Assumptions and limitations

Please read these before drawing conclusions from the output.

- **The fuel effect (0.05 s/lap) is an assumption,** not measured data. The true value depends on the car and the season. Treat results as a range.
- **The 22 s pit loss** used for the "indicative stint length" is a placeholder and varies by circuit.
- **Absolute lap times between stints are not comparable,** because starting fuel loads differ. Only the slope within each stint is meaningful.
- **Short stints give unreliable slopes.** Engine modes, traffic and driver push level also change lap times within a run.
- **2021 and 2022 should not be compared directly,** because of the 2022 regulation change.
- **The replay is not live.** FastF1 can only record a live feed for processing afterwards, so the "live" monitor replays a finished session.
- **Validation is limited.** The correction and filtering logic is covered by unit tests on synthetic data, but the outputs have not been compared with team-grade analysis.


## Tech stack

Python, FastF1, pandas, NumPy, Matplotlib, pytest.

## Data and disclaimer

Timing data comes from the Formula 1 live timing service through FastF1. This project is unofficial and is not associated with Formula 1, the FIA or any team. Formula 1, F1 and related marks are trademarks of their respective owners.

## License

Add a license of your choice (for example MIT) before publishing.
