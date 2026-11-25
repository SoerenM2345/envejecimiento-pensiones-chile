# Presentacion_Graficos.ipynb: léame

Proyecto: *Envejecimiento demográfico y sostenibilidad de las pensiones* (Herramientas de análisis y visualización de datos).
Autores: Sören Lange-Klapproth y Fabian Zimmermann.

## Qué es
Un solo cuaderno que reproduce **todos los gráficos con datos** de la presentación final: diapositivas 3, 7, 8, 9, 10, 18, 19, 20, 21, 22, 23, 24, 25 y 26.
El código es copia del código del proyecto (scripts de limpieza `Scripts/01-35`, constructores de gráficos del dashboard y el estilo de diapositiva del script 34). Las diapositivas de texto, tarjetas y diagramas (1, 2, 4-6, 11-17, 27-34) están hechas en PowerPoint y no tienen código.

El archivo **ya trae guardados los resultados** de ejecutar todas las celdas de arriba abajo: se pueden ver los gráficos sin ejecutar nada.

## Estructura
| Sección | Contenido |
|---|---|
| 0 | Librerías, rutas e interruptor `EJECUTAR_LIMPIEZA` (por defecto `False`) |
| 1 | Limpieza de datos: scripts 01-35 que alimentan los gráficos, cada uno en una función `paso_NN()` |
| 2-4 | Paleta, motor del punto crítico, constructores de gráficos y estilo de diapositiva |
| 5 | Datos de cada gráfico (las mismas llamadas que hacen las páginas del dashboard) |
| 6 | Un gráfico por diapositiva |
| 7 | Verificación de las cifras de la presentación (punto crítico 2038, cobertura 46,5 %, 2,27 cotizantes por persona de 65+, carga 10,1 % en 2038, máximo de la población de 15-64 en 2034) |

## Qué gráfico corresponde a cada diapositiva
| Diapositiva | Gráfico | Id de la figura |
|---|---|---|
| 3 | Pirámide de Chile y Alemania 2024 (tramos 0-14 / 15-64 / 65+) | Script 11 |
| 7 | % de personas de 65+ 1992-2070 · máximo de la población de 15-64 en 2034 | P.3 · P.4 |
| 8 | Cotizantes por persona de 65+, 2010-2070 | 1.2.4 |
| 9 | Costo del Pilar Solidario frente a la capacidad (10 % del sueldo); punto crítico 2038 | 1.2.7 |
| 10 | Mapa de cobertura por región y ranking de las 16 regiones | 1.1/mapa y 1.1/barras_region |
| 18 | Cobertura 2002-2024: región más alta, Chile y región más baja | 1.1.16 |
| 19 | Cobertura 2007-2024: Chile y las regiones que menos avanzaron | N.5b-v2 |
| 19-20 | Tabla de cambio 2007-2024 con cambio de puestos | Script 36 |
| 20 | Puntos ganados desde 2007 menos los de Chile, con rango | 1.1.9 |
| 21 | Mapa de las 7 regiones críticas y desglose de los 224 mil cotizantes que faltan | 1.1.1 · N.5d |
| 22 | De cada 100 personas de 15-64 años, cuántas cotizan | 1.1.4 |
| 23 | Descomposición de la diferencia con Chile en 4 paneles | 1.1.25 |
| 24 | Seis escenarios del punto crítico | 1.2.10 |
| 25 | Cascada de la carga 2024-2038 (6,7 % a 10,1 %) | 1.2.9 |
| 26 | Qué impulsa el costo del Pilar Solidario 2016-2050 | 2.1/drivers |

## Qué NO está incluido en este envío
El `.ipynb` es el único archivo del envío (más este léame). Para **volver a ejecutarlo** hay que tener, junto al cuaderno, las carpetas `Data processed/` y `config/` del repositorio del proyecto:

**https://github.com/SoerenM2345/envejecimiento-pensiones-chile** (rama `main`)

Lo más simple: `git clone https://github.com/SoerenM2345/envejecimiento-pensiones-chile.git`, y abrir `Presentacion_Graficos.ipynb` desde la carpeta clonada (ahí ya están todos los archivos de esta lista, salvo los datos crudos pesados). Detalle de lo que usa el cuaderno:

**1. Datos limpios** (`Data processed/`, unos 6 MB en total):

| Archivo | Lo produce el paso de limpieza |
|---|---|
| `proyeccion_envejecimiento_pais.csv` | 02 |
| `censo_pais_edad_simple.csv`, `indicadores_region.csv` | 01 |
| `alemania_piramide_edad_simple_2024.csv` | 10 |
| `kpi_presion_previsional_region.csv` | 07 |
| `kpi_pc_nacional.csv`, `kpi_pc_parametros_reforma.csv` | 18 |
| `pgu_pbs_aps_nacional_anual.csv` | 12 |
| `gasto_proteccion_social.csv`, `macro_pib_anual.csv` | 13 |
| `kpi_cobertura_tendencia.csv`, `kpi_cobertura_regiones.csv` | 24 |
| `kpi_cobertura_descomposicion.csv`, `kpi_pc_escenarios_fijos.csv` | 25 |
| `kpi_cobertura_composicion.csv` | 29 |
| `kpi_seleccion_dos_preguntas.csv` | 35 |
| `geo/regiones_chile.geojson` (5,3 MB) | 06 |

**2. Configuración:** `config/escenarios.yaml` (supuestos del punto crítico: tope de 10 %, sueldo real +1 %, PGU de $250.000).

La estructura debe ser: `Presentacion_Graficos.ipynb`, `Data processed/` y `config/` en la misma carpeta. El cuaderno busca hacia arriba una carpeta llamada `Data processed`.

**3. Datos crudos** (`Data raw/`, solo con `EJECUTAR_LIMPIEZA = True`; unos 3,9 GB en total; el Censo de 2,3 GB y CASEN no están en git):
- Censo 2024, microdatos de personas (`personas_censo2024.csv`, 2,3 GB, paso 01; en git no está).
- INE: proyecciones de población 1992-2070 base 2024 (paso 02) y base 2017 por comuna (paso 24); encuesta de empleo regional (paso 25).
- Superintendencia de Pensiones: cotizantes y afiliados por región y edad (pasos 03 y 17) e ingreso imponible (paso 18).
- Destatis: población de Alemania por edad (paso 10).
- Pilar Solidario: PGU, PBS y APS (paso 12) · PIB y gasto en protección social, DIPRES y Banco Central (paso 13).
- Paso 25 carga además `Scripts/24_cobertura_tendencia_causas.py` como archivo.

El repositorio no incluye el Censo de 2,3 GB ni CASEN; con `Data raw/` incompleta, si falta un archivo crudo, el paso se salta con un aviso y se conservan los CSV de `Data processed/`. En una prueba sin el Censo se ejecutaron los pasos que no lo necesitan (02, 03, 06, 07, 10, 12, 13, 17, 18, 26, 31, 35) y reprodujeron `Data processed/` idéntico; los pasos 01, 24, 25 y 29 se saltaron por falta del Censo.

**4. Entorno:** Python 3.14 con `pandas`, `numpy`, `plotly 7.1`, `kaleido 1.5` (con Chrome, para guardar PNG), `matplotlib`, `pillow`, `pyyaml`, `duckdb`, `geopandas`, `openpyxl` y `xlrd` (estas últimas solo para la limpieza), más `ipykernel` para abrir el cuaderno. Los mapas descargan el mapa base de internet. Letras: Helvetica Neue (macOS) para el pie de fuente de los PNG y Calibri (de Microsoft Office) para la tabla de las diapositivas 19-20; si faltan, el pie usa otra letra y la tabla no se genera.

## Cosas a tener en cuenta
- **Cifras de la presentación:** la sección 7 las compara con los datos y todas coinciden.
- **Biobío:** las figuras de regiones críticas de las diapositivas usan 7 regiones (Biobío sale por decisión del equipo); el dashboard y la regla de selección siguen con 8.
- **Diapositiva 3:** el gráfico del cuaderno trae las líneas rojas de los tramos de edad; los porcentajes por tramo (Chile 17,73 / 68,30 / 13,97 %; Alemania 13,91 / 63,37 / 22,72 %) se imprimen en la salida de la celda y en la presentación están en recuadros.
- **Diferencias con las imágenes de la presentación:** son las mismas figuras, con diferencias de unos pocos píxeles en el margen inferior, porque aquí cada gráfico se construye directo y no se captura desde el dashboard.
- **Resultados guardados:** los gráficos guardados en este archivo son imágenes (PNG) de cada figura. Al ejecutar el cuaderno en Jupyter se vuelven a calcular y, además, se guardan los PNG de alta resolución en `Outputs/figuras_notebook/`.
