# Guía: ver y reconstruir los 6 KPIs en el dashboard

Cada receta de este documento se ejecutó paso a paso sobre el Explorador (`tests/test_manual_mode.py`) y reproduce la cifra que muestra el dashboard. Si algo cambia en el Explorador o en las tablas, esos tests fallan y avisan que la guía quedó desactualizada.

Leyenda: 🟢 calculado con datos reales · 🟡 calculado en parte · 🔴 **FALTA un dato** (ver sección 5 para conseguirlo) · ⚪ aún sin cálculo.

---

## 0. Abrir el dashboard y encontrar el modo desarrollador

**Abrir** (desde la raíz del proyecto):

```bash
"Data raw/.venv/bin/streamlit" run Dashboards/Inicio.py
```

o, con el entorno activado: `cd Dashboards && streamlit run Inicio.py`. Se abre en `http://localhost:8501`. Streamlit imprime la URL real si el puerto está ocupado.

**Si ves un menú viejo** (una entrada llamada «Inicio» seguida de seis páginas con emojis, sin sección «Dashboard»): es un servidor anterior a estos cambios. Ciérralo y vuelve a abrirlo:

```bash
lsof -ti :8501 | xargs kill        # cierra lo que esté usando el puerto 8501
"Data raw/.venv/bin/streamlit" run Dashboards/Inicio.py
```

Luego recarga el navegador (Cmd+R). La entrada «Inicio» ya no existe: la primera página se llama **Resumen**.

**Qué debes ver en el menú lateral (modo final, por defecto):**

```
Dashboard
  📌 Resumen
  🔎 Problema
  🎯 Objetivo 1: base activa
  💰 Objetivo 2: costo por cliente
  📚 Fuentes y método
Modo desarrollador
  🛠️ Activar modo desarrollador
  ───────────────
  ◯ Modo desarrollador        ← interruptor
```

**Tres formas de activar el modo desarrollador** (todas hacen lo mismo):

1. Clic en **🛠️ Activar modo desarrollador** (sección «Modo desarrollador» del menú) y luego en el botón principal **Activar modo desarrollador**.
2. Prender el **interruptor «Modo desarrollador»**, abajo en el menú lateral.
3. Abrir `http://localhost:8501/?mode=dev`.

Con el modo activo, la sección «Modo desarrollador» muestra las 8 páginas de abajo y el menú indica `DEV: vista con todo el análisis`. Para volver al dashboard final, apaga el interruptor. Si el menú lateral está oculto (ventana angosta), ábrelo con la flecha `>` arriba a la izquierda.

---

## 1. Mapa del menú: dónde ver cada KPI

### Modo final (sección «Dashboard»)

| KPI | Página del menú | Tarjeta | Qué muestra | Estado |
|---|---|---|---|---|
| 1.1 Cobertura regional | **Objetivo 1: base activa** | «1.1 · Cobertura regional» | 3 cifras, mapa por región y barras con la línea del país | 🟢 |
| 1.2 Razón de soporte | **Objetivo 1: base activa** | «1.2 · Razón de soporte» | 3 cifras, barras por región, y un escenario 2035/2050 por país o región (selector «Territorio») | 🟡 |
| 1.3 Participación partes interesadas | **Objetivo 1: base activa** | «1.3 · Participación partes interesadas» | Tarjeta «Pendiente» con la fórmula | 🔴 |
| 2.1 Costo real por adulto mayor | **Objetivo 2: costo por cliente** | «2.1 · Costo real por adulto mayor» | 3 cifras y 5 pestañas: evolución (con el salto de la PGU en 2022), componentes, por beneficiario, frente al ingreso (10 % de la mediana) y proyección 2050 | 🟢 |
| 2.2 Financiamiento dedicado | **Objetivo 2: costo por cliente** | «2.2 · Financiamiento dedicado» | Ratio 1 en % del PIB; el ratio 2 aparece como pendiente | 🟡 |
| 2.3 Pobreza en la vejez | **Objetivo 2: costo por cliente** | «2.3 · Pobreza en la vejez» | 4 cifras, mapa y barras con intervalo de confianza 95% | 🟢 |

El análisis del problema (pirámides, Chile vs Alemania, 14% → 43%, pico de población activa) está en **Problema**; las cifras clave, en **Resumen**; de dónde sale cada dato, en **Fuentes y método**.

### Modo desarrollador (sección «Modo desarrollador»)

| Página | Para qué sirve con los KPIs |
|---|---|
| 🏠 Panorama general | Antigua página de inicio: ranking regional y tarjetas generales |
| 🔍 **Explorador de datos** | **El modo manual** (sección 2): reconstruye cualquier KPI eligiendo tablas, columnas y operadores |
| 🗺️ Mapas | Nivel «Región»: variables «Cobertura previsional (%)» y «Cotizantes por adulto mayor» (KPI 1.1 y 1.2) |
| 📊 Pirámides | Pirámides nacional 1992-2070 y por región/comuna |
| 💰 Pensiones y salud | KPI 1.1 y 1.2 con proyección regional 2024→2035→2050 y el contexto del sistema antiguo (IPS) |
| 🏙️ Socioeconómico | Ingresos (CASEN) y urbanización vs envejecimiento |
| 📋 Políticas | Segmentación de comunas y propuestas |
| 🧪 Estado de datos y KPIs | Estado de los 6 KPIs e inventario de archivos (filas, columnas, fecha) de `Data processed/` y `Data raw/` |

Los KPIs 1.3, 2.1, 2.2 y 2.3 **solo** se ven en el modo final y en el Explorador; no tienen página propia en el modo desarrollador.

---

## 2. Modo manual: el Explorador de datos

Menú lateral → **🔍 Explorador de datos** (requiere modo desarrollador). Todos los controles están en el menú lateral, salvo «Agrupar y agregar», que está al final de la página.

**El Explorador lee solo `Data processed/*.csv`** (no los archivos de `Data raw/`). Para ver un dato crudo hay que procesarlo antes (sección 6).

### Controles, en orden

| # | Control (etiqueta exacta) | Qué hace |
|---|---|---|
| 1 | **Fuente principal** | Elige la tabla (todos los CSV de `Data processed/`). |
| 1 | **Mezclar con una segunda fuente** → **Segunda fuente**, **Cruzar por**, **Tipo de cruce** | Une dos tablas por una columna en común. `Cruzar por` ofrece las columnas que tienen el mismo nombre en ambas (el Explorador unifica `region`→`region_id`, `comuna`→`comuna_id`, `año`→`anio`). Tipos: `left` (todo lo de la principal), `inner` (solo coincidencias), `outer` (todo). Si el cruce infla las filas (la segunda tabla tiene varias filas por clave) aparece una advertencia amarilla: filtra antes de sumar. |
| 1b | **Agregar columna calculada** → **A (columna)**, **Operador**, **B es…** (`una columna` / `un número`), **B (columna)** o **B (número)**, **Multiplicar el resultado por**, **Nombre de la columna nueva** | Crea `A (operador) B × factor` fila a fila, sobre la tabla ya cruzada. Operadores: `÷ dividir`, `× multiplicar`, `− restar`, `+ sumar`. Dividir por cero deja la celda vacía. El factor sirve para porcentajes (100) o para pasar de millones a unidades (1.000.000). |
| 2 | **Columnas a filtrar** | Elige qué columnas filtrar; aparece un control por cada una: **texto** → lista de valores (si hay más de 60 valores, un cuadro «contiene…»); **número** → **deslizador de rango** (desde, hasta). Para quedarte con un solo año, deja ambos extremos del deslizador en ese año. |
| 3 | **Agrupar por**, **Columna a agregar**, **Función**, **Mostrar top N** | Agrupa por una o dos columnas (se ofrecen las de texto y las numéricas con 60 valores distintos o menos) y aplica la función a **una** columna numérica: `sum`, `mean`, `median`, `count`, `min`, `max`. Con **Agrupar por vacío** entrega una sola cifra sobre todas las filas filtradas (total país). Gráfico de barras automático si hay 1 o 2 dimensiones. |
| — | Botones **⬇ Descargar tabla filtrada (CSV)** / **⬇ Descargar agregado (CSV)** | Llevan el resultado a una planilla. |

### Límites que conviene saber

- La columna calculada es **fila a fila**. Un **ratio nacional** (ej. cotizantes ÷ población 15-64 del país) se arma sumando cada columna por separado con «Agrupar por» vacío y `sum`, y dividiendo las dos cifras.
- No hay **índice base año = 100**: para comparar crecimientos (KPI 2.1) se leen los valores de dos años y se divide a mano.
- Se agrega **una** columna por vez.
- La lectura de tablas está en caché: si regeneras un CSV, recarga con el menú ⋮ → **Clear cache** (o `C` en el teclado) y recarga la página.

---

## 3. Receta de cada KPI en el modo manual

En todas: menú lateral → **🔍 Explorador de datos**. «Cifra de control» es el valor que debe aparecer; coincide con el dashboard final.

### KPI 1.1 · Cobertura regional 🟢

Fórmula: `Cotizantes ÷ Población 15-64`.

**Fuentes:** `Data raw/cotizantes_region.xls` (Superintendencia de Pensiones, cotizantes diciembre de 2024 y 2025) → `Scripts/03` → `cotizantes_por_region.csv`; Censo 2024 (`Data raw/personas_censo2024.csv`) → `Scripts/01` → `indicadores_region.csv`; ambas se unen en `Scripts/07` → **`kpi_presion_previsional_region.csv`** (16 regiones).

**Receta A, columna ya calculada**
1. **Fuente principal** = `kpi_presion_previsional_region.csv`.
2. **Agrupar por** = `region_nombre`; **Columna a agregar** = `cobertura_previsional_pct`; **Función** = `mean`.
3. Cifra de control: **Ñuble 37,83**; Magallanes es la mayor y La Araucanía la menor.

**Receta B, desde las columnas base**
1. **Fuente principal** = `kpi_presion_previsional_region.csv`.
2. Marca **Agregar columna calculada**: **A** = `cotizantes_2024`, **Operador** = `÷ dividir`, **B es** `una columna`, **B** = `pob_15_64`, **Multiplicar por** = `100`, **Nombre** = `cobertura_manual`.
3. **Agrupar por** = `region_nombre`; **Columna a agregar** = `cobertura_manual`; **Función** = `mean`. → Ñuble 37,83.

**Promedio país (la línea «País» del gráfico)**
1. Misma fuente. **Agrupar por**: déjalo vacío. **Columna a agregar** = `cotizantes_2024`; **Función** = `sum`. Anota la cifra.
2. Repite con **Columna a agregar** = `pob_15_64`.
3. Divide y multiplica por 100 → **46,5 %**.

**Límite:** cotizantes de dic-2025 contra población del Censo 2024; 13.914 cotizantes no traen región y quedan fuera.

### KPI 1.2 · Razón de soporte 🟡

Fórmula: `Cotizantes ÷ Población 65+`.

**Fuentes:** las de 1.1 más las proyecciones INE (`Data raw/estimaciones-y-proyecciones-de-población-1992-2070_base-2024_base-de-datos.xlsx` → `Scripts/02` → `proyeccion_envejecimiento_pais.csv`; `Scripts/07` → `kpi_proyeccion_regional.csv`).

**Receta, valor actual**
1. **Fuente principal** = `kpi_presion_previsional_region.csv`.
2. **Columna calculada**: **A** = `cotizantes_2024`, `÷ dividir`, **B** = `pob_65_mas`, factor `1`, **Nombre** = `razon_manual`.
3. **Agrupar por** = `region_nombre`; **Columna a agregar** = `razon_manual`; `mean`. → Cifra de control: **Ñuble 1,51** (la más presionada); país: 2,27 (cotizantes de diciembre de 2024 sobre el Censo 2024; con los de 2025 daba 2,30, pero eran 20 meses posteriores al Censo).
   (La columna ya calculada se llama `razon_soporte_previsional`.)

**Receta, escenario 2035 / 2050** (supone que la cobertura de 2024 se mantiene)
1. **Fuente principal** = `kpi_proyeccion_regional.csv`.
2. Marca **Mezclar con una segunda fuente**: **Segunda fuente** = `kpi_presion_previsional_region.csv`, **Cruzar por** = `region_id`, **Tipo de cruce** = `left`.
3. **Columna calculada**: **A** = `cobertura_previsional_pct`, `÷ dividir`, **B** = `indice_dependencia_vejez_proy`, factor `1`, **Nombre** = `razon_2035`. (Equivale a cotizantes proyectados ÷ población 65+ proyectada, con cobertura constante.)
4. **Columnas a filtrar** = `anio`; en el deslizador `anio` deja desde = hasta = `2035` (o `2050`).
5. **Agrupar por** = `region_nombre`; **Columna a agregar** = `razon_2035`; `mean`. → Cifra de control: **Ñuble ≈ 1,05** en 2035.

**Límite:** la población 65+ regional proyectada es un **reparto de las tasas nacionales** del INE, no una proyección oficial regional. 🔴 Mejora pendiente: si el INE publica proyecciones regionales base 2024, se reemplaza (sección 5, ítem D).

#### Análisis adicional del KPI 1.2: ¿dónde está el punto crítico?

Bajo el gráfico del escenario, la misma tarjeta tiene un análisis que responde *a partir de qué año el costo del Pilar Solidario de vejez supera lo que los trabajadores pueden financiar*.

- **Qué se compara** (en pesos de 2025, año a año): **costo** = costo del Pilar Solidario de vejez por persona de 65+ × población de 65+; **capacidad** = carga máxima tolerable × ingreso por trabajador × trabajadores. El cruce de las dos líneas (★) es el punto crítico. La vista «Razón de soporte» muestra lo mismo como cotizantes por persona de 65+ frente a la razón de equilibrio R\*.
- **Interruptores** (un solo gráfico): *Base de ingreso* = **Cotizantes** (ingreso imponible de la SP × cotizantes) o **Todos los ocupados** (ingreso de la ESI del INE × ocupados, «si todos cotizaran»); *Estadístico* = promedio o mediana; *Vista* = dinero o razón de soporte.
- **Territorio:** País (2010-2070, observado hasta 2025), una región (2024 → 2050; ◆ = 2024, 2035 y 2050, los años con población regional) y, tras elegir región, una **comuna** (aproximación: hereda de su región cobertura, ingreso y costo por persona de 65+; solo su estructura de edad del Censo 2024 es propia).
- **Mismo año:** país 2025; región y comuna 2024 (Censo 2024 con cotizantes e ingreso imponible de diciembre 2024, ESI 2024 y gasto 2024).
- **Supuestos que se pueden mover:** carga máxima tolerable (por defecto 10 %, la cotización obligatoria para pensión), crecimiento real del sueldo (1 % anual), cotizantes/población 15-64 en 2050 (solo cotizantes) y si se incluye la PGU de $250.000 (Ley 21.735, sube por edades: 82+ en sep-2025, 75+ en sep-2026, 65+ en sep-2027).
- **Datos:** `kpi_pc_nacional.csv`, `kpi_pc_region.csv`, `kpi_pc_parametros_reforma.csv` (scripts 18 y 19); el cálculo está en `Dashboards/components/critical_point.py`.

**Receta, ingredientes del país en 2025**
1. **Fuente principal** = `kpi_pc_nacional.csv`; **Columnas a filtrar** = `anio`, desde = hasta = `2025`.
2. **Columna calculada**: **A** = `cotizantes_dic`, `÷ dividir`, **B** = `pob_65_mas_ine`, factor `1`, **Nombre** = `razon_manual`. **Agrupar por** = `anio`; **Columna a agregar** = `razon_manual`. → Cifra de control: **2,06 cotizantes por persona de 65+** (con la población INE de 2025). Otras formas de calcular la razón, para no confundirlas: 2,27 = cotizantes regionales de dic-2024 sobre el Censo 2024 (2,59 M de 65+, el de arriba); 2,13 = todos los cotizantes de dic-2024 sobre la proyección INE de 2024 (2,78 M: el INE corrige el subconteo del censo); 2,06 = 2025 con la proyección INE.
3. Mismo filtro, **Columna a agregar** = `costo_vejez_por_65_real25` → **2,15 millones de pesos al año** por persona de 65+ (pesos de 2025).

**Límites:** (1) la carga máxima tolerable es un supuesto, no un dato; (2) el costo por persona de 65+ queda constante en términos reales (la PGU se reajusta por IPC) salvo el aumento a $250.000; (3) el ingreso imponible es bruto y la ESI mide ingreso neto, y las dos bases no se mezclan; (4) la mediana regional del ingreso imponible se estima con la nacional; (5) en la comuna no hay cotizantes, sueldos ni gasto propios; (6) las poblaciones 65+ regionales de 2035 y 2050 siguen siendo el reparto de tasas nacionales de arriba.

### KPI 1.3 · Participación partes interesadas 🔴

Fórmula: `(Aporte empleador + Aporte Estado) ÷ Financiamiento total`.

**Estado:** **no se puede reconstruir todavía.** Tenemos el ingreso del FAPP (estados financieros dic-2025 y jun-2026 en `Data raw/_external/fapp/`) y la nota técnica de DIPRES (`Data raw/_external/dipres/`), pero **falta el monto en pesos de las cotizaciones de los trabajadores**, que es el denominador. Ver sección 5, ítem A.

Receta prevista, **sin probar** hasta que exista el dato: tras crear `Scripts/15_procesar_financiamiento.py` (sección 6) que escriba `financiamiento_por_fuente.csv` con una fila por año y pagador (trabajador, empleador, Estado), en el Explorador: **Fuente principal** = ese archivo, **Agrupar por** = `anio` y `fuente`, **Columna a agregar** = `monto_mm`, `sum`, y se divide (empleador + Estado) por el total.

### KPI 2.1 · Costo real por adulto mayor 🟢

Fórmula: `(Costo público total ÷ Población 65+)` comparado con el crecimiento del PIB per cápita.

**Fuentes:** DIPRES, *Estadísticas de las Finanzas Públicas 2016-2025* (`Data raw/_external/dipres/articles-416514_doc_xls.xlsx`, hoja `CFEGCT$25`, línea «7102 Edad avanzada», pesos de 2025) y Banco Central, PIB (`Data raw/_external/macro/CCNN2018_P0_V2.xlsx`) → `Scripts/13` → `gasto_proteccion_social.csv` y `macro_pib_anual.csv`; población: `proyeccion_envejecimiento_pais.csv`.

**Receta, costo público por persona 65+**
1. **Fuente principal** = `gasto_proteccion_social.csv`.
2. **Mezclar con una segunda fuente**: `proyeccion_envejecimiento_pais.csv`, **Cruzar por** = `anio`, `left`.
3. **Columna calculada**: **A** = `gasto_mm_2025`, `÷ dividir`, **B** = `pob_65_mas`, **Multiplicar por** = `1000000`, **Nombre** = `costo_65`. (El gasto está en millones de pesos de 2025.)
4. **Columnas a filtrar** = `categoria` → deja solo `Edad avanzada`.
5. **Agrupar por** = `anio`; **Columna a agregar** = `costo_65`; `mean`. → Cifra de control: **2025 ≈ 5,13 millones de pesos por persona 65+**.

**Receta, PIB per cápita real**
1. **Fuente principal** = `macro_pib_anual.csv`; **segunda fuente** = `proyeccion_envejecimiento_pais.csv`, por `anio`, `inner`.
2. **Columna calculada**: **A** = `pib_real_mm_2018`, `÷ dividir`, **B** = `pob_total`, factor `1000000`, **Nombre** = `pib_pc_real`.
3. **Agrupar por** = `anio`; **Columna a agregar** = `pib_pc_real`; `mean`.

**Comparación:** divide el valor de 2025 entre el de 2016 en cada receta: el costo por persona 65+ sube **+11 %** y el PIB per cápita real **+9 %** (tarjetas del dashboard). Casi todo el alza es el salto de 2022 (PGU): desde entonces el costo por persona baja **−5 %**. El dashboard lo muestra en pesos reales de 2025, no como índice.

**Pestañas del dashboard (módulo `Dashboards/components/cost_analysis.py`, probado en `tests/test_costo_65.py`):**
- *Qué lo explica:* costo por persona 65+ = PGU + PBS/APS de vejez (Subsecretaría de Previsión Social, `pgu_pbs_aps_nacional_anual.csv`, × deflactor de `kpi_pc_nacional.csv`) + **resto** (= Edad avanzada − los dos anteriores; DIPRES no lo abre). La PGU de 2022 es un residual: Total − (PBS + APS).
- *Por beneficiario:* beneficios de vejez (PGU + PBS vejez + APS vejez, promedio del año) por cada 100 personas 65+ y pago anual por beneficio. Una persona puede tener más de un beneficio: la cobertura es un tope.
- *Frente al ingreso:* costo por persona 65+ como % del PIB per cápita (corriente / corriente); 10 % × 12 × ingreso mediano real de los ocupados (INE, ESI, `kpi_pc_nacional.csv`) = aporte anual de un ocupado mediano; «necesarios» = costo por 65+ ÷ ese aporte; «carga requerida» = gasto ÷ (ocupados × 12 × mediana). Cifras 2025: 30 % del PIB per cápita, 6,3 necesarios vs 3,3 disponibles, 19 %.
- *Proyección 2050:* escenario con la población INE, PIB real (deslizador), PGU de $250.000 (opcional) y el «resto» constante o creciendo con la población 65+.

**Límites:** «Edad avanzada» es el gasto del Gobierno Central e incluye el sistema antiguo, la PGU y los aportes solidarios. El PIB real es volumen encadenado (referencia 2018) y el gasto está en pesos de 2025; por eso el PIB per cápita real se compara como variación y no por nivel. El 10 % es una escala de comparación: va a cuentas individuales y estos gastos se pagan con impuestos generales.

### KPI 2.2 · Financiamiento dedicado 🟡

Fórmula: `(PGU + Pensión solidaria) ÷ PIB` y `(Activos + Reservas) ÷ VP del déficit`.

**Ratio 1 🟢**

**Fuentes:** informes del cierre anual del Pilar Solidario (Subsecretaría de Previsión Social, `Data raw/_external/pilar_solidario/`) → `Scripts/12` → `pgu_pbs_aps_nacional_anual.csv`; PIB corriente de `macro_pib_anual.csv`.

1. **Fuente principal** = `pgu_pbs_aps_nacional_anual.csv`; **segunda fuente** = `macro_pib_anual.csv`, por `anio`, `left`.
2. **Columna calculada**: **A** = `monto_nominal_mm`, `÷ dividir`, **B** = `pib_corriente_mm`, **Multiplicar por** = `100`, **Nombre** = `pct_pib`.
3. **Columnas a filtrar** = `tipo_beneficio` → deja solo `Total`. (Otros valores: `PGU`, `PBS vejez`, `PBS invalidez`, `APS vejez`, `APS invalidez`.)
4. **Agrupar por** = `anio`; **Columna a agregar** = `pct_pib`; `mean`. → Cifra de control: **2025 = 2,07 %**.
5. Para comparar con el gasto total en vejez: `gasto_proteccion_social.csv`, filtro `categoria` = `Edad avanzada`, columna `pct_pib` (2025 = 4,39 %, coincide con lo publicado por DIPRES).

**Ratio 2 🔴:** `(Activos + Reservas) ÷ VP del déficit`. Falta el **valor presente del déficit**. Hasta conseguirlo, la propuesta es `saldo del fondo (FAPP + FRP) ÷ gasto anual en PGU y APS` («años de cobertura»). Ver sección 5, ítems B y C.

**Límite:** el «Total» del Pilar incluye PBS/APS de invalidez, además de vejez. Hay una diferencia de −0,16 % en 2025 entre la suma mensual y el resumen anual publicado en el propio informe; 2022-2024 coinciden exactamente.

### KPI 2.3 · Pobreza en la vejez 🟢

Fórmula: `Personas 65+ bajo la línea de pobreza ÷ Población 65+`.

**Fuente:** CASEN 2022 completa (`Data raw/_external/casen2022/casen_2022.dta`, 501 MB, no está en GitHub) → `Scripts/14` → **`pobreza_65_region.csv`** (17 filas: Chile y 16 regiones). Variables usadas: `edad`, `region`, `pobreza`, `expr`, `varstrat`, `varunit`. El error estándar se calcula con el diseño muestral.

**Receta**
1. **Fuente principal** = `pobreza_65_region.csv`.
2. **Agrupar por** = `region_nombre`; **Columna a agregar** = `pct_pobreza_65`; `mean`. → Cifras de control: **Chile 14,9 %**; la más alta **La Araucanía (23,2 %)**; la más baja **Magallanes (9,8 %)**.
3. Otras columnas útiles para el mismo agrupamiento: `ic95_inf` e `ic95_sup` (intervalo de confianza 95 %), `pct_pobreza_extrema_65`, `pct_pobreza_menores_65` (comparación con menores de 65: Chile 21,3 %), `n_muestra_65`.

**Límites:** (1) **metodología:** la base ya trae `pobreza` con la metodología 2024 del Ministerio (20,5 % de pobreza en 2022; con la anterior eran 6,5 %); no se compara con cifras publicadas en 2023. (2) **Encuesta muestral:** en regiones pequeñas (Aysén, Magallanes, Tarapacá) los intervalos son amplios; lee los rangos. Calcular desde cero requiere el archivo de 501 MB y correr `Scripts/14`.

---

## 4. Cifras de control (para comprobar que todo está bien)

| KPI | Cifra | Dónde |
|---|---|---|
| 1.1 | Ñuble 37,83 % · país 46,5 % | Objetivo 1 / Explorador |
| 1.2 | Ñuble 1,51 · país 2,27 · Ñuble 2035 ≈ 1,05 | Objetivo 1 / Explorador |
| 1.2 punto crítico | País 2025: 2,06 cotizantes por 65+ · carga requerida 6,7 % del sueldo · punto crítico **2039** (promedio, cotizantes, carga máx. 10 %, sueldo +1 %) · 2,15 M$ por persona 65+ | Objetivo 1 / Explorador |
| 2.1 | 5,13 millones por persona 65+ (2025) · costo +11 % vs PIB per cápita +9 % (2016-2025) | Objetivo 2 / Explorador |
| 2.2 | 2,07 % del PIB (2025) · gasto en vejez 4,39 % | Objetivo 2 / Explorador |
| 2.3 | Chile 14,9 % · La Araucanía 23,2 % · Magallanes 9,8 % | Objetivo 2 / Explorador |

Para verificarlo todo de una vez: `"Data raw/.venv/bin/python" -I -m pytest tests -q` (49 pruebas).

---

## 5. 🔴 Datos que faltan, dónde conseguirlos y cómo instalarlos

### A. Monto en pesos de las cotizaciones de los trabajadores, 2024 y 2025 (KPI 1.3)

- **Qué falta:** el denominador «financiamiento total». Ningún archivo trae pesos: `cotizaciones_totales.xls` solo **cuenta** cotizaciones y los estados del FAPP solo cubren el ingreso del FAPP.
- **Dónde:** sitio de la **Superintendencia de Pensiones**, `https://www.spensiones.cl` → menú superior **Estadísticas e Informes** → pestaña **Estadísticas y bases de datos**. (La ruta sale de la pantalla del sitio; el enlace directo a cada tabla no está verificado.)
  1. **Sistema de Pensiones → Cotizaciones y Cotizantes**: montos de cotizaciones, base 2024 antes de la reforma.
  2. **Seguro Social Previsional → Montos de cotizaciones acreditadas**: aporte del empleador al nuevo seguro social (desde agosto de 2025), numerador de 2025-26.
  3. Opcional: **Seguro Social Previsional → Cotizantes** y **Beneficiarios**; **Sistema de Pensiones → Estadísticas financieras** (ingresos de las AFP, para el modo desarrollador).
- **Guardar en:** `Data raw/_external/spensiones/`.
- **Después:** crear `Scripts/15_procesar_financiamiento.py` (sección 6).

### B. Valor presente del déficit (KPI 2.2, ratio 2)

- **Qué falta:** el valor presente del déficit proyectado. La nota técnica de DIPRES sobre el FAPP (ya en `Data raw/_external/dipres/articles-397500_doc_pdf.pdf`) solo estima ingresos y egresos del fondo.
- **Dónde:** el **Informe Financiero** del proyecto de la **Ley 21.735** (publicada el 26-mar-2025). Buscarlo en DIPRES (`https://www.dipres.gob.cl/598/w3-propertyvalue-15499.html`, enlace que usted indicó; **no pude abrirlo desde aquí**) y en la Biblioteca del Congreso Nacional (`https://www.bcn.cl/portal/leyfacil/recurso/reforma-de-pensiones-de-2025`, resumen de la ley; el informe financiero está en la «Historia de la Ley»).
- **Decisión del equipo (no es un archivo):** si no aparece, reemplazar el ratio 2 por `saldo del fondo (FAPP + FRP) ÷ gasto anual en PGU y APS` y dejarlo escrito en la tarjeta.

### C. Saldo del Fondo de Reserva de Pensiones, FRP (KPI 2.2, «reservas»)

- **Qué falta:** la serie del saldo. La publicación de DIPRES lo menciona (PDF `Data raw/_external/dipres/articles-416513_doc_pdf.pdf`, páginas 126 y 164) pero **no está verificado que traiga la serie**; la nota técnica indica que el FRP transfirió hasta US$900 millones al FAPP.
- **Dónde:** revisar esas páginas; si no está, los informes del FRP del Ministerio de Hacienda (sin enlace verificado).
- **Guardar en:** `Data raw/_external/dipres/`.

### D. Opcionales (no bloquean los 6 KPIs)

| Dato | Dónde | Para qué |
|---|---|---|
| CASEN 2024 (más reciente que 2022; pobreza 2024 = 17,3 %) | Observatorio Social, Ministerio de Desarrollo Social: `https://observatorio.ministeriodesarrollosocial.gob.cl`, sección Casen, «Base de datos Casen 2024 STATA» + libro de códigos + nota de uso | Actualizar KPI 2.3 a 2024 |
| Proyecciones regionales INE base 2024 (si existen) | `https://www.ine.gob.cl`, «Estimaciones y proyecciones de la población» (enlace no verificado) | Reemplazar el reparto de tasas nacionales del KPI 1.2 |
| Fuentes de cifras citadas en la presentación: ingreso mediano INE 2024 ($611.162), ingreso mediano de Alemania, cobertura 17,3 % del IPS | INE (ESI/ENE) y Destatis | Citar cada cifra con su archivo |
| Comisiones, traspasos entre AFP y sucursales | Superintendencia de Pensiones | Modo desarrollador (KPIs de la diapositiva 14 que quedaron fuera de los 6) |

---

## 6. Agregar una fuente de datos nueva y que aparezca en el dashboard

1. **Guardar el archivo** en `Data raw/`, en la carpeta del tema (`_external/spensiones/`, `_external/dipres/`, etc.). Si solo sirve para el modo desarrollador, en `Data raw/development sources/`. Lo que no haga falta va a `Data raw/archive/<KPI>/`.
2. **Crear el script** `Scripts/NN_nombre.py` siguiendo los existentes (por ejemplo `Scripts/12_procesar_pilar_solidario.py` para Excel con formato irregular y `Scripts/13_procesar_macro_gasto.py` para tablas anuales): leer desde `Data raw/`, validar contra una cifra publicada y escribir un CSV **ordenado** en `Data processed/`.
3. **Usar nombres de columna estándar** para que el Explorador pueda cruzar: `region_id`, `region_nombre`, `comuna_id`, `anio` (año con cuatro dígitos). Una fila por clave si es posible.
4. **Ejecutar** `"Data raw/.venv/bin/python" -I Scripts/NN_nombre.py`.
5. **Verlo en el Explorador:** menú ⋮ → **Clear cache**, recargar y elegir el archivo en **Fuente principal**. Además aparece en el inventario de **Estado de datos y KPIs**.
6. **Mostrarlo en el dashboard final:** en `config/kpis.yaml`, sección `kpis_presentacion`, cambiar el KPI a `status: live` (o `partial`), anotar `archivo`, `fuente`, `script` y `caveat`, y borrar `pendiente_motivo`/`datos_faltantes`; luego agregar una función `render_x_y()` en `Dashboards/final_pages/objetivo1.py` u `objetivo2.py` y pasarla a `kpi_card("x.y", render_x_y)`. Los gráficos reutilizables están en `Dashboards/components/charts.py`.
7. **Probar:** agregar una receta a `tests/test_manual_mode.py` y correr `pytest tests -q`.

---

## 7. Si algo no se ve

| Síntoma | Causa y solución |
|---|---|
| El menú tiene «Inicio» y seis páginas con emojis | Servidor viejo. Ciérralo (`lsof -ti :8501 \| xargs kill`) y vuelve a abrir (sección 0). |
| No hay menú lateral | Ventana angosta: abre con la flecha `>` arriba a la izquierda. |
| «Modo desarrollador» no muestra las páginas | Recarga con Cmd+R. Alternativa: abre `http://localhost:8501/?mode=dev`. |
| Una tabla nueva no aparece en el Explorador | Caché: menú ⋮ → **Clear cache** y recarga. |
| `ModuleNotFoundError` al abrir | Estás usando otro Python. Usa `Data raw/.venv/bin/streamlit`. |
| Avisos `use_container_width` en la consola | Inofensivos hoy; Streamlit los retirará en una versión futura (pendiente de corregir en todas las páginas). |
