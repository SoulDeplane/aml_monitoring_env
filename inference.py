"""Baseline inference script for AML Monitoring environment.
Runs all 3 tasks (easy, medium, hard) using an LLM agent via OpenAI API.
Produces reproducible scores with seed=42.
Usage:
    export API_BASE_URL=https://api.openai.com/v1
    export MODEL_NAME=gpt-4o-mini
    export OPENAI_API_KEY=sk-your-key
    python inference.py
"""

import json

import os

import sys

import time

import traceback

from openai import OpenAI

API_BASE_URL = os.environ.get("API_BASE_URL", "https://api.openai.com/v1")

MODEL_NAME = os.environ.get("MODEL_NAME", "gpt-4o-mini")

HF_TOKEN = os.environ.get("HF_TOKEN", os.environ.get("OPENAI_API_KEY", ""))

client = OpenAI(base_url=API_BASE_URL, api_key=HF_TOKEN)

SYSTEM_PROMPT = """You are an expert AML compliance analyst reviewing transaction monitoring alerts.
You have access to the following tools:
1. review_transactions(account_id, days, min_amount, transaction_type) - Get transaction history
2. check_customer_profile(account_id) - Review KYC and risk profile
3. analyze_pattern(account_id, pattern_type) - Check for specific suspicious patterns
   Valid patterns: structuring, rapid_movement, round_tripping, layering, shell_company, network_structuring
4. get_network(account_id) - Map transaction relationships between accounts
5. flag_suspicious(account_id, patterns, evidence, risk_assessment) - Flag as suspicious
6. file_sar(account_id, patterns, narrative, estimated_amount) - File a Suspicious Activity Report
7. clear_alert(account_id, justification) - Dismiss alert as false positive
Investigation approach:
1. Review each alert and check customer profiles
2. Analyze transaction patterns for each account
3. Look for: structuring (sub-$10K deposits), rapid movement (pass-through),
   round-tripping (circular flows), layering (multi-hop), shell companies
4. Use network tool to find connections between suspicious accounts
5. Flag/SAR/clear each account with evidence
Respond with EXACTLY ONE tool call in JSON format:
{"tool": "tool_name", "args": {"param1": "value1"}}"""


def run_task(task_id: str, seed: int = 42) -> tuple[dict, int]:
    """Run a single task and return the grading result and steps taken."""

    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

    from server.environment import AMLMonitoringEnvironment

    from openenv.core.env_server.mcp_types import CallToolAction

    env = AMLMonitoringEnvironment()

    obs = env.reset(seed=seed, task_id=task_id)

    max_steps_map = {"easy": 50, "medium": 100, "hard": 200}

    max_steps = max_steps_map.get(task_id, 50)

    meta = obs.metadata or {}

    alerts_text = json.dumps(meta.get("alerts", []), indent=2)

    conversation = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"""AML MONITORING SESSION
Title: {meta.get('title', 'Unknown')}
{meta.get('description', '')}
Task Instructions:
{meta.get('task_description', 'Review the alerts.')}
Pending Alerts:
{alerts_text}
Accounts to review: {', '.join(meta.get('review_accounts', []))}
Begin your investigation. What tool do you want to use first?""",
        },
    ]

    step = 0

    episode_done = False

    while step < max_steps and not episode_done:

        step += 1

        try:

            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=conversation,
                temperature=0.0,
                max_tokens=512,
            )

            assistant_msg = response.choices[0].message.content or ""

        except Exception as e:

            print(f"  [Step {step}] LLM call failed: {e}")

            print(f"[STEP] step={step} reward=0.0", flush=True)

            break

        conversation.append({"role": "assistant", "content": assistant_msg})

        tool_call = _parse_tool_call(assistant_msg)

        if not tool_call:

            conversation.append(
                {
                    "role": "user",
                    "content": 'Please respond with a valid tool call: {"tool": "tool_name", "args": {...}}',
                }
            )

            print(f"[STEP] step={step} reward=0.0", flush=True)

            continue

        tool_name = tool_call.get("tool", "")

        args = tool_call.get("args", {})

        print(f"  [Step {step}] {tool_name}({json.dumps(args, default=str)[:80]})")

        try:

            action = CallToolAction(tool_name=tool_name, arguments=args)

            obs = env.step(action)

            reward = float(getattr(obs, 'reward', 0.0) or 0.0)

            print(f"[STEP] step={step} reward={reward}", flush=True)

        except Exception as e:

            conversation.append(
                {
                    "role": "user",
                    "content": f"Tool call failed: {e}. Try a different approach.",
                }
            )

            print(f"[STEP] step={step} reward=0.0", flush=True)

            continue

        meta = obs.metadata or {}

        episode_done = obs.done

        remaining = meta.get("accounts_remaining", [])

        feedback = meta.get("feedback", "Action completed.")

        conversation.append(
            {
                "role": "user",
                "content": f"Result: {feedback}\n\nAccounts remaining: {remaining}\nSteps: {meta.get('steps_taken', step)}/{meta.get('max_steps', max_steps)} | Reward: {meta.get('episode_reward', 0.0)}\n\nWhat's your next action?",
            }
        )

    grader_result = getattr(env, "_grader_result", None)

    if grader_result is None:

        env._run_grader()

        grader_result = getattr(env, "_grader_result", {"overall_score": 0.0})

    env.close()

    return grader_result, step


def _parse_tool_call(text: str) -> dict | None:
    """Parse a tool call JSON from LLM response."""

    import re

    patterns = [
        r"```json\s*(\{.*?\})\s*```",
        r"```\s*(\{.*?\})\s*```",
        r'(\{[^{}]*"tool"[^{}]*\})',
    ]

    for pattern in patterns:

        match = re.search(pattern, text, re.DOTALL)

        if match:

            try:

                return json.loads(match.group(1))

            except json.JSONDecodeError:

                continue

    try:

        result = json.loads(text.strip())

        if isinstance(result, dict) and "tool" in result:

            return result

    except json.JSONDecodeError:

        pass

    return None


def main():
    """Run baseline inference."""

    print("=" * 60)

    print("AML Monitoring Environment — Baseline Inference")

    print("=" * 60)

    print(f"Model: {MODEL_NAME}")

    print(f"API: {API_BASE_URL}")

    print(f"Seed: 42")

    print()

    results = {}

    total_time = 0

    for task_id in ["easy", "medium", "hard"]:

        print(f"--- Task: {task_id.upper()} ---")

        print(f"[START] task={task_id}", flush=True)

        start = time.time()

        try:

            result, steps = run_task(task_id, seed=42)

            elapsed = time.time() - start

            total_time += elapsed

            score = result.get("overall_score", 0.0)

            results[task_id] = result

            print(f"  Score: {score:.4f}")

            print(f"  Time: {elapsed:.1f}s")
            
            print(f"[END] task={task_id} score={score} steps={steps}", flush=True)

            if "breakdown" in result:

                for key, val in result["breakdown"].items():

                    print(f"    {key}: {val:.4f}")

            print()

        except Exception as e:

            elapsed = time.time() - start

            total_time += elapsed

            print(f"  ERROR: {e}")

            traceback.print_exc()

            results[task_id] = {"overall_score": 0.0, "error": str(e)}

            print(f"[END] task={task_id} score=0.0 steps=0", flush=True)

            print()

    print("=" * 60)

    print("SUMMARY")

    print("=" * 60)

    for task_id in ["easy", "medium", "hard"]:

        score = results.get(task_id, {}).get("overall_score", 0.0)

        print(f"  {task_id.upper():8s}: {score:.4f}")

    avg = sum(r.get("overall_score", 0.0) for r in results.values()) / max(
        len(results), 1
    )

    print(f"  {'AVERAGE':8s}: {avg:.4f}")

    print(f"  Total time: {total_time:.1f}s")

    output_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "inference_results.json"
    )

    with open(output_path, "w") as f:

        json.dump(results, f, indent=2, default=str)

    print(f"\nResults saved to {output_path}")


if __name__ == "__main__":

    main()
