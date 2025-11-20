from langchain.vectorstores import FAISS
from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser
from langchain_community.llms import Ollama
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


def get_ollama_llm(base_url: str, model: str) -> Ollama:
    """Crea una instancia del LLM de Ollama."""
    logger.info(f"Creating Ollama LLM instance - base_url: {base_url}, model: {model}")
    llm = Ollama(
        base_url=base_url,
        model=model,
        temperature=0.1,  # Baja temperatura para respuestas más precisas
    )
    logger.info("Ollama LLM instance created successfully")
    return llm


def format_docs(docs: List[Any]) -> str:
    return "\n\n".join(doc.page_content for doc in docs)


def get_rag_chain(vectorstore: FAISS, llm: Ollama):
    """
    Construye la chain RAG para recibir contexto explícito.
    """
    logger.info("Building RAG chain...")
    
    # Crear retriever
    logger.info("Creating retriever with k=5 similarity search...")
    retriever = vectorstore.as_retriever(
        search_type="similarity",
    )
    logger.info("Retriever created successfully")
    
    # Prompt template
    template = """Sos un asistente que responde sobre un dataset de ventas de Retail 360.

Usa EXCLUSIVAMENTE la información del siguiente CONTEXTO para responder la pregunta.
Si la respuesta no está en el contexto, respondé explícitamente "No tengo suficiente información en los datos para responder esa pregunta."
NO inventes números, clientes, productos ni datos que no estén en el contexto.

CONTEXTO:
{context}

PREGUNTA: {question}

RESPUESTA:"""

    prompt = ChatPromptTemplate.from_template(template)
    logger.info("Prompt template configured")
    
    # Función para formatear documentos
    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)
    
    # Construir chain
    logger.info("Assembling RAG chain components...")
    chain = (
        prompt
        | llm
        | StrOutputParser()
    )
    logger.info("RAG chain built successfully")
    
    return chain, retriever


def query_rag(
    question: str,
    chain,
    retriever: Optional[Any] = None,
    history: List[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Ejecuta una consulta sobre el sistema RAG.

    Nota:
        La `chain` construida por `get_rag_chain` ya incluye un retriever interno
        que usa la pregunta como entrada para recuperar documentos y formar el
        contexto del prompt. El parámetro `retriever` aquí es opcional y se usa
        únicamente si necesitás devolver `sources` consistentes junto con la
        respuesta. Si no se provee, se omiten las fuentes.

    Returns:
        Dict con 'answer' y 'sources'
    """
    import time
    
    try:
        logger.info(f"Starting query_rag for question: {question[:100]}...")
        
        # Obtener documentos relevantes
        logger.info("Step 1: Retrieving relevant documents...")
        retrieval_start = time.time()
    
        if retriever is not None:
            docs = retriever.get_relevant_documents(question)
        retrieval_time = time.time() - retrieval_start
        logger.info(f"Step 1 completed: Retrieved {len(docs)} documents in {retrieval_time:.2f}s")
        

        logger.info(f"Formatting documents for context...")
        context_str = format_docs(docs) if docs else ""
        logger.info("Context string formatted")

        # Ejecutar chain
        logger.info("Step 2: Invoking LLM chain...")
        chain_start = time.time()
        answer = chain.invoke({
            "context": context_str,
            "question": question
        })
        chain_time = time.time() - chain_start
        logger.info(f"Step 2 completed: LLM chain invoked in {chain_time:.2f}s")
        

        return {
            'answer': answer.strip(),
        }
        
    except Exception as e:
        logger.error(f"Error en query_rag: {e}")
        raise
