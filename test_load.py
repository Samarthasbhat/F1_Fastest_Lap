import sys, logging
import fastf1

print("Python:", sys.version)
print("FastF1:", fastf1.__version__)

logging.getLogger("fastf1").setLevel(logging.DEBUG)

for year, gp in [(2023, "Abu Dhabi Grand Prix"), (2024, "Abu Dhabi Grand Prix")]:
    print("-----", year, gp)
    try:
        s = fastf1.get_session(year, gp, "R")
        s.load(telemetry=False, weather=False, messages=False)
        print("Drivers:", len(s.drivers))
        print("Laps:", len(s.laps))
    except Exception as e:
        print("FAILED:", type(e).__name__, e)