# Guion de conferencia — 60 minutos

Título: **Más allá del contexto: construyendo la memoria de los agentes de IA**.

| Minutos | Bloque | Acción visible |
|---|---|---|
| 00–06 | El problema del contexto | Pregunta sobre Git sin memoria persistente |
| 06–15 | Tipos de memoria | Diferencias entre contexto, conocimiento y recuerdos |
| 15–27 | Recuperación | `search` + inspección de `progit` en Kibana |
| 27–36 | RAG | `ask` y opcionalmente `ask --llm` |
| 36–51 | Memoria | `remember`; cerrar terminal; nueva sesión; `ask` |
| 51–57 | Experimento | `forget`, comparar respuestas y discutir privacidad |
| 57–60 | Conclusiones | QR del repositorio y preguntas |

## Orden de comandos para la demostración

Preparación **antes** de entrar al aula:

```bash
docker compose --env-file .env -f docker/compose.yaml up -d
python -m scripts.load_book
python -m src.cli status
```

En directo:

```bash
python -m src.cli search "git branch merge"
python -m src.cli ask "What is the difference between reset and revert?"
python -m src.cli remember "Utilizo Windows y prefiero explicaciones paso a paso con PowerShell"
python -m src.cli memories
# Cerrar la terminal; abrir otra y activar el mismo entorno virtual
python -m src.cli ask "How do I create a new Git branch?"
# Si hay clave de API y conexión:
python -m src.cli ask "How do I create a new Git branch?" --llm
```

**Importante:** Las búsquedas textuales del libro funcionan mejor si las preguntas incluyen términos en inglés, ya que el corpus original está en inglés. Para dudas en español, la generación puede responder en español usando los pasajes en inglés; las consultas BM25 siguen dependiendo de coincidencias léxicas. Si quieres probar consulta en español con mayor calidad, añade posteriormente traducción de consultas o búsqueda semántica.

## Respaldo si falla Internet o el LLM

`ask` sin `--llm` siempre muestra el conocimiento y los recuerdos recuperados, sin conexión externa. Si el repositorio ya se clonó y Elasticsearch está iniciado, no requiere Internet.

## Mensaje final

Un agente no adquiere nuevas capacidades porque el modelo se haya reentrenado, sino porque la aplicación dispone de memoria recuperable y controlada. Recordar no equivale a aprender los parámetros del modelo.
