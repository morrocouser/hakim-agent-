#!/usr/bin/env python3
"""
Test complet de validation du Pattern RepoMap (Cartographie AST) pour AXIOM.
Valide:
1. L'extraction AST des classes, méthodes, signatures et docstrings Python.
2. L'extraction syntaxique des types, interfaces et fonctions TypeScript/JavaScript.
3. Le respect strict du budget de tokens (max_tokens).
4. L'intégration dans FileManager (get_code_map et get_file_symbols).
5. L'intégration de RepoMapTool dans les outils builtin.
6. L'injection proactive dans PromptBuilder.build_user_prompt.
"""

import sys
import os
import tempfile
import asyncio
from pathlib import Path

# S'assurer que le backend est accessible dans sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

from axiom.tools.repo_map import CodebaseMapper, get_repository_map
from axiom.tools.file_manager import FileManager
from axiom.tools.builtin import RepoMapTool
from axiom.core.prompt_builder import PromptBuilder
from axiom.models.schemas import TaskAssignment, AgentName, ModelName, ScoringDimensions


SAMPLE_PYTHON_CODE = '''"""Module de calcul d'ingénierie."""

GLOBAL_TIMEOUT = 120
MAX_RETRIES = 3

class DataPipeline(BasePipeline):
    """Pipeline de traitement vectoriel des données."""

    def __init__(self, name: str, batch_size: int = 64) -> None:
        self.name = name
        self.batch_size = batch_size

    async def execute(self, payload: dict) -> bool:
        """Exécute la transformation."""
        return True


def standalone_helper(x: int, y: int = 10) -> int:
    """Additionne deux entiers."""
    return x + y
'''

SAMPLE_TS_CODE = '''import { Config } from './types';

export interface UserSession {
    id: string;
    token: string;
}

export type Status = 'active' | 'inactive';

export class SessionManager extends BaseManager {
    public sessionId: string;
}

export function createSession(userId: string): UserSession {
    return { id: userId, token: 'abc' };
}
'''


def test_python_ast_extraction():
    print("🧪 Test 1 : Extraction AST Python (Classes, signatures, docstrings, constantes)...")
    with tempfile.TemporaryDirectory() as tmp_dir:
        py_file = Path(tmp_dir) / "pipeline.py"
        py_file.write_text(SAMPLE_PYTHON_CODE, encoding="utf-8")

        mapper = CodebaseMapper(tmp_dir)
        symbols = mapper._extract_python_symbols(py_file)
        full_symbols_text = "\n".join(symbols)

        # Vérifier constantes
        assert "GLOBAL_TIMEOUT = ..." in full_symbols_text
        assert "MAX_RETRIES = ..." in full_symbols_text

        # Vérifier classe et base
        assert "class DataPipeline(BasePipeline):" in full_symbols_text
        assert '"""Pipeline de traitement vectoriel des données."""' in full_symbols_text

        # Vérifier méthode et signature avec annotations de type
        assert "def __init__(self, name: str, batch_size: int=64) -> None" in full_symbols_text
        assert "async def execute(self, payload: dict) -> bool" in full_symbols_text

        # Vérifier fonction standalone
        assert "def standalone_helper(x: int, y: int=10) -> int" in full_symbols_text

        print("  ✅ Extraction AST Python validée avec signatures et types exacts")


def test_ts_js_extraction():
    print("\n🧪 Test 2 : Extraction syntaxique TypeScript / JavaScript...")
    with tempfile.TemporaryDirectory() as tmp_dir:
        ts_file = Path(tmp_dir) / "session.ts"
        ts_file.write_text(SAMPLE_TS_CODE, encoding="utf-8")

        mapper = CodebaseMapper(tmp_dir)
        symbols = mapper._extract_ts_js_symbols(ts_file)
        full_symbols_text = "\n".join(symbols)

        assert "interface UserSession" in full_symbols_text
        assert "type Status =" in full_symbols_text
        assert "class SessionManager extends BaseManager" in full_symbols_text
        assert "function createSession(userId: string)" in full_symbols_text

        print("  ✅ Extraction TypeScript (classes, interfaces, types, fonctions) validée")


def test_token_budget_enforcement():
    print("\n🧪 Test 3 : Respect du budget de tokens (max_tokens)...")
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Créer plusieurs fichiers pour dépasser un petit budget
        for i in range(15):
            p = Path(tmp_dir) / f"module_{i}.py"
            p.write_text(SAMPLE_PYTHON_CODE, encoding="utf-8")

        mapper = CodebaseMapper(tmp_dir)
        small_token_budget = 100  # ~400 caractères
        repomap = mapper.generate_symbol_map(max_tokens=small_token_budget)

        # La taille doit respecter le budget approx + marge de troncature
        assert len(repomap) < (small_token_budget * 4) + 200
        assert "autre(s) fichier(s) omis pour respecter le budget" in repomap

        print("  ✅ Troncature propre et respect du budget de tokens validés")


def test_file_manager_integration():
    print("\n🧪 Test 4 : Méthodes get_code_map et get_file_symbols dans FileManager...")
    with tempfile.TemporaryDirectory() as tmp_dir:
        fm = FileManager(tmp_dir)
        fm.create_file("service.py", SAMPLE_PYTHON_CODE)

        code_map = fm.get_code_map(max_tokens=500)
        assert "service.py" in code_map
        assert "class DataPipeline" in code_map

        outline = fm.get_file_symbols("service.py")
        assert "service.py:" in outline
        assert "async def execute" in outline

        print("  ✅ Méthodes FileManager (get_code_map / get_file_symbols) validées")


def test_builtin_tool_repomap():
    print("\n🧪 Test 5 : Outil interactif RepoMapTool (builtin.py)...")
    with tempfile.TemporaryDirectory() as tmp_dir:
        py_file = Path(tmp_dir) / "app.py"
        py_file.write_text(SAMPLE_PYTHON_CODE, encoding="utf-8")

        tool = RepoMapTool(base_dir=tmp_dir)
        res = asyncio.run(tool._execute({"max_tokens": 500}, context={}))
        assert res.ok is True
        assert "app.py" in res.content
        assert "class DataPipeline" in res.content

        print("  ✅ Exécution de RepoMapTool validée")


def test_proactive_prompt_injection():
    print("\n🧪 Test 6 : Injection proactive dans PromptBuilder...")
    builder = PromptBuilder()

    task_coder = TaskAssignment(
        task_id="T_CODE_01",
        description="Refactoriser la classe DataPipeline",
        agent=AgentName.CODER,
        model=ModelName.BEST,
        score=7.0,
        dimensions=ScoringDimensions(),
    )

    prompt = builder.build_user_prompt(
        task=task_coder,
        context=None,
        iteration=1,
        max_iterations=3,
    )

    assert "[CARTOGRAPHIE SYNTAXIQUE DU PROJET (REPOMAP)]" in prompt
    print("  ✅ Injection automatique de la RepoMap à l'itération 1 pour AGENT_CODER validée")


def run_all():
    print("=" * 70)
    print("🚀 DÉMARRAGE DU SUITE DE VALIDATION DU REPOMAP AST AXIOM")
    print("=" * 70)
    test_python_ast_extraction()
    test_ts_js_extraction()
    test_token_budget_enforcement()
    test_file_manager_integration()
    test_builtin_tool_repomap()
    test_proactive_prompt_injection()
    print("\n" + "=" * 70)
    print("🎉 TOUS LES TESTS DU REPOMAP AST SONT PASSÉS AVEC SUCCÈS !")
    print("=" * 70)


if __name__ == "__main__":
    run_all()
