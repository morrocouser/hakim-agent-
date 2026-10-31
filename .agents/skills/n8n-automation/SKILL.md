---
name: 'n8n-automation'
description: 'Expert n8n automation engineer - design, build, test, and govern complex multi-node workflows, webhook integrations, error handling, credentials, and API orchestration.'
---

# n8n Automation Skill

Expertise in automating workflows, connecting webhooks, integrating APIs, and managing executions with **n8n** (self-hosted or Cloud).

## Core Capabilities

1. **Workflow Architecture & Design**:
   - Design clean, resilient nodes graphs (`Webhook`, `HTTP Request`, `Code (JS/Python)`, `If/Switch`, `Merge`, `Split In Batches`).
   - Modular workflow design using sub-workflows (`Execute Workflow` node).
   - Data shaping, payload transformation, and schema validation.

2. **Webhooks & Realtime Ingestion**:
   - Webhook trigger configuration (`POST`, `GET`, webhook authentication with header tokens or HMAC).
   - Instant response vs delayed response (`Respond to Webhook` node).
   - Handling incoming events from Telegram, Discord, GitHub, Stripe, Shopify, or custom backends.

3. **Resilience & Error Handling**:
   - Error Trigger workflows (`Error Trigger` node) to catch execution failures and alert on Telegram/Discord/Slack.
   - Retry logic (`Retry on Fail`, `Max Tries`, exponential backoff).
   - Idempotency keys and payload deduplication to prevent duplicate processing.

4. **Integration with HakimAgent**:
   - Tool `n8n_manager`:
     - `trigger_webhook`: Send structured JSON payloads to any n8n webhook.
     - `list_workflows`: Inspect active and draft workflows.
     - `get_workflow`: Inspect node layouts and configurations.
     - `create_workflow`: Deploy dynamic JSON workflows.
     - `activate_workflow` / `deactivate_workflow`: Toggle production pipelines.
     - `health_check`: Test network and authentication status.

## Workflow Patterns

### Pattern A: Event-Driven Alert Pipeline
```
[Webhook Trigger] -> [Code / Format Data] -> [Discord / Telegram Node] -> [Respond 200 OK]
```

### Pattern B: Dual Sync with Fallback
```
[Cron / Schedule] -> [Fetch Source API] -> [Check Exists]
                                             ├── Yes -> [Update Record]
                                             └── No  -> [Create Record] -> [Log to DB]
```

## Production Guidelines

- **Never hardcode secrets** in Code nodes; use n8n Credentials or environment variables.
- Always configure an `Error Workflow` in workflow settings for critical tasks.
- Keep payloads lean; filter unwanted fields early in the pipeline.
