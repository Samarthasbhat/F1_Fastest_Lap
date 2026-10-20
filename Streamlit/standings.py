import streamlit as st
import requests

# -------------------- SAFE FETCH --------------------

def safe_int(value):
    try:
        return int(value)
    except:
        return 0


def fetch_json(url):
    try:
        res = requests.get(url, timeout=10)

        if res.status_code != 200:
            return None

        return res.json()

    except Exception:
        return None


# -------------------- DRIVER STANDINGS --------------------

@st.cache_data
def get_driver_standings(year):

    # 🔥 PRIMARY: Jolpica API
    url = f"https://api.jolpi.ca/ergast/f1/{year}/driverStandings.json"
    data = fetch_json(url)

    # 🔁 FALLBACK: Ergast
    if not data:
        url = f"https://ergast.com/api/f1/{year}/driverStandings.json"
        data = fetch_json(url)

    if not data:
        return None

    try:
        return data['MRData']['StandingsTable']['StandingsLists'][0]['DriverStandings']
    except Exception:
        return None


# -------------------- CONSTRUCTOR STANDINGS --------------------

@st.cache_data
def get_constructor_standings(year):

    # 🔥 PRIMARY: Jolpica API
    url = f"https://api.jolpi.ca/ergast/f1/{year}/constructorStandings.json"
    data = fetch_json(url)

    # 🔁 FALLBACK: Ergast
    if not data:
        url = f"https://ergast.com/api/f1/{year}/constructorStandings.json"
        data = fetch_json(url)

    if not data:
        return None

    try:
        return data['MRData']['StandingsTable']['StandingsLists'][0]['ConstructorStandings']
    except Exception:
        return None


# -------------------- UI --------------------

def show_standings(year):


    standings_type = st.radio(
        "📊 Select Standings Type",
        ["Driver Standings", "Constructor Standings"],
        horizontal=True
    )



    # ---------------- DRIVER ----------------
    if standings_type == "Driver Standings":
        if year <= 2021:
            st.info("Standings data for 2021 may be unavailable or incomplete.")
            return
        data = get_driver_standings(year)


        if not data:
            st.warning(f"⚠️ No driver standings available for {year}")
            return

        table = []
        for d in data:
            driver = d['Driver']
            constructor = d['Constructors'][0]

            table.append({
                "Pos": "🥇" if d['position'] == "1" else "🥈" if d['position'] == "2" else "🥉" if d['position'] == "3" else d['position'],
                "Driver": f"{driver['givenName']} {driver['familyName']}",
                "Team": constructor['name'],
                "Points": safe_int(d['points']),
                "Wins": safe_int(d['wins'])
            })

        st.dataframe(table, use_container_width=True)

    # ---------------- CONSTRUCTOR ----------------
    else:
        if year <= 2021:
            st.info("Standings data for 2021 may be unavailable or incomplete.")
            return
        data = get_constructor_standings(year)

        if not data:
            st.warning(f"⚠️ No constructor standings available for {year}")
            return

        table = []
        for d in data:
            constructor = d['Constructor']

            table.append({
                "Pos": "🥇" if d['position'] == "1" else "🥈" if d['position'] == "2" else "🥉" if d['position'] == "3" else d['position'],
                "Team": constructor['name'],
                "Points": safe_int(d['points']),
                "Wins": safe_int(d['wins'])
            })
        table = sorted(table, key=lambda x: x["Points"], reverse=True)
        st.dataframe(table, use_container_width=True)