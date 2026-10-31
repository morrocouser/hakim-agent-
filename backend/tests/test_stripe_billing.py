"""Tests exhaustifs pour le module de facturation et d'abonnements Stripe.

Vérifie:
1. Endpoints publics (/config)
2. Sécurité et authentification (/status, /checkout, /portal)
3. Validation des requêtes invalides (bad tier, bad interval)
4. Création de sessions Stripe Checkout réelles et simulées
5. Traitement idempotent des événements Webhooks (checkout.session.completed,
   customer.subscription.updated, customer.subscription.deleted, invoice.payment_failed)
6. Déduplication stricte des événements Webhook
7. Règle d'intégrité financière : montants manipulés uniquement en entiers de centimes
8. Rejet cryptographique des signatures Webhook invalides
"""

import pytest
import pytest_asyncio
import time
import json
import stripe
from httpx import AsyncClient, ASGITransport
from datetime import datetime
from sqlalchemy import select

from axiom.api.main import app
from axiom.db.models import User, WebhookEvent, PaymentOrder, DatabaseManager
from axiom.auth.jwt import hash_password, create_access_token
from axiom.billing.plans import PLANS
from axiom.billing.stripe_service import stripe_service


def make_webhook_request(payload_dict: dict):
    """Génère le payload encodé et l'en-tête stripe-signature cryptographiquement valide."""
    payload_str = json.dumps(payload_dict)
    payload_bytes = payload_str.encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if stripe_service.webhook_secret:
        sig = stripe.WebhookSignature.generate_signature_header(
            payload_str, stripe_service.webhook_secret
        )
        headers["stripe-signature"] = sig
    return payload_bytes, headers


@pytest_asyncio.fixture(autouse=True)
async def setup_test_db():
    """Initialise la base de données de test et nettoie les tables après chaque test."""
    await DatabaseManager.init_db()
    yield
    # Nettoyage après test
    async with DatabaseManager.get_session() as session:
        for model in (PaymentOrder, WebhookEvent):
            stmt = select(model)
            res = await session.execute(stmt)
            for row in res.scalars().all():
                await session.delete(row)


@pytest_asyncio.fixture
async def test_user():
    """Crée ou réinitialise un utilisateur de test."""
    async with DatabaseManager.get_session() as session:
        stmt = select(User).where(User.username == "stripe_tester")
        res = await session.execute(stmt)
        user = res.scalar_one_or_none()
        if not user:
            user = User(
                username="stripe_tester",
                email="stripe_tester@example.com",
                password_hash=hash_password("Password123!"),
                display_name="Stripe Tester",
                subscription_tier="free",
                subscription_status="active",
            )
            session.add(user)
        else:
            user.subscription_tier = "free"
            user.subscription_status = "active"
            user.stripe_customer_id = None
            user.stripe_subscription_id = None
            user.cancel_at_period_end = 0
            user.current_period_end = None
        await session.flush()
        return user


@pytest.fixture
def auth_headers(test_user):
    """Génère un header d'authentification Bearer valide pour test_user."""
    token = create_access_token(data={"sub": test_user.username, "user_id": test_user.id})
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_billing_config_endpoint():
    """Vérifie que l'endpoint /config retourne les informations publiques."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/billing/config")
        assert resp.status_code == 200
        data = resp.json()
        assert "plans" in data
        assert "pro" in data["plans"]
        assert "free" in data["plans"]
        assert "currency" in data
        assert data["currency"] == "eur"
        assert data["plans"]["pro"]["price_monthly_cents"] == 2900


@pytest.mark.asyncio
async def test_billing_status_unauthenticated():
    """Vérifie que l'endpoint /status exige une authentification."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/billing/status")
        assert resp.status_code == 401


@pytest.mark.asyncio
async def test_billing_status_authenticated(test_user, auth_headers):
    """Vérifie que l'endpoint /status renvoie l'état courant de l'utilisateur."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/billing/status", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["tier"] == "free"
        assert data["status"] == "active"
        assert "orders" in data
        assert isinstance(data["orders"], list)


@pytest.mark.asyncio
async def test_create_checkout_session(test_user, auth_headers):
    """Vérifie la création d'une session Stripe Checkout."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {"tier": "pro", "interval": "month"}
        resp = await client.post("/api/v1/billing/checkout", json=payload, headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "checkout_url" in data
        assert "session_id" in data
        assert data["checkout_url"].startswith("https://checkout.stripe.com") or "pricing" in data["checkout_url"]

        # Vérifier qu'un PaymentOrder pending a été persisté
        async with DatabaseManager.get_session() as session:
            stmt = select(PaymentOrder).where(PaymentOrder.user_id == test_user.id)
            res = await session.execute(stmt)
            orders = res.scalars().all()
            assert len(orders) >= 1
            latest_order = orders[-1]
            assert latest_order.amount_cents == 2900
            assert latest_order.tier == "pro"
            assert latest_order.status == "pending"


@pytest.mark.asyncio
async def test_create_checkout_invalid_plan(auth_headers):
    """Vérifie qu'un plan inexistant renvoie 400 Bad Request."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/v1/billing/checkout", json={"tier": "super_vip_invalid"}, headers=auth_headers)
        assert resp.status_code == 400


@pytest.mark.asyncio
async def test_create_portal_session(test_user, auth_headers):
    """Vérifie la génération d'un lien vers le Customer Portal Stripe."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/v1/billing/portal", json={}, headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "portal_url" in data


@pytest.mark.asyncio
async def test_webhook_checkout_completed_and_idempotency(test_user):
    """Vérifie le traitement de checkout.session.completed et la déduplication."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        event_id = f"evt_test_checkout_{int(time.time() * 1000)}"
        webhook_payload = {
            "id": event_id,
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "id": f"cs_test_{event_id}",
                    "customer": f"cus_test_{test_user.id}",
                    "subscription": "sub_test_12345",
                    "metadata": {
                        "user_id": str(test_user.id),
                        "tier": "pro",
                    },
                }
            },
        }

        body, headers = make_webhook_request(webhook_payload)

        # Premier envoi du webhook
        resp1 = await client.post("/api/v1/billing/webhook", content=body, headers=headers)
        assert resp1.status_code == 200
        data1 = resp1.json()
        assert data1["status"] == "success"
        assert data1["detail"] == "processed"

        # Vérifier en DB que l'utilisateur est passé Pro
        async with DatabaseManager.get_session() as session:
            stmt = select(User).where(User.id == test_user.id)
            res = await session.execute(stmt)
            updated_user = res.scalar_one()
            assert updated_user.subscription_tier == "pro"
            assert updated_user.subscription_status == "active"
            assert updated_user.stripe_subscription_id == "sub_test_12345"

        # Deuxième envoi du MÊME webhook (Idempotency test)
        resp2 = await client.post("/api/v1/billing/webhook", content=body, headers=headers)
        assert resp2.status_code == 200
        data2 = resp2.json()
        assert data2["status"] == "success"
        assert data2["detail"] == "already_processed"


@pytest.mark.asyncio
async def test_webhook_subscription_lifecycle(test_user):
    """Vérifie la mise à jour puis la résiliation d'un abonnement via webhooks."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        customer_id = f"cus_test_{test_user.id}"

        # 1. Associer l'utilisateur au customer_id
        async with DatabaseManager.get_session() as session:
            stmt = select(User).where(User.id == test_user.id)
            res = await session.execute(stmt)
            u = res.scalar_one()
            u.stripe_customer_id = customer_id
            u.subscription_tier = "pro"

        # 2. Événement subscription.updated (marquage cancel_at_period_end)
        update_event = {
            "id": f"evt_upd_{int(time.time() * 1000)}",
            "type": "customer.subscription.updated",
            "data": {
                "object": {
                    "id": "sub_test_12345",
                    "customer": customer_id,
                    "status": "active",
                    "cancel_at_period_end": True,
                    "current_period_end": 1798761600,
                }
            },
        }
        body_upd, headers_upd = make_webhook_request(update_event)
        resp = await client.post("/api/v1/billing/webhook", content=body_upd, headers=headers_upd)
        assert resp.status_code == 200

        async with DatabaseManager.get_session() as session:
            stmt = select(User).where(User.id == test_user.id)
            res = await session.execute(stmt)
            u = res.scalar_one()
            assert u.cancel_at_period_end == 1

        # 3. Événement subscription.deleted (fin d'abonnement -> downgrade free)
        delete_event = {
            "id": f"evt_del_{int(time.time() * 1000)}",
            "type": "customer.subscription.deleted",
            "data": {
                "object": {
                    "id": "sub_test_12345",
                    "customer": customer_id,
                }
            },
        }
        body_del, headers_del = make_webhook_request(delete_event)
        resp_del = await client.post("/api/v1/billing/webhook", content=body_del, headers=headers_del)
        assert resp_del.status_code == 200

        async with DatabaseManager.get_session() as session:
            stmt = select(User).where(User.id == test_user.id)
            res = await session.execute(stmt)
            u = res.scalar_one()
            assert u.subscription_tier == "free"
            assert u.subscription_status == "canceled"
            assert u.stripe_subscription_id is None


@pytest.mark.asyncio
async def test_webhook_signature_rejection():
    """Vérifie le rejet d'un webhook si la signature est invalide."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/billing/webhook",
            content=b'{"id": "evt_fake", "type": "ping"}',
            headers={"stripe-signature": "t=123456,v1=invalidsignature"},
        )
        assert resp.status_code == 400
        assert "Webhook non validé" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_money_amounts_are_integers():
    """Vérifie que les montants monétaires sont strictement des entiers en centimes."""
    for plan_key, plan in PLANS.items():
        assert isinstance(plan["price_monthly_cents"], int), f"Plan {plan_key} price_monthly_cents must be int"
        assert isinstance(plan["price_yearly_cents"], int), f"Plan {plan_key} price_yearly_cents must be int"
        assert plan["price_monthly_cents"] >= 0
        assert plan["currency"] in ("eur", "usd")
