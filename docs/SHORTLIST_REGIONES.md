# Lista corta de regiones prioritarias (KPI 1.1)

Pedido del profesor: «dónde es más baja o está bajando la cobertura, y dónde es más importante». Hay tres preguntas distintas (qué tan baja es, si se acerca o se aleja de Chile, cuánto pesa) y por eso la lista recomendada las combina y hay otras cuatro para compararla. El dashboard deja elegir; **la recomendada es la A (8 regiones)**. Datos: `Data processed/kpi_cobertura_regiones.csv` y `kpi_cobertura_prioridad_robustez.csv` (script 24).

**Año de referencia: 2024** (constante `ANIO_REF` del script 24). Es el año del Censo (la única población medida, no proyectada) y el último con ocupados por región. Cobertura de Chile en 2024: 46,5 %.

## La lista recomendada: tres factores, cada uno como rango de 1 a 16

Cada región recibe un **rango de 1 (la peor) a 16** en tres factores; los empates reciben el rango promedio.

| Factor | Qué mide | Rango 1 = |
|---|---|---|
| **Nivel** | puntos de cobertura bajo la de Chile en 2024 | la más lejos de Chile (La Araucanía, −10,0) |
| **Tendencia** | puntos de cobertura ganados desde 2007 **menos** los que ganó Chile (+9,3) | la que más terreno perdió frente al país (Metropolitana, −2,9) |
| **Brecha** | cotizantes que faltan para alcanzar a Chile = (cobertura de Chile − la de la región) × población 15-64, en personas y con signo (sobre el promedio es negativa) | la que más gente le falta (La Araucanía, 67.220) |

**Regla:** entran las regiones con cobertura **bajo la de Chile** que están **entre las 5 peores de al menos uno de los tres factores**. Se ordenan por la **suma de los tres rangos** (menor = más prioritaria). Como todas las demás reglas del proyecto, el número de regiones lo da la regla, no un cupo: da **8**.

| # | Región | Nivel (rango) | Tendencia desde 2007 frente a Chile (rango) | Brecha (rango) | Suma | Por qué entra |
|---|---|---|---|---|---|---|
| 1 | Valparaíso | −4,2 pts (6) | −0,4 (4) | 53.660 (2) | 12 | Tendencia + brecha: no gana terreno frente a Chile y es la segunda mayor brecha (9,1 % de los cotizantes) |
| 2 | La Araucanía | −10,0 pts (1) | +2,3 (11) | 67.220 (1) | 13 | Nivel + brecha: la cobertura más baja y la mayor brecha; sí se acerca, pero lento |
| 3 | Arica y Parinacota | −6,3 pts (4) | −1,6 (2) | 10.346 (9) | 15 | Nivel + tendencia: baja y se aleja de Chile en los cinco períodos probados |
| 4 | Coquimbo | −6,0 pts (5) | +1,4 (7) | 33.343 (4) | 16 | Nivel + brecha: se acerca a Chile, pero parte de lejos |
| 5 | Los Ríos | −8,3 pts (3) | +1,4 (8) | 22.315 (6) | 17 | Nivel: tercera más baja; la brecha en personas es menor por su tamaño |
| 6 | **Tarapacá** | −3,1 pts (7) | −1,4 (3) | 7.932 (10) | 20 | **Solo tendencia**: está solo 3 puntos bajo Chile, pero desde 2007 pierde terreno (desde 2015, −2,9, la peor del país) |
| 7 | Ñuble | −8,6 pts (2) | +2,5 (13,5)* | 29.346 (5) | 20,5 | Nivel + brecha: segunda más baja |
| 8 | **Biobío** | −3,1 pts (9) | +2,5 (13,5)* | 34.037 (3) | 25,5 | **Solo brecha**: gana terreno frente a Chile y su nivel es medio; entra por tamaño (8,1 % de los cotizantes, tercera mayor brecha) |

\* Biobío y Ñuble son una sola serie hasta 2017 (la Superintendencia las publicó juntas): la tendencia es la del par y por eso es idéntica.

**Las dos últimas, Tarapacá y Biobío, son las que más conviene explicar.** Tarapacá es una región chica (1,9 % de los cotizantes) cuyo problema es de **dirección**: parece mejor que muchas, pero desde 2007 su cobertura sube menos que la del país. Biobío es el caso inverso, un problema de **tamaño**: se acerca a Chile en todos los períodos (+2,5 puntos sobre Chile desde 2007), pero falta más gente que en cualquier otra región salvo La Araucanía y Valparaíso. **Los Lagos** (suma 24, entre Ñuble y Biobío) queda fuera: ninguno de sus tres rangos está entre los 5 peores (nivel 8, tendencia 9, brecha 7). La **Metropolitana** tiene la peor tendencia (rango 1: −2,9 puntos frente a Chile desde 2007; su índice respecto de Chile baja de 120 a 110) pero está 4,5 puntos **sobre** el promedio y por eso no entra; es una región a observar, no una de cobertura baja.

### Por qué 2007 y por qué la regla es robusta

- **Por qué no «el menor aumento en %»:** el aumento porcentual desde 2002 premia a quien parte de abajo (La Araucanía +89 %, la de menor cobertura, sería la «mejor»; la Metropolitana +39 %, la «peor») y desde 2002 solo hay 13 territorios (Arica, Los Ríos y Ñuble van fusionados). Por eso la tendencia se mide en **puntos frente a Chile**.
- **Por qué 2007:** entre 2006 y 2007 la cobertura sube 2 a 4 puntos en 12 de los 13 territorios, sin explicación (`docs/supuestos_y_limitaciones.md`, 2.2); 2007 es el primer año después del salto y deja 15 territorios. El único año con las 16 regiones separadas desde el inicio es 2018.
- **Robustez** (`kpi_cobertura_prioridad_robustez.csv`): la misma regla con cada año de inicio entre 2002 y 2022 elige **exactamente estas 8 regiones con todos los inicios hasta 2019** (18 de 21 casos). Con inicios 2020-2022 la ventana tiene 2 a 4 años, mezcla el rebote de 2021-2022 y la lista cambia en una o dos regiones (Tarapacá sale; con 2020 entran Los Lagos y Maule). Además, las 7 regiones de menor suma de rangos están dentro de la lista con todos los inicios hasta 2018.
- **Lo que no prueba:** el factor «brecha» es nivel × tamaño, así que el nivel pesa dos veces, y la brecha en personas ya era el criterio de la lista B. Que estas regiones salgan arriba no es una confirmación independiente. Con el **peso en los cotizantes** en lugar de la brecha, la Metropolitana (44,8 %) pasa a ser rango 1 y desplaza a Biobío, Coquimbo o Los Ríos; por eso se usa la brecha.

## Las otras cuatro listas (comparación)

| Lista | Las regiones | Criterio |
|---|---|---|
| **B. Mayor brecha de cotizantes** | La Araucanía, Valparaíso, Biobío, Coquimbo, Ñuble | (cobertura de Chile − la de la región) × población 15-64 |
| **C. Caída más fuerte desde 2022** | Arica y Parinacota, Valparaíso, Metropolitana, Biobío, Los Ríos | puntos de cobertura perdidos desde 2022 |
| **D. Mayor peso en los cotizantes** | Metropolitana, Valparaíso, Biobío, Maule, O'Higgins | parte del total de cotizantes del país |
| **E. Brecha o pérdida de cotizantes desde 2022** (la recomendada hasta 2026-11-16, 7 regiones) | La Araucanía, Valparaíso, Biobío, Coquimbo, Ñuble, Los Ríos, Arica y Parinacota | bajo el promedio y (entre las 5 de mayor brecha **o** con menos cotizantes que en 2022) |

La lista E se reemplazó porque descansa sobre 2022-2024 (dos años), y 2023 trajo un descenso nacional de 160 mil cotizantes: el «cambio desde 2022» mide sobre todo cuánto se recuperó cada región en 2024. La nueva sigue incluyendo a las seis regiones más débiles de ese análisis y agrega Tarapacá, que solo se ve con una ventana larga. Revisión crítica de la lista E: `docs/ANALISIS_SIETE_REGIONES.md`.

## Las 16 regiones

Ordenadas por la suma de rangos.

| Región | Cobertura 2024 (%) | Nivel: pts bajo Chile (rango) | Tendencia desde 2007 vs Chile (rango) | Brecha en personas (rango) | Suma | En la lista |
|---|---|---|---|---|---|---|
| Valparaíso | 42,2 | 4,2 (6) | −0,4 (4) | 53.660 (2) | 12 | Sí |
| La Araucanía | 36,5 | 10,0 (1) | +2,3 (11) | 67.220 (1) | 13 | Sí |
| Arica y Parinacota | 40,2 | 6,3 (4) | −1,6 (2) | 10.346 (9) | 15 | Sí |
| Coquimbo | 40,5 | 6,0 (5) | +1,4 (7) | 33.343 (4) | 16 | Sí |
| Los Ríos | 38,1 | 8,3 (3) | +1,4 (8) | 22.315 (6) | 17 | Sí |
| Tarapacá | 43,3 | 3,1 (7) | −1,4 (3) | 7.932 (10) | 20 | Sí |
| Ñuble | 37,8 | 8,6 (2) | +2,5 (13,5) | 29.346 (5) | 20,5 | Sí |
| Los Lagos | 43,3 | 3,1 (8) | +1,5 (9) | 19.099 (7) | 24 | — |
| Biobío | 43,3 | 3,1 (9) | +2,5 (13,5) | 34.037 (3) | 25,5 | Sí |
| Metropolitana | 51,0 | −4,5 (14) | −2,9 (1) | −234.161 (16) | 31 | — (sobre el promedio) |
| Maule | 44,1 | 2,4 (10) | +3,5 (15) | 18.034 (8) | 33 | — |
| Aysén | 47,9 | −1,5 (11) | +2,3 (12) | −1.019 (11) | 34 | — |
| Atacama | 49,3 | −2,8 (12) | +1,5 (10) | −5.712 (12) | 34 | — |
| Magallanes | 54,2 | −7,8 (16) | +1,1 (6) | −8.903 (13) | 35 | — |
| Antofagasta | 51,9 | −5,4 (15) | +0,2 (5) | −24.441 (15) | 35 | — |
| O'Higgins | 49,7 | −3,2 (13) | +4,6 (16) | −21.097 (14) | 43 | — |

Notas: 2018-2023 usa población proyectada (INE base 2017 llevada al Censo 2024); 2024 es el Censo. La tendencia desde 2007 usa la serie fusionada de Biobío y Ñuble (separadas desde 2018); Arica y Los Ríos están separadas desde 2007. Límites en `docs/supuestos_y_limitaciones.md`.
