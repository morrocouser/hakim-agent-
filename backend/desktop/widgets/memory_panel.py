from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QLabel, QTreeWidget, QTreeWidgetItem
)
from PySide6.QtCore import Qt


class MemoryPanel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("memory_panel")
        self.setFixedWidth(320)
        self.setStyleSheet(
            "QFrame#memory_panel{background:#111827;border-right:1px solid #1e293b;}"
        )
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = QLabel(" MEMOIRE")
        header.setFixedHeight(36)
        header.setStyleSheet(
            "QLabel{background:#0d1117;color:#eab308;font-weight:bold;font-size:13px;"
            "border-bottom:1px solid #1e293b;padding-left:12px;}"
        )
        layout.addWidget(header)

        self._tree = QTreeWidget()
        self._tree.setHeaderHidden(True)
        self._tree.setRootIsDecorated(True)
        self._tree.setIndentation(16)
        self._tree.setStyleSheet(
            "QTreeWidget{background:#111827;color:#e6edf3;border:none;font-size:12px;padding:4px;}"
            "QTreeWidget::item{padding:4px 8px;}"
            "QTreeWidget::item:selected{background:#1e293b;color:#3b82f6;}"
        )
        layout.addWidget(self._tree)

        self._token_label = QLabel("Tokens: 0 / 5000")
        self._token_label.setFixedHeight(28)
        self._token_label.setStyleSheet(
            "QLabel{background:#0d1117;color:#6e7681;font-size:11px;border-top:1px solid #1e293b;padding-left:12px;}"
        )
        layout.addWidget(self._token_label)

    def update_memory(self, data: dict):
        self._tree.clear()
        working = data.get("working", {})
        episodic = data.get("episodic", {})
        semantic = data.get("semantic", {})
        tokens = data.get("tokens_estimate", 0)

        self._token_label.setText(f"Tokens: {tokens} / 5000")

        w = QTreeWidgetItem(["📋 Working Memory (Niveau 1)"])
        w.setExpanded(True)
        self._tree.addTopLevelItem(w)
        ct = working.get("current_task")
        if ct:
            w.addChild(QTreeWidgetItem([f"Tache: {ct.get('description', '')}"]))
            w.addChild(QTreeWidgetItem([f"Agent: {ct.get('agent_assigned', '')}"]))
        files = working.get("active_files", [])
        if files:
            fn = QTreeWidgetItem([f"Fichiers ({len(files)})"])
            for f in files:
                fn.addChild(QTreeWidgetItem([f"{f.get('path', '')} ({f.get('type', '')})"]))
            w.addChild(fn)

        e = QTreeWidgetItem(["📜 Episodic Memory (Niveau 2)"])
        e.setExpanded(False)
        self._tree.addTopLevelItem(e)
        user = episodic.get("user", {})
        if user.get("nom"):
            e.addChild(QTreeWidgetItem([f"Utilisateur: {user.get('nom')}"]))
        patterns = episodic.get("patterns_observés", [])
        if patterns:
            p = QTreeWidgetItem([f"Patterns ({len(patterns)})"])
            for pt in patterns[:5]:
                p.addChild(QTreeWidgetItem([pt]))
            e.addChild(p)
        history = episodic.get("historique_tâches", [])
        if history:
            h = QTreeWidgetItem([f"Historique ({len(history)} taches)"])
            for t in history[-5:]:
                h.addChild(QTreeWidgetItem([f"{t.get('id','')}: {t.get('type','')} {t.get('outcome','')}"]))
            e.addChild(h)

        s = QTreeWidgetItem(["💎 Semantic Memory (Niveau 3)"])
        s.setExpanded(False)
        self._tree.addTopLevelItem(s)
        proj = semantic.get("projet", {})
        if proj.get("nom"):
            s.addChild(QTreeWidgetItem([f"Projet: {proj.get('nom')} ({proj.get('type', '')})"]))
        stack = semantic.get("stack_technique", {})
        stack_items = {k: v for k, v in stack.items() if v}
        if stack_items:
            st = QTreeWidgetItem(["Stack technique"])
            for k, v in stack_items.items():
                st.addChild(QTreeWidgetItem([f"{k}: {v}"]))
            s.addChild(st)
        decisions = semantic.get("décisions_architecturales", [])
        if decisions:
            d = QTreeWidgetItem([f"Decisions ({len(decisions)})"])
            for dec in decisions[-5:]:
                d.addChild(QTreeWidgetItem([f"{dec.get('date','')}: {dec.get('décision','')}"]))
            s.addChild(d)
        constraints = semantic.get("contraintes_projet", [])
        if constraints:
            c = QTreeWidgetItem([f"Contraintes ({len(constraints)})"])
            for con in constraints:
                c.addChild(QTreeWidgetItem([con]))
            s.addChild(c)
