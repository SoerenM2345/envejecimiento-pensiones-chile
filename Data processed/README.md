# Data processed — Desafío 1: Envejecimiento demográfico y sostenibilidad de las pensiones

Salidas generadas por los scripts en `../Scripts/` (ejecutar en orden 00→05,
con el venv de `../Data raw/.venv`). Todo se genera desde los archivos
originales en `../Data raw/` — esta carpeta se puede borrar y reconstruir.

## Pipeline

| Script | Qué hace |
|---|---|
| `00_build_lookup.py` | Crea `region_comuna_lookup.csv` (346 comunas, nombres con tildes) desde una fuente pública de códigos DPA oficiales, cruzada contra `codigos_territoriales.csv`. |
| `01_procesar_censo.py` | DuckDB sobre `personas_censo2024.csv` (18.480.432 personas). Agregaciones y tabla de indicadores de envejecimiento por comuna/región. |
| `02_procesar_proyecciones.py` | Tidy del Excel de proyecciones INE 1992-2070 (nivel país). |
| `03_procesar_cotizantes_afiliados.py` | Tidy de las series históricas de Superintendencia de Pensiones (afiliados/cotizantes). |
| `04_procesar_pensiones_pagadas.py` | Tidy de los informes c1/c2/c3 (pago de pensiones, corte julio 2026). |
| `05_graficos_exploratorios.py` | Gráficos de validación (no es el dashboard final) en `../Outputs/figures/`. |

## Archivos y su uso

### Censo 2024
- **`indicadores_comuna.csv`** (346 filas) / **`indicadores_region.csv`** (16 filas) — la tabla principal para el análisis: `pob_total`, `pob_0_14`, `pob_15_64`, `pob_65_mas`, `pob_80_mas`, `edad_mediana`, `pct_65_mas`, `pct_0_14`, `pct_80_mas`, `indice_envejecimiento` (65+/0-14 ×100), `indice_dependencia_total`, `indice_dependencia_vejez` (65+/15-64 ×100), `pct_urbano`.
- **`censo_comuna_edad_sexo.csv`** / **`censo_region_edad_sexo.csv`** — población por edad quinquenal x sexo x área (urbano/rural), para pirámides demográficas por comuna/región.
- **`censo_pais_edad_simple.csv`** — pirámide nacional por edad simple (0-85+) x sexo.
- **`region_comuna_lookup.csv`** — cruce comuna_id/region_id ↔ nombres oficiales (con tildes).

**Cuidado con la edad enmascarada:** en 51 comunas pequeñas/aisladas (`comuna_bajo_umbral=1` en el CSV original — islas como Isla de Pascua y Juan Fernández, comunas rurales de Aysén, Magallanes, Los Ríos, etc.) el INE reemplaza `edad` (edad simple) por `-66` por control de revelación estadística (~151k personas, 0.82% del país). `edad_quinquenal` (tramos de 5 años) SÍ está disponible al 100%. Como los quiebres 0-14/15-64/65+/80+ caen justo en límites de quinquenio, `indicadores_comuna.csv` usa `edad_quinquenal` y logra cobertura 346/346 sin pérdida de precisión en esos indicadores. Solo la mediana de edad de esas 51 comunas es aproximada (columna `edad_mediana_es_aproximada=True`), y solo `censo_pais_edad_simple.csv` (pirámide de edad *simple*) excluye a esas ~151k personas.

**Validación:** `pct_65_mas` nacional (suma ponderada de `indicadores_region.csv`) = **13.97%**, coincide con el ~14% reportado por el INE y con el 13.98% que da independientemente `proyeccion_envejecimiento_pais.csv` para 2024.

### Proyecciones de población (INE)
- **`proyeccion_envejecimiento_pais.csv`** — serie 1992-2070 (anual, corte 30-jun) con los mismos indicadores que las tablas de censo, a nivel país. Solo existe a nivel nacional (el Excel fuente no trae desagregación regional/comunal).
- **`proyeccion_pais_edad_sexo.csv`** — pirámide proyectada por año x edad simple x sexo, para animar/comparar pirámides (ej. 2024 vs 2050).

### Pensiones — Superintendencia de Pensiones
Dos fuentes **distintas y no comparables directamente**:

1. **Afiliados/cotizantes (sistema de AFP actual)**:
   - `cotizantes_por_edad.csv`, `cotizantes_por_region.csv` — anual, 1985-2025.
   - `afiliados_por_region_edad.csv` — mensual, 1993-2026 (dic.1993 a jun.2026).
   - "Afiliado" = tiene cuenta individual (stock). "Cotizante" = cotizó ese mes/año (flujo, subconjunto activo). Incluyen filas agregadas `Total`/`Sin Información` — filtrar si se sumariza por región/edad para evitar doble conteo.
   - Los rótulos de región cambian de formato entre archivos y a lo largo del tiempo (`"V"`, `"R. Metrop."`, `"V Valparíaso"`, `"XIII Metropolitana de Santiago"`...); ya vienen normalizados a `region_id` (1-16, mismo esquema que el Censo).
   - Regiones nuevas (Los Ríos=XIV y Arica y Parinacota=XV desde ~2007-2010, Ñuble=XVI desde 2018) no existen antes de su creación: ausencia esperada, no error.

2. **Pago de pensiones (sistema antiguo IPS/reparto, corte julio 2026)**:
   - `pensiones_pagadas_por_region.csv`, `pensiones_pagadas_por_tramo_edad.csv`, `pensiones_pagadas_por_ex_caja.csv` — formato largo: categoría x `tipo_pension` (Antigüedad/Vejez/Invalidez/Ley Especial/Sobrevivencia) x `sexo` x `numero_pensionados` x `monto_miles_pesos`.
   - **Importante:** los "ex caja" (Empart, Servicio Seguro Social, Empleados Públicos, etc.) son las cajas de previsión del sistema de reparto **anterior a la reforma de 1981**, hoy administradas por el IPS. Este universo (**466.781 pensionados** a julio 2026, validado de forma cruzada e idéntica en los 3 archivos) es mucho menor que la población de 65+ del Censo (2,56M) — **no equivale** a "todos los adultos mayores con pensión" (no incluye AFP, PGU, etc.). Está fuertemente concentrado en edades 75-90 (cohorte que se extingue), lo cual es en sí mismo relevante para la narrativa de sostenibilidad del sistema antiguo.
   - Cada archivo trae una fila `region_nombre`/`tramo_edad`/`ex_caja` = `"Total"` (agregado) — no sumar junto con el resto de las filas.

### Mapas (`geo/`)
- `geo/comunas_chile.geojson` (345/346 comunas, Antártica sin geometría publicada) y `geo/regiones_chile.geojson` (16/16), geometría simplificada (tolerancia 0.001°) desde `pachadotdev/chilemapas`, ya con todos los indicadores de `indicadores_comuna.csv`/`indicadores_region.csv` embebidos como propiedades. Generados por `06_construir_mapas.py`.

### Ingresos (CASEN 2022) — `07_kpis_pension_salud.py` y `08_ingresos_casen.py`
- **`kpi_ingresos_comuna.csv`** / **`kpi_ingresos_region.csv`** — ingreso per cápita y de hogar, ponderados por el factor de expansión CASEN (`expc`). 334/346 comunas (12 comunas pequeñas/aisladas no están en la muestra — ver columna `n_muestra` para juzgar precisión, mediana ~298 casos/comuna).
- **`kpi_ingreso_envejecimiento.csv`** — cruce comuna x ingreso x `pct_65_mas`/`pct_urbano` para el análisis socioeconómico.
- CASEN es una **encuesta muestral**, no un censo — es la única fuente de ingresos disponible (el Censo es censo de derecho, no pregunta ingresos). Microdatos vía `bastianolea/casen_comparador_ingresos` (GitHub), originalmente del Ministerio de Desarrollo Social.

### KPIs de presión previsional y salud (`07_kpis_pension_salud.py`)
- **`kpi_presion_previsional_region.csv`** — cobertura previsional (cotizantes/pob. 15-64) y razón de soporte (cotizantes por adulto mayor) por región. Usa cotizantes AFP 2025 + Censo 2024, **no** los pensionados del sistema antiguo (ver más abajo).
- **`kpi_presion_previsional_edad.csv`** — contexto histórico: pensionados del sistema antiguo (IPS) vs. cotizantes AFP por tramo de edad. Lectura con cuidado (ver caveat de "dos sistemas" arriba).
- **`kpi_proyeccion_regional.csv`** — proyección 2024→2035→2050 de población por región, método de **reparto de tasas nacionales** (shift-share): se aplica a cada región la tasa de crecimiento que el INE proyecta a nivel país por grupo etario. Es una aproximación explícita, no una proyección oficial INE por región (el INE aún no la publica en base 2024).
- **`kpi_indice_demanda_salud_region.csv`** — índice compuesto (suma de z-scores de % 65+, % 80+ y velocidad de envejecimiento 2024→2035) como proxy de demanda potencial de salud geriátrica. No usa datos DEIS de uso real de servicios (no disponibles).
- **`kpi_urbanizacion_envejecimiento.csv`** — comuna x `pct_urbano` x `pct_65_mas` (346 comunas, Censo únicamente).

Definiciones formales, fórmulas e interpretación de cada KPI: `../config/kpis.yaml`.

## Próximos pasos sugeridos
- Reemplazar la proyección regional por reparto de tasas cuando el INE publique proyecciones sub-nacionales en base 2024.
- Cruzar con DEIS/MINSAL (egresos hospitalarios, defunciones) cuando se consiga ese archivo, para pasar del índice de demanda de salud (proxy demográfico) a uso real de servicios.
- Dashboard interactivo: `../Dashboards/` (Streamlit, `streamlit run Inicio.py`) — ya cubre mapas, pirámides, presión previsional/salud, socioeconómico y propuestas de política. `Outputs/figures/` son solo 3 PNGs de validación previos al dashboard.
