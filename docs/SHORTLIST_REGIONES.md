# Lista corta de regiones prioritarias (KPI 1.1)

Pedido del profesor: «dónde es más baja o está bajando la cobertura, y dónde es más importante». Hay tres preguntas distintas (qué tan baja, qué tan rápido cae, cuánto pesa) y por eso hay cuatro listas. El dashboard deja elegir; **la recomendada es la A**. Datos: `Data processed/kpi_cobertura_regiones.csv` (script 24).

**Año de referencia: 2024** (constante `ANIO_REF` del script 24). Es el año del Censo (la única población medida, no proyectada) y el último con ocupados por región, así que el problema (qué regiones) y la explicación (la descomposición) usan el mismo año. Cobertura de Chile en 2024: 46,5 %. La cobertura de 2025 existe (46,9 %) pero su población es una proyección y no hay empleo regional de 2025.

## Las cuatro listas

| Lista | Las regiones | Criterio |
|---|---|---|
| **A. Bajo el promedio, con brecha o pérdida de cotizantes (recomendada)** | 1. La Araucanía, 2. Valparaíso, 3. Biobío, 4. Coquimbo, 5. Ñuble, 6. Los Ríos, 7. Arica y Parinacota | cobertura bajo la de Chile **y** (entre las 5 de mayor brecha **o** con menos cotizantes que en 2022); orden por brecha |
| **B. Mayor brecha de cotizantes** | 1. La Araucanía, 2. Valparaíso, 3. Biobío, 4. Coquimbo, 5. Ñuble | (cobertura de Chile − cobertura de la región) × población 15-64 |
| **C. Caída más fuerte desde 2022** | 1. Arica y Parinacota, 2. Valparaíso, 3. Metropolitana, 4. Biobío, 5. Los Ríos | puntos de cobertura perdidos desde 2022 |
| **D. Mayor peso en los cotizantes** | 1. Metropolitana, 2. Valparaíso, 3. Biobío, 4. Maule, 5. O'Higgins | parte del total de cotizantes del país |

## Qué es cada lista y en qué se diferencian

- **B, mayor brecha:** (cobertura de Chile − cobertura de la región) × población de 15 a 64 años = cuántos cotizantes más tendría la región si alcanzara el promedio. Mira solo el **nivel** y el tamaño; no mira cómo evolucionó.
- **A, recomendada:** primero se queda con las regiones **bajo el promedio de Chile** y, de esas, con las que cumplen **al menos una**: están entre las 5 de mayor brecha (B) **o** tienen **menos cotizantes que en 2022** (en personas). Une el nivel (cuánta gente falta) con el flujo (cuánta gente dejó de pagar). No es un cupo fijo de 5: la regla da 7 regiones.
- La columna «Por qué entra» de la tabla del dashboard lo muestra: **Brecha y pérdida** (La Araucanía, Valparaíso, Biobío, Ñuble), **Solo brecha** (Coquimbo: gran brecha pero ganó 3.523 cotizantes desde 2022) y **Solo pérdida** (Los Ríos y Arica y Parinacota: brecha menor pero perdieron cotizantes).
- **C, caída más fuerte:** puntos de cobertura perdidos desde 2022; sirve para ver dónde cambia la tendencia, pero Arica y Parinacota pesa solo 1,1 % de los cotizantes.
- **D, mayor peso:** importancia por tamaño; la Metropolitana (44,8 % de los cotizantes) solo entra aquí.

Con el año de referencia 2024, las 5 de mayor brecha ya cayeron todas entre 2022 y 2024 (en puntos), así que la antigua versión de A («bajo el promedio y en caída en puntos») coincidía con B. La versión actual de A **no** coincide con B porque agrega las que perdieron cotizantes.

## Las 16 regiones

| Región | Cobertura 2024 (%) | Peso en los cotizantes (%) | Brecha (personas) | Cambio desde 2019 (puntos) | Cambio desde 2022 (puntos) | Cotizantes desde 2022 (personas) | En las listas |
|---|---|---|---|---|---|---|---|
| La Araucanía | 36,5 | 4,2 | 67.220 | +1,5 | −0,4 | −2.524 | A, B |
| Valparaíso | 42,2 | 9,1 | 53.660 | +0,3 | −1,3 | −13.238 | A, B, C, D |
| Biobío | 43,3 | 8,1 | 34.037 | +2,1 | −0,8 | −9.751 | A, B, C, D |
| Coquimbo | 40,5 | 3,9 | 33.343 | +2,4 | −0,1 | +3.523 | A, B |
| Ñuble | 37,8 | 2,2 | 29.346 | +1,6 | −0,7 | −2.327 | A, B |
| Los Ríos | 38,1 | 1,7 | 22.315 | +1,2 | −0,7 | −1.518 | A, C |
| Los Lagos | 43,3 | 4,5 | 19.099 | +1,4 | −0,4 | +132 | — |
| Maule | 44,1 | 5,6 | 18.034 | +1,5 | +0,1 | +3.508 | D |
| Arica y Parinacota | 40,2 | 1,1 | 10.346 | −0,4 | −2,0 | −2.202 | A, C |
| Tarapacá | 43,3 | 1,9 | 7.931 | +1,0 | −0,4 | +1.426 | — |
| O'Higgins | 49,7 | 5,6 | 0 | +4,4 | +0,8 | +7.934 | D |
| Magallanes | 54,2 | 1,1 | 0 | +0,4 | +0,9 | +1.385 | — |
| Metropolitana | 51,0 | 44,8 | 0 | −1,1 | −1,2 | −44.099 | C, D |
| Aysén | 47,9 | 0,6 | 0 | +3,8 | +2,1 | +1.646 | — |
| Atacama | 49,3 | 1,7 | 0 | +3,3 | −0,2 | +16 | — |
| Antofagasta | 51,9 | 4,0 | 0 | +2,9 | −0,3 | +1.888 | — |

Notas: 2018-2023 usa población proyectada (INE base 2017 llevada al Censo 2024); 2024 es el Censo. 2022 es el máximo reciente del país (47,6 %) y 2023 trajo un descenso nacional de 160 mil cotizantes: el «cambio desde 2022» mide en buena parte cuánto se recuperó cada región en 2024. Límites en `docs/supuestos_y_limitaciones.md`; revisión crítica de las siete en `docs/ANALISIS_SIETE_REGIONES.md`.
