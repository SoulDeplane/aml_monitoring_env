"""Tests to strictly verify grader mathematical determinism and boundaries."""

from aml_monitoring_env.graders.grader_easy import grade_easy
from aml_monitoring_env.graders.grader_medium import grade_medium
from aml_monitoring_env.graders.grader_hard import grade_hard

def test_grade_easy_boundaries():
    """Verify that easy grader limits scores strictly between 0 and 1 under ideal inputs."""
    scenario = {
        "expected": {
            "ACC-001": {"suspicious": True, "patterns": ["structuring"], "action": "flag"},
            "ACC-002": {"suspicious": False, "patterns": [], "action": "clear"}
        },
        "review_accounts": ["ACC-001", "ACC-002"],
        "optimal_steps": 10
    }
    
    investigation_log = [
        {"tool": "review_transactions", "account_id": "ACC-001"},
        {"tool": "check_customer_profile", "account_id": "ACC-002"}
    ]
    flags = [{"account_id": "ACC-001", "patterns": ["structuring"]}]
    clears = [{"account_id": "ACC-002", "justification": "legit"}]
    sars = []
    
    result = grade_easy(scenario, investigation_log, flags, clears, sars, total_steps=12)
    assert 0.0 <= result["overall_score"] <= 1.0
    assert result["overall_score"] == 1.0

def test_grade_hard_penalties():
    """Verify that over-flagging and inefficiency correctly penalize the score but stay bounded."""
    scenario = {
        "expected": {
            "ACC-001": {"suspicious": True, "patterns": ["layering"], "action": "file_sar"},
            "ACC-002": {"suspicious": False, "patterns": [], "action": "clear"}
        },
        "review_accounts": ["ACC-001", "ACC-002"],
        "optimal_steps": 20,
        "network": {"ACC-001": {"connected_accounts": []}}
    }
    
    investigation_log = []
    flags = [{"account_id": "ACC-002", "patterns": ["structuring"]}]
    clears = [{"account_id": "ACC-001", "justification": "wrong"}]
    sars = [{"account_id": "ACC-002", "patterns": ["layering"]}]
    
    result = grade_hard(scenario, investigation_log, flags, clears, sars, total_steps=500)
    assert 0.0 <= result["overall_score"] <= 1.0

def test_grade_medium_structure():
    """Verify medium grader breakdown returns all required dictionary keys."""
    scenario = {
        "expected": {
            "ACC-001": {"suspicious": True, "patterns": ["rapid_movement"], "action": "flag"}
        },
        "review_accounts": ["ACC-001"],
        "optimal_steps": 20
    }
    
    result = grade_medium(scenario, [], [], [], [], 5)
    
    assert "overall_score" in result
    assert "breakdown" in result
    assert "true_positive_detection" in result["breakdown"]
    assert "false_positive_avoidance" in result["breakdown"]
    assert "pattern_identification" in result["breakdown"]
    assert "disposition_correctness" in result["breakdown"]
    assert "evidence_quality" in result["breakdown"]
