"""Módulo 3 - Análisis pericial de una imagen satelital (Sentinel-2 L2A, 05/11/2026, Agrelo).

Uso: python analisis_pericial.py <carpeta_sentinel2> <carpeta_evidencia>

Genera las láminas de evidencia del informe:
  - escena completa en color real con el lote del caso marcado,
  - composiciones color real / SWIR-NIR-Rojo,
  - recortes del lote antes (31/10) y después (05/11),
  - histogramas de reflectancia (exposición) y clases SCL,
  - cadena de custodia: URL de origen y SHA-256 de cada archivo.
"""
import hashlib
import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pyproj
import rasterio

S2, EV = sys.argv[1], sys.argv[2]
os.makedirs(EV, exist_ok=True)
HOY, ANTES = "20261105", "20261031"
# Lote del caso (detectado en el procesamiento del Módulo 4): centro en coordenadas geográficas
CASO_LON, CASO_LAT = -68.93831, -33.10120
VENT = 45  # semiancho del recorte en píxeles de 10 m (~900 m de lado)


def rd(f, b):
    with rasterio.open(os.path.join(S2, f"{f}_{b}.tif")) as s:
        return s.read().astype("float32"), s.profile


def stretch(a, lo=2, hi=98):
    p1, p2 = np.nanpercentile(a, (lo, hi))
    return np.clip((a - p1) / (p2 - p1), 0, 1)


tc = {f: rd(f, "visual")[0] for f in (HOY, ANTES)}
prof10 = rd(HOY, "red")[1]
x, y = pyproj.Transformer.from_crs(4326, 32719, always_xy=True).transform(CASO_LON, CASO_LAT)
col, row = ~prof10["transform"] * (x, y)
col, row = int(col), int(row)
r0, r1, c0, c1 = row - VENT, row + VENT, col - VENT, col + VENT

# 1. escena completa con el lote marcado
fig, ax = plt.subplots(figsize=(8, 7.6))
ax.imshow(np.moveaxis(tc[HOY], 0, -1).astype("uint8"))
ax.add_patch(mpatches.Rectangle((c0, r0), 2 * VENT, 2 * VENT, fill=False, ec="yellow", lw=2))
ax.text(c1 + 8, r0 + 10, "Lote del caso", color="yellow", fontsize=11, weight="bold")
ax.set_title("Sentinel-2C · 05/11/2026 · color real (B4-B3-B2) · Agrelo, Luján de Cuyo")
ax.set_xlabel("columna (píxel de 10 m)"); ax.set_ylabel("fila (píxel de 10 m)")
fig.tight_layout(); fig.savefig(os.path.join(EV, "01_escena_color_real.png"), dpi=130); plt.close(fig)


# 2. composición SWIR-NIR-Rojo (20 m): resalta agua en vegetación y suelo
def swir_comp(f):
    sw = rd(f, "swir16")[0][0] / 1e4; n8 = rd(f, "nir08")[0][0] / 1e4
    red = rd(f, "red")[0][0] / 1e4
    h, w = sw.shape
    red20 = red.reshape(h, 2, w, 2).mean(axis=(1, 3))
    return np.dstack([stretch(sw), stretch(n8), stretch(red20)])


sc = {f: swir_comp(f) for f in (HOY, ANTES)}
fig, axs = plt.subplots(1, 2, figsize=(13, 6.2))
axs[0].imshow(np.moveaxis(tc[HOY], 0, -1).astype("uint8")); axs[0].set_title("Color real (lo que vería el ojo)")
axs[1].imshow(sc[HOY]); axs[1].set_title("SWIR · NIR · Rojo (agua y vigor)")
for a in axs:
    a.axis("off")
fig.suptitle("Misma toma, dos «películas»: la composición cambia lo que se ve", fontsize=13)
fig.tight_layout(); fig.savefig(os.path.join(EV, "02_composiciones.png"), dpi=120); plt.close(fig)


# 3. lote del caso: antes / después
def idx(f):
    red = rd(f, "red")[0][0] / 1e4; nir = rd(f, "nir")[0][0] / 1e4
    n8 = rd(f, "nir08")[0][0] / 1e4; sw = rd(f, "swir16")[0][0] / 1e4
    ndvi = (nir - red) / (nir + red)
    ndmi = np.kron((n8 - sw) / (n8 + sw), np.ones((2, 2)))[: red.shape[0], : red.shape[1]]
    return ndvi, ndmi


ind = {f: idx(f) for f in (HOY, ANTES)}
fig, axs = plt.subplots(2, 4, figsize=(15, 7.8))
for i, (f, t) in enumerate(((ANTES, "31/10/2026"), (HOY, "05/11/2026"))):
    axs[i, 0].imshow(np.moveaxis(tc[f][:, r0:r1, c0:c1], 0, -1).astype("uint8")); axs[i, 0].set_title(f"Color real {t}")
    axs[i, 1].imshow(sc[f][r0 // 2:r1 // 2, c0 // 2:c1 // 2]); axs[i, 1].set_title(f"SWIR-NIR-Rojo {t}")
    im2 = axs[i, 2].imshow(ind[f][0][r0:r1, c0:c1], cmap="RdYlGn", vmin=0, vmax=0.8); axs[i, 2].set_title(f"NDVI {t}")
    im3 = axs[i, 3].imshow(ind[f][1][r0:r1, c0:c1], cmap="BrBG", vmin=-0.3, vmax=0.4); axs[i, 3].set_title(f"NDMI {t}")
    for j, a in enumerate(axs[i]):
        a.set_xticks([]); a.set_yticks([])
        k = 0.5 if j == 1 else 1.0  # la composición SWIR está a 20 m: mitad de píxeles
        a.add_patch(mpatches.Circle((VENT * k, VENT * k), 12 * k, fill=False, ec="magenta", lw=1.5))
fig.colorbar(im2, ax=axs[:, 2], shrink=.7); fig.colorbar(im3, ax=axs[:, 3], shrink=.7)
fig.suptitle("Lote del caso (círculo): en 5 días el NDMI y el NDVI caen juntos → menos hojas, no falta de agua", fontsize=13)
fig.savefig(os.path.join(EV, "03_caso_antes_despues.png"), dpi=110, bbox_inches="tight"); plt.close(fig)

yy, xx = np.ogrid[-VENT:VENT, -VENT:VENT]
circ = (xx ** 2 + yy ** 2) <= 12 ** 2
valores = {f: {"ndvi": round(float(np.nanmean(ind[f][0][r0:r1, c0:c1][circ])), 3),
               "ndmi": round(float(np.nanmean(ind[f][1][r0:r1, c0:c1][circ])), 3)} for f in (ANTES, HOY)}

# 4. exposición: histogramas de reflectancia y clases SCL
fig, axs = plt.subplots(1, 2, figsize=(13, 4))
for b, c, lbl in (("red", "#c0392b", "B04 Rojo 665 nm"), ("nir", "#7f8c8d", "B08 NIR 842 nm"),
                  ("nir08", "#8e44ad", "B8A NIR 865 nm"), ("swir16", "#d4a017", "B11 SWIR 1610 nm")):
    a = rd(HOY, b)[0][0] / 1e4
    axs[0].hist(a[a > 0].ravel(), bins=150, range=(0, 0.6), histtype="step", color=c, label=lbl, lw=1.4)
axs[0].set_xlabel("reflectancia de superficie"); axs[0].set_ylabel("píxeles"); axs[0].legend(frameon=False)
axs[0].set_title("«Exposición»: ninguna banda satura ni queda en negro")
scl = rd(HOY, "scl")[0][0]
nombres = {0: "Sin dato", 1: "Saturado/defect.", 2: "Zona oscura", 3: "Sombra nube", 4: "Vegetación", 5: "Suelo desnudo",
           6: "Agua", 7: "No clasif.", 8: "Nube media", 9: "Nube alta", 10: "Cirro", 11: "Nieve"}
vals, cnt = np.unique(scl, return_counts=True)
pct = cnt / cnt.sum() * 100
axs[1].barh([nombres[v] for v in vals], pct, color="#3a7d44"); axs[1].set_xlabel("% del recorte")
for i, p in enumerate(pct):
    axs[1].text(p + 0.5, i, f"{p:.2f} %", va="center", fontsize=9)
axs[1].set_title("Clasificación de escena (SCL) de ESA en el recorte")
fig.tight_layout(); fig.savefig(os.path.join(EV, "04_exposicion_y_scl.png"), dpi=120); plt.close(fig)

stats_bandas = {}
for b in ("red", "nir", "nir08", "swir16"):
    a = rd(HOY, b)[0][0]
    stats_bandas[b] = {"min_dn": int(a[a > 0].min()), "max_dn": int(a.max()), "p2": float(np.percentile(a[a > 0], 2)),
                       "p98": float(np.percentile(a[a > 0], 98)), "sin_dato_px": int((a == 0).sum())}

# 5. cadena de custodia
meta = json.load(open(os.path.join(S2, "stac_metadata.json"), encoding="utf8"))
custodia = {"herramienta": "pystac-client + rasterio (lectura por ventana de COG en AWS)", "catalogo": "https://earth-search.aws.element84.com/v1",
            "coleccion": "sentinel-2-l2a", "imagenes": {}}
for f in (ANTES, HOY):
    p = meta[f]["properties"]
    custodia["imagenes"][f] = {"id": meta[f]["id"], "fecha_hora_utc": p["datetime"], "plataforma": p["platform"],
                               "baseline": p["s2:processing_baseline"], "producto": p["s2:product_uri"],
                               "archivos": {k: {"origen": v["href"], "sha256": v["sha256"], "archivo": v["file"]}
                                            for k, v in meta[f]["assets"].items()}}
for fn in sorted(os.listdir(EV)):
    if fn.endswith(".png"):
        custodia.setdefault("laminas_sha256", {})[fn] = hashlib.sha256(open(os.path.join(EV, fn), "rb").read()).hexdigest()
json.dump(custodia, open(os.path.join(EV, "cadena_de_custodia.json"), "w", encoding="utf8"), indent=1, ensure_ascii=False)

p = meta[HOY]["properties"]
ficha = {k: p.get(k) for k in ("datetime", "platform", "instruments", "s2:processing_baseline", "eo:cloud_cover",
                               "view:sun_elevation", "view:sun_azimuth", "view:incidence_angle", "view:azimuth",
                               "s2:degraded_msi_data_percentage", "s2:saturated_defective_pixel_percentage",
                               "s2:vegetation_percentage", "s2:not_vegetated_percentage", "s2:cloud_shadow_percentage",
                               "s2:thin_cirrus_percentage", "s2:reflectance_conversion_factor", "grid:code",
                               "s2:product_uri", "s2:generation_time", "proj:code")}
json.dump({"ficha_imagen": ficha, "caso": {"lon": CASO_LON, "lat": CASO_LAT, "valores": valores},
           "scl_pct": {nombres[int(v)]: round(float(x), 3) for v, x in zip(vals, pct)}, "bandas": stats_bandas},
          open(os.path.join(EV, "ficha_tecnica.json"), "w", encoding="utf8"), indent=1, ensure_ascii=False, default=str)
print(json.dumps({"ficha": ficha, "caso": valores, "scl": {nombres[int(v)]: round(float(x), 2) for v, x in zip(vals, pct)},
                  "bandas": stats_bandas}, indent=1, ensure_ascii=False, default=str))
