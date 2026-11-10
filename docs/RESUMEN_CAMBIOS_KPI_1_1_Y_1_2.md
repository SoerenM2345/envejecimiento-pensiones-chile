# Resumen de cambios: KPI 1.1 y KPI 1.2 (commits `d0e0438` y `9b2ade8`)

Para quien trabaja en paralelo en el mismo repositorio. Cubre lo hecho desde el commit `d411409` (pautas de diseño de la clase). Ya está en `main`.

## Qué se pidió

Tres mejoras del profesor; solo la 1 está hecha, la 2 y la 3 no se empezaron:

1. **Cobertura por región (KPI 1.1):** dónde es más baja o va bajando, dónde pesa más, y qué lo explica (desempleo, informalidad, industria, migración, 1-2 más). **Hecho.**
2. Forecast con 3-4 escenarios y por qué importa. **Pendiente.** (Los 6 escenarios fijos del KPI 1.2 son escenarios del punto crítico, no el forecast pedido.)
3. Costos como problema nacional y por qué unos factores suben más rápido. **Pendiente.**

## Qué hay de nuevo en el dashboard

### KPI 1.1 (Objetivo 1, primera tarjeta)

Orden de arriba a abajo: tarjetas y mapa/barras de siempre, y después:

| Bloque | Qué es |
|---|---|
| **Selector de las 5 regiones prioritarias** | 4 listas; por defecto la recomendada «bajo el promedio y en caída desde 2022»: La Araucanía, Valparaíso, Biobío, Los Ríos, Los Lagos. Las otras: mayor brecha, caída más fuerte, mayor peso. Cambia todo lo de abajo. Detalle en `docs/SHORTLIST_REGIONES.md` |
| **Barras: cambio de la cobertura desde 2022** | Las 16 regiones, prioritarias en naranja, línea de Chile; mismo diseño que «Cobertura relativa» |
| **Gráfico de 2002 a hoy** | 3 líneas: Chile, la prioritaria más rezagada (o la que más cayó) y la mejor región |
| **«Región por región»** | 16 paneles (o 13 con regiones fusionadas), período 2019-2025 o 2002-2025, franja 2020-2021, casilla «población sin ajustar» con el Censo 2024 como rombo; tabla con peso, nivel y tendencia |
| **¿De dónde viene la diferencia?** | Cobertura = participación × empleo × cotización de los ocupados; 4 paneles, filtro 5 o 16 regiones, línea de Chile, orden por gravedad |
| **¿Qué se asocia con la cobertura?** | Correlaciones (n = 16), tabla de las prioritarias frente a Chile, y desplegables: factores probados, contraste con el estudio de la Asociación de AFP, prueba de asignación regional |

Cada gráfico nuevo lleva debajo una frase en negrita «Qué muestra: …» y una línea gris con fuente y límites.

### KPI 1.2

El simulador de arriba **no cambió**. Debajo hay **6 escenarios fijos del país** (gráfico de dos paneles + tabla):

| Escenario | Punto crítico |
|---|---|
| Tope de carga 10 % (base) | 2038 |
| Tope 11 % | 2044 |
| Tope 12 % | 2048 |
| Cobertura sigue cayendo (tendencia 2022-2025, −0,18 puntos por año hasta 2050) | 2036 |
| Sin informalidad (todos los informales cotizan desde 2026, +41 % de cotizantes) | 2055 |
| Mitad del camino (+21 %) | 2048 |

«Sin informalidad» es un **techo teórico** (mismo ingreso imponible, salto inmediato), no una proyección.

## Resultados que conviene conocer

- Cobertura de Chile: 30,0 % (2002) → 47,8 % (2021) → 46,9 % (2025). Desde 2022 bajan 7 de 16 regiones; desde 2019 solo Arica y Parinacota y la Metropolitana.
- La diferencia con Chile viene sobre todo de **«ocupados que cotizan»** (La Araucanía −7,7 puntos, Ñuble −7,3) y en Biobío de la participación laboral (−3,8). **El desempleo casi no aporta** (entre −0,6 y +0,2).
- La desocupación oficial no se asocia con la cobertura (r = −0,32, no significativa). La informalidad oficial sí (r = −0,83), pero es en parte lo mismo que «no cotiza».
- Los cotizantes de `cotizantes_region.xls` coinciden al decimal con los de la Asociación de AFP en las 16 regiones: son «cotizantes del mes» de diciembre, **sin honorarios** (el archivo no lo dice; se deduce).
- La Metropolitana pesa 1 a 5 puntos más en los cotizantes que en los ocupados. No se sabe si es por la región del empleador o por más empleo formal.

## Decisiones de método (para no deshacerlas sin querer)

- **El Censo 2024 manda**, también en la encuesta de empleo: ocupados y fuerza de trabajo se llevan al nivel del Censo con el mismo factor de la población. Sin eso aparecía un «ajuste al Censo» de ±3 puntos que era un artefacto.
- **Se muestra la medida oficial de cada hipótesis** (desempleo e informalidad de la ENE, migración del Censo), no la de mejor correlación: con 37 factores probados, elegir la que mejor calza exagera.
- **Series fusionadas** en numerador y denominador: Tarapacá+Arica y Los Lagos+Los Ríos hasta 2006, Biobío+Ñuble hasta 2017.
- **Formalización como salto** inmediato en 2026 (no rampa hasta 2050). El motor admite ambos; se eligió el salto.
- Pautas de la clase: títulos-mensaje sin siglas, máximo 4 líneas por panel, ejes desde 0, colores aptos para daltonismo (ΔE ≥ 25), línea punteada de escenarios se mantiene.

## Qué cambió en el código y los datos

| Qué | Dónde |
|---|---|
| Gráficos nuevos y la descomposición reescrita | `Dashboards/components/charts.py` (`region_change_bars`, `coverage_long_chart`, `coverage_trend_panels`, `decomposition_panels`, `fixed_scenarios_chart`) |
| Selector, bloques nuevos, escenarios fijos | `Dashboards/final_pages/objetivo1.py` (`render_1_1_tendencia`, `render_1_1_descomposicion`, `render_1_1_causas`, `render_1_2_escenarios_fijos`) |
| Motor del punto crítico: parámetro **opcional** `cobertura_salto` (por defecto 1,0, no cambia nada existente) | `Dashboards/components/critical_point.py` |
| Tendencia 2002-2025, prioridades, factores del Censo | `Scripts/24_cobertura_tendencia_causas.py` |
| Descomposición, ENE, PIB, contraste con la Asociación de AFP, escenarios fijos | `Scripts/25_explorar_causas.py` (**ejecutar después del 24**) |
| Documentos nuevos | `docs/supuestos_y_limitaciones.md`, `docs/EXPLORACION_COBERTURA.md`, `docs/SHORTLIST_REGIONES.md`; filas 16-24 de `docs/DISCUSION_FUENTES.md` |
| Tests nuevos | `tests/test_cobertura_tendencia.py`, `tests/test_cobertura_causas.py` (119 en total, todos pasan) |

### Datos crudos (reordenados)

Todo lo descargado vive en `Data raw/_external/`, cada carpeta con su `LEEME.md`:

- `ine_ene_regional/`: 21 exportaciones de la Encuesta Nacional de Empleo (XML de Excel 2003, con nombres descriptivos; el `LEEME` trae la correspondencia con los códigos originales).
- `bcentral_pib_regional/`: PIB regional trimestral (15 regiones, **falta Magallanes**, solo total).
- `aafp_cobertura_regiones/`: el estudio de la Asociación de AFP.
- `ine_proyecciones_base2017/`: población regional por año (11 MB).

La carpeta de paso `import razones/` ya no existe.

### Datos procesados nuevos (`Data processed/`)

`kpi_cobertura_tendencia.csv` (2002-2025), `kpi_cobertura_regiones.csv`, `kpi_cobertura_factores.csv`, `kpi_cobertura_factores_anual.csv`, `kpi_cobertura_descomposicion.csv`, `kpi_cobertura_contraste_aafp.csv`, `kpi_cobertura_test_asignacion.csv`, `ene_region_anual.csv`, `pib_regional_anual.csv`, `kpi_pc_escenarios_fijos.csv`. Se regeneran con los scripts 24 y 25; descripción en `Data processed/README.md`.

## Cómo trabajar con esto

- Correr siempre con el entorno del proyecto y aislado: `Data raw/.venv/bin/python -I …`.
- Regenerar datos: `python -I Scripts/24_cobertura_tendencia_causas.py` y luego `python -I Scripts/25_explorar_causas.py`.
- Tests: `python -I -m pytest tests -q` (unos 90 segundos).
- **Streamlit no recarga `components/charts.py` al editarlo**: reiniciar el servidor (`pkill -f "streamlit run Inicio.py"` y volver a lanzarlo desde `Dashboards/`).
- Al tocar `objetivo1.py` o `charts.py`, mirar antes qué cambió aquí: son los dos archivos con más cambios.

## Límites y pendientes

- La encuesta de empleo del archivo llega a mayo de 2024: la descomposición llega a **diciembre de 2024** («hoy»; 2024 sale del anexo del estudio de la Asociación de AFP) y no hay empleo regional para 2025.
- Faltan: encuesta por sexo y con todas las ramas y categorías, cotizantes por rama, PIB por actividad (y Magallanes), la proyección regional base 2024 del INE (segundo semestre de 2026). Instrucciones en `docs/EXPLORACION_COBERTURA.md`, sección 7.
- Salto de +3 puntos de cobertura entre 2006 y 2007 en 12 de 13 territorios: sin explicar, puede ser un cambio de cómputo.
- Pregunta opcional a la Superintendencia de Pensiones: ¿asigna los cotizantes por residencia o por empleador, y están los honorarios? No bloquea nada.
- La regla de «las 5 más importantes» se confirmó con el usuario; falta confirmarla con el profesor.
- Siguen **sin commit** los archivos que agregó el usuario: PDF y Word en `docs/`, `ventas-chile-2021.xlsx`, `guia_clase_posicionamiento_pca.md` y los dos `.docx` de `Outputs/`.

## Actualización 2026-11-10 (sin commit todavía)

- **Descomposición hasta hoy:** los cambios son «2023 a hoy» y «2019 a hoy» (hoy = diciembre de 2024); antes eran 2019-2023. `Scripts/25` agrega 2024 desde el anexo del estudio de la Asociación de AFP (`ene_region_anual.csv` tiene la columna `fuente`).
- **Ordenar por cada columna:** selector «Ordenar las filas por» (diferencia total, participación, empleo, cotización) y «De menor a mayor / De mayor a menor».
- **Bloque nuevo «2. Las razones una por una»:** tabla resumen con cada razón del profesor, la pieza en que cae, su aporte y su asociación. Los títulos del bloque están numerados 1-3.
- **Matriz de riesgo y dispersiones:** punto negro de 5 px en el centro de cada burbuja (`_burbujas`), donde termina la línea del rótulo.
- **Escenarios fijos del KPI 1.2 rediseñados:** 6 paneles, cada uno con el costo (la misma curva roja) y la capacidad (azul); el cruce se ve como cruce, con una línea punteada al eje y el año escrito fuera del gráfico, bajo el eje. Sin puntos con rótulo dentro del gráfico.
- **Comparación de los KPI de costo:** `docs/KPIS_DE_COSTO_COMPARACION.md`.
