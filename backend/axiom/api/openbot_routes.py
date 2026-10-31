"""OpenBot API Routes — Coworkers, Dedicated Virtual Computers, Take the Wheel & Audit Ledger."""

from fastapi import APIRouter, HTTPException, Query, Body, Depends
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from axiom.auth.jwt import get_current_user, optional_user
from axiom.db.models import User
from axiom.core.coworker_computer import coworker_manager, ControlState
from axiom.core.policy_gateway import (
    policy_gateway, ActionRequest, InitiatorKind, PolicyDecision
)
from axiom.core.audit_ledger import audit_ledger
from axiom.logging_setup import log

router = APIRouter(prefix="/api/v1", tags=["openbot"])


class TakeWheelRequest(BaseModel):
    operator_id: str = "human_operator"


class RequestHelpRequest(BaseModel):
    reason: str = "Intervention humaine requise (ex. 2FA, CAPTCHA ou validation critique)"


class ExecuteActionRequest(BaseModel):
    tool_name: str
    intent: str
    command: Optional[str] = None
    url: Optional[str] = None
    file_path: Optional[str] = None
    initiator_kind: str = "person"  # "person", "routine", "handoff", "responsibility"
    actor_id: str = "operator"


class SpawnAgencyRequest(BaseModel):
    slug: str = Field(..., description="Slug ou nom de l'agent Agency à instancier, ex. 'code-reviewer' ou 'frontend-developer'")


# -------------------------------------------------------------
# Coworkers & Virtual Computers
# -------------------------------------------------------------

@router.get("/coworkers")
async def list_coworkers(user: Optional[User] = Depends(optional_user)):
    """Liste tous les AI Coworkers avec l'état de leur ordinateur virtuel."""
    return {"coworkers": coworker_manager.list_coworkers()}


@router.get("/coworkers/{coworker_id}")
async def get_coworker(coworker_id: str, user: Optional[User] = Depends(optional_user)):
    """Détail d'un coworker et état de son écran/terminal."""
    coworker = coworker_manager.get_coworker(coworker_id)
    if not coworker:
        raise HTTPException(status_code=404, detail="Coworker introuvable")
    return {"coworker": coworker.dict()}


@router.post("/coworkers/{coworker_id}/take-wheel")
async def take_wheel(coworker_id: str, req: TakeWheelRequest = Body(...), user: User = Depends(get_current_user)):
    """L'humain prend le contrôle direct de l'ordinateur de l'agent ('Take the Wheel')."""
    try:
        updated = coworker_manager.take_the_wheel(coworker_id, req.operator_id)
        return {"status": "ok", "message": "Contrôle pris avec succès", "coworker": updated.dict()}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/coworkers/{coworker_id}/release-wheel")
async def release_wheel(coworker_id: str, req: TakeWheelRequest = Body(...), user: User = Depends(get_current_user)):
    """L'humain restitue les commandes à l'agent ('Release Wheel')."""
    try:
        updated = coworker_manager.release_the_wheel(coworker_id, req.operator_id)
        return {"status": "ok", "message": "Contrôle rendu au coworker", "coworker": updated.dict()}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/coworkers/{coworker_id}/request-help")
async def request_help(coworker_id: str, req: RequestHelpRequest = Body(...), user: User = Depends(get_current_user)):
    """Simule une demande d'aide du coworker (ex: CAPTCHA, 2FA, transaction)."""
    try:
        updated = coworker_manager.request_help(coworker_id, req.reason)
        return {"status": "ok", "coworker": updated.dict()}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/coworkers/{coworker_id}/execute")
async def execute_on_computer(coworker_id: str, req: ExecuteActionRequest = Body(...), user: User = Depends(get_current_user)):
    """Exécute une action sur l'ordinateur virtuel du coworker sous contrôle de gouvernance."""
    try:
        kind = InitiatorKind(req.initiator_kind.lower())
    except ValueError:
        kind = InitiatorKind.PERSON

    try:
        res = coworker_manager.execute_action(
            coworker_id=coworker_id,
            tool_name=req.tool_name,
            intent=req.intent,
            command=req.command,
            url=req.url,
            file_path=req.file_path,
            initiator_kind=kind,
            actor_id=req.actor_id,
        )
        return res
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# -------------------------------------------------------------
# Audit Ledger (OpenBot Traceability & Filter)
# -------------------------------------------------------------

@router.get("/audit")
async def get_audit_trail(
    user: User = Depends(get_current_user),
    nobody_watching: Optional[bool] = Query(None, description="Filtrer les actions sans surveillance humaine"),
    decision: Optional[str] = Query(None, description="Filtrer par décision (ALLOWED, DENIED, REQUIRE_TAKEOVER)"),
    coworker_id: Optional[str] = Query(None, description="Filtrer par coworker"),
    search: Optional[str] = Query(None, description="Recherche textuelle dans l'audit"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """Consulter le registre d'audit gouverné (Audit Ledger)."""
    return audit_ledger.query(
        nobody_watching=nobody_watching,
        decision=decision,
        coworker_id=coworker_id,
        search=search,
        limit=limit,
        offset=offset,
    )


# -------------------------------------------------------------
# Policy Evaluation API
# -------------------------------------------------------------

@router.post("/policy/evaluate")
async def evaluate_policy(req: ActionRequest = Body(...), user: Optional[User] = Depends(optional_user)):
    """Évalue une action sans l'exécuter pour pré-validation par l'UI ou un outil."""
    res = policy_gateway.evaluate(req)
    return res.dict()


# -------------------------------------------------------------
# Routines & Responsabilités
# -------------------------------------------------------------

@router.get("/routines")
async def list_routines(user: Optional[User] = Depends(optional_user)):
    """Liste toutes les routines autonomes des coworkers."""
    all_routines = []
    for c in coworker_manager.list_coworkers():
        for r in c.get("routines", []):
            r_copy = dict(r)
            r_copy["coworker_id"] = c["id"]
            r_copy["coworker_name"] = c["name"]
            all_routines.append(r_copy)
    return {"routines": all_routines}


@router.post("/routines/{routine_id}/run")
async def run_routine(routine_id: str, user: User = Depends(get_current_user)):
    """Déclenche l'exécution autonome d'une routine avec initiator_kind=routine."""
    found_coworker = None
    target_routine = None
    for c in coworker_manager._coworkers.values():
        for r in c.routines:
            if r.id == routine_id:
                found_coworker = c
                target_routine = r
                break
        if target_routine:
            break

    if not found_coworker or not target_routine:
        raise HTTPException(status_code=404, detail="Routine introuvable")

    # Exécution autonome
    res = coworker_manager.execute_action(
        coworker_id=found_coworker.id,
        tool_name="routine_exec",
        intent=f"Exécution autonome de la routine : {target_routine.name}",
        command=target_routine.command_to_run,
        initiator_kind=InitiatorKind.ROUTINE,
        actor_id="system_cron",
    )
    return {
        "status": "ok",
        "routine": target_routine.dict(),
        "execution": res,
    }


# -------------------------------------------------------------
# Agency Agents Catalog & On-Demand Coworker Spawning
# -------------------------------------------------------------

@router.get("/agency-agents")
async def list_agency_agents(
    division: Optional[str] = None,
    q: Optional[str] = None,
    user: Optional[User] = Depends(optional_user),
):
    """Liste tous les 267 agents spécialisés Agency avec filtres par division et recherche."""
    import json
    import os
    if not isinstance(division, str):
        division = None
    if not isinstance(q, str):
        q = None
    catalog_path = os.path.join(
        os.path.dirname(__file__), "..", "data", "agency_agents_catalog.json"
    )
    if not os.path.exists(catalog_path):
        return {"total": 0, "divisions": {}, "agents": []}
    with open(catalog_path, encoding="utf-8") as f:
        data = json.load(f)
    agents = data.get("agents", [])
    if division:
        agents = [a for a in agents if a.get("division") == division]
    if q:
        query = q.lower()
        agents = [
            a for a in agents
            if query in a.get("name", "").lower()
            or query in a.get("description", "").lower()
            or query in a.get("vibe", "").lower()
        ]
    return {
        "total": len(agents),
        "total_available": data.get("total_agents", len(agents)),
        "divisions": data.get("divisions", {}),
        "agents": agents,
    }


@router.post("/coworkers/spawn-agency")
async def spawn_agency_coworker(req: SpawnAgencyRequest = Body(...), user: User = Depends(get_current_user)):
    """Instancie à la demande un des 267 Agency Agents comme coworker avec son ordinateur virtuel."""
    try:
        coworker = coworker_manager.spawn_agency_coworker(req.slug)
        return {
            "status": "ok",
            "message": f"Coworker '{coworker.name}' prêt à l'emploi",
            "coworker": coworker.dict(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

