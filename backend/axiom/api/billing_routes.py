"""Routes API FastAPI pour la facturation et les abonnements Stripe."""

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from sqlalchemy import select
from axiom.db.models import User, PaymentOrder, DatabaseManager
from axiom.auth.jwt import get_current_user, optional_user
from axiom.billing.stripe_service import stripe_service
from axiom.billing.plans import PLANS, get_plan_by_id
from axiom.logging_setup import log

router = APIRouter(prefix="/billing", tags=["billing"])


class CheckoutRequest(BaseModel):
    tier: str = Field(..., description="Nom de l'offre choisie: pro ou enterprise")
    interval: str = Field("month", description="Fréquence de facturation: month ou year")


class PortalRequest(BaseModel):
    return_url: Optional[str] = Field(None, description="URL de redirection de retour après le portail Stripe")


@router.get("/config")
async def get_billing_config():
    """Retourne la configuration publique de Stripe et la liste des forfaits."""
    return stripe_service.get_public_config()


@router.get("/status")
async def get_billing_status(current_user: User = Depends(get_current_user)):
    """Retourne l'état d'abonnement et l'historique récent de l'utilisateur connecté."""
    async with DatabaseManager.get_session() as session:
        # Recharger l'utilisateur avec ses dernières données
        stmt = select(User).where(User.id == current_user.id)
        res = await session.execute(stmt)
        user = res.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="Utilisateur introuvable")

        # Récupérer les 10 dernières commandes/factures
        order_stmt = (
            select(PaymentOrder)
            .where(PaymentOrder.user_id == user.id)
            .order_by(PaymentOrder.created_at.desc())
            .limit(10)
        )
        order_res = await session.execute(order_stmt)
        orders = order_res.scalars().all()

        current_plan = get_plan_by_id(user.subscription_tier or "free") or PLANS["free"]

        return {
            "tier": user.subscription_tier or "free",
            "tier_name": current_plan.get("name", "Starter"),
            "status": user.subscription_status or "active",
            "current_period_end": user.current_period_end.isoformat() if user.current_period_end else None,
            "cancel_at_period_end": bool(user.cancel_at_period_end),
            "has_stripe_customer": bool(user.stripe_customer_id),
            "stripe_customer_id": user.stripe_customer_id,
            "orders": [
                {
                    "id": o.id,
                    "amount_cents": o.amount_cents,
                    "currency": o.currency,
                    "status": o.status,
                    "tier": o.tier,
                    "billing_reason": o.billing_reason,
                    "created_at": o.created_at.isoformat() if o.created_at else None,
                }
                for o in orders
            ],
            "plan_limits": current_plan.get("limits", {}),
        }


@router.post("/checkout")
async def create_checkout(
    req: CheckoutRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Crée une session Stripe Checkout pour souscrire à une offre.
    Retourne l'URL vers laquelle rediriger l'utilisateur.
    """
    if req.tier not in PLANS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Offre invalide '{req.tier}'. Offres disponibles: {list(PLANS.keys())}",
        )

    if req.interval not in ("month", "year"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="L'intervalle doit être 'month' ou 'year'.",
        )

    async with DatabaseManager.get_session() as session:
        stmt = select(User).where(User.id == current_user.id)
        res = await session.execute(stmt)
        user = res.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="Utilisateur introuvable")

        try:
            checkout_data = await stripe_service.create_checkout_session(
                user=user,
                tier=req.tier,
                interval=req.interval,
                session=session,
            )
            return checkout_data
        except Exception as e:
            log.error("Erreur lors de la création du checkout: %s", str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Impossible de créer la session de paiement: {str(e)}",
            )


@router.post("/portal")
async def create_customer_portal(
    req: PortalRequest = PortalRequest(),
    current_user: User = Depends(get_current_user),
):
    """
    Génère un lien sécurisé vers le Portail Client Stripe
    permettant de modifier sa carte, consulter ses factures ou résilier.
    """
    async with DatabaseManager.get_session() as session:
        stmt = select(User).where(User.id == current_user.id)
        res = await session.execute(stmt)
        user = res.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="Utilisateur introuvable")

        try:
            portal_data = await stripe_service.create_customer_portal_session(
                user=user,
                return_url=req.return_url,
                session=session,
            )
            return portal_data
        except Exception as e:
            log.error("Erreur lors de la création du portail Stripe: %s", str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Impossible d'ouvrir le portail de facturation: {str(e)}",
            )


@router.post("/webhook")
async def handle_stripe_webhook(request: Request):
    """
    Endpoint de réception des webhooks Stripe.
    Valide cryptographiquement la signature et applique les mutations d'état.
    """
    sig_header = request.headers.get("stripe-signature")
    payload = await request.body()

    async with DatabaseManager.get_session() as session:
        success, message, data = await stripe_service.process_webhook(
            payload=payload,
            sig_header=sig_header,
            session=session,
        )

        if not success:
            log.warning("Webhook rejeté avec statut 400: %s", message)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Webhook non validé: {message}",
            )

        return {"status": "success", "detail": message, "data": data}
