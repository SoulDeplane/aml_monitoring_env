"""Grader for Task 2 (Medium): Multi-pattern detection.

Score 0.0–1.0 based on:
- True positive detection (25%)
- False positive avoidance (20%)
- Pattern type identification (20%)
- Correct disposition (flag/clear/SAR) (20%)
- Evidence quality (15%)
"""

from typing import Any, Dict, List

def grade_medium(

    scenario: Dict[str, Any],

    investigation_log: List[Dict[str, Any]],

    flags: List[Dict[str, Any]],

    clears: List[Dict[str, Any]],

    sars: List[Dict[str, Any]],

    total_steps: int,

) -> Dict[str, Any]:

    """Grade a medium AML task episode."""

    expected = scenario["expected"]

    expected_suspicious = {k for k, v in expected.items() if v["suspicious"]}

    flagged_accounts = {f.get("account_id", "") for f in flags} | {s.get("account_id", "") for s in sars}

    correct_flags = flagged_accounts & expected_suspicious

    tp_score = len(correct_flags) / len(expected_suspicious) if expected_suspicious else 0.0

    expected_clean = {k for k, v in expected.items() if not v["suspicious"]}

    false_flags = flagged_accounts & expected_clean

    fp_score = 1.0 - (len(false_flags) / len(expected_clean)) if expected_clean else 1.0

    pattern_score = 0.0

    pattern_total = 0

    pattern_correct = 0

    for flag in flags + sars:

        acc_id = flag.get("account_id", "")

        if acc_id in expected and expected[acc_id]["suspicious"]:

            exp_patterns = set(expected[acc_id]["patterns"])

            det_patterns = set(flag.get("patterns", []))

            pattern_total += len(exp_patterns)

            pattern_correct += len(det_patterns & exp_patterns)

    if pattern_total > 0:

        pattern_score = pattern_correct / pattern_total

    disposition_score = 0.0

    total_accounts = len(expected)

    correct_dispositions = 0

    cleared_accounts = {c.get("account_id", "") for c in clears}

    sar_accounts = {s.get("account_id", "") for s in sars}

    for acc_id, exp in expected.items():

        exp_action = exp["action"]

        if exp_action == "clear" and acc_id in cleared_accounts:

            correct_dispositions += 1

        elif exp_action == "flag" and acc_id in flagged_accounts:

            correct_dispositions += 1

        elif exp_action == "file_sar" and acc_id in sar_accounts:

            correct_dispositions += 1

        elif exp_action == "file_sar" and acc_id in flagged_accounts:

            correct_dispositions += 0.5

    if total_accounts > 0:

        disposition_score = correct_dispositions / total_accounts

    evidence_actions = [a for a in investigation_log if a.get("tool") in ("review_transactions", "check_customer_profile", "analyze_pattern")]

    reviewed = {a.get("account_id") for a in evidence_actions}

    review_accounts = set(scenario["review_accounts"])

    evidence_score = len(reviewed & review_accounts) / len(review_accounts) if review_accounts else 0.0

    overall = (

        tp_score * 0.25

        + fp_score * 0.20

        + pattern_score * 0.20

        + disposition_score * 0.20

        + evidence_score * 0.15

    )

    return {

        "overall_score": round(min(1.0, max(0.0, overall)), 4),

        "breakdown": {

            "true_positive_detection": round(tp_score, 4),

            "false_positive_avoidance": round(fp_score, 4),

            "pattern_identification": round(pattern_score, 4),

            "disposition_correctness": round(disposition_score, 4),

            "evidence_quality": round(evidence_score, 4),

        },

        "total_steps": total_steps,

        "optimal_steps": scenario["optimal_steps"],

    }

