# Las siete regiones prioritarias: qué las une y qué hay que cuestionar

Revisión crítica del 2026-11-10 (año de referencia 2024). Datos: `Data processed/kpi_cobertura_regiones.csv`, `kpi_cobertura_pendularidad.csv`, `kpi_cobertura_factores.csv`. Las pruebas de este documento se hicieron con permutación exacta (11.440 combinaciones de 7 regiones entre 16).

## 1. La observación y cómo queda precisa

Observación: al sumar Arica y Parinacota y Los Ríos a las cinco anteriores, la lista coincide con las regiones que **perdieron cotizantes (personas)** y tienen **peor cobertura**.

Lo exacto es esto:

| | Regiones |
|---|---|
| Perdieron cotizantes entre 2022 y 2024 (personas) | **Metropolitana (−44.099)**, Valparaíso (−13.238), Biobío (−9.751), La Araucanía (−2.524), Ñuble (−2.327), Arica y Parinacota (−2.202), Los Ríos (−1.518). Son exactamente 7; las demás 9 ganaron o quedaron iguales |
| De esas 7, bajo el promedio de Chile | Seis. La séptima es la Metropolitana, con cobertura 51,0 % |
| Bajo el promedio y con cotizantes que **no** cayeron | **Coquimbo** (+3.523), Los Lagos (+132), Tarapacá, Maule |

Entonces el ajuste es exacto para **seis** regiones (Valparaíso, Biobío, La Araucanía, Ñuble, Arica y Parinacota, Los Ríos), la Metropolitana queda fuera solo porque está sobre el promedio, y **Coquimbo es la excepción**: está en la lista por su brecha (33 mil cotizantes) pero no perdió cotizantes. La regla del dashboard lo dice: «bajo el promedio y (entre las 5 de mayor brecha o con menos cotizantes que en 2022)». Da 7 regiones; la columna «Por qué entra» distingue **Brecha y pérdida** (4), **Solo brecha** (Coquimbo) y **Solo pérdida** (Los Ríos, Arica).

## 2. Qué conviene cuestionar de esa lectura

1. **La pérdida es en buena parte un hecho de 2023.** El país perdió 160 mil cotizantes de 2022 a 2023 (−2,7 %) y recuperó 106 mil en 2024. El «cambio desde 2022» mide sobre todo **cuánto se recuperó cada región**: Maule y Coquimbo recuperaron todo; Valparaíso casi nada (+1,2 mil de −14,4 mil); Arica siguió bajando. Es un hallazgo real, pero no es una tendencia de largo plazo.
2. **La pérdida absoluta está muy concentrada.** Metropolitana, Valparaíso y Biobío suman el 89 % de lo perdido (−67 mil de −76 mil); las otras cuatro, −8,6 mil en total. En porcentaje de sus cotizantes, Arica (−3,2 %), Valparaíso (−2,4 %) y Biobío (−2,0 %) pierden más.
3. **La cifra en personas no depende de la población proyectada**, a diferencia de la cobertura. Es una ventaja: se puede defender mejor.
4. **Siete de dieciséis es casi la mitad del país.** Con una regla flexible es fácil acertar; por eso el ajuste exacto no prueba nada por sí solo. Lo que sí informa es dónde **no** acierta (Coquimbo) y que la Metropolitana tiene la mayor pérdida absoluta.

## 3. Búsqueda de otra relación: todo lo que hay guardado

48 variables por región (Censo 2024, ENE, CASEN, PIB regional, estudio de la Asociación de AFP, pendularidad) contra «ser una de las 7». Diferencia de medias (estadístico t), valor p exacto y valor p **ajustado por probar 48 variables** (máximo del estadístico sobre todas las permutaciones).

| Variable | Las 7 | Las otras 9 | t | p | p ajustado |
|---|---|---|---|---|---|
| Participación laboral (ENE, 15+) | 58,2 % | 64,7 % | −4,1 | 0,002 | **0,044** |
| Desocupación (Censo, abril 2024) | 9,8 % | 7,9 % | +4,1 | 0,001 | **0,044** |
| Ocupados que trabajan en otra región | 6,5 % | 2,6 % | +3,6 | 0,003 | 0,10 |
| Participación laboral (Censo, 15+) | 55,7 % | 61,5 % | −3,5 | 0,006 | 0,10 |
| Saldo de pendulares (% de los ocupados) | −4,2 % | +5,8 % | −3,2 | 0,001 | 0,18 |
| Personas de 80+ (%) | 3,5 % | 2,8 % | +3,0 | 0,005 | 0,21 |
| Desocupación (ENE, dic. 2023) | 8,9 % | 6,8 % | +3,0 | 0,013 | 0,22 |
| Informalidad (ENE) | 33,2 % | 28,2 % | +2,2 | 0,048 | 0,61 |

18 de las 48 variables salen con p < 0,05; por azar se esperarían 2,4. Hay estructura, pero las variables se parecen entre sí (envejecimiento, participación y desocupación van juntas), así que no son 18 pruebas independientes. **Solo dos sobreviven al ajuste:** participación laboral baja y desocupación alta, es decir, un **mercado laboral débil**.

**Sin relación con el grupo:** pueblos originarios (17,9 % en ambos grupos, r con la cobertura −0,15), independientes (35,2 % frente a 34,0 %; en la ENE, 25,6 % frente a 25,0 %), sectores de alta informalidad, escolaridad, ingreso imponible, agricultura, pobreza 65+. Descartarlas es un resultado útil. **Informalidad por sexo** (INE, nov-ene 2023-24, `Scripts/28_informalidad_por_sexo.py`): la brecha mujeres − hombres es de 3,2 puntos en las siete y de 3,1 en las demás; su correlación con la cobertura es r = +0,32 (p = 0,23) y con Antofagasta y Atacama fuera, +0,08. Por separado, la informalidad de los hombres (r = −0,82) y la de las mujeres (r = −0,73) se asocian con la cobertura casi igual que el total: separar por sexo no agrega una razón (gráfico 3b del KPI 1.1).

## 4. Candidatos, uno por uno

| Candidato | Qué dicen los datos | Veredicto |
|---|---|---|
| **Mercado laboral débil** (participación baja, desocupación alta) | Separa al grupo (p ajustado 0,044) y en la descomposición la participación explica a Biobío (−2,8 puntos), Arica (−2,3) y Coquimbo (−2,1). **Pero** la participación de 15+ cae con el envejecimiento (r = −0,70 con el % de 65+); con 15 a 64 años la diferencia sigue (64,4 % frente a 68,9 %), aunque menor | Respaldo moderado; hay que usar la medida de 15-64 (ya reemplazó a la de 15+ en el gráfico de asociaciones, r = +0,77) |
| **Regla de asignación y pendularidad** | El saldo de pendulares se asocia con la cobertura (r = +0,59, p = 0,02) y la salida con −0,61 (p = 0,01). Si los cotizantes se contaran por lugar de trabajo, Antofagasta bajaría 7,8 puntos y Coquimbo subiría 2,3; la dispersión entre regiones bajaría de 12,2 % a 10,1 % | **Problema de medición, no de causa.** Importa para Coquimbo, Arica y Valparaíso (+1,4 a +2,3). **No** cambia a las tres de menor cobertura (La Araucanía, Los Ríos, Ñuble: menos de 0,7 puntos): su problema es robusto |
| **Informalidad** | Explica el nivel de la cobertura (r = −0,83) pero casi no distingue al grupo (p ajustado 0,61): Biobío tiene informalidad baja (26,7 %) y aun así está | Explica «cuán baja es la cobertura», no «quiénes son las siete». Es en parte lo mismo que «no cotiza» |
| **Desempleo** | Nivel: casi no aporta a la brecha (−0,1 puntos en promedio). **Cambio:** el cambio de cotizantes 2022-2024 (%) se asocia con la desocupación (ENE ρ = −0,63, p = 0,009; Censo ρ = −0,50) | Distinto según la pregunta: no explica el nivel, sí podría explicar quién perdió gente. Con tantas pruebas, p = 0,009 no resiste el ajuste: dejarlo como pista |
| **Envejecimiento** | 80+ y 65+ más altos en el grupo (p 0,005 y 0,020; ajustado 0,21 y 0,38) | Confunde la participación; contexto |
| **Industria, independientes, rural, pueblos originarios** | Sin relación con el grupo | Descartados |

## 5. Lo que falta y sí se podría conseguir

- **Regla de asignación regional** de la Superintendencia: una línea («¿el cotizante se cuenta en la comuna del empleador o en el domicilio del afiliado?»). Es lo que más cambiaría la lectura de Coquimbo, Arica y Valparaíso.
- **Cotizantes por rama de actividad y por región** (Superintendencia) y la **ENE regional por rama, categoría y sexo con todas las categorías** (los archivos bajados traen solo «Total»): sin ellos, «industria dominante» y «cuenta propia» no se pueden medir con datos oficiales.
- **ENE de diciembre de 2025 y proyección regional base 2024** para pasar el año de referencia a 2025.
- **Densidad de cotizaciones por región** (continuidad de los aportes): mide mejor el «flujo» de las siete que la foto de diciembre.
- **Los cotizantes mensuales de 2023** para ver si la caída de 2023 fue un solo mes (diciembre) o todo el año: el archivo tiene solo diciembre.

## 6. Conclusión

Las siete son regiones con **pocos cotizantes para su tamaño** (nivel) o que **dejaron de sumar** (flujo); lo común es un **mercado laboral más débil** (participación y empleo), no la informalidad ni la industria ni los pueblos originarios. La parte «dónde falta más gente» es sólida (La Araucanía, Los Ríos, Ñuble, incluso con otra regla de asignación); la parte «quién perdió cotizantes» depende de 2023 y de cuánto se recuperó cada región.
