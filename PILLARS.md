
# Product Pillars (Locked-In Requirements)

## Pillar 1 — LangGraph Multi-Agent Architecture
Reasoner + Vision Actor operating inside a resilient LangGraph workflow with checkpointing.

## Pillar 2 — Auto-Resume & Unsticking
System wakes every ~30 minutes, checks heartbeat, and automatically restarts or recovers.

## Pillar 3 — Desktop Control via MCP
All OS and VS Code actions driven through MCP servers (list windows, focus, screenshot, input).

## Pillar 4 — Multi-VS Code Window Awareness
Actor must reliably discover, focus, and verify correct VS Code windows tied to specific repos.

## Pillar 5 — Copilot Chat Management
Open, focus, detect busy state, copy transcript, post messages, verify via screenshots.

## Pillar 6 — Repo & PR Scanning + Persistent Plans
Scan repos directory, derive long-term plan, maintain world state, drive Copilot alignment.

## Pillar 7 — Minimal Custom Tooling
Prefer reuse of existing MCP servers; only thin adapters provided.

## Pillar 8 — Flexible Reasoner ↔ Actor Interface
TaskEnvelope and ActionReport allow arbitrary metadata, screenshots, state, hints.

## Pillar 9 — Observability & Traceability
Episode logs, spans, artifacts, checkpoints, and structured state capture.

## Pillar 10 — Safety & Guardrails
Window allow-listing, dry-run mode, propose→verify→execute pattern.

