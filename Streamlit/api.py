from fastapi import FastAPI
import requests
from functools import lru_cache

app = FastAPI(
    title="F1 Analytics API",
    description="Custom API for F1 Standings & Data",
    version="1.0"
)

# -------------------- ROOT --------------------

@app.get("/")
def root():
    return {"message": "🏎️ F1 API is running 🚀"}


# -------------------- SAFE FETCH --------------------

def fetch_json(url):
    try:
        response = requests.get(url, timeout=10)

        if response.status_code != 200:
            return None

        try:
            return response.json()
        except:
            return None

    except Exception:
        return None


# -------------------- CACHE (performance boost) --------------------

@lru_cache(maxsize=32)
def get_data(url):
    return fetch_json(url)


# -------------------- DRIVER STANDINGS --------------------

@app.get("/standings/drivers/{year}")
def get_driver_standings(year: int):

    url = f"https://api.jolpi.ca/ergast/f1/{year}/driverStandings.json"
    data = get_data(url)

    if not data:
        return {"error": "Failed to fetch driver standings"}

    try:
        standings_list = data.get('MRData', {}) \
                              .get('StandingsTable', {}) \
                              .get('StandingsLists', [])

        if not standings_list:
            if year <= 2021:
                return {"error": f"No driver standings available for {year}"}

        standings = standings_list[0]['DriverStandings']

        # Clean response
        result = []
        for d in standings:
            result.append({
                "position": int(d["position"]),
                "driver": f"{d['Driver']['givenName']} {d['Driver']['familyName']}",
                "team": d["Constructors"][0]["name"],
                "points": int(d["points"]),
                "wins": int(d["wins"])
            })

        return {"data": result}

    except Exception as e:
        return {"error": str(e)}


# -------------------- CONSTRUCTOR STANDINGS --------------------

@app.get("/standings/constructors/{year}")
def get_constructor_standings(year: int):

    url = f"https://api.jolpi.ca/ergast.com/api/f1/{year}/constructorStandings.json"
    data = get_data(url)

    if not data:
        if year <= 2021:
          return {"error": "Failed to fetch constructor standings"}

    try:
        standings_list = data.get('MRData', {}) \
                              .get('StandingsTable', {}) \
                              .get('StandingsLists', [])

        if not standings_list:
            return {"error": f"No constructor standings available for {year}"}

        standings = standings_list[0]['ConstructorStandings']

        # Clean response
        result = []
        for d in standings:
            result.append({
                "position": int(d["position"]),
                "team": d["Constructor"]["name"],
                "points": int(d["points"]),
                "wins": int(d["wins"])
            })

        return {"data": result}

    except Exception as e:
        return {"error": str(e)}


# -------------------- HEALTH CHECK --------------------

@app.get("/health")
def health():
    return {"status": "OK"}