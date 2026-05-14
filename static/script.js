// EV RouteIQ — script.js v3 (tab-based)
const API=''; let selVeh='tesla_model3_lr', wxCond='clear';
let probChart=null,donutChart=null,cmpChart=null,fleetChart=null;
let lastResult=null, webcamStream=null, leafletMap=null;
let detectedSurface=null; // surface class from last Classify tab result
let lastClassifiedFile=null; // last image file used in Classify tab

const SAFETY_COLORS={High:'#39FF14',Medium:'#FFD700',Low:'#FF4444'};
const SC={dry_asphalt_smooth:'#00D4FF',dry_asphalt_slight:'#00aad4',dry_asphalt_severe:'#FF8C00',
  dry_concrete_smooth:'#4FC3F7',dry_concrete_slight:'#29B6F6',dry_concrete_severe:'#F57C00',
  dry_gravel:'#FFD54F',dry_mud:'#A1887F',fresh_snow:'#E3F2FD',ice:'#81D4FA',melted_snow:'#B3E5FC',
  water_asphalt_smooth:'#26C6DA',water_asphalt_slight:'#00ACC1',water_asphalt_severe:'#FF7043',
  water_concrete_smooth:'#4DD0E1',water_concrete_slight:'#26C6DA',water_concrete_severe:'#FF5722',
  water_gravel:'#FFA726',water_mud:'#D32F2F',wet_asphalt_smooth:'#42A5F5',
  wet_asphalt_slight:'#1E88E5',wet_asphalt_severe:'#E53935',wet_concrete_smooth:'#64B5F6',
  wet_concrete_slight:'#2196F3',wet_concrete_severe:'#C62828',wet_gravel:'#FF8F00',wet_mud:'#B71C1C'};
const CLS=['dry_asphalt_severe','dry_asphalt_slight','dry_asphalt_smooth',
  'dry_concrete_severe','dry_concrete_slight','dry_concrete_smooth','dry_gravel','dry_mud',
  'fresh_snow','ice','melted_snow','water_asphalt_severe','water_asphalt_slight',
  'water_asphalt_smooth','water_concrete_severe','water_concrete_slight','water_concrete_smooth',
  'water_gravel','water_mud','wet_asphalt_severe','wet_asphalt_slight','wet_asphalt_smooth',
  'wet_concrete_severe','wet_concrete_slight','wet_concrete_smooth','wet_gravel','wet_mud'];

document.addEventListener('DOMContentLoaded',()=>{
  setupTabs(); checkHealth(); loadVehicles(); setupSliders();
  setupUpload(); setupWeather(); buildRefList('all'); setupRefFilter();
  setupCompareTab(); setupFleet(); setupHeatmap(); setupWebcam(); setupPdf();
});

// ── TABS ──────────────────────────────────────────────────
function setupTabs(){
  document.querySelectorAll('.nav-tab').forEach(btn=>{
    btn.addEventListener('click',()=>{
      document.querySelectorAll('.nav-tab').forEach(b=>b.classList.remove('active'));
      document.querySelectorAll('.tab-content').forEach(t=>t.classList.remove('active'));
      btn.classList.add('active');
      document.getElementById('tab-'+btn.dataset.tab).classList.add('active');
      if(btn.dataset.tab==='compare') updateCmpVehicle();
      if(btn.dataset.tab==='fleet') updateFleetVehicle();
      if(btn.dataset.tab==='heatmap'){
        if(!leafletMap) setTimeout(initMap, 100);
        else setTimeout(()=>leafletMap.invalidateSize(), 100);
      }
    });
  });
}

// ── HEALTH ────────────────────────────────────────────────
async function checkHealth(){
  const dot=document.getElementById('statusDot'),tx=document.getElementById('statusText');
  try{
    const d=await(await fetch('/health')).json();
    dot.className=d.model_loaded?'status-dot ok':'status-dot err';
    tx.textContent=d.model_loaded?`${d.model_type} · ${d.num_classes} classes`:'Model not loaded';
  }catch{dot.className='status-dot err';tx.textContent='Server offline';}
}

// ── VEHICLES ──────────────────────────────────────────────
let allVehicles=[];
async function loadVehicles(){
  try{
    const d=await(await fetch('/vehicles')).json();
    allVehicles=d.vehicles||[];
    renderVehicles(allVehicles);
    populateSurfaceOpts();
    updateCmpVehicle(); updateFleetVehicle();
  }catch(e){console.warn('Vehicles load failed',e);}
}
function renderVehicles(list){
  const grid=document.getElementById('vehicleGrid');
  if(!grid) return;
  grid.innerHTML=list.map(v=>`<button class="vehicle-btn${v.id===selVeh?' active':''}"
    data-id="${v.id}" onclick="selectVehicle('${v.id}',this)">
    <span class="vb-icon">${v.icon}</span>
    <span class="vb-name">${v.name}</span>
    <span class="vb-bat">${v.battery_kwh} kWh · ${v.range_km} km</span>
  </button>`).join('');
  const sv=list.find(v=>v.id===selVeh)||list[0];
  if(sv){
    document.getElementById('svName').textContent=sv.name;
    document.getElementById('svSpecs').textContent=`${sv.battery_kwh} kWh · ${sv.mass_kg} kg · ${sv.range_km} km`;
  }
}
function selectVehicle(id,btn){
  selVeh=id;
  document.querySelectorAll('.vehicle-btn').forEach(b=>b.classList.remove('active'));
  btn.classList.add('active');
  document.getElementById('svName').textContent=btn.querySelector('.vb-name').textContent;
  document.getElementById('svSpecs').textContent=btn.querySelector('.vb-bat').textContent;
  updateCmpVehicle(); updateFleetVehicle();
}
const vsearch=document.getElementById('vehicleSearch');
if(vsearch) vsearch.addEventListener('input',()=>{
  const q=vsearch.value.toLowerCase();
  renderVehicles(allVehicles.filter(v=>v.name.toLowerCase().includes(q)||v.brand.toLowerCase().includes(q)));
});

// ── SLIDERS ───────────────────────────────────────────────
function setupSliders(){
  [['speedSlider','speedVal'],['tempSlider','tempVal'],['pressureSlider','pressureVal'],
   ['socSlider','socVal'],['distSlider','distVal']].forEach(([sid,vid])=>{
    const el=document.getElementById(sid);
    if(el) el.addEventListener('input',()=>{ document.getElementById(vid).textContent=el.value; });
  });
}
function getConditions(){
  return{vehicle_id:selVeh,
    speed_kmh:+document.getElementById('speedSlider').value,
    temperature_c:+document.getElementById('tempSlider').value,
    tire_pressure_bar:+document.getElementById('pressureSlider').value,
    soc_percent:+document.getElementById('socSlider').value,
    distance_km:+document.getElementById('distSlider').value,
    weather_condition:wxCond};
}

// ── UPLOAD + CLASSIFY ─────────────────────────────────────
function setupUpload(){
  const zone=document.getElementById('uploadZone'),
        inp=document.getElementById('fileInput'),
        btn=document.getElementById('classifyBtn'),
        prev=document.getElementById('previewImg'),
        inner=document.getElementById('uploadInner');
  if(!zone) return;
  zone.addEventListener('click',()=>inp.click());
  zone.addEventListener('dragover',e=>{e.preventDefault();zone.classList.add('drag-over');});
  zone.addEventListener('dragleave',()=>zone.classList.remove('drag-over'));
  zone.addEventListener('drop',e=>{e.preventDefault();zone.classList.remove('drag-over');
    if(e.dataTransfer.files[0]) loadFile(e.dataTransfer.files[0]);});
  inp.addEventListener('change',()=>{ if(inp.files[0]) loadFile(inp.files[0]); });
  btn.addEventListener('click',classify);
  function loadFile(f){
    if(!f.type.startsWith('image/')) return alert('Image files only');
    inp._file=f;
    prev.src=URL.createObjectURL(f); prev.style.display='block';
    inner.style.display='none'; btn.disabled=false;
  }
}
async function classify(){
  const btn=document.getElementById('classifyBtn'),
        tx=btn.querySelector('.btn-text'),sp=btn.querySelector('.btn-spinner');
  const f=document.getElementById('fileInput')._file||document.getElementById('fileInput').files[0];
  if(!f) return;
  btn.disabled=true; tx.style.display='none'; sp.style.display='block';
  try{
    const c=getConditions(), form=new FormData();
    form.append('image',f);
    Object.entries(c).forEach(([k,v])=>form.append(k,v));
    const d=await(await fetch('/predict',{method:'POST',body:form})).json();
    if(d.success){
      lastResult=d;
      // Save file so Heatmap tab can reuse it
      lastClassifiedFile=f;
      const ub=document.getElementById('useClassifiedBtn');
      if(ub) ub.disabled=false;
      renderResults(d);
    }
    else alert('Error: '+(d.error||'Unknown'));
  }catch(e){alert('Server error: '+e.message);}
  finally{btn.disabled=false;tx.style.display='block';sp.style.display='none';}
}
function renderResults(d){
  const{prediction:p,surface:sf,crr,energy:e,range:r,vehicle:v,driving:dr}=d;
  document.getElementById('resultsCard').style.display='block';
  document.getElementById('donutCard').style.display='block';
  document.getElementById('resultBadge').textContent=p.label;
  document.getElementById('resultConf').textContent=p.confidence.toFixed(1)+'%';
  document.getElementById('resultDesc').textContent=sf.description||'–';
  document.getElementById('rmCrr').textContent=crr.adjusted_crr.toFixed(5);
  document.getElementById('rmEnergy').textContent=e.energy_wh_per_km.toFixed(0)+' Wh';
  document.getElementById('rmRange').textContent=r.estimated_range_km+' km';
  document.getElementById('rmScore').textContent=dr.quality_score+'/100';
  document.getElementById('rmCo2').textContent=e.co2_kg.toFixed(2)+' kg';
  document.getElementById('rmSpeed').textContent=dr.recommended_speed_kmh+' km/h';
  document.getElementById('battDist').textContent=dr.distance_km;
  const pct=Math.min(100,dr.battery_used_pct||0);
  const fill=document.getElementById('battFill');
  fill.style.width=pct+'%';
  fill.className='batt-fill'+(pct>70?' danger':'');
  document.getElementById('battText').textContent=pct.toFixed(1)+'% used';
  const saf=sf.safety||'Medium',sc=SAFETY_COLORS[saf]||'#FFD700',
        icons={High:'✅',Medium:'⚠️',Low:'🚨'};
  const sb=document.getElementById('safetyBadge');
  sb.style.cssText=`color:${sc};border-color:${sc};background:${sc}18`;
  document.getElementById('safetyIcon').textContent=icons[saf]||'⚠️';
  document.getElementById('safetyText').textContent=saf+' Safety';
  // Physics factor badges: actual value on top, multiplier below
  // Use null-safe helper to avoid crash if element missing
  function setEl(id, val){ const el=document.getElementById(id); if(el) el.textContent=val; }
  setEl('pfSpeedVal',   crr.speed_kmh);
  setEl('pfSpeed',      (crr.speed_factor||1).toFixed(3));
  setEl('pfTempVal',    crr.temperature_c);
  setEl('pfTemp',       (crr.temp_factor||1).toFixed(3));
  setEl('pfPressureVal',crr.tire_pressure_bar);
  setEl('pfPressure',   (crr.pressure_factor||1).toFixed(3));
  setEl('pfWeatherVal', (crr.weather||'clear').replace(/_/g,' '));
  setEl('pfWeather',    (crr.weather_factor||1).toFixed(3));

  renderProbChart(p.all_probabilities);
  renderDonutChart(e);
  // Update locked segment in Compare tab
  updateDetectedSegment(p.class, p.label);
  // Highlight matched surface in Reference panel
  highlightRefSurface(p.class);
}
function renderProbChart(probs){
  // Sort by value descending, take top 8
  const top = Object.entries(probs)
    .sort(([,a],[,b]) => b - a)
    .slice(0, 8);

  const wrap  = document.querySelector('.prob-chart-wrap');
  const canvas = document.getElementById('probChart');

  // Destroy old chart first so we can resize canvas safely
  if(probChart){ probChart.destroy(); probChart = null; }

  // Set EXACT pixel dimensions on canvas — prevents resize feedback on hover
  const barH  = 40;
  const w     = wrap ? wrap.clientWidth : 320;
  const h     = Math.max(80, top.length * barH);
  canvas.width  = w;
  canvas.height = h;
  canvas.style.width  = w + 'px';
  canvas.style.height = h + 'px';

  probChart = new Chart(canvas, {
    type: 'bar',
    data: {
      labels: top.map(([k]) => k.replace(/_/g, ' ')),
      datasets: [{
        data: top.map(([,v]) => v),
        backgroundColor: top.map(([k]) => (SC[k]||'#00D4FF') + '99'),
        borderColor:     top.map(([k]) =>  SC[k]||'#00D4FF'),
        borderWidth: 1, borderRadius: 4
      }]
    },
    options: {
      indexAxis: 'y',
      responsive: false,          // CRITICAL: prevents expand-on-hover
      animation: { duration: 0 },
      layout: { padding: { left: 0, right: 8, top: 2, bottom: 2 } },
      plugins: {
        legend: { display: false },
        tooltip: { enabled: true }
      },
      scales: {
        x: {
          ticks: { color: '#8892AA', font: { size: 11 } },
          grid:  { color: 'rgba(255,255,255,0.05)' },
          max: 100
        },
        y: {
          ticks: {
            color: '#E8EDF8',
            font:  { size: 12, weight: '600' },
            padding: 6,
            autoSkip: false,
            callback: function(val, idx) {
              const raw = top[idx]?.[0] || '';
              return raw.replace(/_/g,' ').replace(/\b\w/g, c => c.toUpperCase());
            }
          },
          grid: { display: false }
        }
      }
    }
  });
}
function renderDonutChart(e){
  if(donutChart) donutChart.destroy();
  donutChart=new Chart(document.getElementById('donutChart'),{type:'doughnut',
    data:{labels:['Rolling','Aero Drag','Regen'],
      datasets:[{data:[e.F_rolling_N,e.F_aero_N,e.regen_kwh*1000],
        backgroundColor:['#00D4FF88','#FF444488','#39FF1488'],
        borderColor:['#00D4FF','#FF4444','#39FF14'],borderWidth:1}]},
    options:{plugins:{legend:{display:false}},cutout:'70%'}});
  document.getElementById('donutLegend').innerHTML=
    [['#00D4FF','Rolling',e.F_rolling_N.toFixed(1)+' N'],
     ['#FF4444','Aero Drag',e.F_aero_N.toFixed(1)+' N'],
     ['#39FF14','Regen',( e.regen_kwh*1000).toFixed(1)+' Wh']]
    .map(([c,l,v])=>`<div class="dl-item"><div class="dl-dot" style="background:${c}"></div>
      <span style="color:#8892AA;flex:1">${l}</span><span style="font-weight:600">${v}</span></div>`).join('');
}

// ── DETECTED SURFACE (auto-fill Route A Seg 1) ───────────
function updateDetectedSegment(cls, label){
  detectedSurface = cls;
  const lbl = document.getElementById('detectedSurfaceLabel');
  const hint = document.getElementById('detectedHint');
  const prompt = document.getElementById('classifyPrompt');
  const dot = document.querySelector('.detected-dot');
  if(lbl){
    lbl.textContent = label || cls.replace(/_/g,' ');
    lbl.title = cls;
  }
  if(hint) hint.style.display = 'inline';
  if(prompt) prompt.classList.add('hidden');
  // Color the dot by safety
  const safety = lastResult?.surface?.safety || 'Medium';
  const sc = {High:'#39FF14',Medium:'#FFD700',Low:'#FF4444'};
  if(dot) dot.style.background = sc[safety] || '#00D4FF';
  // Update segment row border color
  const row = document.getElementById('detectedSegRow');
  if(row){
    const c = sc[safety] || '#00D4FF';
    row.style.borderColor = c+'66';
    row.style.background = c+'0D';
  }
}

// ── ANALYSIS CONFIG STRIP ────────────────────────────────
function showAnalysisStrip(v, dr, crr) {
  const strip = document.getElementById('analysisStrip');
  const grid  = document.getElementById('acsGrid');
  if(!strip || !grid) return;

  const vehName  = v?.name || allVehicles.find(x=>x.id===selVeh)?.name || 'Unknown EV';
  const wxRaw    = document.getElementById('wDesc')?.textContent || 'Clear';
  const wxLabel  = wxRaw.split('(')[0].trim().split('✅')[0].trim() || 'Clear Sky';
  const pressure = document.getElementById('pressureVal')?.textContent || '2.3';

  grid.innerHTML = `
    <div class="acs-item">
      <span class="acs-lbl">🚗 Vehicle</span>
      <span class="acs-val" title="${vehName}">${vehName}</span>
    </div>
    <div class="acs-item">
      <span class="acs-lbl">⚡ Speed · SOC</span>
      <span class="acs-val">${dr.speed_kmh} km/h · ${dr.soc_percent}%</span>
    </div>
    <div class="acs-item">
      <span class="acs-lbl">🌡️ Temp · Pressure</span>
      <span class="acs-val">${dr.temperature_c}°C · ${pressure} bar</span>
    </div>
    <div class="acs-item">
      <span class="acs-lbl">🌦️ Weather</span>
      <span class="acs-val">${wxLabel} (Wx×${crr?.weather_factor?.toFixed(2)||'1.00'})</span>
    </div>
    <div class="acs-item">
      <span class="acs-lbl">📏 Distance</span>
      <span class="acs-val">${dr.distance_km} km segment</span>
    </div>
    <div class="acs-item">
      <span class="acs-lbl">🔄 Adj. Crr</span>
      <span class="acs-val">${crr?.adjusted_crr?.toFixed(5)||'–'}</span>
    </div>`;
  strip.style.display = 'block';
}

// ── WEATHER ───────────────────────────────────────────────
function setupWeather(){
  const btn=document.getElementById('fetchWeatherBtn'),
        inp=document.getElementById('cityInput');
  if(btn) btn.addEventListener('click',fetchWeather);
  if(inp) inp.addEventListener('keydown',e=>{ if(e.key==='Enter') fetchWeather(); });
}
async function fetchWeather(){
  const city=document.getElementById('cityInput').value.trim(); if(!city) return;
  const btn=document.getElementById('fetchWeatherBtn');
  btn.textContent='...'; btn.disabled=true;
  try{
    const d=await(await fetch('/weather?city='+encodeURIComponent(city))).json();
    document.getElementById('wIcon').textContent=d.icon||'🌤️';
    document.getElementById('wCity').textContent=d.city+', '+d.country;
    const srcMap = {
      'live_openmeteo':  ' ✅ Live (Open-Meteo)',
      'live_weatherapi': ' ✅ Live (WeatherAPI)',
      'live_owm': ' ✅ Live (OpenWeatherMap)',
      'demo': ' 🟡 Demo preset',
      'default': ' ⚠️ Default'
    };
    const src = srcMap[d.source] || '';
    document.getElementById('wDesc').textContent = d.description + src;
    document.getElementById('wDesc').style.color=d.source==='default'?'#FFD700':'';
    document.getElementById('wTemp').textContent=d.temperature_c;
    document.getElementById('wHumid').textContent=d.humidity_pct;
    document.getElementById('wWind').textContent=d.wind_kmh;
    // ── AUTO-SYNC temperature slider to live weather ──
    const tSlider=document.getElementById('tempSlider');
    const tVal=document.getElementById('tempVal');
    if(tSlider){
      const t=Math.max(-10,Math.min(50,Math.round(d.temperature_c)));
      tSlider.value=t; tVal.textContent=t;
      tSlider.style.accentColor='#39FF14';
      setTimeout(()=>tSlider.style.accentColor='',2000);
    }
    // ── AUTO-SYNC weather condition for Crr calculations ──
    wxCond=d.condition||'clear';
    const badge=document.getElementById('weatherBadge');
    if(badge){
      const srcLabels={'live_openmeteo':'✅ Live','live_weatherapi':'✅ Live','demo':'🟡 Demo','default':'⚠️ Default'};
      badge.textContent=srcLabels[d.source]||(d.source?.startsWith('live')?'✅ Live':'🟡 Demo');
    }
    const note=document.getElementById('crrNote');
    if(note) note.style.display='flex';
    const wc=document.getElementById('weatherCond');
    if(wc) wc.textContent=d.description;
  }catch(e){alert('Weather error: '+e.message);}
  finally{btn.textContent='Fetch ⚡';btn.disabled=false;}
}

// ── PER-TAB WEATHER FETCH (Compare) ──────────────────────
async function fetchCmpWeather(){
  const city = document.getElementById('cmpCityInput').value.trim();
  if(!city){ alert('Enter a city name first'); return; }
  const btn = document.getElementById('cmpFetchWeatherBtn');
  const status = document.getElementById('cmpWeatherStatus');
  btn.textContent = '...'; btn.disabled = true;
  try{
    const d = await(await fetch('/weather?city='+encodeURIComponent(city))).json();
    // Auto-fill temp input
    const tempEl = document.getElementById('cmpTemp');
    if(tempEl) tempEl.value = Math.round(d.temperature_c);
    // Auto-set hidden weather dropdown
    const wxEl = document.getElementById('cmpWeather');
    if(wxEl) wxEl.value = d.condition || 'clear';
    // Show status badge
    const srcLabel = {
      'live_weatherapi': 'Live WeatherAPI',
      'live_owm': 'Live OpenWeatherMap',
      'demo': 'Demo preset',
      'default': 'Default'
    }[d.source] || d.source;
    const srcColor = d.source.startsWith('live') ? '#39FF14' : '#FFD700';
    status.style.display = 'block';
    status.style.borderColor = srcColor + '66';
    status.innerHTML = `<span style="color:${srcColor};font-weight:700">${d.icon} ${d.city}</span>
      &nbsp;·&nbsp; ${d.temperature_c}°C &nbsp;·&nbsp; ${d.description}
      &nbsp;·&nbsp; <span style="color:${srcColor}">${srcLabel}</span>
      <br/><small style="color:#5A6478">Crr will use: <strong style="color:var(--primary)">${d.condition}</strong> weather factor</small>`;
  }catch(e){ alert('Weather fetch error: '+e.message); }
  finally{ btn.textContent='⚡ Fetch'; btn.disabled=false; }
}

// ── SURFACE REFERENCE ─────────────────────────────────────
const SI={dry_asphalt_smooth:{crr:'0.010–0.011',s:'High'},dry_asphalt_slight:{crr:'0.013–0.015',s:'High'},
  dry_asphalt_severe:{crr:'0.020–0.030',s:'Medium'},dry_concrete_smooth:{crr:'0.011–0.013',s:'High'},
  dry_concrete_slight:{crr:'0.013–0.015',s:'High'},dry_concrete_severe:{crr:'0.020–0.030',s:'Medium'},
  dry_gravel:{crr:'0.020–0.030',s:'Medium'},dry_mud:{crr:'0.100–0.150',s:'Low'},
  fresh_snow:{crr:'0.030–0.050',s:'Low'},ice:{crr:'0.015–0.030',s:'Low'},
  melted_snow:{crr:'0.040–0.060',s:'Low'},water_asphalt_smooth:{crr:'0.012–0.014',s:'High'},
  water_asphalt_slight:{crr:'0.016–0.020',s:'Medium'},water_asphalt_severe:{crr:'0.025–0.035',s:'Low'},
  water_concrete_smooth:{crr:'0.014–0.016',s:'High'},water_concrete_slight:{crr:'0.016–0.020',s:'Medium'},
  water_concrete_severe:{crr:'0.030–0.040',s:'Low'},water_gravel:{crr:'0.030–0.040',s:'Low'},
  water_mud:{crr:'0.150–0.250',s:'Low'},wet_asphalt_smooth:{crr:'0.012–0.015',s:'High'},
  wet_asphalt_slight:{crr:'0.016–0.020',s:'Medium'},wet_asphalt_severe:{crr:'0.024–0.036',s:'Low'},
  wet_concrete_smooth:{crr:'0.014–0.016',s:'High'},wet_concrete_slight:{crr:'0.016–0.020',s:'Medium'},
  wet_concrete_severe:{crr:'0.030–0.040',s:'Low'},wet_gravel:{crr:'0.030–0.040',s:'Low'},
  wet_mud:{crr:'0.150–0.250',s:'Low'}};
function buildRefList(f){
  const list=document.getElementById('refList'); if(!list) return;
  const cls=f==='all'?CLS:f==='snow'?CLS.filter(c=>c.includes('snow')||c==='ice'||c.includes('melted')):CLS.filter(c=>c.startsWith(f));
  const activeCls = window._lastHighlightedCls || null;
  list.innerHTML=cls.map(c=>{
    const i=SI[c]||{};
    const sc=SAFETY_COLORS[i.s]||'#FFD700', cc=SC[c]||'#00D4FF';
    const isActive = c === activeCls;
    const activeClass = isActive ? ' ref-item-active' : '';
    const badge = isActive ? '<span class="ref-your-road">Your Road</span>' : '';
    const crrVal = i.crr || '-';
    const safetyVal = i.s || '-';
    const name = c.replace(/_/g,' ');
    return '<div class="ref-item'+activeClass+'" data-cls="'+c+'" onclick="fillFromRef(\'' + c + '\')">'
      +'<div class="ref-dot" style="background:'+cc+'"></div>'
      +'<span class="ref-name">'+name+'</span>'
      +'<span class="ref-crr">'+crrVal+'</span>'
      +'<span class="ref-safety" style="color:'+sc+';border-color:'+sc+';background:'+sc+'18">'+safetyVal+'</span>'
      +badge+'</div>';
  }).join('');
}
function setupRefFilter(){
  document.querySelectorAll('.ref-btn').forEach(b=>b.addEventListener('click',()=>{
    document.querySelectorAll('.ref-btn').forEach(x=>x.classList.remove('active'));
    b.classList.add('active'); buildRefList(b.dataset.filter);
  }));
}
function highlightRefSurface(cls){
  // Remember which class to highlight
  window._lastHighlightedCls = cls;

  // Switch to All filter without full rebuild flash
  document.querySelectorAll('.ref-btn').forEach(b => {
    b.classList.toggle('active', b.dataset.filter === 'all');
  });
  // Rebuild with highlight baked in (no double-rebuild)
  buildRefList('all');

  // Scroll into view
  const target = document.querySelector(`.ref-item[data-cls="${cls}"]`);
  if(target) setTimeout(() => target.scrollIntoView({behavior:'smooth', block:'nearest'}), 150);
}

// ── SURFACE DROPDOWNS (shared) ────────────────────────────
function populateSurfaceOpts(){
  document.querySelectorAll('.cmp-seg-surface:not(#cmpWeather)').forEach(sel=>fillSel(sel));
}
function fillSel(sel){
  sel.innerHTML=CLS.map(c=>`<option value="${c}">${c.replace(/_/g,' ')}</option>`).join('');
}

// ── COMPARE TAB ───────────────────────────────────────────
function setupCompareTab(){
  ['cmpRouteASegs','cmpRouteBSegs'].forEach(id=>{
    const list=document.getElementById(id);
    if(list) list.querySelectorAll('.cmp-seg-surface').forEach(s=>fillSel(s));
  });
  const btn=document.getElementById('compareBtn');
  if(btn) btn.addEventListener('click',doCompare);
}
function updateCmpVehicle(){
  const v=allVehicles.find(x=>x.id===selVeh);
  const el=document.getElementById('cmpVehicleName');
  if(el&&v) el.textContent=v.name+' · '+v.battery_kwh+' kWh';
}
function addSegment(listId){
  const list=document.getElementById(listId); if(!list) return;
  const n=list.querySelectorAll('.cmp-seg-row').length+1;
  const row=document.createElement('div');
  row.className='cmp-seg-row';
  row.innerHTML=`<span class="seg-num">${n}</span>
    <select class="cmp-seg-surface"></select>
    <input type="number" class="cmp-seg-dist" value="30" min="1" max="999"/>
    <span class="seg-unit">km</span>
    <button class="seg-remove-btn" onclick="removeSegment(this)">×</button>`;
  list.appendChild(row);
  fillSel(row.querySelector('.cmp-seg-surface'));
  updateTotals(listId);
}
function removeSegment(btn){
  const row=btn.closest('.cmp-seg-row');
  const list=row.parentElement;
  if(list.querySelectorAll('.cmp-seg-row').length<=1) return;
  row.remove();
  list.querySelectorAll('.cmp-seg-row .seg-num').forEach((s,i)=>s.textContent=i+1);
  updateTotals(list.id);
}
function updateTotals(listId){
  const list=document.getElementById(listId); if(!list) return;
  const total=[...list.querySelectorAll('.cmp-seg-dist')].reduce((s,i)=>s+(+i.value||0),0);
  const tidMap={cmpRouteASegs:'routeATotalDist',cmpRouteBSegs:'routeBTotalDist'};
  const tid=tidMap[listId];
  if(tid) document.getElementById(tid).textContent='Total: '+total+' km';
}
document.addEventListener('input',e=>{
  if(e.target.classList.contains('cmp-seg-dist')){
    const list=e.target.closest('.route-segs-list');
    if(list) updateTotals(list.id);
  }
});
async function doCompare(){
  const btn=document.getElementById('compareBtn'); btn.disabled=true; btn.textContent='Comparing...';
  try{
    // Seg 1 of Route A = detected surface (locked) or fallback
    const detectedDist = +(document.querySelector('#detectedSegRow .cmp-seg-dist')?.value)||50;
    const seg1Surface = detectedSurface || 'dry_asphalt_smooth';
    if(!detectedSurface){
      alert('Please classify a road image first to auto-detect Segment 1 of Route A.');
      btn.disabled=false; btn.textContent='⚡ Compare Routes';
      return;
    }
    // Remaining Route A segments (user-chosen, excluding the locked first row)
    const extraARows=[...document.getElementById('cmpRouteASegs').querySelectorAll('.cmp-seg-row')]
      .filter(r=>!r.id || r.id!=='detectedSegRow')
      .map(r=>({surface:r.querySelector('.cmp-seg-surface').value,
                distance_km:+(r.querySelector('.cmp-seg-dist').value)||30}));
    const routeA=[{surface:seg1Surface,distance_km:detectedDist},...extraARows];
    // Route B: all user-chosen
    const routeB=[...document.getElementById('cmpRouteBSegs').querySelectorAll('.cmp-seg-row')]
      .map(r=>({surface:r.querySelector('.cmp-seg-surface').value,
                distance_km:+(r.querySelector('.cmp-seg-dist').value)||30}));
    const body={vehicle_id:selVeh,
      soc_percent:+(document.getElementById('cmpSoc').value)||90,
      speed_kmh:+(document.getElementById('cmpSpeed').value)||60,
      temperature_c:+(document.getElementById('cmpTemp').value)||20,
      tire_pressure_bar:+(document.getElementById('cmpPressure').value)||2.3,
      weather_condition:document.getElementById('cmpWeather').value||'clear',
      route_a:routeA, route_b:routeB};
    const d=await(await fetch('/compare',{method:'POST',
      headers:{'Content-Type':'application/json'},body:JSON.stringify(body)})).json();
    if(d.success) renderComparison(d.comparison);
    else alert('Error: '+d.error);
  }catch(e){alert('Error: '+e.message);}
  finally{btn.disabled=false;btn.textContent='⚡ Compare Routes';}
}
function renderComparison(c){
  const panel=document.getElementById('compareResultsPanel');
  const btn=document.getElementById('compareBtn');
  panel.style.display='block';
  /* ── Force panel to same width & alignment as the button ── */
  if(btn){
    const w=btn.offsetWidth;
    const l=btn.offsetLeft;
    panel.style.width=w+'px';
    panel.style.marginLeft=l+'px';
    panel.style.marginRight='0';
    panel.style.boxSizing='border-box';
  }

  const wa=c.winner==='A', wc=wa?'#00D4FF':'#39FF14', wlabel=wa?'🅰 Route A':'🅱 Route B';
  const wb=document.getElementById('winnerBanner');
  wb.style.cssText=`background:${wc}18;border:1px solid ${wc};color:${wc}`;
  wb.textContent=`${wlabel} is more efficient — saves ${c.energy_saved_kwh} kWh (${c.energy_saved_pct}%)`;
  document.getElementById('crBoxA').innerHTML=`<div class="cr-label">Route A</div>
    <div class="cr-val" style="color:#00D4FF">${c.route_a.total_energy_kwh} kWh</div>
    <div class="cr-sub">${c.route_a.total_distance_km} km · Crr ${c.route_a.avg_crr}</div>`;
  document.getElementById('crBoxSavings').innerHTML=`<div class="cr-label" style="color:#FFD700">Savings</div>
    <div class="cr-val" style="color:#FFD700">${c.energy_saved_kwh} kWh</div>
    <div class="cr-sub">${c.energy_saved_pct}% less energy</div>`;
  document.getElementById('crBoxB').innerHTML=`<div class="cr-label">Route B</div>
    <div class="cr-val" style="color:#39FF14">${c.route_b.total_energy_kwh} kWh</div>
    <div class="cr-sub">${c.route_b.total_distance_km} km · Crr ${c.route_b.avg_crr}</div>`;
  if(cmpChart) cmpChart.destroy();
  const cmpCanvas = document.getElementById('compareChart');
  const cmpWrap = cmpCanvas.parentElement;
  const cmpW = cmpWrap ? Math.max(200, cmpWrap.clientWidth - 32) : 400;
  cmpCanvas.width = cmpW; cmpCanvas.height = 180;
  cmpCanvas.style.width = cmpW+'px'; cmpCanvas.style.height = '180px';
  cmpChart=new Chart(cmpCanvas,{type:'bar',
    data:{labels:['Route A','Route B'],
      datasets:[{label:'Energy (kWh)',data:[c.route_a.total_energy_kwh,c.route_b.total_energy_kwh],
        backgroundColor:['#00D4FF44','#39FF1444'],borderColor:['#00D4FF','#39FF14'],
        borderWidth:2,borderRadius:6}]},
    options:{responsive:false,animation:{duration:0},
      plugins:{legend:{labels:{color:'#8892AA',font:{size:12}}},
        tooltip:{enabled:true}},
      categoryPercentage:0.7, barPercentage:0.85,
      scales:{x:{ticks:{color:'#E8EDF8',font:{size:13,weight:'700'}},grid:{display:false}},
        y:{ticks:{color:'#8892AA'},grid:{color:'rgba(255,255,255,0.05)'},
          title:{display:true,text:'Energy (kWh)',color:'#5A6478',font:{size:11}}}}}});
  const mkSegs=(segs,color)=>segs.map(s=>`<div class="csd-seg">
    <span>${s.surface.replace(/_/g,' ')}</span>
    <span>${s.distance_km}km</span>
    <span class="csd-energy" style="color:${color}">${s.energy_kwh}kWh</span></div>`).join('');
  document.getElementById('compareSegsDetail').innerHTML=`
    <div class="csd-panel"><div class="csd-header" style="color:#00D4FF">🅰 Route A Segments</div>
      ${mkSegs(c.route_a.segments,'#00D4FF')}</div>
    <div class="csd-panel"><div class="csd-header" style="color:#39FF14">🅱 Route B Segments</div>
      ${mkSegs(c.route_b.segments,'#39FF14')}</div>`;
  panel.scrollIntoView({behavior:'smooth',block:'nearest'});
}

// ── FLEET ─────────────────────────────────────────────────
let fleetFiles=[];
function setupFleet(){
  const drop=document.getElementById('fleetDrop'), inp=document.getElementById('fleetInput');
  if(!drop) return;
  drop.addEventListener('click',()=>inp.click());
  drop.addEventListener('dragover',e=>{e.preventDefault();drop.classList.add('drag-over');});
  drop.addEventListener('dragleave',()=>drop.classList.remove('drag-over'));
  drop.addEventListener('drop',e=>{e.preventDefault();drop.classList.remove('drag-over');loadFleetFiles([...e.dataTransfer.files]);});
  inp.addEventListener('change',()=>loadFleetFiles([...inp.files]));
  const aBtn=document.getElementById('analyzeFleetBtn');
  if(aBtn) aBtn.addEventListener('click',analyzeFleet);
}
function updateFleetVehicle(){
  const v=allVehicles.find(x=>x.id===selVeh);
  const el=document.getElementById('fleetVehicleName');
  if(el&&v) el.textContent=v.name;
}
function loadFleetFiles(files){
  fleetFiles=files.filter(f=>f.type.startsWith('image/')).slice(0,10);
  const inner=document.getElementById('fleetDropInner'), grid=document.getElementById('fleetPreviewGrid');
  if(inner) inner.style.display=fleetFiles.length?'none':'flex';
  if(grid) grid.innerHTML=fleetFiles.map(f=>`<img src="${URL.createObjectURL(f)}" class="fleet-thumb" title="${f.name}"/>`).join('');
  const btn=document.getElementById('analyzeFleetBtn');
  if(btn) btn.disabled=fleetFiles.length===0;
}
async function analyzeFleet(){
  if(!fleetFiles.length) return;
  const btn=document.getElementById('analyzeFleetBtn');
  btn.textContent='Analyzing...'; btn.disabled=true;
  try{
    const form=new FormData();
    fleetFiles.forEach(f=>form.append('images',f));
    form.append('vehicle_id',selVeh);
    form.append('speed_kmh',document.getElementById('speedSlider')?.value||60);
    form.append('temperature_c',document.getElementById('tempSlider')?.value||20);
    form.append('tire_pressure_bar',document.getElementById('pressureSlider')?.value||2.3);
    form.append('weather_condition',wxCond);
    form.append('distance_km',document.getElementById('fleetSegDist').value||50);
    const d=await(await fetch('/fleet',{method:'POST',body:form})).json();
    if(d.success) renderFleet(d);
    else alert('Fleet error: '+d.error);
  }catch(e){alert('Error: '+e.message);}
  finally{btn.textContent='⚡ Analyze Fleet Route';btn.disabled=false;}
}
function renderFleet(d){
  const res=document.getElementById('fleetResults'); res.style.display='block';
  const sc=d.safety_summary, sf=sc.Low>0?'#FF4444':sc.Medium>0?'#FFD700':'#39FF14';
  document.getElementById('fleetSummary').innerHTML=
    `<div class="fs-metric"><div class="fs-val">${d.total_segments}</div><div class="fs-lbl">Segments</div></div>
     <div class="fs-metric"><div class="fs-val">${d.total_energy_kwh}</div><div class="fs-lbl">Total kWh</div></div>
     <div class="fs-metric"><div class="fs-val">${d.avg_energy_kwh}</div><div class="fs-lbl">Avg kWh</div></div>
     <div class="fs-metric"><div class="fs-val" style="color:${sf}">${sc.Low>0?sc.Low+' DANGER':sc.Medium>0?sc.Medium+' CAUTION':'All SAFE'}</div><div class="fs-lbl">Safety</div></div>`;
  if(fleetChart) fleetChart.destroy();
  const cols=d.segments.map(s=>SAFETY_COLORS[s.safety]||'#00D4FF');
  fleetChart=new Chart(document.getElementById('fleetChart'),{type:'bar',
    data:{labels:d.segments.map((_,i)=>'Seg '+(i+1)),
      datasets:[{label:'Energy (kWh)',data:d.segments.map(s=>s.energy_kwh),
        backgroundColor:cols.map(c=>c+'66'),borderColor:cols,borderWidth:2,borderRadius:5}]},
    options:{plugins:{legend:{labels:{color:'#8892AA',font:{size:10}}}},
      scales:{x:{ticks:{color:'#E8EDF8',font:{size:10}},grid:{display:false}},
        y:{ticks:{color:'#8892AA'},grid:{color:'rgba(255,255,255,0.05)'}}}}});
  const sc2={High:'#39FF14',Medium:'#FFD700',Low:'#FF4444'};
  document.getElementById('fleetTable').innerHTML=`<table>
    <thead><tr><th>#</th><th>Surface</th><th>Conf</th><th>kWh</th><th>Wh/km</th><th>Safety</th><th>Score</th></tr></thead>
    <tbody>${d.segments.map((s,i)=>`<tr>
      <td>${i+1}</td><td>${s.label}</td><td>${s.confidence}%</td>
      <td><strong style="color:#00D4FF">${s.energy_kwh}</strong></td>
      <td>${s.wh_per_km}</td>
      <td><span class="safety-pill" style="color:${sc2[s.safety]};border-color:${sc2[s.safety]};background:${sc2[s.safety]}18">${s.safety}</span></td>
      <td>${s.quality_score}/100</td></tr>`).join('')}</tbody></table>`;
}

// ── HEATMAP ───────────────────────────────────────────────
function setupHeatmap(){
  const zone=document.getElementById('hmUploadZone'),
        inp=document.getElementById('hmFileInput'),
        btn=document.getElementById('addToMapBtn');
  if(!zone) return;
  zone.addEventListener('click',()=>inp.click());
  inp.addEventListener('change',()=>{
    const file = inp.files[0];
    if(file){
      document.getElementById('hmPreview').src=URL.createObjectURL(file);
      document.getElementById('hmPreview').style.display='block';
      document.getElementById('hmUploadInner').style.display='none';
      btn.disabled=false;
      
      // Extract GPS EXIF
      if(window.EXIF){
        EXIF.getData(file, function(){
          const lat = EXIF.getTag(this, "GPSLatitude");
          const lon = EXIF.getTag(this, "GPSLongitude");
          const latRef = EXIF.getTag(this, "GPSLatitudeRef") || "N";
          const lonRef = EXIF.getTag(this, "GPSLongitudeRef") || "E";
          
          if(lat && lon){
            const toDecimal = (gpsData, ref) => {
              const deg = gpsData[0].numerator / gpsData[0].denominator;
              const min = gpsData[1].numerator / gpsData[1].denominator;
              const sec = gpsData[2].numerator / gpsData[2].denominator;
              let dec = deg + (min / 60) + (sec / 3600);
              if(ref === "S" || ref === "W") dec = dec * -1;
              return dec;
            };
            
            const latDec = toDecimal(lat, latRef);
            const lonDec = toDecimal(lon, lonRef);
            
            document.getElementById('hmLat').value = latDec.toFixed(6);
            document.getElementById('hmLon').value = lonDec.toFixed(6);
            document.getElementById('hmLocation').value = 'EXIF GPS Location';
          }
        });
      }
    }
  });
  if(btn) btn.addEventListener('click',addToHeatmap);
}

// ── HEATMAP CITY LOOKUP ───────────────────────────────────
async function lookupHmCity(){
  const city=(document.getElementById('hmCityInput').value||'').trim();
  if(!city) return;
  const btn=document.getElementById('hmLocateBtn');
  const status=document.getElementById('hmCityStatus');
  btn.textContent='...'; btn.disabled=true;
  status.style.display='block'; status.textContent='Looking up...';
  status.style.background='rgba(0,212,255,0.08)'; status.style.color='#8892AA';
  try{
    const d=await(await fetch('/geocode?city='+encodeURIComponent(city))).json();
    if(d.success){
      document.getElementById('hmLat').value=d.lat.toFixed(6);
      document.getElementById('hmLon').value=d.lon.toFixed(6);
      const label=d.city+(d.state?', '+d.state:'')+(d.country?', '+d.country:'');
      document.getElementById('hmLocation').value=label;
      status.textContent='Found: '+label+' ('+d.lat.toFixed(4)+', '+d.lon.toFixed(4)+')';
      status.style.background='rgba(57,255,20,0.08)'; status.style.color='#39FF14';
    } else {
      status.textContent='Not found: '+d.error;
      status.style.background='rgba(255,68,68,0.08)'; status.style.color='#FF4444';
    }
  }catch(e){
    status.textContent='Error: '+e.message;
    status.style.background='rgba(255,68,68,0.08)'; status.style.color='#FF4444';
  }
  btn.textContent='📍 Locate'; btn.disabled=false;
}

function useClassifiedImage(){
  if(!lastClassifiedFile){
    alert('Please classify a road image first in the Classify tab.');
    return;
  }
  // Show preview in heatmap upload zone
  const preview=document.getElementById('hmPreview');
  const inner=document.getElementById('hmUploadInner');
  preview.src=URL.createObjectURL(lastClassifiedFile);
  preview.style.display='block'; inner.style.display='none';
  // Inject file into the hmFileInput via DataTransfer
  try{
    const dt=new DataTransfer();
    dt.items.add(lastClassifiedFile);
    document.getElementById('hmFileInput').files=dt.files;
  }catch(e){ /* DataTransfer not supported in older browsers — file still held in lastClassifiedFile */ }
  document.getElementById('addToMapBtn').disabled=false;
}

function initMap(){
  if(leafletMap||typeof L==='undefined') return;
  leafletMap=L.map('roadMap').setView([20.5937,78.9629],5);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
    {attribution:'© OpenStreetMap',maxZoom:18}).addTo(leafletMap);
}
async function addToHeatmap(){
  const file=document.getElementById('hmFileInput').files[0]||lastClassifiedFile;
  if(!file){ alert('Please upload or select a road image first.'); return; }

  const btn=document.getElementById('addToMapBtn');
  btn.textContent='Analyzing...'; btn.disabled=true;

  // Validate lat/lon
  const latVal = parseFloat(document.getElementById('hmLat').value);
  const lonVal = parseFloat(document.getElementById('hmLon').value);
  if(!latVal || !lonVal || latVal<6 || latVal>37 || lonVal<68 || lonVal>98){
    alert('Please search for a city first to get correct India coordinates, or enter valid lat/lon manually (India: lat 6–37, lon 68–98).');
    btn.textContent='📍 Analyze & Add to Map'; btn.disabled=false;
    return;
  }
  try{
    const form=new FormData();
    form.append('image',file);
    form.append('location',document.getElementById('hmLocation').value||'India');
    form.append('lat', latVal);
    form.append('lon', lonVal);
    const d=await(await fetch('/heatmap/add',{method:'POST',body:form})).json();
    if(d.success){
      if(!leafletMap) initMap();
      const e=d.entry, col=e.safety_color||'#FFD700';
      const icon=L.divIcon({html:`<div style="width:16px;height:16px;background:${col};border-radius:50%;border:2px solid #fff;box-shadow:0 0 8px ${col}88"></div>`,className:'',iconSize:[16,16],iconAnchor:[8,8]});
      L.marker([e.lat,e.lon],{icon}).addTo(leafletMap)
        .bindPopup(`<strong>${e.location}</strong><br/>${e.surface_label}<br/>Quality: ${e.quality_score}/100<br/>Safety: ${e.safety}`);
      leafletMap.setView([e.lat,e.lon],12);
      const list=document.getElementById('hmReadingsList');
      if(list.querySelector('[style*="text-align:center"]')) list.innerHTML='';
      const div=document.createElement('div'); div.className='hm-reading-item';
      div.innerHTML=`<div class="hm-dot" style="background:${col}"></div>
        <div class="hm-loc">${e.location}</div>
        <div class="hm-cls">${e.surface_label}</div>
        <div class="hm-score">${e.quality_score}/100</div>`;
      list.insertBefore(div,list.firstChild);
      document.getElementById('hmLocation').value='';
      document.getElementById('hmLat').value='';
      document.getElementById('hmLon').value='';
      document.getElementById('hmPreview').style.display='none';
      document.getElementById('hmUploadInner').style.display='block';
    } else alert('Error: '+d.error);
  }catch(e){alert('Error: '+e.message);}
  finally{btn.textContent='📍 Analyze & Add to Map';btn.disabled=false;}
}

// ── WEBCAM ────────────────────────────────────────────────
function setupWebcam(){
  const wb=document.getElementById('webcamBtn'),cb=document.getElementById('captureBtn'),
        sb=document.getElementById('stopCamBtn'),vid=document.getElementById('webcamVideo'),
        cvs=document.getElementById('webcamCanvas'),inner=document.getElementById('uploadInner'),
        prev=document.getElementById('previewImg'),clsBtn=document.getElementById('classifyBtn');
  if(!wb) return;
  wb.addEventListener('click',async()=>{
    try{
      webcamStream=await navigator.mediaDevices.getUserMedia({video:true});
      vid.srcObject=webcamStream; vid.style.display='block';
      inner.style.display='none'; prev.style.display='none';
      cb.style.display='inline-block'; sb.style.display='inline-block'; wb.style.display='none';
    }catch(e){alert('Camera error: '+e.message);}
  });
  cb.addEventListener('click',()=>{
    cvs.width=vid.videoWidth; cvs.height=vid.videoHeight;
    cvs.getContext('2d').drawImage(vid,0,0);
    cvs.toBlob(blob=>{
      const f=new File([blob],'webcam.jpg',{type:'image/jpeg'});
      document.getElementById('fileInput')._file=f;
      prev.src=URL.createObjectURL(f); prev.style.display='block';
      vid.style.display='none'; clsBtn.disabled=false;
      stopWebcam(); cb.style.display='none'; sb.style.display='none'; wb.style.display='inline-block';
    },'image/jpeg',0.92);
  });
  sb.addEventListener('click',()=>{
    stopWebcam(); vid.style.display='none';
    cb.style.display='none'; sb.style.display='none'; wb.style.display='inline-block';
    inner.style.display='flex';
  });
}
function stopWebcam(){
  if(webcamStream){webcamStream.getTracks().forEach(t=>t.stop());webcamStream=null;}
}

// ── PDF ───────────────────────────────────────────────────
function setupPdf(){
  const btn=document.getElementById('downloadPdfBtn'); if(!btn) return;
  btn.addEventListener('click',async()=>{
    if(!lastResult){alert('Classify a road image first.');return;}
    btn.textContent='Generating...'; btn.disabled=true;
    try{
      const r=await fetch('/report',{method:'POST',headers:{'Content-Type':'application/json'},
        body:JSON.stringify(lastResult)});
      if(!r.ok) throw new Error('PDF failed');
      const blob=await r.blob(), url=URL.createObjectURL(blob);
      Object.assign(document.createElement('a'),{href:url,download:'ev_routeiq_report.pdf'}).click();
      URL.revokeObjectURL(url);
    }catch(e){alert('PDF error: '+e.message);}
    finally{btn.textContent='📄 Download PDF Report';btn.disabled=false;}
  });
}

// ── HELPERS ───────────────────────────────────────────────
function fillFromRef(cls){
  const s=document.querySelector('#cmpRouteASegs .cmp-seg-surface');
  if(s) s.value=cls;
}