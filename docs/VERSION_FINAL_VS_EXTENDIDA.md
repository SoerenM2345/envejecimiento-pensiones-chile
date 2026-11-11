# Versión final y versión extendida del dashboard (2026-11-10)

El dashboard tiene dos versiones de las mismas cinco páginas (Resumen, Problema, Objetivo 1, Objetivo 2, Fuentes), con un interruptor «Versión extendida» en el menú lateral (o `?mode=extended`; se puede combinar con `?mode=dev`).

- **Final** (por defecto, `Dashboards/final_pages/`): solo lo esencial. Es la que se presenta.
- **Extendida** (`Dashboards/extended_pages/`): copia completa del estado anterior al recorte. Nada se perdió: lo que la final dejó fuera vive solo aquí.

Lo recortado se **borró del código de la final** (funciones, expanders, importaciones); el código compartido (`components/`, `utils.py`) no cambió. Las pruebas de contenido corren contra la extendida; `tests/test_dashboard_smoke.py::test_la_version_final_deja_fuera_lo_que_solo_esta_en_la_extendida` fija qué está en cada una.

## Qué queda solo en la extendida

| Dónde | Qué | Por qué se sacó de la final |
|---|---|---|
| KPI 1.1 | «¿Por qué cotizan más en unas regiones?» (dispersión con selector de variable) | Repite, con una sola variable, lo que ya muestra la sección 3 (todas las características) |
| KPI 1.1 | 3b «¿Cambia algo por sexo? Un descarte» (informalidad por sexo, INE `INF_TOI`) | Es un descarte: no agrega causa |
| KPI 1.1 | Tabla «Exploración: todos los factores probados» | Detalle estadístico; la final muestra solo los factores elegidos |
| KPI 1.1 | Contraste con el estudio de la Asociación de AFP | Validación del método, no resultado |
| KPI 1.1 | Prueba de la regla de asignación regional y pendularidad | Sensibilidad; la final lo dice en una nota |
| KPI 1.2 | Tabla de sensibilidad del punto crítico | La cubren los seis escenarios fijos |
| KPI 1.2 | Cifras de todas las comunas de la región elegida | Aproximación heredada de la región |
| KPI 2.1 | Pestañas «Qué lo explica», «Por beneficiario» y «Proyección 2050» | Las cubren «¿Por qué suben los costos?» y el KPI 2.2 |
| KPI 2.2 | Pestaña «FAPP hoy» (primer semestre de 2026) | Dato puntual fuera del foco del costo nacional |
| Objetivo 2 | «Costos y economía de las administradoras» (5 gráficos) | Es el negocio de las administradoras, no el costo del Estado |

## Qué se revisó contra las pautas de la clase

Auditoría de todos los gráficos de la final (títulos con mensaje y sin siglas, máximo 4 líneas, ejes desde 0, una serie de color por barra, daltonismo): un hallazgo corregido (el título de la descomposición del costo decía «cobertura» en vez de «alcance»). Pendiente, solo en la extendida: el gráfico de costos por administradora tiene 8 líneas (la regla dice 4).
