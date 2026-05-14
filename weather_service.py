"""
EV RouteIQ — Weather Service (Multi-API)
Primary  : Open-Meteo (FREE forever, no API key needed)
Secondary: WeatherAPI.com (key: c5df2b2b72c7453099c35832261405 — trial till May 21)
Fallback : Demo city presets → Default
"""

import requests
import os

# ── API KEYS (set as environment variables — never hardcode keys) ──────
# Set these before running:  set WEATHERAPI_KEY=your_key_here
#                            set OPENWEATHER_API_KEY=your_key_here
WEATHERAPI_KEY = os.environ.get("WEATHERAPI_KEY", "")
OWM_KEY        = os.environ.get("OPENWEATHER_API_KEY", "")


WEATHERAPI_URL = "http://api.weatherapi.com/v1/current.json"
OWM_URL        = "http://api.openweathermap.org/data/2.5/weather"

# WeatherAPI condition codes → our internal condition keys
WEATHERAPI_CONDITION_MAP = {
    1000: "clear",          # Sunny / Clear
    1003: "clouds",         # Partly cloudy
    1006: "clouds",         # Cloudy
    1009: "clouds",         # Overcast
    1030: "mist",           # Mist
    1063: "drizzle",        # Patchy rain possible
    1066: "snow",           # Patchy snow possible
    1069: "drizzle",        # Patchy sleet possible
    1072: "drizzle",        # Patchy freezing drizzle
    1087: "thunderstorm",   # Thundery outbreaks
    1114: "snow",           # Blowing snow
    1117: "snow",           # Blizzard
    1135: "fog",            # Fog
    1147: "fog",            # Freezing fog
    1150: "drizzle",        # Patchy light drizzle
    1153: "drizzle",        # Light drizzle
    1168: "drizzle",        # Freezing drizzle
    1171: "drizzle",        # Heavy freezing drizzle
    1180: "rain",           # Patchy light rain
    1183: "rain",           # Light rain
    1186: "rain",           # Moderate rain at times
    1189: "rain",           # Moderate rain
    1192: "heavy_rain",     # Heavy rain at times
    1195: "heavy_rain",     # Heavy rain
    1198: "rain",           # Light freezing rain
    1201: "heavy_rain",     # Moderate/heavy freezing rain
    1204: "drizzle",        # Light sleet
    1207: "rain",           # Moderate/heavy sleet
    1210: "snow",           # Patchy light snow
    1213: "snow",           # Light snow
    1216: "snow",           # Patchy moderate snow
    1219: "snow",           # Moderate snow
    1222: "snow",           # Patchy heavy snow
    1225: "snow",           # Heavy snow
    1237: "snow",           # Ice pellets
    1240: "rain",           # Light rain shower
    1243: "heavy_rain",     # Moderate/heavy rain shower
    1246: "heavy_rain",     # Torrential rain shower
    1249: "drizzle",        # Light sleet showers
    1252: "rain",           # Moderate/heavy sleet showers
    1255: "snow",           # Light snow showers
    1258: "snow",           # Moderate/heavy snow showers
    1261: "snow",           # Light showers of ice pellets
    1264: "snow",           # Moderate/heavy showers of ice pellets
    1273: "thunderstorm",   # Patchy light rain with thunder
    1276: "thunderstorm",   # Moderate/heavy rain with thunder
    1279: "thunderstorm",   # Patchy light snow with thunder
    1282: "thunderstorm",   # Moderate/heavy snow with thunder
}

# OpenWeatherMap condition ID ranges → our internal keys
OWM_CONDITION_MAP = {
    range(200, 300): "thunderstorm",
    range(300, 321): "drizzle",
    range(500, 505): "rain",
    range(511, 512): "ice_storm",
    range(520, 532): "heavy_rain",
    range(600, 623): "snow",
    range(701, 702): "mist",
    range(711, 712): "haze",
    range(721, 722): "haze",
    range(731, 732): "dust",
    range(741, 742): "fog",
    range(751, 752): "sand",
    range(761, 762): "dust",
    range(771, 772): "thunderstorm",
    range(781, 782): "thunderstorm",
    range(800, 801): "clear",
    range(801, 805): "clouds",
}

ICON_MAP = {
    "clear": "☀️", "clouds": "☁️", "drizzle": "🌦️",
    "rain": "🌧️", "heavy_rain": "🌧️", "thunderstorm": "⛈️",
    "snow": "❄️", "mist": "🌫️", "fog": "🌫️",
    "haze": "🌫️", "dust": "💨", "sand": "💨",
    "ice_storm": "🌨️", "ice": "🧊",
}

DEMO_CITIES = {
    "mysuru":     {"temp": 26, "humidity": 60, "condition": "clear",    "desc": "Clear Sky",     "icon": "☀️"},
    "mysore":     {"temp": 26, "humidity": 60, "condition": "clear",    "desc": "Clear Sky",     "icon": "☀️"},
    "bangalore":  {"temp": 25, "humidity": 65, "condition": "clouds",   "desc": "Partly Cloudy", "icon": "⛅"},
    "bengaluru":  {"temp": 25, "humidity": 65, "condition": "clouds",   "desc": "Partly Cloudy", "icon": "⛅"},
    "mumbai":     {"temp": 30, "humidity": 80, "condition": "rain",     "desc": "Light Rain",    "icon": "🌧️"},
    "delhi":      {"temp": 38, "humidity": 35, "condition": "haze",     "desc": "Haze",          "icon": "🌫️"},
    "hyderabad":  {"temp": 29, "humidity": 60, "condition": "clear",    "desc": "Clear Sky",     "icon": "☀️"},
    "chennai":    {"temp": 32, "humidity": 78, "condition": "drizzle",  "desc": "Drizzle",       "icon": "🌦️"},
    "kolkata":    {"temp": 34, "humidity": 75, "condition": "rain",     "desc": "Moderate Rain", "icon": "🌧️"},
    "pune":       {"temp": 27, "humidity": 58, "condition": "clouds",   "desc": "Overcast",      "icon": "☁️"},
    "mangaluru":  {"temp": 28, "humidity": 80, "condition": "rain",     "desc": "Light Rain",    "icon": "🌧️"},
    "coimbatore": {"temp": 28, "humidity": 65, "condition": "clouds",   "desc": "Partly Cloudy", "icon": "⛅"},
    "jaipur":     {"temp": 35, "humidity": 30, "condition": "clear",    "desc": "Hot & Sunny",   "icon": "☀️"},
    "ahmedabad":  {"temp": 36, "humidity": 35, "condition": "clear",    "desc": "Hot & Sunny",   "icon": "☀️"},
    "kochi":      {"temp": 28, "humidity": 85, "condition": "rain",     "desc": "Coastal Rain",  "icon": "🌧️"},
    "london":     {"temp": 12, "humidity": 80, "condition": "drizzle",  "desc": "Drizzle",       "icon": "🌦️"},
    "new york":   {"temp": 18, "humidity": 55, "condition": "clear",    "desc": "Clear",         "icon": "☀️"},
    "tokyo":      {"temp": 22, "humidity": 68, "condition": "clouds",   "desc": "Cloudy",        "icon": "☁️"},
    "dubai":      {"temp": 42, "humidity": 45, "condition": "clear",    "desc": "Sunny",         "icon": "☀️"},
    "sydney":     {"temp": 20, "humidity": 65, "condition": "clear",    "desc": "Partly Cloudy", "icon": "⛅"},
    "paris":      {"temp": 15, "humidity": 72, "condition": "clouds",   "desc": "Cloudy",        "icon": "☁️"},
    "berlin":     {"temp": 14, "humidity": 68, "condition": "rain",     "desc": "Light Rain",    "icon": "🌧️"},
    "singapore":  {"temp": 30, "humidity": 85, "condition": "rain",     "desc": "Tropical Rain", "icon": "🌧️"},
}


def _owm_id_to_condition(weather_id: int) -> str:
    for id_range, condition in OWM_CONDITION_MAP.items():
        if weather_id in id_range:
            return condition
    return "clear"


# ── WMO Weather Code → condition (Open-Meteo uses WMO codes) ─────────
WMO_CONDITION_MAP = {
    0:  "clear",        # Clear sky
    1:  "clear",        # Mainly clear
    2:  "clouds",       # Partly cloudy
    3:  "clouds",       # Overcast
    45: "fog",          # Fog
    48: "fog",          # Icy fog
    51: "drizzle",      # Light drizzle
    53: "drizzle",      # Moderate drizzle
    55: "drizzle",      # Dense drizzle
    61: "rain",         # Slight rain
    63: "rain",         # Moderate rain
    65: "heavy_rain",   # Heavy rain
    71: "snow",         # Slight snow
    73: "snow",         # Moderate snow
    75: "snow",         # Heavy snow
    77: "snow",         # Snow grains
    80: "rain",         # Slight showers
    81: "rain",         # Moderate showers
    82: "heavy_rain",   # Violent showers
    85: "snow",         # Snow showers
    86: "snow",         # Heavy snow showers
    95: "thunderstorm", # Thunderstorm
    96: "thunderstorm", # Thunderstorm + hail
    99: "thunderstorm", # Thunderstorm + heavy hail
}
WMO_DESC_MAP = {
    0: "Clear Sky", 1: "Mainly Clear", 2: "Partly Cloudy", 3: "Overcast",
    45: "Foggy", 48: "Icy Fog", 51: "Light Drizzle", 53: "Drizzle",
    55: "Heavy Drizzle", 61: "Light Rain", 63: "Moderate Rain", 65: "Heavy Rain",
    71: "Light Snow", 73: "Moderate Snow", 75: "Heavy Snow", 77: "Snow Grains",
    80: "Rain Showers", 81: "Moderate Showers", 82: "Heavy Showers",
    85: "Snow Showers", 86: "Heavy Snow Showers",
    95: "Thunderstorm", 96: "Thunderstorm + Hail", 99: "Severe Thunderstorm",
}


def _try_open_meteo(city: str) -> dict | None:
    """
    Open-Meteo: 100% FREE, no API key, no expiry, no rate limits.
    Step 1: geocode city via open-meteo geocoding API
    Step 2: fetch current weather via open-meteo forecast API
    """
    try:
        # Step 1: Geocode — try "city, India" first for better small city matching
        def _geocode(query):
            r = requests.get(
                "https://geocoding-api.open-meteo.com/v1/search",
                params={"name": query, "count": 5, "language": "en", "format": "json"},
                timeout=6
            )
            if r.status_code != 200:
                return None
            return r.json().get("results")

        # Try with India bias first (helps find small Indian towns)
        results = _geocode(city + ", India")
        # Filter to India results first
        india_results = [r for r in (results or []) if r.get("country_code") == "IN"]
        if india_results:
            loc = india_results[0]
        else:
            # Try bare city name
            results2 = _geocode(city)
            if not results2:
                return None
            loc = results2[0]
        lat, lon = loc["latitude"], loc["longitude"]
        city_name = loc.get("name", city.title())
        country   = loc.get("country_code", "--")

        # Step 2: Fetch weather
        wx = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": lat, "longitude": lon,
                "current": "temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code",
                "wind_speed_unit": "kmh",
                "timezone": "auto"
            },
            timeout=6
        )
        if wx.status_code != 200:
            return None
        cur  = wx.json()["current"]
        code = int(cur["weather_code"])
        cond = WMO_CONDITION_MAP.get(code, "clear")
        desc = WMO_DESC_MAP.get(code, "Clear Sky")
        return {
            "city":          city_name,
            "country":       country,
            "temperature_c": round(cur["temperature_2m"], 1),
            "feels_like_c":  round(cur["temperature_2m"] - 1.5, 1),
            "humidity_pct":  cur["relative_humidity_2m"],
            "wind_kmh":      round(cur["wind_speed_10m"], 1),
            "condition":     cond,
            "description":   desc,
            "icon":          ICON_MAP.get(cond, "🌤️"),
            "source":        "live_openmeteo",
            "success":       True,
        }
    except Exception as e:
        print(f"[Open-Meteo] Error: {e}")
        return None


def _try_weatherapi(city: str) -> dict | None:
    """Try WeatherAPI.com — returns result dict or None on failure."""
    if not WEATHERAPI_KEY:
        return None
    try:
        resp = requests.get(
            WEATHERAPI_URL,
            params={"key": WEATHERAPI_KEY, "q": city, "aqi": "no"},
            timeout=6
        )
        if resp.status_code == 200:
            d = resp.json()
            loc = d["location"]
            cur = d["current"]
            code = cur["condition"]["code"]
            condition = WEATHERAPI_CONDITION_MAP.get(code, "clear")
            return {
                "city":           loc["name"],
                "country":        loc["country"],
                "temperature_c":  round(cur["temp_c"], 1),
                "feels_like_c":   round(cur["feelslike_c"], 1),
                "humidity_pct":   cur["humidity"],
                "wind_kmh":       round(cur["wind_kph"], 1),
                "condition":      condition,
                "description":    cur["condition"]["text"],
                "icon":           ICON_MAP.get(condition, "🌤️"),
                "source":         "live_weatherapi",
                "success":        True,
            }
        print(f"[WeatherAPI] Status {resp.status_code}: {resp.text[:100]}")
        return None
    except Exception as e:
        print(f"[WeatherAPI] Error: {e}")
        return None


def _try_owm(city: str) -> dict | None:
    """Try OpenWeatherMap — returns result dict or None on failure."""
    if not OWM_KEY:
        return None
    try:
        resp = requests.get(
            OWM_URL,
            params={"q": city, "appid": OWM_KEY, "units": "metric"},
            timeout=6
        )
        if resp.status_code == 200:
            d = resp.json()
            weather_id = d["weather"][0]["id"]
            condition  = _owm_id_to_condition(weather_id)
            return {
                "city":           d["name"],
                "country":        d["sys"]["country"],
                "temperature_c":  round(d["main"]["temp"], 1),
                "feels_like_c":   round(d["main"]["feels_like"], 1),
                "humidity_pct":   d["main"]["humidity"],
                "wind_kmh":       round(d["wind"]["speed"] * 3.6, 1),
                "condition":      condition,
                "description":    d["weather"][0]["description"].title(),
                "icon":           ICON_MAP.get(condition, "🌤️"),
                "source":         "live_owm",
                "success":        True,
            }
        print(f"[OWM] Status {resp.status_code}: {resp.text[:100]}")
        return None
    except Exception as e:
        print(f"[OWM] Error: {e}")
        return None


def get_weather(city: str) -> dict:
    """
    Fetch weather for a city.
    Priority: Open-Meteo (free/forever) → WeatherAPI.com → Demo → Default
    """
    city_lower = city.strip().lower()

    # 1️⃣ Open-Meteo — FREE forever, no API key
    result = _try_open_meteo(city)
    if result:
        return result

    # 2️⃣ WeatherAPI.com (fallback while trial active)
    result = _try_weatherapi(city)
    if result:
        return result

    # 3️⃣ Demo preset
    if city_lower in DEMO_CITIES:
        d = DEMO_CITIES[city_lower]
        return {
            "city":           city.title(),
            "country":        "IN",
            "temperature_c":  d["temp"],
            "feels_like_c":   d["temp"] - 2,
            "humidity_pct":   d["humidity"],
            "wind_kmh":       12.0,
            "condition":      d["condition"],
            "description":    d["desc"],
            "icon":           d["icon"],
            "source":         "demo",
            "success":        True,
        }

    # 4️⃣ Generic default
    return {
        "city":           city.title(),
        "country":        "--",
        "temperature_c":  22.0,
        "feels_like_c":   21.0,
        "humidity_pct":   55,
        "wind_kmh":       10.0,
        "condition":      "clear",
        "description":    "Clear Sky (Default)",
        "icon":           "☀️",
        "source":         "default",
        "success":        False,
    }
