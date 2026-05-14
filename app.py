"""
EV RouteIQ — Flask Backend
Intelligent Road Surface Energy Optimizer for Electric Vehicles
"""

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import torch
import torch.nn as nn
import torch.nn.functional as F
from torchvision import transforms
import timm
from PIL import Image
import io, base64, os, traceback, json
from pdf_report import generate_report

# In-memory heatmap store {id: {location, surface, crr, quality_score, ts}}
heatmap_db = []

from physics_engine import (
    calculate_adjusted_crr, calculate_ev_energy,
    calculate_remaining_range, calculate_road_quality_score,
    get_road_surface_info, get_recommended_speed, compare_routes
)
from ev_database import get_vehicle, list_vehicles, EV_DATABASE
from weather_service import get_weather

# ── App Setup ────────────────────────────────────────────────
app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}

# ── Class Names (27 classes, alphabetical = ImageFolder order) ─
CLASS_NAMES = [
    'dry_asphalt_severe', 'dry_asphalt_slight', 'dry_asphalt_smooth',
    'dry_concrete_severe', 'dry_concrete_slight', 'dry_concrete_smooth',
    'dry_gravel', 'dry_mud', 'fresh_snow', 'ice', 'melted_snow',
    'water_asphalt_severe', 'water_asphalt_slight', 'water_asphalt_smooth',
    'water_concrete_severe', 'water_concrete_slight', 'water_concrete_smooth',
    'water_gravel', 'water_mud',
    'wet_asphalt_severe', 'wet_asphalt_slight', 'wet_asphalt_smooth',
    'wet_concrete_severe', 'wet_concrete_slight', 'wet_concrete_smooth',
    'wet_gravel', 'wet_mud'
]
NUM_CLASSES = len(CLASS_NAMES)

# ── Model Path ───────────────────────────────────────────────
# Looks for new EfficientNet-B4 model first, falls back to old ResNet50
MODEL_PATH = os.path.join(os.path.dirname(__file__), 'best_model_ev_routeiq.pth')
if not os.path.exists(MODEL_PATH):
    MODEL_PATH = os.path.join(os.path.dirname(__file__), 'best_model_rscd.pth')
    USE_EFFICIENTNET = False
else:
    USE_EFFICIENTNET = True

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model_name = 'EfficientNet-B4' if USE_EFFICIENTNET else 'ResNet50'
print(f"[INFO] Device: {device} | Model: {model_name}")

# ── Model Architecture ───────────────────────────────────────
class EVRouteIQModel(nn.Module):
    """EfficientNet-B4 model for road surface classification."""
    def __init__(self, num_classes=27):
        super().__init__()
        self.backbone = timm.create_model(
            'efficientnet_b4', pretrained=False, num_classes=0, global_pool='avg')
        in_f = self.backbone.num_features
        self.head = nn.Sequential(
            nn.BatchNorm1d(in_f), nn.Dropout(0.4),
            nn.Linear(in_f, 512), nn.SiLU(),
            nn.BatchNorm1d(512),  nn.Dropout(0.3),
            nn.Linear(512, num_classes)
        )
    def forward(self, x):
        return self.head(self.backbone(x))


def create_resnet_model():
    """Fallback ResNet50 model architecture (matches saved weights: Dropout=0.5)."""
    from torchvision import models
    model = models.resnet50(weights=None)
    in_f = model.fc.in_features
    model.fc = nn.Sequential(
        nn.Linear(in_f, 512),
        nn.ReLU(),
        nn.Dropout(0.5),
        nn.Linear(512, NUM_CLASSES)
    )
    return model


def load_model():
    try:
        print(f"[INFO] Loading model from: {MODEL_PATH}")
        if USE_EFFICIENTNET:
            ckpt = torch.load(MODEL_PATH, map_location=device, weights_only=False)
            model = EVRouteIQModel(NUM_CLASSES)
            state = ckpt.get('state_dict', ckpt)
            model.load_state_dict(state)
            img_size = ckpt.get('img_size', 380)
        else:
            state = torch.load(MODEL_PATH, map_location=device, weights_only=True)
            model = create_resnet_model()
            model.load_state_dict(state)
            img_size = 224
        model.to(device)
        model.eval()
        print(f"[OK] Model ready | img_size={img_size}")
        return model, img_size
    except Exception as e:
        print(f"[ERROR] Model load: {e}")
        traceback.print_exc()
        return None, 224


model, IMG_SIZE = load_model()

# Build transform based on img_size
def build_transform(img_size):
    return transforms.Compose([
        transforms.Resize((img_size, img_size)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ])

transform = build_transform(IMG_SIZE)

# ── Helpers ──────────────────────────────────────────────────
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def preprocess_image(image_bytes):
    img = Image.open(io.BytesIO(image_bytes)).convert('RGB')
    return transform(img).unsqueeze(0), img


def run_prediction(image_tensor):
    if model is None:
        raise Exception("Model not loaded")
    with torch.no_grad():
        image_tensor = image_tensor.to(device)
        outputs      = model(image_tensor)
        probs        = F.softmax(outputs, dim=1)[0]
        conf, idx    = torch.max(probs, 0)
        predicted    = CLASS_NAMES[idx.item()]
        all_probs    = {CLASS_NAMES[i]: round(float(probs[i]) * 100, 2)
                        for i in range(NUM_CLASSES) if float(probs[i]) * 100 >= 0.01}
        all_probs    = dict(sorted(all_probs.items(), key=lambda x: x[1], reverse=True))
    return predicted, float(conf) * 100, all_probs


def build_full_result(predicted_class, confidence, all_probs,
                      image_bytes, vehicle_id="tesla_model3_sr",
                      speed_kmh=60.0, temperature_c=20.0,
                      tire_pressure_bar=2.3, weather_condition="clear",
                      soc_percent=100.0, distance_km=100.0):
    """Build the complete prediction response with all physics calculations."""
    vehicle  = get_vehicle(vehicle_id)
    surface  = get_road_surface_info(predicted_class)

    # Adjusted Crr
    crr_data = calculate_adjusted_crr(
        predicted_class, speed_kmh, temperature_c,
        tire_pressure_bar, weather_condition)

    # EV Energy
    energy   = calculate_ev_energy(
        crr_data['adjusted_crr'], vehicle['mass_kg'],
        distance_km, speed_kmh, vehicle.get('regen_efficiency', 0.65))

    # Remaining Range
    range_data = calculate_remaining_range(
        vehicle['battery_kwh'], soc_percent,
        energy['energy_wh_per_km'], temperature_c)

    # Recommended speed & quality
    rec_speed     = get_recommended_speed(predicted_class)
    quality_score = calculate_road_quality_score(predicted_class)

    # Battery consumption %
    battery_used_pct = round((energy['energy_kwh'] / vehicle['battery_kwh']) * 100, 1) \
                       if distance_km > 0 else 0

    image_b64 = base64.b64encode(image_bytes).decode('utf-8')

    return {
        'success': True,
        'prediction': {
            'class': predicted_class,
            'label': predicted_class.replace('_', ' ').title(),
            'confidence': round(confidence, 2),
            'all_probabilities': all_probs,
        },
        'surface': surface,
        'crr': crr_data,
        'energy': energy,
        'range': range_data,
        'vehicle': {
            'id': vehicle['id'], 'name': vehicle['name'],
            'battery_kwh': vehicle['battery_kwh'],
            'mass_kg': vehicle['mass_kg'],
            'rated_range_km': vehicle['range_km'],
            'icon': vehicle['icon'], 'color': vehicle['color'],
        },
        'driving': {
            'speed_kmh': speed_kmh,
            'temperature_c': temperature_c,
            'tire_pressure_bar': tire_pressure_bar,
            'weather': weather_condition,
            'soc_percent': soc_percent,
            'distance_km': distance_km,
            'recommended_speed_kmh': rec_speed,
            'quality_score': quality_score,
            'battery_used_pct': battery_used_pct,
        },
        'image': f"data:image/jpeg;base64,{image_b64}",
    }


# ── Routes ───────────────────────────────────────────────────
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/predict', methods=['POST'])
def predict():
    try:
        if model is None:
            return jsonify({'success': False, 'error': 'Model not loaded'}), 500
        if 'image' not in request.files:
            return jsonify({'success': False, 'error': 'No image provided'}), 400

        file = request.files['image']
        if not file.filename or not allowed_file(file.filename):
            return jsonify({'success': False, 'error': 'Invalid file type'}), 400

        image_bytes   = file.read()
        image_tensor, _ = preprocess_image(image_bytes)
        predicted, conf, all_probs = run_prediction(image_tensor)

        # Get optional params from form
        vehicle_id        = request.form.get('vehicle_id', 'tesla_model3_sr')
        speed_kmh         = float(request.form.get('speed_kmh', 60))
        temperature_c     = float(request.form.get('temperature_c', 20))
        tire_pressure_bar = float(request.form.get('tire_pressure_bar', 2.3))
        weather_condition = request.form.get('weather_condition', 'clear')
        soc_percent       = float(request.form.get('soc_percent', 100))
        distance_km       = float(request.form.get('distance_km', 100))

        result = build_full_result(
            predicted, conf, all_probs, image_bytes,
            vehicle_id, speed_kmh, temperature_c,
            tire_pressure_bar, weather_condition, soc_percent, distance_km)

        return jsonify(result)

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/compare', methods=['POST'])
def compare():
    """Compare energy cost of Route A vs Route B."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No JSON body'}), 400

        vehicle_id  = data.get('vehicle_id', 'tesla_model3_sr')
        vehicle     = get_vehicle(vehicle_id)
        soc_percent = float(data.get('soc_percent', 100))
        speed_kmh   = float(data.get('speed_kmh', 60))
        temp_c      = float(data.get('temperature_c', 20))
        pressure    = float(data.get('tire_pressure_bar', 2.3))
        weather     = data.get('weather_condition', 'clear')

        route_a = [(seg['surface'], float(seg['distance_km']))
                   for seg in data.get('route_a', [])]
        route_b = [(seg['surface'], float(seg['distance_km']))
                   for seg in data.get('route_b', [])]

        if not route_a or not route_b:
            return jsonify({'success': False, 'error': 'Provide route_a and route_b'}), 400

        result = compare_routes(
            route_a, route_b, vehicle['mass_kg'], vehicle['battery_kwh'],
            soc_percent, speed_kmh, temp_c, pressure, weather)

        return jsonify({'success': True, 'comparison': result,
                        'vehicle': vehicle['name']})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/weather', methods=['GET'])
def weather():
    """Fetch live weather for a city."""
    city = request.args.get('city', 'Hyderabad')
    data = get_weather(city)
    return jsonify(data)


@app.route('/vehicles', methods=['GET'])
def vehicles():
    """List all EV vehicles."""
    return jsonify({'success': True, 'vehicles': list_vehicles(),
                    'count': len(list_vehicles())})


@app.route('/surfaces', methods=['GET'])
def surfaces():
    """List all 27 road surface classes with info."""
    from physics_engine import ROAD_INFO, BASE_CRR
    result = []
    for cls in CLASS_NAMES:
        info  = get_road_surface_info(cls)
        result.append(info)
    return jsonify({'success': True, 'surfaces': result, 'count': len(result)})


@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'healthy',
        'model_loaded': model is not None,
        'model_type': 'EfficientNet-B4' if USE_EFFICIENTNET else 'ResNet50',
        'device': str(device),
        'num_classes': NUM_CLASSES,
        'img_size': IMG_SIZE,
        'version': '2.0.0'
    })


@app.route('/report', methods=['POST'])
def report():
    """Generate and download a PDF report from prediction data."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No JSON body'}), 400
        pdf_bytes = generate_report(data)
        from flask import send_file
        buf = io.BytesIO(pdf_bytes)
        buf.seek(0)
        return send_file(buf, mimetype='application/pdf',
                         as_attachment=True,
                         download_name='ev_routeiq_report.pdf')
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/fleet', methods=['POST'])
def fleet():
    """Analyze multiple road images for fleet management."""
    try:
        if model is None:
            return jsonify({'success': False, 'error': 'Model not loaded'}), 500
        files   = request.files.getlist('images')
        if not files:
            return jsonify({'success': False, 'error': 'No images provided'}), 400

        vehicle_id        = request.form.get('vehicle_id', 'tesla_model3_sr')
        speed_kmh         = float(request.form.get('speed_kmh', 60))
        temperature_c     = float(request.form.get('temperature_c', 20))
        tire_pressure_bar = float(request.form.get('tire_pressure_bar', 2.3))
        weather_condition = request.form.get('weather_condition', 'clear')
        distance_km       = float(request.form.get('distance_km', 50))
        vehicle           = get_vehicle(vehicle_id)

        results     = []
        total_energy = 0.0
        safety_counts = {'High': 0, 'Medium': 0, 'Low': 0}

        for f in files[:10]:   # max 10 images
            if not allowed_file(f.filename):
                continue
            img_bytes = f.read()
            tensor, _ = preprocess_image(img_bytes)
            predicted, conf, all_probs = run_prediction(tensor)
            crr_data   = calculate_adjusted_crr(predicted, speed_kmh, temperature_c,
                                                tire_pressure_bar, weather_condition)
            energy_data = calculate_ev_energy(crr_data['adjusted_crr'],
                                              vehicle['mass_kg'], distance_km, speed_kmh)
            surface_info = get_road_surface_info(predicted)
            total_energy += energy_data['energy_kwh']
            safety_counts[surface_info.get('safety', 'Medium')] = \
                safety_counts.get(surface_info.get('safety', 'Medium'), 0) + 1

            results.append({
                'filename'    : f.filename,
                'class'       : predicted,
                'label'       : predicted.replace('_', ' ').title(),
                'confidence'  : round(conf, 2),
                'crr'         : crr_data['adjusted_crr'],
                'energy_kwh'  : energy_data['energy_kwh'],
                'wh_per_km'   : energy_data['energy_wh_per_km'],
                'safety'      : surface_info.get('safety', 'Medium'),
                'quality_score': calculate_road_quality_score(predicted),
            })

        avg_energy = total_energy / len(results) if results else 0
        ideal_energy = calculate_ev_energy(0.010, vehicle['mass_kg'],
                                           distance_km, speed_kmh)['energy_kwh']
        savings_pct = round((1 - ideal_energy / avg_energy) * 100, 1) if avg_energy > 0 else 0

        return jsonify({
            'success'       : True,
            'segments'      : results,
            'total_segments': len(results),
            'total_energy_kwh': round(total_energy, 3),
            'avg_energy_kwh': round(avg_energy, 3),
            'potential_savings_pct': savings_pct,
            'safety_summary': safety_counts,
            'vehicle'       : vehicle['name'],
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/heatmap/add', methods=['POST'])
def heatmap_add():
    """Add a road surface reading to the heatmap database."""
    try:
        if model is None:
            return jsonify({'success': False, 'error': 'Model not loaded'}), 500
        if 'image' not in request.files:
            return jsonify({'success': False, 'error': 'No image'}), 400

        file      = request.files['image']
        location  = request.form.get('location', 'Unknown')
        lat       = float(request.form.get('lat', 0))
        lon       = float(request.form.get('lon', 0))

        img_bytes = file.read()
        tensor, _ = preprocess_image(img_bytes)
        predicted, conf, _ = run_prediction(tensor)
        surface   = get_road_surface_info(predicted)
        score     = calculate_road_quality_score(predicted)

        from physics_engine import BASE_CRR
        entry = {
            'id'           : len(heatmap_db) + 1,
            'location'     : location,
            'lat'          : lat,
            'lon'          : lon,
            'surface_class': predicted,
            'surface_label': predicted.replace('_', ' ').title(),
            'crr'          : BASE_CRR.get(predicted, 0.020),
            'quality_score': score,
            'safety'       : surface.get('safety', 'Medium'),
            'safety_color' : surface.get('safety_color', '#FFD700'),
            'confidence'   : round(conf, 2),
        }
        heatmap_db.append(entry)
        return jsonify({'success': True, 'entry': entry,
                        'total_readings': len(heatmap_db)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/heatmap/data', methods=['GET'])
def heatmap_data():
    """Get all heatmap readings."""
    return jsonify({'success': True, 'readings': heatmap_db,
                    'count': len(heatmap_db)})


@app.route('/geocode', methods=['GET'])
def geocode():
    """Geocode a city name to lat/lon — India only, using Open-Meteo API."""
    city = request.args.get('city', '').strip()
    if not city:
        return jsonify({'success': False, 'error': 'No city provided'}), 400
    try:
        import requests as req
        # Try two queries: city+India bias, then city alone — always filter to IN
        for query in [f"{city} India", city]:
            r = req.get(
                'https://geocoding-api.open-meteo.com/v1/search',
                params={'name': query, 'count': 10, 'language': 'en', 'format': 'json'},
                timeout=6
            )
            results = r.json().get('results', [])
            india = [x for x in results if x.get('country_code') == 'IN']
            if india:
                best = india[0]
                return jsonify({
                    'success': True,
                    'city':    best.get('name', city),
                    'lat':     best.get('latitude'),
                    'lon':     best.get('longitude'),
                    'state':   best.get('admin1', ''),
                    'country': 'India',
                })
        return jsonify({'success': False,
                        'error': f'"{city}" not found in India. Try a larger nearby city.'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)