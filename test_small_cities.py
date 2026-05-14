import sys
sys.stdout.reconfigure(encoding='utf-8')
from weather_service import _try_open_meteo

# Small Indian towns that are hard to find
small_cities = [
    'Hospet', 'Davangere', 'Tumkur', 'Hassan', 'Bellary',
    'Bidar', 'Raichur', 'Chikkamagaluru', 'Dharwad',
    'Nellore', 'Karimnagar', 'Khammam', 'Nizamabad',
    'Tirunelveli', 'Vellore', 'Salem', 'Erode', 'Thanjavur',
    'Bhilai', 'Raipur', 'Bilaspur', 'Korba',
    'Jamshedpur', 'Bokaro', 'Dhanbad',
    'Siliguri', 'Durgapur', 'Asansol',
    'Aligarh', 'Moradabad', 'Bareilly', 'Saharanpur'
]

ok = 0
fail = []
for city in small_cities:
    w = _try_open_meteo(city)
    if w:
        ok += 1
        print(f"  ✅ {w['city']:<22} {w['temperature_c']}C | {w['description']}")
    else:
        fail.append(city)
        print(f"  ❌ {city}")

print(f"\nResult: {ok}/{len(small_cities)} small cities found")
if fail:
    print("Failed:", fail)
