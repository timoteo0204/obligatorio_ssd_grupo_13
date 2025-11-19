from langchain.vectorstores import FAISS
from langchain.prompts import ChatPromptTemplate
from langchain.schema.runnable import RunnablePassthrough
from langchain.schema.output_parser import StrOutputParser
from langchain_community.llms import Ollama
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


def get_ollama_llm(base_url: str, model: str) -> Ollama:
    """Crea una instancia del LLM de Ollama."""
    return Ollama(
        base_url=base_url,
        model=model,
        temperature=0.1,  # Baja temperatura para respuestas más precisas
    )


def get_rag_chain(vectorstore: FAISS, llm: Ollama):
    """
    Construye la chain RAG completa.
    """
    # Crear retriever
    retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 5}
    )
    
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
    
    # Función para formatear documentos
    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)
    
    # Construir chain
    chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    
    return chain, retriever


def query_rag(
    question: str,
    chain,
    retriever,
    history: List[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Ejecuta una consulta sobre el sistema RAG.
    
    Returns:
        Dict con 'answer' y 'sources'
    """
    try:
        # Obtener documentos relevantes
        docs = retriever.get_relevant_documents(question)
        
        # Ejecutar chain
        answer = chain.invoke(question)
        
        # Extraer sources de los documentos
        sources = []
        for doc in docs:
            source = {
                'id': doc.metadata.get('venta_id') or doc.metadata.get('cliente') or doc.metadata.get('producto'),
                'type': doc.metadata.get('type'),
                'metadata': doc.metadata
            }
            sources.append(source)
        
        return {
            'answer': answer.strip(),
            'sources': sources
        }
        
    except Exception as e:
        logger.error(f"Error en query_rag: {e}")
        raise
