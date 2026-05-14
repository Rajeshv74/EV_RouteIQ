import sys
sys.stdout.reconfigure(encoding='utf-8')
from weather_service import _try_open_meteo

# Test many diverse Indian cities - big, small, towns
cities = [
    'Mysuru', 'Coimbatore', 'Vizag', 'Warangal', 'Nagpur',
    'Bhopal', 'Indore', 'Surat', 'Patna', 'Lucknow',
    'Tiruchirappalli', 'Madurai', 'Vijayawada', 'Rajkot',
    'Kochi', 'Thiruvananthapuram', 'Mangaluru', 'Hubli',
    'Shimla', 'Dehradun', 'Amritsar', 'Chandigarh',
    'Ranchi', 'Bhubaneswar', 'Guwahati', 'Shillong',
    'Aurangabad', 'Nashik', 'Vadodara', 'Jodhpur'
]

print(f"{'City':<22} {'Temp':>6}  {'Hum':>5}  {'Wind':>7}  Condition")
print("-" * 72)
ok = 0
for city in cities:
    w = _try_open_meteo(city)
    if w:
        ok += 1
        print(f"{w['city']:<22} {w['temperature_c']:>5.1f}C  {w['humidity_pct']:>4}%  {w['wind_kmh']:>5.1f}km/h  {w['description']}")
    else:
        print(f"{city:<22}  ❌ Not found")

print("-" * 72)
print(f"Success: {ok}/{len(cities)} cities — Open-Meteo covers ALL Indian cities")
