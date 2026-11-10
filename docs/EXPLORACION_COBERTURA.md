# Exploración: qué puede explicar la cobertura previsional por región (KPI 1.1)

Pedido del profesor (2026-11): ver dónde la cobertura (cotizantes ÷ población 15-64) es más baja o va bajando y dónde pesa más, y buscar causas (desempleo, informalidad, industria dominante, migración, «1 o 2 más»). Todo sale de `Scripts/24_cobertura_tendencia_causas.py` y `Scripts/25_explorar_causas.py` (en ese orden); el resultado está en el KPI 1.1 del dashboard: tendencia entre los bloques 1 y 2, y descomposición y asociaciones al final. Límites y supuestos: **`docs/supuestos_y_limitaciones.md`**.

## 1. ¿Sube o baja?

| Chile (cotizantes con región ÷ población 15-64, al nivel del Censo) | 2002 | 2010 | 2019 | 2021 | 2022 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| Cobertura | 30,0 % | 40,4 % | 46,1 % | 47,8 % | 47,6 % | 46,5 % | 46,9 % |

- **Subió** en todas las regiones entre 2002 y 2019. El salto de 2006 a 2007 (+3 puntos en 12 de 13 territorios) no está explicado: ver supuestos 2.2.
- **Desde 2019**: 2 de las 16 regiones están bajo su nivel de 2019 (con 2024: Metropolitana −1,1 y Arica y Parinacota −0,4; el resto subió).
- **Desde 2022 baja:** con 2024 como año de referencia (ver abajo), 12 de las 16 regiones tienen menos cobertura que en 2022 (Arica y Parinacota −2,0, Valparaíso −1,3, Metropolitana −1,2, Biobío −0,8, Los Ríos −0,7, Ñuble −0,7, La Araucanía −0,4, Tarapacá −0,4, Los Lagos −0,4, Antofagasta −0,3, Atacama −0,2, Coquimbo −0,1).
- 2020 es un año raro: la cobertura baja en 13 de las 16 regiones (Chile 46,1 % → 44,7 %) y en 2021 rebota (47,8 %).

**Año de referencia: 2024** para todas las comparaciones del bloque (barras, listas, tabla y descomposición): es el año del Censo (la única población medida) y el último con ocupados por región. La cobertura de 2025 existe pero su población es proyección y no hay empleo regional. El gráfico tiene dos períodos (2019-2024 con las 16 regiones; 2002-2024 con Tarapacá+Arica, Los Lagos+Los Ríos y Biobío+Ñuble fusionadas en numerador y denominador) y una casilla para usar la proyección del INE sin ajustar, con el Censo 2024 como rombo aparte.

## 2. «Las 5 regiones más importantes»

Hay cuatro listas de 5 (bajo el promedio y en caída, mayor brecha, caída más fuerte, mayor peso), en `docs/SHORTLIST_REGIONES.md`; el tablero deja elegir y **recomienda la primera** (cobertura bajo la de Chile y cayendo desde 2022). Con 2024 como referencia es La Araucanía, Valparaíso, Biobío, Coquimbo y Ñuble, la misma de «mayor brecha». Con 2025 como año final eran La Araucanía, Valparaíso, Biobío, Los Ríos y Los Lagos (Coquimbo y Ñuble se «recuperaban» en 2025, pero con población proyectada).

**Brecha:** prioridad = brecha de cotizantes = (cobertura de Chile − cobertura de la región) × población 15-64 de la región = cuántos cotizantes más habría si alcanzara el promedio. Pesa el nivel (qué tan baja es) y el tamaño (cuánta gente). Es la misma fórmula que propone el informe de Claude Desktop.

| # | Región | Peso (% de los cotizantes) | Nivel: cobertura 2024 | Tendencia desde 2019 | Desde 2022 | Brecha |
|---|---|---|---|---|---|---|
| 1 | La Araucanía | 4,2 | 36,5 % | +1,5 | −0,4 | 67.220 |
| 2 | Valparaíso | 9,1 | 42,2 % | +0,3 | −1,3 | 53.660 |
| 3 | Biobío | 8,1 | 43,3 % | +2,1 | −0,8 | 34.037 |
| 4 | Coquimbo | 3,9 | 40,5 % | +2,4 | −0,1 | 33.343 |
| 5 | Ñuble | 2,2 | 37,8 % | +1,6 | −0,7 | 29.346 |

Metropolitana (44,8 % de los cotizantes) **no entra** porque su cobertura (51,0 %) está sobre el promedio. Si «importante» significa «más cotizantes», es la lista «mayor peso» (columnas `prioridad_*` de `kpi_cobertura_regiones.csv`; `prioridad` es la recomendada).

## 3. Datos nuevos (`Data raw/_external/ine_ene_regional/`, `bcentral_pib_regional/` y `aafp_cobertura_regiones/`)

Descargados a mano por el equipo el 2026-11-09. Llegaron en una carpeta de paso (`import razones/`) y se ordenaron en `_external/`, con nombres descriptivos (la tabla código → nombre está en `ine_ene_regional/LEEME.md`). Los 21 `.xls` no son Excel binario sino **XML de Excel 2003** del explorador de datos del INE (se leen con `ElementTree`, sin librerías de Excel). Los archivos tienen nombre con código: el script los reconoce por su contenido.

| Contenido | Archivos | Se usa |
|---|---|---|
| **ENE por región y trimestre móvil, ambos sexos** (INE, proyecciones base 2017, 2010 a mar-may 2024): ocupados | 1 | Sí |
| ídem desocupados | 1 | Sí |
| ídem ocupados informales, tasa de ocupación informal (+1 copia en inglés), tasa en el sector informal, tasa informal sin agropecuario (desde jul-sep 2017) | 5 | Sí |
| ídem tasa de tiempo parcial involuntario | 1 | Sí |
| ENE por región, categoría ocupacional / rama / grupo ocupacional, pero **solo el total** | 3 | No (sin corte útil) |
| ENE solo país, por tramo de edad o por nivel educacional (ocupados, desocupados, tiempo parcial); tasa informal por rama | 10 | No (no sirven para comparar regiones) |
| PIB regional trimestral, volumen encadenado, ref. 2018, 2013-I a 2026-II (Banco Central); **15 regiones, falta Magallanes**; solo el total | 1 `.xlsx` | Sí |
| Estudio de la Asociación de AFP (IPE N° 135): cobertura, informalidad y ocupados, diciembre 2019 y 2024 | 1 PDF | Contraste |

### Validación

Con los ocupados, desocupados e informales del INE y los cotizantes de la Superintendencia, **se reproducen las cifras del estudio de la AAFP en las 16 regiones**: ocupados de diciembre 2019 (diferencia < 0,01 %), desocupación e informalidad 2019 (iguales), cotizantes ÷ ocupados 2019 y 2024 (diferencia máxima 0,0 puntos). Tres consecuencias: (1) leí bien los archivos y el trimestre «diciembre» del INE es nov-ene; (2) los cotizantes de `cotizantes_region.xls` son los «cotizantes del mes» (sin honorarios) que usa la AAFP; (3) las cifras del estudio son recalculables. También coincide el saldo migratorio del Censo: RM −216.023, Valparaíso +44.917, La Araucanía +42.993, Maule +39.881 (el informe cita −218.317, +44.480, +42.842, +39.688; menos de 1 % de diferencia, otro tratamiento de los casos sin dato).

## 4. Descomposición: de dónde viene la diferencia

La cobertura es exactamente **participación × empleo × cotización de los ocupados**:

```
cotizantes / pob. 15-64  =  (fuerza de trabajo / pob. 15-64) × (ocupados / fuerza de trabajo) × (cotizantes / ocupados)
                                participación laboral             1 − desocupación               ocupados que cotizan
```

Cada hipótesis del profesor cae en un factor: desempleo → empleo; informalidad y rama → ocupados que cotizan; participación (mujeres, desaliento) → participación. Los aportes se miden en puntos con la media logarítmica y **suman exacto** la diferencia de cobertura (test `test_aportes_suman_exacto_la_diferencia_de_cobertura`). «Hoy» es diciembre de 2024, el último con ocupados y desocupados por región (2010-2023: exportaciones del INE; 2024: anexo del estudio de la Asociación de AFP, la misma serie). Para 2025 no hay empleo regional.

**Diferencia con Chile hoy, 2024 (puntos de cobertura; las 5 regiones prioritarias recomendadas):**

| Región | Participación | Empleo | Ocupados que cotizan | Total |
|---|---|---|---|---|
| La Araucanía | −1,9 | −0,4 | **−7,7** | −10,0 |
| Ñuble | −1,3 | −0,4 | **−7,0** | −8,6 |
| Coquimbo | −2,1 | +0,1 | **−4,0** | −6,0 |
| Valparaíso | −0,5 | −0,0 | **−3,7** | −4,2 |
| Biobío | **−2,8** | −0,3 | +0,1 | −3,1 |

Lectura: en 4 de las 5 la diferencia viene sobre todo de que menos ocupados cotizan (La Araucanía, Ñuble, Coquimbo, Valparaíso); en Biobío viene de la participación. **El desempleo casi no aporta** (entre −0,4 y +0,1 puntos). Promedio de las 5: cotización −4,5, participación −1,7, empleo −0,2.

**Cambios hasta hoy:** entre 2019 y 2024 la cobertura sumó +1,6 puntos en promedio en las 5 (La Araucanía +1,5, Biobío +2,1, Coquimbo +2,4, Ñuble +1,6, Valparaíso +0,3), por «ocupados que cotizan» (+2,0 en promedio, Coquimbo +3,8); Valparaíso es la excepción (−0,3 de cotización), en línea con el estudio de la Asociación de AFP, que le calcula −0,4. Entre 2023 y 2024 los cambios son chicos (+0,7 en promedio). En el tablero se elige «Diferencia con Chile hoy», «Cambio entre 2023 y hoy» o «Cambio entre 2019 y hoy», y las filas se ordenan por cada columna.

## 5. Asociaciones con la cobertura 2024 (16 regiones, no causas)

| Factor | Hipótesis | r | p | Fuente |
|---|---|---|---|---|
| Ocupados informales (tasa oficial) | Informalidad | −0,83 | < 0,001 | ENE dic. 2023 |
| Ingreso per cápita | Otros | +0,77 | < 0,001 | CASEN 2022 |
| Participación laboral (de 15+) | Otros | +0,74 | < 0,001 | Censo 2024 |
| Ocupados en enseñanza (%) | Industria | −0,73 | 0,001 | Censo 2024 |
| Migración interna neta en 5 años | Migración | −0,66 | 0,006 | Censo 2024 |
| Desocupación oficial | Desempleo | **−0,32 (no significativa)** | 0,23 | ENE dic. 2023 |

Otros resultados del cuadro completo (34 factores sobre el nivel, 3 sobre el cambio; desplegable «Exploración» del dashboard): informalidad sin agricultura −0,81, ocupados en el sector informal −0,75, participación oficial de la ENE +0,72, PIB por habitante +0,71 (n = 15), PIB por ocupado +0,68, participación de las mujeres +0,65, crecimiento del PIB 2013-2023 −0,59, tiempo parcial involuntario −0,46 (n.s.). Los cambios 2019-2023 de desocupación, informalidad y participación **no se asocian** con el cambio de la cobertura (|r| ≤ 0,19).

**Cambio de regla frente a la primera versión:** antes se mostraba la mejor correlación por hipótesis; con eso «desempleo» era la desocupación del Censo (r = −0,71). Ahora se muestra la medida **oficial** (ENE), que no es significativa. La diferencia entre ambas (Censo en abril de 2024, ENE en diciembre de 2023) está anotada en supuestos 4.4. Mostrar la que mejor calza entre 37 pruebas habría exagerado el papel del desempleo.

**Cómo leerlo:**
- La informalidad oficial es en parte lo mismo que «no cotiza» (se cuenta como informal al dependiente sin cotizaciones por su empleo): una asociación alta es casi una tautología, y lo que aporta es la descomposición (el aporte está en el factor «ocupados que cotizan»).
- «Ocupados en enseñanza» es probablemente un efecto de composición, no una causa.
- La migración interna neta positiva (más llegados que salidos) se asocia a **menor** cobertura (La Araucanía, Los Ríos, Ñuble: +45 a +50 por mil). El Censo no dice quién llega.
- Industria con más peso frente a Chile: La Araucanía y Ñuble, agricultura (1,6× y 2,2×); Coquimbo, minería (3,6×); Valparaíso, minería (1,2×); Biobío, industria manufacturera (1,3×). En todas el comercio es la rama más grande. El PIB por rama de actividad no está disponible.

## 6. Comparación con el enfoque de Claude Desktop

Se comparó lo hecho antes de esta ronda con el prompt y el informe que preparó Claude Desktop, punto por punto.

| Punto del prompt / informe | Antes | Ahora | Comentario |
|---|---|---|---|
| Paso 0: definición de cotizantes | No estaba | `supuestos_y_limitaciones.md` §0.1 | Mes de referencia (diciembre) sí; **honorarios: el archivo no lo dice**, se deduce que no por el contraste con la AAFP |
| Paso 0: prueba de asignación RM | No estaba | §0.2 y expander del dashboard | La RM pesa 1-5 puntos más en cotizantes que en ocupados; no se concluye |
| Paso 1: numerador `cotizantes_por_region.csv` | Sí | Sí | |
| Paso 1: denominador INE base 2017 y el Censo como **marcador aparte**, sin empalmar | Línea ajustada al Censo (constante por región), sin marcador | Por defecto igual (así 2024 coincide con el KPI y se respeta «el Censo manda»); casilla para la proyección sin ajustar con el Censo como rombo | El ajuste es un factor constante: **la forma de la serie es la misma**; solo cambia el nivel (Chile 2025: 46,9 % vs 43,4 %). El informe teme un «salto»: con ajuste constante no hay salto |
| Paso 1: serie larga con Tarapacá+Arica, Los Lagos+Los Ríos, Biobío+Ñuble | Solo Biobío+Ñuble y desde 2010 | Las tres fusiones, 2002-2025 | |
| Paso 1: ventana corta 2019-2025 con 16 regiones | No | Sí (por defecto) | |
| Paso 1: país + 5 regiones prioritarias, marcar 2020-2021 | 15 paneles con las 5 en naranja, sin marca | 16 paneles (o 13) con las 5 en naranja, Chile en gris y franja 2020-2021 | Una sola gráfica con 6 líneas rompe la pauta de la clase (máximo 4 líneas): se usan paneles pequeños |
| Paso 2: brecha = (cob. nacional − cob. región) × pob. 15-64; tabla con peso, nivel y tendencia | Brecha y tabla sin peso | Igual fórmula, tabla con peso, nivel y tendencia 2019 y 2022 | Misma lista de 5 regiones |
| Paso 3: descomposición en tres factores | No estaba | Sí, con el Censo aplicado también a los ocupados | El «ajuste al Censo» como factor propio daba ±3 puntos artificiales; se eliminó al llevar ocupados al nivel del Censo. Se usó la media logarítmica en vez de «log-diferencias simples» para que la suma sea exacta |
| Paso 3: nombre `Scripts/10_explorar_causas.py` | — | `Scripts/25_explorar_causas.py` | El 10 ya existe (`10_procesar_piramide_alemania.py`) |
| Paso 3: cruces descriptivos sin regresión | Correlaciones con el Censo | Con ENE oficial; sin regresión | |
| Desocupación, informalidad oficiales | Aproximación con el Censo | ENE (INE) | |
| % cuenta propia | Independientes del Censo | Igual | La ENE regional por categoría ocupacional bajó solo con el total |
| Participación femenina | No | Censo 2024 (la ENE trae «Ambos sexos») | Falta la oficial |
| Estructura por rama | Censo | Censo | ENE por rama regional: solo total |
| Saldo migratorio 2019-2024 | Censo | Censo (coincide con el informe) | |
| Cada gráfico con fuente y año | Solo algunos | Los nuevos y el de factores llevan «Fuente: …» | |
| Lenguaje no causal | Sí | Sí | |
| Limitaciones en `docs/supuestos_y_limitaciones.md` | No existía | Creado | |
| Contraste AAFP | No | Expander y tabla; coincide al decimal | |

**Qué dice el informe de Claude Desktop que no se confirmó o no coincide con el proyecto:**
- Dice que `regional_2002_2035_base2017.csv` «está en el proyecto»: no estaba. Se descargó el archivo comunal del INE (11 MB) y se agrega por región.
- «KPI 1.1 tiene dos gráficos de barras (razón de soporte y cobertura)»: en el tablero actual son el mapa y las barras regionales (bloque 1), el diagrama de dispersión con tres variables (bloque 2) y la matriz de riesgo (bloque 3). El «gráfico 2 y 3» del profesor corresponde con alta probabilidad a la dispersión y la matriz.
- Cifras de desocupación por región de abril-junio de 2026 que cita (Ñuble 10,5 %, etc.): **no se pueden verificar con los archivos bajados**, que terminan en mar-may 2024.
- Su advertencia de que informalidad es «parcialmente circular» sí se confirmó (r = −0,83).
- Sobre la industria: dice que la ENE por rama regional «no está confirmada»; de hecho el archivo bajado trae rama «Total» solamente.

## 7. Qué falta y cómo bajarlo

Dejar cada archivo en una carpeta nueva de `Data raw/` y avisar.

1. **ENE por región, base 2024, desde jun-ago 2024.** Explorador de datos del INE ([stats.ine.cl](https://stats.ine.cl)), mismos conjuntos que los de `ine_ene_regional/`. Con eso la descomposición llega a 2024-2025.
2. **ENE regional por sexo** (Ocupados, Desocupados y Población en edad de trabajar, segmento «Mujeres») para la participación femenina oficial.
3. **ENE regional por rama de actividad y por categoría ocupacional**: en los conjuntos «Ocupados según rama…» y «…según categoría ocupacional» hay que seleccionar **todas** las ramas / categorías (los archivos bajados traen solo «Total»).
4. **Cotizantes por rama de actividad y densidad de cotizaciones por región**, Superintendencia de Pensiones ([spensiones.cl](https://www.spensiones.cl) → Estadísticas): con la rama de los cotizantes y la de los ocupados se calcula qué parte de cada industria cotiza.
5. **PIB regional por actividad económica y Magallanes**, Banco Central ([si3.bcentral.cl](https://si3.bcentral.cl) → PIB regional → «Exportar a Excel»; máximo 25 series por exportación).
6. **Proyección de población regional base 2024** del INE, anunciada para el segundo semestre de 2026 ([noticia del INE del 28-ene-2026](https://www.ine.gob.cl/sala-de-prensa/prensa/general/noticia/2026/01/28/el-ine-proyecta-que-en-2026-la-poblaci%C3%B3n-de-chile-alcanzar%C3%A1-las-20.150.948-personas-llegando-a-su-nivel-m%C3%A1ximo-a-mediados-de-la-pr%C3%B3xima-d%C3%A9cada)): reemplaza la base 2017 en el script 24.
7. **Pregunta opcional a la Superintendencia de Pensiones:** ¿los cotizantes se asignan a la región de residencia o a la del empleador, y los honorarios están incluidos? No bloquea nada: el análisis sigue con lo que se sabe y lo declara (supuestos §0.1 y §0.2).
