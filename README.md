---
title: AML Monitoring Env
emoji: 🚔
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 8000
---
# AML Transaction Monitoring Environment

An OpenEnv environment that simulates **Anti-Money Laundering (AML) transaction monitoring** — a regulatory requirement for every financial institution worldwide.

## Overview

An AI agent acts as an AML compliance analyst reviewing transaction monitoring alerts. The agent must analyze customer profiles, transaction histories, and inter-account relationships to detect money laundering patterns while avoiding false positives on legitimate business operations.

**Suspicious patterns to detect:**
- **Structuring (Smurfing):** Splitting large cash amounts into sub-$10K deposits to avoid CTR filing
- **Rapid movement:** Funds deposited and wired out within 48 hours (pass-through)
- **Round-tripping:** Money sent offshore, returns through different entities
- **Layering:** Multi-hop transfers across entities/jurisdictions to obscure origin
- **Shell company activity:** Transactions with offshore entities with no clear business purpose
- **Network structuring:** Coordinated sub-threshold deposits from satellite accounts

## Action Space (MCP Tools)

| Tool | Parameters | Description |
|------|-----------|-------------|
| `review_transactions` | `account_id`, `days`, `min_amount`, `transaction_type` | Get transaction history |
| `check_customer_profile` | `account_id` | Review KYC, risk level, PEP status |
| `analyze_pattern` | `account_id`, `pattern_type` | Check for specific suspicious patterns |
| `get_network` | `account_id` | Map transaction relationships |
| `flag_suspicious` | `account_id`, `patterns`, `evidence`, `risk_assessment` | Flag as suspicious |
| `file_sar` | `account_id`, `patterns`, `narrative`, `estimated_amount` | File a SAR |
| `clear_alert` | `account_id`, `justification` | Dismiss as false positive |

## Task Descriptions

### Task 1 — Easy: Cash Structuring Detection
- **Scope:** 3 alerts (2 true positives, 1 false positive)
- **Patterns:** Basic structuring (sub-$10K cash deposits)
- **Expected score:** ~0.70–0.90
- **Max steps:** 50 | Optimal: ~10

### Task 2 — Medium: Multi-Pattern Detection
- **Scope:** 5 alerts (3 true positives, 2 false positives)
- **Patterns:** Structuring, rapid movement, round-tripping
- **Expected score:** ~0.40–0.70
- **Max steps:** 100 | Optimal: ~20

### Task 3 — Hard: Money Laundering Network Investigation
- **Scope:** 8 alerts (5 true positives, 3 false positives)
- **Patterns:** Layering, shell companies, network structuring, combined patterns
- **Requires:** Cross-account network analysis, tracing fund flows through intermediaries
- **Expected score:** ~0.15–0.40
- **Max steps:** 200 | Optimal: ~35

## Reward Function

```
flag_reward:
  +0.20 for correctly flagging suspicious account
  -0.15 for false positive flag

sar_reward:
  +0.30 for correctly filing SAR on confirmed ML
  +0.10 for SAR on suspicious but flag-level account
  -0.20 for SAR on legitimate account

clear_reward:
  +0.15 for correctly clearing false positive
  -0.25 for clearing genuine suspicious activity

investigation:
  +0.05 per valid investigation action
  -0.02 for repeated redundant queries
```

## Setup

### Local
```bash
pip install -e .
uvicorn server.app:app --host 0.0.0.0 --port 8000 --reload
```

### Docker
```bash
docker build -f server/Dockerfile -t aml-monitoring-env .
docker run -p 8000:8000 aml-monitoring-env
```

### Deploy
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
| `/ws` | WebSocket | Persistent session |
| `/health` | HTTP GET | Health check |
| `/reset` | HTTP POST | Reset environment |
| `/step` | HTTP POST | Execute action |
| `/state` | HTTP GET | Get state |
| `/docs` | HTTP GET | OpenAPI docs |

## Data Model

The environment simulates 25 customer accounts:
- 15 legitimate (low risk)
- 5 medium-risk (legitimate high-volume)
- 5 genuinely suspicious (various ML patterns)
- Includes individual and corporate accounts, offshore shell companies, PEPs
- 90 days of transaction history per account
- Ground-truth labels for deterministic scoring
