# Módulo 1: Toma de Decisiones

# Selección del enfoque tecnológico de SatellAgro mediante investigación asistida por IA

## Descripción
Antes de construir el prototipo de SatellAgro había que decidir **con qué tecnología medir el estado hídrico de la vid**. Esa elección condiciona el costo, la escala, el tipo de aviso y el modelo de negocio, así que la tratamos como una decisión formal:

1. Investigación asistida por IA (Claude) sobre teledetección del agua en vegetación, fuentes de imágenes gratuitas y competencia, con cada afirmación atada a una fuente.
2. Matriz de decisión ponderada con seis criterios y análisis de sensibilidad.
3. Contraste con datos reales: imágenes Sentinel-2 de Agrelo (Luján de Cuyo) entre septiembre y noviembre de 2026.

## Alternativas evaluadas
* **A · Óptico Sentinel-2 (NDMI + NDVI)**: gratis, 20 m, cada ~5 días; avisa tarde.
* **B · Térmico Landsat 8/9 (CWSI)**: gratis, 100 m, cada ~8 días; avisa temprano.
* **C · Sensores de humedad en finca (IoT)**: continuo, pero puntual y con hardware en cada cuartel.

| | A · Sentinel-2 | B · Térmico | C · Sensores |
|---|---|---|---|
| Puntaje ponderado (sobre 5) | **4,25** | 4,10 | 2,60 |

## Decisión: Alternativa A
Sentinel-2 gana en cinco de los seis análisis de sensibilidad. Sólo pierde si lo más importante fuera anticiparse al cierre de estomas, y por eso el térmico queda como **evolución futura**. Límite asumido: SatellAgro dice **dónde ir a mirar**, no cuánto regar.

# Descarga del informe
[Descargá aquí el informe en PDF](M1%20-%20TyHMII%20-%20Seleccion%20del%20enfoque%20tecnologico%20-%20SatellAgro.pdf)
