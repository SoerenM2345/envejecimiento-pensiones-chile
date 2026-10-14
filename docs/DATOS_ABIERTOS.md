# Datos: qué falta (verificado 2026-10-07)

Revisado dos veces: inventario con `find` y, de forma independiente, con `os.walk` + hash SHA-256 (83 archivos en ambas pasadas; los duplicados idénticos se detectaron por contenido).

## Resumen por KPI

| KPI | Datos | Estado |
|---|---|---|
| 1.1 Cobertura regional | Cotizantes por región (Superintendencia) + Censo 2024 | Completo |
| 1.2 Razón de soporte | Ídem + proyecciones INE nacionales | Completo (proyección regional = reparto de tasas nacionales, no oficial) |
| 1.3 Participación del flujo comisionable | Fichas Estadísticas Previsionales N° 136-159 (cotizantes e ingreso promedio 2024-2025), estados financieros FAPP dic-2025, Pilar Solidario, Nota Técnica Ley 21.735 (Tabla 1), proyecciones INE | **Calculado** (script 15, dashboard): real 2024-2025 y escenario 2026-2035 |
| 2.1 Costo real por adulto mayor | DIPRES gasto "7102 Edad avanzada" 2016-2025, PGU/PBS/APS mensual 2008-2025, PIB Banco Central 2013-2025, población 65+ INE | **Calculado** (script 13, dashboard) |
| 2.2 Financiamiento dedicado | Ídem + nota FAPP, estados del FAPP, informe mensual del FRP (DIPRES, jul-2026), Ley 21.735 Tabla 2, SII (UTM, dólar) | **Ratio 1 calculado; ratio 2 con alternativa calculada (script 21); VP del déficit oficial pendiente** |
| 2.3 Pobreza en la vejez | CASEN 2022 completa (`edad`, `region`, `pobreza`, `expr`, `varstrat`, `varunit`) | **Calculado** (script 14, dashboard) |

## Lo que sigue abierto

1. ~~**Monto en pesos de las cotizaciones de los trabajadores (2024 y 2025)**~~ (KPI 1.3). **Resuelto como estimación:** cotizantes × ingreso promedio × 10% de las Fichas Estadísticas Previsionales (`_external/fichas_previsionales/`, 12 meses por año). El monto oficial (*Montos de cotizaciones acreditadas*) serviría para validar, pero ya no bloquea.
2. **Valor presente del déficit** (KPI 2.2, ratio 2). No está en ningún archivo (la nota DIPRES del FAPP solo estima ingresos y egresos del fondo). Decisión del equipo: reemplazarlo por *saldo del fondo (FAPP + FRP) / gasto anual en PGU y APS* ("años de cobertura"), o buscar el Informe Financiero de la Ley 21.735. Para el numerador de esa alternativa: el script 16 deja los activos financieros del Gobierno Central (`dipres_pasivos_activos_gc.csv`), pero el FRP viene mezclado con el FEES y otros fondos en una sola línea; el saldo del FRP hay que tomarlo del informe trimestral del fondo (DIPRES), que no está en Data raw. El balance del FAPP (jun-2026) solo muestra el pasivo con el FRP (208.272.126 M$), no el saldo del FRP.
3. ~~**Saldo del Fondo de Reserva de Pensiones (FRP)**~~ **Resuelto (2026-10-13)** con el informe ejecutivo mensual del FRP de DIPRES (julio 2026, `_external/frp/`): valor de mercado a fines de 2020-2025 en US$ (10.313 M a fines de 2025, de los cuales 222 M ya están transferidos al FAPP). Quedan abiertos los estados del FAPP de julio a septiembre de 2026. Texto anterior:  La publicación DIPRES lo menciona (págs. 126 y 164) pero **verificado (2026-10-13): no trae la serie**. La pág. 126 (numeración del PDF) solo explica que el FRP y el FEES están dentro de los activos financieros en moneda extranjera, y la pág. 164 es el glosario; el resto de las menciones son la clasificación funcional (aporte fiscal al FRP) y el catálogo de informes de DIPRES. El saldo del FRP hay que sacarlo del informe trimestral del fondo, que no está en Data raw. La nota técnica indica que el FRP transfirió hasta US$900 millones al FAPP.

## Decisiones, no archivos

- **CASEN: metodología.** La base `casen_2022.dta` ya trae `pobreza` recalculada con la metodología 2024: da 20,49% de pobreza por ingresos en 2022 (oficial con metodología 2024: 20,5%; con la anterior eran 6,5%). La base trae también `pobreza_2013` (metodología anterior): 6,5% para todas las personas y 2,2% para los 65+ (con la 2024, 14,9% para los 65+), así que el nivel del KPI 2.3 depende por completo de la metodología. No se debe comparar con cifras publicadas en 2023. Ojo: el PDF `Valor_CBA_y_LPs_25.12.pdf` (líneas de pobreza, dic-2025) está calculado con la metodología **2013** (el propio informe dice que se publica solo para completar la serie 2025), así que no documenta la metodología 2024 y sirve solo de contexto, no de respaldo del KPI. CASEN 2024 (17,3%) existe y daría un dato más reciente; usarlo es opcional.
- **Cotizantes dic-2024:** `cotizantes_region.xls` ya tiene la serie anual 1985-2025, así que se puede alinear con el Censo 2024 sin descargar nada.
- **Sistema antiguo (IPS):** no hace falta el gasto anual del IPS aparte; el gasto DIPRES "Edad avanzada" ya lo incluye.

## Opcionales (no bloquean los 6 KPIs)

Proyecciones regionales INE base 2024 (si el INE las publica); fuentes de cifras citadas en la presentación (ingreso mediano INE $611.162, ingreso mediano de Alemania, cobertura 17,3% del IPS); comisiones, traspasos y sucursales por AFP (modo dev).

## Nota de calidad

La suma mensual de PGU/PBS/APS reproduce el resumen anual publicado en 2022, 2023 y 2024 (diferencia 0,00%). En 2025 la diferencia es −0,16% (7.043.112 vs 7.054.104 MM$); proviene de una revisión de cifras en el propio informe y no se corrigió.
