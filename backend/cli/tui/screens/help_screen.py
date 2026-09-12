from textual.screen import Screen
from textual.widgets import Static, Button
from textual.containers import Vertical, Horizontal
from textual.binding import Binding


class HelpScreen(Screen):
    """Écran d'aide avec raccourcis."""

    BINDINGS = [
        ("escape", "close", "Fermer"),
        ("f1", "close", "Fermer"),
    ]

    def compose(self):
        yield Vertical(
            Static("⌨️ RACCOURCIS APEX TUI", id="help-title", classes="help-section"),
            Static("""
┌─ Navigation ────────────────────────────────────────────┐
│ Entrée          Envoyer le message                       │
│ Maj + Entrée    Nouvelle ligne                           │
│ Ctrl + C        Interrompre la génération                │
│ Ctrl + L        Effacer la conversation                  │
│ Ctrl + Q        Quitter                                  │
├─ Historique & Complétion ───────────────────────────────┤
│ ↑ / ↓           Naviguer dans l'historique               │
│ Tab             Complétion (commandes, agents)           │
│ Échap           Annuler la complétion                    │
├─ Panels ────────────────────────────────────────────────┤
│ F1              Aide                                     │
│ F2              Toggle sidebar Agents                    │
│ F3              Toggle panel Mémoire                     │
│ F4              Toggle mode compact                      │
├─ Commandes slash ───────────────────────────────────────┤
│ /help           Affiche cette aide                       │
│ /agents         Liste les agents                         │
│ /memory         Affiche la mémoire                       │
│ /clear          Efface la conversation                   │
│ /settings       Ouvre les paramètres                     │
│ /agent <nom>    Force un agent                           │
│ /model <nom>    Force un modèle                          │
│ /project <nom>  Définit le projet                        │
├─ Copie ─────────────────────────────────────────────────┤
│ Ctrl+Shift+C    Copier dernier bloc de code              │
└─────────────────────────────────────────────────────────┘
            """, classes="help-content"),
            Horizontal(
                Button("Fermer (Échap)", id="close_btn", variant="primary"),
                id="help-buttons",
            ),
            id="help-screen",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "close_btn":
            self.app.pop_screen()

    def action_close(self):
        self.app.pop_screen()