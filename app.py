import os
import streamlit as st
import fastf1
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

# -------------------- CONFIG --------------------

st.set_page_config(page_title="F1 Analysis", layout="wide")
st.title("🏎️ F1 Tire Degradation Analysis")

# Only list seasons that load lap data (check with year_check.py)
AVAILABLE_YEARS = [2022, 2021]

st.caption(
    "Data source: FastF1 (F1 timing data + Ergast/Jolpica). "
    "Lap data may be unavailable for some seasons depending on the data source."
)

# -------------------- CACHE SETUP --------------------

# On your Mac, reuse FastF1's default cache if it exists.
# On Streamlit Cloud that folder doesn't exist, so a local "cache" folder is used.
default_mac_cache = os.path.expanduser("~/Library/Caches/fastf1")
cache_dir = default_mac_cache if os.path.isdir(default_mac_cache) else "cache"
os.makedirs(cache_dir, exist_ok=True)
fastf1.Cache.enable_cache(cache_dir)

# -------------------- FUNCTIONS --------------------

@st.cache_data(show_spinner=False)
def get_schedule(year):
    return fastf1.get_event_schedule(year, include_testing=False)


@st.cache_resource(show_spinner=False)
def load_session(year, event_name, session_type):
    schedule = fastf1.get_event_schedule(year, include_testing=False)
    event = schedule[schedule["EventName"] == event_name].iloc[0]

    session = event.get_session(session_type)
    session.load(laps=True, telemetry=False, weather=False, messages=False)

    # Raise if lap data is missing, so a failed load is never cached
    laps = session.laps
    if laps is None or laps.empty:
        raise ValueError("No lap data returned for this session")

    return session

# -------------------- YEAR --------------------

year = st.selectbox("Select Year", AVAILABLE_YEARS)

# -------------------- SCHEDULE --------------------

try:
    schedule = get_schedule(year)
except Exception:
    st.error("Couldn't load the race schedule right now. Please try again later.")
    st.stop()

# -------------------- EVENT --------------------

event_names = schedule["EventName"].tolist()
event_name = st.selectbox("Select Grand Prix", event_names)

event = schedule[schedule["EventName"] == event_name].iloc[0]

# -------------------- SESSION --------------------

available_sessions = []
for i in range(1, 6):
    name = event.get(f"Session{i}")
    if name:
        available_sessions.append(name)

session_type = st.selectbox("Select Session", available_sessions)

# -------------------- LOAD SESSION --------------------

try:
    with st.spinner("Loading session data..."):
        session = load_session(year, event_name, session_type)
    laps = session.laps
except Exception as e:
    st.error(
        "Lap data isn't available for this session right now. "
        "Try another race, session or year."
    )
    #st.exception(e)  # TEMPORARY for debugging: delete this line before deploying
    st.stop()

# -------------------- DRIVER --------------------

drivers = laps["Driver"].dropna().unique()
driver = st.selectbox("Select Driver", drivers)

driver_laps = laps.pick_drivers(driver).pick_accurate()
driver_laps = driver_laps[driver_laps["Compound"] != "TEST_UNKNOWN"]

if driver_laps.empty:
    st.warning("No accurate laps found for this driver in this session.")
    st.stop()

# -------------------- DATA --------------------

lap_times = driver_laps["LapTime"].dt.total_seconds()

color_map = {
    "SOFT": "#ff4d4d",
    "MEDIUM": "#ffd700",
    "HARD": "#cccccc",
    "INTERMEDIATE": "#00cc44",
    "WET": "#0066ff",
}

colors = driver_laps["Compound"].map(color_map).fillna("#888888")

# -------------------- PLOT --------------------

plt.style.use("dark_background")

fig, ax = plt.subplots(figsize=(12, 7))

ax.barh(driver_laps["LapNumber"], lap_times, color=colors)

ax.set_title(f"{event_name} - {driver} ({session_type} {year})")
ax.set_xlabel("Lap Time (seconds)")
ax.set_ylabel("Lap Number")

legend_elements = [
    Patch(facecolor="#ff4d4d", label="Soft"),
    Patch(facecolor="#ffd700", label="Medium"),
    Patch(facecolor="#cccccc", label="Hard"),
    Patch(facecolor="#00cc44", label="Intermediate"),
    Patch(facecolor="#0066ff", label="Wet"),
]

ax.legend(handles=legend_elements, title="Tire Compound")
ax.grid(True)

st.pyplot(fig)