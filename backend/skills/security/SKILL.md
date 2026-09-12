---
name: security-validator
description: Skill de validation de sécurité pour APEX v4.0. Fournit des outils pour valider le code, les fichiers et les opérations avant exécution.
version: 1.0.0
author: APEX Team
license: MIT
tools:
  - validate_code
  - validate_file_path
  - validate_file_content
  - scan_for_injections
  - check_dangerous_patterns
triggers:
  - security
  - validate
  - check
  - scan
  - safe
examples:
  - name: Validate Python code
    description: Valider du code Python avant exécution
    input: """
    code: |
      import os
      print("Hello")
    language: python
    """
    output: """
    {
      "valid": false,
      "errors": ["Import 'os' bloqué"],
      "warnings": []
    }
    """
entry_points:
  validate_code: security_tools:validate_code
  validate_file_path: security_tools:validate_file_path
  validate_file_content: security_tools:validate_file_content
  scan_for_injections: security_tools:scan_for_injections
  check_dangerous_patterns: security_tools:check_dangerous_patterns
---

# Security Validator Skill

Ce skill fournit une couche supplémentaire de validation de sécurité pour les opérations de code et de fichiers.

## Fonctionnalités

- **Validation de code**: Vérifie le code source contre les patterns dangereux
- **Validation de chemins**: Détecte les tentatives de path traversal
- **Validation de contenu**: Vérifie la taille et le format des fichiers
- **Détection d'injections**: Scanne pour les injections SQL, command injection, etc.

## Configuration

Les règles de sécurité sont configurées dans `security_tools.py` et peuvent être personnalisées.

## Sécurité

Ce skill lui-même n'exécute PAS de code. Il ne fait que valider et analyser les entrées.
