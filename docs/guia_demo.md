# Guía paso a paso para ejecutar la demo en clase

Ejecuta todos los comandos desde la raíz del proyecto:

```bash
cd /c/Users/jartu/Code/elastic/memoria-agente-git
```

## 1. Preparar el entorno

En Git Bash, activa el entorno virtual:

```bash
source .venv/Scripts/activate
```

Comprueba el intérprete:

```bash
python --version
```

Debe mostrar Python 3.12.

Si es la primera ejecución en ese ordenador, crea `.env`:

```bash
cp .env.example .env
```

## 2. Iniciar Elasticsearch y Kibana

```bash
docker compose --env-file .env -f docker/compose.yaml up -d
```

Comprueba que los contenedores están funcionando:

```bash
docker compose --env-file .env -f docker/compose.yaml ps
```

Espera unos segundos si Elasticsearch todavía está arrancando.

## 3. Explorar el libro con ES|QL en Discover

Abre Discover en el navegador:

<http://localhost:5601/app/discover>

En Elastic Stack 9.5, Discover puede abrir inicialmente en modo clásico. Abre el menú de la aplicación y selecciona **Query in ES|QL** o **Try ES|QL** para mostrar el editor de consultas.

### Contar los fragmentos indexados

```esql
FROM progit
| STATS fragmentos = COUNT(*)
```

Con la versión utilizada para esta guía, el resultado esperado es `112`. El número puede cambiar cuando se actualice el repositorio de la traducción española.

### Ver cómo está representado el libro

```esql
FROM progit METADATA _id
| KEEP _id, title, section, content, source
| LIMIT 10
```

En cada fila puedes señalar:

- `title` y `section`: la ubicación conceptual del fragmento.
- `content`: el texto que podrá recuperar el agente.
- `source`: la referencia al documento original.
- `_id`: el identificador estable del fragmento indexado.

### Contar los fragmentos por capítulo

```esql
FROM progit
| STATS fragmentos = COUNT(*) BY chapter
| SORT chapter ASC
```

Esta consulta permite explicar que el libro se ha dividido en fragmentos, pero conserva metadatos para identificar su capítulo de origen.

### Buscar contenido sobre ramas y fusiones

```esql
FROM progit METADATA _score
| WHERE content : "crear fusionar ramas"
| KEEP _score, title, section, content, source
| SORT _score DESC
| LIMIT 10
```

El operador `:` realiza una búsqueda de texto completo sobre el campo analizado `content`. La columna `_score` permite ordenar los fragmentos por relevancia.

Si una consulta indica que `progit` no existe o no contiene filas, continúa con el paso siguiente y ejecuta la carga del libro.

## 4. Comprobar el estado del laboratorio

```bash
python -m src.cli status
```

Resultado esperado:

```text
Elasticsearch OK: 9.5.6
  progit: 112 documentos
  agent-memories: 0 documentos
```

El número de documentos de `progit` puede variar si se ha cargado otra versión del libro.

Si `progit` está vacío, carga el contenido:

```bash
python -m scripts.load_book
```

Después, repite:

```bash
python -m src.cli status
```

## 5. Demostrar la recuperación documental

Busca información en *Pro Git*:

```bash
python -m src.cli search "crear y fusionar ramas"
```

Explica que:

- La pregunta se envía a Elasticsearch.
- Elasticsearch busca fragmentos relevantes mediante BM25.
- Los resultados proceden del índice `progit`.
- Todavía no interviene ningún LLM.
- Cada resultado conserva título, sección y fuente.

Puedes probar otra consulta:

```bash
python -m src.cli search "cómo crear una rama y cambiar a ella"
```

## 6. Mostrar el agente sin memoria

Antes de guardar preferencias, ejecuta:

```bash
python -m src.cli ask "¿Cómo creo una rama de Git?" --user alumno-01
```

La terminal mostrará tres secciones:

```text
=== CONOCIMIENTO RECUPERADO ===
...

=== MEMORIA RECUPERADA ===
(ninguna)

=== RESPUESTA ===
Modo local: sin LLM...
```

Punto didáctico: el conocimiento documental y la memoria del usuario son fuentes independientes.

## 7. Guardar un recuerdo explícito

```bash
python -m src.cli remember "Estoy aprendiendo Git y prefiero ejemplos paso a paso con PowerShell" --user alumno-01
```

La CLI devolverá el identificador del recuerdo:

```text
Recuerdo guardado: <identificador>
```

Explica que el recuerdo:

- Se guarda en `agent-memories`.
- Está asociado a `alumno-01`.
- Persiste aunque se cierre la terminal.
- No modifica el índice `progit`.
- Se almacena únicamente porque el usuario lo solicitó explícitamente.

## 8. Inspeccionar la memoria

```bash
python -m src.cli memories --user alumno-01
```

Debe aparecer el recuerdo guardado:

```text
<identificador> | Estoy aprendiendo Git y prefiero ejemplos paso a paso con PowerShell
```

Comprueba también los contadores:

```bash
python -m src.cli status
```

Resultado aproximado:

```text
progit: 112 documentos
agent-memories: 1 documentos
```

## 9. Repetir la pregunta con memoria

```bash
python -m src.cli ask "¿Cómo creo una rama de Git?" --user alumno-01
```

Ahora la sección de memoria debe contener la preferencia:

```text
=== MEMORIA RECUPERADA ===
- Estoy aprendiendo Git y prefiero ejemplos paso a paso con PowerShell
```

Explica que, en modo local, la aplicación enseña el contexto que recibiría el modelo, pero no genera una respuesta natural.

## 10. Opcional: generar una respuesta con el LLM

Realiza este paso únicamente si `.env` contiene una `OPENAI_API_KEY` válida y quieres utilizar la API:

```bash
python -m src.cli ask "¿Cómo creo una rama de Git?" --user alumno-01 --llm
```

La respuesta debería:

- Utilizar *Pro Git* como fuente factual.
- Incluir referencias a los fragmentos recuperados.
- Adaptar el estilo a la preferencia por PowerShell.
- Tratar los recuerdos como preferencias, no como hechos técnicos.

Este paso puede implicar coste y envía la pregunta y parte del contexto al proveedor del modelo.

## 11. Demostrar la persistencia entre sesiones

Cierra Git Bash, abre otra terminal y vuelve al proyecto:

```bash
cd /c/Users/jartu/Code/elastic/memoria-agente-git
source .venv/Scripts/activate
```

Consulta de nuevo:

```bash
python -m src.cli memories --user alumno-01
```

El recuerdo seguirá disponible porque reside en Elasticsearch, no en la memoria del proceso Python.

## 12. Borrar la memoria para la siguiente demo

Primero muestra el contenido que se va a borrar:

```bash
python -m src.cli memories --user alumno-01
```

Ejecuta el borrado interactivo:

```bash
python -m src.cli reset-memory
```

La CLI solicitará:

```text
Escribe BORRAR para confirmar:
```

Introduce exactamente:

```text
BORRAR
```

Para un guion automatizado puedes utilizar:

```bash
python -m src.cli reset-memory --confirm
```

Este comando:

- Elimina todos los documentos de `agent-memories`.
- Conserva el índice y su mapping.
- No modifica ni elimina `progit`.
- Puede ejecutarse repetidamente.

## 13. Verificación final

```bash
python -m src.cli memories --user alumno-01
python -m src.cli status
```

Resultado esperado:

```text
Sin recuerdos.
```

```text
Elasticsearch OK: 9.5.6
  progit: 112 documentos
  agent-memories: 0 documentos
```

El laboratorio queda preparado para comenzar otra demostración sin tener que volver a cargar *Pro Git*.

Cuando termines la clase, puedes detener los contenedores conservando los datos:

```bash
docker compose --env-file .env -f docker/compose.yaml down
```

No uses `scripts.reset_demo` ni `docker compose down -v` entre demostraciones: ambos eliminan más datos de los necesarios.
