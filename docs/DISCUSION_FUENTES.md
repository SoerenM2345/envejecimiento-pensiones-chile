# Discusión de fuentes: conflictos, decisión y efecto en los resultados

Documento vivo. Aquí se anota cada vez que dos fuentes (o dos fechas) chocan, qué se decidió y cuánto cambia el resultado según la opción. Sirve para discutirlo en el equipo sin tener que reconstruir el análisis.

## Regla de prioridad

> **El Censo 2024 manda.** Cuando el Censo choca con otra fuente (población, estructura de edad, territorio), las cifras principales del dashboard se calculan con el Censo. La otra fuente solo aporta lo que el Censo no tiene (la dinámica en el tiempo, años anteriores o posteriores), siempre **llevada al nivel del Censo** y con el conflicto anotado aquí junto con su efecto.

Cómo se aplica:
1. Año de referencia = **2024** (el del Censo, abril de 2024). Los demás datos se alinean a él: cotizantes e ingreso imponible de **diciembre de 2024** (8 meses de diferencia; diciembre de 2025 estaría a 20), ESI 2024, gasto del año 2024.
2. Si la otra fuente tiene otro nivel (p. ej. el INE corrige el subconteo del censo), se usa su *variación* (proyección en el tiempo) multiplicada por `Censo 2024 / fuente 2024`.
3. Se calcula el resultado con ambas opciones y se anota la diferencia (columna «Efecto»). Si la diferencia es menor que la precisión que se afirma, queda como nota; si no, se explica en el dashboard.

## Conflictos y decisiones

| # | Tema | Fuente A | Fuente B | Decisión | Efecto en los resultados |
|---|---|---|---|---|---|
| 1 | **Nivel de la población** | Censo 2024: 18.480.432 personas; 65+ = 2.587.238; 15-64 = 12.618.546 | Proyecciones INE base 2024: 19.904.328; 65+ = 2.781.829 (+7,5 %); 15-64 = 13.644.595 (+8,1 %). El INE corrige el subconteo del censo | **Censo.** Para el país, la serie INE 1992-2070 se multiplica por 0,930 (65+) y 0,925 (15-64) | Razón de soporte 2024 del país: **2,29** (Censo) frente a 2,13 (nivel INE). El **costo total, la carga requerida y el año crítico no cambian** (2039 en ambos casos): el gasto es el mismo y el costo por persona de 65+ sube en la misma proporción en que baja su población. |
| 2 | **Fecha de los cotizantes** | Dic-2024 (a 8 meses del Censo) | Dic-2025 (a 20 meses) | **Dic-2024** | Razón de soporte (regiones): 2,27 con dic-2024 frente a 2,30 con dic-2025 sobre el Censo (el numerador crece 1,7 % pero la población es la misma: sobrestima). Ñuble: 1,51 frente a 1,54. |
| 3 | **Cotizantes sin región** | Suma de regiones 2024: 5.862.883 | Total país 2024: 5.918.977 (56.094 «Sin información», ~1 %) | Regiones y comunas **sin** esos 56.094; el país **con** ellos | País: 2,29 (con) frente a 2,27 (suma de regiones). Ver la nota del punto 1: la tarjeta base usa la suma de regiones (2,27), el análisis del punto crítico usa el total (2,29). |
| 4 | **Ingreso: bruto vs. neto** | Ingreso imponible (Superintendencia): bruto, mensual, solo de cotizantes | ESI del INE: ingreso neto del trabajo de todos los ocupados | **Dos bases, un interruptor** en el gráfico; nunca se mezclan en un mismo cálculo | Con la base «ocupados» el punto crítico se retrasa de 2039 a 2048 (más trabajadores, menos ingreso por persona). |
| 5 | **Dos totales de ingreso imponible 2025** | Cuadro 04A (total de cotizantes): $1.299.840 | Cuadro 32C (total por región y AFP): $1.308.020 (+0,6 %) | **04A** para el nivel nacional; **32C** solo para repartir por región | Despreciable para el punto crítico (< 1 año). |
| 6 | **Mediana regional del ingreso imponible** | La SP publica la mediana por tramos solo a nivel nacional y por AFP | No existe por región | **Estimada** (fórmula abajo) | Es una aproximación: usa la forma de la distribución nacional. Solo afecta a la opción «mediana» de la base de cotizantes en regiones y comunas. |
| 7 | **Población 65+ regional 2035 y 2050** | Reparto de las tasas de crecimiento nacionales del INE por región (shift-share), ya en `kpi_proyeccion_regional.csv` | El INE no publica proyección regional base 2024 | Se mantiene; rotulada como escenario | Las regiones no suman exactamente el país proyectado. Ñuble y Valparaíso son las más sensibles. |
| 8 | **Gasto del Pilar Solidario por región** | El informe trimestral trae trimestres en distintas bases de pesos (dic-2023, dic-2024) | El gasto anual nacional (pesos nominales, deflactado con el IPC) | Se usa solo la **cuota** de cada región en el trimestre octubre-diciembre de 2024 y se aplica al total nacional de 2024 | Supone que el reparto regional del trimestre es el del año. Supuesto no contrastado: no se verificó cuánto difiere el reparto de un trimestre del anual. |
| 9 | **Costo por persona de 65+** | Gasto de PGU + APS/PBS de vejez dividido entre **todas** las personas de 65+ | Solo los beneficiarios (~2,0-2,4 M) | Se divide entre toda la población 65+ (Censo): es el costo que el sistema reparte entre todas las personas de esa edad | Si se dividiera entre los ~2,06 M de beneficiarios de la PGU (79 % de los 65+ del Censo), el costo por persona subiría ~26 %; el costo total y el año crítico no cambian. |
| 10 | **Comunas** | Población 65+ y 15-64 del Censo 2024 (propia) | No hay cotizantes, ingresos ni gasto por comuna | La comuna **hereda** de su región cobertura, ingreso y costo por 65+ | La razón de soporte comunal mide la estructura de edad, no cotizantes reales. Las comunas suman exactamente su región. |
| 11 | **Ñuble antes de 2018** | Ñuble existe como región desde 2018 | Antes forma parte de Biobío | Su ingreso imponible 2010-2017 se aproxima con el de Biobío (columna `ingreso_imponible_aprox_biobio`) | Solo afecta a series históricas regionales de Ñuble; el análisis usa 2024. |
| 12 | **IPC** | Variación mensual con un decimal | — | Se encadena desde diciembre de 2008 y se promedia por año | Sirve para razones entre años, no como nivel; error acumulado del orden de 1 % (estimación, no verificada). |
| 13 | **PGU de $250.000** | Calendario por edad (82+ sep-2025, 75+ sep-2026, 65+ sep-2027) tomado de prensa y sitios oficiales | Texto de la Ley 21.735 | Se usa el calendario; **pendiente de contrastar con el texto de la ley** | El supuesto pesa: con el aumento a $250.000 el punto crítico es **2039**; sin él, **2045** (por eso es una casilla del dashboard). Un desfase de un año en el calendario movería el resultado menos que eso (no se calculó). |
| 14 | **Edad enmascarada en el Censo** | 151.199 personas (0,8 %) de 51 comunas pequeñas sin edad exacta | — | Se usa `edad_quinquenal`, completa | Sin efecto sobre 65+ por grupos quinquenales. |
| 15 | **Mediana ESI 2025** | Archivo importado: $680.000 | Publicación del INE del 14-jul-2026: $680.000 | Confirmada | — |

## Cómo se estiman las cifras regionales y comunales

1. **Mediana del ingreso imponible de una región** (base cotizantes, estadístico «mediana»):

   `mediana_región = mediana_nacional × (promedio_región ÷ promedio_nacional)`

   con la mediana nacional calculada por interpolación lineal dentro del tramo de ingreso imponible donde se acumula el 50 % de los cotizantes (tabla 19B de la Superintendencia), y los promedios del cuadro 32C (región) y 04A (país), todos de diciembre de 2024. Es decir, se supone que cada región tiene la **misma forma de distribución** que el país y solo cambia su nivel. Si la desigualdad dentro de una región es distinta, la mediana real también lo es (la razón mediana/promedio del país fue 0,70 en 2010, 0,74 en 2015, 0,76 en 2024). Para mejorarlo haría falta la distribución por tramos de ingreso desglosada por región, que la Superintendencia no publica.
2. **Ocupados y cotizantes regionales**: se usan tal cual (ENE octubre-diciembre 2024 y cotizantes de diciembre de 2024). Para 2035 y 2050 se escalan con la población 15-64 regional proyectada; entre medio se interpola linealmente.
3. **Población 65+ y 15-64 regional 2035/2050**: reparto de las tasas nacionales del INE (punto 7).
4. **Costo del Pilar Solidario por persona de 65+ en la región**: `cuota_región(oct-dic 2024) × gasto nacional de vejez 2024 ÷ población 65+ de la región (Censo 2024)`.
5. **Comuna**: `trabajadores_comuna = trabajadores_región × (pob 15-64 comuna ÷ pob 15-64 región)`, mismo ingreso por trabajador y mismo costo por persona de 65+ que la región; la población de la comuna crece al ritmo de su región.

## Para la próxima conversación

- Cuando haya que elegir entre el Censo y otra fuente: **gana el Censo**, la otra se reescala a su nivel y el conflicto se agrega a la tabla de arriba con su efecto.
- Pendientes: contrastar el calendario de la PGU con el texto de la Ley 21.735 (punto 13); decidir si el país en la tarjeta base debe incluir los cotizantes sin región (punto 3); ampliar la lista cuando otro KPI traiga un conflicto nuevo.
