from fastapi import APIRouter
from app.models import HealthResponse, RunningModelResponse
import httpx
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/ollama-health", response_model=HealthResponse)
async def health_check():
    """Endpoint de health check."""
    from app.main import app_state
    
    ollama_available = False
    
    try:
        if app_state.get('ollama_base_url'):
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{app_state['ollama_base_url']}/api/tags")
                ollama_available = response.status_code == 200
    except:
        pass
    
    return HealthResponse(
        status="ok",
        vectorstore_loaded=app_state.get('vectorstore') is not None,
        ollama_available=ollama_available
    )



@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Endpoint de health check."""
  
    return HealthResponse(
        status="ok",
    )

@router.get("/model", response_model=RunningModelResponse)
async def health_check():
    """Endpoint de health check."""
    from app.main import app_state
    
    ollama_available = ""
    
    ollama_available = app_state.get('ollama_model', "")

    return RunningModelResponse(
        model=ollama_available,
    )
    
