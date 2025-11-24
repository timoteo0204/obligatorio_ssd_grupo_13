from fastapi import APIRouter, HTTPException
from app.models import ChatRequest, ChatResponse, Source
from app.rag.chain import query_rag
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Endpoint para hacer preguntas al chatbot."""
    import time
    from app.main import app_state
    
    # Log incoming request
    logger.info(f"Incoming chat request - Question: {request.question[:100]}...")
    start_time = time.time()
    
    if not app_state.get('chain') or not app_state.get('retriever'):
        raise HTTPException(
            status_code=503,
            detail="El sistema RAG no está inicializado. Intenta más tarde."
        )
    
    try:
        result = await  query_rag(
            question=request.question,
            chain=app_state['chain'],
            retriever=app_state['retriever']
        )
        
        
        response = ChatResponse(
            answer=result['answer'],
            sources=result.get('sources', [])
        )
        
        # Log total request time
        total_time = time.time() - start_time
        logger.info(f"Chat request completed in {total_time:.2f}s with {len(response.sources)} sources")
        
        return response
        
    except Exception as e:
        logger.error(f"Error en chat endpoint: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error al procesar la consulta: {str(e)}"
        )
