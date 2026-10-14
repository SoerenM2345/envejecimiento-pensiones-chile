# Inventario de fuentes de `Data raw/`: qué es cada una y qué contiene

Elaborado el 2026-10-13 abriendo los archivos (hojas, cabeceras, rangos de fechas, notas al pie, conteos de filas), no solo leyendo los nombres.
Complementa a [README.md](README.md) (que dice *dónde* está cada archivo); este documento dice *qué es* y *qué hay adentro*.

Convenciones: «MM$» = millones de pesos; «M$» = miles de pesos; las cifras de ejemplo son valores leídos directamente del archivo.

---

## 0. Panorama

| Zona | Archivos | Peso | Rol |
|---|---|---|---|
| Raíz (3) + `_external/` (41) | 44 | ≈ 3,0 GB | Fuentes activas: alimentan los 6 KPIs de la presentación y el análisis del problema |
| `import_KPI1.2/` | 106 + 228 descargados | ≈ 12 MB | Insumos del análisis «punto crítico» del KPI 1.2 (ingreso por trabajador, IPC); ver §2.7 |
| `development sources/` | 9 | 7,4 MB | Solo el modo desarrollador del dashboard |
| `archive/` | 59 (23 son copias) | 29 MB | Descartados, pero conservados |
| `.venv/` | — | 974 MB | **No es una fuente**: entorno Python del proyecto |

### Qué fuente alimenta qué KPI

| KPI / análisis | Fuentes que lo alimentan |
|---|---|
| Problema general (envejecimiento, pirámides) | Censo 2024, Proyecciones INE, Destatis (Alemania) |
| 1.1 Cobertura regional | `cotizantes_region.xls` + Censo 2024 |
| 1.2 Razón de soporte | `cotizantes_region.xls` + Censo 2024 + Proyecciones INE. **Análisis «punto crítico»:** `import_KPI1.2/` (ingreso imponible SP, ESI y ENE del INE, IPC) + Pilar Solidario + Proyecciones INE |
| 1.3 Participación partes interesadas | Fichas Estadísticas Previsionales (cotizantes e ingreso promedio 2024-2025), Nota Técnica Ley 21.735 (Tabla 1), FAPP. El monto oficial en pesos de las cotizaciones no está: el KPI usa la estimación cotizantes × ingreso × 10 % |
| 2.1 Costo real por adulto mayor | DIPRES (gasto «7102 Edad avanzada»), Banco Central (PIB), Proyecciones INE |
| 2.2 Financiamiento dedicado | Pilar Solidario (OND 2023-2025), Banco Central, DIPRES, FAPP (estados), informe mensual del FRP, Ley 21.735 (Tabla 2), SII (UTM, dólar) |
| 2.3 Pobreza en la vejez | CASEN 2022 completa (`casen_2022.dta`) |

---

## 1. Fuentes activas en la raíz de `Data raw/`

### 1.1 `personas_censo2024.csv`: Censo 2024, microdatos de personas
- **Productor:** INE Chile. **Tamaño:** 2,5 GB (no versionado en Git). **Separador:** `;`.
- **Contenido:** una fila por persona. **18.480.432 personas**, 6.622.597 hogares (combinaciones vivienda-hogar distintas), 346 comunas, 56 provincias, 16 regiones.
- **Columnas (≈ 70):** identificadores (`id_vivienda`, `id_hogar`, `id_persona`); territorio (`region`, `provincia`, `comuna`, `area` urbano/rural); `sexo`, `edad`, `edad_quinquenal`, `parentesco`; estado civil, lugar de residencia y de nacimiento, nacionalidad, pueblos originarios, afrodescendencia, religión; 6 preguntas de dificultad funcional (ver, oír, mover, cognición, cuidado, comunicación) y `discapacidad`; educación (`escolaridad`, `cine11`, asistencia por nivel); fuerza de trabajo (`sit_fuerza_trabajo`, CIUO/CAENES, medio de transporte); fecundidad (hijos nacidos, sobrevivientes, último nacimiento).
- **Datos de referencia:** 2.587.238 personas con `edad_quinquenal ≥ 65` (14,0 %). Mujeres 9.513.399, hombres 8.967.033. 16.018.474 en área urbana, 2.461.958 en rural.
- **Atención:** en 51 comunas pequeñas (`comuna_bajo_umbral`) el INE enmascara `edad` con el valor `-66` (151.199 personas, 0,8 %). Por eso se trabaja con `edad_quinquenal`, que está completa. Con `edad` exacta, `≥ 65` da solo 2.560.690.
- **Uso:** script 01 → `indicadores_comuna/region.csv`, pirámides, mapas.

### 1.2 `estimaciones-y-proyecciones-de-población-1992-2070_base-2024_base-de-datos.xlsx`: Proyecciones INE
- **Productor:** INE Chile, base Censo 2024. **Hoja única** `BBDD_EEPP-2024_0101`, 31.916 filas × 5 columnas.
- **Columnas:** `NIVEL`, `SEXO`, `FECHA`, `EDAD` (0-100), `POBLACION`.
- **Cobertura:** solo `NIVEL = PAÍS` (no hay regiones ni comunas), 158 cortes de fecha (1 de enero y 30 de junio) entre 1992 y 2070. Población total: 13,66 M (1992), 19,83 M (2024), 17,06 M (2070).
- **Atención:** como no hay proyección subnacional, la proyección regional del proyecto es un reparto de tasas nacionales (aproximación, no cifra oficial).
- **Uso:** script 02 → pico de población activa, 14 % → 43 % de 65+, KPI 1.2 (proyección), KPI 2.1 (denominador).

### 1.3 `cotizantes_region.xls`: Cotizantes por región, 1985-2025
- **Productor:** Superintendencia de Pensiones. Hoja `Cot_región`, 30 filas × 42 columnas.
- **Contenido:** número de cotizantes por región (columnas = años 1985…2025), cifras a diciembre de cada año. Incluye `Sin Información` y `Total`.
- **Datos de referencia:** total 1.321.938 (1985) → **5.974.428 (2025)**. R. Metropolitana 2.678.039; `Sin Información` 13.914 en 2025.
- **Atención:** XIV, XV y XVI aparecen con «-» antes de su creación. Definición: afiliados que cotizaron en diciembre por remuneraciones del mes anterior.
- **Uso:** script 03 → KPI 1.1 y 1.2.

---

## 2. Fuentes activas en `_external/`

### 2.1 `16_bevoelkerungsvorausberechnung_daten.csv`: Población de Alemania (Destatis)
- **Productor:** Statistisches Bundesamt (Destatis). **Formato:** `;`, decimal con coma, 2.818 filas × 104 columnas.
- **Estructura:** `Variante` (30 valores), `Simulationsjahr`, `mw` (m/w = sexo), `Bev` (total) y `Bev_0_1 … Bev_99_100` (población por año de edad). Las cifras están en **miles de personas**.
- **Cobertura:** `Variante 0` = datos históricos 1950-2024; variantes 1-29 = escenarios de proyección 2025-2070. En 2024: 41.241,7 mil hombres y 42.335,4 mil mujeres (≈ 83,6 M).
- **Uso:** scripts 10 y 11 usan solo `Variante 0`, año 2024 → comparación de pirámides Chile-Alemania.

### 2.2 `pilar_solidario/`: Informes trimestrales del Pilar Solidario (3 archivos)
- **Productor:** Subsecretaría de Previsión Social, Dirección de Estudios Previsionales.
- **Archivos:** informe del trimestre **OND** (octubre-diciembre = cierre de año) de 2023, 2024 y 2025. Tienen 32, 32 y 35 hojas.
- **Estructura del informe (índice):**
  - **I. Beneficios pagados** (1.1 total nacional, 1.2 regional, 1.3 PGU, 1.4 PBS, 1.5 APS, 1.6 suspendidos y extintos): beneficiarios, monto real (MM$) y monto promedio, por sexo, tipo de beneficio y tramo etario. Incluye hojas pivote con series mensuales desde 2008 (`dinamica pgu`, `N PBS`, `MONTOS PBS`, `DINAMICA APS`).
  - **II. Estado de solicitudes** (2.1-2.6): solicitudes ingresadas, concedidas y rechazadas, nacional, regional y comunal, y tasas de concesión (jul-2008 a sep-2025).
  - **III. Bono por Hijo** y **IV. Subsidio al Trabajador Joven**: series desde 2009.
  - Hojas históricas: `Regiones` y `Comunas` (concesiones jul-2008 a dic-2022), `Por sexo`, `Focalización y monto del beneficio (SPS y PGU, 2008-2023)`.
- **Datos de referencia (OND 2025):** diciembre 2025: PGU 2.243.121 beneficiarios (1.297.963 mujeres y 945.158 hombres). Año 2025: PGU 5.819.013 MM$ reales; total Pilar 7.104.117 MM$ reales, con 2,64 M de beneficiarios promedio. Serie mensual procesada: ago-2008 a dic-2025.
- **Atención:** el «Total» incluye PBS/APS de invalidez, no solo vejez. La PBS de vejez queda en 0 en 2025 (la reemplaza la PGU).
- **Uso:** script 12 → `pgu_pbs_aps_nacional_anual/mensual.csv`, `pgu_pbs_aps_region_trimestral.csv` → KPI 2.1 y 2.2.

### 2.3 `dipres/`: Finanzas públicas (4 archivos)
- **Productor:** Dirección de Presupuestos (DIPRES), Ministerio de Hacienda.

| Archivo | Qué es | Contenido |
|---|---|---|
| `articles-416514_doc_xls.xlsx` | *Estadísticas de las Finanzas Públicas 2016-2025*, cuadros del **Gobierno Central** (24 hojas) | Estado de operaciones (total, presupuestario, extrapresupuestario), balance cíclicamente ajustado, ejecución trimestral y mensual 2025, **clasificación funcional** de erogaciones (en MM$ corrientes, MM$ de 2025, % PIB y % gasto total), ingresos tributarios e impuestos a la renta |
| `articles-416517_doc_xls.xlsx` | Mismas estadísticas, cuadros del **Sector Público** (13 hojas) | Pasivos y activos financieros (Gobierno Central, Banco Central, empresas públicas), pasivo consolidado, perfil de amortizaciones, deuda garantizada, **Bonos de Reconocimiento** (1982-2025: bonos liquidados y stock actualizado de los bonos activos, en MM$ y % PIB), deuda bruta |
| `articles-416513_doc_pdf.pdf` | Versión publicación del mismo documento (167 páginas, mayo 2026) | Texto y los mismos cuadros, incluida la clasificación funcional |
| `articles-397500_doc_pdf.pdf` | *Nota técnica «Estimación de ingresos y egresos del FAPP»*, Estudios de Finanzas Públicas 2025/47 (37 páginas, diciembre 2025) | Contexto de la Ley 21.735 (Seguro Social Previsional), transferencias del Fondo de Reserva de Pensiones al FAPP (hasta US$ 900 M; primera de US$ 200 M), proyección mensual de ingresos y egresos hasta mediados de 2030, tasa de reintegro (2,5 %), valor esperado del balance |

- **Datos de referencia (gasto «7102 Edad avanzada», Gobierno Central):** 6.226.523 MM$ (2016) → **14.909.335 MM$ (2025)**. Equivale a 3,7 % → 4,4 % del PIB y a 15,6 % → 18,0 % del gasto total.
- **Uso:** script 13 lee solo las hojas `CFEGCT`, `CFEGCT$25` y `CFEGCT%PIB` de `416514` → `gasto_proteccion_social.csv` (KPI 2.1 y 2.2). Las hojas `PAFGC`, `PAFGC%PIB` y `Bono_Reconocimiento` de `416517` se procesan en el script 16 (`dipres_pasivos_activos_gc.csv`, `bonos_reconocimiento.csv`). El resto de las hojas y los PDF son contexto sin script.

### 2.4 `macro/CCNN2018_P0_V2.xlsx`: PIB anual, Banco Central
- **Productor:** Banco Central de Chile, Cuentas Nacionales, referencia 2018. Tres hojas: `Cuadro`, `Metadatos`, `Series`.
- **Contenido:** 3 series anuales 2013-2025, en miles de millones de pesos: PIB a precios corrientes, PIB volumen a precios del año anterior encadenado, y esta última desestacionalizada. Última actualización: 18-08-2026.
- **Datos de referencia:** PIB corriente 137.309 (2013) → 339.978 (2025). PIB real encadenado 169.864 → 215.645. Crecimiento real 2025: +2,5 %.
- **Atención:** la hoja `Metadatos` dice «frecuencia trimestral», porque describe la serie original; el cuadro entregado ya es anual. El PIB encadenado no es comparable en nivel con pesos de 2025, por eso los índices usan base 2016 = 100.
- **Uso:** script 13 → `macro_pib_anual.csv` (KPI 2.1 y 2.2).

### 2.5 `fapp/`: Estados financieros del Fondo Autónomo de Protección Previsional (2 PDF)
- **Productor:** FAPP, con informe de auditores KPMG. El FAPP nace con la Ley 21.735 y paga el Seguro Social Previsional.

| Archivo | Período | Datos clave (miles de pesos) |
|---|---|---|
| `FAPP_estados_financieros_2025-12-31.pdf` (28 págs.) | 1-ago-2025 a 31-dic-2025 | Patrimonio final 282.861.092. Cotizaciones 272.374.252. Aporte del Estado 0. Pasivo FRP 200.196.177. Cotizaciones impagas 5.938.791 (cuenta de orden) |
| `FAPP_estados_financieros_interinos_2026-06-30.pdf` | enero a 30-jun-2026 (revisión limitada) | Cotizaciones **439.587.480**. Aporte del Estado 0. Transferencias al IPS para pagar beneficios 698.890.077 (606.036.423 por años cotizados y 92.853.654 por expectativa de vida). Rentabilidad cartera 9.001.349. Patrimonio final 25.719.095. Pasivo FRP 208.272.126 |

- **Contenido:** balance general, estado de variación patrimonial y notas. El texto indica que los aportes del Estado comienzan en enero de 2027.
- **Uso:** KPI 1.3 y, en el KPI 2.2, script 21 → `fapp_balance.csv` (balance de ambos cierres y flujo de enero a junio de 2026). Las cifras se transcribieron a mano (no hay lector de PDF en el entorno) y el script valida que activos = pasivos exigibles + patrimonio.

### 2.5b `frp/`: Informe Ejecutivo Mensual del Fondo de Reserva de Pensiones, julio 2026 (1 PDF)
- **Productor:** DIPRES, Ministerio de Hacienda. Descargado el 2026-10-13 de `https://www.dipres.gob.cl/598/articles-426503_doc_pdf.pdf` (abierto y leído; la URL salió de una búsqueda web).
- **Contenido (pág. 2):** variación anual del valor de mercado 2020-2025 en millones de US$: inicial, aportes, retiros, interés, ganancias de capital, costos, final. A fines de 2025: **US$ 10.313,19 M** (incluye US$ 222,05 M de la transferencia de US$ 200 M al FAPP del 1-ago-2025); retiros 2022-2025: 268,92 / 299,94 / 303,59 / 332,39. Composición por clase de activo y rentabilidad.
- **Atención:** los retiros de 2020 (1.576,48) y 2021 (2.959,82) no se desglosan. El valor de mercado total incluye la cuenta por cobrar al FAPP: para sumarlo con los activos del FAPP se usa la cartera propia (total menos transferencia).
- **Uso:** script 21 → `frp_reserva_anual.csv` (KPI 2.2). El dólar (promedio anual para los retiros, último día hábil para los saldos) sale del SII (`https://www.sii.cl/valores_y_fechas/dolar/dolarAAAA.htm`, 2022-2025, abiertas el 2026-10-13); la UTM de 2025, de `https://www.sii.cl/valores_y_fechas/utm/utm2025.htm`. El dólar de cierre coincide al centavo con el que implica la tabla de activos en dólares de DIPRES (script 21 lo valida).
- **Aporte del Estado al FAPP:** Tabla 2 de la *Nota Técnica Reforma de Pensiones Ley 21.735* (Subsecretaría de Previsión Social, julio 2025, `Data raw/_external/ley_21735/`), pág. 13-14: 2,2 millones de UTM en 2028 y 2029, 5, 7, 9, 10, 12, 13, 14 y 15 hasta 2037; DIPRES (`articles-397500`) dice «año 12 en adelante: 15 millones» y ubica el primer aporte «en 2027». Se usa 2028 y se prueba 2027.

### 2.8 `fichas_previsionales/`: Fichas Estadísticas Previsionales (24 PDF)
- **Productor:** Superintendencia de Pensiones. Una ficha mensual, N° 136 (marzo 2024) a N° 159 (febrero 2026): 24 números consecutivos, sin huecos, de ≈ 10 páginas.
- **Contenido (ficha 159):** valor de los Fondos de Pensiones A-E (US$ 255.451 M, 66,2 % del PIB a enero 2026), cartera de inversión y rentabilidad real; **afiliados y cotizantes del mes de referencia** (dic-2025: 12.112.802 afiliados, **5.974.428 cotizantes**, ingreso promedio $ 1.299.840; hombres $ 1.373.224, mujeres $ 1.206.186); traspasos entre fondos, cuentas APV y una tabla por AFP (afiliados, cotizantes, comisión, ingreso imponible).
- **Cobertura útil:** el mes de referencia de cada ficha es el mes anterior a su fecha de publicación: ene-2024 a dic-2025, 24 meses. Los 5.974.428 cotizantes y los $ 1.299.840 de dic-2025 coinciden con `cotizantes_region.xls` y con el cuadro 04A.
- **Uso:** script 15 (KPI 1.3, estimación del monto de cotizaciones).

### 2.9 `ley_21735/`: Nota Técnica «Reforma de Pensiones, Ley N° 21.735»
- **Productor:** Subsecretaría de Previsión Social, Dirección de Estudios Previsionales (44 páginas; la portada dice «Julio de 2025», no agosto).
- **Contenido:** Tabla 1 (gradualidad de la cotización del empleador), Tabla 2 (aporte anual del Estado al FAPP, en millones de UTM, desde 2028), **Tabla 3 (gradualidad de la PGU de $ 250.000: 82+ desde el 1-sep-2025, 75+ desde el 1-sep-2026, 65+ desde el 1-sep-2027)**, Tabla 4 (calendario de reajustes de la PGU), cotización con rentabilidad protegida, beneficio por años cotizados y compensación por expectativa de vida.
- **Uso:** script 15 (Tabla 1) y script 21 (Tabla 2). La Tabla 3 respalda el calendario de la PGU del script 18 (ver §6, punto 11).

### 2.6 `casen2022/`: Encuesta CASEN 2022 (4 archivos)
- **Productor:** Ministerio de Desarrollo Social y Familia (División Observatorio Social; INE ejecutó el diseño muestral).

| Archivo | Qué es |
|---|---|
| `casen_2022.dta` (501 MB, no versionado) | Base de microdatos en formato Stata: **202.231 personas × 959 variables**, de las cuales 33.570 tienen 65 años o más (sin expandir) |
| `Libro_de_codigos_…(18marzo2024).xlsx` | Diccionario con ficha técnica, cuestionario y una hoja por módulo (hoja de ruta, factores de expansión, residentes, educación, trabajo, ingresos, salud, identidades, vivienda, ingresos CEPAL y MDSF, pobreza multidimensional, variables adicionales, anexos CIUO y CAENES) con etiquetas de valores y frecuencias |
| `Nota uso base de datos Casen 2022.pdf` (5 págs.) | Recomendaciones de uso: la encuesta es representativa a nivel nacional, regional y por área (urbano/rural), y debe usarse el factor de expansión regional `expr` (calibrado por raking con proyecciones base Censo 2017) |
| `Valor_CBA_y_LPs_25.12.pdf` (14 págs.) | Informe mensual de diciembre 2025: valor de la canasta básica y líneas de pobreza. Línea de pobreza por persona equivalente: $ 241.258. Línea de pobreza extrema: $ 160.838 |

- **Variables clave del `.dta`:** `region`, `edad`, `sexo`, `expr`, `pobreza` (pobreza por ingresos), `pobreza_2013`, `pobreza_severa`, `pobreza_multi`, `ytotcor`, `ytotcorh`, `ypchtrabcor`, `y2803` (jubilación o pensión de vejez), `pco1`, `nse`, `activ`, `esc`. **No trae comuna.**
- **Resultado procesado:** pobreza 65+ nacional 14,9 % (error estándar 0,27 pp; IC 95 %: 14,4 %-15,4 %) frente a 21,3 % en menores de 65 (`pobreza_65_region.csv`).
- **Atención:** la variable `pobreza` usa la metodología 2024, mientras que el PDF de líneas de pobreza está calculado con la metodología 2013 (el propio PDF lo advierte). Sirve de contexto, no de insumo numérico.
- **Uso:** script 14 → `pobreza_65_region.csv` (KPI 2.3).

### 2.7 `import_KPI1.2/`: ingreso por trabajador y deflactor (análisis «punto crítico» del KPI 1.2)
- **Productores:** Superintendencia de Pensiones (SP), INE y Banco Central. Descargados el 2026-10-13.

| Archivos | Qué son | Cobertura |
|---|---|---|
| `04A*.xls` (60) + `04A_descargas/04A_AAAAMM.xls` (228, script 19) | Cuadro 04A de la SP: **nº de cotizantes e ingreso imponible promedio por tipo (dependientes, independientes, voluntarios) y sexo**. Son tablas HTML con extensión `.xls` (latin-1). El título trae la fecha («Al 31 de Diciembre de 2024») | Mensual, **octubre 2002 a agosto 2026** (287 meses, sin huecos). A mano estaban enero 2020 a diciembre 2024 |
| `32C*.xls`, `estadisticas (n).xls` | **Ingreso imponible promedio por región y AFP**; se usa la fila Total. Ñuble aparece desde 2018 (antes forma parte de Biobío) | Cada diciembre, 2010-2025 (16 años) |
| `19B*.xls`, `estadisticas (n).xls` | **Cotizantes por tramo de ingreso imponible** (tramos de $20-50 mil, hasta $3,5 M) y AFP. De aquí sale la mediana de los cotizantes | Cada diciembre, 2010-2025 |
| `CL01,DF_YMEDIANOOCU_SEXO,1.0+A....csv`, `CL01,DF_YMEDIOOCU_SEXO,1.0+A....csv` | INE, **Encuesta Suplementaria de Ingresos (ESI)**: ingreso mediano y medio **nominal** de los ocupados, por región (17 áreas con `_T` = país) y sexo, separador `;` | Anual 2010-2025. Mediana nacional 2024: $611.162; media: $897.019 |
| `CL01,DF_OCU_SEXO,1.0+M...AS.csv` | INE, **Encuesta Nacional de Empleo**: ocupados por región, trimestre móvil. Se usa octubre-diciembre (período de la ESI) | Mensual 2010-01 a 2026-06 |
| `F074IPCVARZZCM.xlsx` | Banco Central, **IPC general, variación mensual** (histórico desde 1928). El libro viene mal formado: `workbook.xml` apunta a otra hoja y los datos están en `xl/worksheets/sheet1.xml` (el script lo lee con `zipfile`) | Hasta 2026 |
| `A`, `A (1)`, `M`, `CL01…all.csv` | Versiones anteriores o duplicadas de las descargas del INE (hasta 2024). **No se usan** | — |

- **Atención:** el ingreso imponible es **bruto y mensual** (SP) mientras la ESI mide ingreso **neto** del trabajo: las dos bases no son directamente comparables, por eso el dashboard las alterna con un interruptor en vez de mezclarlas. La SP no publica la mediana regional (los tramos vienen solo por AFP): la regional se estima con la nacional. El total de la SP por región (cuadro 32C, dic-2025: $1.308.020) difiere un 0,6 % del 04A (dic-2025: $1.299.840) por definiciones distintas.
- **Atención 2:** el IPC viene con un decimal, así que el índice encadenado sirve para razones entre años (deflactar a pesos de 2025), no como nivel.
- **Uso:** script 19 (descarga lo que falta del 04A) y script 18 → `sp_ingreso_imponible_nacional.csv`, `sp_ingreso_imponible_region.csv`, `sp_cotizantes_por_tramo.csv`, `ine_ingresos_ocupados.csv`, `ipc_anual.csv`, `kpi_pc_nacional.csv`, `kpi_pc_region.csv`, `kpi_pc_parametros_reforma.csv`.

---

## 3. `development sources/` (solo modo desarrollador)

### 3.1 Superintendencia de Pensiones: afiliados, cotizantes y cotizaciones

| Archivo | Contenido | Cobertura |
|---|---|---|
| `afiliados_region_edad.xls` | Afiliados (personas con cuenta individual, no pensionadas ni fallecidas) por región × tramo de edad (hasta 20, 20-25, … 60-65, 65+, S/I). 2.152 filas × 15 columnas | Mensual, dic-1993 a jun-2026 (131 cortes). Jun-2026: 12.201.632 afiliados en total; R. Metropolitana 5.516.255 |
| `cotizantes_edad.xls` | Cotizantes por tramo de edad, anual | 1985-2025. 2025: 5.974.428 en total, de los cuales 26.466 son «más de 65» |
| `cotizantes_tipo_sexo.xls` | Cotizantes por tipo (dependientes, independientes, afiliados voluntarios) × sexo, anual | 1985-2025. 2025: 5.927.500 dependientes, 45.927 independientes, 1.001 voluntarios. 3.349.729 hombres y 2.624.699 mujeres. *Sin desglose por tipo en 1985* |
| `cotizantes_region_afp.xls` | Cotizantes por región × AFP, mensual. 1.174 filas × 20 columnas | dic-1993 a jun-2026. Cuenta afiliados con pago de cotización del mes de devengamiento anterior |
| `cotizaciones_totales.xls` | Número de **cotizaciones** (no pesos) por AFP, mensual. 517 filas × 37 columnas, una columna por AFP (incluidas las desaparecidas) | ene-1984 a jul-2026. Jun-2026: 12.880.275; jul-2026: 8.133.143. Nota: cada junio sube por los trabajadores independientes que cotizan a través de la Tesorería |

- **Uso:** `afiliados_region_edad.xls` y `cotizantes_edad.xls` → script 03. `cotizantes_tipo_sexo.xls`, `cotizantes_region_afp.xls` y `cotizaciones_totales.xls` → script 17 (`cotizantes_por_tipo_sexo.csv`, `cotizantes_por_region_afp.csv`, `cotizaciones_por_afp.csv`). Las tres cuadran entre sí: dic-2025 da 5.974.428 cotizantes en `cotizantes_region`, en `cotizantes_tipo_sexo` y en `cotizantes_region_afp` (`Sistema`), y en `cotizaciones_totales` el total `SISTEMA` es igual a la suma de las AFP.

### 3.2 `c1_202607.xlsx`, `c2_202607.xlsx`, `c3_202607.xlsx`: pensiones pagadas, julio 2026
- **Productor:** Superintendencia de Pensiones, a partir de la base de Imponentes y Pensionados del IPS. Es el **sistema antiguo (ex cajas de previsión, reparto)**, no el de las AFP.
- **Contenido:** número de pensiones y monto en miles de pesos, por tipo de pensión (antigüedad, vejez, invalidez, sobrevivencia…) × sexo, según tres cortes: `c1` por ex caja (Empart, Servicio de Seguro Social, Empleados Públicos… 23 filas), `c2` por región (16 regiones) y `c3` por tramo de edad (de «–20» a «+100»).
- **Datos de referencia:** vejez, 77.953 hombres y 151.735 mujeres (los montos son 38,5 y 51,4 mil millones de pesos). Los tres archivos cuadran en el total (466.781 pensionados en todas las categorías, según el procesamiento).
- **Atención:** no incluye pensiones no previsionales (Leyes de Reparación) ni las del ISL. Desde agosto 2025 incorpora a los exonerados con abono de tiempo.
- **Uso:** script 04 → `pensiones_pagadas_por_*.csv`.

### 3.3 `casen_ingresos.parquet`: extracto CASEN 2022 con comuna (de terceros)
- **Origen:** extracto de microdatos CASEN 2022 publicado por un tercero (`bastianolea/casen_comparador_ingresos`), no el archivo oficial del Ministerio.
- **Contenido:** 202.231 filas (las mismas personas que el `.dta`) × 11 columnas: `comuna` (335 comunas distintas), `region`, `pco1`, `expc` (factor de expansión comunal), `ytotcorh`, `ytotcor`, `yoprcor`, `ypc`, `y2803`, `estrato`, `id_persona`.
- **Por qué existe:** el `.dta` oficial no trae comuna, y este extracto sí. Permite el ingreso por comuna (334/346 comunas).
- **Uso:** script 08 → `kpi_ingresos_comuna/region.csv`.

---

## 4. `archive/`: lo descartado (nada se borró)

| Carpeta | Archivos | Qué contiene | Por qué se descartó |
|---|---|---|---|
| `0_problema_general/` | 1 | `D1_Poblacion-censada-por-sexo-y-edad…xlsx`: tablas oficiales INE del Censo 2024 (población por sexo, edad quinquenal y región; 5 hojas) | Solo sirve para contrastar los microdatos |
| `1.1_cobertura_regional/duplicados/` | 2 | Dos copias de `cotizantes_region.xls` | Ver §6 (los bytes difieren, las celdas son idénticas) |
| `1.3_participacion_partes_interesadas/` | 2 | `2630681.pdf`: Diario Oficial del 10-abr-2025, decreto exento 110 (preinstalación del Administrador del FAPP). `Administrador_FAPP_estados_financieros_interinos_2026-06-30.pdf`: estados financieros del *Administrador* del FAPP (resultados, situación presupuestaria, flujos), revisados por KPMG | Contexto administrativo. Son los gastos de la entidad que gestiona el fondo, no del fondo (nota 14: sus ingresos son transferencias del FAPP) |
| `2.1_costo_real_adulto_mayor/` | 45 | **Informes trimestrales intermedios del Pilar Solidario** (10): OND-2022, EFM/AMJ/JAS-2023, EFM/AMJ/JAS-2024 y EFM/AMJ/JAS-2025 (varios nombres dicen «Marzo», «Junio» o «Diciembre»). **Informes mensuales** (10): sep-dic 2018, sep-dic 2021, mar y jun 2022 (según el nombre; llevan la hoja `datos`, solicitudes y concesiones nacional y regional). **PIB per cápita del Banco Mundial** (`NY.GDP.PCAP.CD`, US$ a precios actuales, todos los países, 1960-2025, actualizado 2026-07-13: el `.zip` y sus 3 CSV extraídos). **2 planillas DIPRES**: `416515` (Municipalidades y Gobierno General) y `416516` (empresas públicas: Codelco, ENAP…). **19 copias** | La serie mensual 2008-2025 ya sale del informe de cierre OND. El PIB en USD mezcla tipo de cambio. Las planillas DIPRES no pertenecen al Gobierno Central |
| `2.2_financiamiento_dedicado/` | 8 | 7 planillas de estados financieros (Balance, Estado de Resultados, Situación Presupuestaria, Flujo de Efectivo, Fondos no Presupuestarios, Cambio en Patrimonio) en formato DIPRES, más 1 copia | Son formularios en blanco: en el Balance de las 6 `.xlsx` revisadas solo hay 18 celdas numéricas distintas de cero y el nombre de la entidad está vacío |
| `2.3_pobreza_vejez/duplicados/` | 1 | Copia de la nota de uso CASEN | Idéntica al original |

---

## 5. `.venv/`
Entorno virtual de Python 3.14 (974 MB) con streamlit, pandas, duckdb, geopandas, plotly, openpyxl, xlrd, pytest, playwright y otros. No contiene datos del proyecto. Se recrea con `python3 -m venv "Data raw/.venv" && "Data raw/.venv/bin/pip" install -r Scripts/requirements.txt`.

---

## 6. Observaciones y puntos de atención

1. **KPI 1.3 (a cargo de Fabi, fuera del alcance de este inventario): ninguna fuente de `Data raw/` trae el monto en pesos de las cotizaciones de los trabajadores.** `cotizaciones_totales.xls` cuenta *número* de cotizaciones, no pesos. El FAPP informa sus cotizaciones (272.374 MM$ entre ago-dic 2025 y 439.587 MM$ en ene-jun 2026) y un aporte del Estado de 0 hasta 2027, pero el balance no separa quién aporta (empleador o trabajador). Es lo que anotan `config/kpis.yaml` y `docs/DATOS_ABIERTOS.md`.
2. **Duplicados:** el README dice «verificadas por hash». Es cierto para las 21 copias de Pilar Solidario, PIB, planilla DIPRES y nota CASEN, pero **no para las dos copias de `cotizantes_region.xls`**: sus bytes (y su MD5) difieren del original y entre sí, pero las celdas de ambas copias son idénticas a las del original (comparadas una a una). Es una diferencia de guardado del archivo, no de datos. El README de esta carpeta ya está corregido.
3. **Dos universos de pensiones que no se pueden sumar:** el sistema antiguo (IPS, `c1-c3`, 466.781 pensionados) frente a las AFP (afiliados/cotizantes) y el Pilar Solidario (PGU, 2,24 M de beneficiarios en dic-2025). El universo de 65+ del Censo es de ≈ 2,6 M.
4. **Denominadores de distinta época:** cotizantes a diciembre de 2025, Censo 2024 (abril de 2024) y CASEN 2022 expandida con proyecciones base Censo 2017. Esto afecta a las razones entre fuentes (KPI 1.1, 1.2, 2.3).
5. **Pobreza en la vejez:** la variable `pobreza` del `.dta` usa la metodología 2024 (20,49 % de todas las personas; 14,9 % de los 65+). La misma base trae `pobreza_2013`: 6,5 % y 2,2 %. El PDF de líneas de pobreza está calculado con la metodología 2013, así que no respalda `pobreza`: el docstring del script 14 y `docs/DATOS_ABIERTOS.md` decían que sí y ya están corregidos.
6. **Hojas de DIPRES sin uso:** los pasivos/activos del Gobierno Central y los Bonos de Reconocimiento ya están procesados (script 16), pero **no resuelven el ratio 2 del KPI 2.2**: los activos en dólares mezclan FEES, FRP y otros fondos en una línea, y el saldo del FRP no está en ningún archivo de `Data raw/`: el PDF de las Estadísticas de las Finanzas Públicas lo menciona (págs. 126 y 164 del PDF) solo en la metodología y el glosario, sin serie. Hay que sacarlo del informe trimestral del FRP de DIPRES. La nota técnica DIPRES 2025/47 modela ingresos y egresos del FAPP, pero no entrega un valor presente del déficit. Siguen sin script las demás hojas de `416514`/`416517` (ingresos tributarios, deuda, empresas públicas, etc.).
7. **Archivos sin script:** ninguno de `_external/`. `fapp/` lo leen los scripts 15 y 20; `fichas_previsionales/` y `ley_21735/`, el 15 (y el 20 la Tabla 2); `frp/`, el 20.
8. **Error corregido en el script 12:** las tablas regionales del Pilar Solidario escriben «Región del Bíobío» y «Bío-Bío» (con tilde); el script solo buscaba «biob» y descartaba la región sin avisar (15 de 16 regiones en `pgu_pbs_aps_region_trimestral.csv`). Ahora están las 16, y el informe OND-2025 ya no queda con el trimestre rotulado «Trimestre».

9. **KPI 1.2, datos del análisis «punto crítico»: nada pendiente de descargar** (revisado el 2026-10-13). El cuadro 04A tiene los 287 meses publicados (oct-2002 a ago-2026; el script 19 en modo `--seco` confirma «por descargar: 0»), el 32C y el 19B tienen cada diciembre 2010-2025 sin huecos, la ESI llega a 2025, la ENE a jun-2026 y el IPC a sep-2026. Lo que queda abierto en el KPI 1.2 no es un archivo por bajar sino datos que no existen o no están publicados: (a) **proyección regional de población base 2024**: el INE publicó solo la nacional (28-ene-2026) y anunció la regional para el segundo semestre de 2026; no pude confirmar que ya esté publicada (revisar [la página de estimaciones y proyecciones del INE](https://www.ine.gob.cl/estadisticas-por-tema/demografia-y-poblacion/estimaciones-y-proyecciones-de-poblacion)); hasta entonces sigue el reparto de tasas nacionales (`kpi_proyeccion_regional.csv`); (b) **mediana del ingreso imponible por región**: la SP no la publica; (c) **cotizantes e ingreso por comuna**: no existen en estas fuentes, la comuna hereda de su región; (d) **gasto del Pilar Solidario por región antes de 2023**: `kpi_pc_region.csv` solo tiene la cuota regional de 2023, 2024 y 2025 (208 de 256 filas vacías en `cuota_gasto_vejez`), porque solo hay informes OND de esos años en `_external/`. El informe OND 2022 sí está en `archive/2.1_costo_real_adulto_mayor/pilar_solidario_informes_intermedios/` (`…Diciembre-2022-VF_2.xlsx`) y podría agregar 2022.
10. **Redundancias en `import_KPI1.2/` (11 archivos que se pueden archivar sin perder datos):** `04A (24).xls` y `04A (25).xls` son idénticos byte a byte (diciembre 2022); seis diciembres del 19B están dos veces, con archivos idénticos byte a byte (2013: `estadisticas (2)` y `(6)`; 2014: `(1)` y `(7)`; 2015: `(8)` y `estadisticas.xls`; 2017: `19B (8)` y `(10)`; 2018: `19B (7)` y `(11)`; 2019: `19B (6)` y `(12)`); `A`, `A (1)` y `M` son descargas viejas del INE (2010-2024) sustituidas por los `CL01…csv`; y `CL01,DF_YMEDIOOCU_SEXO,1.0+all.csv` tiene los mismos valores que el `…+A....csv`. Además, el contenido no se deduce del nombre: `estadisticas (n).xls` mezcla cuadros 19B (2010-2015) y 32C, y `04A (n).xls` guarda los meses sin orden. El script 18 no depende de los nombres (lee el título), así que renombrarlos no lo rompe.
11. **Calendario de la PGU contrastado:** `docs/DISCUSION_FUENTES.md` (punto 13) lo dejaba «pendiente de contrastar con el texto de la ley». La Tabla 3 de la Nota Técnica de la Subsecretaría (`_external/ley_21735/`, pág. 28) confirma las tres fechas que usa el script 18 (82+ el 1-sep-2025, 75+ el 1-sep-2026, 65+ el 1-sep-2027, monto $ 250.000 más reajustes). Es una fuente oficial secundaria («elaboración propia en base a la Ley»), no el texto de la ley.
12. **Insumos que no están como archivo en `Data raw/`:** el script 21 usa el valor de la UTM 2025 y el dólar observado del SII (páginas web leídas el 2026-10-13) y cifras transcritas a mano de PDF. Las URLs están en el docstring, pero si el SII cambia la página no hay copia. Conviene guardar las dos tablas del SII (por ejemplo en `_external/sii/`).
