# `sp_costos_administracion/`: Costos de administración de los Fondos de Pensiones (Superintendencia de Pensiones)

Informe anual que la Superintendencia publica por el art. 28 del DL 3.500: ingresos (comisiones, encaje, otros), gastos (personal, operación, depreciación, otros), ganancia y rentabilidad de cada AFP y del sistema. Cifras en millones de pesos de diciembre de cada año (FECU / estados financieros consolidados).

Descargados el 2026-11-10 de la página «Gestión de las AFP → Costos de administración» de spensiones.cl. Nombre original → nombre aquí:

| Año | Archivo original (https://www.spensiones.cl/portal/institucional/594/…) | Archivo aquí |
|---|---|---|
| 2016 | `articles-11295_recurso_1.pdf` | `costos_administracion_2016.pdf` |
| 2017 | `articles-13349_recurso_1.pdf` | `costos_administracion_2017.pdf` |
| 2018 | `articles-13777_recurso_1.pdf` | `costos_administracion_2018.pdf` |
| 2019 | `articles-14025_recurso_1.pdf` | `costos_administracion_2019.pdf` |
| 2020 | `articles-14650_recurso_1.pdf` | `costos_administracion_2020.pdf` |
| 2021 | `articles-15368_recurso_1.pdf` | `costos_administracion_2021.pdf` |
| 2022 | `articles-15621_recurso_1.pdf` | `costos_administracion_2022.pdf` |
| 2023 | `articles-16059_recurso_1.pdf` | `costos_administracion_2023.pdf` |
| 2024 | `articles-16623_recurso_1.pdf` | `costos_administracion_2024.pdf` |
| 2025 | `articles-17085_recurso_1.pdf` | `costos_administracion_2025.pdf` |

Procesa: `Scripts/27_procesar_costos_afp.py` → `Data processed/afp_resultados_sistema.csv` (solo el sistema; el cuadro N° 1 por AFP no se extrae todavía). Ojo: el total de gastos de 2019 y 2021 incluye la prima del seguro de invalidez y sobrevivencia (≈ 330 millones), que el desglose del texto no trae. El semestral 2025 no se descargó.
