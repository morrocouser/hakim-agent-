from textual.widgets import Static, Tree
from textual.containers import Vertical
from textual.reactive import reactive
from textual.message import Message
from typing import Dict, Any, Optional


class AgentPanel(Vertical):
    """Sidebar des 8 agents avec sélection."""

    class AgentSelected(Message):
        def __init__(self, agent_name: str) -> None:
            self.agent_name = agent_name
            super().__init__()

    DEFAULT_CSS = """
    AgentPanel {
        width: 36;
    }
    """

    agents_data: reactive[Dict[str, Any]] = reactive({})
    selected_agent: reactive[Optional[str]] = reactive(None)

    def compose(self):
        yield Static("🏗️ AGENTS", id="sidebar-title")
        yield Tree("Agents", id="agent_tree")

    def on_mount(self):
        tree = self.query_one("#agent_tree", Tree)
        tree.show_root = False
        tree.show_guides = True
        self._populate_tree()

    def _populate_tree(self):
        tree = self.query_one("#agent_tree", Tree)
        tree.clear()

        # Ordre d'affichage
        order = [
            "AGENT_ARCHITECT", "AGENT_CODER", "AGENT_DEBUGGER",
            "AGENT_ANALYST", "AGENT_WRITER", "AGENT_RESEARCHER",
            "AGENT_PLANNER", "AGENT_QUICKSHOT",
        ]

        for name in order:
            data = self.agents_data.get(name, {})
            label = data.get("label", name)
            icon = data.get("icon", "🤖")
            model = data.get("default_model", "")
            model_short = model.split("/")[-1].replace(":free", "") if model else ""
            
            display = f"{icon} {label}"
            if model_short:
                display += f" [dim]({model_short})[/dim]"
            
            node = tree.root.add(display, data={"agent": name})
            if self.selected_agent == name:
                tree.select_node(node)

    def update_agents(self, agents: Dict[str, Any]):
        self.agents_data = agents
        self._populate_tree()

    def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
        node_data = event.node.data
        if node_data and "agent" in node_data:
            self.selected_agent = node_data["agent"]
            self.post_message(self.AgentSelected(self.selected_agent))

    def select_agent(self, agent_name: str):
        tree = self.query_one("#agent_tree", Tree)
        for node in tree.root.children:
            if node.data and node.data.get("agent") == agent_name:
                tree.select_node(node)
                break