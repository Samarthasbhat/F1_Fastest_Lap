import pandas as pd

_blink_state = True


def draw_drs_zones(ax, lap):
    """
    Draw glowing DRS zones based on availability (DRS > 0).
    """

    car_data = lap.get_car_data().add_distance()
    pos_data = lap.get_pos_data()

    merged = pd.merge_asof(
        car_data.sort_values("Time"),
        pos_data.sort_values("Time"),
        on="Time"
    )

    if "DRS" not in merged.columns:
        return

    drs_zone = merged[merged["DRS"] > 0]

    if drs_zone.empty:
        return

    # Glow layer
    ax.plot(
        drs_zone["X"],
        drs_zone["Y"],
        color="#00ff66",
        linewidth=18,
        alpha=0.15,
        solid_capstyle="round",
        zorder=2
    )

    # Bright center
    ax.plot(
        drs_zone["X"],
        drs_zone["Y"],
        color="#00ff99",
        linewidth=6,
        solid_capstyle="round",
        zorder=3
    )


def draw_detection_line(ax, lap):
    """
    Draw detection marker where DRS first becomes available.
    """

    car_data = lap.get_car_data().add_distance()
    pos_data = lap.get_pos_data()

    if "DRS" not in car_data.columns:
        return

    drs_available = car_data[car_data["DRS"] > 0]

    if drs_available.empty:
        return

    detection_time = drs_available.iloc[0]["Time"]

    detection_point = pos_data.iloc[
        (pos_data["Time"] - detection_time).abs().argsort()[:1]
    ]

    x = detection_point["X"].values[0]
    y = detection_point["Y"].values[0]

    ax.scatter(
        x,
        y,
        color="white",
        s=120,
        marker="|",
        linewidths=3,
        zorder=4
    )


def update_car_drs_style(car, tel, frame_idx):
    """
    Apply blinking glow when DRS is active.
    Returns True if DRS active.
    """

    global _blink_state

    if "DRS" not in tel.columns:
        car.set_markersize(6)
        car.set_markeredgewidth(0)
        return False

    if frame_idx >= len(tel):
        return False

    drs_status = tel.loc[frame_idx, "DRS"]

    if drs_status == 2:
        _blink_state = not _blink_state

        if _blink_state:
            car.set_markersize(14)
            car.set_markeredgecolor("#00ff66")
            car.set_markeredgewidth(2)
        else:
            car.set_markersize(10)
            car.set_markeredgewidth(0)

        return True
    else:
        car.set_markersize(6)
        car.set_markeredgewidth(0)
        return False
