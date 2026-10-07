# Datos: qué falta (verificado 2026-10-07)

Revisado dos veces: inventario con `find` y, de forma independiente, con `os.walk` + hash SHA-256 (83 archivos en ambas pasadas; los duplicados idénticos se detectaron por contenido).

## Resumen por KPI

| KPI | Datos | Estado |
|---|---|---|
| 1.1 Cobertura regional | Cotizantes por región (Superintendencia) + Censo 2024 | Completo |
| 1.2 Razón de soporte | Ídem + proyecciones INE nacionales | Completo (proyección regional = reparto de tasas nacionales, no oficial) |
| 1.3 Participación partes interesadas | Estados financieros FAPP dic-2025 y jun-2026, nota técnica DIPRES | **Incompleto: falta el denominador** |
| 2.1 Costo real por adulto mayor | DIPRES gasto "7102 Edad avanzada" 2016-2025, PGU/PBS/APS mensual 2008-2025, PIB Banco Central 2013-2025, población 65+ INE | **Calculado** (script 13, dashboard) |
| 2.2 Financiamiento dedicado | Ídem + nota FAPP | **Ratio 1 calculado; ratio 2 incompleto** |
| 2.3 Pobreza en la vejez | CASEN 2022 completa (`edad`, `region`, `pobreza`, `expr`, `varstrat`, `varunit`) | **Calculado** (script 14, dashboard) |

## Lo que sigue abierto

1. **Monto en pesos de las cotizaciones de los trabajadores (2024 y 2025)** (KPI 1.3, denominador "financiamiento total"). Ningún archivo lo trae: `cotizaciones_totales.xls` cuenta cotizaciones, no pesos, y los estados del FAPP solo cubren el ingreso del FAPP. Descargar de la Superintendencia de Pensiones: *Sistema de Pensiones → Cotizaciones y Cotizantes* (montos) y *Seguro Social Previsional → Montos de cotizaciones acreditadas*.
2. **Valor presente del déficit** (KPI 2.2, ratio 2). No está en ningún archivo (la nota DIPRES del FAPP solo estima ingresos y egresos del fondo). Decisión del equipo: reemplazarlo por *saldo del fondo (FAPP + FRP) / gasto anual en PGU y APS* ("años de cobertura"), o buscar el Informe Financiero de la Ley 21.735.
3. **Saldo del Fondo de Reserva de Pensiones (FRP)**. La publicación DIPRES lo menciona (págs. 126 y 164) pero no está verificado que traiga la serie; extraer en la fase de cálculo. La nota técnica indica que el FRP transfirió hasta US$900 millones al FAPP.

## Decisiones, no archivos

- **CASEN: metodología.** La base `casen_2022.dta` ya trae `pobreza` recalculada con la metodología 2024: da 20,49% de pobreza por ingresos en 2022 (oficial con metodología 2024: 20,5%; con la anterior eran 6,5%). Es coherente con el informe de líneas de pobreza (dic-2025), pero no se debe comparar con cifras publicadas en 2023. CASEN 2024 (17,3%) existe y daría un dato más reciente; usarlo es opcional.
- **Cotizantes dic-2024:** `cotizantes_region.xls` ya tiene la serie anual 1985-2025, así que se puede alinear con el Censo 2024 sin descargar nada.
- **Sistema antiguo (IPS):** no hace falta el gasto anual del IPS aparte; el gasto DIPRES "Edad avanzada" ya lo incluye.

## Opcionales (no bloquean los 6 KPIs)

Proyecciones regionales INE base 2024 (si el INE las publica); fuentes de cifras citadas en la presentación (ingreso mediano INE $611.162, ingreso mediano de Alemania, cobertura 17,3% del IPS); comisiones, traspasos y sucursales por AFP (modo dev).

## Nota de calidad

La suma mensual de PGU/PBS/APS reproduce el resumen anual publicado en 2022, 2023 y 2024 (diferencia 0,00%). En 2025 la diferencia es −0,16% (7.043.112 vs 7.054.104 MM$); proviene de una revisión de cifras en el propio informe y no se corrigió.
