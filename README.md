# Retail 360 Chatbot

Sistema de chatbot con arquitectura RAG (Retrieval-Augmented Generation) para consultas sobre un dataset de ventas.

## Características

- **Backend**: FastAPI + LangChain + Ollama
- **Frontend**: Flutter Web
- **Arquitectura**: RAG con vector store FAISS
- **Deployment**: Docker Compose

## Requisitos

- Docker y Docker Compose
- Archivo Excel con datos de ventas en `./data/dataset.xlsx`

## Estructura del Proyecto

```
.
├── backend/              
│   ├── app/
│   │   ├── api/        
│   │   ├── rag/         
│   │   ├── config.py  
│   │   ├── main.py      
│   │   ├── models.py    
│   │   └── excel_loader.py
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/           
│   ├── lib/
│   │   └── main.dart
│   ├── Dockerfile
│   └── nginx.conf
├── data/               
│   └── dataset.xlsx    
├── ollama/             
└── docker-compose.yml
```

## Instalación y Uso

### 1. Iniciar los servicios

```bash
docker compose up --build
```

Esto iniciará:
- **Ollama** (puerto 11434): Servidor de modelos LLM
- **Backend** (puerto 8000): API FastAPI
- **Frontend** (puerto 80): Aplicación web

### 2. Descargar el modelo (primera vez)

En otra terminal, ejecuta:

```bash
docker exec -it retail360-ollama ollama pull llama3
```

### 3. Acceder a la aplicación

- **Frontend**: http://localhost
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/health

## Endpoints de la API

### GET /api/health
Verifica el estado del sistema.

### POST /api/chat (legacy)
Consulta rápida sin persistencia de historial.

### Chats Persistentes (MongoDB)

1. POST /api/chats
   Crea un nuevo chat.
   Body: {"user_id": "u123", "first_message": "Opcional"}

2. GET /api/chats?user_id=u123
   Lista los chats del usuario.

3. GET /api/chats/{chat_id}
   Obtiene detalles y mensajes de un chat.

4. POST /api/chats/{chat_id}/message
   Envía pregunta y guarda respuesta.
   Body: {"user_id": "u123", "question": "¿Cuántas ventas hubo en marzo de 2023?"}

**Ejemplo Respuesta mensaje:**
```json
{
  "answer": "En marzo de 2023 hubo 150 ventas...",
  "sources": [
    {"id": "...", "type": "mes_agregado", "metadata": {}}
  ]
}
```

### POST /api/rebuild-index
Reconstruye el índice vectorial desde el Excel.

## Configuración

Variables de entorno en `docker-compose.yml`:

- `EXCEL_PATH`: Ruta al archivo Excel (default: `/data/dataset.xlsx`)
- `OLLAMA_BASE_URL`: URL del servidor Ollama (default: `http://ollama:11434`)
- `OLLAMA_MODEL`: Modelo LLM a usar (default: `llama3`)
- `EMBEDDING_MODEL`: Modelo para embeddings (default: `llama3`)
- `VECTORSTORE_PATH`: Ruta al vector store (default: `/data/vectorstore`)
- `MONGO_URI`: URI de conexión MongoDB (default: `mongodb://mongodb:27017/retail360`)

## Desarrollo Local

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Configurar variables de entorno:
```bash
export EXCEL_PATH=../data/dataset.xlsx
export OLLAMA_BASE_URL=http://localhost:11434
export OLLAMA_MODEL=llama3
```

### Frontend

```bash
cd frontend
flutter pub get
flutter run -d chrome --dart-define=API_URL=http://localhost:8000
```

## Ejemplos de Preguntas

- "¿Cuántas ventas hubo en marzo de 2023?"
- "¿Cuál fue el cliente que más compró?"
- "¿Cuál es el producto más vendido?"
- "¿Cuál fue el total de ventas en 2023?"
- "¿Qué local tuvo más ventas?"


## Consideraciones sobre el vector store
La primera vez, el sistema construye el índice vectorial. Esto puede tomar varios minutos dependiendo del tamaño del dataset. El índice se guarda en disco y se reutiliza en siguientes inicios.

Para reconstruir el índice:
```bash
curl -X POST http://localhost:8000/api/rebuild-index
```

## Tecnologías

- **LangChain**: Framework para aplicaciones LLM
- **Ollama**: Servidor de modelos LLM locales
- **FastAPI**: Framework web moderno para Python
- **Flutter**: Framework UI multiplataforma
- **FAISS**: Vector store para búsqueda de similitud
- **Docker**: Containerización

