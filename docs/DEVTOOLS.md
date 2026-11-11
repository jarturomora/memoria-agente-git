# Consultas reproducibles desde Kibana Dev Tools

Abre http://localhost:5601/app/dev_tools#/console tras iniciar Docker.

```http
GET /_cluster/health
GET /progit/_count
GET /agent-memories/_count

GET /progit/_search
{
  "size": 3,
  "query": {
    "multi_match": {
      "query": "crear y fusionar ramas",
      "fields": ["title^3", "section^2", "content"]
    }
  },
  "_source": ["title", "section", "content", "source"]
}

GET /agent-memories/_search
{
  "query": {"term": {"user_id": "alumno-01"}}
}
```

**Nota:** Los recuerdos pueden incluir información personal. Usa únicamente datos ficticios en la charla.
