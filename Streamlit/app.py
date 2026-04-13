import streamlit as st
import fastf1
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import plotly.graph_objects as go
import os

# -------------------- CONFIG --------------------

st.set_page_config(page_title="F1 Analysis", layout="wide")

st.markdown("""
# 🏎️ F1 Analytics Dashboard
### 🛞 Tire Degradation & Performance Insights
""")

# -------------------- MODE --------------------

mode = st.radio(
    "🏁 Select Mode",
    ["Single Driver", "Comparison", "Standings", "Telemetry"],
    horizontal=True
)

# -------------------- CACHE --------------------

cache_dir = "cache"
os.makedirs(cache_dir, exist_ok=True)
fastf1.Cache.enable_cache(cache_dir)

# -------------------- YEAR --------------------

year = st.selectbox("Select Year", [2021, 2022, 2023, 2024])

# -------------------- STANDINGS --------------------

if mode == "Standings":
    from standings import show_standings
    st.subheader(f"🏆 Championship Standings ({year})")
    show_standings(year)
    st.stop()

# -------------------- LOAD SCHEDULE --------------------

@st.cache_data
def get_schedule(year):
    return fastf1.get_event_schedule(year)

schedule = get_schedule(year)

# -------------------- EVENT --------------------

event_names = schedule['EventName'].tolist()
event_name = st.selectbox("Select Grand Prix", event_names)

event = schedule[schedule['EventName'] == event_name].iloc[0]

# -------------------- SESSION --------------------

is_testing = event['EventFormat'] == 'testing'

if is_testing:
    session_type = st.selectbox("Select Testing Day", [1, 2, 3])
else:
    sessions = [event.get(f"Session{i}") for i in range(1, 6) if event.get(f"Session{i}")]
    session_type = st.selectbox("Select Session", sessions)

# -------------------- LOAD SESSION --------------------

@st.cache_data
def load_session(year, event_name, session_type):
    try:
        schedule = fastf1.get_event_schedule(year)
        event = schedule[schedule['EventName'] == event_name].iloc[0]

        session = event.get_session(session_type)
        session.load()  # ✅ important

        if session.laps is None or session.laps.empty:
            return None

        return session

    except Exception as e:
        print("ERROR:", e)
        return None

session = load_session(year, event_name, session_type)

if session is None:
    st.error("❌ Failed to load session data")
    st.stop()

laps = session.laps
drivers = sorted(laps['Driver'].dropna().unique())

# -------------------- SINGLE DRIVER --------------------

if mode == "Single Driver":

    driver = st.selectbox("Select Driver", drivers)

    driver_laps = laps.pick_drivers(driver).pick_accurate()
    driver_laps = driver_laps[driver_laps['Compound'] != 'TEST_UNKNOWN']

    st.subheader("🛞 Tire Performance")

    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(12, 7))

    color_map = {
        'SOFT': '#ff4d4d',
        'MEDIUM': '#ffd700',
        'HARD': '#cccccc',
        'INTERMEDIATE': '#00cc44',
        'WET': '#0066ff'
    }

    lap_times = driver_laps['LapTime'].dt.total_seconds()
    colors = driver_laps['Compound'].map(color_map).fillna('#888888')

    ax.barh(driver_laps['LapNumber'], lap_times, color=colors)

    ax.set_title(f"{event_name} - {driver}")
    ax.set_xlabel("Lap Time (seconds)")
    ax.set_ylabel("Lap Number")
    ax.grid(True)

    legend_elements = [
        Patch(facecolor='#ff4d4d', label='🛞 Soft'),
        Patch(facecolor='#ffd700', label='🛞 Medium'),
        Patch(facecolor='#cccccc', label='🛞 Hard'),
        Patch(facecolor='#00cc44', label='🛞 Intermediate'),
        Patch(facecolor='#0066ff', label='🛞 Wet')
    ]

    ax.legend(handles=legend_elements)

    st.pyplot(fig)

# -------------------- COMPARISON --------------------

elif mode == "Comparison":

    col1, col2 = st.columns(2)

    with col1:
        driver1 = st.selectbox("Driver 1", drivers)

    with col2:
        driver2 = st.selectbox("Driver 2", drivers, index=1)

    if driver1 == driver2:
        st.warning("⚠️ Select two different drivers")
        st.stop()

    laps1 = laps.pick_drivers(driver1).pick_accurate()
    laps2 = laps.pick_drivers(driver2).pick_accurate()

    st.subheader("🛞 Comparison")

    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(12, 7))

    lap_times1 = laps1['LapTime'].dt.total_seconds()
    lap_times2 = laps2['LapTime'].dt.total_seconds()

    ax.barh(laps1['LapNumber'] - 0.2, lap_times1, height=0.4, label=driver1)
    ax.barh(laps2['LapNumber'] + 0.2, lap_times2, height=0.4, label=driver2)

    ax.set_title(f"{driver1} vs {driver2}")
    ax.set_xlabel("Lap Time (seconds)")
    ax.set_ylabel("Lap Number")
    ax.legend()
    ax.grid(True)

    st.pyplot(fig)

    # Metrics
    avg1 = lap_times1.mean()
    avg2 = lap_times2.mean()

    col1, col2 = st.columns(2)

    with col1:
        st.metric(f"🏎️ {driver1}", f"{avg1:.2f}s")

    with col2:
        st.metric(f"🏎️ {driver2}", f"{avg2:.2f}s")

# -------------------- TELEMETRY --------------------

elif mode == "Telemetry":

    st.subheader("📈 Interactive Telemetry")

    col1, col2 = st.columns(2)

    with col1:
        driver1 = st.selectbox("Driver 1", drivers)

    with col2:
        driver2 = st.selectbox("Driver 2", drivers, index=1)

    if driver1 == driver2:
        st.warning("⚠️ Select two different drivers")
        st.stop()

    lap1 = laps.pick_drivers(driver1).pick_fastest()
    lap2 = laps.pick_drivers(driver2).pick_fastest()

    if lap1 is None or lap2 is None:
        st.error("❌ Telemetry not available")
        st.stop()

    tel1 = lap1.get_car_data().add_distance()
    tel2 = lap2.get_car_data().add_distance()

    tel1 = tel1[tel1['Speed'] > 0]
    tel2 = tel2[tel2['Speed'] > 0]

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=tel1['Distance'],
        y=tel1['Speed'],
        mode='lines',
        name=f"🏎️ {driver1}"
    ))

    fig.add_trace(go.Scatter(
        x=tel2['Distance'],
        y=tel2['Speed'],
        mode='lines',
        name=f"🏎️ {driver2}"
    ))

    fig.update_layout(
        title=f"{driver1} vs {driver2} Telemetry",
        xaxis_title="Distance (m)",
        yaxis_title="Speed (km/h)",
        template="plotly_dark",
        hovermode="x unified"
    )

    st.plotly_chart(fig, use_container_width=True)
