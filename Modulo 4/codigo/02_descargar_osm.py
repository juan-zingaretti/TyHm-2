"""Descarga de capas vectoriales de OpenStreetMap (Overpass API) para la zona piloto de Agrelo.

Uso: python 02_descargar_osm.py <carpeta_salida>
Capas: viñedos (landuse=vineyard), canales y acequias, rutas principales, localidades y bodegas.
Datos © colaboradores de OpenStreetMap, licencia ODbL.
"""
import json
import os
import sys

import requests

BBOX = (-33.16, -68.95, -33.08, -68.85)  # sur, oeste, norte, este (formato Overpass)
b = ",".join(str(x) for x in BBOX)
QUERY = f"""[out:json][timeout:90];
(
 way["landuse"="vineyard"]({b});
 relation["landuse"="vineyard"]({b});
 way["waterway"~"canal|ditch|drain|river|stream"]({b});
 way["highway"~"motorway|trunk|primary|secondary|tertiary"]({b});
 node["place"]({b});
 node["craft"="winery"]({b});
 way["craft"="winery"]({b});
);
out geom;"""

out = sys.argv[1]
os.makedirs(out, exist_ok=True)
r = requests.post("https://overpass-api.de/api/interpreter", data={"data": QUERY},
                  headers={"User-Agent": "TyHM2-student-project/1.0"}, timeout=180)
r.raise_for_status()
json.dump(r.json(), open(os.path.join(out, "raw.json"), "w"))
print("elementos:", len(r.json()["elements"]))
