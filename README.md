# F1 Fastest Lap | F1 Analytics | Python | Data Visualization 

Formula 1 cars operate at the absolute limit of performance, where tire behavior plays a crucial role in lap time, race strategy, and overall competitiveness. Understanding how tires degrade over a stint is essential for predicting performance drop-off and optimizing pit stop decisions.

This project analyzes tire degradation during the 2026 Formula 1 Pre-Season Testing using real telemetry and timing data provided by the FastF1 library. By visualizing lap times as a horizontal bar chart colored by tire compound, the analysis highlights how different tires perform over successive laps and how performance evolves as tires wear.

Such insights are widely used in motorsport engineering and data analysis to evaluate consistency, compare compounds, and identify potential performance trends under testing conditions.

## Formula 1 Session Types (FastF1 Codes)
| Code | Session            | Purpose            |
|------|--------------------|--------------------|
| FP1  | Practice 1         | Setup & testing    |
| FP2  | Practice 2         | Long runs          |
| FP3  | Practice 3         | Final practice     |
| Q    | Qualifying         | Sets race grid     |
| SQ   | Sprint Shootout    | Sets sprint grid   |
| S    | Sprint Race        | Short race         |
| R    | Grand Prix         | Main race          |

#### Tech Stack

- Python 3.x
- FastF1
- Matplotlib
- Pandas


## Tire Degradation - 2026 'LEC'
<img width="940" height="498" alt="image" src="https://github.com/user-attachments/assets/63a05cce-8c68-49ed-a2eb-ad17b7b0e59b" />


### Features
- Uses real F1 timing data via FastF1
- Supports 2026 Pre-Season Testing sessions
- Filters competitive laps only
- Visualizes degradation across ALL tire compounds
- Horizontal bar graph for clear stint analysis
- Custom legend for tire types
- Clean, presentation-ready plot


#### Installation
```python
pip install fastf1 matplotlib pandas
```

#### Load Session
```python
schedule = fastf1.get_event_schedule(2026)
testing_event = schedule[schedule['EventName'] == 'Pre-Season Testing'].iloc[0]
session = testing_event.get_session(1)
session.load()
```
#### Filter Driver Laps
```python
laps = session.laps.pick_drivers('LEC').pick_quicklaps()
```

#### Plot Degradation
```python
plt.barh(laps['LapNumber'], lap_times, color=colors)
```
⚠️ Note: Testing sessions involve experimental runs and mixed conditions, so lap times are not representative of competitive race pace.
