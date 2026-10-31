"""Tests unitaires pour les connecteurs n8n et Figma."""

import pytest
import json
from axiom.tools.n8n_tool import N8nTool
from axiom.tools.figma_tool import FigmaTool
from axiom.tools.base import ToolRegistry, ToolResultType
from axiom.tools.builtin import register_builtin_tools


@pytest.mark.asyncio
async def test_n8n_tool_schema():
    tool = N8nTool()
    assert tool.name == "n8n_manager"
    assert tool.schema.name == "n8n_manager"
    props = tool.schema.parameters["properties"]
    assert "action" in props
    assert "trigger_webhook" in props["action"]["enum"]
    assert "list_workflows" in props["action"]["enum"]


@pytest.mark.asyncio
async def test_n8n_tool_simulation_mode():
    tool = N8nTool()

    # 1. Health check
    res = await tool.execute(action="health_check")
    assert res.ok is True
    assert "n8n" in res.content.lower()

    # 2. Trigger webhook (simulated)
    res = await tool.execute(
        action="trigger_webhook",
        webhook_url="webhook/test-event",
        payload={"event": "order_created", "amount": 99.0},
    )
    assert res.ok is True
    data = json.loads(res.content)
    assert data["status"] == "simulated_success"
    assert data["payload_delivered"]["amount"] == 99.0

    # 3. List workflows
    res = await tool.execute(action="list_workflows")
    assert res.ok is True
    data = json.loads(res.content)
    assert "workflows" in data
    assert len(data["workflows"]) >= 1

    # 4. Get workflow
    res = await tool.execute(action="get_workflow", workflow_id="wf_crm_sync_01")
    assert res.ok is True
    data = json.loads(res.content)
    assert data["id"] == "wf_crm_sync_01"
    assert "nodes" in data

    # 5. Create workflow
    res = await tool.execute(
        action="create_workflow",
        workflow_data={"name": "Auto Alert Pipeline", "nodes": []},
    )
    assert res.ok is True
    data = json.loads(res.content)
    assert "Auto Alert Pipeline" in data["name"]

    # 6. Activate & deactivate
    res = await tool.execute(action="activate_workflow", workflow_id="wf_crm_sync_01")
    assert res.ok is True
    res2 = await tool.execute(action="deactivate_workflow", workflow_id="wf_crm_sync_01")
    assert res2.ok is True

    # 7. Invalid action
    res_err = await tool.execute(action="unknown_action")
    assert res_err.ok is False
    assert res_err.type == ToolResultType.ERROR


@pytest.mark.asyncio
async def test_figma_tool_schema():
    tool = FigmaTool()
    assert tool.name == "figma_manager"
    props = tool.schema.parameters["properties"]
    assert "action" in props
    assert "get_file" in props["action"]["enum"]
    assert "extract_tokens" in props["action"]["enum"]


@pytest.mark.asyncio
async def test_figma_tool_simulation_mode():
    tool = FigmaTool()

    # 1. Status
    res = await tool.execute(action="status")
    assert res.ok is True
    assert "Figma" in res.content

    # 2. Get file
    res = await tool.execute(action="get_file", file_key="app_design_v2")
    assert res.ok is True
    data = json.loads(res.content)
    assert "document" in data
    assert "components" in data

    # 3. Get nodes
    res = await tool.execute(action="get_nodes", file_key="app_design_v2", node_ids=["1:2", "2:1"])
    assert res.ok is True
    data = json.loads(res.content)
    assert "nodes" in data
    assert "1:2" in data["nodes"]

    # 4. Get components
    res = await tool.execute(action="get_components", file_key="app_design_v2")
    assert res.ok is True
    data = json.loads(res.content)
    assert len(data["components"]) >= 1

    # 5. Get styles
    res = await tool.execute(action="get_styles", file_key="app_design_v2")
    assert res.ok is True
    data = json.loads(res.content)
    assert len(data["styles"]) >= 1

    # 6. Export images
    res = await tool.execute(action="export_images", file_key="app_design_v2", node_ids=["1:2"], format="png")
    assert res.ok is True
    data = json.loads(res.content)
    assert "images" in data
    assert "1:2" in data["images"]

    # 7. Extract tokens
    res = await tool.execute(action="extract_tokens")
    assert res.ok is True
    data = json.loads(res.content)
    assert "colors" in data
    assert "spacing" in data
    assert "css_variables" in data
    assert "--primary" in data["css_variables"]

    # 8. Invalid action
    res_err = await tool.execute(action="non_existent")
    assert res_err.ok is False
    assert res_err.type == ToolResultType.ERROR


def test_builtin_registration_includes_n8n_and_figma():
    reg = ToolRegistry()
    register_builtin_tools(reg)
    tool_names = [t.name for t in reg.all_tools()]

    assert "n8n_manager" in tool_names
    assert "figma_manager" in tool_names
    assert "email_manager" in tool_names
    assert "google_drive" in tool_names
    assert "telegram_notify" in tool_names
    assert "discord_notify" in tool_names

    # Check categories
    cat_tools = reg.by_category("automation")
    assert any(t.name == "n8n_manager" for t in cat_tools)

    design_tools = reg.by_category("design")
    assert any(t.name == "figma_manager" for t in design_tools)
