"""Database — SQLite async avec SQLAlchemy pour users et conversations.

Ce module fournit:
- Modèles ORM pour User, Conversation, Message
- Gestionnaire de base de données async
- Factory de sessions avec lifecycle management
"""

import os
from datetime import datetime
from typing import Optional, AsyncGenerator
from contextlib import asynccontextmanager
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, relationship
from axiom.logging_setup import log

DB_PATH = os.getenv("HAKIM_DB_PATH", os.path.join(os.path.dirname(__file__), "..", "data", "apex.db"))


class Base(DeclarativeBase):
    """Base class pour tous les modèles SQLAlchemy."""
    pass


class User(Base):
    """Modèle utilisateur."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(120), unique=True, nullable=True)
    password_hash = Column(String(255), nullable=False)
    display_name = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")


class Conversation(Base):
    """Modèle de conversation."""
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(200), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan", order_by="Message.created_at")


class Message(Base):
    """Modèle de message."""
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    role = Column(String(20), nullable=False)  # "user", "assistant", "system"
    content = Column(Text, nullable=False)
    agent = Column(String(50), nullable=True)
    model = Column(String(100), nullable=True)
    score = Column(Integer, nullable=True)
    extra_data = Column("metadata", JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    conversation = relationship("Conversation", back_populates="messages")


# =============================================================================
# GESTIONNAIRE DE BASE DE DONNÉES
# =============================================================================

class DatabaseManager:
    """
    Gestionnaire de base de données avec lifecycle management.
    
    Utilise le pattern Singleton pour s'assurer qu'une seule instance
    de l.engine et du sessionmaker existe par processus.
    """
    
    _engine: Optional[any] = None
    _async_sessionmaker: Optional[any] = None
    
    @classmethod
    def get_engine(cls) -> any:
        """Retourne ou crée l.engine async SQLAlchemy."""
        if cls._engine is None:
            os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
            db_url = f"sqlite+aiosqlite:///{DB_PATH}"
            cls._engine = create_async_engine(db_url, echo=False)
            log.info("Engine SQLAlchemy créé: %s", db_url)
        return cls._engine
    
    @classmethod
    def get_sessionmaker(cls) -> any:
        """Retourne ou crée le async_sessionmaker."""
        if cls._async_sessionmaker is None:
            eng = cls.get_engine()
            cls._async_sessionmaker = async_sessionmaker(
                eng,
                class_=AsyncSession,
                expire_on_commit=False,
                autocommit=False,
                autoflush=False,
            )
            log.info("Sessionmaker SQLAlchemy créé")
        return cls._async_sessionmaker
    
    @classmethod
    @asynccontextmanager
    async def get_session(cls) -> AsyncGenerator[AsyncSession, None]:
        """
        Context manager pour obtenir une session de base de données.
        
        La session est automatiquement commité si pas d'erreur,
        ou rollbackée si erreur. Elle est toujours fermée à la sortie.
        
        Utilisation:
            async with DatabaseManager.get_session() as session:
                # utiliser session
        """
        sessionmaker = cls.get_sessionmaker()
        session = sessionmaker()
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            log.warning("Rollback session DB: %s", str(e))
            raise
        finally:
            await session.close()
    
    @classmethod
    async def init_db(cls):
        """Crée toutes les tables."""
        eng = cls.get_engine()
        async with eng.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            log.info("Tables DB créées")
    
    @classmethod
    async def close_db(cls):
        """Ferme la connexion à la base de données."""
        if cls._engine:
            await cls._engine.dispose()
            log.info("Engine SQLAlchemy fermé")
        cls._engine = None
        cls._async_sessionmaker = None


# =============================================================================
# FONCTIONS DE COMPATIBILITÉ (pour le code existant)
# =============================================================================

def get_engine():
    """Retourne l.engine (compatibilité descendante)."""
    return DatabaseManager.get_engine()


async def get_session() -> AsyncSession:
    """Retourne une nouvelle session (compatibilité descendante)."""
    sessionmaker = DatabaseManager.get_sessionmaker()
    return sessionmaker()


async def init_db():
    """Initialise la base de données (compatibilité descendante)."""
    await DatabaseManager.init_db()


async def close_db():
    """Ferme la base de données (compatibilité descendante)."""
    await DatabaseManager.close_db()
