"""Grader for Task 1 (Easy): Structuring detection.

Score 0.0–1.0 based on:
- Correctly flagging suspicious accounts (35%)
- Pattern type identification (20%)
- Correctly clearing false positives (25%)
- Evidence quality (10%)
- Efficiency (10%)
"""

from typing import Any, Dict, List


def grade_easy(
    scenario: Dict[str, Any],
    investigation_log: List[Dict[str, Any]],
    flags: List[Dict[str, Any]],
    clears: List[Dict[str, Any]],
    sars: List[Dict[str, Any]],
    total_steps: int,
) -> Dict[str, Any]:
    """Grade an easy AML task episode."""
    expected = scenario["expected"]

    # 1. True positive detection (35%)
    tp_score = 0.0
    expected_suspicious = {k for k, v in expected.items() if v["suspicious"]}
    flagged_accounts = {f.get("account_id", "") for f in flags} | {s.get("account_id", "") for s in sars}
    correct_flags = flagged_accounts & expected_suspicious
    if expected_suspicious:
        tp_score = len(correct_flags) / len(expected_suspicious)

    # 2. Pattern identification (20%)
    pattern_score = 0.0
    pattern_checks = 0
    pattern_correct = 0
    for flag in flags + sars:
        acc_id = flag.get("account_id", "")
        if acc_id in expected and expected[acc_id]["suspicious"]:
            pattern_checks += 1
            detected = set(flag.get("patterns", []))
            expected_patterns = set(expected[acc_id]["patterns"])
            if detected & expected_patterns:
                pattern_correct += 1
    if pattern_checks > 0:
        pattern_score = pattern_correct / pattern_checks

    # 3. False positive avoidance (25%)
    fp_score = 1.0
    expected_clean = {k for k, v in expected.items() if not v["suspicious"]}
    false_flags = flagged_accounts & expected_clean
    if expected_clean:
        fp_score = 1.0 - (len(false_flags) / len(expected_clean))

    # 4. Evidence quality (10%)
    evidence_score = 0.0
    evidence_actions = [a for a in investigation_log if a.get("tool") in ("review_transactions", "check_customer_profile")]
    reviewed = {a.get("account_id") for a in evidence_actions}
    review_accounts = set(scenario["review_accounts"])
    if review_accounts:
        evidence_score = len(reviewed & review_accounts) / len(review_accounts)

    # 5. Efficiency (10%)
    optimal = scenario["optimal_steps"]
    efficiency_score = 1.0
    if total_steps > 2 * optimal:
        over = total_steps - 2 * optimal
        efficiency_score = max(0.0, 1.0 - (over / (2 * optimal)))

    overall = (
        tp_score * 0.35
        + pattern_score * 0.20
        + fp_score * 0.25
        + evidence_score * 0.10
        + efficiency_score * 0.10
    )

    return {
        "overall_score": round(min(1.0, max(0.0, overall)), 4),
        "breakdown": {
            "true_positive_detection": round(tp_score, 4),
            "pattern_identification": round(pattern_score, 4),
            "false_positive_avoidance": round(fp_score, 4),
            "evidence_quality": round(evidence_score, 4),
            "efficiency": round(efficiency_score, 4),
        },
        "total_steps": total_steps,
        "optimal_steps": optimal,
    }
