# Módulo 3: Taller de Fotografía

## Descripción
Aplicamos la fotografía como **prueba documental** a las "fotos" que usa SatellAgro: imágenes satelitales. Trabajamos con una toma real de Sentinel-2C sobre Agrelo, Luján de Cuyo (05/11/2026), y la analizamos como en un peritaje.

## Contenido del informe
1. **Cadena de custodia:** origen exacto de cada banda (catálogo STAC de Earth Search) y huella SHA-256 de cada recorte y de cada lámina (`evidencia/cadena_de_custodia.json`).
2. **Análisis técnico de la toma ("EXIF" satelital):** instrumento, fecha y hora, resolución, exposición (histogramas, saturación), iluminación (elevación y azimut solar), punto de vista, atmósfera, composición de bandas y encuadre.
3. **Peritaje de una falla:** un lote de ~7 ha donde el índice de agua (NDMI) cayó de 0,21 a −0,01 en cinco días habría disparado un rojo. Por la velocidad del cambio, la geometría y la caída conjunta del NDVI (0,45 → 0,16), el dictamen es una **falsa alarma por menos hojas** (corte o cosecha), no estrés hídrico.

## Contenido de la carpeta
* `evidencia/`: láminas PNG, `ficha_tecnica.json` y `cadena_de_custodia.json`.
* `codigo/analisis_pericial.py`: genera todas las láminas a partir de los recortes Sentinel-2.

## 📥 Descargas
[Descargá aquí el informe en PDF](M3%20-%20TyHMII%20-%20Analisis%20pericial%20de%20imagen%20satelital.pdf)
