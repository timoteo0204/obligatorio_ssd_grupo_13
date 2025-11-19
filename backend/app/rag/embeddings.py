from langchain.embeddings.base import Embeddings
from langchain_community.embeddings import HuggingFaceEmbeddings
from typing import List
import logging

logger = logging.getLogger(__name__)


def get_embedding_model(model_name: str = "sentence-transformers/all-MiniLM-L6-v2") -> Embeddings:
    """
    Factory para obtener el modelo de embeddings.
    Usa HuggingFace embeddings locales.
    
    Args:
        model_name: Nombre del modelo de HuggingFace
    
    Returns:
        Embeddings: Modelo de embeddings configurado
    """
    try:
        embeddings = HuggingFaceEmbeddings(
            model_name=model_name,
            model_kwargs={'device': 'cpu'},  
            encode_kwargs={'normalize_embeddings': True}
        )
        logger.info(f"Modelo de embeddings cargado: {model_name}")
        return embeddings
    except Exception as e:
        logger.error(f"Error al cargar modelo de embeddings: {e}")
        raise
