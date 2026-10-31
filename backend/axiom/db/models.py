"""Database — SQLite async avec SQLAlchemy pour users, conversations et facturation Stripe.

Ce module fournit:
- Modèles ORM pour User, Conversation, Message, WebhookEvent, PaymentOrder
- Gestionnaire de base de données async avec cycle de vie
- Migration SQLite automatique et non-destructive
"""

import os
from datetime import datetime
from typing import Optional, AsyncGenerator
from contextlib import asynccontextmanager
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, relationship
from axiom.logging_setup import log

DB_PATH = os.getenv("HAKIM_DB_PATH", os.path.join(os.path.dirname(__file__), "..", "data", "apex.db"))


class Base(DeclarativeBase):
    """Base class pour tous les modèles SQLAlchemy."""
    pass


class User(Base):
    """Modèle utilisateur avec gestion des abonnements et identifiants Stripe."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(120), unique=True, nullable=True)
    password_hash = Column(String(255), nullable=False)
    display_name = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

    # Identifiants & statuts Stripe (Facturation & Abonnements)
    stripe_customer_id = Column(String(100), unique=True, nullable=True, index=True)
    subscription_tier = Column(String(50), default="free", nullable=False)  # free, pro, enterprise
    subscription_status = Column(String(50), default="active", nullable=False)  # active, trialing, past_due, canceled
    stripe_subscription_id = Column(String(100), nullable=True, index=True)
    current_period_end = Column(DateTime, nullable=True)
    cancel_at_period_end = Column(Integer, default=0, nullable=False)  # 0 = non, 1 = oui

    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
    orders = relationship("PaymentOrder", back_populates="user", cascade="all, delete-orphan")


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


class WebhookEvent(Base):
    """Table de déduplication et traçabilité des webhooks Stripe (idempotence)."""
    __tablename__ = "webhook_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String(100), unique=True, nullable=False, index=True)
    event_type = Column(String(100), nullable=False)
    status = Column(String(50), default="pending", nullable=False)  # pending, processed, failed, ignored
    payload = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)


class PaymentOrder(Base):
    """Historique des commandes et transactions de facturation Stripe."""
    __tablename__ = "payment_orders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    stripe_session_id = Column(String(150), unique=True, nullable=True, index=True)
    stripe_payment_intent_id = Column(String(150), nullable=True, index=True)
    amount_cents = Column(Integer, nullable=False)  # Montant en centimes (entier minor unit - JAMAIS de float)
    currency = Column(String(10), default="eur", nullable=False)
    status = Column(String(50), default="pending", nullable=False)  # pending, succeeded, failed, refunded
    tier = Column(String(50), nullable=False)  # pro, enterprise, credits
    billing_reason = Column(String(100), nullable=True)  # checkout_session, subscription_cycle, etc.
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="orders")


# =============================================================================
# GESTIONNAIRE DE BASE DE DONNÉES
# =============================================================================

class DatabaseManager:
    """
    Gestionnaire de base de données avec lifecycle management.
    
    Utilise le pattern Singleton pour s'assurer qu'une seule instance
    de l'engine et du sessionmaker existe par processus.
    """
    
    _engine: Optional[any] = None
    _async_sessionmaker: Optional[any] = None
    
    @classmethod
    def get_engine(cls) -> any:
        """Retourne ou crée l'engine async SQLAlchemy."""
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
        Commit automatique si pas d'erreur, rollback si exception.
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
        """Crée toutes les tables et applique les migrations douces si nécessaire."""
        eng = cls.get_engine()
        async with eng.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

            # Migration douce SQLite pour les colonnes Stripe de 'users'
            def _migrate_users_table(connection):
                result = connection.execute(text("PRAGMA table_info(users)"))
                columns = [row[1] for row in result.fetchall()]
                
                new_cols = [
                    ("stripe_customer_id", "VARCHAR(100)"),
                    ("subscription_tier", "VARCHAR(50) DEFAULT 'free'"),
                    ("subscription_status", "VARCHAR(50) DEFAULT 'active'"),
                    ("stripe_subscription_id", "VARCHAR(100)"),
                    ("current_period_end", "DATETIME"),
                    ("cancel_at_period_end", "INTEGER DEFAULT 0"),
                ]
                for col_name, col_type in new_cols:
                    if col_name not in columns:
                        connection.execute(text(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}"))
                        log.info("Colonne SQLite ajoutée: users.%s", col_name)

            await conn.run_sync(_migrate_users_table)
            log.info("Tables DB créées et migrées avec succès")
    
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
    """Retourne l'engine (compatibilité descendante)."""
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
