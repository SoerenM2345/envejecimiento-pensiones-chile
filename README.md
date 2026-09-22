# Envejecimiento demográfico y sostenibilidad de las pensiones

ICS100 — Herramientas de Análisis y Visualización de Datos · Proyecto de cierre, Desafío 1.

## Estructura

```
Proyecto/
├── Data raw/           # fuentes originales sin tocar (censo 2,4GB, xlsx/xls de INE y Superintendencia de Pensiones)
│   └── .venv/           # entorno Python del proyecto (ver Scripts/requirements.txt)
├── Data processed/      # todas las tablas limpias/agregadas + geo/ (GeoJSON) — ver README.md ahí
├── config/
│   └── kpis.yaml         # catálogo de KPIs: fórmula, fuente, grano, archivo, track del enunciado
├── Scripts/              # pipeline numerado 00→08, reproducible de punta a punta (ver abajo)
├── Dashboards/           # app Streamlit multipágina (explorador + dashboard territorial)
├── Outputs/figures/      # gráficos exploratorios estáticos (validación, no el dashboard final)
└── docs/                 # borradores del informe final (Partes 1, 2, 4 del curso) — pendiente
```

## Archivos que NO están en GitHub

Por el límite de 100 MB de GitHub, estos archivos se excluyen (`.gitignore`) y hay que copiarlos a mano:

- `Data raw/personas_censo2024.csv` (2,3 GB) — microdatos Censo 2024, INE. Solo hace falta para re-correr `01_procesar_censo.py`; el dashboard funciona sin él (usa `Data processed/`).
- `.venv/` — se recrea con `python3 -m venv "Data raw/.venv" && "Data raw/.venv/bin/pip" install -r Scripts/requirements.txt`.
- Archivos DEIS (egresos/defunciones, `.zip`) — ver `docs/PLAN_KPIs.md` §0.

## Cómo correr el pipeline

```bash
cd "Data raw" && source .venv/bin/activate   # el venv ya tiene todo instalado

python3 ../Scripts/00_build_lookup.py                 # tabla región/comuna con tildes
python3 ../Scripts/01_procesar_censo.py                # censo -> indicadores por comuna/región (DuckDB, ~20s)
python3 ../Scripts/02_procesar_proyecciones.py         # proyecciones INE nacionales 1992-2070
python3 ../Scripts/03_procesar_cotizantes_afiliados.py # series Superintendencia de Pensiones
python3 ../Scripts/04_procesar_pensiones_pagadas.py    # pago de pensiones jul-2026 (c1/c2/c3)
python3 ../Scripts/05_graficos_exploratorios.py        # PNGs de validación
python3 ../Scripts/06_construir_mapas.py               # geojson comuna/región + indicadores
python3 ../Scripts/07_kpis_pension_salud.py            # cobertura previsional, proyección regional, índice de salud
python3 ../Scripts/08_ingresos_casen.py                # ingresos CASEN 2022 (descarga una vez a Data raw/_external/)
```

Todo se regenera desde `Data raw/` — `Data processed/` se puede borrar y reconstruir corriendo lo anterior en orden.

## Cómo correr el dashboard

```bash
cd Dashboards && source "../Data raw/.venv/bin/activate"
streamlit run Inicio.py
```

Abre `http://localhost:8501`. Páginas:

| Página | Qué responde |
|---|---|
| 🔍 Explorador de datos | "back end": cualquier archivo de `Data processed/`, con filtros dinámicos, cruce de dos fuentes y agrupar/sumar por lo que sea |
| 🗺️ Mapas | *Mapas territoriales del envejecimiento* |
| 📊 Pirámides | *Construir pirámides demográficas y su evolución* |
| 💰 Pensiones y salud | *Proyectar la presión sobre salud y pensiones* |
| 🏙️ Socioeconómico | *Relacionar con variables socioeconómicas (ingresos, urbanización)* |
| 📋 Políticas | *Propuestas de políticas de envejecimiento activo* (segmentación basada en datos, no genérica) |

La página de Inicio también responde *Identificar regiones y comunas con mayor envejecimiento* (ranking) y sirve de *Dashboard territorial* general.

## Estado por track del enunciado

| Track | Estado |
|---|---|
| Identificar regiones/comunas con mayor envejecimiento | ✅ completo — `indicadores_comuna.csv`/`indicadores_region.csv`, ranking en Inicio |
| Construir pirámides demográficas y su evolución | ✅ completo — nacional 1992-2070 + región/comuna 2024 |
| Mapas territoriales | ✅ completo (345/346 comunas; falta geometría de Antártica) |
| Variables socioeconómicas (ingresos, urbanización) | 🟡 parcial — urbanización 100% (Censo); ingreso vía CASEN 2022 (334/346 comunas, encuesta muestral, no censo) |
| Presión sobre salud y pensiones | 🟡 parcial — cobertura/razón de soporte previsional real; proyección regional y demanda de salud son **aproximaciones** (INE no publica proyección subnacional base 2024; no hay datos DEIS de uso real de salud) |
| Dashboard territorial | ✅ completo (Streamlit, 6 páginas) |
| Propuestas de envejecimiento activo | ✅ completo — 5 segmentos de comunas + propuestas regionales, todo trazable a los datos |

Detalle metodológico completo, fórmulas y limitaciones de cada indicador: `config/kpis.yaml` y `Data processed/README.md`.
