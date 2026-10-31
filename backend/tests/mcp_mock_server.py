import sys, json

def send(msg):
    # MCP JSON-RPC 2.0 requires the "jsonrpc" field
    if "jsonrpc" not in msg:
        msg["jsonrpc"] = "2.0"
    sys.stdout.write(json.dumps(msg) + "\n")
    sys.stdout.flush()

while True:
    line = sys.stdin.readline()
    if not line:
        break
    msg = json.loads(line.strip())

    method = msg.get("method")
    msg_id = msg.get("id")

    if method == "initialize":
        send({
            "id": msg_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}, "prompts": {}, "resources": {}},
                "serverInfo": {"name": "test-mock", "version": "1.0.0"}
            }
        })
    elif method == "tools/list":
        send({
            "id": msg_id,
            "result": {
                "tools": [
                    {
                        "name": "echo_tool",
                        "description": "Echo a message",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "message": {"type": "string", "description": "Message to echo"}
                            },
                            "required": ["message"]
                        }
                    },
                    {
                        "name": "delete_item",
                        "description": "Delete an item (dangerous)",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "item_id": {"type": "string"}
                            },
                            "required": ["item_id"]
                        }
                    }
                ]
            }
        })
    elif method == "tools/call":
        tool_name = msg["params"]["name"]
        args = msg["params"].get("arguments", {})
        if tool_name == "echo_tool":
            text = "ECHO: " + args["message"]
            send({
                "id": msg_id,
                "result": {"content": [{"type": "text", "text": text}]}
            })
        elif tool_name == "delete_item":
            text = "Deleted item " + args["item_id"]
            send({
                "id": msg_id,
                "result": {"content": [{"type": "text", "text": text}]}
            })
        else:
            send({
                "id": msg_id,
                "error": {"code": -32601, "message": "Tool not found"}
            })
    elif method in ("prompts/list", "resources/list"):
        send({"id": msg_id, "result": {"prompts": []} if method == "prompts/list" else {"resources": []}})
    elif method is None:
        # Notification (no id) — ignore
        pass
    else:
        # Unknown method with id — send error, not empty result
        if msg_id is not None:
            send({"id": msg_id, "error": {"code": -32601, "message": "Method not found"}})
