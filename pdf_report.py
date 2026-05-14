"""
EV RouteIQ — PDF Report Generator
Generates a professional PDF report after road surface analysis.
"""

import io
from datetime import datetime

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm, cm
    from reportlab.lib import colors
    from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                     Table, TableStyle, HRFlowable, KeepTogether)
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    REPORTLAB_AVAILABLE = True

    # ── Brand colors (only when reportlab available) ──────────
    DARK_BG = colors.HexColor('#0A0E1A')
    PRIMARY = colors.HexColor('#00D4FF')
    ACCENT  = colors.HexColor('#39FF14')
    WARN    = colors.HexColor('#FFD700')
    DANGER  = colors.HexColor('#FF4444')
    GRAY    = colors.HexColor('#8892AA')
    LIGHT   = colors.HexColor('#E8EDF8')
    CARD_BG = colors.HexColor('#0F1628')
    MID     = colors.HexColor('#1a2540')

except ImportError:
    REPORTLAB_AVAILABLE = False


def generate_report(prediction_data: dict) -> bytes:
    """
    Generate a professional PDF report from a prediction result.
    Returns PDF as bytes, or raises RuntimeError if reportlab unavailable.
    """
    if not REPORTLAB_AVAILABLE:
        raise RuntimeError("reportlab not installed. Run: pip install reportlab")

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            leftMargin=20*mm, rightMargin=20*mm,
                            topMargin=20*mm, bottomMargin=20*mm)

    styles   = getSampleStyleSheet()
    elements = []

    # ── Custom styles ──────────────────────────────────────
    title_style = ParagraphStyle('Title', parent=styles['Normal'],
        fontSize=22, fontName='Helvetica-Bold', textColor=PRIMARY,
        alignment=TA_CENTER, spaceAfter=4)
    subtitle_style = ParagraphStyle('Sub', parent=styles['Normal'],
        fontSize=10, fontName='Helvetica', textColor=GRAY,
        alignment=TA_CENTER, spaceAfter=2)
    h2_style = ParagraphStyle('H2', parent=styles['Normal'],
        fontSize=13, fontName='Helvetica-Bold', textColor=PRIMARY,
        spaceBefore=12, spaceAfter=6)
    h3_style = ParagraphStyle('H3', parent=styles['Normal'],
        fontSize=10, fontName='Helvetica-Bold', textColor=LIGHT,
        spaceBefore=6, spaceAfter=3)
    body_style = ParagraphStyle('Body', parent=styles['Normal'],
        fontSize=9, fontName='Helvetica', textColor=GRAY,
        spaceAfter=3, leading=14)
    value_style = ParagraphStyle('Val', parent=styles['Normal'],
        fontSize=10, fontName='Helvetica-Bold', textColor=LIGHT)
    small_style = ParagraphStyle('Small', parent=styles['Normal'],
        fontSize=8, fontName='Helvetica', textColor=GRAY)
    winner_style = ParagraphStyle('Winner', parent=styles['Normal'],
        fontSize=11, fontName='Helvetica-Bold', textColor=ACCENT,
        alignment=TA_CENTER, spaceBefore=6, spaceAfter=6)

    def divider():
        return HRFlowable(width='100%', thickness=0.5,
                          color=colors.HexColor('#1a2540'), spaceAfter=6)

    # ── HEADER ─────────────────────────────────────────────
    elements.append(Paragraph('⚡ EV RouteIQ', title_style))
    elements.append(Paragraph('Intelligent Road Surface Energy Optimizer', subtitle_style))
    elements.append(Paragraph(
        f"Report generated: {datetime.now().strftime('%d %B %Y, %I:%M %p')}",
        subtitle_style))
    elements.append(Spacer(1, 6))
    elements.append(divider())

    pred    = prediction_data.get('prediction', {})
    surface = prediction_data.get('surface', {})
    crr     = prediction_data.get('crr', {})
    energy  = prediction_data.get('energy', {})
    rng     = prediction_data.get('range', {})
    vehicle = prediction_data.get('vehicle', {})
    driving = prediction_data.get('driving', {})

    # ── SECTION 1: Classification Result ───────────────────
    elements.append(Paragraph('1. Road Surface Classification', h2_style))

    safety_color_map = {'High': ACCENT, 'Medium': WARN, 'Low': DANGER}
    safety_col = safety_color_map.get(surface.get('safety', 'Medium'), WARN)
    safety_icons = {'High': 'SAFE', 'Medium': 'CAUTION', 'Low': 'DANGER'}

    class_data = [
        ['Surface Class', pred.get('label', '–')],
        ['Confidence',    f"{pred.get('confidence', 0):.1f}%"],
        ['Crr Range',     surface.get('crr_range', '–')],
        ['Safety Level',  safety_icons.get(surface.get('safety', ''), '–')],
        ['Quality Score', f"{driving.get('quality_score', 0)} / 100"],
        ['Rec. Speed',    f"{driving.get('recommended_speed_kmh', 0)} km/h"],
    ]
    t1 = Table(class_data, colWidths=[55*mm, 110*mm])
    t1.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), MID),
        ('BACKGROUND', (0, 0), (0, -1), MID),
        ('TEXTCOLOR',  (0, 0), (0, -1), GRAY),
        ('TEXTCOLOR',  (1, 0), (1, -1), LIGHT),
        ('FONTNAME',   (1, 0), (1, -1), 'Helvetica-Bold'),
        ('FONTSIZE',   (0, 0), (-1, -1), 9),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [CARD_BG, colors.HexColor('#111827')]),
        ('GRID',       (0, 0), (-1, -1), 0.3, colors.HexColor('#1a2540')),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(t1)
    elements.append(Spacer(1, 4))
    elements.append(Paragraph(surface.get('description', ''), body_style))
    elements.append(divider())

    # ── SECTION 2: Vehicle & Conditions ────────────────────
    elements.append(Paragraph('2. Vehicle & Driving Conditions', h2_style))
    cond_data = [
        ['EV Model',       vehicle.get('name', '–'),
         'Battery',        f"{vehicle.get('battery_kwh', 0)} kWh"],
        ['Vehicle Mass',   f"{vehicle.get('mass_kg', 0)} kg",
         'Rated Range',    f"{vehicle.get('rated_range_km', 0)} km"],
        ['Speed',          f"{driving.get('speed_kmh', 0)} km/h",
         'Temperature',    f"{driving.get('temperature_c', 0)}°C"],
        ['Tire Pressure',  f"{driving.get('tire_pressure_bar', 0)} bar",
         'Battery SOC',    f"{driving.get('soc_percent', 0)}%"],
        ['Weather',        driving.get('weather', 'clear').title(),
         'Distance',       f"{driving.get('distance_km', 0)} km"],
    ]
    t2 = Table(cond_data, colWidths=[45*mm, 45*mm, 35*mm, 45*mm])
    t2.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), CARD_BG),
        ('BACKGROUND', (0, 0), (0, -1), MID),
        ('BACKGROUND', (2, 0), (2, -1), MID),
        ('TEXTCOLOR',  (0, 0), (0, -1), GRAY),
        ('TEXTCOLOR',  (2, 0), (2, -1), GRAY),
        ('TEXTCOLOR',  (1, 0), (1, -1), LIGHT),
        ('TEXTCOLOR',  (3, 0), (3, -1), LIGHT),
        ('FONTNAME',   (1, 0), (1, -1), 'Helvetica-Bold'),
        ('FONTNAME',   (3, 0), (3, -1), 'Helvetica-Bold'),
        ('FONTSIZE',   (0, 0), (-1, -1), 9),
        ('GRID',       (0, 0), (-1, -1), 0.3, colors.HexColor('#1a2540')),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(t2)
    elements.append(divider())

    # ── SECTION 3: Physics & Energy ────────────────────────
    elements.append(Paragraph('3. Physics-Based Energy Analysis', h2_style))

    # Crr factors table
    crr_data = [
        ['Crr Factor',      'Value',         'Standard'],
        ['Base Crr',        f"{crr.get('base_crr', 0):.5f}",       'Wallentowitz 2004 / Bosch'],
        ['Adjusted Crr',    f"{crr.get('adjusted_crr', 0):.5f}",   'Combined factors'],
        ['Speed Factor',    f"×{crr.get('speed_factor', 1):.4f}",  'SAE J2452'],
        ['Temp Factor',     f"×{crr.get('temp_factor', 1):.4f}",   'NRC Canada'],
        ['Pressure Factor', f"×{crr.get('pressure_factor', 1):.4f}",'ISO 28580'],
        ['Weather Factor',  f"×{crr.get('weather_factor', 1):.4f}", 'Wong (1993)'],
    ]
    t3 = Table(crr_data, colWidths=[60*mm, 45*mm, 65*mm])
    t3.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY),
        ('TEXTCOLOR',  (0, 0), (-1, 0), DARK_BG),
        ('FONTNAME',   (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [CARD_BG, colors.HexColor('#111827')]),
        ('TEXTCOLOR',  (0, 1), (-1, -1), GRAY),
        ('TEXTCOLOR',  (1, 1), (1, -1), LIGHT),
        ('FONTNAME',   (1, 1), (1, -1), 'Helvetica-Bold'),
        ('FONTSIZE',   (0, 0), (-1, -1), 9),
        ('GRID',       (0, 0), (-1, -1), 0.3, colors.HexColor('#1a2540')),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(t3)
    elements.append(Spacer(1, 8))

    # Energy metrics
    energy_data = [
        ['Energy Metric',         'Value',                    'Notes'],
        ['Rolling Resistance',    f"{energy.get('F_rolling_N',0):.1f} N",  'F = Crr × m × g'],
        ['Aerodynamic Drag',      f"{energy.get('F_aero_N',0):.1f} N",     'Cd=0.28, A=2.4 m²'],
        ['Total Force',           f"{energy.get('F_total_N',0):.1f} N",    'Rolling + Aero'],
        ['Energy / km',           f"{energy.get('energy_wh_per_km',0):.1f} Wh/km", 'At given speed'],
        ['Energy / 100 km',       f"{energy.get('energy_kwh',0):.3f} kWh", 'Without regen'],
        ['Regen Recovery',        f"{energy.get('regen_kwh',0):.3f} kWh",  '30% × regen eff.'],
        ['Net Energy',            f"{energy.get('net_energy_kwh',0):.3f} kWh", 'After regen'],
        ['CO₂ Equivalent',        f"{energy.get('co2_kg',0):.3f} kg",      'Petrol equiv.'],
        ['Vs Ideal Surface',      f"+{energy.get('energy_overhead_pct',0):.1f}%", 'vs dry_asphalt_smooth'],
    ]
    t4 = Table(energy_data, colWidths=[60*mm, 50*mm, 60*mm])
    t4.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY),
        ('TEXTCOLOR',  (0, 0), (-1, 0), DARK_BG),
        ('FONTNAME',   (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [CARD_BG, colors.HexColor('#111827')]),
        ('TEXTCOLOR',  (0, 1), (-1, -1), GRAY),
        ('TEXTCOLOR',  (1, 1), (1, -1), LIGHT),
        ('FONTNAME',   (1, 1), (1, -1), 'Helvetica-Bold'),
        ('FONTSIZE',   (0, 0), (-1, -1), 9),
        ('GRID',       (0, 0), (-1, -1), 0.3, colors.HexColor('#1a2540')),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(t4)
    elements.append(divider())

    # ── SECTION 4: Range & Battery ─────────────────────────
    elements.append(Paragraph('4. Battery & Range Estimation', h2_style))

    bar_pct  = min(100, driving.get('battery_used_pct', 0))
    bar_fill = int(bar_pct / 5)  # 0-20 blocks

    range_data = [
        ['Parameter',          'Value'],
        ['Usable Battery',     f"{rng.get('usable_kwh', 0):.2f} kWh"],
        ['Temperature Penalty',f"{rng.get('temp_penalty_pct', 0):.1f}%"],
        ['Battery Used',       f"{bar_pct:.1f}% for {driving.get('distance_km',0)} km"],
        ['Estimated Range',    f"{rng.get('estimated_range_km', 0):.1f} km"],
        ['Est. Drive Time',    f"{rng.get('drive_hours', 0):.2f} hours"],
    ]
    t5 = Table(range_data, colWidths=[70*mm, 100*mm])
    t5.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), MID),
        ('TEXTCOLOR',  (0, 0), (-1, 0), GRAY),
        ('BACKGROUND', (0, 1), (0, -1), MID),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [CARD_BG, colors.HexColor('#111827')]),
        ('TEXTCOLOR',  (0, 1), (0, -1), GRAY),
        ('TEXTCOLOR',  (1, 1), (1, -1), LIGHT),
        ('FONTNAME',   (1, 1), (1, -1), 'Helvetica-Bold'),
        ('FONTSIZE',   (0, 0), (-1, -1), 9),
        ('GRID',       (0, 0), (-1, -1), 0.3, colors.HexColor('#1a2540')),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(t5)
    elements.append(divider())

    # ── SECTION 5: Recommendations ─────────────────────────
    elements.append(Paragraph('5. Recommendations', h2_style))

    safety = surface.get('safety', 'Medium')
    rec_speed = driving.get('recommended_speed_kmh', 60)
    overhead = energy.get('energy_overhead_pct', 0)

    recs = []
    if safety == 'Low':
        recs.append(f'• DANGER: This surface is hazardous. Maximum safe speed: {rec_speed} km/h.')
        recs.append('• Increase following distance significantly (minimum 4x normal).')
        recs.append('• Avoid hard braking — use gentle progressive deceleration.')
    elif safety == 'Medium':
        recs.append(f'• CAUTION: Surface is degraded. Recommended speed: {rec_speed} km/h.')
        recs.append('• Maintain extra following distance and be alert for road damage.')
    else:
        recs.append(f'• Surface is in good condition. Optimal speed: {rec_speed} km/h.')

    if overhead > 20:
        recs.append(f'• Energy overhead is {overhead:.1f}% vs ideal surface — consider alternative route.')
    elif overhead > 5:
        recs.append(f'• Minor energy overhead ({overhead:.1f}%) vs ideal surface — acceptable.')
    else:
        recs.append('• Energy consumption is near-optimal for this surface type.')

    if driving.get('tire_pressure_bar', 2.3) < 2.0:
        recs.append('• Tire pressure is low! Inflate to 2.3 bar to reduce rolling resistance.')
    if driving.get('temperature_c', 20) < 5:
        recs.append('• Cold weather warning: Battery capacity reduced. Plan charging stops more frequently.')

    for r in recs:
        elements.append(Paragraph(r, body_style))

    elements.append(Spacer(1, 6))
    elements.append(divider())

    # ── FOOTER ────────────────────────────────────────────
    elements.append(Paragraph(
        'EV RouteIQ v2.0 | Physics: SAE J2452 + ISO 28580 + Wallentowitz (2004) + Wong (1993)',
        small_style))
    elements.append(Paragraph(
        'Model: EfficientNet-B4 | 27 Road Surface Classes | For informational purposes only.',
        small_style))

    doc.build(elements)
    return buf.getvalue()
