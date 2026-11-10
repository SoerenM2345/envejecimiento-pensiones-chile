# Las 7 regiones prioritarias frente al promedio de Chile

Documento generado por `Scripts/25_explorar_causas.py` (`Data processed/kpi_cobertura_siete_vs_chile.csv`); se rehace solo cada vez que se corre el script. Regiones: **Ñuble, Valparaíso, Los Ríos, La Araucanía, Biobío, Coquimbo, Arica y Parinacota**.

**Cómo leer los promedios.** Son **agregados**, no promedios simples de tasas: la cobertura de «las 7 juntas» es la suma de sus cotizantes dividida por la suma de su población de 15 a 64 años; las tasas de empleo se ponderan con los ocupados o la fuerza de trabajo, y el resto con la población. «Chile» es la suma de las 16 regiones (igual que en la descomposición del dashboard) y «las otras 9» son las regiones no seleccionadas. Así el promedio de las 7 se compara de igual a igual con el del país.

## 1. Nivel y cambio de la cobertura

| Indicador | Las 7 juntas | Chile | Las otras 9 | Las 7 menos Chile | Cómo se calcula |
|---|---|---|---|---|---|
| Cobertura 2024 (% de 15-64) | 40,7 | 46,5 | 49,5 | −5,7 | cotizantes ÷ población 15-64 de las regiones sumadas |
| Cambio desde 2019 (puntos) | +1,3 | +0,7 | +0,3 | +0,6 | cobertura del grupo en 2024 menos en 2019 |
| Cambio desde 2022 (puntos) | −0,8 | −0,7 | −0,7 | −0,1 | cobertura del grupo en 2024 menos en 2022 |
| Cotizantes desde 2022 (personas) | −28.037 | −54.201 | −26.164 | — | suma de las regiones |
| Cotizantes desde 2022 (%) | −1,6 | −0,9 | −0,6 | −0,6 | suma de las regiones |

Las 7 regiones juntas tienen una cobertura de **40,7 %**, frente a 46,5 % de Chile y 49,5 % de las otras 9: **5,7 puntos bajo el país**. Desde 2019 subieron 1,3 puntos (Chile: 0,7); desde 2022 −0,8 (Chile: −0,7), y su cantidad de cotizantes cambió −1,6 % frente a −0,9 % del país.

**Dos lecturas honestas.** (1) La brecha de las 7 con el país es sobre todo de **nivel**, no de caída reciente: desde 2022 su cobertura cae casi igual que la del resto (−0,8 puntos frente a −0,7); lo que sí es peor es la pérdida de cotizantes en personas (−1,6 % frente a −0,6 % en las otras 9). (2) Desde 2019 el grupo mejoró más que el país (+1,3 frente a +0,7 puntos): la distancia con Chile se achicó 0,6 puntos, aunque sigue en 5,7.

## 2. Cuánto pesan

| Indicador | Las 7 juntas | Chile | Las otras 9 | Las 7 menos Chile | Cómo se calcula |
|---|---|---|---|---|---|
| Parte de la población de 15 a 64 años (%) | 34,6 | 100,0 | 65,4 | — | Censo 2024 |
| Parte de los cotizantes (%) | 30,3 | 100,0 | 69,7 | — | suma de las regiones |
| Brecha de cotizantes frente a Chile (personas) | 250.266 | — | 45.065 | — | suma de las brechas regionales (solo regiones bajo el promedio) |

## 3. De dónde viene la diferencia con Chile (las 7 juntas como un solo territorio)

| Indicador | Las 7 juntas | Chile | Las otras 9 | Las 7 menos Chile | Cómo se calcula |
|---|---|---|---|---|---|
| Participación laboral (de 15 a 64 años) (puntos) | −1,6 | +0,0 | +0,9 | −1,6 | descomposición exacta del grupo como un solo territorio |
| Empleo (1 − desocupación) (puntos) | −0,1 | +0,0 | +0,1 | −0,1 | descomposición exacta del grupo como un solo territorio |
| Ocupados que cotizan (puntos) | −4,0 | +0,0 | +2,0 | −4,0 | descomposición exacta del grupo como un solo territorio |
| Diferencia total (puntos) | −5,7 | +0,0 | +3,0 | −5,7 | suma de las tres piezas |

La diferencia total de las 7 con el país es de **−5,7 puntos**; de ellos, −4,0 vienen de que menos ocupados cotizan, −1,6 de la participación laboral y −0,1 del desempleo. Las otras 9 regiones, en cambio, están +3,0 puntos respecto del país (sobre el promedio).

## 4. Cómo cambió la cobertura desde 2019, por pieza

| Indicador | Las 7 juntas | Chile | Las otras 9 | Las 7 menos Chile | Cómo se calcula |
|---|---|---|---|---|---|
| Participación laboral (puntos) | +0,2 | −0,0 | −0,1 | +0,2 | descomposición del cambio de cada grupo |
| Empleo (puntos) | −0,4 | −0,3 | −0,2 | −0,1 | descomposición del cambio de cada grupo |
| Ocupados que cotizan (puntos) | +1,5 | +1,0 | +0,7 | +0,5 | descomposición del cambio de cada grupo |

## 5. El resto de los indicadores

| Indicador | Las 7 juntas | Chile | Las otras 9 | Las 7 menos Chile | Cómo se calcula |
|---|---|---|---|---|---|
| Informalidad (tasa oficial, ENE dic. 2023) (%) | 32,0 | 27,6 | 25,5 | +4,5 | promedio ponderado por ocupados 2023 |
| Desocupación (ENE dic. 2023) (%) | 8,9 | 8,4 | 8,2 | +0,4 | promedio ponderado por fuerza de trabajo 2023 |
| Participación laboral de 15 a 64 años (Censo 2024) (%) | 64,7 | 68,1 | 69,9 | −3,4 | promedio ponderado por población 15-64 |
| Participación laboral de las mujeres de 15+ (Censo 2024) (%) | 45,9 | 50,6 | 53,1 | −4,7 | promedio ponderado por población 15-64 |
| Ocupados independientes (Censo 2024) (%) | 34,3 | 33,8 | 33,5 | +0,5 | promedio ponderado por ocupados 2023 |
| Ingreso per cápita (CASEN 2022) ($ al mes) | 438.715 | 530.177 | 579.888 | −91.462 | promedio ponderado por población total |
| Pobreza en personas de 65+ (CASEN 2022) (%) | 17,1 | 14,9 | 13,5 | +2,2 | promedio ponderado por personas de 65+ |
| Personas de 65+ (Censo 2024) (% de la población) | 15,4 | 14,0 | 13,2 | +1,4 | promedio ponderado por población total |
| Población urbana (Censo 2024) (%) | 81,0 | 86,7 | 89,8 | −5,7 | promedio ponderado por población total |
| Migración interna neta en 5 años (Censo 2024) (por 1.000 habitantes) | 28,8 | 0,2 | −15,4 | +28,6 | promedio ponderado por población total |
| Ocupados que trabajan en otra región (Censo 2024) (%) | 6,5 | 3,5 | 2,1 | +3,0 | promedio ponderado por ocupados que viven en la región |

## Límites

- Los promedios ocultan diferencias entre las regiones del grupo (La Araucanía y Los Ríos tienen la cotización mucho más baja que Biobío, por ejemplo); el detalle por región está en `docs/ANALISIS_SIETE_REGIONES.md` y en el dashboard.
- La descomposición del grupo trata a las 7 regiones como un solo territorio: es exacta, pero sus piezas no son el promedio de las piezas de cada región.
- Las tasas de la ENE son de diciembre de 2023; la desocupación y la informalidad de 2024 no están por región en los archivos bajados (solo en el anexo del estudio de la Asociación de AFP).
- Todo es asociación y aritmética, no causa; con 16 regiones no hay regresión.
