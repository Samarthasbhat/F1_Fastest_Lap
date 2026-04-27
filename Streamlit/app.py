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
    ["Tire Performance", "Comparison", "Standings", "Telemetry" , "Year vs Year"],
    horizontal=True
)

# -------------------- CACHE --------------------

cache_dir = "cache"
os.makedirs(cache_dir, exist_ok=True)
fastf1.Cache.enable_cache(cache_dir)

# -------------------- YEAR (skip for Year vs Year — handled inside) --------------------

if mode != "Year vs Year":
    year = st.selectbox("Select Year", [2021, 2022, 2023, 2024, 2025, 2026])

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

# -------------------- YEAR VS YEAR MODE --------------------

if mode == "Year vs Year":

    st.subheader("📅 Year vs Year — Same Driver, Same Track")

    # Year selectors
    col1, col2 = st.columns(2)
    with col1:
        year_a = st.selectbox("📅 Year 1", [2021, 2022, 2023, 2024, 2025, 2026], index=2, key="yvy_year_a")
    with col2:
        year_b = st.selectbox("📅 Year 2", [2021, 2022, 2023, 2024, 2025, 2026], index=3, key="yvy_year_b")

    if year_a == year_b:
        st.warning("⚠️ Please select two different years.")
        st.stop()

    # Load schedules for both years
    try:
        schedule_a = get_schedule(year_a)
        schedule_b = get_schedule(year_b)
    except Exception as e:
        st.error(f"❌ Failed to load schedules: {e}")
        st.stop()

    # Find common Grand Prix names across both years
    events_a = set(schedule_a['EventName'].tolist())
    events_b = set(schedule_b['EventName'].tolist())
    common_events = sorted(events_a & events_b)

    if not common_events:
        st.error("❌ No common races found between the selected years.")
        st.stop()

    race_name = st.selectbox("🏁 Select Grand Prix", common_events, key="yvy_race")

    # Session type
    event_row_a = schedule_a[schedule_a['EventName'] == race_name].iloc[0]
    sessions_a = [event_row_a.get(f"Session{i}") for i in range(1, 6) if event_row_a.get(f"Session{i}")]
    session_type = st.selectbox("🗂️ Select Session", sessions_a, key="yvy_session")

    # Load session helper
    @st.cache_data
    def load_session(year, event_name, session_type):
        try:
            schedule = fastf1.get_event_schedule(year)
            event = schedule[schedule['EventName'] == event_name].iloc[0]
            session = event.get_session(session_type)
            session.load()
            if session.laps is None or session.laps.empty:
                return None
            return session
        except Exception as e:
            st.error(f"❌ Error loading {year} session: {e}")
            return None

    with st.spinner(f"Loading {year_a} session..."):
        session_a = load_session(year_a, race_name, session_type)

    with st.spinner(f"Loading {year_b} session..."):
        session_b = load_session(year_b, race_name, session_type)

    if session_a is None or session_b is None:
        st.error("❌ Could not load one or both sessions. They may not have occurred yet.")
        st.stop()

    # Find drivers present in BOTH sessions
    drivers_a = set(session_a.laps['Driver'].dropna().unique())
    drivers_b = set(session_b.laps['Driver'].dropna().unique())
    common_drivers = sorted(drivers_a & drivers_b)

    if not common_drivers:
        st.warning("⚠️ No common drivers found between the two years for this race.")
        st.stop()

    driver = st.selectbox("🧑‍✈️ Select Driver", common_drivers, key="yvy_driver")

    # Extract laps
    laps_a = session_a.laps.pick_drivers(driver).pick_accurate()
    laps_b = session_b.laps.pick_drivers(driver).pick_accurate()

    laps_a = laps_a[laps_a['Compound'] != 'TEST_UNKNOWN']
    laps_b = laps_b[laps_b['Compound'] != 'TEST_UNKNOWN']

    lap_times_a = laps_a['LapTime'].dt.total_seconds()
    lap_times_b = laps_b['LapTime'].dt.total_seconds()

    # ---- Plotly Interactive Chart ----
    st.subheader(f"📊 {driver} — {race_name} | {year_a} vs {year_b}")

    color_map = {
        'SOFT': '#ff4d4d',
        'MEDIUM': '#ffd700',
        'HARD': '#e0e0e0',
        'INTERMEDIATE': '#00cc44',
        'WET': '#3399ff',
    }

    fig = go.Figure()

    # Year A traces (one per compound)
    for compound, group in laps_a.groupby('Compound'):
        t = group['LapTime'].dt.total_seconds()
        fig.add_trace(go.Scatter(
            x=group['LapNumber'],
            y=t,
            mode='lines+markers',
            name=f"{year_a} — {compound}",
            line=dict(color=color_map.get(compound, '#888888'), width=2),
            marker=dict(size=6, symbol='circle'),
            legendgroup=f"{year_a}",
            hovertemplate=(
                f"<b>{year_a} {compound}</b><br>"
                "Lap %{x}<br>"
                "Time: %{y:.2f}s<extra></extra>"
            )
        ))

    # Year B traces (dashed, same colors)
    for compound, group in laps_b.groupby('Compound'):
        t = group['LapTime'].dt.total_seconds()
        fig.add_trace(go.Scatter(
            x=group['LapNumber'],
            y=t,
            mode='lines+markers',
            name=f"{year_b} — {compound}",
            line=dict(color=color_map.get(compound, '#888888'), width=2, dash='dash'),
            marker=dict(size=6, symbol='diamond'),
            legendgroup=f"{year_b}",
            hovertemplate=(
                f"<b>{year_b} {compound}</b><br>"
                "Lap %{x}<br>"
                "Time: %{y:.2f}s<extra></extra>"
            )
        ))

    fig.update_layout(
        template="plotly_dark",
        title=dict(
            text=f"🏎️ {driver} — {race_name}  |  {year_a} <span style='color:#888'>(solid)</span>  vs  {year_b} <span style='color:#888'>(dashed)</span>",
            font=dict(size=16)
        ),
        xaxis_title="Lap Number",
        yaxis_title="Lap Time (seconds)",
        hovermode="x unified",
        legend=dict(
            orientation="v",
            x=1.01,
            y=1,
            bordercolor="#444",
            borderwidth=1
        ),
        height=520,
    )

    st.plotly_chart(fig, use_container_width=True)

    # ---- Summary Metrics ----
    st.subheader("📈 Summary")

    m_col1, m_col2, m_col3, m_col4 = st.columns(4)

    avg_a = lap_times_a.mean()
    avg_b = lap_times_b.mean()
    best_a = lap_times_a.min()
    best_b = lap_times_b.min()
    delta_avg = avg_b - avg_a
    delta_best = best_b - best_a

    with m_col1:
        st.metric(f"🏁 {year_a} Avg Lap", f"{avg_a:.3f}s")
    with m_col2:
        st.metric(f"🏁 {year_b} Avg Lap", f"{avg_b:.3f}s", delta=f"{delta_avg:+.3f}s")
    with m_col3:
        st.metric(f"⚡ {year_a} Fastest", f"{best_a:.3f}s")
    with m_col4:
        st.metric(f"⚡ {year_b} Fastest", f"{best_b:.3f}s", delta=f"{delta_best:+.3f}s")

    st.stop()

# -------------------- LOAD SCHEDULE (non-YvY modes) --------------------

schedule = get_schedule(year)
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
        session.load()
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

# -------------------- TIRE PERFORMANCE --------------------

if mode == "Tire Performance":

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

    avg1 = lap_times1.mean()
    avg2 = lap_times2.mean()

    col1, col2 = st.columns(2)

    with col1:
        st.metric(f"🏎️ {driver1}", f"{avg1:.2f}s")

    with col2:
        st.metric(f"🏎️ {driver2}", f"{avg2:.2f}s")

# -------------------- TELEMETRY --------------------

elif mode == "Telemetry":

    if year != "2026":

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
            mode='lines+markers',
            marker=dict(size=6, symbol='circle'),
            name=f"🏎️ {driver1}"
        ))

        fig.add_trace(go.Scatter(
            x=tel2['Distance'],
            y=tel2['Speed'],
            mode='lines+markers',
            marker=dict(size=6, symbol='diamond'),
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
    else:
        st.error("The required data is not present")
        st.stop()
