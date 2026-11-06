# Módulo 5: Dinámica de Sistemas

## Planteo del problema: difusión de SatellAgro por los cauces de riego
SatellAgro llega a los regantes **cauce por cauce**, a través del inspector de cada Inspección de Cauce, con un reporte gratis (marketing de guerrilla). Modelamos en **Vensim** el embudo del regante (sin conocer → conocen → con reporte → suscriptos → abandonaron), los cauces aliados, la reputación del servicio, los casos de éxito y la economía, durante dos temporadas (78 semanas desde el 1/11/2026).

## Validación
Replicamos el modelo en Python ecuación por ecuación (Euler, paso de 0,25 semanas). La réplica **coincide exactamente** con los 30 valores de Vensim de la tabla de cinco tácticas: guerrilla calibrada, sin calibrar, zumbido, contacto en frío y una reunión por semana.

## Pruebas con la función STEP
`marketing_guerrilla_STEP.mdl` agrega dos escalones:
1. **Esfuerzo de campo:** las reuniones con inspectores pasan de 0,25 a 1 por semana en la semana 4 (`STEP(0,75; 4)`).
2. **Calibración:** las falsas alarmas bajan del 30 % al 10 % al cierre de la primera temporada (`STEP(0,20; 22)`).

### Conclusión técnica
Más esfuerzo sin calibrar trae más suscriptos (110) pero peor resultado (−3.912 USD): la reputación cae y los nuevos abandonan. Calibrar al cierre de la primera temporada recupera casi todo el beneficio (79 suscriptos contra 82). Los dos escalones juntos se potencian: 155 suscriptos y un resultado casi en equilibrio. Con 25 % o más de falsas alarmas, ningún esfuerzo de campo hace rentable el negocio en dos temporadas.

## 📥 Descargas
[Ver el informe del Módulo 5 en formato web](https://juan-zingaretti.github.io/TyHm-2/Modulo%205/Informe_M5.html)

[Descargá aquí el informe en PDF](https://raw.githubusercontent.com/juan-zingaretti/TyHm-2/main/Modulo%205/M5%20-%20TyHMII%20-%20Dinamica%20de%20sistemas%20-%20Difusion%20de%20SatellAgro.pdf)

[Descargá aquí el modelo de Vensim (.mdl)](https://raw.githubusercontent.com/juan-zingaretti/TyHm-2/main/Modulo%205/marketing_guerrilla.mdl) · [Variante con STEP (.mdl)](https://raw.githubusercontent.com/juan-zingaretti/TyHm-2/main/Modulo%205/marketing_guerrilla_STEP.mdl)

## Reproducir en Python
```bash
cd "Modulo 5/simulacion"
python modelo_guerrilla.py          # cinco tácticas
python analisis_m5.py ../figuras    # gráficos, pruebas STEP y sensibilidad
```
