# Unidad: Posicionamiento — Principal Components Analysis (PCA)
**Asignatura:** Data Analytics / Data Science · Ing. Comercial / Magíster Continuidad Marketing (9° sem.)
**Caso del programa:** Posicionamiento / reducción de componentes · **Herramientas del programa:** PSPP, KNIME, MS Excel

> **Resultado de aprendizaje de la unidad:** *Muestra las ubicaciones de las marcas en los mapas perceptuales desarrollados y determina las estrategias de negocio a seguir.*
> **Contenidos:** Bases del PCA · Reducción de variables · Factor Analysis con PSPP · Caso de posicionamiento.

---

## 0. Contenido del paquete

| Archivo | Para qué sirve |
|---|---|
| `guia_clase_posicionamiento_pca.md` | Este documento |
| `pca_posicionamiento.py` | Script completo: diagnóstico → PCA → Varimax → mapa perceptual |
| `generar_datasets.py` | Regenera los datasets (cambia la semilla o las marcas para crear variantes por grupo) |
| `data/percepciones_supermercados.csv` | 1.200 encuestas, 8 marcas ficticias, 12 atributos (escala 1-7) |
| `data/percepciones_bancos.csv` | Ídem, categoría bancos/fintech (para el trabajo grupal) |
| `data/medias_*.csv` | Promedios por marca (para usar en Excel o para mostrar el análisis "agregado") |
| `resultados_*/` | Salidas de referencia (gráficos, cargas, coordenadas) para que verifiques el script |

**Importante:** los datasets son **sintéticos**. Las marcas son ficticias y los datos se construyeron a partir de dimensiones latentes, por lo que la estructura sale más limpia que en una encuesta real. Conviene decirlo explícitamente a los alumnos y contrastarlo con la discusión de "qué pasa con datos reales".

**Ejecución rápida**
```bash
pip install -r requirements.txt
python pca_posicionamiento.py --datos data/percepciones_supermercados.csv
python pca_posicionamiento.py --datos data/percepciones_bancos.csv --ejes 1 3
```

---

## 1. Marco conceptual (material de estudio)

### 1.1 ¿Por qué PCA en posicionamiento?
Dentro del modelo **STP** (Segmentación → *Targeting* → Posicionamiento), el posicionamiento busca responder *¿cómo perciben los consumidores mi marca frente a la competencia?* Una encuesta típica mide 10-30 atributos por marca; es imposible "ver" 12 dimensiones. El PCA resume esos atributos en 2-4 **dimensiones perceptuales** (p. ej. "precio", "calidad", "servicio") y permite dibujar un **mapa perceptual** donde la distancia entre marcas es la similitud percibida.

Preguntas de negocio que responde el mapa:
- ¿Con quién compito realmente (marcas vecinas en el mapa)?
- ¿Qué espacios están vacíos (posiciones sin ocupar)?
- ¿Coincide la posición percibida con la posición deseada?
- ¿Qué atributos habría que reforzar para moverme hacia una posición más atractiva?

### 1.2 Idea central del PCA
- Se buscan **combinaciones lineales** de las variables originales (los *componentes*) que sean **no correlacionadas entre sí** y capturen la mayor varianza posible: el 1er componente captura lo máximo, el 2° lo máximo de lo que queda, etc.
- Con variables **estandarizadas**, el PCA equivale a descomponer la **matriz de correlaciones** en *autovalores* y *autovectores*.
  - **Autovalor (λ):** varianza que captura un componente. Con p variables estandarizadas, la varianza total es p.
  - **% de varianza explicada:** λ / p.
  - **Carga (loading):** correlación entre la variable original y el componente. Se usa para *nombrar* el componente.
  - **Comunalidad:** proporción de la varianza de una variable explicada por los componentes retenidos (suma de cargas² de esa variable). Comunalidad baja (< 0.4-0.5) = la variable "no encaja" en la solución.
  - **Puntaje (score):** coordenada de cada observación en el componente. El promedio de puntajes por marca da su ubicación en el mapa.

### 1.3 PCA vs. Análisis Factorial (AF)
| | PCA | Análisis Factorial exploratorio |
|---|---|---|
| Objetivo | Resumir la **varianza total** | Modelar la **varianza común** (factores latentes) |
| Modelo | Componentes = combinaciones de variables | Variables = combinación de factores + error específico |
| Uso típico | Reducción de datos, mapas, índices | Construcción y validación de escalas |

En la práctica de marketing ambos suelen dar soluciones muy parecidas cuando hay comunalidades altas y muchas variables. **PSPP** (`FACTOR`) permite ambos (`/EXTRACTION=PC` o `PAF`); vale la pena mostrar que el resultado cambia poco y explicar por qué.

### 1.4 Flujo de trabajo (los 6 pasos que se enseñan)
1. **Preparar datos:** escala común, sin faltantes graves, revisar valores atípicos. Regla práctica: 5-10 casos por variable (mínimo ~100-150).
2. **Diagnosticar** si tiene sentido reducir:
   - **Correlaciones:** deben existir bloques de variables correlacionadas (|r| > 0.3).
   - **Prueba de esfericidad de Bartlett:** H₀ = matriz identidad. Se espera *p* < 0.05.
   - **KMO** (Kaiser-Meyer-Olkin): ≥ 0.8 muy bueno · 0.7-0.8 bueno · 0.6-0.7 mediocre · < 0.5 inaceptable. Revisar también el KMO *por variable* (eliminar las < 0.5).
3. **Decidir cuántos componentes retener** (usar varios criterios, no solo uno):
   - **Kaiser:** λ > 1 (tiende a sobreestimar con muchas variables).
   - **Scree plot:** buscar el "codo".
   - **Varianza acumulada:** ≥ 60% suele considerarse aceptable en ciencias sociales.
   - **Análisis paralelo (Horn):** retener componentes cuyo λ supera al de datos aleatorios. Es el criterio más recomendado en la literatura.
   - **Interpretabilidad:** el componente debe poder nombrarse con sentido de negocio.
4. **Rotar** (Varimax): redistribuye la varianza para que cada variable cargue fuerte en un solo componente, lo que facilita la interpretación. Ojo: la rotación **no cambia** la varianza total explicada, solo su reparto. Si se sospecha que las dimensiones están correlacionadas, usar rotación **oblicua** (oblimin/promax); PSPP las ofrece en `/ROTATION`.
5. **Interpretar cargas:** |carga| > 0.5 para asignar variables a componentes; nombrar cada componente (p. ej. "Calidad percibida").
6. **Construir el mapa:** puntaje medio por marca en los ejes elegidos + vectores de atributos (biplot).

### 1.5 Lectura del mapa perceptual
- **Marcas cercanas** = percepción similar → competidores directos.
- **Una flecha de atributo** apunta hacia donde ese atributo es más fuerte; una marca "en la dirección de la flecha" es percibida como fuerte en él. Flechas opuestas = atributos que se perciben como opuestos (trade-off).
- **Espacios vacíos** = oportunidad potencial, *pero solo si existe demanda*: para eso se agrega el **punto ideal** o una regresión de preferencia sobre los puntajes (en el dataset: `intencion_recompra`; el script imprime la correlación de cada componente con ella).
- **Advertencia:** los ejes son abstractos y los signos de los componentes son arbitrarios. Siempre se interpreta con las cargas, no con la posición sola.

### 1.6 Otras técnicas para mapas perceptuales (para contextualizar)
El PCA/AF parte de **atributos predefinidos** (mapa "basado en atributos"). Existen alternativas: **Escalamiento Multidimensional (MDS)** a partir de similitudes entre marcas (no requiere listar atributos), **Análisis de Correspondencias** (para datos categóricos, p. ej. "¿qué marca asocia a cada frase?") y **Análisis Discriminante** (maximiza la separación entre marcas). Puede ser una buena discusión de cierre: *¿qué ventaja y qué sesgo tiene pedir atributos al encuestado?*

### 1.7 Errores y limitaciones frecuentes
- Aplicar PCA con variables no correlacionadas o con muy pocos casos.
- Retener componentes solo por Kaiser sin mirar el scree ni el análisis paralelo.
- **Falacia del promedio:** agregar por marca *antes* de hacer PCA oculta dimensiones. En el dataset de supermercados, el PCA sobre las **medias por marca** (8 filas) entrega solo 2 dimensiones que explican 94% de la varianza, mientras que sobre las **encuestas individuales** emergen 4 dimensiones interpretables (69%). *(Se puede demostrar con `--nivel marcas`.)*
- **n < p:** la matriz de correlaciones es singular; no se pueden calcular KMO ni Bartlett (el script lo advierte).
- Interpretar los mapas como "verdad" y no como una foto de percepciones de una muestra en un momento dado.
- **Sesgo halo:** un encuestado que "quiere" a una marca tiende a puntuar todo alto; se ve como un primer componente "general".

---

## 2. Plan de clase sugerido (2 sesiones, ~110 min c/u; ajustar al bloque real)

### Sesión 1 — Fundamentos y diagnóstico (≈110 min)
| Min | Actividad | Recurso |
|---|---|---|
| 0-10 | **Gancho:** mostrar un mapa perceptual (`03_mapa_perceptual.png`) sin explicar y preguntar *"¿qué estrategia le recomendarían a Andina?"* | Gráfico de resultados |
| 10-30 | Posicionamiento en el modelo STP y lectura de mapas perceptuales | §1.1, §1.5 |
| 30-55 | Idea del PCA: varianza, autovalores, cargas, comunalidad (con analogía de "resumir 12 preguntas en 4 ideas") | §1.2-1.3 |
| 55-65 | *Pausa* | |
| 65-90 | **Taller 1 (Excel):** abrir `percepciones_supermercados.csv`, calcular la matriz de correlaciones (Análisis de datos → Correlación) y marcar los bloques. Predecir cuántas dimensiones habrá | §3.1 |
| 90-110 | Diagnóstico: Bartlett, KMO y criterios de retención; discusión: ¿cuántos componentes y por qué? | §1.4 |

### Sesión 2 — Aplicación y caso (≈110 min)
| Min | Actividad | Recurso |
|---|---|---|
| 0-35 | **Taller 2 (PSPP):** `FACTOR` con extracción PC + Varimax y lectura de cargas | §3.2 |
| 35-55 | **Demo en vivo (Python):** ejecutar el script y comparar resultados con PSPP | `pca_posicionamiento.py` |
| 55-65 | *Pausa* | |
| 65-95 | **Caso grupal:** dataset de bancos → mapa perceptual y recomendación estratégica | §4 |
| 95-110 | Plenario: cada grupo muestra su mapa y su recomendación (3 min por grupo) + cierre | Rúbrica §5 |

**Alternativa con KNIME** (herramienta del programa): usar el flujo de §3.3 en la Sesión 2 en lugar de PSPP, o como taller opcional.

---

## 3. Talleres con las herramientas del programa

### 3.1 Excel
Excel **no calcula PCA de forma nativa**; úsalo para lo que sí hace bien:
1. Abrir el CSV (Datos → Desde texto/CSV).
2. Análisis de datos → *Coeficiente de correlación* sobre las 12 columnas de atributos y aplicar formato condicional de escala de color para "ver" los bloques.
3. Tabla dinámica con el promedio por marca (o abrir `medias_supermercados.csv`) y un gráfico de barras/radar por marca.
4. Actividad: con las **cargas ya calculadas** (`resultados_*/cargas.csv`), pedir que nombren los componentes y expliquen qué atributos definen cada uno.

### 3.2 PSPP (sintaxis de referencia)
> ⚠️ **Sintaxis a validar antes de la clase** en tu versión de PSPP (no pude ejecutarla en este entorno). Los nombres de las opciones corresponden a la documentación del comando `FACTOR`.

Importar el CSV con *Archivo → Abrir → Asistente de importación de texto* (delimitador coma, primera fila = nombres). Luego, en una ventana de sintaxis:

```
FACTOR
  /VARIABLES=precio_bajo ofertas_promociones calidad_productos frescura
             prestigio_marca sustentabilidad atencion_personal orden_limpieza
             rapidez_caja cercania_ubicacion app_digital variedad_surtido
  /MISSING=LISTWISE
  /PRINT=INITIAL EXTRACTION ROTATION KMO
  /PLOT=EIGEN
  /CRITERIA=MINEIGEN(1) ITERATE(25)
  /EXTRACTION=PC
  /ROTATION=VARIMAX.
```
- `KMO` imprime KMO y la prueba de Bartlett · `PLOT=EIGEN` genera el scree plot · `MINEIGEN(1)` aplica el criterio de Kaiser (o usar `FACTORS(4)` para fijar el número).
- Para comparar con AF "clásico": cambiar `/EXTRACTION=PC` por `/EXTRACTION=PAF`.
- Para guardar puntajes y promediarlos por marca, añadir `/SAVE=REG(ALL)` y luego usar `AGGREGATE` (o *Datos → Agregar*) por la variable `marca`.

### 3.3 KNIME (flujo sugerido)
`CSV Reader` → `Column Filter` (dejar solo los 12 atributos + `marca`) → `Normalizer` (Z-score) → `PCA Compute` → `PCA Apply` → `GroupBy` (por `marca`, media de los componentes) → `Scatter Plot`.
- Ver la varianza explicada en el modelo de `PCA Compute` y decidir cuántos componentes dejar en `PCA Apply`.
- Según recuerdo, los nodos estándar de KNIME no incluyen rotación Varimax; para rotar puedes usar un nodo `Python Script` con la función `varimax()` de este paquete, o bien comparar contra PSPP/Python. Vale la pena verificarlo en tu versión.

### 3.4 Python
Todo el flujo está en `pca_posicionamiento.py` (funciones `bartlett_esfericidad`, `kmo`, `analisis_paralelo`, `varimax`, `mapa_perceptual`). Está pensado para **leerse en clase**: cada función corresponde a un paso de §1.4. Sugerencia: importarlo en un notebook y llamar a las funciones por separado.

---

## 4. Caso para el trabajo grupal: "Posicionamiento en la banca"

**Contexto para los alumnos:** *Eres el equipo de marketing de **Nova Digital**, un banco 100% digital. Gerencia quiere saber cómo lo perciben los clientes frente a la competencia y hacia dónde debería moverse su posicionamiento.*

**Datos:** `data/percepciones_bancos.csv` (8 marcas; 12 atributos en escala 1-7; `intencion_recompra`, `edad`, `nse` como variables adicionales).

**Entregable (máx. 6 láminas o 3 páginas):**
1. Diagnóstico de factorizabilidad (KMO, Bartlett) e interpretación.
2. Justificación del número de componentes (≥ 2 criterios) y % de varianza.
3. Tabla de cargas rotadas con **nombre de cada componente**.
4. Mapa perceptual con lectura: competidores directos y espacios vacíos.
5. ¿Qué componente se asocia más a `intencion_recompra`? (correlación o regresión sobre los puntajes).
6. **Recomendación estratégica** (reposicionar, reforzar o defender) con 2-3 acciones concretas.
7. Limitaciones del análisis.

### Resultados de referencia (para el docente, con la semilla 2026)
**Supermercados** — KMO = 0.776 · Bartlett χ² = 4.360 (gl 66; p < 0.001) · Kaiser y análisis paralelo sugieren 4 · varianza acumulada = 69.4%

| Componente | Atributos con carga alta | Nombre sugerido |
|---|---|---|
| C1 | calidad_productos (.83), frescura (.80), prestigio_marca (.76), sustentabilidad (.70) | Calidad / premium |
| C2 | atencion_personal (.82), orden_limpieza (.80), rapidez_caja (.75) | Experiencia en tienda |
| C3 | cercania_ubicacion (.83), app_digital (.80), variedad_surtido (.77) | Conveniencia |
| C4 | ofertas_promociones (.89), precio_bajo (.86) | Economía |

Lectura esperada: **Andina** = descuento (C4 alto); **Cordillera** = calidad/boutique; **Pacifico** = premium con buen servicio; **Atacama** y **Costanera** = conveniencia; **Maipo** = generalista al centro del mapa.

**Bancos** — KMO = 0.732 · Bartlett χ² = 4.137 (gl 66; p < 0.001) · 4 componentes · varianza acumulada = 69.1% · componentes: Confianza, Digital/innovación, Costo, Presencial. El componente de **Confianza** es el más asociado a `intencion_recompra` (r ≈ 0.30).

> El **orden y la etiqueta** (C1, C2…) pueden variar si cambias la semilla o los datos; lo que debe repetirse es la **estructura** de las cargas. Nota también que `sustentabilidad_esg` es un atributo "ambiguo" (carga en Confianza y en Presencial): buen material para discutir comunalidades y cargas cruzadas.

### Variantes para no repetir caso entre cursos o secciones
Edita el diccionario `marcas` o `SEMILLA` en `generar_datasets.py` y vuelve a ejecutarlo. También puedes crear una tercera categoría (p. ej. aseguradoras o retail de tecnología) copiando la estructura de `SUPERMERCADOS`.

---

## 5. Rúbrica sugerida para el caso (pauta de 100 pts)

| Criterio | Pts | Nivel máximo |
|---|---|---|
| Diagnóstico y supuestos (KMO, Bartlett, correlaciones) | 15 | Los calcula, los interpreta y decide en consecuencia |
| Selección del nº de componentes | 15 | Usa ≥ 2 criterios y justifica |
| Rotación e interpretación de cargas | 20 | Nombra componentes con criterio; comenta cargas cruzadas y comunalidades |
| Mapa perceptual y lectura competitiva | 20 | Identifica competidores, espacios vacíos y trade-offs |
| Vínculo con preferencia/recompra | 10 | Conecta dimensiones con resultado de negocio |
| Recomendación estratégica | 15 | Acciones concretas y coherentes con el análisis |
| Limitaciones y claridad de la presentación | 5 | Reconoce sesgos y comunica con claridad |

---

## 6. Preguntas de discusión y control

1. Si el KMO fuese 0.45, ¿qué harías antes de seguir?
2. Kaiser sugiere 5 componentes y el scree sugiere 3. ¿Cómo decides?
3. ¿Por qué el % de varianza explicada de cada componente cambia tras la rotación Varimax, pero el total no?
4. Una marca queda en el centro del mapa. ¿Es "neutral" o "indefinida"? ¿Qué implica para su estrategia?
5. ¿Qué diferencia hay entre una carga de 0.85 y una comunalidad de 0.85?
6. El mapa de medias por marca muestra 2 dimensiones y el de encuestas individuales 4. ¿Cuál es más útil y por qué?
7. ¿Por qué los ejes de un mapa perceptual no tienen un "signo" natural?

**Ideas para el examen:** dar una tabla de cargas y pedir nombrar componentes; dar un scree plot con análisis paralelo y pedir decidir *k*; dar un mapa y pedir una recomendación para una marca.

---

## 7. Datasets adicionales (para practicar PCA más allá del posicionamiento)

- `sklearn.datasets.load_wine()` — 13 variables químicas de 178 vinos, 3 cultivares. Se instala con scikit-learn y no requiere descarga; clásico para mostrar reducción de dimensiones y separación de grupos.
- `sklearn.datasets.load_iris()` — 4 variables; sirve para una primera demostración muy simple.
- Conjuntos de R como `mtcars` o `USArrests` (accesibles desde `statsmodels.datasets.get_rdataset`, requiere internet).
- Encuestas propias: los alumnos pueden diseñar una mini-encuesta (Google Forms, escala 1-7, 10-12 atributos, 4-6 marcas) para una categoría cercana (cafeterías, apps de delivery, universidades). Es la mejor forma de mostrar que **los datos reales son menos ordenados** que los sintéticos.

---

## 8. Bibliografía sugerida para profundizar
*(Referencias de memoria: verifica edición y datos antes de citarlas formalmente.)*

- **Hair, J. F., Black, W. C., Babin, B. J., Anderson, R. E.** *Multivariate Data Analysis* (Pearson) — capítulo de Análisis Factorial; referencia estándar para criterios de retención, rotación y tamaño muestral.
- **Jolliffe, I. T.** (2002). *Principal Component Analysis* (2ª ed.), Springer — referencia técnica del PCA.
- **James, G., Witten, D., Hastie, T., Tibshirani, R.** *An Introduction to Statistical Learning* — capítulo de aprendizaje no supervisado (PCA); gratuito en línea, con versión en Python.
- **Kaiser, H. F.** (1958). The varimax criterion for analytic rotation in factor analysis. *Psychometrika*. · **Kaiser, H. F.** (1974). An index of factor simplicity. *Psychometrika* (origen del KMO).
- **Horn, J. L.** (1965). A rationale and test for the number of factors in factor analysis. *Psychometrika* (análisis paralelo).
- **Hauser, J. R. y Koppelman, F. S.** (1979). Alternative perceptual mapping techniques: relative accuracy and usefulness. *Journal of Marketing Research*.
- **Ries, A. y Trout, J.** (1981). *Positioning: The Battle for Your Mind* · **Kotler, P. y Armstrong, G.** (bibliografía básica del programa) — capítulos de segmentación y posicionamiento.
- Documentación: `scikit-learn` (`sklearn.decomposition.PCA`) y manual de PSPP (comando `FACTOR`).
