import os
import streamlit as st
import fastf1
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import plotly.graph_objects as go

# -------------------- CONFIG --------------------

st.set_page_config(page_title="F1 Analysis", layout="wide")

# Seasons where FastF1 returns lap data. Edit after testing (year_check.py).
LAP_YEARS = [2022, 2021]

# Standings use Ergast/Jolpica, which still loads recent seasons.
STANDINGS_YEARS = [2026, 2025, 2024, 2023, 2022, 2021]

# Set True to show the real error message when a session fails to load.
DEBUG = False

COLOR_MAP = {
    "SOFT": "#ff4d4d",
    "MEDIUM": "#ffd700",
    "HARD": "#cccccc",
    "INTERMEDIATE": "#00cc44",
    "WET": "#0066ff",
}

st.markdown("""
# 🏎️ F1 Analytics Dashboard
### 🛞 Tire Degradation & Performance Insights
""")

st.caption(
    "Data source: FastF1 (F1 timing data + Ergast/Jolpica). "
    "Lap data may be unavailable for some seasons depending on the data source."
)

# -------------------- CACHE --------------------

cache_dir = "cache"
os.makedirs(cache_dir, exist_ok=True)
fastf1.Cache.enable_cache(cache_dir)

# -------------------- HELPERS --------------------

@st.cache_data(show_spinner=False)
def get_schedule(year):
    return fastf1.get_event_schedule(year, include_testing=False)


@st.cache_resource(show_spinner=False)
def load_session(year, event_name, session_type, with_telemetry=False):
    """Load a session. Raises if there is no lap data, so failures are never cached."""
    schedule = fastf1.get_event_schedule(year, include_testing=False)
    event = schedule[schedule["EventName"] == event_name].iloc[0]

    session = event.get_session(session_type)
    session.load(laps=True, telemetry=with_telemetry, weather=False, messages=False)

    try:
        laps = session.laps
    except Exception:
        raise ValueError("No lap data returned for this session")
    if laps is None or laps.empty:
        raise ValueError("No lap data returned for this session")

    return session


def try_load(year, event_name, session_type, with_telemetry=False):
    """Return (session, error). Never raises."""
    try:
        return load_session(year, event_name, session_type, with_telemetry), None
    except Exception as e:
        return None, e


def show_load_error(error):
    st.error(
        "Lap data isn't available for this session right now. "
        "Try another race, session or year."
    )
    if DEBUG and error is not None:
        st.exception(error)


def session_names(event_row):
    return [
        event_row.get(f"Session{i}")
        for i in range(1, 6)
        if event_row.get(f"Session{i}")
    ]


# -------------------- MODE --------------------

mode = st.radio(
    "🏁 Select Mode",
    ["Tire Performance", "Comparison", "Standings", "Telemetry", "Year vs Year"],
    horizontal=True,
)

# -------------------- STANDINGS --------------------

if mode == "Standings":
    year = st.selectbox("Select Year", STANDINGS_YEARS)
    st.subheader(f"🏆 Championship Standings ({year})")
    try:
        from standings import show_standings
        show_standings(year)
    except Exception as e:
        st.error("Standings are unavailable right now. Please try again later.")
        if DEBUG:
            st.exception(e)
    st.stop()

# -------------------- YEAR VS YEAR --------------------

if mode == "Year vs Year":

    st.subheader("📅 Year vs Year — Same Driver, Same Track")

    if len(LAP_YEARS) < 2:
        st.warning("Year vs Year needs at least two seasons with lap data.")
        st.stop()

    col1, col2 = st.columns(2)
    with col1:
        year_a = st.selectbox("📅 Year 1", LAP_YEARS, index=0, key="yvy_year_a")
    with col2:
        year_b = st.selectbox("📅 Year 2", LAP_YEARS, index=1, key="yvy_year_b")

    if year_a == year_b:
        st.warning("⚠️ Please select two different years.")
        st.stop()

    try:
        schedule_a = get_schedule(year_a)
        schedule_b = get_schedule(year_b)
    except Exception as e:
        st.error("❌ Couldn't load the race schedules right now. Please try again later.")
        if DEBUG:
            st.exception(e)
        st.stop()

    common_events = sorted(
        set(schedule_a["EventName"]) & set(schedule_b["EventName"])
    )
    if not common_events:
        st.error("❌ No common races found between the selected years.")
        st.stop()

    race_name = st.selectbox("🏁 Select Grand Prix", common_events, key="yvy_race")

    event_row_a = schedule_a[schedule_a["EventName"] == race_name].iloc[0]
    session_type = st.selectbox(
        "🗂️ Select Session", session_names(event_row_a), key="yvy_session"
    )

    with st.spinner(f"Loading {year_a} session..."):
        session_a, err_a = try_load(year_a, race_name, session_type)
    with st.spinner(f"Loading {year_b} session..."):
        session_b, err_b = try_load(year_b, race_name, session_type)

    if session_a is None or session_b is None:
        show_load_error(err_a or err_b)
        st.stop()

    drivers_a = set(session_a.laps["Driver"].dropna().unique())
    drivers_b = set(session_b.laps["Driver"].dropna().unique())
    common_drivers = sorted(drivers_a & drivers_b)

    if not common_drivers:
        st.warning("⚠️ No common drivers found between the two years for this race.")
        st.stop()

    driver = st.selectbox("🧑‍✈️ Select Driver", common_drivers, key="yvy_driver")

    laps_a = session_a.laps.pick_drivers(driver).pick_accurate()
    laps_b = session_b.laps.pick_drivers(driver).pick_accurate()

    laps_a = laps_a[laps_a["Compound"] != "TEST_UNKNOWN"]
    laps_b = laps_b[laps_b["Compound"] != "TEST_UNKNOWN"]

    if laps_a.empty or laps_b.empty:
        st.warning("⚠️ Not enough accurate laps for this driver in one of the years.")
        st.stop()

    lap_times_a = laps_a["LapTime"].dt.total_seconds()
    lap_times_b = laps_b["LapTime"].dt.total_seconds()

    st.subheader(f"📊 {driver} — {race_name} | {year_a} vs {year_b}")

    fig = go.Figure()

    for compound, group in laps_a.groupby("Compound"):
        fig.add_trace(go.Scatter(
            x=group["LapNumber"],
            y=group["LapTime"].dt.total_seconds(),
            mode="lines+markers",
            name=f"{year_a} — {compound}",
            line=dict(color=COLOR_MAP.get(compound, "#888888"), width=2),
            marker=dict(size=6, symbol="circle"),
            legendgroup=f"{year_a}",
            hovertemplate=(
                f"<b>{year_a} {compound}</b><br>"
                "Lap %{x}<br>Time: %{y:.2f}s<extra></extra>"
            ),
        ))

    for compound, group in laps_b.groupby("Compound"):
        fig.add_trace(go.Scatter(
            x=group["LapNumber"],
            y=group["LapTime"].dt.total_seconds(),
            mode="lines+markers",
            name=f"{year_b} — {compound}",
            line=dict(color=COLOR_MAP.get(compound, "#888888"), width=2, dash="dash"),
            marker=dict(size=6, symbol="diamond"),
            legendgroup=f"{year_b}",
            hovertemplate=(
                f"<b>{year_b} {compound}</b><br>"
                "Lap %{x}<br>Time: %{y:.2f}s<extra></extra>"
            ),
        ))

    fig.update_layout(
        template="plotly_dark",
        title=dict(
            text=f"🏎️ {driver} — {race_name} | {year_a} (solid) vs {year_b} (dashed)",
            font=dict(size=16),
        ),
        xaxis_title="Lap Number",
        yaxis_title="Lap Time (seconds)",
        hovermode="x unified",
        legend=dict(orientation="v", x=1.01, y=1, bordercolor="#444", borderwidth=1),
        height=520,
    )

    st.plotly_chart(fig)

    st.subheader("📈 Summary")

    avg_a, avg_b = lap_times_a.mean(), lap_times_b.mean()
    best_a, best_b = lap_times_a.min(), lap_times_b.min()

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric(f"🏁 {year_a} Avg Lap", f"{avg_a:.3f}s")
    with m2:
        st.metric(f"🏁 {year_b} Avg Lap", f"{avg_b:.3f}s", delta=f"{avg_b - avg_a:+.3f}s")
    with m3:
        st.metric(f"⚡ {year_a} Fastest", f"{best_a:.3f}s")
    with m4:
        st.metric(f"⚡ {year_b} Fastest", f"{best_b:.3f}s", delta=f"{best_b - best_a:+.3f}s")

    st.stop()

# -------------------- YEAR / EVENT / SESSION (remaining modes) --------------------

year = st.selectbox("Select Year", LAP_YEARS)

try:
    schedule = get_schedule(year)
except Exception as e:
    st.error("Couldn't load the race schedule right now. Please try again later.")
    if DEBUG:
        st.exception(e)
    st.stop()

event_names = schedule["EventName"].tolist()
event_name = st.selectbox("Select Grand Prix", event_names)
event = schedule[schedule["EventName"] == event_name].iloc[0]

session_type = st.selectbox("Select Session", session_names(event))

# Only the Telemetry mode needs the heavy telemetry download
needs_telemetry = mode == "Telemetry"

with st.spinner("Loading session data..."):
    session, load_error = try_load(year, event_name, session_type, needs_telemetry)

if session is None:
    show_load_error(load_error)
    st.stop()

laps = session.laps
drivers = sorted(laps["Driver"].dropna().unique())

if not drivers:
    st.warning("No drivers found for this session.")
    st.stop()

# -------------------- TIRE PERFORMANCE --------------------

if mode == "Tire Performance":

    driver = st.selectbox("Select Driver", drivers)

    driver_laps = laps.pick_drivers(driver).pick_accurate()
    driver_laps = driver_laps[driver_laps["Compound"] != "TEST_UNKNOWN"]

    if driver_laps.empty:
        st.warning("No accurate laps found for this driver in this session.")
        st.stop()

    st.subheader("🛞 Tire Performance")

    plt.style.use("dark_background")
    fig, ax = plt.subplots(figsize=(12, 7))

    lap_times = driver_laps["LapTime"].dt.total_seconds()
    colors = driver_laps["Compound"].map(COLOR_MAP).fillna("#888888")

    ax.barh(driver_laps["LapNumber"], lap_times, color=colors)

    ax.set_title(f"{event_name} - {driver} ({year})")
    ax.set_xlabel("Lap Time (seconds)")
    ax.set_ylabel("Lap Number")
    ax.grid(True)

    legend_elements = [
        Patch(facecolor="#ff4d4d", label="Soft"),
        Patch(facecolor="#ffd700", label="Medium"),
        Patch(facecolor="#cccccc", label="Hard"),
        Patch(facecolor="#00cc44", label="Intermediate"),
        Patch(facecolor="#0066ff", label="Wet"),
    ]
    ax.legend(handles=legend_elements, title="Tire Compound")

    st.pyplot(fig)

# -------------------- COMPARISON --------------------

elif mode == "Comparison":

    if len(drivers) < 2:
        st.warning("Need at least two drivers with data for this session.")
        st.stop()

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

    laps1 = laps1[laps1["Compound"] != "TEST_UNKNOWN"]
    laps2 = laps2[laps2["Compound"] != "TEST_UNKNOWN"]

    if laps1.empty or laps2.empty:
        st.warning("Not enough accurate laps for one of these drivers.")
        st.stop()

    st.subheader("🛞 Comparison")

    plt.style.use("dark_background")
    fig, ax = plt.subplots(figsize=(12, 7))

    lap_times1 = laps1["LapTime"].dt.total_seconds()
    lap_times2 = laps2["LapTime"].dt.total_seconds()

    ax.barh(laps1["LapNumber"] - 0.2, lap_times1, height=0.4, label=driver1)
    ax.barh(laps2["LapNumber"] + 0.2, lap_times2, height=0.4, label=driver2)

    ax.set_title(f"{driver1} vs {driver2} — {event_name} ({year})")
    ax.set_xlabel("Lap Time (seconds)")
    ax.set_ylabel("Lap Number")
    ax.legend()
    ax.grid(True)

    st.pyplot(fig)

    col1, col2 = st.columns(2)
    with col1:
        st.metric(f"🏎️ {driver1} avg lap", f"{lap_times1.mean():.2f}s")
    with col2:
        st.metric(f"🏎️ {driver2} avg lap", f"{lap_times2.mean():.2f}s")

# -------------------- TELEMETRY --------------------

elif mode == "Telemetry":

    if len(drivers) < 2:
        st.warning("Need at least two drivers with data for this session.")
        st.stop()

    st.subheader("📈 Interactive Telemetry")

    col1, col2 = st.columns(2)
    with col1:
        driver1 = st.selectbox("Driver 1", drivers)
    with col2:
        driver2 = st.selectbox("Driver 2", drivers, index=1)

    if driver1 == driver2:
        st.warning("⚠️ Select two different drivers")
        st.stop()

    try:
        lap1 = laps.pick_drivers(driver1).pick_fastest()
        lap2 = laps.pick_drivers(driver2).pick_fastest()

        if lap1 is None or lap2 is None:
            raise ValueError("No fastest lap")

        tel1 = lap1.get_car_data().add_distance()
        tel2 = lap2.get_car_data().add_distance()
    except Exception:
        st.error("❌ Telemetry isn't available for these drivers in this session.")
        st.stop()

    tel1 = tel1[tel1["Speed"] > 0]
    tel2 = tel2[tel2["Speed"] > 0]

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=tel1["Distance"],
        y=tel1["Speed"],
        mode="lines",
        name=f"🏎️ {driver1}",
    ))

    fig.add_trace(go.Scatter(
        x=tel2["Distance"],
        y=tel2["Speed"],
        mode="lines",
        name=f"🏎️ {driver2}",
    ))

    fig.update_layout(
        title=f"{driver1} vs {driver2} — Fastest Lap Speed ({event_name} {year})",
        xaxis_title="Distance (m)",
        yaxis_title="Speed (km/h)",
        template="plotly_dark",
        hovermode="x unified",
    )

    st.plotly_chart(fig)