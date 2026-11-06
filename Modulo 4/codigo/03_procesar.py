"""Procesamiento SIG de la zona piloto de SatellAgro (Agrelo, Luján de Cuyo).

Uso: python 03_procesar.py <carpeta_sentinel2> <carpeta_osm> <carpeta_modulo4>

Hace en Python los mismos pasos que en QGIS:
  1. Capas vectoriales OSM -> GeoJSON (EPSG:4326) y áreas en EPSG:32719 (UTM 19S).
  2. Índices NDVI (10 m) y NDMI (20 m) con la máscara SCL oficial de ESA.
  3. Estadística zonal por cuartel de viñedo y semáforo SatellAgro del 05/11/2026.
  4. Comparación de vegetación vigorosa nov-2024 vs nov-2026 (en hectáreas).
  5. Voronoi y Delaunay de bodegas, y área de influencia (buffer) de los canales.
  6. Superposiciones PNG reproyectadas para los mapas web (Leaflet).
"""
import json
import os
import sys
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pyproj
import rasterio
from rasterio.features import rasterize
from rasterio.warp import Resampling, calculate_default_transform, reproject
from shapely import delaunay_triangles, voronoi_polygons
from shapely.geometry import (LineString, MultiPoint, Point, Polygon, box, mapping)
from shapely.ops import linemerge, polygonize, transform as stransform, unary_union
from PIL import Image

S2, OSM, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
VEC = os.path.join(OUT, "datos", "vector")
RAS = os.path.join(OUT, "datos", "raster")
FIG = os.path.join(OUT, "figuras")
for d in (VEC, RAS, FIG, os.path.join(OUT, "mapa ndmi")):
    os.makedirs(d, exist_ok=True)

BBOX = (-68.95, -33.16, -68.85, -33.08)
FECHAS = ["20241105", "20260104", "20260926", "20261006", "20261031", "20261105"]
HOY = "20261105"
BASE_30D = ["20261006", "20261031"]  # imágenes de los 30 días previos al 05/11/2026
to_utm = pyproj.Transformer.from_crs(4326, 32719, always_xy=True).transform
to_geo = pyproj.Transformer.from_crs(32719, 4326, always_xy=True).transform
area_bbox = box(*BBOX)
resumen = {}

# ---------------------------------------------------------------- 1. vectores OSM
raw = json.load(open(os.path.join(OSM, "raw.json"), encoding="utf8"))["elements"]


def line_of(way):
    return LineString([(p["lon"], p["lat"]) for p in way["geometry"]])


vinedos, canales, rutas, lugares, bodegas = [], [], [], [], {}
for e in raw:
    t = e.get("tags", {})
    if t.get("landuse") == "vineyard":
        if e["type"] == "way" and len(e["geometry"]) >= 4:
            g = Polygon([(p["lon"], p["lat"]) for p in e["geometry"]])
        elif e["type"] == "relation":
            outer = [line_of(m) for m in e["members"] if m.get("role") == "outer" and "geometry" in m]
            inner = [line_of(m) for m in e["members"] if m.get("role") == "inner" and "geometry" in m]
            g = unary_union(list(polygonize(linemerge(outer))))
            if inner:
                g = g.difference(unary_union(list(polygonize(linemerge(inner)))))
        else:
            continue
        g = g.buffer(0).intersection(area_bbox)
        if not g.is_empty:
            vinedos.append({"osm_id": f"{e['type']}/{e['id']}", "nombre": t.get("name", ""), "geom": g})
    elif t.get("waterway") in ("canal", "ditch", "drain", "river", "stream"):
        canales.append({"nombre": t.get("name", "(sin nombre)"), "tipo": t["waterway"],
                        "geom": line_of(e).intersection(area_bbox)})
    elif "highway" in t:
        rutas.append({"nombre": t.get("name", ""), "tipo": t["highway"], "ref": t.get("ref", ""),
                      "geom": line_of(e).intersection(area_bbox)})
    elif "place" in t and e["type"] == "node":
        lugares.append({"nombre": t.get("name", ""), "tipo": t["place"], "geom": Point(e["lon"], e["lat"])})
    if t.get("craft") == "winery" and t.get("name"):
        p = Point(e["lon"], e["lat"]) if e["type"] == "node" else Polygon(
            [(q["lon"], q["lat"]) for q in e["geometry"]]).centroid
        bodegas.setdefault(t["name"], p)

for i, v in enumerate(vinedos, 1):
    v["id"] = i
    v["area_ha"] = round(stransform(to_utm, v["geom"]).area / 1e4, 2)


def write_geojson(name, feats, props):
    fc = {"type": "FeatureCollection", "features": [
        {"type": "Feature", "geometry": mapping(f["geom"]), "properties": {k: f.get(k) for k in props}}
        for f in feats if not f["geom"].is_empty]}
    json.dump(fc, open(os.path.join(VEC, name), "w", encoding="utf8"), ensure_ascii=False)


bod = [{"nombre": k, "geom": v} for k, v in sorted(bodegas.items())]
write_geojson("canales.geojson", canales, ["nombre", "tipo"])
write_geojson("rutas.geojson", rutas, ["nombre", "tipo", "ref"])
write_geojson("localidades.geojson", lugares, ["nombre", "tipo"])
write_geojson("bodegas.geojson", bod, ["nombre"])

# ---------------------------------------------------------------- 2. índices
def read(fecha, banda):
    with rasterio.open(os.path.join(S2, f"{fecha}_{banda}.tif")) as s:
        return s.read(1).astype("float32"), s.profile


_, prof10 = read(HOY, "red")
_, prof20 = read(HOY, "scl")
H20, W20 = prof20["height"], prof20["width"]
VALIDAS = (4, 5)  # SCL: 4 vegetación, 5 suelo desnudo

ndvi10, ndvi20, ndmi20, valid20 = {}, {}, {}, {}
with np.errstate(divide="ignore", invalid="ignore"):
    for f in FECHAS:
        red, _ = read(f, "red"); nir, _ = read(f, "nir")
        n8a, _ = read(f, "nir08"); sw, _ = read(f, "swir16"); scl, _ = read(f, "scl")
        red, nir, n8a, sw = red / 1e4, nir / 1e4, n8a / 1e4, sw / 1e4  # offset BOA ya aplicado
        ok20 = np.isin(scl, VALIDAS) & (n8a > 0) & (sw > 0)
        ok10 = np.kron(ok20, np.ones((2, 2), bool))[: red.shape[0], : red.shape[1]] & (red > 0)
        ndvi10[f] = np.where(ok10, (nir - red) / (nir + red), np.nan)
        r20 = red.reshape(H20, 2, W20, 2).mean(axis=(1, 3)); n20 = nir.reshape(H20, 2, W20, 2).mean(axis=(1, 3))
        ndvi20[f] = np.where(ok20, (n20 - r20) / (n20 + r20), np.nan)
        ndmi20[f] = np.where(ok20, (n8a - sw) / (n8a + sw), np.nan)
        valid20[f] = ok20
        resumen.setdefault("validez_scl", {})[f] = round(float(ok20.mean()), 4)


def save_tif(name, arr, prof):
    p = prof.copy(); p.update(dtype="float32", count=1, nodata=np.nan, compress="deflate", predictor=3)
    with rasterio.open(os.path.join(RAS, name), "w", **p) as d:
        d.write(np.round(arr, 4).astype("float32"), 1)


base_ndmi = np.nanmedian(np.stack([ndmi20[f] for f in BASE_30D]), axis=0)
delta_ndmi = ndmi20[HOY] - base_ndmi
base_ndvi = np.nanmedian(np.stack([ndvi20[f] for f in BASE_30D]), axis=0)
delta_ndvi = ndvi20[HOY] - base_ndvi
for f in ("20241105", "20260104", HOY):
    save_tif(f"NDVI_{f}_10m.tif", ndvi10[f], prof10)
    save_tif(f"NDMI_{f}_20m.tif", ndmi20[f], prof20)
save_tif(f"DeltaNDMI_{HOY}_vs_mediana30d_20m.tif", delta_ndmi, prof20)

# ---------------------------------------------------------------- 3. zonal + semáforo
geoms_utm = [stransform(to_utm, v["geom"]) for v in vinedos]
ids = rasterize([(g, v["id"]) for g, v in zip(geoms_utm, vinedos)], out_shape=(H20, W20),
                transform=prof20["transform"], fill=0, dtype="int32")


def estado(ndvi_hoy, d, frac_valida, n_base):
    """Lógica de estados de SatellAgro con umbrales ilustrativos (no calibrados en campo)."""
    if frac_valida < 0.5:
        return "Sin dato nuevo"
    if n_base < 2:
        return "Juntando historia"
    if ndvi_hoy < 0.25:
        return "No evaluable aún"
    if abs(d) > 0.30:
        return "A revisar"
    if d <= -0.10:
        return "Posible estrés hídrico"
    if d <= -0.05:
        return "Atención"
    return "Sin señales de estrés"


for v in vinedos:
    m = ids == v["id"]
    v["pixeles_20m"] = int(m.sum())
    if v["pixeles_20m"] == 0:
        v["estado"] = "Sin dato nuevo"; continue
    for f in FECHAS:
        v[f"ndvi_{f}"] = None if np.all(np.isnan(ndvi20[f][m])) else round(float(np.nanmean(ndvi20[f][m])), 3)
        v[f"ndmi_{f}"] = None if np.all(np.isnan(ndmi20[f][m])) else round(float(np.nanmean(ndmi20[f][m])), 3)
    frac = float(valid20[HOY][m].mean())
    serie_base = [v[f"ndmi_{f}"] for f in BASE_30D if v[f"ndmi_{f}"] is not None]
    med = float(np.median(serie_base)) if serie_base else np.nan
    v["ndmi_mediana30d"] = round(med, 3) if serie_base else None
    v["delta_ndmi"] = round(v[f"ndmi_{HOY}"] - med, 3) if serie_base and v[f"ndmi_{HOY}"] is not None else None
    nb = [v[f"ndvi_{f}"] for f in BASE_30D if v[f"ndvi_{f}"] is not None]
    v["delta_ndvi"] = round(v[f"ndvi_{HOY}"] - float(np.median(nb)), 3) if nb and v[f"ndvi_{HOY}"] is not None else None
    v["estado"] = estado(v[f"ndvi_{HOY}"] or 0, v["delta_ndmi"] or 0, frac, len(serie_base))
    v["confianza"] = "alta" if frac > 0.95 else ("media" if frac > 0.7 else "baja")
    v["fecha_imagen"] = "2026-11-05"

props = ["id", "osm_id", "nombre", "area_ha", "pixeles_20m", "estado", "confianza", "fecha_imagen",
         "ndvi_20261105", "ndmi_20261105", "ndmi_mediana30d", "delta_ndmi", "delta_ndvi",
         "ndvi_20260104", "ndmi_20260104", "ndvi_20241105", "ndmi_20241105"]
write_geojson("cuarteles_vinedo_semaforo.geojson", vinedos, props)
from collections import Counter
resumen["vinedos"] = {"n": len(vinedos), "area_total_ha": round(sum(v["area_ha"] for v in vinedos), 1),
                      "estados": Counter(v["estado"] for v in vinedos),
                      "area_por_estado_ha": {k: round(sum(v["area_ha"] for v in vinedos if v["estado"] == k), 1)
                                             for k in set(v["estado"] for v in vinedos)}}
serie = {}
for f in FECHAS:
    mv = ids > 0
    serie[f] = {"ndvi": round(float(np.nanmean(ndvi20[f][mv])), 3), "ndmi": round(float(np.nanmean(ndmi20[f][mv])), 3)}
resumen["serie_media_vinedos"] = serie

# ---------------------------------------------------------------- 4. comparación 2024 vs 2026
PIX10_HA = 0.01
vig = {}
for f in ("20241105", "20260104", HOY):
    a = ndvi10[f]
    vig[f] = {"vigorosa_ndvi_gt_0.4_ha": round(float(np.nansum(a > 0.4)) * PIX10_HA, 1),
              "suelo_o_rala_ndvi_lt_0.2_ha": round(float(np.nansum(a < 0.2)) * PIX10_HA, 1),
              "ndvi_medio": round(float(np.nanmean(a)), 3)}
    ids10 = np.kron(ids, np.ones((2, 2), "int32"))[: a.shape[0], : a.shape[1]]
    vig[f]["vigorosa_en_vinedos_osm_ha"] = round(float(np.nansum((a > 0.4) & (ids10 > 0))) * PIX10_HA, 1)
resumen["vegetacion_vigorosa"] = vig
resumen["area_recorte_ha"] = round(prof10["width"] * prof10["height"] * PIX10_HA, 1)

# ---------------------------------------------------------------- 5. Voronoi, Delaunay, buffers
marco_utm = stransform(to_utm, area_bbox)
pts_utm = MultiPoint([stransform(to_utm, b["geom"]) for b in bod])
vor = voronoi_polygons(pts_utm, extend_to=marco_utm)
vin_utm = unary_union(geoms_utm)
celdas = []
for cell in vor.geoms:
    cell = cell.intersection(marco_utm)
    dueno = next(b for b in bod if stransform(to_utm, b["geom"]).within(cell.buffer(1)))
    celdas.append({"bodega": dueno["nombre"], "area_celda_ha": round(cell.area / 1e4, 1),
                   "vinedo_osm_ha": round(cell.intersection(vin_utm).area / 1e4, 1),
                   "geom": stransform(to_geo, cell)})
write_geojson("voronoi_bodegas.geojson", celdas, ["bodega", "area_celda_ha", "vinedo_osm_ha"])
tri = delaunay_triangles(pts_utm, only_edges=True)
aristas = [{"largo_km": round(l.length / 1000, 2), "geom": stransform(to_geo, l)} for l in tri.geoms]
write_geojson("delaunay_bodegas.geojson", aristas, ["largo_km"])
resumen["voronoi"] = sorted([{k: c[k] for k in ("bodega", "area_celda_ha", "vinedo_osm_ha")} for c in celdas],
                            key=lambda c: -c["vinedo_osm_ha"])
resumen["delaunay_largo_medio_km"] = round(float(np.mean([a["largo_km"] for a in aristas])), 2)

BUF = 300
zonas = []
for nombre in sorted(set(c["nombre"] for c in canales)):
    lin = unary_union([stransform(to_utm, c["geom"]) for c in canales if c["nombre"] == nombre])
    z = lin.buffer(BUF).intersection(marco_utm)
    zonas.append({"canal": nombre, "largo_km": round(lin.length / 1000, 2), "buffer_m": BUF,
                  "area_ha": round(z.area / 1e4, 1), "vinedo_osm_ha": round(z.intersection(vin_utm).area / 1e4, 1),
                  "geom": stransform(to_geo, z)})
write_geojson("influencia_canales_300m.geojson", zonas, ["canal", "largo_km", "buffer_m", "area_ha", "vinedo_osm_ha"])
resumen["canales"] = [{k: z[k] for k in ("canal", "largo_km", "area_ha", "vinedo_osm_ha")} for z in zonas]

# ---------------------------------------------------------------- 6. PNG para mapas web
def to_png(arr, prof, cmap, vmin, vmax, name):
    src_crs = prof["crs"]
    tr, w, h = calculate_default_transform(src_crs, "EPSG:4326", prof["width"], prof["height"], *_bounds(prof))
    dst = np.full((h, w), np.nan, "float32")
    reproject(arr.astype("float32"), dst, src_transform=prof["transform"], src_crs=src_crs, src_nodata=np.nan,
              dst_transform=tr, dst_crs="EPSG:4326", dst_nodata=np.nan, resampling=Resampling.nearest)
    rgba = (plt.get_cmap(cmap)(np.clip((dst - vmin) / (vmax - vmin), 0, 1)) * 255).astype("uint8")
    rgba[np.isnan(dst), 3] = 0
    Image.fromarray(rgba).save(os.path.join(OUT, "mapa ndmi", name), optimize=True)
    west, north = tr.c, tr.f
    return [[north + h * tr.e, west], [north, west + w * tr.a]]


def _bounds(prof):
    t = prof["transform"]
    return (t.c, t.f + prof["height"] * t.e, t.c + prof["width"] * t.a, t.f)


capas = {}
capas["ndvi_hoy"] = to_png(ndvi10[HOY], prof10, "RdYlGn", 0.0, 0.8, "ndvi_20261105.png")
capas["ndvi_2024"] = to_png(ndvi10["20241105"], prof10, "RdYlGn", 0.0, 0.8, "ndvi_20241105.png")
capas["ndvi_ene"] = to_png(ndvi10["20260104"], prof10, "RdYlGn", 0.0, 0.8, "ndvi_20260104.png")
capas["ndmi_hoy"] = to_png(ndmi20[HOY], prof20, "BrBG", -0.3, 0.4, "ndmi_20261105.png")
capas["ndmi_ene"] = to_png(ndmi20["20260104"], prof20, "BrBG", -0.3, 0.4, "ndmi_20260104.png")
capas["delta"] = to_png(delta_ndmi, prof20, "RdBu", -0.2, 0.2, "delta_ndmi_20261105.png")
json.dump(capas, open(os.path.join(OUT, "mapa ndmi", "capas_bounds.json"), "w"), indent=1)

# ---------------------------------------------------------------- figuras para el informe
fechas_lbl = ["05/11/24", "04/01/26", "26/09/26", "06/10/26", "31/10/26", "05/11/26"]
fig, ax = plt.subplots(figsize=(8, 3.6))
ax.plot(fechas_lbl, [serie[f]["ndvi"] for f in FECHAS], "o-", color="#3a7d44", label="NDVI medio (viñedos)")
ax.plot(fechas_lbl, [serie[f]["ndmi"] for f in FECHAS], "s-", color="#2c6e9b", label="NDMI medio (viñedos)")
ax.set_ylabel("Índice"); ax.grid(alpha=.3); ax.legend(frameon=False)
ax.set_title("Viñedos OSM de Agrelo: NDVI y NDMI medios por fecha (Sentinel-2 L2A)")
fig.tight_layout(); fig.savefig(os.path.join(FIG, "serie_indices_vinedos.png"), dpi=150); plt.close(fig)

fig, axs = plt.subplots(1, 3, figsize=(12, 4.2))
for ax, f, t in zip(axs, ("20241105", "20260104", HOY), ("05/11/2024", "04/01/2026", "05/11/2026")):
    im = ax.imshow(ndvi10[f], cmap="RdYlGn", vmin=0, vmax=0.8); ax.set_title(f"NDVI {t}"); ax.axis("off")
fig.colorbar(im, ax=axs, shrink=.8, label="NDVI")
fig.savefig(os.path.join(FIG, "ndvi_tres_fechas.png"), dpi=130, bbox_inches="tight"); plt.close(fig)

fig, axs = plt.subplots(1, 2, figsize=(10, 4.6))
im0 = axs[0].imshow(ndmi20[HOY], cmap="BrBG", vmin=-0.3, vmax=0.4); axs[0].set_title("NDMI 05/11/2026"); axs[0].axis("off")
fig.colorbar(im0, ax=axs[0], shrink=.8)
im1 = axs[1].imshow(delta_ndmi, cmap="RdBu", vmin=-0.2, vmax=0.2); axs[1].set_title("ΔNDMI vs mediana 30 días"); axs[1].axis("off")
fig.colorbar(im1, ax=axs[1], shrink=.8)
fig.savefig(os.path.join(FIG, "ndmi_y_delta.png"), dpi=130, bbox_inches="tight"); plt.close(fig)

fig, ax = plt.subplots(figsize=(7, 3.4))
cats = ["Vigorosa (NDVI>0,4)", "Suelo o rala (NDVI<0,2)"]
x = np.arange(2); wbar = 0.38
ax.bar(x - wbar / 2, [vig["20241105"]["vigorosa_ndvi_gt_0.4_ha"], vig["20241105"]["suelo_o_rala_ndvi_lt_0.2_ha"]], wbar, label="05/11/2024", color="#9db4c0")
ax.bar(x + wbar / 2, [vig[HOY]["vigorosa_ndvi_gt_0.4_ha"], vig[HOY]["suelo_o_rala_ndvi_lt_0.2_ha"]], wbar, label="05/11/2026", color="#3a7d44")
ax.set_xticks(x, cats); ax.set_ylabel("hectáreas"); ax.legend(frameon=False); ax.grid(axis="y", alpha=.3)
ax.set_title("Misma fecha, dos años: superficie por clase de NDVI")
fig.tight_layout(); fig.savefig(os.path.join(FIG, "comparacion_2024_2026.png"), dpi=150); plt.close(fig)

json.dump(resumen, open(os.path.join(OUT, "datos", "resumen_resultados.json"), "w", encoding="utf8"),
          indent=1, ensure_ascii=False, default=str)
print(json.dumps(resumen, indent=1, ensure_ascii=False, default=str))
