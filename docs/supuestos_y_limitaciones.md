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

Resultado, sin concluir más: la Metropolitana pesa **más en los cotizantes que en los ocupados** en todas las fechas, y la diferencia **se achica** (5,0 puntos en 2010, 1,0 en 2023). Con estos datos no se distingue entre «se asigna por la región de la empresa» (las casas matrices están en Santiago) y «la Metropolitana tiene más empleo formal». **La sensibilidad ya está calculada** (Censo 2024, ocupados que viven en una región y trabajan en otra; `kpi_cobertura_pendularidad.csv`, tabla en el desplegable del dashboard): si fuera por lugar de trabajo, Antofagasta bajaría 7,8 puntos de cobertura y Coquimbo subiría 2,3, pero las tres regiones de menor cobertura (La Araucanía, Los Ríos, Ñuble) cambiarían menos de 0,7 puntos. La pregunta para la Superintendencia cabe en una línea: ¿cada cotizante se cuenta en la comuna de su empleador o en el domicilio del afiliado? Para saberlo habría que preguntarle a la Superintendencia cuál es la regla; **no bloquea nada**: mientras no se sepa, el argumento de migración se presenta como contexto y no como causa (cambia el denominador; el numerador solo si se asigna por residencia).

## 1. Población (denominador)

**Año de referencia: 2024** para todas las comparaciones del KPI 1.1 (barras de cambio, listas de regiones prioritarias, tabla y descomposición): el problema y su explicación usan el mismo año. Es el año del Censo y el último con ocupados por región. La cobertura de 2025 se calcula (46,9 % en Chile) pero con población proyectada y sin empleo regional, y por eso queda fuera de las comparaciones; cambiarlo es una constante del script 24 (`ANIO_REF`) cuando haya ENE de 2025 y la proyección regional base 2024. Efecto: con 2025 como final, Coquimbo y Ñuble «se recuperaban» y entraban en su lugar Los Ríos y Los Lagos.

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
| 2.6 | **La tendencia de las regiones prioritarias** (puntos ganados desde 2007 menos los de Chile) usa la serie fusionada de Biobío y Ñuble hasta 2017, así que las dos tienen la misma tendencia; Arica y Los Ríos están separadas desde 2007. Los tres rangos pesan igual y la brecha (nivel × tamaño) repite en parte el nivel. | Con 16 regiones, un rango de 1 a 16 por factor es una elección: con otro peso o con el cotizantes por región en lugar de la brecha (la Metropolitana pasa a rango 1) la lista cambia. La regla se probó con 21 años de inicio: igual con todos hasta 2019 (`kpi_cobertura_prioridad_robustez.csv`). |

## 3. Encuesta Nacional de Empleo (ENE) y descomposición

| # | Supuesto o límite | Efecto |
|---|---|---|
| 3.1 | El archivo bajado del explorador del INE usa proyecciones base 2017 y llega a **mar-may 2024**. La descomposición llega a **diciembre de 2024 («hoy»)**: 2010-2023 salen de esas exportaciones y 2024 del **anexo del estudio de la Asociación de AFP**, que trae la misma serie (en 2019 coinciden al decimal con las exportaciones, ver el contraste); es un dato transcrito del PDF, no una descarga del INE. | La cobertura de 2025 no se descompone (no hay ocupados por región). Para verificar 2024 y extender a 2025 hay que bajar la serie base 2024 del explorador del INE (no pude comprobar si ya está publicada). |
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
| 4.2 | Se probaron 39 factores sobre el nivel y 3 sobre el cambio: con tantos, 1 o 2 salen significativos por azar. Por eso se muestra la medida **oficial** de cada hipótesis (desocupación e informalidad de la ENE, migración del Censo), aunque no sea la que mejor calza, y no «la que salió». |
| 4.3 | **Informalidad oficial = en parte «no cotiza».** La ENE cuenta como informal al dependiente sin cotizaciones previsionales por su empleo (y al independiente cuyo negocio no está registrado). Que la informalidad «explique» la cobertura es en parte lo mismo dicho de otro modo (r = −0,80 con diciembre 2024). |
| 4.4 | Desocupación del Censo (abril 2024) y de la ENE (diciembre 2024) dan correlaciones distintas con la cobertura (−0,71 y −0,34): la definición y el momento importan. El tablero muestra la oficial. |
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
| Sin informalidad | todos los informales de hoy cotizan desde 2026 (+39 % de cotizantes) | 2054 |
| Mitad del camino | la mitad de los informales cotiza (+19 %) | 2048 |

| # | Supuesto o límite | Efecto |
|---|---|---|
| 6.1 | **«Cobertura sigue cayendo» = tendencia 2022-2025** (ajuste lineal de 4 puntos, −0,18 puntos por año), prolongada hasta 2050 y constante después (así es el motor). La serie cayó de 47,6 % (2022) a 46,0 % (2023) y se recuperó a 46,9 % (2025): la pendiente depende de la ventana (con 2021-2025 sería −0,30). | Con −0,30 el punto crítico sería 2035 en vez de 2036; con la cobertura de 2025 constante, 2038. |
| 6.2 | **«Sin informalidad» es un techo teórico, no una proyección.** Suma a los cotizantes todos los ocupados informales de hoy (ENE, diciembre 2024, del anexo del estudio de la Asociación de AFP, llevados al nivel del Censo con el factor de la población: 2,28 millones). Supone que (a) ninguno está hoy entre los cotizantes, (b) cotizan desde 2026 de golpe y (c) con el **mismo ingreso imponible promedio** que los cotizantes de hoy. | Los informales ganan menos, así que la masa real sería menor y el punto crítico, antes de 2054. La ENE tiene ingresos; no se usaron. |
| 6.3 | Los cotizantes no son todos los formales: en 2024 el 67 % de los ocupados cotiza y el 74 % no es informal (la diferencia son honorarios y regímenes fuera de la estadística). Sumar todos los informales lleva la razón cotizantes ÷ ocupados a 94 %. | Otra razón para leerlo como límite superior. |
| 6.4 | Solo país: las regiones y comunas del simulador no tienen escenarios fijos (su horizonte llega a 2050 y no hay informalidad regional proyectada). | — |
| 6.5 | Los topes de 11 y 12 % son criterio, no dato: la PGU se paga con impuestos generales. Aquí solo muestran cuánto se atrasa el cruce. | — |

## 7. Composición actual de los cotizantes y de los que no cotizan (KPI 1.1, `Scripts/29_composicion_cotizantes.py`)

Gráfico «¿Quién cotiza hoy y por qué no cotiza el resto?»: las 12,6 millones de personas de 15 a 64 años (Censo 2024) en seis grupos que suman el total. **Los grupos son las piezas de la descomposición de la cobertura** (participación × empleo × ocupados que cotizan), no una clasificación nueva: lo que cotiza es la cobertura de la tarjeta (46,5 %) y cada razón de la tabla «Las razones una por una» cae en el mismo grupo.

| Grupo | Pieza | Personas (dic-2024) | % de 15-64 |
|---|---|---|---|
| Cotizan: dependientes | Ocupados que cotizan | 5.814.037 | 46,1 |
| Cotizan: independientes y voluntarios | Ocupados que cotizan | 48.846 | 0,4 |
| No cotizan: ocupados informales (ENE) | Ocupados que cotizan | 2.283.299 | 18,1 |
| No cotizan: ocupados formales fuera de la estadística | Ocupados que cotizan | 547.148 | 4,3 |
| Buscan trabajo (desocupados) | Empleo | 755.707 | 6,0 |
| Ni trabajan ni buscan | Participación laboral | 3.169.508 | 25,1 |

| # | Supuesto o límite | Efecto |
|---|---|---|
| 7.1 | Los cotizantes con región (5.862.883, los de la cobertura) se reparten entre dependientes, independientes y voluntarios con la proporción del total país de la Superintendencia (5.918.977). | Los 56 mil «sin información» pesan igual en los tres tipos; el efecto en los porcentajes es menor a 0,01 puntos. |
| 7.2 | Ocupados, desocupados y personas de 65 años o más: la fuerza de trabajo incluye a los mayores de 65 que trabajan, igual que la cobertura. | «Ni trabajan ni buscan» es un **resto** (población 15-64 − ocupados − desocupados), unos 0,7 millones menos de los que realmente no participan entre 15 y 64. |
| 7.3 | **Se supone que ningún informal figura entre los cotizantes.** Los informales de la ENE (2.467.359, diciembre 2024 = nov-ene 2024-25, del anexo del estudio de la Asociación de AFP) se llevan al nivel del Censo con el factor de los ocupados (× 0,925). | Si algunos informales cotizan (por ejemplo un independiente con negocio no registrado que cotiza), «formales fuera de la estadística» sube y los informales bajan en lo mismo. Sin cambio en los que cotizan ni en el total de los que no. |
| 7.4 | **«Formales fuera de la estadística» es una resta**: ocupados − cotizantes − informales. Se interpreta como honorarios, regímenes fuera de las administradoras (Capredena, Dipreca) y cotizaciones declaradas y no pagadas, pero eso no se puede comprobar con estos datos. | Coincide con lo dicho en 6.3 (67 % de los ocupados cotiza y 72 % no es informal en 2023). |
| 7.5 | Segundo gráfico («independientes entre los ocupados y entre los cotizantes»): el Censo clasifica la categoría ocupacional (`p40_cise_rec`; el código 1 se toma como independiente, igual que el script 24; **no se encontró el libro de códigos del INE para confirmarlo**) distinto de la ENE (en las regiones sale 28-40 % en el Censo y 30-32 % en la Asociación de AFP). | Muestra el orden de magnitud (1 de cada 3 ocupados frente a menos de 1 de cada 100 cotizantes), no una brecha exacta. |
| 7.6 | **Los dependientes no cuadran entre fuentes**: con el Censo, los ocupados que no son independientes son unos 5,5 millones y los cotizantes dependientes de la Superintendencia 5,9 millones. | Por eso no se muestra cuántos dependientes no cotizan: con estas fuentes saldría cero o negativo, lo que contradice la informalidad de los dependientes de la ENE. La informalidad de la ENE no se separa por tipo de trabajo (los archivos descargados traen la categoría ocupacional en «Total»). Pendiente en la sección 8. |
| 7.7 | Los independientes que cotizan caen de 135 mil (2017) a 84 mil (2019) y 48 mil (2024). | Posible cambio de definición con la Ley 21.133 (honorarios); no se pudo comprobar, es el mismo quiebre posible de 0.1. |
| 7.8 | El mismo gráfico por región (`kpi_cobertura_composicion_region.csv`): la Superintendencia no publica los cotizantes por tipo y región, así que los independientes y voluntarios se reparten en cada región con la proporción del país (0,8 % de los cotizantes). | Los 0,3-0,5 puntos de cada región no son un dato regional; no cambian el total que cotiza (la cobertura de la región). |
| 7.9 | Los informales de cada región (ENE) se llevan al nivel del Censo con el factor de esa región (ocupados del KPI ÷ ocupados de la ENE). En O'Higgins el resultado supera a los ocupados que no cotizan y se limita a ellos. | En O'Higgins «formales fuera de la estadística» queda en 0; en las regiones prioritarias no se activa el límite. |

## 8. Pendiente (datos que faltan)

| Dato | Para qué | Estado |
|---|---|---|
| Regla de asignación regional de la Superintendencia | Saber si migración y empleo se miden en la misma región | Opcional; no bloquea |
| ENE después de mar-may 2024, base 2024 | Extender la descomposición a 2024-2025 | Bajar del explorador del INE |
| ENE regional por sexo | Participación femenina oficial | Bajar (los archivos traen «Ambos sexos») |
| ENE regional por rama de actividad y categoría ocupacional | Industria dominante y cuenta propia oficiales | Bajar (los archivos traen «Total») |
| Cotizantes por rama de actividad (Superintendencia) | Qué parte de cada rama cotiza | Bajar |
| PIB regional por actividad, y Magallanes | Industria dominante por producto | Re-exportar del Banco Central (máx. 25 series) |
| Densidad de cotizaciones por región | Medida directa de la continuidad | Superintendencia |

## 9. Reforma de la cotización del empleador (KPI 1.3 y KPI 1.2; `Scripts/15`, `Scripts/30`, `Scripts/31`)

Bloques: «¿Adónde va la cotización del empleador?» (KPI 1.3), variantes del flujo comisionable con el efecto de la reforma en el empleo (KPI 1.3), «Con la reforma del empleador: dos escenarios frente a la base» (KPI 1.2) y «¿Qué puede hacer una administradora y qué le corresponde al Estado?» (KPI 1.1). Los destinos por escalón salen de la Tabla 1 de la Nota Técnica de la Ley 21.735 (copia en `Data raw/_external/ley_21735/`): antes de la reforma el empleador paga solo el seguro de invalidez y sobrevivencia (1,88 %); en agosto de 2033 paga 8,5 % (4,5 a la cuenta individual, 2,5 al Seguro Social permanente y 1,5 al transitorio); el aumento neto es 6,62 puntos.

| # | Supuesto o límite | Efecto |
|---|---|---|
| 9.1 | **La elasticidad del empleo formal frente al costo laboral es un supuesto, no una estimación.** Base 0 (traspaso total a los sueldos; Gruber 1997, NBER w5053, lo encontró en Chile al *bajar* las cotizaciones); variantes −0,1 y −0,3 (`config/escenarios.yaml`, `reforma_empleador`). | No hay estimación para esta reforma ni para una *subida*. Las dos variantes muestran el orden de magnitud: cotizantes −0,6 % y −1,7 % en 2033; punto crítico del KPI 1.2 −3 y −10 meses (2038 → 2038 y 2037). |
| 9.2 | El aumento del costo laboral es el aumento de la cotización del empleador frente a antes de la reforma, en % del sueldo imponible; no se cuentan otras cargas del empleador. | Sobrestima algo el aumento relativo del costo. |
| 9.3 | Solo reaccionan los cotizantes dependientes (99,2 % de los de dic-2024); los independientes no pagan cotización del empleador. | Los independientes siguen igual en todos los escenarios. |
| 9.4 | El efecto se mide desde 2025 (el escalón de agosto de 2025 ya está en los datos) y se mantiene desde 2033. | El factor de 2025 es 1; `kpi_reforma_empleo_factor.csv` trae la trayectoria hasta 2070. |
| 9.5 | **El Seguro Social no se suma a la capacidad del punto crítico.** Sus ingresos pagan el Beneficio por Años Cotizados, la compensación a las mujeres y el seguro de invalidez y sobrevivencia, no el Pilar Solidario (PGU, PBS, APS). | Sumarlo exigiría sumar también esas prestaciones. El aporte del Estado al fondo del Seguro Social ya está en el KPI 2.2. |
| 9.6 | En el KPI 1.3 el efecto casi no mueve el porcentaje del flujo en cuentas individuales (−0,1 y −0,3 puntos en 2033) porque la pérdida de cotizantes también reduce el Seguro Social; sí mueve el monto (−0,6 % y −1,7 %). | Se muestra el monto en la nota bajo el gráfico. |
| 9.7 | Cuánto de la tasa va al seguro de invalidez y sobrevivencia: la Nota Técnica fija 1,88 % hasta julio de 2026 y no separa qué parte del 2,5 % del Seguro Social permanente lo es desde agosto de 2026; se supone 1,88 % constante. | Solo reparte el 2,5 % entre «seguro de invalidez» y «Seguro Social»; el total no cambia. |
| 9.8 | **Las palancas de la administradora** (`kpi_cobertura_palancas.csv`): el alcance de la administradora y el impacto son un juicio del equipo. Lo que dicen la ley y los documentos del gremio (Hoja de Ruta 555, 2023; Mesa de Formalidad Laboral, 2024) se cita, no se evalúa. | No hay medición del efecto de estas palancas. Los grupos de personas se superponen y no se suman. |
| 9.9 | **Corrección frente a un texto de apoyo:** la cobranza de cotizaciones impagas ya no la hace cada administradora por separado: desde el 1 de junio de 2026 rige un Sistema Único de Cobranza que las administradoras financian (Nota Técnica, sección 3.1.4). | La palanca «cobrar» es directa pero ya está en la ley; no es una opción nueva. |
| 9.10 | **No se incorporó:** la cobertura ocupacional oficial de la Subsecretaría de Previsión Social (en un texto de apoyo: 68,05 % en la tabla y 70,1 % en el texto de la nota técnica, sin verificar), ni la parte de honorarios (Ley 21.133) y otros regímenes dentro del 4,3 % «formales fuera de la estadística». | Definiciones distintas de la cobertura del KPI 1.1 (46,5 % de 15 a 64 años). Si se incorporan, el Censo manda y el conflicto va a `docs/DISCUSION_FUENTES.md`. |
