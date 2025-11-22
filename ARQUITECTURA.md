# Arquitectura del Sistema

## Descripción General

Sistema de chatbot con arquitectura RAG (Retrieval-Augmented Generation) para consultas sobre datasets de ventas.

## Diagrama de Arquitectura

```
┌──────────────┐
│   Usuario    │
│  (Browser)   │
└──────┬───────┘
       │
       │ HTTP
       ▼
┌──────────────────────────────────────┐
│         Frontend (Flutter Web)        │
│  - UI tipo chat                       │
│  - Llamadas HTTP al backend           │
│  - Visualización de respuestas        │
└──────────────┬───────────────────────┘
               │
               │ REST API
               ▼
┌──────────────────────────────────────┐
│         Backend (FastAPI)             │
│  ┌────────────────────────────────┐  │
│  │     API Layer                  │  │
│  │  /api/chat                     │  │
│  │  /api/health                   │  │
│  │  /api/rebuild-index            │  │
│  └────────────┬───────────────────┘  │
│               │                       │
│  ┌────────────▼───────────────────┐  │
│  │     RAG Pipeline               │  │
│  │  1. Query → Embeddings         │  │
│  │  2. Vector Search (FAISS)      │  │
│  │  3. Retrieve Documents         │  │
│  │  4. Build Prompt + Context     │  │
│  │  5. LLM Generation             │  │
│  └────────────┬───────────────────┘  │
│               │                       │
└───────────────┼───────────────────────┘
                │
                ▼
         ┌──────────────┐
         │   Ollama     │
         │   (llama3)   │
         └──────────────┘
```

## Tecnologías Clave

| Componente | Tecnología | Versión | Propósito |
|------------|-----------|---------|-----------|
| Frontend | Flutter | 3.x | UI Web |
| Backend | FastAPI | 0.104+ | API REST |
| RAG Framework | LangChain | 0.1+ | Orquestación RAG |
| Vector Store | FAISS | 1.7+ | Búsqueda vectorial |
| LLM Server | Ollama | latest | Modelos locales |
| LLM Model | llama3 | latest | Generación de texto |
| Data Processing | Pandas | 2.1+ | Procesamiento Excel |
| Containerization | Docker | latest | Deployment |

## Seguridad

- CORS configurado en backend
- Sin autenticación (MVP, agregar en producción)
- Vector store local (sin envío de datos a cloud)
- LLM local (privacidad de datos)
- Validación de inputs en API

## Limitaciones Actuales

1. **Sin autenticación**: Acceso abierto
2. **Single-user**: No multi-tenancy
3. **Embeddings lentos**: Primera vez toma tiempo

## Mejoras Futuras

1. Implementar autenticación (JWT)
2. Cache de respuestas frecuentes
3. Streaming de respuestas (SSE)
4. Métricas y monitoring (Prometheus)
5. Rate limiting
6. Multi-idioma
