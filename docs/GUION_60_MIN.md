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
python -m src.cli search "crear y fusionar ramas"
python -m src.cli ask "¿Cuál es la diferencia entre reset y revert?"
python -m src.cli remember "Utilizo Windows y prefiero explicaciones paso a paso con PowerShell"
python -m src.cli memories
# Cerrar la terminal; abrir otra y activar el mismo entorno virtual
python -m src.cli ask "¿Cómo creo una nueva rama de Git?"
# Si hay clave de API y conexión:
python -m src.cli ask "¿Cómo creo una nueva rama de Git?" --llm
```

**Importante:** El corpus y su analizador lingüístico están en español, por lo que las consultas de la demostración deben formularse en español. Los comandos de Git (`branch`, `switch`, `reset`, etc.) se conservan tal como aparecen en el libro y también son términos de búsqueda útiles.

## Respaldo si falla Internet o el LLM

`ask` sin `--llm` siempre muestra el conocimiento y los recuerdos recuperados, sin conexión externa. Si el repositorio ya se clonó y Elasticsearch está iniciado, no requiere Internet.

## Mensaje final

Un agente no adquiere nuevas capacidades porque el modelo se haya reentrenado, sino porque la aplicación dispone de memoria recuperable y controlada. Recordar no equivale a aprender los parámetros del modelo.
