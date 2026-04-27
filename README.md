# F1 Analytics Dashboard - [Link](https://f1fastestlap.streamlit.app/)

A full-stack Formula 1 data analysis dashboard built using Python, Streamlit, and FastF1.
This application provides insights into race performance, tire degradation, driver comparison, telemetry, and championship standings.

---

## Features

### Tire Degradation Analysis

* Visualize lap times across different tire compounds
* Identify performance trends over laps

### Driver Comparison

* Compare lap times between two drivers
* View average lap performance metrics

### Championship Standings

* Driver standings
* Constructor standings
* Podium highlighting
* API fallback system for improved reliability

### Interactive Telemetry

* Speed vs distance comparison
* Zoom and hover for detailed analysis
* Compare fastest laps between drivers
* Built using Plotly for interactivity

### Year vs Year
* Compare single driver with different year, same track
* Compound of tires used
* Summary of two years
* Interactive Graph
---

## Tech Stack

* Frontend: Streamlit
* Data Source: FastF1
* Visualization: Matplotlib, Plotly
* API: Jolpica (Ergast-compatible)
* Language: Python

---

## Project Structure

```
Streamlit/
│
├── app.py              # Main Streamlit application
├── standings.py        # Standings module (API handling)
├── api.py              # Optional FastAPI backend
├── requirements.txt
└── README.md
```

---

## Installation

### Clone the repository

```
git clone https://github.com/your-username/f1-analytics-dashboard.git
cd f1-analytics-dashboard
```

### Install dependencies

```
pip install -r requirements.txt
```

### Run the application

```
streamlit run app.py
```

---

## Usage

1. Select a year
2. Choose a Grand Prix
3. Select a session
4. Choose a mode:

   * Single Driver
   * Comparison
   * Standings
   * Telemetry

---

## Notes

* Some sessions may not contain complete data
* Older seasons may have limited availability
* Telemetry requires valid lap data
---

## License

This project is intended for educational and portfolio purposes.

---

## Author

Samartha Bhat
https://github.com/Samarthasbhat
