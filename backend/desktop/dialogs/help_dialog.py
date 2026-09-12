from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
from PySide6.QtCore import Qt


class HelpDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Raccourcis APEX")
        self.setMinimumSize(500, 520)
        self.setStyleSheet("""
        QDialog{background:#0a0e1a;color:#e6edf3;}
        QLabel{color:#e6edf3;font-size:13px;}
        QPushButton{background:#3b82f6;color:white;border:none;border-radius:6px;padding:8px 24px;font-weight:bold;}
        QPushButton:hover{background:#2563eb;}
        """)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel("⌨️  RACCOURCIS CLAVIER")
        title.setStyleSheet("font-size:18px;font-weight:bold;color:#3b82f6;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        text = QLabel(
            '<table style="width:100%;border-collapse:collapse;color:#e6edf3;font-size:13px;">'
            '<tr style="color:#3b82f6;font-weight:bold;"><td style="padding:6px;">Touche</td><td style="padding:6px;">Action</td></tr>'
            '<tr style="border-bottom:1px solid #1e293b;"><td style="padding:6px;color:#22c55e;">Ctrl+Entrée</td><td style="padding:6px;">Envoyer</td></tr>'
            '<tr style="border-bottom:1px solid #1e293b;"><td style="padding:6px;color:#22c55e;">↑ / ↓</td><td style="padding:6px;">Historique</td></tr>'
            '<tr style="border-bottom:1px solid #1e293b;"><td style="padding:6px;color:#eab308;">Ctrl+I</td><td style="padding:6px;">Interrompre</td></tr>'
            '<tr style="border-bottom:1px solid #1e293b;"><td style="padding:6px;color:#22c55e;">F1</td><td style="padding:6px;">Aide</td></tr>'
            '<tr style="border-bottom:1px solid #1e293b;"><td style="padding:6px;color:#22c55e;">F2</td><td style="padding:6px;">Panneau Agents</td></tr>'
            '<tr style="border-bottom:1px solid #1e293b;"><td style="padding:6px;color:#22c55e;">F3</td><td style="padding:6px;">Panneau Memoire</td></tr>'
            '<tr style="border-bottom:1px solid #1e293b;"><td style="padding:6px;color:#22c55e;">Ctrl+L</td><td style="padding:6px;">Effacer chat</td></tr>'
            '<tr style="border-bottom:1px solid #1e293b;"><td style="padding:6px;color:#22c55e;">Ctrl+,</td><td style="padding:6px;">Parametres</td></tr>'
            '<tr style="border-bottom:1px solid #1e293b;"><td style="padding:6px;color:#ef4444;">Ctrl+Q</td><td style="padding:6px;">Quitter</td></tr>'
            '</table>'
            '<br>'
            '<table style="width:100%;border-collapse:collapse;color:#e6edf3;font-size:13px;">'
            '<tr style="color:#eab308;font-weight:bold;"><td style="padding:6px;">Commande</td><td style="padding:6px;">Description</td></tr>'
            '<tr style="border-bottom:1px solid #1e293b;"><td style="padding:6px;color:#22c55e;">/help</td><td style="padding:6px;">Affiche cette aide</td></tr>'
            '<tr style="border-bottom:1px solid #1e293b;"><td style="padding:6px;color:#22c55e;">/clear</td><td style="padding:6px;">Efface la conversation</td></tr>'
            '<tr style="border-bottom:1px solid #1e293b;"><td style="padding:6px;color:#22c55e;">/agents</td><td style="padding:6px;">Liste les agents</td></tr>'
            '<tr style="border-bottom:1px solid #1e293b;"><td style="padding:6px;color:#22c55e;">/memory</td><td style="padding:6px;">Affiche la memoire</td></tr>'
            '<tr style="border-bottom:1px solid #1e293b;"><td style="padding:6px;color:#22c55e;">/agent &lt;nom&gt;</td><td style="padding:6px;">Force un agent</td></tr>'
            '<tr style="border-bottom:1px solid #1e293b;"><td style="padding:6px;color:#22c55e;">/model &lt;nom&gt;</td><td style="padding:6px;">Force un modele</td></tr>'
            '<tr style="border-bottom:1px solid #1e293b;"><td style="padding:6px;color:#22c55e;">/project &lt;nom&gt;</td><td style="padding:6px;">Definit le projet</td></tr>'
            '<tr style="border-bottom:1px solid #1e293b;"><td style="padding:6px;color:#22c55e;">/score &lt;desc&gt;</td><td style="padding:6px;">Score une tache</td></tr>'
            '<tr><td style="padding:6px;color:#22c55e;">/settings</td><td style="padding:6px;">Ouvre les parametres</td></tr>'
            '</table>'
        )
        text.setTextFormat(Qt.RichText)
        text.setWordWrap(True)
        text.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(text)

        close_btn = QPushButton("Fermer")
        close_btn.clicked.connect(self.accept)
        row = QHBoxLayout()
        row.addStretch()
        row.addWidget(close_btn)
        layout.addLayout(row)
