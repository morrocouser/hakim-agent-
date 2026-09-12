from textual.binding import Binding


BINDINGS = [
    Binding("enter", "send", "Envoyer", show=True),
    Binding("shift+enter", "newline", "Nouvelle ligne", show=False),
    Binding("ctrl+c", "interrupt", "Interrompre", show=True),
    Binding("up", "history_up", "Historique ↑", show=False),
    Binding("down", "history_down", "Historique ↓", show=False),
    Binding("tab", "complete", "Complétion", show=True),
    Binding("f1", "help", "Aide", show=True),
    Binding("f2", "toggle_agents", "Agents", show=True),
    Binding("f3", "toggle_memory", "Mémoire", show=True),
    Binding("f4", "toggle_compact", "Compact", show=True),
    Binding("ctrl+l", "clear", "Effacer", show=True),
    Binding("ctrl+shift+c", "copy_code", "Copier code", show=False),
    Binding("ctrl+q", "quit", "Quitter", show=False),
    Binding("escape", "cancel_completion", "Annuler", show=False),
]


def get_binding(key: str) -> str:
    for b in BINDINGS:
        if b.action == key:
            return b.key
    return ""