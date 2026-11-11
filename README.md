# Más allá del contexto: memoria para agentes de IA con Elasticsearch

Laboratorio de conferencia universitaria · Python + Docker + Elasticsearch + Pro Git.

**Idea:** demostrar por separado recuperación documental (RAG) y memoria persistente de un agente. El modo base **no requiere API de LLM**. El modo `--llm` es opcional y puede conllevar costes de API.

## Requisitos

- Docker Desktop con motor WSL2 (Windows), o Docker Engine + Compose (Linux/macOS).
- Python 3.10 o superior, Git, al menos 6–8 GB de memoria disponible para Docker y el sistema.
- Acceso a Internet la primera vez, para las imágenes Docker, dependencias y descarga del libro.
- Puertos locales libres: 9200 y 5601.

> Seguridad: los servicios están **sin autenticación** y ligados a `127.0.0.1`. Úsalo **únicamente en tu ordenador**, nunca en un servidor público. Docker Compose persiste los datos en un volumen.

## Inicio rápido (Windows PowerShell)

Desde la raíz del proyecto:

```powershell
Copy-Item .env.example .env
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
docker compose --env-file .env -f docker/compose.yaml up -d
python -m src.cli status
python -m scripts.load_book
python -m src.cli search "git branch merge"
```

Si PowerShell restringe la activación, abre una terminal CMD o ejecuta `Set-ExecutionPolicy -Scope Process Bypass` (solo para esa sesión) antes de activar el entorno.

## Inicio rápido (macOS / Linux / WSL)

```bash
cp .env.example .env
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
docker compose --env-file .env -f docker/compose.yaml up -d
python -m src.cli status
python -m scripts.load_book
python -m src.cli search "git branch merge"
```

**Primera carga:** `load_book` clona `progit/progit2` en `data/progit2` (esta carpeta no se incluye en el ZIP). Indexa los capítulos 02 y 03 en inglés con un parser ligero de AsciiDoc. Al repetir el comando se actualizan los mismos fragmentos, sin duplicarlos (ID estable por archivo y posición). Los resultados pueden variar si cambia el repositorio original.

## Demostración paso a paso

```bash
# Recuperación de documentación
python -m src.cli search "git branch merge"

# Mostrar el contexto que recibiría un LLM (sin coste ni clave)
python -m src.cli ask "How do I create and switch branches?"

# Guardar una preferencia explícita
python -m src.cli remember "Uso Windows; prefiero ejemplos paso a paso con PowerShell" --user alumno-01

# Comprobar que existe
python -m src.cli memories --user alumno-01

# Cerrar terminal; abrir una nueva y reactivar .venv
python -m src.cli ask "How do I create a Git branch?" --user alumno-01
```

La opción `ask` por defecto **no genera una respuesta en lenguaje natural**. Enseña los pasajes y recuerdos realmente recuperados, y permite validar el ejercicio sin LLM.

### Opcional: respuestas generadas con un LLM

Rellena `OPENAI_API_KEY` en `.env` y, si necesitas, cambia `OPENAI_MODEL`. El modelo configurado debe existir y estar disponible en tu cuenta API. La llamada se realiza al proveedor del modelo: parte del contexto recuperado se envía a su servicio. No uses datos personales auténticos.

```bash
python -m src.cli ask "How do I create a Git branch?" --user alumno-01 --llm
```

Este ejemplo usa la API Responses del SDK oficial de OpenAI. Las credenciales se mantienen fuera de Git con `.gitignore`.

### Inspeccionar los índices

- Elasticsearch: http://localhost:9200
- Kibana: http://localhost:5601
- Consultas listas para Dev Tools: [`docs/DEVTOOLS.md`](docs/DEVTOOLS.md)

### Eliminar recuerdos o reiniciar

```bash
python -m src.cli memories --user alumno-01
python -m src.cli forget ID_DEL_RECUERDO --user alumno-01
# Esto borra ambos índices del laboratorio:
python -m scripts.reset_demo --confirm
# Detener contenedores sin borrar datos:
docker compose --env-file .env -f docker/compose.yaml down
# Borrar también el volumen persistente (IRREVERSIBLE):
docker compose --env-file .env -f docker/compose.yaml down -v
```

## Pruebas

```bash
python -m pytest -q
```

Las pruebas unitarias no necesitan Elasticsearch instalado. La ejecución integral con Docker **no se ha validado automáticamente al generar este material**; comprueba `status`, `load_book` y las consultas antes de la charla.

## Material didáctico

- [`docs/GUION_60_MIN.md`](docs/GUION_60_MIN.md): presentación y comandos en vivo.
- [`docs/RETOS_ALUMNOS.md`](docs/RETOS_ALUMNOS.md): ejercicios de ampliación.
- [`docs/DEVTOOLS.md`](docs/DEVTOOLS.md): consultas para Kibana.

## Decisiones de diseño y limitaciones

- **BM25** para una primera demo sin modelos de embeddings ni servicios de inferencia adicionales.
- **Dos índices independientes**: `progit` (documentos del libro) y `agent-memories` (recuerdos).
- La memoria se añade con `remember`, no se extrae automáticamente del diálogo: el control y consentimiento son explícitos.
- El recuperador de memoria es un ejemplo mínimo: prioriza coincidencia lexical y, de forma acotada, recuerdos recientes de un usuario. No incluye caducidad, revisión de hechos, cifrado ni autorización robusta.
- Los identificadores `--user` son etiquetas de demo, **no autenticación real**.
- El indexador AsciiDoc es intencionadamente simplificado: algunas macros/tablas pueden quedar en el texto. La referencia a GitHub enlaza al documento fuente.
- No hay interfaz web de chat, orquestación multiagente ni embeddings de serie.

## Atribución y licencia del corpus

El contenido de **Pro Git (segunda edición)** pertenece a sus autores, Scott Chacon y Ben Straub, y colaboradores, bajo **CC BY-NC-SA 3.0**. No incluimos el texto del libro en este ZIP: el script lo obtiene de su [repositorio oficial](https://github.com/progit/progit2) y conserva enlaces de origen. [Libro web](https://git-scm.com/book/en/v2).

El código original de este laboratorio se ofrece con licencia MIT (véase `LICENSE`). La licencia del código no sustituye la licencia del contenido del libro.

## Fuentes técnicas

- [Elastic: instalación Docker](https://www.elastic.co/docs/deploy-manage/deploy/self-managed/install-elasticsearch-docker-basic)
- [Cliente oficial Python Elasticsearch](https://www.elastic.co/docs/reference/elasticsearch/clients/python)
- [OpenAI SDK Python](https://developers.openai.com/api/reference/python)
