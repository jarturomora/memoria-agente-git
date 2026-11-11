"""Configuración compartida para la demo local."""
import os
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # tests can import helper modules without optional dependencies
ES_URL = os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")
BOOK_INDEX = os.getenv("ELASTICSEARCH_INDEX", "progit")
MEMORY_INDEX = os.getenv("MEMORY_INDEX", "agent-memories")
