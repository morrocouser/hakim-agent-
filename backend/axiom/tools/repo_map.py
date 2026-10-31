"""
AXIOM v4.0 — Cartographie Syntaxique du Code par AST (Pattern RepoMap).

Génère une carte synthétique et condensée des symboles d'une base de code
(classes, méthodes, signatures, annotations de type, exports et docstrings)
en respectant un budget strict de tokens (~800-1000 tokens).

Permet aux agents d'avoir une compréhension globale immédiate de l'architecture
sans avoir à lire chaque fichier individuellement.
"""

from __future__ import annotations

import ast
import os
import re
from pathlib import Path
from typing import Optional, List, Dict, Tuple, Set
from axiom.logging_setup import log


# Répertoires et fichiers ignorés pour l'analyse
IGNORED_DIRS: Set[str] = {
    "__pycache__", ".git", ".venv", "venv", "env", "node_modules",
    ".pytest_cache", ".mypy_cache", ".ruff_cache", "dist", "build",
    ".idea", ".vscode", "axiom.egg-info", "logs", "user_files",
}

# Extensions de fichiers de code prises en charge
SOURCE_EXTENSIONS: Set[str] = {
    ".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".rs", ".sql"
}


class CodebaseMapper:
    """
    Cartographe AST de base de code.
    Analyse les fichiers sources et produit une synthèse concise des définitions.
    """

    def __init__(self, root_dir: str | Path = "."):
        self.root_dir = Path(root_dir).resolve()

    def _should_ignore_dir(self, dir_name: str) -> bool:
        return dir_name in IGNORED_DIRS or dir_name.startswith(".")

    def _list_source_files(self, max_files: int = 200) -> List[Path]:
        """Liste tous les fichiers sources pertinents dans root_dir."""
        matched: List[Path] = []
        if not self.root_dir.exists() or not self.root_dir.is_dir():
            return matched

        for root, dirs, files in os.walk(self.root_dir):
            # Filtrer les répertoires à ignorer sur place
            dirs[:] = [d for d in dirs if not self._should_ignore_dir(d)]

            for file in sorted(files):
                ext = Path(file).suffix.lower()
                if ext in SOURCE_EXTENSIONS:
                    full_p = Path(root) / file
                    matched.append(full_p)
                    if len(matched) >= max_files:
                        return matched
        return matched

    def _format_arg(self, arg: ast.arg) -> str:
        """Formate un argument AST avec son annotation de type si présente."""
        res = arg.arg
        if arg.annotation:
            try:
                res += f": {ast.unparse(arg.annotation)}"
            except Exception:
                pass
        return res

    def _format_function_signature(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
        """Extrait la signature compacte d'une fonction Python."""
        prefix = "async def " if isinstance(node, ast.AsyncFunctionDef) else "def "
        args = [self._format_arg(a) for a in node.args.args]
        
        # Args optionnels avec défauts
        defaults = node.args.defaults
        if defaults:
            num_defaults = len(defaults)
            for i, d in enumerate(defaults):
                idx = len(args) - num_defaults + i
                if 0 <= idx < len(args):
                    try:
                        args[idx] += f"={ast.unparse(d)}"
                    except Exception:
                        pass

        if node.args.vararg:
            args.append(f"*{node.args.vararg.arg}")
        if node.args.kwarg:
            args.append(f"**{node.args.kwarg.arg}")

        sig = f"{prefix}{node.name}({', '.join(args)})"
        if node.returns:
            try:
                sig += f" -> {ast.unparse(node.returns)}"
            except Exception:
                pass
        return sig

    def _extract_python_symbols(self, file_path: Path) -> List[str]:
        """Analyse un fichier Python via ast.parse et extrait les définitions."""
        lines: List[str] = []
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
            tree = ast.parse(content, filename=str(file_path))
        except Exception:
            return lines

        for node in tree.body:
            # Classes
            if isinstance(node, ast.ClassDef):
                bases = []
                for b in node.bases:
                    try:
                        bases.append(ast.unparse(b))
                    except Exception:
                        pass
                base_str = f"({', '.join(bases)})" if bases else ""
                lines.append(f"  class {node.name}{base_str}:")
                
                # Première ligne de docstring de la classe
                doc = ast.get_docstring(node)
                if doc:
                    first_line = doc.strip().splitlines()[0][:80]
                    lines.append(f'    """{first_line}"""')

                for subnode in node.body:
                    if isinstance(subnode, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        sig = self._format_function_signature(subnode)
                        lines.append(f"    {sig}")

            # Fonctions de niveau supérieur
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                sig = self._format_function_signature(node)
                lines.append(f"  {sig}")
                doc = ast.get_docstring(node)
                if doc:
                    first_line = doc.strip().splitlines()[0][:80]
                    lines.append(f'    """{first_line}"""')

            # Constantes globales significatives (ex: CONSTANT = ...)
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id.isupper():
                        lines.append(f"  {target.id} = ...")

        return lines

    def _extract_ts_js_symbols(self, file_path: Path) -> List[str]:
        """Extrait les déclarations TypeScript/JavaScript via motifs syntaxiques."""
        lines: List[str] = []
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            return lines

        # Patterns TypeScript / JavaScript classiques
        patterns = [
            r"^(?:export\s+)?(?:default\s+)?(?:abstract\s+)?class\s+(\w+)(?:\s+extends\s+\w+)?",
            r"^(?:export\s+)?interface\s+(\w+)",
            r"^(?:export\s+)?type\s+(\w+)\s*=",
            r"^(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*\([^)]*\)(?:\s*:\s*[^{]+)?",
            r"^(?:export\s+)?const\s+(\w+)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>",
        ]
        combined = re.compile("|".join(f"({p})" for p in patterns), re.MULTILINE)

        for line in content.splitlines():
            line_str = line.strip()
            if combined.match(line_str):
                # Nettoyer et garder la signature
                cleaned = line_str.rstrip("{").strip()
                lines.append(f"  {cleaned}")

        return lines

    def get_file_outline(self, file_path: str | Path) -> str:
        """Génère l'aperçu synthétique d'un fichier donné."""
        p = Path(file_path)
        if not p.is_absolute():
            p = self.root_dir / p
        if not p.exists() or not p.is_file():
            return f"[Erreur] Fichier introuvable: {file_path}"

        ext = p.suffix.lower()
        if ext == ".py":
            symbols = self._extract_python_symbols(p)
        elif ext in (".ts", ".tsx", ".js", ".jsx"):
            symbols = self._extract_ts_js_symbols(p)
        else:
            return f"[Info] Format non pris en charge pour l'AST: {ext}"

        if not symbols:
            return f"{p.name} (aucun symbole racine détecté)"
        return f"{p.name}:\n" + "\n".join(symbols)

    def generate_symbol_map(
        self,
        max_tokens: int = 1000,
        focus_keywords: Optional[List[str]] = None,
    ) -> str:
        """
        Génère la carte syntaxique globale du projet avec limitation de tokens.
        
        Args:
            max_tokens: Budget de tokens approximatif (~4 caractères par token).
            focus_keywords: Mots-clés pour prioriser les fichiers pertinents.
            
        Returns:
            Chaîne formatée représentant la carte syntaxique dense du projet.
        """
        max_chars = max_tokens * 4
        source_files = self._list_source_files()
        if not source_files:
            return "[Aucun fichier source analysable trouvé]"

        # Tri et priorisation selon les mots-clés
        def score_file(p: Path) -> int:
            rel = str(p.relative_to(self.root_dir)).lower()
            score = 0
            if focus_keywords:
                for kw in focus_keywords:
                    if kw.lower() in rel:
                        score += 5
            # Prioriser les fichiers core, models, schemas
            if any(k in rel for k in ("core", "models", "api", "schemas", "client")):
                score += 2
            if rel.endswith("__init__.py"):
                score -= 1
            return score

        sorted_files = sorted(source_files, key=score_file, reverse=True)

        map_parts: List[str] = []
        current_len = 0

        for f in sorted_files:
            try:
                rel_path = f.relative_to(self.root_dir).as_posix()
            except ValueError:
                rel_path = f.name

            ext = f.suffix.lower()
            if ext == ".py":
                symbols = self._extract_python_symbols(f)
            elif ext in (".ts", ".tsx", ".js", ".jsx"):
                symbols = self._extract_ts_js_symbols(f)
            else:
                symbols = []

            if not symbols:
                continue

            file_header = f"📄 {rel_path}:\n"
            file_body = "\n".join(symbols) + "\n"
            chunk = file_header + file_body

            if current_len + len(chunk) > max_chars:
                # Si le budget est dépassé, on ajoute un indicateur de troncature propre
                remaining_files = len(sorted_files) - len(map_parts)
                map_parts.append(
                    f"\n... [{remaining_files} autre(s) fichier(s) omis pour respecter le budget de {max_tokens} tokens]"
                )
                break

            map_parts.append(chunk)
            current_len += len(chunk)

        log.info("🗺️ RepoMap générée: %s caractères (~%s tokens, %s fichiers inclus)",
                 current_len, current_len // 4, len(map_parts))

        return "\n".join(map_parts).strip()


# Helper global rapide
def get_repository_map(
    root_dir: Optional[str | Path] = None,
    max_tokens: int = 1000,
    focus_keywords: Optional[List[str]] = None,
) -> str:
    """Helper pratique pour générer la RepoMap sans instancier manuellement."""
    resolved_dir = (
        root_dir
        if root_dir is not None
        else (os.getenv("AXIOM_WORKSPACE") or os.getenv("HAKIM_SAFE_DIR") or ".")
    )
    mapper = CodebaseMapper(resolved_dir)
    return mapper.generate_symbol_map(max_tokens=max_tokens, focus_keywords=focus_keywords)
