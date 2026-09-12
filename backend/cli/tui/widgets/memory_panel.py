from textual.widgets import Static, Tree, RichLog
from textual.containers import Vertical
from textual.reactive import reactive
from typing import Dict, Any


class MemoryPanel(Vertical):
    """Panel de visualisation mémoire 3 niveaux."""

    DEFAULT_CSS = """
    MemoryPanel {
        width: 48;
    }
    .memory-level {
        color: $text;
    }
    .memory-key {
        color: $accent;
        text-style: bold;
    }
    .memory-value {
        color: $text-muted;
    }
    """

    memory_data: reactive[Dict[str, Any]] = reactive({})

    def compose(self):
        yield Static("🧠 MÉMOIRE 3 NIVEAUX", id="sidebar-title")
        yield Tree("Mémoire", id="memory_tree")

    def on_mount(self):
        tree = self.query_one("#memory_tree", Tree)
        tree.show_root = False
        tree.show_guides = True
        self._populate_tree()

    def _populate_tree(self):
        tree = self.query_one("#memory_tree", Tree)
        tree.clear()

        working = self.memory_data.get("working", {})
        episodic = self.memory_data.get("episodic", {})
        semantic = self.memory_data.get("semantic", {})
        tokens = self.memory_data.get("tokens_estimate", 0)

        # Niveau 1: Working Memory
        w_node = tree.root.add("📋 Working Memory (Niveau 1)", expand=True)
        if working.get("current_task"):
            ct = working["current_task"]
            w_node.add_leaf(f"[bold]Tâche:[/bold] {ct.get('description', '')} ({ct.get('agent_assigned', '')})")
            w_node.add_leaf(f"[bold]Modèle:[/bold] {ct.get('model_assigned', '')} | Score: {ct.get('model_score', 0)}")
        if working.get("active_files"):
            files_node = w_node.add("📁 Fichiers actifs", expand=True)
            for f in working["active_files"]:
                files_node.add_leaf(f"{f.get('path', '')} ({f.get('type', '')})")
        w_node.add_leaf(f"[dim]Tokens session: {working.get('tokens_used_session', 0)}[/dim]")

        # Niveau 2: Episodic Memory
        e_node = tree.root.add("📜 Episodic Memory (Niveau 2)", expand=True)
        user = episodic.get("user", {})
        if user.get("nom"):
            e_node.add_leaf(f"[bold]Utilisateur:[/bold] {user.get('nom')} ({user.get('niveau_technique', '')})")
        if episodic.get("patterns_observés"):
            p_node = e_node.add("🔍 Patterns", expand=True)
            for p in episodic["patterns_observés"][:5]:
                p_node.add_leaf(p)
        if episodic.get("historique_tâches"):
            h_node = e_node.add(f"📝 Historique ({len(episodic['historique_tâches'])} tâches)", expand=True)
            for t in episodic["historique_tâches"][-5:]:
                h_node.add_leaf(f"{t.get('id', '')}: {t.get('type', '')} {t.get('outcome', '')}")
        if episodic.get("erreurs_apprises"):
            err_node = e_node.add("⚠️ Erreurs apprises", expand=True)
            for e in episodic["erreurs_apprises"][-5:]:
                err_node.add_leaf(f"{e.get('code', '')}: {e.get('erreur', '')} → {e.get('correction', '')}")

        # Niveau 3: Semantic Memory
        s_node = tree.root.add("💎 Semantic Memory (Niveau 3)", expand=True)
        proj = semantic.get("projet", {})
        if proj.get("nom"):
            s_node.add_leaf(f"[bold]Projet:[/bold] {proj.get('nom')} ({proj.get('type', '')})")
        stack = semantic.get("stack_technique", {})
        if any(stack.values()):
            st_node = s_node.add("🛠️ Stack", expand=True)
            for k, v in stack.items():
                if v:
                    st_node.add_leaf(f"{k}: {v}")
        if semantic.get("décisions_architecturales"):
            d_node = s_node.add("📋 Décisions", expand=True)
            for d in semantic["décisions_architecturales"][-5:]:
                d_node.add_leaf(f"{d.get('date', '')}: {d.get('décision', '')}")
        if semantic.get("contraintes_projet"):
            c_node = s_node.add("⚙️ Contraintes", expand=True)
            for c in semantic["contraintes_projet"]:
                c_node.add_leaf(c)
        if semantic.get("glossaire"):
            g_node = s_node.add("📖 Glossaire", expand=True)
            for g in semantic["glossaire"][-5:]:
                g_node.add_leaf(f"{g.get('terme', '')}: {g.get('définition', '')}")

        # Tokens
        tree.root.add_leaf(f"[dim]Total estimé: {tokens} / 5000 tokens[/dim]")

    def update_memory(self, data: Dict[str, Any]):
        self.memory_data = data
        self._populate_tree()