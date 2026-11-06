"""Lámina estática de la Actividad 1 (para el informe en PDF): capas vectoriales sobre la imagen en color real.

Uso: python 05_lamina_vectorial.py <carpeta_sentinel2> <carpeta_modulo4>
"""
import json
import os
import sys
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)
import matplotlib
matplotlib.use("Agg")
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np
import pyproj
import rasterio
from shapely.geometry import shape
from shapely.ops import transform

S2, M4 = sys.argv[1], sys.argv[2]
V = os.path.join(M4, "datos", "vector")
tr = pyproj.Transformer.from_crs(4326, 32719, always_xy=True).transform
COL = {"Sin señales de estrés": "#2e9e4f", "Atención": "#f2c230", "Posible estrés hídrico": "#d63b2f",
       "No evaluable aún": "#c9ced3", "Juntando historia": "#6c8ebf", "Sin dato nuevo": "#5a5a5a", "A revisar": "#8e44ad"}


def capa(n):
    return [(transform(tr, shape(f["geometry"])), f["properties"]) for f in
            json.load(open(os.path.join(V, n), encoding="utf8"))["features"]]


with rasterio.open(os.path.join(S2, "20261105_visual.tif")) as s:
    img = np.moveaxis(s.read(), 0, -1); b = s.bounds
fig, axs = plt.subplots(1, 2, figsize=(15, 7.6))
for ax in axs:
    ax.imshow(img, extent=(b.left, b.right, b.bottom, b.top), alpha=.75)
    ax.set_xlim(b.left, b.right); ax.set_ylim(b.bottom, b.top); ax.set_xticks([]); ax.set_yticks([])


def poly(ax, g, **kw):
    for p in getattr(g, "geoms", [g]):
        if p.geom_type == "Polygon":
            ax.add_patch(mpatches.Polygon(np.array(p.exterior.coords), closed=True, **kw))


def line(ax, g, **kw):
    for l in getattr(g, "geoms", [g]):
        if l.geom_type == "LineString":
            ax.plot(*l.xy, **kw)


# panel izquierdo: semáforo + canales + buffers
a = axs[0]
for g, p in capa("influencia_canales_300m.geojson"):
    poly(a, g, fc="#1e88e5", ec="#1e88e5", alpha=.15, lw=.8)
for g, p in capa("cuarteles_vinedo_semaforo.geojson"):
    poly(a, g, fc=COL[p["estado"]], ec="white", alpha=.6, lw=.6)
for g, p in capa("canales.geojson"):
    line(a, g, color="#0d47a1" if p["tipo"] == "canal" else "#42a5f5", lw=2.2 if p["tipo"] == "canal" else 1)
for g, p in capa("rutas.geojson"):
    line(a, g, color="#ff8f00", lw=1.5)
for g, p in capa("localidades.geojson"):
    if p["tipo"] == "village":
        a.plot(g.x, g.y, "k^", ms=8); a.text(g.x + 150, g.y + 150, p["nombre"], fontsize=11, weight="bold")
a.set_title("Cuarteles de vid con semáforo SatellAgro (05/11/2026), canales y buffer de 300 m")
a.legend(handles=[mpatches.Patch(color=COL["Sin señales de estrés"], label="Sin señales de estrés (71)"),
                  mpatches.Patch(color=COL["No evaluable aún"], label="No evaluable aún (10)"),
                  Line2D([], [], color="#0d47a1", lw=2.2, label="Canal (Flores, Corvalán)"),
                  Line2D([], [], color="#42a5f5", lw=1, label="Acequia"),
                  mpatches.Patch(color="#1e88e5", alpha=.25, label="Influencia 300 m"),
                  Line2D([], [], color="#ff8f00", lw=1.5, label="Rutas (RN40, RN7)")],
         loc="lower right", fontsize=8.5, framealpha=.9)

# panel derecho: bodegas, Voronoi, Delaunay
a = axs[1]
for g, p in capa("cuarteles_vinedo_semaforo.geojson"):
    poly(a, g, fc="#2e9e4f", ec="none", alpha=.35)
for g, p in capa("voronoi_bodegas.geojson"):
    poly(a, g, fc="none", ec="#ab47bc", lw=2)
for g, p in capa("delaunay_bodegas.geojson"):
    line(a, g, color="#6a1b9a", lw=1, ls="--")
for g, p in capa("bodegas.geojson"):
    a.plot(g.x, g.y, "o", ms=8, mfc="#7b1fa2", mec="white", mew=1.5)
    dx, dy, ha = {"Bodega Favre": (120, -380, "left"), "Bodega Norton": (-120, 160, "right"),
                  "Bodega Ruca Malen": (-120, -380, "right")}.get(p["nombre"], (120, 120, "left"))
    a.text(g.x + dx, g.y + dy, p["nombre"], fontsize=7.5, color="white", ha=ha,
           bbox=dict(fc="#4a148c", ec="none", alpha=.75, pad=1.2))
a.set_title("Bodegas: polígonos de Voronoi y triangulación de Delaunay")
a.legend(handles=[Line2D([], [], color="#ab47bc", lw=2, label="Voronoi (área de influencia)"),
                  Line2D([], [], color="#6a1b9a", lw=1, ls="--", label="Delaunay (vecindad)"),
                  mpatches.Patch(color="#2e9e4f", alpha=.35, label="Viñedo (OSM)")],
         loc="lower right", fontsize=8.5, framealpha=.9)
# escala de 2 km
for ax in axs:
    x0, y0 = b.left + 400, b.bottom + 400
    ax.plot([x0, x0 + 2000], [y0, y0], color="white", lw=4); ax.text(x0 + 1000, y0 + 180, "2 km", color="white", ha="center", weight="bold")
fig.tight_layout()
fig.savefig(os.path.join(M4, "figuras", "lamina_actividad1.png"), dpi=130)
print("ok")
