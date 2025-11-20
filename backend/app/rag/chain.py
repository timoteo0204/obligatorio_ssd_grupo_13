from langchain.vectorstores import FAISS
from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser
from langchain_community.llms import Ollama
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


def get_ollama_llm(base_url: str, model: str) -> Ollama:
    """Crea una instancia del LLM de Ollama."""
    return Ollama(
        base_url=base_url,
        model=model,
        temperature=0.1,  # Baja temperatura para respuestas más precisas
    )


def format_docs(docs: List[Any]) -> str:
    return "\n\n".join(doc.page_content for doc in docs)


def get_rag_chain(vectorstore: FAISS, llm: Ollama):
    """
    Construye la chain RAG para recibir contexto explícito.
    """
    # Crear retriever que será usado externamente para armar el contexto
    retriever = vectorstore.as_retriever(
        search_type="similarity",
    )

    # Prompt template (requiere variables: context, question)
    template = """Sos un asistente que responde sobre un dataset de ventas de Retail 360.

Usa EXCLUSIVAMENTE la información del siguiente CONTEXTO para responder la pregunta.
Si la respuesta no está en el contexto, respondé explícitamente "No tengo suficiente información en los datos para responder esa pregunta."
NO inventes números, clientes, productos ni datos que no estén en el contexto.

CONTEXTO:
{context}

PREGUNTA: {question}

RESPUESTA:"""

    prompt = ChatPromptTemplate.from_template(template)

    # La chain ahora solo formatea el prompt y ejecuta el LLM
    chain = (
        prompt
        | llm
        | StrOutputParser()
    )

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
    try:
        # Recuperación explícita para construir el contexto
        docs = []
        if retriever is not None:
            docs = retriever.get_relevant_documents(question)

        context_str = format_docs(docs) if docs else ""

        # Ejecutar chain con contexto y pregunta explícitos
        answer = chain.invoke({
            "context": context_str,
            "question": question
        })

        return {
            'answer': answer.strip(),
        }
        
    except Exception as e:
        logger.error(f"Error en query_rag: {e}")
        raise
