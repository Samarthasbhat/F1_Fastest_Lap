import fastf1
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

fastf1.Cache.enable_cache('cache')

schedule = fastf1.get_event_schedule(2026)
testing_event = schedule[schedule['EventName'] == 'Pre-Season Testing'].iloc[0]

session = testing_event.get_session(1)   # Day 1
session.load()

#drivers_lap
driver_laps = session.laps.pick_drivers('LEC').pick_quicklaps()

# #Lap
# fastest_lap = session.laps.pick_fastest()
# slowest_lap = session.laps.pick_accurate().sort_values(by='LapTime').iloc[-1]
#
# #Telemetry
# tel_fast = fastest_lap.get_car_data().add_distance()
# tel_slow = slowest_lap.get_car_data().add_distance()
#
# #Remove zero speed garbage
# tel_fast = tel_fast[tel_fast['Speed']>0]
# tel_slow = tel_slow[tel_slow['Speed']>0]
#
# #Compound
# compound_fast = fastest_lap['Compound']
# compound_slow = slowest_lap['Compound']
#
# plt.figure(figsize=(11,5))
# plt.plot(
#    tel_fast['Distance'],
#          tel_fast['Speed'],
#          color='black',
#          label=f"Fastest — {fastest_lap['Driver']} ({compound_fast})"
#          )
#
# plt.plot(
#    tel_slow['Distance'],
#          tel_slow['Speed'],
#          color='orange',
#          label=f"Slowest — {slowest_lap['Driver']} ({compound_slow})"
#          )
#
# plt.title(f"Fastest Lap vs Slowest Lap")
# plt.xlabel("Distance (m)")
# plt.ylabel("Speed (km/h)")

# -------------------- FOR Tire Degradation
#Compound
# compound = 'SOFT'
# driver_laps = driver_laps[driver_laps['Compound']==compound]



#Convert lap time to seconds
lap_times = driver_laps['LapTime'].dt.total_seconds()


color_map = {
    'SOFT': 'red',
    'MEDIUM': 'yellow',
    'HARD': 'white',
    'INTERMEDIATE': 'green',
    'WET': 'blue'
}

colors = driver_laps['Compound'].map(color_map).fillna('gray')

#Plot - H Bars
plt.figure(figsize=(11,7))

plt.barh(
    driver_laps['LapNumber'],
    lap_times,
    color=colors,
    label=colors
)



plt.title(f"Tire Degradation - LEC 2026 Pre-Season")
plt.xlabel("Lap Time(Seconds)")
plt.ylabel("Lap Number")

# plt.gca().invert_xaxis()

legend_elements = [
    Patch(facecolor='red', label='Soft'),
    Patch(facecolor='yellow', label='Medium'),
    Patch(facecolor='white', edgecolor='black', label='Hard'),
    Patch(facecolor='green', label='Intermediate'),
    Patch(facecolor='blue', label='Wet')
]


plt.legend(handles=legend_elements, title='Tire Compound')
plt.grid(True)

plt.show()
