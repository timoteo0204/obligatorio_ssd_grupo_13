from langchain_community.vectorstores import FAISS
from langchain.schema import Document
from langchain.embeddings.base import Embeddings
from typing import List, Optional
import os
import pickle
import logging

logger = logging.getLogger(__name__)


def load_vectorstore_or_build(
    documents: List[Document],
    embeddings: Embeddings,
    vectorstore_path: str
) -> FAISS:
    """
    Carga el vector store desde disco o lo construye si no existe.
    """
    index_file = os.path.join(vectorstore_path, "index.faiss")
    pkl_file = os.path.join(vectorstore_path, "index.pkl")
    
    # Intentar cargar desde disco
    if os.path.exists(index_file) and os.path.exists(pkl_file):
        try:
            logger.info(f"Cargando vector store desde {vectorstore_path}")
            vectorstore = FAISS.load_local(
                vectorstore_path,
                embeddings,
                allow_dangerous_deserialization=True
            )
            logger.info("Vector store cargado exitosamente")
            return vectorstore
        except Exception as e:
            logger.warning(f"Error al cargar vector store: {e}. Reconstruyendo...")
    
    # Construir nuevo vector store
    logger.info(f"Construyendo nuevo vector store con {len(documents)} documentos")
    vectorstore = FAISS.from_documents(documents, embeddings)
    
    # Guardar en disco
    save_vectorstore(vectorstore, vectorstore_path)
    
    return vectorstore


def save_vectorstore(vectorstore: FAISS, vectorstore_path: str):
    """Guarda el vector store en disco."""
    try:
        os.makedirs(vectorstore_path, exist_ok=True)
        vectorstore.save_local(vectorstore_path)
        logger.info(f"Vector store guardado en {vectorstore_path}")
    except Exception as e:
        logger.error(f"Error al guardar vector store: {e}")


def rebuild_vectorstore(
    documents: List[Document],
    embeddings: Embeddings,
    vectorstore_path: str
) -> FAISS:
    """
    Reconstruye el vector store desde cero.
    """
    logger.info(f"Reconstruyendo vector store con {len(documents)} documentos")
    vectorstore = FAISS.from_documents(documents, embeddings)
    save_vectorstore(vectorstore, vectorstore_path)
    return vectorstore
