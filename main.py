import fastf1
import fastf1.plotting
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from choice import get_telemetry
from drs import draw_drs_zones, draw_detection_line, update_car_drs_style

# =============================
# SETUP
# =============================
fastf1.Cache.enable_cache("cache")
fastf1.plotting.setup_mpl()

paused = False
frame_idx = 0
speed_multiplier = 1

# =============================
# LOAD SESSION (WEEKEND 1)
# =============================
session = fastf1.get_session(2025, 24, 'R')
session.load()

event_name = session.event["EventName"]
event_year = session.event.year
gp_title = f"{event_year} {event_name}"

all_driver_numbers = session.drivers

# =============================
# TRACK BACKGROUND
# =============================
lap = session.laps.pick_fastest()
track_tel = lap.get_telemetry()

fig, ax = plt.subplots(figsize=(14, 8))
fig.patch.set_facecolor("black")
ax.set_facecolor("black")
ax.axis("off")

# Track outer border
ax.plot(
    track_tel["X"],
    track_tel["Y"],
    color="black",
    linewidth=16,
    solid_capstyle="round",
    zorder=0
)

# Track inner surface
ax.plot(
    track_tel["X"],
    track_tel["Y"],
    color="white",
    linewidth=8,
    solid_capstyle="round",
    zorder=1
)

# =============================
# FIX TRACK CUTTING (IMPORTANT)
# =============================
x_min = track_tel["X"].min()
x_max = track_tel["X"].max()
y_min = track_tel["Y"].min()
y_max = track_tel["Y"].max()

x_padding = (x_max - x_min) * 0.1
y_padding = (y_max - y_min) * 0.1
leaderboard_space = (x_max - x_min) * 0.6

ax.set_xlim(x_min - x_padding, x_max + leaderboard_space)
ax.set_ylim(y_min - y_padding, y_max + y_padding)
ax.set_aspect('equal', adjustable='box')

# =============================
# DRS VISUALS
# =============================
draw_drs_zones(ax, lap)
draw_detection_line(ax, lap)

# =============================
# GP TITLE
# =============================
ax.text(
    0.5, 0.97,
    gp_title.upper(),
    transform=ax.transAxes,
    fontsize=18,
    color="white",
    fontweight="bold",
    ha="center",
    va="top",
    zorder=20
)

ax.text(
    0.5, 0.93,
    "FASTEST LAP MODE",
    transform=ax.transAxes,
    fontsize=12,
    color="#00ff66",
    ha="center",
    va="top",
    zorder=20
)

# =============================
# LOAD FASTEST TELEMETRY
# =============================
print("Loading FASTEST laps...")
telemetry, _ = get_telemetry(session, all_driver_numbers, "FASTEST")

driver_numbers = list(telemetry.keys())
max_frames = min(len(telemetry[d]) for d in driver_numbers)

# =============================
# GLOBAL CONTAINERS
# =============================
cars = {}
leaderboard_bg = {}
leaderboard_text = {}
driver_codes = {}
row_height = (y_max - y_min) * 0.06
header_offset = (y_max - y_min) * 0.15

# =============================
# BUILD UI
# =============================
def rebuild_scene():
    global cars, leaderboard_bg, leaderboard_text, driver_codes

    driver_codes = {
        num: session.get_driver(num)["Abbreviation"]
        for num in driver_numbers
    }

    # Create cars
    for num in driver_numbers:
        code = driver_codes[num]
        color = fastf1.plotting.get_driver_color(code, session=session)

        cars[num], = ax.plot(
            [],
            [],
            marker="o",
            markersize=6,
            linestyle="",
            color=color,
            zorder=5
        )

    # Leaderboard position
    x_offset = x_max + (leaderboard_space * 0.1)
    box_width = leaderboard_space * 0.8
    box_height = row_height * 0.8

    for i, num in enumerate(driver_numbers):

        y_pos = (y_max - header_offset) - i * row_height

        code = driver_codes[num]
        color = fastf1.plotting.get_driver_color(code, session=session)

        rect = ax.add_patch(
            plt.Rectangle(
                (x_offset, y_pos),
                box_width,
                box_height,
                facecolor=color,
                edgecolor="none",
                alpha=0.9,
                zorder=6
            )
        )

        txt = ax.text(
            x_offset + box_width * 0.05,
            y_pos + box_height / 2,
            "",
            fontsize=10,
            va="center",
            color="white",
            zorder=7
        )

        leaderboard_bg[num] = rect
        leaderboard_text[num] = txt


rebuild_scene()

# =============================
# UPDATE FUNCTION
# =============================
def update(_):
    global frame_idx, paused

    if paused:
        return []

    artists = []

    for pos, num in enumerate(driver_numbers):

        tel = telemetry[num]

        if frame_idx >= len(tel):
            continue

        x = tel.loc[frame_idx, "X"]
        y = tel.loc[frame_idx, "Y"]

        cars[num].set_data([x], [y])
        update_car_drs_style(cars[num], tel, frame_idx)

        artists.append(cars[num])

        # Detect DRS for leaderboard
        drs_active = False
        if "DRS" in tel.columns:
            drs_active = tel.loc[frame_idx, "DRS"] == 2

        drs_label = "DRS  " if drs_active else ""

        code = driver_codes[num]

        leaderboard_text[num].set_text(
            f"{drs_label}{pos+1:>2}  {code}"
        )

        leaderboard_text[num].set_fontweight("bold" if drs_active else "normal")

        artists.append(leaderboard_bg[num])
        artists.append(leaderboard_text[num])

    frame_idx += speed_multiplier

    if frame_idx >= max_frames:
        paused = True

    return artists


# =============================
# KEYBOARD CONTROLS
# =============================
def on_key(event):
    global paused, speed_multiplier

    key = event.key.lower()

    if key == " ":
        paused = not paused

    elif event.key == "up":
        speed_multiplier *= 2

    elif event.key == "down":
        speed_multiplier = max(1, speed_multiplier // 2)

    elif key == "1":
        speed_multiplier = 1


fig.canvas.mpl_connect("key_press_event", on_key)

# =============================
# ANIMATION
# =============================
ani = FuncAnimation(
    fig,
    update,
    interval=20,
    blit=False,
    cache_frame_data=False
)

plt.show()
