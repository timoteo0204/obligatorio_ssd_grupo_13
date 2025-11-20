from fastapi import APIRouter, HTTPException
from app.models import ChatRequest, ChatResponse, Source
from app.rag.chain import query_rag
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Endpoint para hacer preguntas al chatbot."""
    from app.main import app_state
    
    if not app_state.get('chain') or not app_state.get('retriever'):
        raise HTTPException(
            status_code=503,
            detail="El sistema RAG no está inicializado. Intenta más tarde."
        )
    
    try:
        result = query_rag(
            question=request.question,
            chain=app_state['chain'],
            retriever=app_state['retriever']
        )
        
        
        return ChatResponse(
            answer=result['answer'],
        )
        
    except Exception as e:
        logger.error(f"Error en chat endpoint: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error al procesar la consulta: {str(e)}"
        )
