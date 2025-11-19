from fastapi import APIRouter, HTTPException
from app.excel_loader import ExcelLoader
from app.rag.documents import dataframes_to_documents
from app.rag.vectorstore import rebuild_vectorstore
from app.rag.embeddings import get_embedding_model
from app.rag.chain import get_rag_chain, get_ollama_llm
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/rebuild-index")
async def rebuild_index():
    """Reconstruye el índice vectorial desde el Excel."""
    from app.main import app_state
    from app.config import get_settings
    
    settings = get_settings()
    
    try:
        logger.info("Recargando Excel...")
        loader = ExcelLoader(settings.excel_path)
        dataframes = loader.load()
        
        logger.info("Convirtiendo a documentos...")
        documents = dataframes_to_documents(dataframes)
        
        if not documents:
            raise HTTPException(
                status_code=400,
                detail="No se pudieron generar documentos desde el Excel"
            )
        
        embeddings = get_embedding_model(
            settings.ollama_base_url,
            settings.embedding_model
        )
        
        logger.info("Reconstruyendo vector store...")
        vectorstore = rebuild_vectorstore(
            documents,
            embeddings,
            settings.vectorstore_path
        )
        
        llm = get_ollama_llm(settings.ollama_base_url, settings.ollama_model)
        chain, retriever = get_rag_chain(vectorstore, llm)
        
        app_state['vectorstore'] = vectorstore
        app_state['chain'] = chain
        app_state['retriever'] = retriever
        
        return {
            "status": "success",
            "message": f"Índice reconstruido con {len(documents)} documentos"
        }
        
    except Exception as e:
        logger.error(f"Error al reconstruir índice: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error al reconstruir índice: {str(e)}"
        )
