from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Optional, Tuple
from axiom.logging_setup import log


# Configuration de sécurité
ALLOWED_EXTENSIONS = {
    ".ts", ".tsx", ".js", ".jsx", ".py", ".md", ".json", ".sql", ".yaml", ".yml",
    ".txt", ".csv", ".html", ".css", ".xml",
}

# Extensions dangereuses bloquées
DANGEROUS_EXTENSIONS = {
    ".sh", ".bash", ".bat", ".cmd", ".ps1", ".exe", ".dll", ".so",
    ".com", ".msi", ".app", ".jar", ".class",
}

MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10MB
MAX_FILENAME_LENGTH = 255

# Patterns dangereux dans les noms de fichiers
DANGEROUS_FILENAME_PATTERNS = [
    r"\.\.",  # Path traversal
    r"^\.",  # Fichiers cachés (sauf .gitignore, etc.)
    r"[<>:\"|?*]",  # Caractères spéciaux Windows
    r"^\s*$",  # Noms vides
]

# Répertoire de base pour l'isolation
SAFE_BASE_DIR = os.getenv("HAKIM_SAFE_DIR", "./user_files")


class FileManager:
    def __init__(self, base_dir: Optional[str] = None):
        # Utiliser un répertoire de base sécurisé
        self.base_dir = (Path(base_dir) if base_dir else Path(SAFE_BASE_DIR)).resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)
        log.info(f"FileManager initialisé avec base_dir: {self.base_dir}")

    def _validate_filename(self, filename: str) -> Tuple[bool, str]:
        """Valider le nom de fichier contre les attaques."""
        # Vérifier la longueur
        if len(filename) > MAX_FILENAME_LENGTH:
            return False, f"Nom de fichier trop long (max {MAX_FILENAME_LENGTH})"
        
        # Vérifier les patterns dangereux
        for pattern in DANGEROUS_FILENAME_PATTERNS:
            if re.search(pattern, filename, re.IGNORECASE):
                return False, f"Nom de fichier invalide: correspond à un pattern dangereux"
        
        return True, ""

    def _validate_extension(self, path: Path) -> Tuple[bool, str]:
        """Valider l'extension du fichier."""
        ext = path.suffix.lower()
        
        # Vérifier contre les extensions dangereuses
        if ext in DANGEROUS_EXTENSIONS:
            return False, f"Extension dangereuse bloquée: {ext}"
        
        # Vérifier contre les extensions autorisées
        if ext not in ALLOWED_EXTENSIONS:
            return False, f"Extension non autorisée: {ext}"
        
        return True, ""

    def _validate_content(self, content: str) -> Tuple[bool, str]:
        """Valider le contenu du fichier."""
        # Vérifier la taille
        if len(content.encode("utf-8")) > MAX_FILE_SIZE_BYTES:
            return False, f"Fichier trop grand (max {MAX_FILE_SIZE_BYTES // (1024*1024)}MB)"
        
        # Détecter du contenu binaire suspect
        # (simpliste: vérifier si c'est du texte valide)
        try:
            content.encode("utf-8")
        except UnicodeEncodeError:
            return False, "Contenu non-UTF-8 détecté"
        
        return True, ""

    def _resolve_safe_path(self, relative_path: str) -> Optional[Path]:
        """Résoudre un chemin de manière sécurisée."""
        if not relative_path or relative_path.strip() in ("", ".", "/"):
            return self.base_dir

        # Valider le nom de fichier d'abord
        is_valid, error = self._validate_filename(relative_path)
        if not is_valid:
            log.warning(f"Nom de fichier invalide: {error}")
            return None
        
        # Normaliser le chemin
        try:
            # Remplacer les barres obliques multiples
            normalized = re.sub(r"[/\\]+", "/", relative_path)
            # Supprimer les / de début
            normalized = normalized.lstrip("/")
            
            target = (self.base_dir / normalized).resolve()
            
            # Vérifier que le chemin est bien dans base_dir
            target.relative_to(self.base_dir)
            return target
        except ValueError:
            log.warning(f"Tentative de path traversal: {relative_path}")
            return None
        except Exception as e:
            log.warning(f"Erreur résolution chemin: {e}")
            return None

    def create_file(self, relative_path: str, content: str) -> str:
        """Créer un fichier de manière sécurisée."""
        # Valider le chemin
        path = self._resolve_safe_path(relative_path)
        if not path:
            return "[Erreur de Sécurité] Accès refusé : Chemin invalide"
        
        # Valider l'extension
        is_valid_ext, ext_error = self._validate_extension(path)
        if not is_valid_ext:
            return f"[Erreur de Sécurité] {ext_error}"
        
        # Valider le contenu
        is_valid_content, content_error = self._validate_content(content)
        if not is_valid_content:
            return f"[Erreur de Sécurité] {content_error}"
        
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
            log.info(f"Fichier créé: {path}")
            return f"Fichier créé: {path.relative_to(self.base_dir)}"
        except PermissionError:
            return "[Erreur] Permission refusée"
        except Exception as e:
            log.error(f"Erreur création fichier: {e}")
            return f"[Erreur] {str(e)}"

    def read_file(self, relative_path: str) -> str:
        """Lire un fichier de manière sécurisée."""
        path = self._resolve_safe_path(relative_path)
        if not path:
            return "[Erreur de Sécurité] Accès refusé : Chemin invalide"
        if not path.exists():
            return f"[Erreur] Fichier introuvable: {relative_path}"
        
        try:
            content = path.read_text(encoding="utf-8")
            # Valider la taille au retour aussi
            if len(content.encode("utf-8")) > MAX_FILE_SIZE_BYTES:
                return f"[Erreur] Fichier trop grand pour être lu"
            return content
        except Exception as e:
            log.error(f"Erreur lecture fichier: {e}")
            return f"[Erreur] {str(e)}"

    def delete_file(self, relative_path: str) -> str:
        """Supprimer un fichier de manière sécurisée."""
        path = self._resolve_safe_path(relative_path)
        if not path:
            return "[Erreur de Sécurité] Accès refusé : Chemin invalide"
        if not path.exists():
            return f"[Erreur] Fichier introuvable: {relative_path}"
        
        try:
            os.remove(path)
            log.info(f"Fichier supprimé: {path}")
            return f"Fichier supprimé: {path.relative_to(self.base_dir)}"
        except Exception as e:
            log.error(f"Erreur suppression fichier: {e}")
            return f"[Erreur] {str(e)}"

    def list_files(self, relative_path: str = "") -> str:
        """Lister les fichiers dans un répertoire de manière sécurisée."""
        path = self._resolve_safe_path(relative_path)
        if not path:
            return "[Erreur de Sécurité] Accès refusé : Chemin invalide"
        
        if not path.exists():
            return f"[Erreur] Répertoire introuvable: {relative_path}"
        
        if not path.is_dir():
            return f"[Erreur] {relative_path} n'est pas un répertoire"
        
        try:
            files = []
            for item in path.iterdir():
                files.append(item.relative_to(self.base_dir).as_posix())
            return "\n".join(files) if files else "[Aucun fichier]"
        except Exception as e:
            log.error(f"Erreur listage fichiers: {e}")
            return f"[Erreur] {str(e)}"

    def get_code_map(
        self,
        relative_path: str = "",
        max_tokens: int = 1000,
        focus_keywords: Optional[list[str]] = None,
    ) -> str:
        """Générer une cartographie syntaxique AST sécurisée des symboles du répertoire."""
        path = self._resolve_safe_path(relative_path)
        if not path:
            return "[Erreur de Sécurité] Accès refusé : Chemin invalide"
        if not path.exists():
            return f"[Erreur] Répertoire introuvable: {relative_path}"
        if not path.is_dir():
            return f"[Erreur] {relative_path} n'est pas un répertoire"

        from axiom.tools.repo_map import CodebaseMapper
        mapper = CodebaseMapper(path)
        return mapper.generate_symbol_map(max_tokens=max_tokens, focus_keywords=focus_keywords)

    def get_file_symbols(self, relative_path: str) -> str:
        """Extraire le plan des symboles (classes, fonctions, signatures) d'un fichier source."""
        path = self._resolve_safe_path(relative_path)
        if not path:
            return "[Erreur de Sécurité] Accès refusé : Chemin invalide"
        if not path.exists() or not path.is_file():
            return f"[Erreur] Fichier introuvable: {relative_path}"

        from axiom.tools.repo_map import CodebaseMapper
        mapper = CodebaseMapper(self.base_dir)
        return mapper.get_file_outline(path)

