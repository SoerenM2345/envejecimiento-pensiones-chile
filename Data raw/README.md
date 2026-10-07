# Data raw: qué hay y para qué sirve

Reorganizado el 2026-10-07. Cada archivo está en una de tres zonas.

## 1. Fuentes de los 6 KPIs y del análisis del problema (se quedan donde las leen los scripts)

| Archivo | Uso | Script |
|---|---|---|
| `personas_censo2024.csv` (2,5 GB, no versionado) | Censo 2024: estructura etaria, pirámides, población 15-64 y 65+ | 01 |
| `estimaciones-y-proyecciones-de-población-1992-2070_base-2024_base-de-datos.xlsx` | Proyecciones INE (14% → 43%, pico de población activa) | 02 |
| `cotizantes_region.xls` | KPI 1.1 y 1.2 (cotizantes por región) | 03 |
| `_external/16_bevoelkerungsvorausberechnung_daten.csv` | Pirámide de Alemania (Destatis) | 10 |
| `_external/pilar_solidario/` | Informes de cierre (OND) 2023, 2024 y 2025: PGU/PBS/APS. KPI 2.1 y 2.2 | 12 |
| `_external/dipres/` | Estadísticas de las Finanzas Públicas 2016-2025 (PDF y Excel, gasto funcional "7102 Edad avanzada"), pasivos y activos, nota técnica FAPP. KPI 2.1, 2.2, 1.3 | 13 |
| `_external/macro/CCNN2018_P0_V2.xlsx` | PIB anual a precios corrientes y encadenado 2013-2025 (Banco Central). KPI 2.1, 2.2 | 13 |
| `_external/fapp/` | Estados financieros del FAPP al 31-dic-2025 y al 30-jun-2026. KPI 1.3, 2.2 | por hacer |
| `_external/casen2022/` | CASEN 2022 completa (`casen_2022.dta`, 501 MB, no versionado), libro de códigos, nota de uso y líneas de pobreza. KPI 2.3 | 14 |

## 2. `development sources/`: usados por el modo desarrollador, no por los 6 KPIs

`afiliados_region_edad.xls`, `cotizantes_edad.xls` (script 03), `c1/c2/c3_202607.xlsx` (script 04, solo sistema antiguo IPS), `casen_ingresos.parquet` (script 08, extracto CASEN de terceros), y tres archivos de la Superintendencia sin script aún: `cotizantes_region_afp.xls`, `cotizantes_tipo_sexo.xls`, `cotizaciones_totales.xls`.

## 3. `archive/<KPI>/`: no hacen falta (nada se borró)

| Carpeta | Contenido | Por qué |
|---|---|---|
| `0_problema_general/` | `D1_Poblacion-censada…xlsx` | Tablas oficiales INE; solo servían de contraste de los microdatos |
| `1.1_cobertura_regional/duplicados/` | 2 copias de `cotizantes_region.xls` | Contenido idéntico al original |
| `1.3_participacion_partes_interesadas/` | Decreto del Diario Oficial (preinstalación del FAPP), estados financieros del Administrador del FAPP | Contexto administrativo, sin cifras de financiamiento |
| `2.1_costo_real_adulto_mayor/` | Informes Pilar Solidario intermedios (trimestres que no son el cierre), informes mensuales de solicitudes, planillas DIPRES de gobierno general y empresas públicas, PIB per cápita del Banco Mundial en USD | La serie mensual 2008-2025 ya sale del informe de cierre; el PIB en USD mezcla tipo de cambio |
| `2.2_financiamiento_dedicado/` | 8 planillas DIPRES de estados financieros | Son plantillas contables sin montos |
| `2.3_pobreza_vejez/duplicados/` | Copia de la nota de uso CASEN | Idéntica |
| `…/duplicados/` (varias) | Copias idénticas (verificadas por hash) | Descargas repetidas |

Los nombres originales de las descargas se conservan, salvo los PDF del FAPP (`gcs-file*.pdf`), renombrados para que se entienda qué son.
