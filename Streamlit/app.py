import os
import streamlit as st
import fastf1
import plotly.graph_objects as go
# CHANGED 1: matplotlib and Patch imports removed. Every chart is now Plotly, so all modes look and behave the same.

# -------------------- CONFIG --------------------

# CHANGED 2: browser-tab title now matches the page heading
st.set_page_config(page_title="F1 Analytics Dashboard", page_icon="🏎️", layout="wide")

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

# CHANGED 3: "Tire" -> "Tyre" everywhere, and the mode name lives in one constant
# so the radio button and the `if mode == ...` check can never drift apart.
MODE_TYRE = "Tyre Performance"
MODES = [MODE_TYRE, "Comparison", "Standings", "Telemetry", "Year vs Year"]

st.markdown("""
# 🏎️ F1 Analytics Dashboard
### 🛞 Race Analysis & Performance Insights
""")

# CHANGED 4: shorter note that also says which seasons each mode covers, plus the disclaimer
st.caption(
    f"Data: FastF1 and Ergast/Jolpica. Lap-based modes cover {', '.join(str(y) for y in sorted(LAP_YEARS))}; "
    "standings cover more seasons. Some sessions may have limited lap data. "
    "Unofficial project, not associated with Formula 1 or the FIA."
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
    names = []
    for i in range(1, 6):
        name = event_row.get(f"Session{i}")
        # CHANGED 5: accept only real, non-empty text (a missing value is truthy and would slip through)
        if isinstance(name, str) and name:
            names.append(name)
    return names


def default_session_index(names):
    # CHANGED 6: open on the Race, which has cleaner tyre data than Practice 1
    return names.index("Race") if "Race" in names else 0


def drivers_by_laps(laps):
    # CHANGED 7: drivers ranked by laps completed, so the defaults are drivers with plenty of data
    # (the old default was whoever came first alphabetically, e.g. ALB)
    return list(laps["Driver"].dropna().value_counts().index)


def clean_laps(laps, driver):
    driver_laps = laps.pick_drivers(driver).pick_accurate()
    return driver_laps[driver_laps["Compound"] != "TEST_UNKNOWN"]


# -------------------- MODE --------------------

mode = st.radio("🏁 Select Mode", MODES, horizontal=True)

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

    # CHANGED 8: honest caveat; 2022 was a regulation change, so this is not a like-for-like driver comparison
    st.caption(
        "2022 brought new cars and 18-inch tyres, so differences between 2021 and 2022 "
        "reflect the car and tyre change as well as the driver."
    )

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

    c_race, c_session = st.columns(2)
    with c_race:
        race_name = st.selectbox("🏁 Select Grand Prix", common_events, key="yvy_race")

    event_row_a = schedule_a[schedule_a["EventName"] == race_name].iloc[0]
    names_a = session_names(event_row_a)
    with c_session:
        session_type = st.selectbox(
            "🗂️ Select Session", names_a,
            index=default_session_index(names_a), key="yvy_session"
        )

    # CHANGED 9: spinner says the first load can be slow
    with st.spinner(f"Loading {year_a} session... the first load can take a few minutes"):
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

    ranked = [d for d in drivers_by_laps(session_a.laps) if d in common_drivers]
    default_driver = common_drivers.index(ranked[0]) if ranked else 0
    driver = st.selectbox("🧑‍✈️ Select Driver", common_drivers,
                          index=default_driver, key="yvy_driver")

    laps_a = clean_laps(session_a.laps, driver)
    laps_b = clean_laps(session_b.laps, driver)

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

# CHANGED 10: year, Grand Prix and session sit in one row instead of three stacked full-width boxes
c_year, c_gp, c_session = st.columns(3)

with c_year:
    year = st.selectbox("Select Year", LAP_YEARS)

try:
    schedule = get_schedule(year)
except Exception as e:
    st.error("Couldn't load the race schedule right now. Please try again later.")
    if DEBUG:
        st.exception(e)
    st.stop()

event_names = schedule["EventName"].tolist()
with c_gp:
    event_name = st.selectbox("Select Grand Prix", event_names)
event = schedule[schedule["EventName"] == event_name].iloc[0]

names = session_names(event)
with c_session:
    session_type = st.selectbox("Select Session", names, index=default_session_index(names))

# Only the Telemetry mode needs the heavy telemetry download
needs_telemetry = mode == "Telemetry"

# CHANGED 9 (continued): same friendlier spinner message
with st.spinner("Loading session data... the first load can take a few minutes"):
    session, load_error = try_load(year, event_name, session_type, needs_telemetry)

if session is None:
    show_load_error(load_error)
    st.stop()

laps = session.laps
drivers = sorted(laps["Driver"].dropna().unique())

if not drivers:
    st.warning("No drivers found for this session.")
    st.stop()

ranked_drivers = drivers_by_laps(laps)

# -------------------- TYRE PERFORMANCE --------------------

if mode == MODE_TYRE:

    driver = st.selectbox("Select Driver", drivers, index=drivers.index(ranked_drivers[0]))

    driver_laps = clean_laps(laps, driver)

    if driver_laps.empty:
        st.warning("No accurate laps found for this driver in this session.")
        st.stop()

    st.subheader("🛞 Tyre Performance")

    # CHANGED 11: dots on a lap-time axis instead of bars that start at zero.
    # With bars every lap looked about the same length, so pace differences were invisible.
    fig = go.Figure()

    for _, stint in driver_laps.groupby("Stint"):
        fig.add_trace(go.Scatter(
            x=stint["LapNumber"],
            y=stint["LapTime"].dt.total_seconds(),
            mode="lines",
            line=dict(color="#555555", width=1),
            hoverinfo="skip",
            showlegend=False,
        ))

    for compound, group in driver_laps.groupby("Compound"):
        fig.add_trace(go.Scatter(
            x=group["LapNumber"],
            y=group["LapTime"].dt.total_seconds(),
            mode="markers",
            name=str(compound).title(),   # legend lists only the compounds this driver used
            marker=dict(size=8, color=COLOR_MAP.get(compound, "#888888"),
                        line=dict(color="black", width=1)),
            hovertemplate="Lap %{x}<br>Time: %{y:.2f}s<extra></extra>",
        ))

    fig.update_layout(
        template="plotly_dark",
        title=f"{event_name} - {driver} ({session_type} {year})",
        xaxis_title="Lap Number",
        yaxis_title="Lap Time (seconds)",
        legend_title_text="Tyre compound",
        height=520,
    )
    st.plotly_chart(fig)

    # CHANGED 12: honest note about what this chart can and cannot show
    st.caption(
        "Lap times are not fuel-corrected, so a flat or falling line does not mean the tyres are "
        "not wearing. The repo's tyre_deg.py gives the fuel-corrected analysis."
    )

# -------------------- COMPARISON --------------------

elif mode == "Comparison":

    if len(drivers) < 2:
        st.warning("Need at least two drivers with data for this session.")
        st.stop()

    # CHANGED 7 (continued): defaults are the two drivers with the most laps
    default1 = drivers.index(ranked_drivers[0])
    default2 = drivers.index(ranked_drivers[1])

    col1, col2 = st.columns(2)
    with col1:
        driver1 = st.selectbox("Driver 1", drivers, index=default1)
    with col2:
        driver2 = st.selectbox("Driver 2", drivers, index=default2)

    if driver1 == driver2:
        st.warning("⚠️ Select two different drivers")
        st.stop()

    laps1 = clean_laps(laps, driver1)
    laps2 = clean_laps(laps, driver2)

    if laps1.empty or laps2.empty:
        st.warning("Not enough accurate laps for one of these drivers.")
        st.stop()

    st.subheader("🛞 Comparison")

    lap_times1 = laps1["LapTime"].dt.total_seconds()
    lap_times2 = laps2["LapTime"].dt.total_seconds()

    # CHANGED 13: two lines on a lap-time axis instead of paired bars from zero
    fig = go.Figure()
    for drv, drv_laps, times in ((driver1, laps1, lap_times1), (driver2, laps2, lap_times2)):
        fig.add_trace(go.Scatter(
            x=drv_laps["LapNumber"],
            y=times,
            mode="lines+markers",
            name=drv,
            marker=dict(size=6),
            hovertemplate=f"<b>{drv}</b><br>Lap %{{x}}<br>Time: %{{y:.2f}}s<extra></extra>",
        ))

    fig.update_layout(
        template="plotly_dark",
        title=f"{driver1} vs {driver2} — {event_name} ({year})",
        xaxis_title="Lap Number",
        yaxis_title="Lap Time (seconds)",
        hovermode="x unified",
        height=520,
    )
    st.plotly_chart(fig)

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

    default1 = drivers.index(ranked_drivers[0])
    default2 = drivers.index(ranked_drivers[1])

    col1, col2 = st.columns(2)
    with col1:
        driver1 = st.selectbox("Driver 1", drivers, index=default1)
    with col2:
        driver2 = st.selectbox("Driver 2", drivers, index=default2)

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