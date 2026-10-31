"""
HakimAgent - Test End-to-End d'une Tâche Réelle Complète (Étape 8)
Scénario de bout en bout :
1. Conception de l'ergonomie et des tokens UI/UX par @ux_designer
2. Génération et scaffolding d'un site/composant web interactif via WebBuilderTool
3. Sauvegarde physique du prototype dans websites/
4. Audit qualité et validation finale par @qa_reviewer
"""

import os
import sys
import pytest
import asyncio
from pathlib import Path

# Force UTF-8 sous Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

ROOT_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = ROOT_DIR / "backend"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from hakim_agent.supervisor import SupervisorAgent
from hakim_agent.orchestrator import HakimOrchestrator
from hakim_agent.state import AgentStatus, EventBus
from axiom.tools.web_builder_tool import WebBuilderTool


@pytest.mark.asyncio
async def test_full_end_to_end_web_generation_and_validation(tmp_path):
    """
    Exécute un pipeline complet de création web :
    UI/UX -> Scaffolding & Code -> Sauvegarde de fichier -> Audit QA.
    """
    site_slug = "test_qa_showcase"
    site_output_dir = ROOT_DIR / "websites" / site_slug

    # 1. Étape 1 : Conception des spécifications UI/UX
    sup = SupervisorAgent(llm_client=False)
    ux_worker = sup.ux_designer
    ux_res = await ux_worker.execute(
        step="Concevoir une landing page SaaS sombre et épurée avec hero banner et CTA",
        context={},
    )
    assert ux_res["success"] is True
    assert "design_tokens" in ux_res
    tokens = ux_res["design_tokens"]

    # 2. Étape 2 : Génération et Scaffolding via WebBuilderTool
    tool = WebBuilderTool()
    scaffold_res = await tool.execute(
        action="scaffold",
        template="saas_landing",
        site_name=site_slug,
        context={},
    )
    assert scaffold_res.ok is True
    assert "scaffold_html" in scaffold_res.metadata

    # Sauvegarde physique du prototype via action="save_site"
    save_res = await tool.execute(
        action="save_site",
        site_name=site_slug,
        html_content=scaffold_res.metadata["scaffold_html"],
        context={},
    )
    assert save_res.ok is True
    assert "index.html" in save_res.content

    # Vérification que le fichier index.html a bien été créé physiquement
    index_file = site_output_dir / "index.html"
    assert index_file.exists(), f"Le fichier généré {index_file} doit exister"
    html_content = index_file.read_text(encoding="utf-8")
    assert "<!DOCTYPE html>" in html_content
    assert "tailwindcss" in html_content.lower()

    # 3. Étape 3 : Audit Qualité et Validation par @qa_reviewer
    qa_worker = sup.qa_reviewer
    qa_res = await qa_worker.execute(
        step="Vérifier et valider le prototype web généré",
        context={
            "ux_conception": ux_res,
            "web_scaffold": {"output": save_res.content, "success": True, "file_path": str(index_file)},
        },
    )

    assert qa_res["success"] is True
    assert qa_res["is_valid"] is True
    assert qa_res["agent"] == "@qa_reviewer"

    print("\n  ✅ Tâche E2E complète validée avec succès :")
    print(f"     1. Design tokens émis par {ux_res['agent']} ({tokens['theme']})")
    print(f"     2. Prototype scaffoldé dans : websites/{site_slug}/index.html ({len(html_content)} octets)")
    print(f"     3. Revue et feu vert accordé par {qa_res['agent']}")


if __name__ == "__main__":
    print("=" * 70)
    print("🚀 TEST END-TO-END D'UNE TÂCHE RÉELLE COMPLÈTE HAKIMAGENT")
    print("=" * 70)
    asyncio.run(test_full_end_to_end_web_generation_and_validation(Path(".")))
    print("=" * 70)
    print("🎉 TÂCHE END-TO-END RÉUSSIE AVEC SUCCÈS !")
    print("=" * 70)
