import logging
from chromadb import HttpClient
from chromadb.utils import embedding_functions
from src.config.config import get_settings

# Configurar el logger
logger = logging.getLogger('__name__')
logger.setLevel(logging.INFO)

_SETTINGS = get_settings()

client = HttpClient(host=_SETTINGS.vector_database_host, port=_SETTINGS.vector_database_port)
embedding_func = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
)

collection = client.get_or_create_collection(
    name="news", 
    embedding_function=embedding_func, 
    metadata={"hnsw:space": "cosine"}
)

def get_chroma_db_client():
    return collection

if __name__ == "__main__":
    try:
        logger.info("Iniciando conexión a ChromaDB")
        test_collection = get_chroma_db_client()
        logger.info("Conexión a ChromaDB establecida correctamente.")
    except Exception as e:
        logger.error(f"Error al conectar con ChromaDB: {e}")