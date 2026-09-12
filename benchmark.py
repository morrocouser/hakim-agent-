#!/usr/bin/env python3
"""AXIOM BENCHMARK SUITE v1.0 - Evaluation complete des performances"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import os, time, json, statistics, urllib.request, urllib.error
from pathlib import Path
from dataclasses import dataclass, field

ROOT    = Path(__file__).parent
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

API_BASE = "http://127.0.0.1:8000/api/v1"

R="\033[91m"; G="\033[92m"; Y="\033[93m"; C="\033[96m"
W="\033[97m"; M="\033[95m"; DIM="\033[2m"; BOLD="\033[1m"; RST="\033[0m"

# ---------------------------------------------------------------
@dataclass
class BenchResult:
    name: str
    passed: int = 0
    failed: int = 0
    latencies_ms: list = field(default_factory=list)
    errors: list = field(default_factory=list)

    @property
    def total(self): return self.passed + self.failed
    @property
    def success_rate(self): return (self.passed/self.total*100) if self.total else 0
    @property
    def avg_ms(self): return statistics.mean(self.latencies_ms) if self.latencies_ms else 0
    @property
    def p95_ms(self):
        if not self.latencies_ms: return 0
        s = sorted(self.latencies_ms)
        return s[int(len(s)*0.95)] if len(s)>1 else s[0]
    @property
    def min_ms(self): return min(self.latencies_ms) if self.latencies_ms else 0
    @property
    def max_ms(self): return max(self.latencies_ms) if self.latencies_ms else 0

# ---------------------------------------------------------------
def hdr(t): print(f"\n{BOLD}{C}{'='*62}{RST}\n{BOLD}{C}  {t}{RST}\n{BOLD}{C}{'='*62}{RST}")
def sub(t): print(f"\n  {BOLD}{W}{t}{RST}\n  {DIM}{'-'*44}{RST}")
def ok(m):  print(f"    {G}[OK]{RST}  {m}")
def ko(m):  print(f"    {R}[KO]{RST}  {m}")
def inf(m): print(f"    {DIM}[i]   {m}{RST}")

def http_post(path, data):
    url = f"{API_BASE}{path}"
    req = urllib.request.Request(url, data=json.dumps(data).encode(),
                                 headers={"Content-Type":"application/json"}, method="POST")
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read()), (time.perf_counter()-t0)*1000
    except Exception as e:
        return {"error": str(e)}, (time.perf_counter()-t0)*1000

def http_get(path):
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(f"{API_BASE}{path}", timeout=10) as r:
            return json.loads(r.read()), (time.perf_counter()-t0)*1000
    except Exception as e:
        return {"error": str(e)}, (time.perf_counter()-t0)*1000

# ===============================================================
#  BENCH 1 - Routage Interne (sans LLM)
# ===============================================================
ROUTING_CASES = [
    ("Implementer une API REST avec FastAPI",           "CODE",    "AGENT_CODER",      "Code simple"),
    ("Debug stack trace asyncio Python",                "DEBUG",   "AGENT_DEBUGGER",   "Bug critique"),
    ("Architecture microservices avec Kafka",           "ARCH",    "AGENT_ARCHITECT",  "Architecture"),
    ("Analyser ce CSV de donnees de ventes",            "DATA",    "AGENT_ANALYST",    "Analyse data"),
    ("Rediger un README pour le projet",                "DOC",     "AGENT_WRITER",     "Documentation"),
    ("Rechercher les dernieres tendances AI",           "RESEARCH","AGENT_RESEARCHER", "Recherche"),
    ("Planifier le sprint Q3 avec priorites",           "PLAN",    "AGENT_PLANNER",    "Planification"),
    ("C'est quoi Python?",                              "QUICK",   "AGENT_QUICKSHOT",  "Question rapide"),
    ("Refactorer ce code legacy complexe distribue",    "CODE",    "AGENT_CODER",      "Code complexe"),
    ("Strategie roadmap produit 2025",                  "PLAN",    "AGENT_PLANNER",    "Strategie"),
    ("Corriger ce crash en production urgent prod",     "DEBUG",   "AGENT_DEBUGGER",   "Bug urgent"),
    ("Generer rapport de donnees JSON analyse",         "DATA",    "AGENT_ANALYST",    "Rapport JSON"),
]

def bench_routing():
    hdr("BENCH 1 -- Routage d'Agents (scoring interne)")
    try:
        from axiom.core.scoring import score_and_route
        from axiom.models.schemas import TaskType
    except ImportError as e:
        print(f"  {R}Import impossible: {e}{RST}"); return BenchResult("Routage Agents")

    type_map = {"CODE":TaskType.CODE,"DEBUG":TaskType.DEBUG,"ARCH":TaskType.ARCH,
                "DATA":TaskType.DATA,"DOC":TaskType.DOC,"RESEARCH":TaskType.RESEARCH,
                "PLAN":TaskType.PLAN,"QUICK":TaskType.QUICK}

    r = BenchResult("Routage Agents")
    agent_dist, model_dist = {}, {}

    sub("12 scenarios de routage")
    for desc, ttype_s, exp, label in ROUTING_CASES:
        ttype = type_map.get(ttype_s, TaskType.QUICK)
        t0 = time.perf_counter()
        a  = score_and_route(desc, ttype)
        ms = (time.perf_counter()-t0)*1000
        r.latencies_ms.append(ms)

        got = a.agent.value
        agent_dist[got] = agent_dist.get(got, 0)+1
        model_dist[a.model.value] = model_dist.get(a.model.value, 0)+1

        if got == exp:
            r.passed += 1
            ok(f"{label:<22} -> {G}{got.replace('AGENT_',''):<14}{RST} score={C}{a.score:.2f}{RST} {ms:.3f}ms")
        else:
            r.failed += 1
            ko(f"{label:<22} -> {R}{got.replace('AGENT_',''):<14}{RST} (attendu {Y}{exp.replace('AGENT_','')}{RST}) {ms:.3f}ms")
            r.errors.append(f"{label}: got {got} expected {exp}")

    sub("Distribution agents")
    for ag, cnt in sorted(agent_dist.items(), key=lambda x:-x[1]):
        print(f"    {M}{ag.replace('AGENT_',''):<16}{RST} {'|'*cnt} ({cnt})")

    sub("Distribution modeles")
    for m, cnt in sorted(model_dist.items(), key=lambda x:-x[1]):
        short = m.split("/")[-1] if "/" in m else m
        print(f"    {C}{short:<28}{RST} {'|'*cnt} ({cnt})")

    return r

# ===============================================================
#  BENCH 2 - Selection de Modele
# ===============================================================
MODEL_CASES = [
    (2.0,2.0,2.0,2.0,3.0, "SMALL",  "Tache triviale   -> SMALL"),
    (4.0,4.0,4.0,5.0,4.0, "MEDIUM", "Tache moyenne    -> MEDIUM"),
    (6.0,6.0,5.0,6.0,6.0, "LARGE",  "Tache complexe   -> LARGE"),
    (9.0,9.0,8.0,5.0,9.0, "BEST",   "Tache critique   -> BEST"),
    (8.0,3.0,6.0,2.0,7.0, "SMALL",  "Complexe urgent  -> SMALL (override)"),
]

def bench_model():
    hdr("BENCH 2 -- Selection de Modele")
    try:
        from axiom.core.scoring import select_model, calculate_score
        from axiom.models.schemas import ScoringDimensions, ModelName
    except ImportError as e:
        print(f"  {R}Import impossible: {e}{RST}"); return BenchResult("Selection Modele")

    # Map actual model enum values to expected tier names
    tier_map = {
        ModelName.SMALL: "SMALL",
        ModelName.MEDIUM: "MEDIUM",
        ModelName.LARGE: "LARGE",
        ModelName.BEST: "BEST",
    }

    r = BenchResult("Selection Modele")
    sub("Precision de selection par score 5D")
    for c,st,cr,sp,dm,exp,label in MODEL_CASES:
        dims = ScoringDimensions(complexity=c,stakes=st,creativity=cr,speed_need=sp,domain_match=dm)
        t0   = time.perf_counter()
        score= calculate_score(dims)
        m    = select_model(score, dims)
        ms   = (time.perf_counter()-t0)*1000
        r.latencies_ms.append(ms)

        got_tier = tier_map.get(m, m.value)
        short = m.value.split("/")[-1] if "/" in m.value else m.value
        match = (got_tier == exp)
        if match:
            r.passed += 1
            ok(f"{label:<40} score={score:.2f} -> {G}{got_tier}{RST} ({short})  {ms:.3f}ms")
        else:
            r.failed += 1
            ko(f"{label:<40} attendu:{Y}{exp}{RST} got:{R}{got_tier}{RST} ({short})")
            r.errors.append(f"{label}: got {got_tier}, expected tier {exp}")
    return r

# ===============================================================
#  BENCH 3 - API HTTP
# ===============================================================
HTTP_CASES = [
    {"description":"Implementer un cache Redis",          "task_type":"CODE"},
    {"description":"Bug NullPointerException en prod",    "task_type":"DEBUG"},
    {"description":"Architecture event-driven scalable",  "task_type":"ARCH"},
    {"description":"Analyse donnees utilisateurs CSV",    "task_type":"DATA"},
    {"description":"Rediger la documentation API",        "task_type":"DOC"},
    {"description":"C'est quoi Docker?",                  "task_type":"QUICK"},
    {"description":"Plan de sprint Q4 2025",              "task_type":"PLAN"},
    {"description":"Recherche concurrents startup IA",    "task_type":"RESEARCH"},
]

def bench_http():
    hdr("BENCH 3 -- API HTTP Performance")
    r = BenchResult("API HTTP")

    sub("Health Check")
    body, ms = http_get("/health")
    if "error" in body:
        ko(f"Backend non disponible: {body['error']}")
        ko("Lancez d'abord: cd backend && python -m axiom.api.main")
        r.failed += 1; r.errors.append("Backend offline")
        return r
    ok(f"GET /health  {ms:.1f}ms | status={body.get('status')} | openrouter={body.get('openrouter_configured')}")
    r.passed += 1; r.latencies_ms.append(ms)

    sub("Agents Registry")
    body, ms = http_get("/agents")
    if "error" not in body:
        ok(f"GET /agents  {ms:.1f}ms | {len(body)} agents enregistres")
        for name, cfg in body.items():
            inf(f"{cfg.get('icon','')}  {cfg.get('label',''):<20} model={cfg.get('default_model','')}")
        r.passed += 1; r.latencies_ms.append(ms)
    else:
        ko(f"GET /agents -> {body['error']}"); r.failed += 1

    sub("POST /score -- 8 scenarios")
    for case in HTTP_CASES:
        body, ms = http_post("/score", case)
        r.latencies_ms.append(ms)
        if "error" in body and "agent" not in body:
            ko(f"{case['description'][:35]:<35} ERREUR {ms:.1f}ms"); r.failed += 1
        else:
            ag = body.get("agent","?").replace("AGENT_","")
            sc = body.get("score", 0)
            ok(f"{case['description'][:35]:<35} -> {G}{ag:<12}{RST} score={C}{sc:.1f}{RST}  {ms:.1f}ms")
            r.passed += 1

    sub("Stress Test -- 20 requetes sequentielles")
    stress = []
    for i in range(20):
        _, ms = http_post("/score", {"description":f"requete stress #{i}", "task_type":"QUICK"})
        stress.append(ms); r.latencies_ms.append(ms)
    avg = statistics.mean(stress)
    std = statistics.stdev(stress) if len(stress)>1 else 0
    ok(f"20 req | avg={avg:.1f}ms  std={std:.1f}ms  min={min(stress):.1f}ms  max={max(stress):.1f}ms")
    r.passed += 1

    # Throughput estimate
    rps = 1000 / avg if avg > 0 else 0
    inf(f"Throughput estime: ~{rps:.0f} req/s (sequentiel)")
    return r

# ===============================================================
#  BENCH 4 - Inference Dimensions
# ===============================================================
INFER_CASES = [
    ("Architecture complexe distribuee microservices", "ARCH", "complexity", 8.0, ">=", "Complexite elevee"),
    ("Bug urgent en prod client attend",               "DEBUG","stakes",     8.0, ">=", "Stakes elevees"),
    ("C'est quoi Python",                              "QUICK","complexity", 3.0, "<=", "Complexite faible"),
    ("Analyse avancee des donnees SQL critiques",      "DATA", "complexity", 6.0, ">=", "Data complexe"),
]

def bench_infer():
    hdr("BENCH 4 -- Inference des Dimensions 5D")
    try:
        from axiom.core.scoring import infer_dimensions
        from axiom.models.schemas import TaskType
    except ImportError as e:
        print(f"  {R}Import impossible: {e}{RST}"); return BenchResult("Inference Dims")

    type_map = {"CODE":TaskType.CODE,"DEBUG":TaskType.DEBUG,"ARCH":TaskType.ARCH,
                "DATA":TaskType.DATA,"DOC":TaskType.DOC,"RESEARCH":TaskType.RESEARCH,
                "PLAN":TaskType.PLAN,"QUICK":TaskType.QUICK}

    r = BenchResult("Inference Dimensions")
    sub("Validation dimensions inferees")
    for desc, ttype_s, dim, threshold, op, label in INFER_CASES:
        ttype = type_map.get(ttype_s, TaskType.QUICK)
        t0  = time.perf_counter()
        d   = infer_dimensions(desc, ttype)
        ms  = (time.perf_counter()-t0)*1000
        r.latencies_ms.append(ms)

        val    = getattr(d, dim)
        passed = (val >= threshold) if op == ">=" else (val <= threshold)
        if passed:
            r.passed += 1
            ok(f"{label:<24} {dim}={G}{val:.1f}{RST} {op} {threshold}  {ms:.3f}ms")
        else:
            r.failed += 1
            ko(f"{label:<24} {dim}={R}{val:.1f}{RST} (attendu {op} {threshold})")
            r.errors.append(f"{dim}={val}, expected {op} {threshold}")
    return r

# ===============================================================
#  RAPPORT FINAL
# ===============================================================
def report(results):
    print(f"\n{BOLD}{C}{'='*62}{RST}")
    print(f"{BOLD}{C}  RAPPORT FINAL -- AXIOM BENCHMARK SUITE{RST}")
    print(f"{BOLD}{C}{'='*62}{RST}")

    tp = tf = 0
    for r in results:
        tp += r.passed; tf += r.failed
        color = G if r.success_rate>=80 else Y if r.success_rate>=60 else R
        badge = "[**]" if r.success_rate==100 else "[OK]" if r.success_rate>=80 else "[!!]"
        print(f"\n  {badge} {BOLD}{W}{r.name}{RST}")
        print(f"       Reussite  : {color}{r.success_rate:.0f}%{RST} ({r.passed}/{r.total})")
        if r.latencies_ms:
            print(f"       Latence   : avg={C}{r.avg_ms:.3f}ms{RST}"
                  f" | p95={Y}{r.p95_ms:.3f}ms{RST}"
                  f" | min={r.min_ms:.3f} / max={r.max_ms:.3f}ms")
        for e in r.errors[:3]:
            print(f"       {R}  > {e}{RST}")

    grand = tp+tf
    rate  = (tp/grand*100) if grand else 0
    note  = int(rate)
    nc    = G if note>=90 else Y if note>=70 else R

    print(f"\n{BOLD}{C}{'-'*62}{RST}")
    print(f"\n  {BOLD}TOTAL : {tp}/{grand} tests reussis{RST}")
    print(f"\n  {BOLD}{nc}NOTE GLOBALE : {note} / 100{RST}  " + ("*"*int(note/20)))

    filled = int(40*note/100)
    bar    = f"{G}{'#'*filled}{DIM}{'.'*(40-filled)}{RST}"
    print(f"\n  [{bar}] {note}%")

    print(f"\n{BOLD}{W}  RECOMMANDATIONS :{RST}")
    if rate < 70:
        print(f"  {R}  > Routage a ameliorer -- verifier AGENT_ROUTING dans scoring.py{RST}")
    if any(r.p95_ms>50 for r in results if r.latencies_ms):
        print(f"  {Y}  > Latence p95>50ms -- envisager cache sur infer_dimensions(){RST}")
    if rate >= 90:
        print(f"  {G}  > Excellent ! AXIOM est pret pour la production.{RST}")
    elif rate >= 70:
        print(f"  {Y}  > Bon. Quelques ajustements de routage amelioreraient la precision.{RST}")
    print(f"\n{BOLD}{C}{'='*62}{RST}\n")

    out = ROOT / "benchmark_results.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "note": note, "global_rate_pct": round(rate,2),
            "total_passed": tp, "total_failed": tf,
            "benches": [{"name":r.name,"passed":r.passed,"failed":r.failed,
                         "success_rate_pct":round(r.success_rate,2),
                         "avg_ms":round(r.avg_ms,4),"p95_ms":round(r.p95_ms,4),
                         "errors":r.errors} for r in results]
        }, f, indent=2, ensure_ascii=False)
    print(f"  {DIM}Resultats JSON -> {out}{RST}\n")
    return note

# ===============================================================
#  ENTRY POINT
# ===============================================================
if __name__ == "__main__":
    print(f"\n{BOLD}{M}+====================================================+{RST}")
    print(f"{BOLD}{M}|     AXIOM BENCHMARK SUITE v1.0                     |{RST}")
    print(f"{BOLD}{M}|     Orchestrateur Multi-Agents IA                  |{RST}")
    print(f"{BOLD}{M}+====================================================+{RST}")
    print(f"  {DIM}Backend : {BACKEND}{RST}")
    print(f"  {DIM}API     : {API_BASE}{RST}")
    print(f"  {DIM}Heure   : {time.strftime('%Y-%m-%d %H:%M:%S')}{RST}")

    results = [bench_routing(), bench_model(), bench_http(), bench_infer()]
    note    = report(results)
    sys.exit(0 if note >= 70 else 1)
