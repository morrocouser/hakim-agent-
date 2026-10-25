import pytest
from pathlib import Path
from axiom.skills_catalog import search_skills, score_skill
from axiom.skills.registry import SkillRegistry
from axiom.skills.router import ToolRouter
from axiom.commands.registry import CommandRegistry
from axiom.commands.handlers import CommandHandlers


# --- Ranked catalog search ---------------------------------------------------

def test_search_multi_word_query_matches_all_terms_first():
    """A multi-word query no longer needs to appear verbatim in the text."""
    results = search_skills("karpathy coding mistakes", limit=5)
    assert results and results[0]["skill"] == "karpathy-guidelines"


def test_search_ranks_name_match_above_description_match():
    skill_name_hit = {"skill": "react-testing", "repo": "x", "description": "helpers"}
    description_hit = {"skill": "helpers", "repo": "x", "description": "react testing"}
    terms = ["react", "testing"]
    assert score_skill(skill_name_hit, terms) > score_skill(description_hit, terms)


def test_search_empty_or_symbol_query_returns_nothing():
    assert search_skills("") == []
    assert search_skills("  !!  ") == []


def test_search_respects_limit():
    assert len(search_skills("skill", limit=3)) == 3


# --- Skill router scoring -----------------------------------------------------

@pytest.fixture
def two_skill_registry(tmp_path):
    skills_dir = tmp_path / "skills"
    for name, tools, triggers in [
        ("file-system", ["read_file", "write_file"], ["read file", "write file", "file"]),
        ("planner", ["task_decompose"], ["plan", "break down"]),
    ]:
        d = skills_dir / name
        d.mkdir(parents=True)
        trigger_lines = "\n".join(f'  - "{t}"' for t in triggers)
        (d / "SKILL.md").write_text(
            f'---\nname: {name}\ndescription: "{name}"\ntools: {tools}\n'
            f"triggers:\n{trigger_lines}\n---\n".replace("'", '"')
        )
    return SkillRegistry(skills_dir)


async def test_router_matches_multi_word_trigger_inside_sentence(two_skill_registry):
    router = ToolRouter(two_skill_registry)
    result = await router.route("please break down the migration", {})
    assert result.skill_name == "planner"


async def test_router_prefers_skill_with_more_evidence(two_skill_registry):
    router = ToolRouter(two_skill_registry)
    result = await router.route("read file config.json then plan", {})
    # "read file" phrase + "file" + tool words outweigh the single "plan" hit.
    assert result.skill_name == "file-system"
    assert result.tool_name == "read_file"
    assert 0.5 < result.confidence <= 0.85


async def test_router_lowers_confidence_on_tie(two_skill_registry):
    router = ToolRouter(two_skill_registry)
    # planner: "break down" phrase = 4; file-system: "file" trigger + 2 tools = 4.
    result = await router.route("break down file", {})
    assert result.confidence <= 0.6


# --- /plan and /skill-info commands -------------------------------------------

@pytest.fixture
def handlers():
    return CommandHandlers(CommandRegistry())


def test_plan_command_returns_ordered_tasks(handlers):
    res = handlers.execute(CommandRegistry().get("/plan"), "Build a REST API with authentication")
    assert res["success"] is True
    names = [t["name"] for t in res["output"]["tasks"]]
    assert names == ["design_schema", "implement_auth", "create_endpoints", "write_tests"]
    # Every task comes after the tasks it depends on.
    for i, task in enumerate(res["output"]["tasks"]):
        assert set(task["dependencies"]) <= set(names[:i])


def test_plan_without_args_shows_last_plan(handlers):
    assert handlers.handle_plan("")["success"] is False
    handlers.handle_plan("Build a web frontend")
    res = handlers.handle_plan("")
    assert res["success"] is True
    assert res["output"]["objective"] == "Build a web frontend"


def test_skills_command_works_from_any_cwd(handlers, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    res = handlers.handle_skills("")
    assert "planner" in res["output"]["skills"]


def test_skill_info_returns_skill_md(handlers):
    res = handlers.execute(CommandRegistry().get("/skill-info"), "karpathy-guidelines")
    assert res["success"] is True
    assert res["output"]["repo"] == "andrej-karpathy-skills"
    assert "karpathy" in res["output"]["content"].lower()


def test_skill_info_accepts_repo_prefix(handlers):
    res = handlers.handle_skill_info("taste-skill/taste-skill")
    assert res["success"] is True


def test_skill_info_unknown_skill_suggests_alternatives(handlers):
    res = handlers.handle_skill_info("karpathy")
    assert res["success"] is False
    assert "andrej-karpathy-skills/karpathy-guidelines" in res["suggestions"]
