---
title: AML Monitoring Env
emoji: 🚔
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 8000
pinned: false
---
# AML Transaction Monitoring Environment

An OpenEnv environment that simulates **Anti-Money Laundering (AML) transaction monitoring** — a regulatory requirement for every financial institution worldwide. This environment trains and evaluates AI agents on real-world compliance investigation workflows.

## Motivation

Financial institutions process millions of transactions daily and are legally required to detect and report suspicious activity. AML compliance analysts review automated alerts, investigate customer profiles and transaction histories, and make disposition decisions. This domain is:

- **High-impact**: AML failures result in billions in fines annually (Wells Fargo $3B, Danske Bank €2B)
- **Complex reasoning**: Requires multi-document analysis, pattern recognition, network tracing, and judgment calls
- **Clear ground truth**: Every account has a deterministic label enabling objective grading
- **Novel for OpenEnv**: No existing AML/financial compliance environment in the ecosystem

## Action Space (MCP Tools)

The agent interacts via 7 MCP tools registered through FastMCP:

| Tool | Parameters | Description |
|------|-----------|-------------|
| `review_transactions` | `account_id`, `days`, `min_amount`, `transaction_type` | Retrieve filtered transaction history for an account |
| `check_customer_profile` | `account_id` | Review KYC data, risk level, PEP status, expected volumes |
| `analyze_pattern` | `account_id`, `pattern_type` | Run targeted analysis for a specific suspicious pattern |
| `get_network` | `account_id` | Map transaction relationships and shared counterparties |
| `flag_suspicious` | `account_id`, `patterns`, `evidence`, `risk_assessment` | Flag account as suspicious with supporting evidence |
| `file_sar` | `account_id`, `patterns`, `narrative`, `estimated_amount` | File a Suspicious Activity Report for confirmed ML |
| `clear_alert` | `account_id`, `justification` | Dismiss alert as a false positive with reasoning |

## Observation Space

Inherits from OpenEnv `Observation` base class:

| Field | Type | Description |
|-------|------|-------------|
| `done` | `bool` | Whether the episode is complete |
| `reward` | `float` | Reward signal from the last action |
| `metadata` | `dict` | Contains alerts, scenario info, progress, and investigation log |

Metadata includes: `scenario_id`, `title`, `alerts_count`, `accounts_remaining`, `accounts_total`, `flags_count`, `sars_count`, `clears_count`, `steps_taken`, `max_steps`, `feedback`, `investigation_log`, `episode_reward`.

## Task Descriptions

### Task 1 — Easy: Cash Structuring Detection
- **Scope:** 3 alerts (2 true positives, 1 false positive)
- **Patterns:** Basic cash structuring (sub-$10K deposits to avoid CTR filing)
- **Challenge:** Distinguish genuine smurfing from normal high-volume business
- **Expected score:** ~0.70–0.90
- **Max steps:** 50 | Optimal: ~10

### Task 2 — Medium: Multi-Pattern Detection
- **Scope:** 5 alerts (3 true positives, 2 false positives)
- **Patterns:** Structuring, rapid fund movement (pass-through), round-tripping
- **Challenge:** Multi-pattern recognition, correct disposition (flag vs SAR vs clear)
- **Expected score:** ~0.40–0.70
- **Max steps:** 100 | Optimal: ~20

### Task 3 — Hard: Money Laundering Network Investigation
- **Scope:** 8 alerts (5 true positives, 3 false positives)
- **Patterns:** Layering, shell companies, network structuring, combined patterns
- **Challenge:** Cross-account network analysis, tracing fund flows through intermediaries, identifying coordinated laundering operations while avoiding false positives on legitimate high-risk business
- **Expected score:** ~0.15–0.40
- **Max steps:** 200 | Optimal: ~35

## Reward Function

The reward function provides granular per-step signals to enable RL training:

```
flag_reward:
  +0.20 for correctly flagging a suspicious account
  -0.15 for false positive flag

sar_reward:
  +0.30 for correctly filing SAR on confirmed money laundering
  +0.10 for SAR on suspicious-but-flag-level account (partial credit)
  -0.20 for SAR on a legitimate account

clear_reward:
  +0.15 for correctly clearing a false positive alert
  -0.25 for clearing genuine suspicious activity

investigation_reward:
  +0.05 per valid investigative action (review, profile check, pattern analysis)
  -0.02 for repeated redundant queries on the same account/tool
```

## Data Model

The environment generates deterministic, seeded data with `random.Random(seed)`:

- **25 customer profiles**: Individual and corporate accounts across multiple jurisdictions
  - 15 legitimate (low risk)
  - 5 medium-risk (legitimate high-volume businesses)
  - 5 genuinely suspicious (various ML patterns)
- **Transaction history**: 30–90 days depending on task difficulty
- **Suspicious patterns**: Structuring, rapid movement, round-tripping, layering, shell company transactions, network structuring
- **Ground-truth labels**: Every account has a deterministic suspicious/clean label for scoring

## Setup

### Local Development
```bash
pip install -e .
uvicorn server.app:app --host 0.0.0.0 --port 8000 --reload
```

### Docker
```bash
docker build -f server/Dockerfile -t aml-monitoring-env .
docker run -p 8000:8000 aml-monitoring-env
```

### Deploy to HF Spaces
```bash
openenv push --repo-id your-username/aml-monitoring-env
```

## Running Inference

```bash
export API_BASE_URL=https://api.openai.com/v1
export MODEL_NAME=gpt-4o-mini
export OPENAI_API_KEY=your-key
python inference.py
```

## Using the Client

```python
from aml_monitoring_env import AMLMonitoringEnv

# Async (recommended)
async with AMLMonitoringEnv(base_url="http://localhost:8000") as env:
    result = await env.reset()
    tools = await env.list_tools()
    result = await env.call_tool("review_transactions", account_id="ACC-0001")
    result = await env.call_tool("check_customer_profile", account_id="ACC-0001")
    result = await env.call_tool("analyze_pattern", account_id="ACC-0001", pattern_type="structuring")
    result = await env.call_tool("flag_suspicious",
        account_id="ACC-0001",
        patterns=["structuring"],
        evidence="7 cash deposits between $8,200-$9,900 within 7 days",
        risk_assessment="high"
    )

# Sync
with AMLMonitoringEnv(base_url="http://localhost:8000").sync() as env:
    result = env.reset()
    tools = env.list_tools()
```

## Baseline Scores (gpt-4o-mini, seed=42)

| Task | Expected Score |
|------|---------------|
| Easy | ~0.75 |
| Medium | ~0.50 |
| Hard | ~0.25 |

## Endpoints

| Endpoint | Protocol | Description |
|----------|----------|-------------|
| `/ws` | WebSocket | Persistent session (used by client) |
| `/health` | HTTP GET | Health check |
| `/reset` | HTTP POST | Reset environment (stateless) |
| `/step` | HTTP POST | Execute action (stateless) |
| `/state` | HTTP GET | Get current state |
| `/docs` | HTTP GET | OpenAPI documentation |
| `/web` | HTTP GET | Interactive web UI |
