import pytest
from axiom.core.agents import AGENT_CONFIGS, AgentName
from axiom.core.system_prompt import build_system_prompt
from axiom.core.operation_modes import OperationMode
from axiom.models.schemas import ModelName
from axiom.commands.registry import CommandRegistry
from axiom.commands.handlers import CommandHandlers


def test_subagent_skills_mapping():
    """Vérifie que chaque sous-agent possède la liste appropriée de compétences."""
    coder = AGENT_CONFIGS[AgentName.CODER]
    assert "Code Generation" in coder.skills
    assert "TypeScript" in coder.skills

    debugger = AGENT_CONFIGS[AgentName.DEBUGGER]
    assert "Debugging" in debugger.skills

    researcher = AGENT_CONFIGS[AgentName.RESEARCHER]
    assert "Web Search" in researcher.skills


def test_system_prompt_skills_injection():
    """Vérifie l'injection des compétences dans le system prompt."""
    prompt = build_system_prompt(
        agent=AgentName.CODER,
        model=ModelName.LARGE,
        mode=OperationMode.AUTONOME,
        task_score=8.5,
        task_description="Générer un composant React"
    )
    assert "COMPÉTENCES DÉDIÉES" in prompt
    assert "Code Generation" in prompt


def test_slash_command_handlers():
    """Vérifie l'exécution des handlers pour les commandes slash."""
    registry = CommandRegistry()
    handlers = CommandHandlers(registry)

    # Test /help
    cmd_help = registry.get("/help")
    res_help = handlers.execute(cmd_help, "")
    assert res_help["success"] is True

    # Test /status
    cmd_status = registry.get("/status")
    res_status = handlers.execute(cmd_status, "")
    assert res_status["success"] is True

    # Test /teamwork
    res_team = handlers.handle_teamwork("")
    assert res_team["success"] is True
    assert res_team["output"]["mode"] == "teamwork"

    # Test /goal
    res_goal = handlers.handle_goal("Créer un composant UI")
    assert res_goal["success"] is True
    assert res_goal["output"]["goal"] == "Créer un composant UI"

    # Test /find-skills
    res_find = handlers.handle_find_skills("react")
    assert res_find["success"] is True
    assert "skills" in res_find["output"]


def test_find_skills_function():
    """Vérifie la fonction find_skills d'agent_skills_catalog."""
    from axiom.agent_skills_catalog import find_skills
    skills = find_skills("code")
    assert isinstance(skills, list)

