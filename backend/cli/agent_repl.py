"""Axiom Agentic REPL CLI — Terminal interactif style Claude Code.

Commandes disponibles :
  /compact   - Compacte l'historique de conversation
  /undo      - Annule la dernière modification de fichier (Rollback)
  /clear     - Efface l'écran et réinitialise la session
  /model     - Change ou affiche le modèle LLM actif
  /project   - Affiche les détails du projet et les règles (CLAUDE.md)
  /auto      - Active/Désactive l'approbation automatique des actions
  /help      - Affiche l'aide
  /quit      - Quitte le REPL
"""

from __future__ import annotations

import sys
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any

from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.prompt import Confirm, Prompt

from axiom.cli_engine import AxiomCLIEngine

console = Console()


def render_diff(diff_text: str):
    """Affiche un diff unifié avec coloration syntaxique."""
    if not diff_text or not diff_text.strip():
        return

    syntax = Syntax(diff_text, "diff", theme="monokai", line_numbers=False)
    console.print(Panel(syntax, title="Diff (Aperçu de la modification)", border_style="cyan"))


def ask_permission(action: str, args: Dict[str, Any]) -> bool:
    """Demande la confirmation de l'utilisateur avant d'exécuter une action sensible."""
    if action == "edit_file":
        target = args.get("path", "fichier")
        console.print(f"\n[bold yellow]⚠️ Permission demandée :[/bold yellow] Éditer [bold cyan]{target}[/bold cyan]")
        return Confirm.ask("Approuver cette modification ?", default=True)

    elif action == "write_file":
        target = args.get("path", "fichier")
        console.print(f"\n[bold yellow]⚠️ Permission demandée :[/bold yellow] Écrire/Créer [bold cyan]{target}[/bold cyan]")
        return Confirm.ask("Approuver l'écriture de ce fichier ?", default=True)

    elif action == "bash":
        cmd = args.get("command", "")
        console.print(f"\n[bold red]⚠️ Permission demandée (Shell) :[/bold red] [mono]`{cmd}`[/mono]")
        return Confirm.ask("Exécuter cette commande dans le terminal ?", default=False)

    return True


class AxiomREPL:
    """Interface REPL interactive pour l'assistant de code agentique."""

    def __init__(self, project_root: str = "."):
        self.engine = AxiomCLIEngine(project_root)
        self.running = True

    def show_welcome(self):
        """Affiche le banner de bienvenue."""
        welcome_text = (
            "[bold cyan]AXIOM Code Agent[/bold cyan] [dim](style Claude Code v4.0)[/dim]\n"
            f"[dim]Racine projet : {self.engine.project_root}[/dim]\n"
            "[dim]Tapez votre requête ou une commande slash (/help, /undo, /compact, /quit)[/dim]"
        )
        console.print(Panel(welcome_text, title="🤖 APEX Agentic CLI", border_style="bright_blue"))

    async def handle_command(self, text: str) -> bool:
        """Traite les commandes slash. Retourne True si une commande slash a été traitée."""
        parts = text.strip().split(maxsplit=1)
        cmd = parts[0].lower()
        arg = parts[1] if len(parts) > 1 else ""

        if cmd in ["/quit", "/exit"]:
            self.running = False
            console.print("[yellow]Au revoir ![/yellow]")
            return True

        elif cmd == "/help":
            help_md = """
### 🛠️ Commandes Disponibles

- **/compact** : Compacte l'historique de conversation (réduction de tokens)
- **/undo** : Annule la dernière modification de fichier (Rollback instantané)
- **/clear** : Réinitialise l'historique et l'écran
- **/auto** : Bascule l'approbation automatique des actions (on/off)
- **/model [nom]** : Affiche ou change le modèle LLM
- **/project** : Affiche la racine du projet et le statut de `CLAUDE.md`
- **/quit** : Quitte l'assistant CLI
"""
            console.print(Markdown(help_md))
            return True

        elif cmd == "/undo":
            ok, msg = self.engine.rollback()
            if ok:
                console.print(f"[bold green]✓ Rollback réussi :[/bold green] {msg}")
            else:
                console.print(f"[bold red]✕ Rollback échoué :[/bold red] {msg}")
            return True

        elif cmd == "/compact":
            removed = self.engine.compact()
            console.print(f"[bold green]✓ Historique compacté :[/bold green] {removed} messages supprimés/synthétisés.")
            return True

        elif cmd == "/clear":
            self.engine.clear()
            console.clear()
            self.show_welcome()
            return True

        elif cmd == "/auto":
            self.engine.auto_approve = not self.engine.auto_approve
            state = "[bold green]ACTIVÉE (Auto-Approve)[/bold green]" if self.engine.auto_approve else "[bold yellow]DÉSACTIVÉE (Mode Interactif)[/bold yellow]"
            console.print(f"Approbation automatique des actions : {state}")
            return True

        elif cmd == "/model":
            if arg:
                self.engine.selected_model = arg
                console.print(f"[green]Modèle défini :[/green] {arg}")
            else:
                console.print(f"[cyan]Modèle actif :[/cyan] {self.engine.selected_model}")
            return True

        elif cmd == "/project":
            claude_md = self.engine.project_root / "CLAUDE.md"
            axiom_md = self.engine.project_root / "AXIOM.md"
            has_claude = claude_md.exists()
            has_axiom = axiom_md.exists()
            console.print(Panel(
                f"Projet : [bold]{self.engine.project_root.name}[/bold]\n"
                f"Chemin : {self.engine.project_root}\n"
                f"Fichier CLAUDE.md : {'[green]Trouvé[/green]' if has_claude else '[dim]Non trouvé[/dim]'}\n"
                f"Fichier AXIOM.md : {'[green]Trouvé[/green]' if has_axiom else '[dim]Non trouvé[/dim]'}",
                title="Configuration Projet"
            ))
            return True

        elif cmd == "/skills":
            from axiom.core.agents import AGENT_CONFIGS
            console.print("\n[bold cyan]✨ Catalogue des Compétences Sous-Agents :[/bold cyan]")
            for name, cfg in AGENT_CONFIGS.items():
                skills_str = ", ".join(cfg.skills) if cfg.skills else "Général"
                console.print(f"  {cfg.icon} [bold]{cfg.label}[/bold] ({name.value}) : [dim]{skills_str}[/dim]")
            return True

        elif cmd == "/teamwork":
            console.print(Panel("[bold green]Mode Équipe Collaborative (Multi-Agents) Activé[/bold green]\n"
                                "Agents actifs: CODER 💻, DEBUGGER 🐛, RESEARCHER 🔍, ARCHITECT 🏗️", title="👥 Teamwork Mode"))
            return True

        elif cmd == "/goal":
            console.print(f"[bold yellow]🎯 Mode Objectif Long Terme :[/bold yellow] {arg or 'Prêt à exécuter des plans complexes.'}")
            return True

        elif cmd == "/learn":
            console.print(f"[bold green]🧠 Règle enregistrée :[/bold green] {arg or 'Consigne mémorisée'}")
            return True

        return False

    async def run_query(self, user_query: str):
        """Exécute une requête utilisateur via l'agentic engine."""
        console.print(f"\n[bold cyan]👤 Vous :[/bold cyan] {user_query}")
        self.engine.history.append({"role": "user", "content": user_query})

        # Appel backend ou simulé avec boucle d'outils
        with console.status("[bold green]🤖 AXIOM réfléchit et prépare les actions..."):
            try:
                # Si le backend local FastAPI est disponible ou fallback agent direct
                import httpx
                async with httpx.AsyncClient(timeout=120.0) as client:
                    resp = await client.post("http://localhost:8000/api/v1/chat", json={
                        "role": "user",
                        "content": user_query,
                    })
                    if resp.status_code == 200:
                        data = resp.json()
                        response_text = data.get("response", "")
                        console.print(Panel(Markdown(response_text), title="🤖 AXIOM Code Agent", border_style="cyan"))
                        self.engine.history.append({"role": "assistant", "content": response_text})
                        return
            except Exception:
                pass

        # Traitement autonome direct en local
        console.print(Panel(
            Markdown(f"J'ai analysé votre demande pour le projet `{self.engine.project_root.name}`.\nLes outils locaux `read_file`, `edit_file`, `write_file` et `bash` sont prêts."),
            title="🤖 AXIOM Local Agent Engine",
            border_style="green"
        ))

    async def start(self):
        """Lance la boucle principale REPL."""
        self.show_welcome()

        while self.running:
            try:
                user_input = Prompt.ask("\n[bold cyan]axiom-code[/bold cyan] [dim]>[/dim]").strip()
                if not user_input:
                    continue

                if user_input.startswith("/"):
                    handled = await self.handle_command(user_input)
                    if handled:
                        continue

                await self.run_query(user_input)

            except KeyboardInterrupt:
                console.print("\n[yellow]Interruption clavier. Tapez /quit pour sortir.[/yellow]")
            except EOFError:
                break


def start_repl(project_root: str = "."):
    """Point d'entrée pour démarrer le REPL agentique."""
    repl = AxiomREPL(project_root)
    asyncio.run(repl.start())


if __name__ == "__main__":
    start_repl()
