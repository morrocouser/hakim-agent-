from __future__ import annotations

from pydantic import BaseModel, Field
from axiom.tools.registry import axiom_tool, ToolContext
from axiom.tools.web_search import WebSearchTool
from axiom.tools.file_manager import FileManager
from axiom.tools.code_executor import CodeExecutor
from axiom.tools.error_log import ErrorLog
from typing import Optional


class WebSearchParams(BaseModel):
    query: str = Field(..., description="Requ\u00eate de recherche web")
    max_results: int = Field(5, ge=1, le=20, description="Nombre de r\u00e9sultats")


@axiom_tool(name="web_search", description="Recherche web et retourne les r\u00e9sultats en texte.", permissions="read", schema=WebSearchParams)
async def _web_search(params: WebSearchParams, ctx: ToolContext) -> str:
    tool: WebSearchTool = ctx.web_search or WebSearchTool()
    return await tool.search(params.query, params.max_results)


class FileReadParams(BaseModel):
    path: str = Field(..., description="Chemin relatif au workspace")


@axiom_tool(name="file_read", description="Lit le contenu d'un fichier du workspace.", permissions="read", schema=FileReadParams)
def _file_read(params: FileReadParams, ctx: ToolContext) -> str:
    tool: FileManager = ctx.file_manager or FileManager()
    return tool.read_file(params.path)


class FileCreateParams(BaseModel):
    path: str = Field(..., description="Chemin relatif au workspace")
    content: str = Field(..., description="Contenu du fichier \u00e0 cr\u00e9er")


@axiom_tool(name="file_create", description="Cr\u00e9e ou \u00e9cras\u00e9 un fichier dans le workspace.", permissions="write", schema=FileCreateParams)
def _file_create(params: FileCreateParams, ctx: ToolContext) -> str:
    tool: FileManager = ctx.file_manager or FileManager()
    return tool.create_file(params.path, params.content)


class FileDeleteParams(BaseModel):
    path: str = Field(..., description="Chemin relatif au workspace")


@axiom_tool(name="file_delete", description="Supprime un fichier du workspace.", permissions="write", schema=FileDeleteParams)
def _file_delete(params: FileDeleteParams, ctx: ToolContext) -> str:
    tool: FileManager = ctx.file_manager or FileManager()
    return tool.delete_file(params.path)


class CodeExecuteParams(BaseModel):
    language: str = Field("python", description="python | javascript | bash | sql")
    code: str = Field(..., description="Code \u00e0 ex\u00e9cuter")


@axiom_tool(name="code_execute", description="Ex\u00e9cute du code dans un sandbox contr\u00f4l\u00e9.", permissions="write", schema=CodeExecuteParams)
def _code_execute(params: CodeExecuteParams, ctx: ToolContext) -> str:
    tool: CodeExecutor = ctx.code_executor or CodeExecutor()
    return tool.execute(params.language, params.code)


class ErrorLogParams(BaseModel):
    tier: int = Field(1, ge=1, le=5)
    agent: str = ""
    context: str = ""
    symptom: str = Field(..., description="Sympt\u00f4me de l'erreur")
    root_cause: str = Field(..., description="Cause racine")
    fix: str = Field(..., description="Correctif")
    lesson: str = ""
    score: int = Field(5, ge=0, le=10)


@axiom_tool(name="error_log", description="Journalise une erreur apprise pour r\u00e9utilisation.", permissions="write", schema=ErrorLogParams)
def _error_log(params: ErrorLogParams, ctx: ToolContext) -> str:
    tool: ErrorLog = ctx.error_log or ErrorLog()
    entry = tool.log(
        tier=params.tier, agent=params.agent, context=params.context,
        symptom=params.symptom, root_cause=params.root_cause,
        fix=params.fix, lesson=params.lesson, score=params.score,
    )
    return f"Erreur enregistr\u00e9e (id={entry.id})"


def default_context(**overrides) -> ToolContext:
    """Construit un ToolContext avec les instances par d\u00e9faut des helpers."""
    base_dir = overrides.get("base_dir")
    return ToolContext(
        read_only=overrides.get("read_only", False),
        web_search=overrides.get("web_search") or WebSearchTool(),  # pragma: no cover
        file_manager=overrides.get("file_manager") or FileManager(base_dir),
        code_executor=overrides.get("code_executor") or CodeExecutor(),
        error_log=overrides.get("error_log") or ErrorLog(),
        memory=overrides.get("memory"),
    )