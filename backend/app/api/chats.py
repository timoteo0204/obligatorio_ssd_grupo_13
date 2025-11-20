from fastapi import APIRouter, HTTPException
from bson import ObjectId
from datetime import datetime
from app.models import ChatCreateRequest, ChatSummary, ChatDetail, ChatMessage, ChatMessageAddRequest, ChatResponse, Source
from app.rag.chain import query_rag
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


def oid(id_str: str) -> ObjectId:
    try:
        return ObjectId(id_str)
    except Exception:
        raise HTTPException(status_code=400, detail="chat_id inválido")


@router.post("/chats", response_model=ChatDetail)
async def create_chat(req: ChatCreateRequest):
    from app.main import app_state
    db = app_state.get('db')
    if db is None:
        raise HTTPException(status_code=500, detail="DB no inicializada")
    now = datetime.utcnow()
    messages = []
    title = "Nuevo chat"
    if req.first_message:
        messages.append(ChatMessage(role="user", content=req.first_message, ts=now).dict())
        title = req.first_message[:60]
    doc = {
        "user_id": req.user_id,
        "title": title,
        "messages": messages,
        "created_at": now,
        "updated_at": now,
    }
    res = await db.chats.insert_one(doc)
    doc["_id"] = res.inserted_id
    return ChatDetail(
        id=str(doc["_id"]),
        user_id=doc["user_id"],
        title=doc["title"],
        messages=[ChatMessage(**m) for m in doc["messages"]],
        created_at=doc["created_at"],
        updated_at=doc["updated_at"],
    )


@router.get("/chats", response_model=list[ChatSummary])
async def list_chats(user_id: str):
    from app.main import app_state
    db = app_state.get('db')
    cursor = db.chats.find({"user_id": user_id}).sort("updated_at", -1)
    chats = []
    async for c in cursor:
        chats.append(ChatSummary(
            id=str(c["_id"]),
            title=c.get("title", "Chat"),
            created_at=c["created_at"],
            updated_at=c["updated_at"],
        ))
    return chats


@router.get("/chats/{chat_id}", response_model=ChatDetail)
async def get_chat(chat_id: str):
    from app.main import app_state
    db = app_state.get('db')
    c = await db.chats.find_one({"_id": oid(chat_id)})
    if not c:
        raise HTTPException(status_code=404, detail="Chat no encontrado")
    return ChatDetail(
        id=str(c["_id"]),
        user_id=c["user_id"],
        title=c.get("title", "Chat"),
        messages=[ChatMessage(**m) for m in c.get("messages", [])],
        created_at=c["created_at"],
        updated_at=c["updated_at"],
    )


@router.post("/chats/{chat_id}/message", response_model=ChatResponse)
async def add_message(chat_id: str, req: ChatMessageAddRequest):
    from app.main import app_state
    if not app_state.get('chain') or not app_state.get('retriever'):
        raise HTTPException(status_code=503, detail="RAG no inicializado")
    db = app_state.get('db')
    c = await db.chats.find_one({"_id": oid(chat_id), "user_id": req.user_id})
    if not c:
        raise HTTPException(status_code=404, detail="Chat no encontrado")
    now = datetime.utcnow()
    user_msg = ChatMessage(role="user", content=req.question, ts=now).dict()
    result = query_rag(
        question=req.question,
        chain=app_state['chain'],
        retriever=app_state['retriever'],
    )
    assistant_msg = ChatMessage(role="assistant", content=result['answer'], ts=datetime.utcnow()).dict()
    new_messages = c.get("messages", []) + [user_msg, assistant_msg]
    await db.chats.update_one({"_id": c["_id"]}, {"$set": {"messages": new_messages, "updated_at": datetime.utcnow(), "title": c.get("title") or req.question[:60]}})
    return ChatResponse(answer=result['answer'])
