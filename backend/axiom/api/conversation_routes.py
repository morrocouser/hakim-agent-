"""Conversation Routes — CRUD conversations + historique messages."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from sqlalchemy import select, desc, func
from axiom.db.models import User, Conversation, Message, get_session
from axiom.auth.jwt import get_current_user

router = APIRouter(prefix="/conversations", tags=["conversations"])


class ConversationCreate(BaseModel):
    title: str = Field(None, max_length=200)


class MessageCreate(BaseModel):
    role: str = Field(..., pattern="^(user|assistant|system)$")
    content: str
    agent: Optional[str] = None
    model: Optional[str] = None
    score: Optional[int] = None
    metadata: Optional[dict] = None


class ConversationResponse(BaseModel):
    id: int
    title: Optional[str] = None
    created_at: str
    updated_at: str
    message_count: int = 0


class MessageResponse(BaseModel):
    id: int
    role: str
    content: str
    agent: Optional[str] = None
    model: Optional[str] = None
    score: Optional[float] = None
    metadata: Optional[dict] = None
    created_at: str

    model_config = {"from_attributes": True}


@router.get("", response_model=list[ConversationResponse])
async def list_conversations(user: User = Depends(get_current_user)):
    session = await get_session()
    try:
        stmt = (
            select(
                Conversation,
                func.count(Message.id).label("message_count"),
            )
            .outerjoin(Message, Message.conversation_id == Conversation.id)
            .where(Conversation.user_id == user.id)
            .group_by(Conversation.id)
            .order_by(desc(Conversation.updated_at))
        )
        result = await session.execute(stmt)
        rows = result.all()
        responses = []
        for convo, count in rows:
            responses.append(ConversationResponse(
                id=convo.id,
                title=convo.title,
                created_at=str(convo.created_at),
                updated_at=str(convo.updated_at),
                message_count=count,
            ))
        return responses
    finally:
        await session.close()


@router.post("", response_model=ConversationResponse)
async def create_conversation(req: ConversationCreate, user: User = Depends(get_current_user)):
    session = await get_session()
    try:
        convo = Conversation(user_id=user.id, title=req.title)
        session.add(convo)
        await session.commit()
        await session.refresh(convo)
        return ConversationResponse(
            id=convo.id,
            title=convo.title,
            created_at=str(convo.created_at),
            updated_at=str(convo.updated_at),
            message_count=0,
        )
    finally:
        await session.close()


@router.get("/{convo_id}")
async def get_conversation(convo_id: int, user: User = Depends(get_current_user)):
    session = await get_session()
    try:
        result = await session.execute(
            select(Conversation).where(Conversation.id == convo_id, Conversation.user_id == user.id)
        )
        convo = result.scalar_one_or_none()
        if not convo:
            raise HTTPException(status_code=404, detail="Conversation non trouvée")

        msg_result = await session.execute(
            select(Message).where(Message.conversation_id == convo_id).order_by(Message.created_at)
        )
        messages = msg_result.scalars().all()

        return {
            "id": convo.id,
            "title": convo.title,
            "created_at": str(convo.created_at),
            "updated_at": str(convo.updated_at),
            "messages": [
                MessageResponse(
                    id=m.id,
                    role=m.role,
                    content=m.content,
                    agent=m.agent,
                    model=m.model,
                    score=m.score,
                    metadata=m.extra_data,
                    created_at=str(m.created_at),
                ).model_dump()
                for m in messages
            ],
        }
    finally:
        await session.close()



@router.post("/{convo_id}/messages", response_model=MessageResponse)
async def add_message(convo_id: int, req: MessageCreate, user: User = Depends(get_current_user)):
    session = await get_session()
    try:
        # Verify ownership
        result = await session.execute(
            select(Conversation).where(Conversation.id == convo_id, Conversation.user_id == user.id)
        )
        convo = result.scalar_one_or_none()
        if not convo:
            raise HTTPException(status_code=404, detail="Conversation non trouvée")

        msg = Message(
            conversation_id=convo_id,
            role=req.role,
            content=req.content,
            agent=req.agent,
            model=req.model,
            score=req.score,
            extra_data=req.metadata,
        )
        session.add(msg)

        # Update conversation timestamp
        convo.updated_at = datetime.utcnow()

        await session.commit()
        await session.refresh(msg)

        return MessageResponse(
            id=msg.id,
            role=msg.role,
            content=msg.content,
            agent=msg.agent,
            model=msg.model,
            score=msg.score,
            metadata=msg.extra_data,
            created_at=str(msg.created_at),
        )
    finally:
        await session.close()


@router.delete("/{convo_id}")
async def delete_conversation(convo_id: int, user: User = Depends(get_current_user)):
    session = await get_session()
    try:
        result = await session.execute(
            select(Conversation).where(Conversation.id == convo_id, Conversation.user_id == user.id)
        )
        convo = result.scalar_one_or_none()
        if not convo:
            raise HTTPException(status_code=404, detail="Conversation non trouvée")

        await session.delete(convo)
        await session.commit()
        return {"ok": True}
    finally:
        await session.close()
