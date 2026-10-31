import pytest
from pathlib import Path
from axiom.models.schemas import AgentName, TaskType
from axiom.core.scoring import score_and_route
from axiom.core.agents import AGENT_CONFIGS, get_agent_config
from axiom.tools.web_builder_tool import WebBuilderTool


def test_web_builder_agent_config():
    """Vérifie la configuration de l'agent AGENT_WEB_BUILDER."""
    assert AgentName.WEB_BUILDER in AGENT_CONFIGS
    cfg = get_agent_config(AgentName.WEB_BUILDER)
    assert cfg.icon == "🌐"
    assert "Web" in cfg.label or "Sites" in cfg.label
    assert "Tailwind CSS" in cfg.speciality
    assert len(cfg.skills) > 0


def test_web_builder_routing():
    """Vérifie que les demandes de création de site web sont routées vers AGENT_WEB_BUILDER."""
    prompts = [
        "je veux que je cree un site comme auto ds",
        "crée-moi une landing page moderne avec dark mode",
        "peux-tu faire un site web pour mon agence",
        "développe un portfolio moderne avec animations et tailwind",
        "création de site e-commerce avec panier",
    ]
    for prompt in prompts:
        assignment = score_and_route(prompt)
        assert assignment.agent == AgentName.WEB_BUILDER, f"Échec de routage pour: '{prompt}' (obtenu: {assignment.agent})"


@pytest.mark.asyncio
async def test_web_builder_tool_templates(tmp_path):
    """Vérifie le fonctionnement de l'outil WebBuilderTool."""
    tool = WebBuilderTool(base_dir=str(tmp_path))
    res = await tool.execute(action="list_templates")
    assert res.ok is True
    assert "saas_landing" in res.metadata["templates"]
    assert "ecommerce_store" in res.metadata["templates"]


@pytest.mark.asyncio
async def test_web_builder_tool_scaffold_and_save(tmp_path):
    """Vérifie le scaffold et la sauvegarde automatique d'un site web."""
    tool = WebBuilderTool(base_dir=str(tmp_path))
    scaffold_res = await tool.execute(action="scaffold", site_name="test-saas", template="saas_landing")
    assert scaffold_res.ok is True
    html = scaffold_res.metadata["scaffold_html"]
    assert "<!DOCTYPE html>" in html
    assert "cdn.tailwindcss.com" in html

    save_res = await tool.execute(action="save_site", site_name="test-saas", html_content=html)
    assert save_res.ok is True
    saved_file = Path(save_res.metadata["absolute_path"])
    assert saved_file.exists()
    assert saved_file.read_text(encoding="utf-8") == html
