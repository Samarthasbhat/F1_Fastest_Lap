import streamlit as st
import fastf1
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

st.set_page_config(page_title="F1 Analysis", layout="wide")

st.title("🏎️ F1 Tire Degradation Analysis")

# -------------------- YEAR --------------------

year = st.selectbox("Select Year", [2023, 2024])

# -------------------- LOAD SCHEDULE --------------------

@st.cache_data
def get_schedule(year):
    fastf1.Cache.enable_cache('cache')
    return fastf1.get_event_schedule(year)

schedule = get_schedule(year)

# -------------------- EVENT --------------------

event_names = schedule['EventName'].tolist()
event_name = st.selectbox("Select Grand Prix", event_names)

event = schedule[schedule['EventName'] == event_name].iloc[0]

# -------------------- SESSION / TESTING LOGIC --------------------

is_testing = "Testing" in event_name

if is_testing:
    st.info("🧪 Pre-Season Testing → Select Day")

    day = st.selectbox("Select Testing Day", [1, 2, 3])
    session_type = day

else:
    available_sessions = []

    for i in range(1, 6):
        name = event.get(f"Session{i}")
        if name is not None:
            available_sessions.append(name)

    session_type = st.selectbox("Select Session", available_sessions)

# -------------------- LOAD SESSION --------------------

@st.cache_data
def load_session(year, event_name, session_type):
    fastf1.Cache.enable_cache('cache')

    schedule = fastf1.get_event_schedule(year)
    event = schedule[schedule['EventName'] == event_name].iloc[0]

    session = event.get_session(session_type)
    session.load(laps=True)

    return session

with st.spinner("Loading session data..."):
    session = load_session(year, event_name, session_type)

# -------------------- SAFETY CHECK --------------------

if session.laps is None or session.laps.empty:
    st.error("No data available for this session")
    st.stop()

# -------------------- DRIVER --------------------

drivers = session.laps['Driver'].dropna().unique()
driver = st.selectbox("Select Driver", drivers)

driver_laps = session.laps.pick_drivers(driver).pick_accurate()

# Remove unknown compounds
driver_laps = driver_laps[driver_laps['Compound'] != 'TEST_UNKNOWN']

# -------------------- DEBUG --------------------

st.write("Compound Distribution:")
st.dataframe(driver_laps['Compound'].value_counts())

# -------------------- DATA --------------------

lap_times = driver_laps['LapTime'].dt.total_seconds()

color_map = {
    'SOFT': '#ff4d4d',
    'MEDIUM': '#ffd700',
    'HARD': '#cccccc',
    'INTERMEDIATE': '#00cc44',
    'WET': '#0066ff'
}

colors = driver_laps['Compound'].map(color_map).fillna('#888888')

# -------------------- PLOT --------------------

plt.style.use('dark_background')

fig, ax = plt.subplots(figsize=(12, 7))

ax.barh(
    driver_laps['LapNumber'],
    lap_times,
    color=colors
)

ax.set_title(f"{event_name} - {driver} ({session_type} {year})")
ax.set_xlabel("Lap Time (seconds)")
ax.set_ylabel("Lap Number")

legend_elements = [
    Patch(facecolor='#ff4d4d', label='Soft'),
    Patch(facecolor='#ffd700', label='Medium'),
    Patch(facecolor='#cccccc', label='Hard'),
    Patch(facecolor='#00cc44', label='Intermediate'),
    Patch(facecolor='#0066ff', label='Wet')
]

ax.legend(handles=legend_elements, title="Tire Compound")
ax.grid(True)

st.pyplot(fig)