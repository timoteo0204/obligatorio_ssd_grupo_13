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

## Componentes

### 1. Frontend (Flutter Web)
- **Tecnología**: Flutter 3.x, Dart
- **Responsabilidades**:
  - Interfaz de usuario tipo chat
  - Envío de preguntas al backend
  - Visualización de respuestas y fuentes
  - Manejo de estado de conversación

### 2. Backend (FastAPI + Python)
- **Tecnología**: Python 3.11+, FastAPI, LangChain
- **Componentes principales**:

#### a. API Layer (`app/api/`)
- **chat.py**: Endpoint principal para consultas
- **health.py**: Health checks del sistema
- **admin.py**: Administración (rebuild index)

#### b. RAG Pipeline (`app/rag/`)
- **documents.py**: Conversión de datos a documentos LangChain
  - Documentos por venta individual
  - Documentos agregados por cliente
  - Documentos agregados por producto
  - Documentos agregados por mes
  
- **embeddings.py**: Generación de embeddings
  - Conexión con Ollama para embeddings
  - Wrapper de LangChain Embeddings

- **vectorstore.py**: Gestión del índice vectorial
  - FAISS como vector store
  - Persistencia en disco
  - Carga/reconstrucción de índice

- **chain.py**: Construcción de la RAG chain
  - Retriever de documentos similares
  - Prompt engineering
  - Integración con LLM
  - Post-procesamiento de respuestas

#### c. Data Layer
- **excel_loader.py**: Carga y procesamiento de Excel
  - Lectura de múltiples hojas
  - Normalización de datos
  - Transformaciones de columnas

### 3. Ollama (Servidor LLM)
- **Tecnología**: Ollama
- **Modelo**: llama3 (configurable)
- **Responsabilidades**:
  - Generación de embeddings
  - Generación de texto (respuestas)
  - Servir modelo local sin conexión a internet

### 4. Vector Store (FAISS)
- **Tecnología**: FAISS (Facebook AI Similarity Search)
- **Responsabilidades**:
  - Almacenamiento de embeddings
  - Búsqueda de similitud vectorial
  - Recuperación de documentos relevantes

## Flujo de Datos

### Flujo de Inicialización

1. **Backend inicia**
2. **Carga Excel** → DataFrames
3. **Transforma datos** → Documentos LangChain
4. **Genera embeddings** → Vectores (vía Ollama)
5. **Construye índice** → FAISS vector store
6. **Guarda en disco** → `/data/vectorstore`
7. **Inicializa RAG chain** → Listo para consultas

### Flujo de Consulta

1. **Usuario** envía pregunta desde Frontend
2. **Frontend** → POST `/api/chat` con pregunta
3. **Backend** recibe consulta
4. **Genera embedding** de la pregunta (vía Ollama)
5. **Vector search** en FAISS → Top 5 documentos similares
6. **Construye prompt**:
   ```
   CONTEXTO: [documentos recuperados]
   PREGUNTA: [pregunta del usuario]
   ```
7. **Envía a Ollama** para generación
8. **LLM genera respuesta** basada en contexto
9. **Backend** extrae sources de documentos
10. **Responde a Frontend** con answer + sources
11. **Frontend** muestra respuesta al usuario

## Consideraciones de Diseño

### Anti-Alucinación
- Prompt explícito: "Solo usa información del contexto"
- Instrucción: "Di cuando no hay suficiente información"
- Temperatura baja (0.1) para respuestas más determinísticas
- Validación de fuentes en respuesta

### Performance
- Vector store persistente (no recalcular embeddings)
- Chunking optimizado (500-1000 caracteres)
- Top-k = 5 (balance entre contexto y velocidad)
- Agregaciones pre-calculadas en documentos

### Escalabilidad
- FAISS eficiente para miles de documentos
- Embeddings en batch cuando sea posible
- Vector store en disco para persistencia
- Stateless API (puede escalar horizontalmente)

### Mantenibilidad
- Separación clara de responsabilidades
- Configuración vía variables de entorno
- Logging comprehensivo
- Tipo hints en Python
- Documentación inline

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

1. **Sin base de datos relacional**: Todo en memoria/archivos
2. **Sin autenticación**: Acceso abierto
3. **Sin historial persistente**: Conversaciones no se guardan
4. **Single-user**: No multi-tenancy
5. **Embeddings lentos**: Primera vez toma tiempo

## Mejoras Futuras

1. Agregar PostgreSQL para persistencia
2. Implementar autenticación (JWT)
3. Guardar historial de conversaciones
4. Cache de respuestas frecuentes
5. Streaming de respuestas (SSE)
6. Métricas y monitoring (Prometheus)
7. Rate limiting
8. Multi-idioma
