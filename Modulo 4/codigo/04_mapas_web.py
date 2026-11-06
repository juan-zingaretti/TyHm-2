"""Genera los dos mapas web interactivos (Leaflet) del Módulo 4 con los datos embebidos.

Uso: python 04_mapas_web.py <carpeta_modulo4>
  - mapa cuarteles/index.html : cuarteles con semáforo, canales, influencia, bodegas, Voronoi, Delaunay.
  - mapa ndmi/index.html      : superposiciones NDVI / NDMI / ΔNDMI de Sentinel-2.
"""
import json
import os
import sys

M4 = sys.argv[1]
V = os.path.join(M4, "datos", "vector")


def gj(n):
    return open(os.path.join(V, n), encoding="utf8").read()


HEAD = """<!DOCTYPE html>
<html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>
 html,body{{margin:0;height:100%;font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif}}
 #map{{position:absolute;top:56px;bottom:0;left:0;right:0}}
 header{{height:56px;display:flex;align-items:center;gap:12px;padding:0 16px;background:#1f3a2b;color:#fff}}
 header h1{{font-size:16px;margin:0;font-weight:600}} header span{{font-size:13px;opacity:.8}}
 .legend{{background:#fff;padding:8px 10px;border-radius:6px;box-shadow:0 1px 4px rgba(0,0,0,.3);font-size:12px;line-height:1.5;max-width:230px}}
 .legend i{{display:inline-block;width:12px;height:12px;margin-right:6px;vertical-align:-1px;border-radius:2px}}
 .legend .bar{{height:10px;border-radius:2px;margin:4px 0}}
 .leaflet-popup-content{{font-size:13px}} .leaflet-popup-content td{{padding:1px 6px 1px 0}}
</style></head><body>
<header><h1>{title}</h1><span>SatellAgro · Grupo λ (Grupo 2) · TyHM II 2026</span></header>
<div id="map"></div>
<script>
const map = L.map('map');
const sat = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{{z}}/{{y}}/{{x}}',
  {{maxZoom:18, attribution:'Imágenes © Esri, Maxar, Earthstar Geographics'}}).addTo(map);
const osm = L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png',
  {{maxZoom:19, attribution:'© colaboradores de OpenStreetMap (ODbL)'}});
"""

# ------------------------------------------------------------------ mapa 1: cuarteles
m1 = HEAD.format(title="Agrelo: cuarteles de viñedo y red de riego") + f"""
const cuarteles = {gj('cuarteles_vinedo_semaforo.geojson')};
const canales = {gj('canales.geojson')};
const influencia = {gj('influencia_canales_300m.geojson')};
const rutas = {gj('rutas.geojson')};
const bodegas = {gj('bodegas.geojson')};
const voronoi = {gj('voronoi_bodegas.geojson')};
const delaunay = {gj('delaunay_bodegas.geojson')};
const lugares = {gj('localidades.geojson')};
const COL = {{"Sin señales de estrés":"#2e9e4f","Atención":"#f2c230","Posible estrés hídrico":"#d63b2f",
  "No evaluable aún":"#9aa3ab","Juntando historia":"#6c8ebf","Sin dato nuevo":"#5a5a5a","A revisar":"#8e44ad"}};
const f = v => (v===null||v===undefined) ? '—' : v.toFixed(3).replace('.',',');
const lCuart = L.geoJSON(cuarteles, {{
  style: ft => ({{color:'#fff', weight:1, fillColor:COL[ft.properties.estado]||'#999', fillOpacity:.55}}),
  onEachFeature: (ft, l) => {{ const p = ft.properties; l.bindPopup(
   `<b>Cuartel ${{p.id}}</b> ${{p.nombre?'· '+p.nombre:''}}<br><b style="color:${{COL[p.estado]}}">${{p.estado}}</b>
    · confianza ${{p.confianza}} · imagen ${{p.fecha_imagen}}<table>
    <tr><td>Superficie</td><td>${{String(p.area_ha).replace('.',',')}} ha</td></tr>
    <tr><td>NDVI hoy</td><td>${{f(p.ndvi_20261105)}}</td></tr>
    <tr><td>NDMI hoy</td><td>${{f(p.ndmi_20261105)}}</td></tr>
    <tr><td>NDMI mediana 30 d</td><td>${{f(p.ndmi_mediana30d)}}</td></tr>
    <tr><td>ΔNDMI</td><td>${{f(p.delta_ndmi)}}</td></tr>
    <tr><td>NDVI 04/01/2026</td><td>${{f(p.ndvi_20260104)}}</td></tr></table>
    <small>Umbrales ilustrativos, no calibrados en campo.</small>`); }}
}}).addTo(map);
const lInf = L.geoJSON(influencia, {{style:{{color:'#1e88e5', weight:1, fillOpacity:.12, dashArray:'4'}},
  onEachFeature:(ft,l)=>l.bindPopup(`<b>${{ft.properties.canal}}</b><br>Buffer 300 m: ${{ft.properties.area_ha}} ha<br>Viñedo dentro: ${{ft.properties.vinedo_osm_ha}} ha`)}});
const lCan = L.geoJSON(canales, {{style: ft => ({{color: ft.properties.tipo==='canal' ? '#0d47a1' : '#42a5f5', weight: ft.properties.tipo==='canal'?3:1.5}}),
  onEachFeature:(ft,l)=>l.bindTooltip(ft.properties.nombre)}}).addTo(map);
const lRut = L.geoJSON(rutas, {{style:{{color:'#ff8f00', weight:2}}, onEachFeature:(ft,l)=>ft.properties.nombre&&l.bindTooltip(ft.properties.nombre)}}).addTo(map);
const lVor = L.geoJSON(voronoi, {{style:{{color:'#ab47bc', weight:2, fillOpacity:0}},
  onEachFeature:(ft,l)=>l.bindPopup(`<b>Área de influencia: ${{ft.properties.bodega}}</b><br>Celda: ${{ft.properties.area_celda_ha}} ha<br>Viñedo OSM en la celda: ${{ft.properties.vinedo_osm_ha}} ha`)}});
const lDel = L.geoJSON(delaunay, {{style:{{color:'#6a1b9a', weight:1, dashArray:'2 4'}}, onEachFeature:(ft,l)=>l.bindTooltip(ft.properties.largo_km+' km')}});
const lBod = L.geoJSON(bodegas, {{pointToLayer:(ft,ll)=>L.circleMarker(ll,{{radius:6,color:'#fff',weight:2,fillColor:'#7b1fa2',fillOpacity:1}}),
  onEachFeature:(ft,l)=>l.bindTooltip(ft.properties.nombre)}}).addTo(map);
const lLug = L.geoJSON(lugares, {{pointToLayer:(ft,ll)=>L.marker(ll), onEachFeature:(ft,l)=>l.bindTooltip(ft.properties.nombre,{{permanent:ft.properties.tipo==='village'}})}}).addTo(map);
L.control.layers({{'Satélite (Esri)':sat,'OpenStreetMap':osm}}, {{
 'Cuarteles · semáforo 05/11/2026':lCuart, 'Canales y acequias':lCan, 'Influencia de canales (300 m)':lInf,
 'Rutas':lRut, 'Bodegas':lBod, 'Voronoi de bodegas':lVor, 'Delaunay de bodegas':lDel, 'Localidades':lLug}}, {{collapsed: window.innerWidth < 700}}).addTo(map);
map.fitBounds(lCuart.getBounds());
const lg = L.control({{position:'bottomleft'}});
lg.onAdd = () => {{ const d = L.DomUtil.create('div','legend');
  d.innerHTML = '<b>Estado SatellAgro (05/11/2026)</b><br>' + Object.entries(COL).map(([k,c])=>`<i style="background:${{c}}"></i>${{k}}`).join('<br>')
   + '<br><small>Cuartel = polígono landuse=vineyard de OSM. Clic para ver datos.</small>'; return d; }};
lg.addTo(map);
L.control.scale({{imperial:false}}).addTo(map);
</script></body></html>"""
open(os.path.join(M4, "mapa cuarteles", "index.html"), "w", encoding="utf8").write(m1)

# ------------------------------------------------------------------ mapa 2: NDVI / NDMI
b = json.load(open(os.path.join(M4, "mapa ndmi", "capas_bounds.json")))
m2 = HEAD.format(title="Agrelo: agua y verdor desde Sentinel-2") + f"""
const B = {json.dumps(b)};
const op = {{opacity:.85}};
const capas = {{
 'NDMI 05/11/2026 (agua del canopeo)': L.imageOverlay('ndmi_20261105.png', B.ndmi_hoy, op),
 'ΔNDMI vs mediana 30 días': L.imageOverlay('delta_ndmi_20261105.png', B.delta, op),
 'NDMI 04/01/2026 (pleno verano)': L.imageOverlay('ndmi_20260104.png', B.ndmi_ene, op),
 'NDVI 05/11/2026': L.imageOverlay('ndvi_20261105.png', B.ndvi_hoy, op),
 'NDVI 04/01/2026': L.imageOverlay('ndvi_20260104.png', B.ndvi_ene, op),
 'NDVI 05/11/2024 (hace dos años)': L.imageOverlay('ndvi_20241105.png', B.ndvi_2024, op)
}};
map.fitBounds(B.ndmi_hoy);
capas['NDMI 05/11/2026 (agua del canopeo)'].addTo(map);
const cuarteles = {gj('cuarteles_vinedo_semaforo.geojson')};
const lC = L.geoJSON(cuarteles, {{style:{{color:'#fff', weight:1, fill:false}},
  onEachFeature:(ft,l)=>l.bindPopup(`<b>Cuartel ${{ft.properties.id}}</b><br>${{ft.properties.estado}}<br>NDMI ${{ft.properties.ndmi_20261105}} · NDVI ${{ft.properties.ndvi_20261105}}`)}}).addTo(map);
const caso = L.circle([-33.10120, -68.93831], {{radius:120, color:'#ff00ff', weight:2, fill:false}})
  .bindPopup('<b>Caso del Módulo 3</b><br>NDVI 0,45 → 0,16 y NDMI 0,21 → −0,01 en 5 días:<br>menos hojas (corte), no falta de agua.').addTo(map);
L.control.layers({{'Satélite (Esri)':sat,'OpenStreetMap':osm}}, Object.assign({{}}, capas, {{'Contorno de cuarteles':lC, 'Caso Módulo 3':caso}}), {{collapsed: window.innerWidth < 700}}).addTo(map);
map.fitBounds(B.ndmi_hoy);
const lg = L.control({{position:'bottomleft'}});
lg.onAdd = () => {{ const d = L.DomUtil.create('div','legend');
 d.innerHTML = `<b>NDMI</b> (−0,3 a 0,4)<div class="bar" style="background:linear-gradient(90deg,#543005,#bf812d,#f6e8c3,#c7eae5,#35978f,#003c30)"></div>
 <b>NDVI</b> (0 a 0,8)<div class="bar" style="background:linear-gradient(90deg,#a50026,#f46d43,#fee08b,#d9ef8b,#66bd63,#006837)"></div>
 <b>ΔNDMI</b> (−0,2 a +0,2)<div class="bar" style="background:linear-gradient(90deg,#67001f,#d6604d,#f7f7f7,#4393c3,#053061)"></div>
 <label>Opacidad <input id="op" type="range" min="0" max="100" value="85"></label>
 <br><small>Sentinel-2 L2A (ESA Copernicus) vía Earth Search. Máscara SCL: solo vegetación y suelo.</small>`;
 L.DomEvent.disableClickPropagation(d); return d; }};
lg.addTo(map);
document.getElementById('op').addEventListener('input', e => Object.values(capas).forEach(c => c.setOpacity(e.target.value/100)));
L.control.scale({{imperial:false}}).addTo(map);
</script></body></html>"""
open(os.path.join(M4, "mapa ndmi", "index.html"), "w", encoding="utf8").write(m2)
print("mapas generados")
