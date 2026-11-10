# Lista corta de regiones prioritarias (KPI 1.1)

Pedido del profesor: «dónde es más baja o está bajando la cobertura, y dónde es más importante». Hay tres preguntas distintas (qué tan baja, qué tan rápido cae, cuánto pesa) y por eso hay cuatro listas de 5. El dashboard deja elegir; **la recomendada es la A**. Datos: `Data processed/kpi_cobertura_regiones.csv` (script 24).

**Año de referencia: 2024** (constante `ANIO_REF` del script 24). Es el año del Censo (la única población medida, no proyectada) y el último con ocupados por región, así que el problema (qué regiones) y la explicación (la descomposición) usan el mismo año. Cobertura de Chile en 2024: 46,5 %. La cobertura de 2025 existe (46,9 %) pero su población es una proyección y no hay empleo regional de 2025; se deja fuera de las comparaciones.

## Las cuatro listas

| Lista | Las 5 regiones | Criterio |
|---|---|---|
| **A. Bajo el promedio y en caída (recomendada)** | 1. La Araucanía, 2. Valparaíso, 3. Biobío, 4. Coquimbo, 5. Ñuble | cobertura bajo la de Chile **y** cayendo desde 2022; orden por brecha |
| **B. Mayor brecha de cotizantes** | 1. La Araucanía, 2. Valparaíso, 3. Biobío, 4. Coquimbo, 5. Ñuble | (cobertura de Chile − cobertura de la región) × población 15-64 |
| **C. Caída más fuerte desde 2022** | 1. Arica y Parinacota, 2. Valparaíso, 3. Metropolitana, 4. Biobío, 5. Los Ríos | puntos de cobertura perdidos desde 2022 |
| **D. Mayor peso en los cotizantes** | 1. Metropolitana, 2. Valparaíso, 3. Biobío, 4. Maule, 5. O'Higgins | parte del total de cotizantes del país |

- **A** responde lo que se pidió: bajo el promedio (brecha) *y* con evolución negativa. Con 2024 como referencia coincide con **B**: las 5 regiones con más brecha cayeron todas entre 2022 y 2024 (La Araucanía −0,4, Valparaíso −1,3, Biobío −0,8, Ñuble −0,7, Coquimbo −0,1 puntos). Con 2025 como año final, Coquimbo y Ñuble se recuperaban (+0,2 y +0,3) y entraban en su lugar Los Ríos y Los Lagos; esa versión usaba una población de 2025 que es proyección.
- **C** muestra las caídas, pero son chicas y dos son regiones pequeñas (Arica y Parinacota pesa 1,1 % de los cotizantes). Sirve para ver dónde cambia la tendencia, no para priorizar sola.
- **D** es la importancia por tamaño. La Metropolitana (44,8 % de los cotizantes) solo entra aquí: su cobertura está sobre el promedio (51,0 %), pero cae 1,2 puntos desde 2022 y por su tamaño es el mayor volumen de cotizantes que se movió.

## Las 16 regiones

| Región | Cobertura 2024 (%) | Peso en los cotizantes (%) | Brecha (personas) | Cambio desde 2019 (puntos) | Cambio desde 2022 (puntos) | En las listas |
|---|---|---|---|---|---|---|
| La Araucanía | 36,5 | 4,2 | 67.220 | +1,5 | −0,4 | A, B |
| Valparaíso | 42,2 | 9,1 | 53.660 | +0,3 | −1,3 | A, B, C, D |
| Biobío | 43,3 | 8,1 | 34.037 | +2,1 | −0,8 | A, B, C, D |
| Coquimbo | 40,5 | 3,9 | 33.343 | +2,4 | −0,1 | A, B |
| Ñuble | 37,8 | 2,2 | 29.346 | +1,6 | −0,7 | A, B |
| Los Ríos | 38,1 | 1,7 | 22.315 | +1,2 | −0,7 | C |
| Los Lagos | 43,3 | 4,5 | 19.099 | +1,4 | −0,4 | — |
| Maule | 44,1 | 5,6 | 18.034 | +1,5 | +0,1 | D |
| Arica y Parinacota | 40,2 | 1,1 | 10.346 | −0,4 | −2,0 | C |
| Tarapacá | 43,3 | 1,9 | 7.931 | +1,0 | −0,4 | — |
| O'Higgins | 49,7 | 5,6 | 0 | +4,4 | +0,8 | D |
| Magallanes | 54,2 | 1,1 | 0 | +0,4 | +0,9 | — |
| Metropolitana | 51,0 | 44,8 | 0 | −1,1 | −1,2 | C, D |
| Aysén | 47,9 | 0,6 | 0 | +3,8 | +2,1 | — |
| Atacama | 49,3 | 1,7 | 0 | +3,3 | −0,2 | — |
| Antofagasta | 51,9 | 4,0 | 0 | +2,9 | −0,3 | — |

Notas: 2018-2023 usa población proyectada (INE base 2017 llevada al Censo 2024); 2024 es el Censo. El año 2022 es el máximo reciente del país (47,6 %). Límites en `docs/supuestos_y_limitaciones.md`.

## Qué cambia en las causas según la lista

La descomposición (participación × empleo × cotización de los ocupados) existe para las 16 regiones: al cambiar la lista en el tablero cambian las regiones analizadas, no el método.
