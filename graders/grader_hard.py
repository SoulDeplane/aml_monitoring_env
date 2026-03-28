"""Grader for Task 3 (Hard): Money laundering network investigation.

Score 0.0–1.0 based on:
- True positive detection (20%)
- False positive avoidance (15%)
- Pattern identification accuracy (15%)
- Network connections identified (15%)
- SAR filing decisions (10%)
- Evidence quality and completeness (15%)
- Investigation efficiency (10%)
"""

from typing import Any, Dict, List, Set


def grade_hard(
    scenario: Dict[str, Any],
    investigation_log: List[Dict[str, Any]],
    flags: List[Dict[str, Any]],
    clears: List[Dict[str, Any]],
    sars: List[Dict[str, Any]],
    total_steps: int,
) -> Dict[str, Any]:
    """Grade a hard AML task episode."""
    expected = scenario["expected"]
    network = scenario.get("network", {})

    # 1. True positive detection (20%)
    expected_suspicious = {k for k, v in expected.items() if v["suspicious"]}
    flagged_accounts = {f.get("account_id", "") for f in flags} | {s.get("account_id", "") for s in sars}
    correct_flags = flagged_accounts & expected_suspicious
    tp_score = len(correct_flags) / len(expected_suspicious) if expected_suspicious else 0.0

    # 2. False positive avoidance (15%)
    expected_clean = {k for k, v in expected.items() if not v["suspicious"]}
    false_flags = flagged_accounts & expected_clean
    fp_score = 1.0 - (len(false_flags) / len(expected_clean)) if expected_clean else 1.0

    # 3. Pattern identification (15%)
    pattern_total = 0
    pattern_correct = 0
    for flag in flags + sars:
        acc_id = flag.get("account_id", "")
        if acc_id in expected and expected[acc_id]["suspicious"]:
            exp_patterns = set(expected[acc_id]["patterns"])
            det_patterns = set(flag.get("patterns", []))
            pattern_total += len(exp_patterns)
            pattern_correct += len(det_patterns & exp_patterns)
    pattern_score = pattern_correct / pattern_total if pattern_total > 0 else 0.0

    # 4. Network identification (15%)
    network_score = 0.0
    network_actions = [a for a in investigation_log if a.get("tool") == "get_network"]
    network_queried = {a.get("account_id", "") for a in network_actions}
    network_accounts = set(network.keys())
    if network_accounts:
        network_score = len(network_queried & network_accounts) / len(network_accounts)
        # Bonus if they queried network for connected accounts
        all_connected = set()
        for acc, info in network.items():
            all_connected.update(info.get("connected_accounts", []))
        connected_queried = network_queried & all_connected
        if all_connected:
            network_score = (network_score + len(connected_queried) / len(all_connected)) / 2

    # 5. SAR filing (10%)
    sar_score = 0.0
    expected_sars = {k for k, v in expected.items() if v["action"] == "file_sar"}
    sar_accounts = {s.get("account_id", "") for s in sars}
    if expected_sars:
        correct_sars = sar_accounts & expected_sars
        false_sars = sar_accounts - expected_sars
        sar_score = len(correct_sars) / len(expected_sars)
        # Penalize false SARs
        if false_sars:
            sar_score = max(0.0, sar_score - 0.2 * len(false_sars))

    # 6. Evidence quality (15%)
    evidence_tools = {"review_transactions", "check_customer_profile", "analyze_pattern", "get_network"}
    evidence_actions = [a for a in investigation_log if a.get("tool") in evidence_tools]
    reviewed = {a.get("account_id") for a in evidence_actions if a.get("account_id")}
    review_accounts = set(scenario["review_accounts"])
    evidence_score = len(reviewed & review_accounts) / len(review_accounts) if review_accounts else 0.0

    # Bonus for using diverse tools
    tools_used = {a.get("tool") for a in evidence_actions}
    if len(tools_used) >= 3:
        evidence_score = min(1.0, evidence_score + 0.1)

    # 7. Efficiency (10%)
    optimal = scenario["optimal_steps"]
    efficiency_score = 1.0
    if total_steps > 2 * optimal:
        over = total_steps - 2 * optimal
        efficiency_score = max(0.0, 1.0 - (over / (3 * optimal)))

    overall = (
        tp_score * 0.20
        + fp_score * 0.15
        + pattern_score * 0.15
        + network_score * 0.15
        + sar_score * 0.10
        + evidence_score * 0.15
        + efficiency_score * 0.10
    )

    return {
        "overall_score": round(min(1.0, max(0.0, overall)), 4),
        "breakdown": {
            "true_positive_detection": round(tp_score, 4),
            "false_positive_avoidance": round(fp_score, 4),
            "pattern_identification": round(pattern_score, 4),
            "network_identification": round(network_score, 4),
            "sar_filing": round(sar_score, 4),
            "evidence_quality": round(evidence_score, 4),
            "efficiency": round(efficiency_score, 4),
        },
        "total_steps": total_steps,
        "optimal_steps": optimal,
    }
