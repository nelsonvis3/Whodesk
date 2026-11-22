# Evaluación del asistente (recuperación y abstención)

Comando: `python manage.py eval_rag --sweep` (con la base de demostración cargada: `python manage.py seed_demo`).
Hay además un test (`test_eval_rag_quality_regression_guard`) que falla si Hit@1 baja de 85 % o Hit@3 de 95 %.

## Qué se mide (y qué no)

| Se mide | No se mide |
|---|---|
| Hit@k: ¿el artículo esperado está entre los k primeros resultados? | La calidad de la respuesta generada por el LLM (no hay clave de API en el entorno de desarrollo) |
| Abstención correcta: ¿se abstiene cuando el corpus no tiene la respuesta? | Groundedness (si cada afirmación se sostiene en las fuentes) |
| Falsas abstenciones: ¿se abstiene cuando sí había respuesta? | Satisfacción real de usuarios (el feedback 👍/👎 queda registrado en `RagQuery.feedback`) |
| Latencia de recuperación | Latencia del proveedor de LLM |

## Resultados (30 preguntas: 22 con respuesta, 8 sin respuesta; corpus público de 10 fragmentos)

| Métrica | Resultado |
|---|---|
| Hit@1 | 95 % |
| Hit@3 | 100 % |
| Hit@4 | 100 % |
| Latencia de recuperación (mediana) | 0,02 ms (índice BM25 en memoria, corpus mínimo) |

Barrido del umbral de abstención (puntaje BM25 del mejor fragmento):

| Umbral | Abstención correcta (sin respuesta) | Falsas abstenciones | Top-1 correcto y respondido |
|---|---|---|---|
| 1.5 | 62 % | 5 % | 91 % |
| 2.0 | 75 % | 9 % | 86 % |
| **2.5 (elegido)** | **88 %** | **9 %** | **86 %** |
| 3.0 | 88 % | 23 % | 73 % |
| 3.5 | 100 % | 36 % | 64 % |
| 4.0 | 100 % | 36 % | 64 % |

Se eligió 2.5 como equilibrio: casi no deja pasar preguntas sin respuesta y mantiene bajas las falsas abstenciones.

## Limitaciones que hay que tener presentes

1. **Sesgo de autor.** Las preguntas y el corpus los escribió la misma persona. Eso infla los resultados: un conjunto escrito por otras personas, con su propia forma de preguntar, daría peores números. Lo honesto es leer estos valores como "funciona en el caso feliz", no como una garantía.
2. **Corpus mínimo y sintético.** 30 preguntas sobre 10 fragmentos no permiten conclusiones estadísticas. La diferencia entre 95 % y 100 % es una pregunta.
3. **Búsqueda léxica.** BM25 con un stemming simple y una tabla de sinónimos escrita a mano. No entiende paráfrasis que no comparten palabras con el texto. Los errores que quedan se ven con `eval_rag --verbose`.
4. **El umbral depende del tamaño del corpus.** El puntaje BM25 absoluto cambia cuando se agregan documentos (cambia el idf). Hay que recalibrar con `--sweep` cuando el corpus crezca; por eso el umbral es configurable (`ASSISTANT_MIN_SCORE`).
5. **Las consultas largas puntúan más alto.** En "sugerir respuesta" la consulta es el texto del ticket y el puntaje absoluto es más alto que con preguntas cortas, por lo que se abstiene menos. Ese caso no está en el conjunto de evaluación.

## Registro de decisiones (lo que falló primero)

El primer criterio de abstención fue la *cobertura ponderada por idf* (fracción de términos de la consulta presentes en el mejor fragmento) con umbral 0,5. Con las mismas 30 preguntas dio **64 % de falsas abstenciones**: las preguntas válidas usan palabras que el artículo no tiene ("link", "funciona", "cambiar"), mientras que algunas preguntas sin respuesta comparten una palabra común con el corpus ("plan"). Ningún umbral de cobertura separaba ambos grupos. Pasar al puntaje BM25 absoluto mejoró el equilibrio (9 % de falsas abstenciones con 88 % de abstención correcta).

## Próximos experimentos

- Embeddings (por API) con búsqueda híbrida (BM25 + vectores) y comparar Hit@k con esta línea base.
- Un conjunto de evaluación escrito por otras personas y con preguntas largas (tickets reales anonimizados).
- Medir groundedness con una muestra revisada a mano cuando haya un proveedor de LLM configurado.
