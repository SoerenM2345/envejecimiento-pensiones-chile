# Costos y economía de las AFP: hallazgos verificados (2016-2025)

Fuente única: Superintendencia de Pensiones, «Costos de administración de los Fondos de Pensiones», informes anuales 2016-2025
(`Data raw/_external/sp_costos_administracion/`, procesados por `Scripts/27_procesar_costos_afp.py` en
`Data processed/afp_resultados_sistema.csv` y `afp_resultados_por_afp.csv`). Cifras en millones de pesos de cada año salvo que
se diga otra cosa; pesos de 2025 con el IPC anual (`ipc_anual.csv`). Los valores marcados están en `tests/test_costos_afp.py`.

Solo se anotan los hallazgos **comprobados** (✅) o **mayormente comprobados** (🟡, con la salvedad escrita). Las hipótesis (efectos
de escala por AFP, recomendaciones) quedan fuera hasta tener los datos que faltan (abajo).

## Hallazgos

| # | Hallazgo | Estado | Salvedad |
|---|---|---|---|
| 1 | La comisión sostiene el negocio: es entre 72 % y 90 % de los ingresos de las AFP cada año (2025: 1.189.569 de 1.533.038 millones, 77,6 %). | ✅ | Incluye comisiones de pensionados (retiro programado, renta temporal), APV y Cuenta 2, no solo de cotizantes. |
| 2 | Costos y comisión crecen al mismo ritmo: 2016-2025, en pesos de 2025, costos +22,1 % y comisión +21,5 %; los costos son ~51 % de la comisión en 2016 (50,6 %) y en 2025 (50,8 %), con un máximo de 65,7 % en 2020. A nivel sistema no hay ganancia de eficiencia. | ✅ | No comparar tasas de crecimiento que crucen 2020/21 (Habitat se reexpresó por la división societaria); las razones dentro de cada año sí son comparables. |
| 3 | El alza de la ganancia 2025 viene del encaje: el encaje fue 19,0 % de los ingresos (2024: 10,9 %); la ganancia creció 18,0 % real (cifra de la Superintendencia, IPC de diciembre), pero la ganancia antes de impuestos sin encaje solo +4,4 % nominal (≈ +0,2 % real con el IPC de 2024). | ✅ | Con el IPC anual del proyecto la ganancia sube 17,0 % real. El encaje es muy volátil (2,7 % a 20,5 % de los ingresos). |
| 4 | Estructura del gasto 2025: personal 47,9 % (administrativo 30,8 %, ventas 17,2 %), operación 39,1 % (administración 20,9 %, computación 9,5 %, otros 5,9 %, comercialización 2,7 %), depreciación 9,5 %, otros 3,5 %. | ✅ | Porcentajes con una decimal tal como los publica el informe; montos por componente se derivan de ellos. |
| 5 | Del vendedor al computador: la venta (personal de ventas + comercialización) baja de 13,2 % de la comisión en 2016 a 10,1 % en 2025 (mínimo 8,7 % en 2022); la computación sube de 3,3 % a 4,8 % (máximo 6,0 % en 2020). | ✅ | Que el cambio sea digitalización no está demostrado. |
| 6 | Costo por cliente 2025: 49.891 $ por afiliado y 101.151 $ por cotizante al año (afiliados y cotizantes de diciembre, Superintendencia). En pesos de 2025, el costo por afiliado subió solo ~3 % desde 2016 y el costo por cotizante ~8 %. | 🟡 | Costo promedio, no marginal; los costos atienden también a pensionados y ahorrantes voluntarios. |
| 7 | Comisión de equilibrio (escenario, no pronóstico): con el costo 2025 por cotizante, una comisión de **0,65 % del sueldo imponible** (ingreso promedio 1.294.399 $ al mes, fichas previsionales 2025) cubre los costos; la comisión implícita del sistema es 1,28 %. Con costos fijos, la comisión podría bajar ~49 % antes de que el negocio principal (sin encaje ni impuestos) tenga pérdida. | 🟡 | La comisión implícita está sobreestimada (ver hallazgo 1). Las comisiones por AFP aún no están en el repo. |
| 8 | Ley 21.735, licitación de stock: cada 24 meses se licita el 10 % de los afiliados no pensionados (selección aleatoria y representativa); pueden postular solo AFP con menos de 25 % de los afiliados no pensionados, y entidades nuevas. | ✅ | Fuente: Nota Técnica de la Subsecretaría de Previsión Social (`Data raw/_external/ley_21735/`). Fecha de la primera licitación y duración de la comisión adjudicada: no comprobadas en el repo. |
| 9 | Por administradora, costo sin depreciación ÷ ingresos ordinarios, 2022 → 2025: Habitat 36,1 → 37,8 %, Modelo 52,9 → 41,7 %, PlanVital 51,8 → 45,7 %, Cuprum 46,7 → 43,3 %, Provida 44,7 → 45,7 %, Capital 45,8 → 47,0 %, Uno 45,7 → 50,0 %, sistema 44,6 → 43,6 %. Rentabilidad sobre patrimonio 2025: Uno 64,8 %, PlanVital 54,1 %, Modelo 53,6 %, Habitat 48,4 %, Capital 25,9 %, Cuprum 16,1 %, Provida 11,5 % (sistema 23,2 %). | 🟡 | Por AFP solo hay «ingresos ordinarios» (incluyen otros ingresos operacionales), no comisiones. Con n = 7 no se puede afirmar un efecto de escala. |

## Lo que falta para el resto (por prioridad)

1. Comisiones por AFP (Superintendencia, «Comisiones»): comparar la comisión de equilibrio con el mercado.
2. Cotizantes y afiliados por AFP: costo por cuenta y cuota de mercado (regla del 25 %).
3. Texto de la ley sobre fecha de inicio y duración de la licitación de stock.
