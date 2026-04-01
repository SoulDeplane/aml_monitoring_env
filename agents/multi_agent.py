"""Multi-agent baseline implementation for the AML Monitoring environment.
This script demonstrates a dual-agent architecture:
1. Investigator Agent: Gathers facts using read-only analysis tools.
2. Compliance Officer Agent: Reviews the Investigator's reports and executes final dispositions.
"""

import json
import os
import sys
from openai import OpenAI

from openenv.core.env_server.mcp_types import CallToolAction

API_BASE_URL = os.environ.get("API_BASE_URL", "https://api.openai.com/v1")
MODEL_NAME = os.environ.get("MODEL_NAME", "gpt-4o-mini")
HF_TOKEN = os.environ.get("HF_TOKEN", os.environ.get("OPENAI_API_KEY", ""))

client = OpenAI(base_url=API_BASE_URL, api_key=HF_TOKEN)

INVESTIGATOR_PROMPT = """You are an AML Investigator. Your sole job is to gather facts.
You may use the following tools:
1. review_transactions(account_id, days, min_amount, transaction_type)
2. check_customer_profile(account_id)
3. analyze_pattern(account_id, pattern_type)
4. get_network(account_id)

Once you have thoroughly investigated an account and have a concrete recommendation, format your final message as:
[RECOMMENDATION]
Account: <account_id>
Action: <flag_suspicious | file_sar | clear_alert>
Evidence: <summary with patterns and risk factors>

Respond with EXACTLY ONE tool call in JSON format:
{"tool": "tool_name", "args": {"param1": "value1"}}
Do not make disposition tool calls yourself."""

OFFICER_PROMPT = """You are a Senior AML Compliance Officer.
You review recommendations from your Investigator and make the final disposition.
You must use exactly one of these tools based on the recommendation:
1. flag_suspicious(account_id, patterns, evidence, risk_assessment)
2. file_sar(account_id, patterns, narrative, estimated_amount)
3. clear_alert(account_id, justification)

Respond with EXACTLY ONE tool call in JSON format:
{"tool": "tool_name", "args": {"param1": "value1"}}"""

def _extract_json(text: str) -> dict:
    """Extract tool call JSON from model output."""
    try:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1:
            return json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        pass
    return {}

def run_multi_agent_task(task_id: str, seed: int = 42) -> float:
    """Run the multi-agent system on a specified task."""
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from server.environment import AMLMonitoringEnvironment

    env = AMLMonitoringEnvironment()
    obs = env.reset(seed=seed, task_id=task_id)
    meta = obs.metadata or {}
    alerts_text = json.dumps(meta.get("alerts", []), indent=2)
    accounts = meta.get("review_accounts", [])
    
    for account_id in accounts:
        recommendation = _run_investigator(env, account_id, alerts_text)
        _run_officer(env, account_id, recommendation)
    return getattr(env, "_episode_reward", 0.0)

def _run_investigator(env, account_id: str, alerts_text: str) -> str:
    """Run the Investigator agent to gather facts on a single account."""
    conversation = [
        {"role": "system", "content": INVESTIGATOR_PROMPT},
        {
            "role": "user",
            "content": f"Investigate account: {account_id}\n\nContext Alerts:\n{alerts_text}",
        },
    ]
    
    for _ in range(15):
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=conversation,
            temperature=0.0,
        )
        msg_content = response.choices[0].message.content or ""
        conversation.append({"role": "assistant", "content": msg_content})
        
        if "[RECOMMENDATION]" in msg_content:
            return msg_content
            
        tool_call = _extract_json(msg_content)
        if not tool_call:
            conversation.append({"role": "user", "content": "Please output valid JSON."})
            continue
            
        try:
            action = CallToolAction(tool_name=tool_call.get("tool", ""), arguments=tool_call.get("args", {}))
            obs = env.step(action)
            observation_data = getattr(obs, "result", str(obs))
            conversation.append({"role": "user", "content": str(observation_data)})
        except Exception as e:
            conversation.append({"role": "user", "content": f"Tool error: {e}"})
            
    return "[RECOMMENDATION]\nAction: clear_alert\nEvidence: Timed out during investigation."

def _run_officer(env, account_id: str, recommendation: str) -> None:
    """Run the Compliance Officer agent to execute the final disposition."""
    conversation = [
        {"role": "system", "content": OFFICER_PROMPT},
        {"role": "user", "content": f"Review this recommendation and execute the tool:\n{recommendation}"},
    ]
    
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=conversation,
        temperature=0.0,
    )
    msg_content = response.choices[0].message.content or ""
    tool_call = _extract_json(msg_content)
    
    if tool_call:
        try:
            action = CallToolAction(tool_name=tool_call.get("tool", ""), arguments=tool_call.get("args", {}))
            env.step(action)
        except Exception:
            pass

if __name__ == "__main__":
    for level in ["easy", "medium", "hard"]:
        score = run_multi_agent_task(level)
        print(f"Task {level}: executed successfully.")
