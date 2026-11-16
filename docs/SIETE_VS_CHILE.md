# Las 8 regiones prioritarias frente al promedio de Chile

Documento generado por `Scripts/25_explorar_causas.py` (`Data processed/kpi_cobertura_siete_vs_chile.csv`); se rehace solo cada vez que se corre el script. Regiones: **Ñuble, Valparaíso, Los Ríos, La Araucanía, Biobío, Coquimbo, Arica y Parinacota, Tarapacá**.

**Cómo leer los promedios.** Son **agregados**, no promedios simples de tasas: la cobertura de «las 8 juntas» es la suma de sus cotizantes dividida por la suma de su población de 15 a 64 años; las tasas de empleo se ponderan con los ocupados o la fuerza de trabajo, y el resto con la población. «Chile» es la suma de las 16 regiones (igual que en la descomposición del dashboard) y «las otras 8» son las regiones no seleccionadas. Así el promedio de las 8 se compara de igual a igual con el del país.

## 1. Nivel y cambio de la cobertura

| Indicador | Las 8 juntas | Chile | Las otras 8 | Las 8 menos Chile | Cómo se calcula |
|---|---|---|---|---|---|
| Cobertura 2024 (% de 15-64) | 40,9 | 46,5 | 49,7 | −5,6 | cotizantes ÷ población 15-64 de las regiones sumadas |
| Cambio desde 2019 (puntos) | +1,3 | +0,7 | +0,3 | +0,6 | cobertura del grupo en 2024 menos en 2019 |
| Cambio desde 2022 (puntos) | −0,8 | −0,7 | −0,7 | −0,1 | cobertura del grupo en 2024 menos en 2022 |
| Cotizantes desde 2022 (personas) | −26.611 | −54.201 | −27.590 | — | suma de las regiones |
| Cotizantes desde 2022 (%) | −1,4 | −0,9 | −0,7 | −0,5 | suma de las regiones |

Las 8 regiones juntas tienen una cobertura de **40,9 %**, frente a 46,5 % de Chile y 49,7 % de las otras 8: **5,6 puntos bajo el país**. Desde 2019 subieron 1,3 puntos (Chile: 0,7); desde 2022 −0,8 (Chile: −0,7), y su cantidad de cotizantes cambió −1,4 % frente a −0,9 % del país.

**Dos lecturas honestas.** (1) La brecha de las 8 con el país es sobre todo de **nivel**, no de caída reciente: desde 2022 su cobertura cae casi igual que la del resto (−0,8 puntos frente a −0,7); lo que sí es peor es la pérdida de cotizantes en personas (−1,4 % frente a −0,7 % en las otras 8). (2) Desde 2019 el grupo mejoró más que el país (+1,3 frente a +0,7 puntos): la distancia con Chile se achicó 0,6 puntos, aunque sigue en 5,6.

## 2. Cuánto pesan

| Indicador | Las 8 juntas | Chile | Las otras 8 | Las 8 menos Chile | Cómo se calcula |
|---|---|---|---|---|---|
| Parte de la población de 15 a 64 años (%) | 36,6 | 100,0 | 63,4 | — | Censo 2024 |
| Parte de los cotizantes (%) | 32,2 | 100,0 | 67,8 | — | suma de las regiones |
| Brecha de cotizantes frente a Chile (personas) | 258.198 | — | 37.133 | — | suma de las brechas regionales (solo regiones bajo el promedio) |

## 3. De dónde viene la diferencia con Chile (las 8 juntas como un solo territorio)

| Indicador | Las 8 juntas | Chile | Las otras 8 | Las 8 menos Chile | Cómo se calcula |
|---|---|---|---|---|---|
| Participación laboral (de 15 a 64 años) (puntos) | −1,6 | +0,0 | +1,0 | −1,6 | descomposición exacta del grupo como un solo territorio |
| Empleo (1 − desocupación) (puntos) | −0,1 | +0,0 | +0,1 | −0,1 | descomposición exacta del grupo como un solo territorio |
| Ocupados que cotizan (puntos) | −3,9 | +0,0 | +2,2 | −3,9 | descomposición exacta del grupo como un solo territorio |
| Diferencia total (puntos) | −5,6 | +0,0 | +3,2 | −5,6 | suma de las tres piezas |

La diferencia total de las 8 con el país es de **−5,6 puntos**; de ellos, −3,9 vienen de que menos ocupados cotizan, −1,6 de la participación laboral y −0,1 del desempleo. Las otras 8 regiones, en cambio, están +3,2 puntos respecto del país (sobre el promedio).

## 4. Cómo cambió la cobertura desde 2019, por pieza

| Indicador | Las 8 juntas | Chile | Las otras 8 | Las 8 menos Chile | Cómo se calcula |
|---|---|---|---|---|---|
| Participación laboral (puntos) | +0,3 | −0,0 | −0,2 | +0,3 | descomposición del cambio de cada grupo |
| Empleo (puntos) | −0,3 | −0,3 | −0,3 | −0,1 | descomposición del cambio de cada grupo |
| Ocupados que cotizan (puntos) | +1,4 | +1,0 | +0,7 | +0,4 | descomposición del cambio de cada grupo |

## 5. El resto de los indicadores

| Indicador | Las 8 juntas | Chile | Las otras 8 | Las 8 menos Chile | Cómo se calcula |
|---|---|---|---|---|---|
| Informalidad (tasa oficial, ENE dic. 2023) (%) | 32,2 | 27,6 | 25,2 | +4,7 | promedio ponderado por ocupados 2023 |
| Desocupación (ENE dic. 2023) (%) | 8,7 | 8,4 | 8,3 | +0,2 | promedio ponderado por fuerza de trabajo 2023 |
| Participación laboral de 15 a 64 años (Censo 2024) (%) | 64,9 | 68,1 | 70,0 | −3,2 | promedio ponderado por población 15-64 |
| Participación laboral de las mujeres de 15+ (Censo 2024) (%) | 46,4 | 50,6 | 53,0 | −4,2 | promedio ponderado por población 15-64 |
| Ocupados independientes (Censo 2024) (%) | 34,5 | 33,8 | 33,4 | +0,8 | promedio ponderado por ocupados 2023 |
| Ingreso per cápita (CASEN 2022) ($ al mes) | 439.846 | 530.177 | 583.717 | −90.331 | promedio ponderado por población total |
| Pobreza en personas de 65+ (CASEN 2022) (%) | 17,0 | 14,9 | 13,5 | +2,1 | promedio ponderado por personas de 65+ |
| Personas de 65+ (Censo 2024) (% de la población) | 15,1 | 14,0 | 13,3 | +1,1 | promedio ponderado por población total |
| Población urbana (Censo 2024) (%) | 81,8 | 86,7 | 89,6 | −4,9 | promedio ponderado por población total |
| Migración interna neta en 5 años (Censo 2024) (por 1.000 habitantes) | 25,4 | 0,2 | −14,8 | +25,2 | promedio ponderado por población total |
| Ocupados que trabajan en otra región (Censo 2024) (%) | 6,3 | 3,5 | 2,1 | +2,8 | promedio ponderado por ocupados que viven en la región |

## Límites

- Los promedios ocultan diferencias entre las regiones del grupo (La Araucanía y Los Ríos tienen la cotización mucho más baja que Biobío, por ejemplo); el detalle por región está en `docs/ANALISIS_SIETE_REGIONES.md` y en el dashboard.
- La descomposición del grupo trata a las 8 regiones como un solo territorio: es exacta, pero sus piezas no son el promedio de las piezas de cada región.
- Las tasas de la ENE son de diciembre de 2023; la desocupación y la informalidad de 2024 no están por región en los archivos bajados (solo en el anexo del estudio de la Asociación de AFP).
- Todo es asociación y aritmética, no causa; con 16 regiones no hay regresión.
