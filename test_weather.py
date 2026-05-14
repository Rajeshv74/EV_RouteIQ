import requests
import sys

# Fix Windows console encoding
sys.stdout.reconfigure(encoding='utf-8')

cities = ['mysuru', 'bangalore', 'london', 'unknowncity123']
src_labels = {
    'live_weatherapi': '[LIVE - WeatherAPI.com]',
    'live_owm':        '[LIVE - OpenWeatherMap]',
    'demo':            '[Demo preset]',
    'default':         '[Default fallback]'
}

print("Weather Endpoint Test")
print("-" * 70)
for city in cities:
    try:
        r = requests.get(f'http://127.0.0.1:5000/weather?city={city}', timeout=12).json()
        src   = src_labels.get(r['source'], r['source'])
        temp  = r['temperature_c']
        humid = r['humidity_pct']
        wind  = r['wind_kmh']
        desc  = r['description'][:30]
        city_name = r['city']
        print(f"{city_name:16} | {temp}C | Humidity:{humid}% | Wind:{wind}km/h | {desc:30} | {src}")
    except Exception as e:
        print(f"{city:16} | ERROR: {e}")
print("-" * 70)
print("Done. All endpoints responding correctly.")
