import typer
import httpx
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown
from typing import Optional

app = typer.Typer(help="APEX v4.0 -- Orchestrateur Multi-Agents CLI")
console = Console()
API_BASE = "http://localhost:8000/api/v1"

# Default timeouts
DEFAULT_TIMEOUT = 30.0
LONG_TIMEOUT = 120.0


def get_client(timeout: float = DEFAULT_TIMEOUT) -> httpx.Client:
    """Create HTTP client with consistent settings."""
    return httpx.Client(verify=True, timeout=timeout)


@app.command()
def tui():
    """Lance le TUI interactif style Claude Code."""
    from cli.tui.app import AxiomTUI
    AxiomTUI().run()


@app.command()
def code(project: str = "."):
    """Lance l'assistant de code agentique CLI autonome (Style Claude Code)."""
    from cli.agent_repl import start_repl
    start_repl(project)


@app.command()
def score(description: str, task_type: str = "QUICK"):
    """Calcule et route une tache vers le meilleur agent/modele."""
    try:
        with get_client(DEFAULT_TIMEOUT) as client:
            resp = client.post(f"{API_BASE}/score", json={
                "description": description,
                "task_type": task_type.upper(),
            })
            if resp.is_error:
                console.print(f"[red]Erreur: {resp.text}[/red]")
                raise typer.Exit(1)
            data = resp.json()
    except httpx.ConnectError:
        console.print("[red]Erreur: Impossible de se connecter au serveur APEX (port 8000)[/red]")
        raise typer.Exit(1)
    except httpx.TimeoutException:
        console.print("[red]Erreur: Timeout lors de la requête[/red]")
        raise typer.Exit(1)
    
    table = Table(title="Resultat du Scoring")
    table.add_column("Propriete", style="cyan")
    table.add_column("Valeur", style="green")
    table.add_row("Tache", data["description"])
    table.add_row("Score", f"{data['score']}/10")
    table.add_row("Agent", data["agent"])
    table.add_row("Modele", data["model"])
    table.add_row("Complexite", str(data["dimensions"]["complexity"]))
    table.add_row("Enjeux", str(data["dimensions"]["stakes"]))
    table.add_row("Creativite", str(data["dimensions"]["creativity"]))
    table.add_row("Urgence", str(data["dimensions"]["speed_need"]))
    table.add_row("Domaine", str(data["dimensions"]["domain_match"]))
    console.print(table)


@app.command()
def execute(description: str, task_type: str = "QUICK", context: Optional[str] = None):
    """Execute une tache via l'orchestrateur AXIOM."""
    with console.status("[bold green]APEX execute la tache..."):
        try:
            with get_client(LONG_TIMEOUT) as client:
                resp = client.post(f"{API_BASE}/execute", json={
                    "description": description,
                    "task_type": task_type.upper(),
                    "context": context,
                })
                if resp.is_error:
                    console.print(f"[red]Erreur: {resp.text}[/red]")
                    raise typer.Exit(1)
                data = resp.json()
        except httpx.ConnectError:
            console.print("[red]Erreur: Impossible de se connecter au serveur APEX (port 8000)[/red]")
            raise typer.Exit(1)
        except httpx.TimeoutException:
            console.print("[red]Erreur: Timeout lors de l'exécution[/red]")
            raise typer.Exit(1)
    
    status_color = "green" if data["status"] == "DONE" else "red"
    task_id = data["task_id"]
    agent = data["agent"]
    model = data["model"]
    score_val = data["score"]
    quality = data["quality_score"]
    iteration = data["iteration"]
    output = data.get("output", "")
    error = data.get("error")
    header = Panel(
        f"[bold]Tache {task_id}[/bold] | {agent} . {model} | "
        f"Score: {score_val} | Qualite: {quality}/10 | "
        f"Iteration: {iteration} | Statut: [{status_color}]{data['status']}[/{status_color}]",
    )
    console.print(header)
    if output:
        md = Markdown(output)
        console.print(Panel(md, title="Resultat"))
    if error:
        console.print(f"[red]Erreur: {error}[/red]")


@app.command()
def chat(message: str):
    """Envoie un message a l'orchestrateur AXIOM."""
    with console.status("[bold green]APEX reflechit..."):
        try:
            with get_client(LONG_TIMEOUT) as client:
                resp = client.post(f"{API_BASE}/chat", json={
                    "role": "user",
                    "content": message,
                })
                if resp.is_error:
                    console.print(f"[red]Erreur: {resp.text}[/red]")
                    raise typer.Exit(1)
                data = resp.json()
        except httpx.ConnectError:
            console.print("[red]Erreur: Impossible de se connecter au serveur APEX (port 8000)[/red]")
            raise typer.Exit(1)
        except httpx.TimeoutException:
            console.print("[red]Erreur: Timeout lors de la requête[/red]")
            raise typer.Exit(1)
    
    task = data["task"]
    console.print(Panel(
        f"[bold]{task['agent']}[/bold] . {task['model']} | "
        f"Score: {task['score']} | Qualite: {task['quality_score']}/10"
    ))
    md = Markdown(data["response"])
    console.print(md)


@app.command()
def agents():
    """Liste les 8 sous-agents disponibles."""
    try:
        with get_client(DEFAULT_TIMEOUT) as client:
            resp = client.get(f"{API_BASE}/agents")
            if resp.is_error:
                console.print(f"[red]Erreur: {resp.text}[/red]")
                raise typer.Exit(1)
            data = resp.json()
    except httpx.ConnectError:
        console.print("[red]Erreur: Impossible de se connecter au serveur APEX (port 8000)[/red]")
        raise typer.Exit(1)
    except httpx.TimeoutException:
        console.print("[red]Erreur: Timeout lors de la requête[/red]")
        raise typer.Exit(1)
    
    table = Table(title="Registre des Sous-Agents APEX")
    table.add_column("", style="cyan", width=2)
    table.add_column("Agent", style="bold", width=20)
    table.add_column("Modele", width=20)
    table.add_column("Specialite", width=50)
    for name, cfg in data.items():
        table.add_row(cfg["icon"], name, cfg["default_model"], cfg["speciality"])
    console.print(table)


@app.command()
def memory():
    """Affiche la memoire a 3 niveaux."""
    try:
        with get_client(DEFAULT_TIMEOUT) as client:
            resp = client.get(f"{API_BASE}/memory")
            if resp.is_error:
                console.print(f"[red]Erreur: {resp.text}[/red]")
                raise typer.Exit(1)
            data = resp.json()
    except httpx.ConnectError:
        console.print("[red]Erreur: Impossible de se connecter au serveur APEX (port 8000)[/red]")
        raise typer.Exit(1)
    except httpx.TimeoutException:
        console.print("[red]Erreur: Timeout lors de la requête[/red]")
        raise typer.Exit(1)
    
    console.print(Panel(f"Tokens estimes: {data['tokens_estimate']}", title="Memoire APEX"))
    md = Markdown(f"```json\n{data}\n```"[:2000])
    console.print(md)


@app.command()
def serve():
    """Demarre le serveur API AXIOM."""
    from axiom.api.main import start
    start()


def main():
    """Point d'entrée AXIOM. Sans argument = TUI interactif."""
    import sys
    if len(sys.argv) == 1:
        tui()
    else:
        app()


if __name__ == "__main__":
    main()
