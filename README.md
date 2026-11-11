# Más allá del contexto: memoria para agentes de IA con Elasticsearch

Laboratorio universitario con Python, Elasticsearch, Kibana y la edición española de *Pro Git*.

El objetivo es comprender cómo una aplicación puede proporcionar conocimiento y memoria persistente a un agente sin reentrenar el modelo. La práctica funciona completamente en modo local para inspeccionar la recuperación. El uso de un LLM es opcional.

## Qué aprenderás

Al terminar el laboratorio podrás:

- distinguir el contexto temporal, el conocimiento documental y la memoria persistente;
- indexar un libro en fragmentos dentro de Elasticsearch;
- recuperar pasajes mediante búsqueda BM25 en español;
- guardar preferencias explícitas asociadas a un usuario de demostración;
- construir el contexto que recibiría un LLM;
- borrar la memoria sin eliminar el conocimiento documental.

## El modelo mental del laboratorio

Un LLM no recuerda automáticamente lo ocurrido en ejecuciones anteriores. Solo puede utilizar la información que la aplicación incluye en la petición actual. Por eso, en este laboratorio, Python construye el contexto de cada consulta recuperando datos externos desde Elasticsearch.

El proyecto separa esos datos persistentes en dos categorías con responsabilidades diferentes:

- **Conocimiento documental**: información técnica procedente de *Pro Git*. Se utiliza como fuente factual para responder preguntas sobre Git.
- **Memoria del usuario**: preferencias o datos que el usuario decide guardar explícitamente. Se utiliza para personalizar la respuesta, no para establecer hechos técnicos.

La pregunta actual, el conocimiento recuperado y los recuerdos relevantes se combinan temporalmente para formar el contexto del agente. Esta combinación no modifica los parámetros del modelo ni equivale a reentrenarlo: Elasticsearch actúa como almacenamiento externo y recuperable.

En la siguiente tabla se resume dónde vive cada tipo de información y durante cuánto tiempo permanece disponible.
La comparación ayuda a distinguir los datos temporales de aquellos que Elasticsearch conserva para futuras sesiones.

| Elemento | Dónde vive | Ejemplo | Duración |
|---|---|---|---|
| Pregunta actual | Proceso Python | «¿Cómo creo una rama?» | Una ejecución |
| Conocimiento | Índice `progit` | Fragmentos de *Pro Git* | Persistente |
| Memoria | Índice `agent-memories` | «Prefiero ejemplos con PowerShell» | Persistente |

El flujo de una consulta es:

```mermaid
flowchart LR
    question["👤 Pregunta<br/>del usuario"]

    subgraph retrieval["🔎 Recuperación en Elasticsearch"]
        direction TB
        bookSearch["📚 Buscar en<br/><b>progit</b>"]
        memorySearch["🧠 Buscar en<br/><b>agent-memories</b>"]
        knowledge["📖 Conocimiento<br/>documental"]
        preferences["💡 Preferencias<br/>del usuario"]

        bookSearch --> knowledge
        memorySearch --> preferences
    end

    question --> bookSearch
    question --> memorySearch
    knowledge --> context["🧩 Construir<br/>el contexto"]
    preferences --> context

    context --> useLlm{"🤖 ¿Usar<br/><code>--llm</code>?"}
    useLlm -- "No" --> local["🖥️ Mostrar el<br/>contexto recuperado"]
    useLlm -- "Sí" --> response["✨ Generar una<br/>respuesta adaptada"]

    classDef input fill:#dbeafe,stroke:#2563eb,color:#111827,stroke-width:2px
    classDef knowledge fill:#dcfce7,stroke:#16a34a,color:#111827,stroke-width:2px
    classDef memory fill:#fef3c7,stroke:#d97706,color:#111827,stroke-width:2px
    classDef process fill:#ede9fe,stroke:#7c3aed,color:#111827,stroke-width:2px
    classDef output fill:#fce7f3,stroke:#db2777,color:#111827,stroke-width:2px

    class question input
    class bookSearch,knowledge knowledge
    class memorySearch,preferences memory
    class context,useLlm process
    class local,response output
```

La recuperación documental y la memoria se mantienen separadas deliberadamente. Una preferencia del usuario no se trata como una fuente técnica sobre Git.

## Requisitos

- Python 3.10 o superior.
- Git.
- En Windows, una terminal Git Bash o PowerShell.
- Docker Desktop con WSL2 en Windows, o Docker Engine con Compose en Linux/macOS.
- 6–8 GB de memoria disponible entre Docker y el sistema.
- Acceso a Internet durante la primera instalación.
- Puertos locales 9200 y 5601 libres.

> [!WARNING]
> Elasticsearch y Kibana se ejecutan sin autenticación y solo se publican en `127.0.0.1`. Utiliza este proyecto exclusivamente como laboratorio local. No lo expongas a Internet.

## Guía paso a paso

A continuación se presenta un recorrido completo para preparar el entorno, cargar *Pro Git* en español y observar cómo el agente recupera conocimiento y memoria. Los pasos están ordenados para que puedas reproducir la práctica desde una instalación nueva y comprobar el resultado después de cada operación.

El recorrido comienza con la configuración de Python y Docker, continúa con una consulta sin memoria y después incorpora una preferencia persistente. Finalmente, muestra cómo generar una respuesta opcional con un LLM y cómo limpiar la memoria para repetir la demostración.

## 1. Preparar Python

Abre una terminal en la raíz del proyecto.

### Windows con Git Bash

```bash
cp .env.example .env
py -3 -m venv .venv
source .venv/Scripts/activate
python -m pip install -r requirements.txt
```

### Windows con PowerShell

```powershell
Copy-Item .env.example .env
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Si PowerShell bloquea la activación, ejecuta `Set-ExecutionPolicy -Scope Process Bypass` para esa terminal y vuelve a intentarlo.

### Linux, macOS o WSL

```bash
cp .env.example .env
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Comprueba que estás usando el entorno virtual:

```bash
python --version
python -m pip check
```

## 2. Iniciar Elasticsearch y Kibana

```bash
docker compose --env-file .env -f docker/compose.yaml up -d
docker compose --env-file .env -f docker/compose.yaml ps
```

Espera hasta que `elasticsearch` aparezca como saludable y `kibana` esté iniciado. También puedes abrir:

- Elasticsearch: <http://localhost:9200>
- Kibana: <http://localhost:5601>

Comprueba la conexión desde Python:

```bash
python -m src.cli status
```

En la primera ejecución es normal que `progit` tenga cero documentos.

## 3. Cargar *Pro Git* en español

```bash
python -m scripts.load_book
```

El cargador:

1. clona [`progit/progit2-es`](https://github.com/progit/progit2-es) en `data/progit2-es`;
2. selecciona los capítulos 02 y 03;
3. limpia de forma ligera el AsciiDoc;
4. divide el contenido en fragmentos;
5. guarda cada fragmento en `progit` con su capítulo, sección y URL de origen.

La versión utilizada al preparar este laboratorio genera 112 fragmentos. El número puede cambiar si se actualiza la traducción.

Verifica la carga:

```bash
python -m src.cli status
```

Resultado orientativo:

```text
Elasticsearch OK: 9.5.6
  progit: 112 documentos
  agent-memories: 0 documentos
```

El contenido, el título y la sección utilizan el analizador `spanish` de Elasticsearch. Ejecutar de nuevo `load_book` actualiza los documentos con identificadores estables y no crea duplicados.

### Regenerar un índice documental antiguo

Si `progit` contenía la edición inglesa o cambió su mapping, regénéralo explícitamente:

```bash
python -m scripts.load_book --recreate --confirm
```

Este comando elimina y recrea únicamente `progit`. No modifica `agent-memories`.

## 4. Explorar los datos antes de usar el agente

Abre Discover en <http://localhost:5601/app/discover>, activa el modo **ES|QL** y prueba:

```esql
FROM progit
| STATS fragmentos = COUNT(*)
```

Para inspeccionar el texto y su trazabilidad:

```esql
FROM progit METADATA _id
| KEEP _id, title, section, content, source
| LIMIT 10
```

La [guía completa de la demostración](docs/guia_demo.md) contiene más consultas ES|QL y un recorrido preparado para clase.

## 5. Recuperar conocimiento en español

```bash
python -m src.cli search "cómo crear y fusionar ramas"
```

Observa que cada resultado incluye:

- el capítulo y la sección;
- un fragmento del contenido recuperado;
- la URL del archivo original;
- el orden de relevancia calculado por Elasticsearch.

Este paso no utiliza un LLM. Es una búsqueda BM25 sobre el índice `progit`.

## 6. Ver el agente sin memoria

```bash
python -m src.cli ask "¿Cómo creo una rama y cambio a ella?" --user alumno-01
```

La salida separa tres bloques:

```text
=== CONOCIMIENTO RECUPERADO ===
Fragmentos de Pro Git

=== MEMORIA RECUPERADA ===
(ninguna)

=== RESPUESTA ===
Modo local: sin LLM
```

`ask` muestra el contexto recuperado, pero no genera texto si no se añade `--llm`. Esto permite estudiar el flujo sin clave API y sin coste.

## 7. Añadir memoria explícita

Guarda una preferencia ficticia:

```bash
python -m src.cli remember "Uso Windows y prefiero ejemplos paso a paso con PowerShell" --user alumno-01
```

Inspecciona los recuerdos del usuario:

```bash
python -m src.cli memories --user alumno-01
```

Repite la pregunta:

```bash
python -m src.cli ask "¿Cómo creo una rama y cambio a ella?" --user alumno-01
```

Ahora la preferencia aparecerá en `MEMORIA RECUPERADA`. Puedes cerrar la terminal, abrir otra, reactivar `.venv` y repetir el comando: el recuerdo seguirá allí porque está almacenado en Elasticsearch.

> [!NOTE]
> `alumno-01` es solo una etiqueta didáctica. No representa autenticación ni seguridad multiusuario real.

## 8. Generar una respuesta con un LLM — opcional

Añade una clave válida a `.env`:

```dotenv
OPENAI_API_KEY=tu_clave
OPENAI_MODEL=un_modelo_disponible_en_tu_cuenta
```

Después ejecuta:

```bash
python -m src.cli ask "¿Cómo creo una rama y cambio a ella?" --user alumno-01 --llm
```

El modelo recibe los pasajes y recuerdos recuperados. La instrucción del agente le pide usar *Pro Git* como fuente factual y la memoria únicamente para adaptar el estilo.

Este paso puede implicar coste y envía la pregunta y parte del contexto al proveedor del modelo. No utilices información personal real.

## 9. Borrar la memoria para repetir la demo

Primero comprueba qué recuerdos existen:

```bash
python -m src.cli memories --user alumno-01
```

Borra toda la memoria de forma interactiva:

```bash
python -m src.cli reset-memory
```

Escribe `BORRAR` cuando se solicite. Para una automatización controlada:

```bash
python -m src.cli reset-memory --confirm
```

Verifica el resultado:

```bash
python -m src.cli status
```

Resultado esperado:

```text
  progit: 112 documentos
  agent-memories: 0 documentos
```

`reset-memory` conserva el índice, su mapping y todo el contenido de *Pro Git*.

## Referencia rápida de comandos

| Comando | Función | Modifica datos |
|---|---|---|
| `python -m src.cli status` | Muestra versión y contadores | Solo crea índices ausentes |
| `python -m src.cli search "pregunta"` | Busca fragmentos de *Pro Git* | No, salvo crear índices ausentes |
| `python -m src.cli ask "pregunta"` | Muestra conocimiento y memoria recuperados | No, salvo crear índices ausentes |
| `python -m src.cli remember "texto"` | Guarda una preferencia explícita | Sí, memoria |
| `python -m src.cli memories` | Lista recuerdos del usuario | No, salvo crear índices ausentes |
| `python -m src.cli forget ID` | Elimina un recuerdo concreto | Sí, memoria |
| `python -m src.cli reset-memory` | Elimina todos los recuerdos | Sí, memoria |
| `python -m scripts.load_book` | Indexa el libro español | Sí, conocimiento |

Los comandos `remember`, `memories`, `forget` y `ask` aceptan `--user`; su valor predeterminado es `alumno-01`. `reset-memory` elimina todos los recuerdos y por eso no se limita a un usuario.

## Detener o reiniciar el laboratorio

Detener los contenedores conservando datos:

```bash
docker compose --env-file .env -f docker/compose.yaml down
```

Eliminar ambos índices del laboratorio:

```bash
python -m scripts.reset_demo --confirm
```

Eliminar contenedores y también el volumen persistente:

```bash
docker compose --env-file .env -f docker/compose.yaml down -v
```

> [!CAUTION]
> Los dos últimos comandos eliminan conocimiento y memoria. Para preparar otra demostración utiliza normalmente `reset-memory`, no `reset_demo` ni `down -v`.

## Ejecutar las pruebas

```bash
python -m pytest -q
```

Las pruebas unitarias utilizan mocks y no modifican Elasticsearch. Antes de una clase, sigue la lista de comprobación de `docs/guia_demo.md` para validar también el entorno Docker y los datos de la demostración.

## Problemas frecuentes

### «Elasticsearch no responde»

```bash
docker compose --env-file .env -f docker/compose.yaml ps
docker compose --env-file .env -f docker/compose.yaml logs elasticsearch
```

Espera a que el servicio esté saludable y vuelve a ejecutar `python -m src.cli status`.

### `ModuleNotFoundError`

Comprueba que `.venv` está activado e instala de nuevo las dependencias:

```bash
python -m pip install -r requirements.txt
python -m pip check
```

### La búsqueda no devuelve resultados útiles

- Formula la pregunta en español, porque el libro y su analizador están en español.
- Conserva los nombres de comandos Git, por ejemplo `branch`, `switch`, `reset` o `revert`.
- Comprueba que `progit` contiene documentos con `python -m src.cli status`.

### El índice todavía contiene el libro inglés

```bash
python -m scripts.load_book --recreate --confirm
```

## Material didáctico

- [`docs/guia_demo.md`](docs/guia_demo.md): ejecución completa de la demo en clase.
- [`docs/retos_alumnos.md`](docs/retos_alumnos.md): ejercicios de ampliación.

### 🏠 Reto para casa

La demostración es solo el punto de partida. Cuando termines la práctica, abre [`docs/retos_alumnos.md`](docs/retos_alumnos.md), elige al menos un reto e intenta resolverlo por tu cuenta. Añade pruebas para tu solución y documenta qué decisión tomaste: aprenderás mucho más modificando el agente que limitándote a ejecutar los comandos preparados.

## Decisiones de diseño y limitaciones

- Se utiliza **BM25** para mostrar recuperación léxica sin embeddings ni servicios adicionales.
- La memoria se añade mediante `remember`; no se extrae automáticamente del diálogo.
- El recuperador de memoria es deliberadamente sencillo y no incluye caducidad, cifrado, revisión de hechos ni autorización robusta.
- El indexador AsciiDoc es ligero: algunas macros o tablas pueden permanecer en el texto.
- No hay interfaz web de chat, orquestación multiagente ni embeddings de serie.

## Atribución y licencias

El contenido de **Pro Git (segunda edición)** pertenece a Scott Chacon, Ben Straub y sus colaboradores, bajo licencia **CC BY-NC-SA 3.0**. El texto no se distribuye dentro del proyecto: el cargador lo obtiene del [repositorio oficial de la traducción española](https://github.com/progit/progit2-es) y conserva enlaces a los archivos de origen. También puedes consultar el [libro web en español](https://git-scm.com/book/es/v2).

El código de este laboratorio se ofrece bajo licencia MIT. Consulta [`LICENSE`](LICENSE). La licencia del código no sustituye la licencia del libro.

## Fuentes técnicas

- [Instalar Elasticsearch con Docker](https://www.elastic.co/docs/deploy-manage/deploy/self-managed/install-elasticsearch-docker-basic)
- [Cliente oficial de Elasticsearch para Python](https://www.elastic.co/docs/reference/elasticsearch/clients/python)
- [OpenAI SDK para Python](https://developers.openai.com/api/reference/python)
