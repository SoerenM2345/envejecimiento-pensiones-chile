# Supuestos y limitaciones: cobertura previsional por región (KPI 1.1)

Documento vivo. Cada gráfico del KPI 1.1 que mira la tendencia o las causas de la cobertura remite aquí. Los números salen de `Scripts/24_cobertura_tendencia_causas.py` y `Scripts/25_explorar_causas.py`; los conflictos entre fuentes están en `docs/DISCUSION_FUENTES.md` y la exploración en `docs/EXPLORACION_COBERTURA.md`.

Regla de lenguaje: lo que se muestra son **asociaciones y descomposiciones aritméticas**, no causas. Con 16 regiones no se hace regresión.

## 0. Antes de construir: qué cuentan los cotizantes

### 0.1 Definición (primeras filas de `Data raw/cotizantes_region.xls`, Superintendencia de Pensiones)

| Campo | Lo que dice el archivo |
|---|---|
| Título | «Cotizantes por región (1)» y «Número de cotizantes por región (2)» |
| Nota (1) | «Cifras a diciembre de cada año» |
| Nota (2) | «Corresponde al número de afiliados que cotizaron durante diciembre de cada año, por remuneraciones devengadas en el mes anterior» |
| Periodo | 1985-2025, regiones I a XVI y «Sin información» |
| Honorarios | **El archivo no lo dice.** |

Lo que se pudo comprobar: el estudio de la Asociación de AFP (informe N° 135) dice que usa «la estadística de cotizantes del mes disponible en la Superintendencia de Pensiones» y que esa **no incluye a los independientes con boleta de honorarios** ni las cotizaciones declaradas y no pagadas (esas están en otra serie, la de «cotizantes totales», que se publica con mucho retraso). Con los cotizantes de este archivo y los ocupados del INE, la cobertura de la AAFP de 2019 y de 2024 sale **idéntica en las 16 regiones** (diferencia máxima 0,0 puntos, `kpi_cobertura_contraste_aafp.csv`). Es decir, el archivo es la misma estadística que la AAFP llama «cotizantes del mes»: cotizantes de diciembre **sin** honorarios.

**Consecuencia:** una región con muchos independientes a honorarios (La Araucanía 31 %, Aysén 32 %, Arica 30 % de los ocupados son independientes según la AAFP) queda con menos cotizantes por definición. Esto no es un error, pero hay que decirlo: parte de la «baja cobertura» es que esos trabajadores no están en la estadística. Posible quiebre de serie desde 2019 (Ley 21.133, los honorarios empiezan a cotizar por la operación renta): **no se pudo comprobar** en el archivo, que no separa las series.

### 0.2 Prueba de asignación regional

¿Se cuenta al cotizante en la región donde vive o en la de su empleador? Ni la Superintendencia ni la AAFP lo dicen. Prueba pedida: participación de la Región Metropolitana en los cotizantes frente a su participación en los ocupados (`kpi_cobertura_test_asignacion.csv`):

| Fecha | RM en los cotizantes | RM en los ocupados (ENE) | RM en la población de 15 a 64 años |
|---|---|---|---|
| Diciembre 2010 | 47,4 % | 42,4 % | 39,0 % |
| Diciembre 2015 | 45,7 % | 42,4 % | 39,1 % |
| Diciembre 2019 | 45,8 % | 43,6 % | 40,2 % |
| Diciembre 2023 | 45,2 % | 44,2 % | 40,8 % |
| Censo 2024 (abril) | 44,8 % | 43,4 % | 41,1 % |

Resultado, sin concluir más: la Metropolitana pesa **más en los cotizantes que en los ocupados** en todas las fechas, y la diferencia **se achica** (5,0 puntos en 2010, 1,0 en 2023). Con estos datos no se distingue entre «se asigna por la región de la empresa» (las casas matrices están en Santiago) y «la Metropolitana tiene más empleo formal». Para saberlo habría que preguntarle a la Superintendencia cuál es la regla; **no bloquea nada**: mientras no se sepa, el argumento de migración se presenta como contexto y no como causa (cambia el denominador; el numerador solo si se asigna por residencia).

## 1. Población (denominador)

| # | Supuesto o límite | Efecto |
|---|---|---|
| 1.1 | La población regional por año es la proyección del INE base 2017 llevada al nivel del Censo 2024 con un factor constante por región (0,88 a 1,00; Antofagasta y Metropolitana los más bajos, Ñuble 1,00). Solo corrige el nivel. | La tendencia no cambia; el nivel sí (Chile 2025: 46,9 % ajustado, 43,4 % sin ajustar). La casilla «Población proyectada sin ajustar» del gráfico muestra ambas. |
| 1.2 | 2018-2025 son proyecciones, no datos. No incorporan lo que mostró el Censo 2024 (p. ej. migración distinta a la esperada). | Las tendencias de los últimos años dependen de una proyección anterior al Censo. |
| 1.3 | La proyección regional base 2024 del INE aún no está publicada (anunciada para el segundo semestre de 2026). | Cuando salga, reemplazar la base 2017 en el script 24. |
| 1.4 | El Censo contó menos gente que la proyección en casi todo el país, pero **más en Ñuble**. El factor del Censo puede reflejar subconteo censal o error de la proyección; no se distingue. | Si el subconteo difiere por región, el nivel relativo entre regiones se mueve. |
| 1.5 | Chile antes de 2010 = suma de las regiones empalmada con la serie del KPI 1.2 en 2010 (diferencia de 0,2 puntos). | Solo afecta la línea gris de la ventana larga. |

## 2. Cotizantes (numerador) y cambios de regiones

| # | Supuesto o límite | Efecto |
|---|---|---|
| 2.1 | Hasta 2006 Arica y Parinacota va dentro de Tarapacá y Los Ríos dentro de Los Lagos; hasta 2017, Ñuble dentro de Biobío. La serie larga (desde 2002) fusiona los pares en numerador **y** denominador (series 801, 810, 816). | Sin esto, los cotizantes de Tarapacá «caían» 36 % en 2007 y la cobertura de Biobío 10 puntos en 2018. |
| 2.2 | Entre 2006 y 2007 la cobertura sube 2 a 4 puntos en 12 de los 13 territorios (Chile 34,1 % → 37,2 %). No viene de las fusiones. Puede ser un cambio en cómo se cuenta o un efecto real; **no está confirmado**. | La ventana larga (2002-2025) mezcla ese salto con el crecimiento real. |
| 2.3 | Cotizantes «sin región informada» (56 mil en 2024) quedan fuera de los territorios; el país usa los que tienen región. | Subestima la cobertura nacional en 0,4 puntos. |
| 2.4 | **Cotizantes es un registro de diciembre; ocupados, un trimestre móvil (nov-ene).** | La estacionalidad (cosecha, comercio de fin de año) puede mover el cociente en regiones agrícolas. |
| 2.5 | 2020 es un año atípico: la cobertura cae en 13 de las 16 regiones y en 2021 rebota. En la descomposición, «ocupados que cotizan» **sube** en 2020 (de 66,0 % a 72,7 % en Chile) mientras baja la participación: una explicación posible, no verificada, es que perdieron el empleo sobre todo los informales. | Se marcan 2020-2021 en el gráfico. No usar 2020 como base de comparación. |

## 3. Encuesta Nacional de Empleo (ENE) y descomposición

| # | Supuesto o límite | Efecto |
|---|---|---|
| 3.1 | El archivo bajado del explorador del INE usa proyecciones base 2017 y llega a **mar-may 2024**. La descomposición termina en **diciembre de 2023** (trimestre nov-ene). | La cobertura de 2024-2025 no se descompone. Para extenderla hay que bajar la serie base 2024 del mismo explorador (no pude comprobar si el INE ya la publicó). |
| 3.2 | «Diciembre» = trimestre móvil nov-ene (el INE lo rotula por su mes central). Con ese criterio los ocupados, la desocupación y la informalidad de 2019 coinciden con los del estudio de la AAFP. | Validación en `kpi_cobertura_contraste_aafp.csv`. |
| 3.3 | **El Censo manda también en la ENE:** ocupados y fuerza de trabajo se llevan al nivel del Censo con el mismo factor que la población (la ENE los expande con la proyección 2017). Supuesto: la proyección se equivoca en la misma proporción en personas y en ocupados. Sin esto, el «ajuste al Censo» aparecía como un factor de hasta 3 puntos que no es economía sino medición. | Los cotizantes (registro) se comparan con ocupados al nivel del Censo. La razón «cotizantes ÷ ocupados» al nivel del Censo no es la de la AAFP (66,0 % frente a 61,6 % en Chile en 2019), que usa los ocupados tal como los publica el INE. |
| 3.4 | La fuerza de trabajo de la ENE incluye a los de 65+ que trabajan; la cobertura se mide sobre 15-64. «Participación laboral (de 15 a 64 años)» mezcla la participación y el envejecimiento (que se compensan). | Se lee como un solo factor; no se interpreta como «las mujeres no trabajan». |
| 3.5 | La descomposición es aritmética (identidad exacta, media logarítmica): dice **de dónde sale** la diferencia, no por qué. | Un aporte grande de «ocupados que cotizan» no distingue informalidad, honorarios, rotación ni asignación regional. |
| 3.6 | Error muestral: la ENE regional de las regiones chicas (Aysén, Magallanes) fluctúa mucho. Las 5 prioritarias son grandes, pero un solo trimestre sigue siendo ruidoso. | No se promedió por 4 trimestres porque cotizantes es de un mes; sensibilidad pendiente. |
| 3.7 | La ENE da cortes por sexo y por rama solo para el país; los archivos regionales traen «Ambos sexos» y rama «Total». | La participación femenina viene del Censo (2024), no de la ENE. No hay desocupación por rama ni cotizantes por rama. |

## 4. Factores de las asociaciones (n = 16)

| # | Supuesto o límite |
|---|---|
| 4.1 | n = 16 regiones (15 con PIB: **el archivo del Banco Central no trae Magallanes**). Una correlación de |r| = 0,5 con n = 16 tiene p ≈ 0,05. |
| 4.2 | Se probaron 34 factores sobre el nivel y 3 sobre el cambio: con tantos, 1 o 2 salen significativos por azar. Por eso se muestra la medida **oficial** de cada hipótesis (desocupación e informalidad de la ENE, migración del Censo), aunque no sea la que mejor calza, y no «la que salió». |
| 4.3 | **Informalidad oficial = en parte «no cotiza».** La ENE cuenta como informal al dependiente sin cotizaciones previsionales por su empleo (y al independiente cuyo negocio no está registrado). Que la informalidad «explique» la cobertura es en parte lo mismo dicho de otro modo (r = −0,83). |
| 4.4 | Desocupación del Censo (abril 2024) y de la ENE (diciembre 2023) dan correlaciones distintas con la cobertura (−0,71 y −0,32): la definición y el momento importan. El tablero muestra la oficial. |
| 4.5 | «Ocupados en enseñanza» es probablemente un efecto de composición (regiones con poco empleo privado), no una causa. |
| 4.6 | Migración: el Censo da un saldo de 5 años (2019-2024), no una serie. La migración interna neta **positiva** se asocia a **menor** cobertura (La Araucanía, Los Ríos, Ñuble); el Censo no dice quién llega. Si la asignación regional fuera por la región del empleador (punto 0.2), la migración cambiaría el denominador pero no el numerador. |
| 4.7 | **Industria dominante:** el Censo da el empleo por rama, no el producto; el PIB regional del Banco Central bajado es el total, no por actividad. La AAFP asocia las regiones de menor ingreso imponible con economías agrícolas, pero O'Higgins, una de ellas, tiene la mayor cobertura sobre ocupados (70,2 %): «agricultura = baja cobertura» no vale en general. |
| 4.8 | Los factores están medidos en 2023-2024 y la cobertura de 2024: son asociaciones entre regiones en un corte, no cambios en el tiempo. Los 3 cambios 2019-2023 (desocupación, informalidad, participación) no se asocian con el cambio de la cobertura (|r| ≤ 0,19). |

## 5. Fuente con interés propio

La Asociación de AFP es el gremio de las administradoras. Sus cifras salen de la Superintendencia y del INE y se pueden recalcular (se hizo: coinciden); sus interpretaciones («los independientes explican...») no tienen por qué compartirse. Se usa solo como contraste.

## 6. Escenarios fijos del KPI 1.2 (país)

Seis escenarios con supuestos fijos, además del simulador (que sigue igual). Definidos en `Scripts/25_explorar_causas.py` (`kpi_pc_escenarios_fijos.csv`) y calculados con el motor de `Dashboards/components/critical_point.py`; todo lo demás como en `config/escenarios.yaml` (sueldo real +1 % anual, PGU de $250.000, pesos reales de 2025).

| Escenario | Qué cambia | Punto crítico |
|---|---|---|
| Tope de carga 10 % (base) | nada | 2038 |
| Tope de carga 11 % | el sistema tolera 11 % del sueldo | 2044 |
| Tope de carga 12 % | el sistema tolera 12 % del sueldo | 2048 |
| Cobertura sigue cayendo | cobertura −0.18 puntos por año hasta 2050, de 46,9 % a 42,4 % | 2036 |
| Sin informalidad | todos los informales de hoy cotizan desde 2026 (+41 % de cotizantes) | 2055 |
| Mitad del camino | la mitad de los informales cotiza (+21 %) | 2048 |

| # | Supuesto o límite | Efecto |
|---|---|---|
| 6.1 | **«Cobertura sigue cayendo» = tendencia 2022-2025** (ajuste lineal de 4 puntos, −0,18 puntos por año), prolongada hasta 2050 y constante después (así es el motor). La serie cayó de 47,6 % (2022) a 46,0 % (2023) y se recuperó a 46,9 % (2025): la pendiente depende de la ventana (con 2021-2025 sería −0,30). | Con −0,30 el punto crítico sería 2035 en vez de 2036; con la cobertura de 2025 constante, 2038. |
| 6.2 | **«Sin informalidad» es un techo teórico, no una proyección.** Suma a los cotizantes todos los ocupados informales de hoy (ENE, diciembre 2023, llevados al nivel del Censo con el factor de la población: 2.36 millones). Supone que (a) ninguno está hoy entre los cotizantes, (b) cotizan desde 2026 de golpe y (c) con el **mismo ingreso imponible promedio** que los cotizantes de hoy. | Los informales ganan menos, así que la masa real sería menor y el punto crítico, antes de 2055. La ENE tiene ingresos; no se usaron. |
| 6.3 | Los cotizantes no son todos los formales: en 2023 el 67 % de los ocupados cotiza y el 72 % no es informal (la diferencia son honorarios y regímenes fuera de la estadística). Sumar todos los informales lleva la razón cotizantes ÷ ocupados a 95 %. | Otra razón para leerlo como límite superior. |
| 6.4 | Solo país: las regiones y comunas del simulador no tienen escenarios fijos (su horizonte llega a 2050 y no hay informalidad regional proyectada). | — |
| 6.5 | Los topes de 11 y 12 % son criterio, no dato: la PGU se paga con impuestos generales. Aquí solo muestran cuánto se atrasa el cruce. | — |

## 7. Pendiente (datos que faltan)

| Dato | Para qué | Estado |
|---|---|---|
| Regla de asignación regional de la Superintendencia | Saber si migración y empleo se miden en la misma región | Opcional; no bloquea |
| ENE después de mar-may 2024, base 2024 | Extender la descomposición a 2024-2025 | Bajar del explorador del INE |
| ENE regional por sexo | Participación femenina oficial | Bajar (los archivos traen «Ambos sexos») |
| ENE regional por rama de actividad y categoría ocupacional | Industria dominante y cuenta propia oficiales | Bajar (los archivos traen «Total») |
| Cotizantes por rama de actividad (Superintendencia) | Qué parte de cada rama cotiza | Bajar |
| PIB regional por actividad, y Magallanes | Industria dominante por producto | Re-exportar del Banco Central (máx. 25 series) |
| Densidad de cotizaciones por región | Medida directa de la continuidad | Superintendencia |
