# Intégration du Paiement & des Abonnements Stripe — HakimAgent / AXIOM

Ce document décrit l'architecture, la configuration et l'exploitation du système de facturation et d'abonnements récurrents Stripe pour la plateforme **HakimAgent / AXIOM**.

---

## 1. Principes d'Ingénierie & Sécurité Financière

L'intégration a été conçue selon les règles strictes d'ingénierie financière (*Payments & Billing Engineering*) :

1. **Aucune donnée de carte bancaire sur nos serveurs (SAQ-A) :**
   - Toutes les transactions transitent par les formulaires hébergés officiels **Stripe Checkout** et **Stripe Customer Portal**.
   - Aucun numéro de carte (PAN) ou code CVC n'est intercepté ou stocké.
2. **Idempotence stricte :**
   - Chaque création de session Checkout porte une clé d'idempotence unique scoped par utilisateur et horodatage pour interdire toute double facturation lors de clics répétés ou réessais réseau.
3. **Les Webhooks sont la source de vérité :**
   - L'activation ou la modification d'un abonnement ne repose **jamais** sur la simple redirection du navigateur client (un utilisateur peut fermer son onglet).
   - Les droits sont octroyés et mis à jour uniquement sur réception des événements Webhooks signés par Stripe.
4. **Déduplication durable des événements :**
   - Chaque événement reçu est enregistré avec son `event_id` unique dans la table `webhook_events`. Si Stripe réémet un événement déjà traité, le serveur répond `200 OK` instantanément sans réexécuter les mutations.
5. **Gestion monétaire en centimes entiers (Minor Units) :**
   - Tous les montants (`amount_cents`) sont stockés et calculés sous forme d'entiers stricts (ex. `2900` pour 29,00 €), éliminant tout bug d'arrondi lié aux nombres flottants (`float`).

---

## 2. Variables d'Environnement

Ajoutez les variables suivantes dans votre fichier `backend/.env` :

```ini
# ---- Stripe Payment & Subscriptions ----
# Clés API disponibles sur https://dashboard.stripe.com/test/apikeys
STRIPE_SECRET_KEY=sk_test_51...
STRIPE_PUBLISHABLE_KEY=pk_test_51...

# Secret de signature du Webhook (fourni par 'stripe listen' ou le Dashboard Stripe)
STRIPE_WEBHOOK_SECRET=whsec_...

# Optionnel : IDs de prix récurrents si configurés dans votre catalogue de produits Stripe
# Si laissés vides, des line_items dynamiques conformes sont automatiquement générés
STRIPE_PRICE_PRO_MONTHLY=
STRIPE_PRICE_PRO_YEARLY=
STRIPE_PRICE_ENTERPRISE_MONTHLY=

# URL du frontend pour les redirections
FRONTEND_URL=http://localhost:3000
```

> **Mode Simulation automatique :** Si aucune clé `STRIPE_SECRET_KEY` n'est définie (ex. environnement de test local ou sans compte Stripe immédiat), le système bascule de façon transparente en mode simulation : les liens de redirection et de webhook fonctionnent sans bloquer l'application.

---

## 3. Modèles de Données & Base de Données

Les modèles SQLite / SQLAlchemy suivants gèrent la persistance :

### Modèle `User` (`backend/axiom/db/models.py`)
- `stripe_customer_id` : Identifiant client Stripe (`cus_...`).
- `subscription_tier` : Forfait actif (`free`, `pro`, `enterprise`).
- `subscription_status` : Statut Stripe (`active`, `trialing`, `past_due`, `canceled`).
- `stripe_subscription_id` : Identifiant de l'abonnement Stripe (`sub_...`).
- `current_period_end` : Date de fin de la période en cours.
- `cancel_at_period_end` : Indicateur de résiliation programmée (`1` si actif jusqu'à échéance, `0` sinon).

### Modèle `WebhookEvent`
- `event_id` : ID unique de l'événement (`evt_...`, contrainte `UNIQUE`).
- `event_type` : Type d'événement (`checkout.session.completed`, etc.).
- `status` : Statut de traitement (`pending`, `processed`, `failed`).
- `payload` : Contenu JSON complet de l'événement.
- `processed_at` : Horodatage UTC du traitement.

### Modèle `PaymentOrder`
- `stripe_session_id` / `stripe_payment_intent_id` : Références Stripe.
- `amount_cents` : Montant en centimes (ex. 2900 pour 29.00 EUR).
- `currency` : Code devise ISO 4217 (`eur`).
- `status` : Statut de la commande (`pending`, `succeeded`, `failed`, `refunded`).

---

## 4. Endpoints API REST

Toutes les routes sont préfixées par `/api/v1/billing` (et `/api/billing`) :

| Méthode | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/config` | Non | Retourne les forfaits, prix et la clé publique Stripe |
| `GET` | `/status` | Oui (JWT) | Retourne l'état de l'abonnement et l'historique des factures |
| `POST` | `/checkout` | Oui (JWT) | Crée une session Stripe Checkout et retourne `{ "checkout_url": "..." }` |
| `POST` | `/portal` | Oui (JWT) | Crée une session Customer Portal pour gérer la CB et les factures |
| `POST` | `/webhook` | Signature | Reçoit et valide cryptographiquement les événements Stripe |

---

## 5. Guide de Test Local avec Stripe CLI

### A. Écouter les Webhooks en Local
Téléchargez la [CLI Stripe](https://stripe.com/docs/stripe-cli) et connectez votre compte :
```bash
stripe login
```

Transférez les webhooks vers votre serveur local FastAPI :
```bash
stripe listen --forward-to localhost:8000/api/v1/billing/webhook
```
La CLI affichera votre secret de webhook local :
```
> Ready! Your webhook signing secret is whsec_123456...
```
Copiez cette valeur dans `backend/.env` sous `STRIPE_WEBHOOK_SECRET`.

### B. Déclencher des Événements de Test
Dans un autre terminal :
```bash
# Simuler une souscription terminée
stripe trigger checkout.session.completed

# Simuler une résiliation d'abonnement
stripe trigger customer.subscription.deleted

# Simuler un paiement d'échéance réussie
stripe trigger invoice.payment_succeeded
```

### C. Cartes de Test Stripe Recommandées
- **Succès standard** : `4242 4242 4242 4242`, Date > future, CVC `123`.
- **Authentification 3D Secure requise** : `4000 0027 6000 3184`.
- **Refus pour fonds insuffisants** : `4000 0000 0000 0119`.

---

## 6. Interface Utilisateur (Frontend)

- **Page des tarifs** : accessible via `/pricing` et le menu de navigation latéral ("Tarifs & Pro").
  - Présentation des forfaits Starter (0€), Pro Développeur (29€/mois) et Entreprise (99€/mois).
  - Bascule mensuelle / annuelle (-20%).
  - Bouton intelligent : "Passer à l'offre Pro" ou "Gérer mon abonnement" (si déjà Pro).
  - Foire aux questions (FAQ) interactive.
- **Page de confirmation** : `/pricing/success` avec rappel des avantages activés.
- **Page d'annulation** : `/pricing/cancel` informant l'utilisateur qu'aucun débit n'a eu lieu.
- **Portail Client** : accès instantané aux reçus PDF et modification de CB via le bouton officiel Stripe Customer Portal.
