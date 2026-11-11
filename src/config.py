"""Configuración compartida por todos los módulos del laboratorio.

Las variables de entorno permiten cambiar URLs o nombres de índices sin tocar
el código. Los valores predeterminados están pensados para Docker Compose.
"""

import os

# ``python-dotenv`` carga las variables escritas en ``.env``. El bloque
# ``try`` mantiene importables los módulos auxiliares en entornos mínimos.
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass  # Las pruebas de helpers pueden ejecutarse sin esta dependencia.

# URL HTTP publicada por el contenedor local de Elasticsearch.
ES_URL = os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")

# Se usan índices separados para no confundir conocimiento con recuerdos.
# ``ELASTICSEARCH_INDEX`` se conserva por compatibilidad con la configuración
# inicial del proyecto.
BOOK_INDEX = os.getenv("ELASTICSEARCH_INDEX", "progit")
MEMORY_INDEX = os.getenv("MEMORY_INDEX", "agent-memories")
