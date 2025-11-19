from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import sys

from app.config import get_settings
from app.excel_loader import ExcelLoader
from app.rag.documents import dataframes_to_documents
from app.rag.embeddings import get_embedding_model
from app.rag.vectorstore import load_vectorstore_or_build
from app.rag.chain import get_rag_chain, get_ollama_llm
from app.api import health, chat, admin

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)

logger = logging.getLogger(__name__)

app_state = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    
    logger.info("Iniciando aplicación...")
    logger.info(f"Configuración: {settings.dict()}")
    
    try:
        # Cargar Excel
        logger.info(f"Cargando Excel desde {settings.excel_path}")
        loader = ExcelLoader(settings.excel_path)
        dataframes = loader.load()
        
        # Convertir a documentos
        logger.info("Convirtiendo datos a documentos...")
        documents = dataframes_to_documents(dataframes)
        logger.info(f"Generados {len(documents)} documentos")
        
        if not documents:
            logger.error("No se generaron documentos desde el Excel")
            raise Exception("No se pudieron generar documentos")
        
        # Obtener modelo de embeddings
        logger.info("Inicializando embeddings...")
        embeddings = get_embedding_model()
        
        # Cargar o construir vector store
        logger.info("Cargando/construyendo vector store...")
        vectorstore = load_vectorstore_or_build(
            documents,
            embeddings,
            settings.vectorstore_path
        )
        
        # Crear LLM
        logger.info("Inicializando LLM de Ollama...")
        llm = get_ollama_llm(settings.ollama_base_url, settings.ollama_model)
        
        # Crear RAG chain
        logger.info("Construyendo RAG chain...")
        chain, retriever = get_rag_chain(vectorstore, llm)
        
        # Guardar en estado global
        app_state['vectorstore'] = vectorstore
        app_state['chain'] = chain
        app_state['retriever'] = retriever
        app_state['ollama_base_url'] = settings.ollama_base_url
        app_state['settings'] = settings
        
        logger.info("Aplicación iniciada correctamente")
        
        yield
        
    except Exception as e:
        logger.error(f"Error al iniciar aplicación: {e}")
        # Continuar de todos modos para que health check pueda responder
        yield
    
    # Cleanup
    logger.info("Cerrando aplicación...")


# Crear aplicación FastAPI
app = FastAPI(
    title="Retail 360 Chatbot API",
    description="API RAG para consultas sobre dataset de ventas",
    version="1.0.0",
    lifespan=lifespan
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar dominios permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Montar routers
app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(chat.router, prefix="/api", tags=["chat"])
app.include_router(admin.router, prefix="/api", tags=["admin"])


@app.get("/")
async def root():
    """Endpoint raíz."""
    return {
        "message": "Retail 360 Chatbot API",
        "version": "1.0.0",
        "docs": "/docs"
    }
