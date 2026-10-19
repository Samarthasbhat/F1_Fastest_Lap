# 🏎️ F1 Analytics Dashboard

An interactive Formula 1 data dashboard built with Python, Streamlit, and FastF1. It covers tyre degradation, driver comparison, telemetry, championship standings, and year-over-year performance.

🔗 **[Live demo](https://f1analyseboard.streamlit.app/)**

<!-- Add 2-3 screenshots or a short GIF here, for example: -->
![Tire Performance](Streamlit/image.png)

---

## Features

### 🛞 Tyre Degradation Analysis
- Lap times coloured by tyre compound
- Performance trends over a stint

### 🧑‍✈️ Driver Comparison
- Compare lap times between two drivers
- Average lap metrics side by side

### 🏆 Championship Standings
- Driver and constructor standings
- Podium highlighting
- API fallback for improved reliability

### 📈 Interactive Telemetry
- Speed vs distance for the fastest laps of two drivers
- Zoom and hover, built with Plotly

### 📅 Year vs Year
- Same driver, same track, two different seasons
- Tyre compounds used in each year
- Summary metrics and an interactive chart

---

## Tech Stack

- **App framework:** Streamlit
- **Data:** FastF1, Jolpica (Ergast-compatible API)
- **Visualization:** Matplotlib, Plotly
- **Language:** Python 3.12

---

## Project Structure

```
Streamlit/
├── app.py            # Main Streamlit application
├── standings.py      # Standings module (API handling)
├── requirements.txt
└── README.md
```

---

## Run Locally

```bash
git clone https://github.com/Samarthasbhat/F1_Fastest_Lap.git
cd F1_Fastest_Lap/Streamlit

python3.12 -m venv venv
source venv/bin/activate

python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Python 3.12 is recommended. Some dependencies may not support the newest Python releases yet.

---

## Usage

1. Choose a mode: Tire Performance, Comparison, Standings, Telemetry, or Year vs Year
2. Select a year, Grand Prix, and session
3. Pick a driver (or two) and explore the charts

---

## Data Availability

- Lap-based modes use FastF1 timing data. Timing data for some recent seasons may be unavailable, so those modes currently offer seasons **<!-- EDIT: e.g. 2021-2022 -->**.
- Standings use the Jolpica API and cover more seasons.
- Some sessions may be incomplete, and telemetry needs valid lap data.

---

## Author

**Samartha Bhat**
[GitHub](https://github.com/Samarthasbhat) · [LinkedIn](https://www.linkedin.com/in/samarthabhat)
