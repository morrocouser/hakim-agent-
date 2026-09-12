# -*- mode: python ; coding: utf-8 -*-
import os
import sys

block_cipher = None
backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend')

a = Analysis(
    ['backend/desktop/main.py'],
    pathex=[backend_dir],
    binaries=[],
    datas=[
        ('backend/desktop/resources', 'desktop/resources'),
        ('backend/cli/tui/css', 'cli/tui/css'),
    ],
    hiddenimports=[
        'desktop',
        'desktop.main_window',
        'desktop.widgets',
        'desktop.widgets.chat_area',
        'desktop.widgets.message_bubble',
        'desktop.widgets.input_widget',
        'desktop.widgets.agent_sidebar',
        'desktop.widgets.memory_panel',
        'desktop.widgets.status_bar',
        'desktop.dialogs',
        'desktop.dialogs.settings_dialog',
        'desktop.dialogs.help_dialog',
        'desktop.workers',
        'desktop.workers.chat_worker',
        'desktop.workers.history_manager',
        'axiom',
        'axiom.core',
        'axiom.core.scoring',
        'axiom.core.agents',
        'axiom.core.memory',
        'axiom.core.react_loop',
        'axiom.models',
        'axiom.models.schemas',
        'axiom.models.memory_models',
        'axiom.claude',
        'axiom.claude.client',
        'cli',
        'cli.tui',
        'cli.tui.config',
        'markdown',
        'markdown.extensions.fenced_code',
        'markdown.extensions.codehilite',
        'markdown.extensions.tables',
        'pygments',
        'pygments.formatters',
        'pygments.formatters.html',
        'httpx',
        'httpx._transports',
        'httpx._transports.default',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'numpy', 'pandas', 'scipy'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='AXIOM',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='AXIOM',
)
