# Módulo 4: QGIS / Sistemas de Información Geográfica

## Descripción
Construimos el SIG de la zona piloto de SatellAgro: **Agrelo, Luján de Cuyo** (recorte de 9,3 × 8,9 km). El procesamiento se hizo con scripts de Python (rasterio, shapely, pyproj) que reproducen las herramientas de QGIS: reproyección, calculadora raster, estadística zonal, Voronoi, Delaunay, buffer y cálculo de áreas. Todas las capas resultantes (`.geojson` y `.tif`) se abren directamente en QGIS.

## Contenido de la Actividad 1: análisis vectorial
1. **Capas OSM:** 81 cuarteles de viñedo, canales (Flores, Corvalán) y acequias, rutas (RN40, RN7), bodegas y localidades.
2. **Proyección:** de EPSG:4326 a **EPSG:32719 (WGS 84 / UTM 19S)** para medir áreas en hectáreas sin distorsión.
3. **Estadística zonal y semáforo:** NDVI y NDMI medios por cuartel y estado SatellAgro al 05/11/2026 (71 cuarteles sin señales de estrés, 10 no evaluables por brotación).
4. **Buffer de 300 m de los canales:** viñedo que depende de cada canal. El Canal Corvalán resulta el más vitícola (75 % de su franja es viñedo).
5. **Voronoi y Delaunay de bodegas:** área de influencia de cada bodega para el canal comercial "bodega con proveedores".

### 🌐 Mapa web interactivo
👉 [Ver el mapa de cuarteles, canales y bodegas](https://juan-zingaretti.github.io/TyHm-2/Modulo%204/mapa%20cuarteles/index.html)

## Contenido de la Actividad 2: análisis raster
1. **Imágenes:** Sentinel-2 L2A de seis fechas (05/11/2024, 04/01/2026, 26/09, 06/10, 31/10 y 05/11/2026) descargadas por ventana vía STAC.
2. **Máscara SCL de ESA:** sólo píxeles de vegetación y suelo (97,2 % a 99,9 % válidos).
3. **Calculadora raster:** NDVI (10 m), NDMI (20 m) y ΔNDMI contra la mediana de 30 días.
4. **Comparación entre dos años:** misma fecha (5 de noviembre) en 2024 y 2026; superficie de vegetación vigorosa en hectáreas, leída con cautela por el efecto de la fenología.

### 🌐 Mapa web interactivo
👉 [Ver el mapa de NDVI / NDMI](https://juan-zingaretti.github.io/TyHm-2/Modulo%204/mapa%20ndmi/index.html)

## Contenido de la carpeta
* `datos/vector/`: capas GeoJSON (cuarteles con semáforo, canales, buffers, rutas, bodegas, Voronoi, Delaunay, localidades).
* `datos/raster/`: GeoTIFF de NDVI, NDMI y ΔNDMI (EPSG:32719).
* `datos/resumen_resultados.json`: todas las cifras del informe.
* `figuras/`: gráficos y láminas.
* `codigo/`: `01` descarga Sentinel-2, `02` descarga OSM, `03` procesamiento SIG, `04` mapas web, `05` lámina estática.

## 📥 Descargas
[Descargá aquí el informe en PDF](M4%20-%20TyHMII%20-%20SIG%20de%20la%20zona%20piloto%20Agrelo.pdf)
