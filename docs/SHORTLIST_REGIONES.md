# Lista corta de regiones prioritarias (KPI 1.1)

Pedido del profesor: «dónde es más baja o está bajando la cobertura, y dónde es más importante». Hay tres preguntas distintas (qué tan baja, qué tan rápido cae, cuánto pesa) y por eso hay cuatro listas de 5. El dashboard deja elegir; **la recomendada es la A**. Datos: `Data processed/kpi_cobertura_regiones.csv` (script 24). Cobertura de Chile en 2025: 46,9 %.

## Las cuatro listas

| Lista | Las 5 regiones | Criterio |
|---|---|---|
| **A. Bajo el promedio y en caída (recomendada)** | 1. La Araucanía, 2. Valparaíso, 3. Biobío, 4. Los Ríos, 5. Los Lagos | cobertura bajo la de Chile **y** cayendo desde 2022; orden por brecha |
| **B. Mayor brecha de cotizantes** | 1. La Araucanía, 2. Valparaíso, 3. Biobío, 4. Coquimbo, 5. Ñuble | (cobertura de Chile − cobertura de la región) × población 15-64 |
| **C. Caída más fuerte desde 2022** | 1. Arica y Parinacota, 2. Valparaíso, 3. Biobío, 4. Metropolitana, 5. Los Ríos | puntos de cobertura perdidos desde 2022 |
| **D. Mayor peso en los cotizantes** | 1. Metropolitana, 2. Valparaíso, 3. Biobío, 4. Maule, 5. O'Higgins | parte del total de cotizantes del país |

- **A** responde lo que se pidió: bajo el promedio (brecha) *y* con evolución negativa. Es una condición, no un promedio de dos rankings, así que se entiende en una frase. Entran Los Ríos y Los Lagos (cobertura 38,6 % y 43,6 %, caen 0,2 y 0,1 puntos); salen Coquimbo y Ñuble, que están bajo el promedio pero han subido desde 2022 (+0,2 y +0,3).
- **B** es la lista de la primera versión (solo nivel y tamaño). Coincide con A en tres regiones.
- **C** muestra las caídas, pero son chicas y dos son regiones pequeñas (Arica y Parinacota pesa 1,1 % de los cotizantes). Sirve para ver dónde cambia la tendencia, no para priorizar sola.
- **D** es la importancia por tamaño. La Metropolitana (44,9 % de los cotizantes) solo entra aquí: su cobertura está sobre el promedio y cae poco (−0,3 puntos), pero por su tamaño es el mayor volumen de cotizantes que se movió (unos 16 mil menos que si hubiera mantenido la cobertura de 2022).

## Las 16 regiones

| Región | Cobertura 2025 (%) | Peso en los cotizantes (%) | Brecha (personas) | Cambio desde 2019 (puntos) | Cambio desde 2022 (puntos) | En las listas |
|---|---|---|---|---|---|---|
| La Araucanía | 36,7 | 4,1 | 68.462 | +1,7 | −0,2 | A, B |
| Valparaíso | 42,5 | 9,0 | 55.175 | +0,6 | −1,0 | A, B, C, D |
| Biobío | 43,5 | 8,0 | 36.972 | +2,3 | −0,7 | A, B, C, D |
| Coquimbo | 40,8 | 3,9 | 34.079 | +2,7 | +0,2 | B |
| Ñuble | 38,8 | 2,2 | 27.593 | +2,5 | +0,3 | B |
| Los Ríos | 38,6 | 1,7 | 22.360 | +1,6 | −0,2 | A, C |
| Los Lagos | 43,6 | 4,5 | 20.268 | +1,6 | −0,1 | A |
| Maule | 44,5 | 5,6 | 17.664 | +2,0 | +0,6 | D |
| Arica y Parinacota | 40,3 | 1,1 | 10.928 | −0,3 | −1,9 | C |
| Tarapacá | 44,1 | 1,9 | 7.043 | +1,8 | +0,4 | — |
| O'Higgins | 50,3 | 5,6 | 0 | +5,0 | +1,5 | D |
| Magallanes | 55,0 | 1,1 | 0 | +1,1 | +1,6 | — |
| Metropolitana | 51,9 | 44,9 | 0 | −0,2 | −0,3 | C, D |
| Aysén | 49,0 | 0,6 | 0 | +4,9 | +3,3 | — |
| Atacama | 50,2 | 1,7 | 0 | +4,2 | +0,7 | — |
| Antofagasta | 53,4 | 4,0 | 0 | +4,5 | +1,3 | — |

Notas: 2018-2025 usa población proyectada (INE base 2017 llevada al Censo 2024), no datos; el año 2022 es el máximo reciente del país (47,6 %); desde 2019 solo caen Arica y Parinacota y la Metropolitana. Límites en `docs/supuestos_y_limitaciones.md`.

## Qué cambia en las causas según la lista

La descomposición (participación × empleo × cotización de los ocupados) existe para las 16 regiones: al cambiar la lista en el tablero cambian las regiones analizadas, no el método. En las listas A y B domina «ocupados que cotizan» (La Araucanía −7,7 puntos frente a Chile, Valparaíso −3,4); en Biobío pesa más la participación laboral (−3,8).
