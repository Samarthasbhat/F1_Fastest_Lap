def get_telemetry(session, drivers, mode="FASTEST"):

    telemetry = {}

    if mode == "FASTEST":

        for drv in drivers:
            laps = session.laps.pick_drivers(drv)
            if laps.empty:
                continue

            lap = laps.pick_fastest()
            if lap is None:
                continue

            tel = lap.get_telemetry().reset_index(drop=True)
            telemetry[drv] = tel

    elif mode == "RACE":

        for drv in drivers:
            laps = session.laps.pick_drivers(drv)
            if laps.empty:
                continue

            tel = laps.get_telemetry().reset_index(drop=True)
            telemetry[drv] = tel

    else:
        raise ValueError("mode must be 'FASTEST' or 'RACE'")

    return telemetry, None
