"""Service de facturation et d'intégration Stripe pour HakimAgent / AXIOM.

Respecte scrupuleusement les règles d'ingénierie financière :
1. Aucun numéro de carte ne transite sur nos serveurs (SAQ-A / Stripe Checkout & Customer Portal).
2. Clés d'idempotence sur toutes les mutations pour éliminer les doubles facturations.
3. Les webhooks signés constituent la seule source de vérité (pas la redirection client).
4. Déduplication transactionnelle des événements webhooks via la table WebhookEvent.
5. Gestion des montants exclusivement en nombres entiers de centimes (minor units, ISO 4217).
6. Support d'un mode simulation automatique en l'absence de clé de production Stripe.
"""

import os
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Tuple
import stripe
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from axiom.db.models import User, WebhookEvent, PaymentOrder
from axiom.billing.plans import PLANS, get_plan_by_id
from axiom.logging_setup import log


class StripeService:
    """Service centralisé de gestion des paiements et abonnements Stripe."""

    def __init__(self):
        self.secret_key = os.getenv("STRIPE_SECRET_KEY", "").strip()
        self.publishable_key = os.getenv("STRIPE_PUBLISHABLE_KEY", "").strip()
        self.webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET", "").strip()
        self.frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000").rstrip("/")
        
        # Mapping optionnel d'IDs de prix récurrents configurés sur Stripe Dashboard
        self.price_ids = {
            "pro_month": os.getenv("STRIPE_PRICE_PRO_MONTHLY", "").strip(),
            "pro_year": os.getenv("STRIPE_PRICE_PRO_YEARLY", "").strip(),
            "enterprise_month": os.getenv("STRIPE_PRICE_ENTERPRISE_MONTHLY", "").strip(),
        }

        if self.secret_key:
            stripe.api_key = self.secret_key
            log.info("StripeService initialisé avec clé secrète Stripe")
        else:
            log.warning("StripeService: STRIPE_SECRET_KEY non configuré. Mode simulation actif.")

    @property
    def is_configured(self) -> bool:
        """Retourne True si une vraie clé Stripe valide est configurée."""
        return bool(self.secret_key and not self.secret_key.startswith("sk_test_placeholder"))

    def get_public_config(self) -> Dict[str, Any]:
        """Retourne les paramètres publics pour le frontend."""
        return {
            "publishable_key": self.publishable_key,
            "stripe_configured": self.is_configured,
            "plans": PLANS,
            "currency": "eur",
        }

    async def get_or_create_customer(self, user: User, session: AsyncSession) -> str:
        """
        Récupère ou crée un client Stripe associé à l'utilisateur de manière idempotente.
        Met à jour stripe_customer_id dans la base de données.
        """
        if user.stripe_customer_id:
            return user.stripe_customer_id

        customer_id: str
        if self.is_configured:
            idempotency_key = f"cust-create-user-{user.id}"
            try:
                customer = stripe.Customer.create(
                    email=user.email or f"{user.username}@hakimagent.local",
                    name=user.display_name or user.username,
                    metadata={"user_id": str(user.id), "username": user.username},
                    idempotency_key=idempotency_key,
                )
                customer_id = customer.id
            except Exception as e:
                log.error("Échec création Customer Stripe pour user %s: %s", user.id, str(e))
                raise
        else:
            # Mode simulation
            customer_id = f"cus_sim_{user.id}_{int(time.time())}"

        user.stripe_customer_id = customer_id
        await session.commit()
        log.info("Client Stripe assigné à user %s: %s", user.id, customer_id)
        return customer_id

    async def create_checkout_session(
        self,
        user: User,
        tier: str,
        interval: str = "month",
        session: AsyncSession = None,
    ) -> Dict[str, Any]:
        """
        Crée une session Stripe Checkout pour un abonnement récurrent.
        
        Args:
            user: Instance de l'utilisateur SQLAlchemy
            tier: Identifiant de l'offre ("pro", "enterprise")
            interval: Fréquence ("month" ou "year")
            session: Session SQLAlchemy async
        """
        plan = get_plan_by_id(tier)
        if not plan:
            raise ValueError(f"Plan inconnu: {tier}")

        if tier == "free":
            # Le plan gratuit ne nécessite pas de paiement Stripe
            user.subscription_tier = "free"
            user.subscription_status = "active"
            if session:
                await session.commit()
            return {
                "checkout_url": f"{self.frontend_url}/pricing?downgraded=true",
                "session_id": "free_tier",
                "simulated": False,
            }

        price_cents = plan["price_yearly_cents"] if interval == "year" else plan["price_monthly_cents"]
        price_id_key = f"{tier}_{interval}"
        stripe_price_id = self.price_ids.get(price_id_key)

        customer_id = await self.get_or_create_customer(user, session)
        success_url = f"{self.frontend_url}/pricing/success?session_id={{CHECKOUT_SESSION_ID}}"
        cancel_url = f"{self.frontend_url}/pricing/cancel"

        # Clé d'idempotence dérivée de l'utilisateur, du plan et du créneau horaire
        idempotency_key = f"checkout-{user.id}-{tier}-{interval}-{int(time.time() // 60)}"

        if self.is_configured:
            # Construction des line_items
            if stripe_price_id:
                line_items = [{"price": stripe_price_id, "quantity": 1}]
            else:
                # Mode dynamique price_data si pas de Price ID pré-enregistré
                interval_stripe = "year" if interval == "year" else "month"
                line_items = [
                    {
                        "price_data": {
                            "currency": plan["currency"],
                            "product_data": {
                                "name": f"HakimAgent — {plan['name']}",
                                "description": plan["description"],
                            },
                            "unit_amount": price_cents,
                            "recurring": {"interval": interval_stripe},
                        },
                        "quantity": 1,
                    }
                ]

            try:
                checkout_session = stripe.checkout.Session.create(
                    customer=customer_id,
                    mode="subscription",
                                        line_items=line_items,
                    success_url=success_url,
                    cancel_url=cancel_url,
                    metadata={
                        "user_id": str(user.id),
                        "tier": tier,
                        "interval": interval,
                    },
                    subscription_data={
                        "metadata": {
                            "user_id": str(user.id),
                            "tier": tier,
                        }
                    },
                    idempotency_key=idempotency_key,
                )
                checkout_url = checkout_session.url
                session_id = checkout_session.id
            except Exception as e:
                log.error("Erreur création Checkout Session Stripe: %s", str(e))
                raise
        else:
            # Simulation en local sans credentials Stripe
            session_id = f"cs_test_sim_{user.id}_{tier}_{int(time.time())}"
            checkout_url = f"{self.frontend_url}/pricing/success?session_id={session_id}&simulated=true"

        # Enregistrement de la commande en statut pending
        if session:
            order = PaymentOrder(
                user_id=user.id,
                stripe_session_id=session_id,
                amount_cents=price_cents,
                currency=plan["currency"],
                status="pending",
                tier=tier,
                billing_reason="checkout_subscription",
            )
            session.add(order)
            await session.commit()

        log.info("Checkout Session créée [user=%s, tier=%s, session_id=%s]", user.id, tier, session_id)
        return {
            "checkout_url": checkout_url,
            "session_id": session_id,
            "simulated": not self.is_configured,
        }

    async def create_customer_portal_session(
        self,
        user: User,
        return_url: Optional[str] = None,
        session: AsyncSession = None,
    ) -> Dict[str, Any]:
        """
        Génère une session sécurisée pour le portail client Stripe
        (gestion de carte bancaire, téléchargement des factures, annulation d'abonnement).
        """
        customer_id = await self.get_or_create_customer(user, session)
        target_return = return_url or f"{self.frontend_url}/pricing"

        if self.is_configured:
            try:
                portal_session = stripe.billing_portal.Session.create(
                    customer=customer_id,
                    return_url=target_return,
                )
                return {"portal_url": portal_session.url, "simulated": False}
            except Exception as e:
                log.error("Erreur création Portal Session Stripe: %s", str(e))
                raise
        else:
            return {
                "portal_url": f"{target_return}?portal_simulated=true",
                "simulated": True,
            }

    async def process_webhook(
        self,
        payload: bytes,
        sig_header: Optional[str],
        session: AsyncSession,
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Valide et traite un événement Stripe de manière idempotente et transactionnelle.
        
        Garanties:
        - Signature cryptographique obligatoire si webhook_secret configuré.
        - Déduplication stricte par event_id : si déjà traité, retourne succès immédiat (200 OK) sans re-traiter.
        - Traitement des événements majeurs :
            * checkout.session.completed
            * customer.subscription.created / updated
            * customer.subscription.deleted
            * invoice.payment_succeeded
            * invoice.payment_failed
        """
        event: Dict[str, Any]

        if self.is_configured and self.webhook_secret:
            if not sig_header:
                log.warning("Webhook Stripe rejeté: header stripe-signature manquant")
                return False, "missing_signature", {}
            try:
                event = stripe.Webhook.construct_event(
                    payload=payload,
                    sig_header=sig_header,
                    secret=self.webhook_secret,
                )
            except stripe.SignatureVerificationError as e:
                log.warning("Signature Webhook Stripe invalide: %s", str(e))
                return False, "invalid_signature", {}
            except Exception as e:
                log.error("Erreur parsing payload Webhook Stripe: %s", str(e))
                return False, "invalid_payload", {}
        else:
            # Mode simulation ou test
            import json
            try:
                event = json.loads(payload.decode("utf-8"))
            except Exception as e:
                return False, f"json_decode_error: {str(e)}", {}

        if hasattr(event, "to_dict"):
            event = event.to_dict()
        elif hasattr(event, "to_dict_recursive"):
            event = event.to_dict_recursive()

        event_id = event.get("id") or f"evt_fallback_{int(time.time())}"
        event_type = event.get("type", "unknown")
        data_object = event.get("data", {}).get("object", {})

        # Déduplication d'événements (Idempotency)
        stmt = select(WebhookEvent).where(WebhookEvent.event_id == event_id)
        res = await session.execute(stmt)
        existing_event = res.scalar_one_or_none()

        if existing_event and existing_event.status == "processed":
            log.info("Événement Stripe déjà traité (déduplication): %s (%s)", event_id, event_type)
            return True, "already_processed", {"event_id": event_id, "type": event_type}

        if not existing_event:
            existing_event = WebhookEvent(
                event_id=event_id,
                event_type=event_type,
                status="pending",
                payload=event,
            )
            session.add(existing_event)
            await session.flush()

        try:
            # Dispatch selon le type d'événement
            if event_type == "checkout.session.completed":
                await self._handle_checkout_completed(data_object, session)

            elif event_type in ("customer.subscription.created", "customer.subscription.updated"):
                await self._handle_subscription_updated(data_object, session)

            elif event_type == "customer.subscription.deleted":
                await self._handle_subscription_deleted(data_object, session)

            elif event_type == "invoice.payment_succeeded":
                await self._handle_invoice_succeeded(data_object, session)

            elif event_type == "invoice.payment_failed":
                await self._handle_invoice_failed(data_object, session)

            else:
                log.info("Événement Stripe ignoré (sans impact d'état): %s", event_type)

            existing_event.status = "processed"
            existing_event.processed_at = datetime.utcnow()
            await session.commit()
            log.info("Événement Stripe traité avec succès: %s (%s)", event_id, event_type)
            return True, "processed", {"event_id": event_id, "type": event_type}

        except Exception as e:
            existing_event.status = "failed"
            existing_event.error_message = str(e)
            await session.commit()
            log.error("Erreur lors du traitement de l'événement %s: %s", event_id, str(e))
            return False, f"processing_error: {str(e)}", {"event_id": event_id}

    async def _handle_checkout_completed(self, session_obj: Dict[str, Any], session: AsyncSession) -> None:
        """Active l'abonnement suite à une session Checkout réussie."""
        metadata = session_obj.get("metadata") or {}
        user_id_str = metadata.get("user_id")
        tier = metadata.get("tier", "pro")
        subscription_id = session_obj.get("subscription")
        customer_id = session_obj.get("customer")
        session_id = session_obj.get("id")

        user: Optional[User] = None
        if user_id_str and str(user_id_str).isdigit():
            stmt = select(User).where(User.id == int(user_id_str))
            res = await session.execute(stmt)
            user = res.scalar_one_or_none()

        if not user and customer_id:
            stmt = select(User).where(User.stripe_customer_id == customer_id)
            res = await session.execute(stmt)
            user = res.scalar_one_or_none()

        if user:
            user.subscription_tier = tier
            user.subscription_status = "active"
            if customer_id:
                user.stripe_customer_id = customer_id
            if subscription_id:
                user.stripe_subscription_id = str(subscription_id)
            user.cancel_at_period_end = 0

            # Mettre à jour l'ordre de paiement
            if session_id:
                order_stmt = select(PaymentOrder).where(PaymentOrder.stripe_session_id == session_id)
                order_res = await session.execute(order_stmt)
                order = order_res.scalar_one_or_none()
                if order:
                    order.status = "succeeded"
                    order.updated_at = datetime.utcnow()

            log.info("Abonnement activé pour l'utilisateur %s -> Tier: %s", user.id, tier)

    async def _handle_subscription_updated(self, sub_obj: Dict[str, Any], session: AsyncSession) -> None:
        """Met à jour le statut, les dates de renouvellement et l'état de résiliation."""
        customer_id = sub_obj.get("customer")
        status = sub_obj.get("status", "active")
        current_period_end_ts = sub_obj.get("current_period_end")
        cancel_at_period_end = 1 if sub_obj.get("cancel_at_period_end") else 0
        subscription_id = sub_obj.get("id")

        if not customer_id:
            return

        stmt = select(User).where(User.stripe_customer_id == customer_id)
        res = await session.execute(stmt)
        user = res.scalar_one_or_none()

        if user:
            user.subscription_status = status
            user.stripe_subscription_id = subscription_id
            user.cancel_at_period_end = cancel_at_period_end
            if current_period_end_ts:
                try:
                    user.current_period_end = datetime.fromtimestamp(current_period_end_ts, tz=timezone.utc).replace(tzinfo=None)
                except Exception:
                    pass
            log.info("Abonnement mis à jour pour user %s: status=%s", user.id, status)

    async def _handle_subscription_deleted(self, sub_obj: Dict[str, Any], session: AsyncSession) -> None:
        """Passe l'utilisateur au forfait gratuit suite à la fin de l'abonnement."""
        customer_id = sub_obj.get("customer")
        if not customer_id:
            return

        stmt = select(User).where(User.stripe_customer_id == customer_id)
        res = await session.execute(stmt)
        user = res.scalar_one_or_none()

        if user:
            user.subscription_tier = "free"
            user.subscription_status = "canceled"
            user.cancel_at_period_end = 0
            user.stripe_subscription_id = None
            log.info("Abonnement terminé pour user %s -> retour au forfait gratuit (free)", user.id)

    async def _handle_invoice_succeeded(self, invoice_obj: Dict[str, Any], session: AsyncSession) -> None:
        """Enregistre le paiement de renouvellement d'abonnement dans l'historique."""
        customer_id = invoice_obj.get("customer")
        amount_paid = invoice_obj.get("amount_paid", 0)
        currency = invoice_obj.get("currency", "eur")
        payment_intent_id = invoice_obj.get("payment_intent")
        billing_reason = invoice_obj.get("billing_reason", "subscription_cycle")

        if not customer_id:
            return

        stmt = select(User).where(User.stripe_customer_id == customer_id)
        res = await session.execute(stmt)
        user = res.scalar_one_or_none()

        if user and amount_paid > 0:
            order = PaymentOrder(
                user_id=user.id,
                stripe_payment_intent_id=str(payment_intent_id) if payment_intent_id else None,
                amount_cents=amount_paid,
                currency=currency,
                status="succeeded",
                tier=user.subscription_tier or "pro",
                billing_reason=billing_reason,
            )
            session.add(order)
            log.info("Facture acquittée (%s centimes %s) pour user %s", amount_paid, currency, user.id)

    async def _handle_invoice_failed(self, invoice_obj: Dict[str, Any], session: AsyncSession) -> None:
        """Marque l'abonnement comme past_due lors d'un échec de prélèvement."""
        customer_id = invoice_obj.get("customer")
        if not customer_id:
            return

        stmt = select(User).where(User.stripe_customer_id == customer_id)
        res = await session.execute(stmt)
        user = res.scalar_one_or_none()

        if user:
            user.subscription_status = "past_due"
            log.warning("Échec prélèvement facture pour user %s -> statut: past_due", user.id)


# Instance globale du service de facturation
stripe_service = StripeService()
