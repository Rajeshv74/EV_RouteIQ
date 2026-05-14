"""
EV RouteIQ — Comprehensive Test Suite
Covers: Unit, Integration, Functional, API tests
Run: pytest tests/test_project.py -v
"""
import sys, os, io, json, pytest, requests
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

BASE = "http://127.0.0.1:5001"

# ══════════════════════════════════════════════════════
# UNIT TESTS — Physics Engine
# ══════════════════════════════════════════════════════
from physics_engine import (
    calculate_adjusted_crr, calculate_ev_energy,
    calculate_road_quality_score, get_road_surface_info,
    get_recommended_speed, compare_routes, BASE_CRR
)

class TestPhysicsEngine:
    def test_base_crr_dry_smooth(self):
        """Best surface has lowest Crr"""
        assert BASE_CRR['dry_asphalt_smooth'] == 0.0105

    def test_base_crr_wet_mud_worst(self):
        """Worst surface has highest Crr"""
        assert BASE_CRR['wet_mud'] == 0.2000

    def test_adjusted_crr_speed_increases_with_speed(self):
        """Higher speed → higher adjusted Crr"""
        low  = calculate_adjusted_crr('dry_asphalt_smooth', speed_kmh=60)
        high = calculate_adjusted_crr('dry_asphalt_smooth', speed_kmh=120)
        assert high['adjusted_crr'] > low['adjusted_crr']

    def test_adjusted_crr_cold_temp_increases(self):
        """Cold temperature → higher Crr (rubber stiffness)"""
        warm = calculate_adjusted_crr('dry_asphalt_smooth', temperature_c=20)
        cold = calculate_adjusted_crr('dry_asphalt_smooth', temperature_c=0)
        assert cold['adjusted_crr'] > warm['adjusted_crr']

    def test_adjusted_crr_low_pressure_increases(self):
        """Under-inflated tyre → higher Crr"""
        ok   = calculate_adjusted_crr('dry_asphalt_smooth', tire_pressure_bar=2.3)
        flat = calculate_adjusted_crr('dry_asphalt_smooth', tire_pressure_bar=1.5)
        assert flat['adjusted_crr'] > ok['adjusted_crr']

    def test_adjusted_crr_rain_multiplier(self):
        """Rain weather → higher Crr than clear"""
        clear = calculate_adjusted_crr('dry_asphalt_smooth', weather_condition='clear')
        rain  = calculate_adjusted_crr('dry_asphalt_smooth', weather_condition='rain')
        assert rain['adjusted_crr'] > clear['adjusted_crr']

    def test_ev_energy_positive(self):
        """Energy consumption must be positive"""
        crr  = calculate_adjusted_crr('dry_asphalt_smooth')
        e    = calculate_ev_energy(crr['adjusted_crr'], 1500, 100, 60)
        assert e['energy_kwh'] > 0

    def test_ev_energy_mud_greater_than_asphalt(self):
        """Mud consumes more energy than smooth asphalt"""
        crr_a = calculate_adjusted_crr('dry_asphalt_smooth')['adjusted_crr']
        crr_m = calculate_adjusted_crr('dry_mud')['adjusted_crr']
        e_a   = calculate_ev_energy(crr_a, 1500, 100, 60)['energy_kwh']
        e_m   = calculate_ev_energy(crr_m, 1500, 100, 60)['energy_kwh']
        assert e_m > e_a

    def test_quality_score_best_surface(self):
        """Smooth dry asphalt → score near 100"""
        assert calculate_road_quality_score('dry_asphalt_smooth') >= 95

    def test_quality_score_wet_mud_worst(self):
        """Wet mud → score near 0"""
        assert calculate_road_quality_score('wet_mud') == 0

    def test_quality_score_range(self):
        """All surfaces score between 0 and 100"""
        for s in BASE_CRR:
            sc = calculate_road_quality_score(s)
            assert 0 <= sc <= 100, f"{s} score {sc} out of range"

    def test_road_info_safety_levels(self):
        """Safety must be High, Medium, or Low"""
        for s in BASE_CRR:
            info = get_road_surface_info(s)
            assert info['safety'] in ('High', 'Medium', 'Low'), f"{s} has invalid safety"

    def test_recommended_speed_ice_low(self):
        """Ice surface → very low recommended speed"""
        assert get_recommended_speed('ice') <= 20

    def test_recommended_speed_dry_smooth_high(self):
        """Dry smooth asphalt → high recommended speed"""
        assert get_recommended_speed('dry_asphalt_smooth') >= 100

    def test_compare_routes_winner(self):
        """Compare routes returns a valid winner"""
        route_a = [('dry_asphalt_smooth', 50)]
        route_b = [('wet_mud', 50)]
        result  = compare_routes(route_a, route_b, 1500, 72, 90, 60, 20, 2.3, 'clear')
        assert result['winner'] in ('A', 'B')
        assert result['winner'] == 'A'  # smooth asphalt must win over wet mud

    def test_compare_routes_energy_saved_positive(self):
        """Energy saved must be non-negative"""
        route_a = [('dry_asphalt_smooth', 50)]
        route_b = [('dry_gravel', 50)]
        result  = compare_routes(route_a, route_b, 1500, 72)
        assert result['energy_saved_kwh'] >= 0


# ══════════════════════════════════════════════════════
# UNIT TESTS — EV Database
# ══════════════════════════════════════════════════════
from ev_database import get_vehicle, list_vehicles

class TestEVDatabase:
    def test_list_vehicles_not_empty(self):
        assert len(list_vehicles()) > 0

    def test_get_vehicle_has_required_keys(self):
        v = get_vehicle('tesla_model3_lr')
        for key in ['id','name','battery_kwh','mass_kg','range_km']:
            assert key in v, f"Missing key: {key}"

    def test_battery_kwh_positive(self):
        for v in list_vehicles():
            assert v['battery_kwh'] > 0

    def test_mass_kg_realistic(self):
        for v in list_vehicles():
            assert 800 < v['mass_kg'] < 4000, f"{v['name']} mass unrealistic"


# ══════════════════════════════════════════════════════
# INTEGRATION / API TESTS — Flask Endpoints
# ══════════════════════════════════════════════════════
def _server_up():
    try:
        return requests.get(f"{BASE}/health", timeout=3).status_code == 200
    except:
        return False

@pytest.mark.skipif(not _server_up(), reason="Server not running on port 5001")
class TestAPIEndpoints:

    def _make_image_bytes(self, color=(80, 80, 80)):
        from PIL import Image
        img = Image.new('RGB', (224, 224), color)
        buf = io.BytesIO()
        img.save(buf, format='JPEG')
        buf.seek(0)
        return buf

    def test_health_ok(self):
        r = requests.get(f"{BASE}/health")
        d = r.json()
        assert r.status_code == 200
        assert d['status'] == 'healthy'

    def test_health_model_loaded(self):
        d = requests.get(f"{BASE}/health").json()
        assert d['model_loaded'] is True

    def test_vehicles_endpoint(self):
        d = requests.get(f"{BASE}/vehicles").json()
        assert d['success'] is True
        assert d['count'] > 0

    def test_surfaces_endpoint(self):
        d = requests.get(f"{BASE}/surfaces").json()
        assert d['success'] is True
        assert d['count'] == 27

    def test_predict_returns_success(self):
        r = requests.post(f"{BASE}/predict",
            data={'vehicle_id':'tesla_model3_lr','speed_kmh':60,
                  'temperature_c':20,'tire_pressure_bar':2.3,
                  'soc_percent':90,'distance_km':100,'weather_condition':'clear'},
            files={'image':('road.jpg', self._make_image_bytes(), 'image/jpeg')},
            timeout=30)
        d = r.json()
        assert d['success'] is True
        assert 'prediction' in d
        assert 'energy' in d
        assert 'crr' in d

    def test_predict_confidence_in_range(self):
        r = requests.post(f"{BASE}/predict",
            data={'vehicle_id':'tesla_model3_lr'},
            files={'image':('road.jpg', self._make_image_bytes(), 'image/jpeg')},
            timeout=30)
        d = r.json()
        assert 0 <= d['prediction']['confidence'] <= 100

    def test_predict_class_valid(self):
        r = requests.post(f"{BASE}/predict",
            data={'vehicle_id':'tesla_model3_lr'},
            files={'image':('road.jpg', self._make_image_bytes(), 'image/jpeg')},
            timeout=30)
        d = r.json()
        valid = list(BASE_CRR.keys())
        assert d['prediction']['class'] in valid

    def test_compare_route_a_wins_smooth_vs_mud(self):
        body = {
            'vehicle_id': 'tesla_model3_lr',
            'soc_percent': 90, 'speed_kmh': 60,
            'temperature_c': 20, 'tire_pressure_bar': 2.3,
            'weather_condition': 'clear',
            'route_a': [{'surface':'dry_asphalt_smooth','distance_km':50}],
            'route_b': [{'surface':'wet_mud','distance_km':50}]
        }
        d = requests.post(f"{BASE}/compare",
            json=body, timeout=20).json()
        assert d['success'] is True
        assert d['comparison']['winner'] == 'A'

    def test_geocode_bengaluru(self):
        d = requests.get(f"{BASE}/geocode?city=Bengaluru", timeout=10).json()
        assert d['success'] is True
        assert 12.0 < d['lat'] < 14.0
        assert 77.0 < d['lon'] < 78.5

    def test_geocode_hyderabad(self):
        d = requests.get(f"{BASE}/geocode?city=Hyderabad", timeout=10).json()
        assert d['success'] is True
        assert d['country'] == 'India'

    def test_geocode_empty_city_returns_error(self):
        d = requests.get(f"{BASE}/geocode?city=", timeout=10).json()
        assert d['success'] is False

    def test_heatmap_add_valid(self):
        r = requests.post(f"{BASE}/heatmap/add",
            data={'location':'Bengaluru','lat':12.9716,'lon':77.5946},
            files={'image':('road.jpg', self._make_image_bytes(), 'image/jpeg')},
            timeout=30)
        d = r.json()
        assert d['success'] is True
        assert 'entry' in d
        e = d['entry']
        assert e['lat'] == 12.9716
        assert e['lon'] == 77.5946

    def test_heatmap_data_endpoint(self):
        d = requests.get(f"{BASE}/heatmap/data").json()
        assert d['success'] is True
        assert 'readings' in d

    def test_weather_endpoint(self):
        d = requests.get(f"{BASE}/weather?city=Hyderabad", timeout=10).json()
        assert 'condition' in d or 'error' in d  # either live or error is fine

    def test_predict_no_image_returns_error(self):
        r = requests.post(f"{BASE}/predict",
            data={'vehicle_id':'tesla_model3_lr'}, timeout=10)
        d = r.json()
        assert d['success'] is False

    def test_compare_missing_routes_returns_error(self):
        r = requests.post(f"{BASE}/compare",
            json={'vehicle_id':'tesla_model3_lr'}, timeout=10)
        d = r.json()
        assert d['success'] is False


# ══════════════════════════════════════════════════════
# FUNCTIONAL TESTS — Crr Physics correctness
# ══════════════════════════════════════════════════════
class TestCrrPhysicsCorrectness:
    """Verify Crr values match published automotive engineering standards."""

    def test_dry_asphalt_smooth_within_sae_range(self):
        """SAE J2452: smooth asphalt Crr ≈ 0.010–0.012"""
        crr = BASE_CRR['dry_asphalt_smooth']
        assert 0.009 <= crr <= 0.013

    def test_ice_crr_lower_than_asphalt(self):
        """Ice has lower Crr than mud (less deformation, more slip)"""
        assert BASE_CRR['ice'] < BASE_CRR['dry_mud']

    def test_wet_surfaces_higher_than_dry(self):
        """Wet versions of same surface have higher Crr than dry"""
        pairs = [
            ('dry_asphalt_smooth', 'wet_asphalt_smooth'),
            ('dry_concrete_smooth', 'wet_concrete_smooth'),
            ('dry_gravel', 'wet_gravel'),
        ]
        for dry, wet in pairs:
            assert BASE_CRR[wet] >= BASE_CRR[dry], f"{wet} should be >= {dry}"

    def test_energy_formula_units(self):
        """1 kWh = 3,600,000 J — verify conversion"""
        crr  = calculate_adjusted_crr('dry_asphalt_smooth')
        e    = calculate_ev_energy(crr['adjusted_crr'], 1500, 1.0, 60)
        # 1 km at 60 km/h: energy must be between 0.05 and 0.5 kWh
        assert 0.05 <= e['energy_kwh'] <= 0.5


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
