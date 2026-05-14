import sys
sys.stdout.reconfigure(encoding='utf-8')
from weather_service import get_weather, _try_open_meteo

cities = ['Hyderabad', 'Chennai', 'Delhi', 'London']
print("Testing Open-Meteo directly:")
for city in cities:
    w = _try_open_meteo(city)
    if w:
        print(f"  {city}: {w['temperature_c']}C | {w['description']} | {w['source']}")
    else:
        print(f"  {city}: FAILED")

print()
print("Testing full chain (get_weather):")
for city in cities:
    w = get_weather(city)
    src = w.get('source','?')
    tag = 'FREE-FOREVER' if 'openmeteo' in src else ('WEATHERAPI' if 'weatherapi' in src else src.upper())
    print(f"  {city:<12} | {tag:<14} | {w['temperature_c']}C | {w['humidity_pct']}% | {w['description']}")
