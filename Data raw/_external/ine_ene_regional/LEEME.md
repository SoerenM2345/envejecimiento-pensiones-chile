# `ine_ene_regional/`: Encuesta Nacional de Empleo (INE), exportaciones del explorador de datos

Descargadas a mano el 2026-11-09 (carpeta de paso `import razones/`, ya ordenada aquí). Los `.xls` son **XML de Excel 2003** («MyOECD export»), no Excel binario. Cada uno trae un título («Dataset: …»), filtros fijos (indicador, sexo, rama…), una columna por región (Total país + 16) y una fila por trimestre móvil; los números van en miles de personas (conteos) o en %. Proyecciones de población base 2017, 2010 a mar-may 2024 (informalidad desde jul-sep 2017).

El script `Scripts/25_explorar_causas.py` reconoce cada archivo por su contenido, no por el nombre. Prefijos del nombre nuevo: `ene_regional_*` = una columna por región y ambos sexos (se usan); `ene_regional_solo_total_*` = por región pero con el filtro de rama / categoría en «Total» (no sirven); `ene_pais_*` = solo país, por edad, nivel educacional o rama (no se usan).

Faltan, para ser útiles: los mismos conjuntos con **todas** las ramas y categorías, por sexo, y la ENE desde junio de 2024 (base 2024). Instrucciones en `docs/EXPLORACION_COBERTURA.md`, sección 7.

| Nombre actual | Nombre original (código del explorador) |
|---|---|
| `ene_pais_desocupados_por_nivel_educacional.xls` | `40024726-39eb-42a7-8f9b-b5bf2a70ff20.xls` |
| `ene_pais_desocupados_por_tramo_etario.xls` | `ce951244-2605-4613-a240-7daedda515dc.xls` |
| `ene_pais_ocupados_por_nivel_educacional.xls` | `fb78b1e4-dcf2-45d1-a4ca-45ac003fcd31.xls` |
| `ene_pais_ocupados_por_tramo_etario.xls` | `7edad916-9558-4bbb-80be-60e5560dd4a2.xls` |
| `ene_pais_ocupados_segun_categoria_ocupacional_por_tramo_etario.xls` | `4ebb7f21-a88a-41b7-af4a-c5cfbc319b05.xls` |
| `ene_pais_ocupados_segun_grupo_ocupacional_ciuo_88_por_tramo_etario.xls` | `fc0a0281-e6cf-4b1b-b601-cccff9dacb97.xls` |
| `ene_pais_ocupados_segun_rama_de_actividad_economica_ciiu_por_tramo_etario.xls` | `8ef183a5-02a9-4616-8394-a07dc788e3ee.xls` |
| `ene_pais_tasa_de_ocupacion_informal_por_rama_economica.xls` | `bc7a206d-34c8-43b3-8105-7541b4de449f.xls` |
| `ene_pais_tasa_de_tiempo_parcial_involuntario_por_nivel_educacional.xls` | `9850bf64-cafd-498a-b32d-381163e6c55b.xls` |
| `ene_pais_tasa_de_tiempo_parcial_involuntario_por_tramo_etario.xls` | `66d710fc-3a2b-4858-83d2-3a8ce954471b.xls` |
| `ene_regional_desocupados.xls` | `617132b0-42c0-459b-8fdc-254e73dd15c4.xls` |
| `ene_regional_informales.xls` | `46bc24b8-81f5-4040-b021-bc7c1a03d62a.xls` |
| `ene_regional_ocupados.xls` | `e8f06cb5-78b6-4408-8375-6438fbb5f4ff.xls` |
| `ene_regional_solo_total_ocupados_segun_categoria_ocupacional.xls` | `50f18e5a-37c6-49e6-a0d1-c8a9ed60f773.xls` |
| `ene_regional_solo_total_ocupados_segun_grupo_ocupacional_ciuo_88.xls` | `023fc6b1-2d1c-4084-908e-42596a7b34d8.xls` |
| `ene_regional_solo_total_ocupados_segun_rama_de_actividad_economica_ciiu.xls` | `c1d74d5b-371f-423d-be30-33b4791c8d2e.xls` |
| `ene_regional_tasa_informal.xls` | `cf58d0d2-59e7-4384-ab4b-11105c1ec9ae.xls` |
| `ene_regional_tasa_informal_copia_en_ingles.xls` | `f3a525ed-524f-4f30-a0b0-c6efeff5f3ce.xls` |
| `ene_regional_tasa_informal_sin_agro.xls` | `f1981bf1-099d-410e-9518-bd61c4f3bfbe.xls` |
| `ene_regional_tasa_parcial_involuntario.xls` | `a9a08433-090d-4307-ba36-ffbd15909d67.xls` |
| `ene_regional_tasa_sector_informal.xls` | `0cb83c21-3c7c-4c45-ba12-ba2b708867a4.xls` |

## Tasa de informalidad por sexo (CSV, no XML)

`ene_regional_tasa_informal_por_sexo.csv` (nombre original `INF_TOI_10112026141536651.csv`, descargado el 2026-11-10): tasa de ocupación informal por trimestre móvil, región y sexo (total, hombres, mujeres). Trae dos series: `INF_TOI_P2017` (proyecciones base 2017, jul-sep 2017 a mar-may 2024, la misma de `ene_regional_tasa_informal.xls`: coincide con `ene_region_anual.csv` hasta 5×10⁻⁵ puntos) e `INF_TOI` (base 2002, hasta nov-ene 2019, obsoleta). Solo se usa la primera, en `Scripts/28_informalidad_por_sexo.py`; el script 25 no la lee (solo lee `*.xls`).
