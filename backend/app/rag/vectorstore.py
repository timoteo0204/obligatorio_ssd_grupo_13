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
    import time
    
    index_file = os.path.join(vectorstore_path, "index.faiss")
    pkl_file = os.path.join(vectorstore_path, "index.pkl")
    
    # Intentar cargar desde disco
    if os.path.exists(index_file) and os.path.exists(pkl_file):
        try:
            logger.info(f"Attempting to load vector store from {vectorstore_path}")
            start_time = time.time()
            
            vectorstore = FAISS.load_local(
                vectorstore_path,
                embeddings,
                allow_dangerous_deserialization=True
            )
            
            load_time = time.time() - start_time
            logger.info(f"Vector store loaded successfully from disk in {load_time:.2f}s")
            return vectorstore
        except Exception as e:
            logger.warning(f"Error al cargar vector store: {e}. Reconstruyendo...")
    
    # Construir nuevo vector store
    logger.info(f"Building new vector store with {len(documents)} documents")
    start_time = time.time()
    
    vectorstore = FAISS.from_documents(documents, embeddings)
    
    build_time = time.time() - start_time
    logger.info(f"Vector store built successfully in {build_time:.2f}s")
    
    # Guardar en disco
    save_vectorstore(vectorstore, vectorstore_path)
    
    return vectorstore


def save_vectorstore(vectorstore: FAISS, vectorstore_path: str):
    """Guarda el vector store en disco."""
    import time
    
    try:
        logger.info(f"Saving vector store to {vectorstore_path}")
        start_time = time.time()
        
        os.makedirs(vectorstore_path, exist_ok=True)
        vectorstore.save_local(vectorstore_path)
        
        save_time = time.time() - start_time
        logger.info(f"Vector store saved successfully in {save_time:.2f}s")
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
    import time
    
    logger.info(f"Rebuilding vector store from scratch with {len(documents)} documents")
    start_time = time.time()
    
    vectorstore = FAISS.from_documents(documents, embeddings)
    
    build_time = time.time() - start_time
    logger.info(f"Vector store rebuilt in {build_time:.2f}s")
    
    save_vectorstore(vectorstore, vectorstore_path)
    return vectorstore
