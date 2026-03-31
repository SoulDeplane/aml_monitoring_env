"""Task 1: Easy — Detect obvious cash structuring."""

TASK_DESCRIPTION = """## Task: Cash Structuring Detection
You are an AML compliance analyst reviewing transaction monitoring alerts.
**Your goal:** Review 3 alerts for potential cash structuring (smurfing) and
determine which accounts are genuinely suspicious vs. false positives.
**What is structuring?** Structuring means deliberately splitting large cash
transactions into multiple smaller ones to evade the $10,000 Currency
Transaction Report (CTR) threshold.
**Investigation approach:**
1. Review the alert details for each account
2. Check customer profiles (KYC info, risk level, business type)
3. Review transaction history — look for patterns of sub-threshold deposits
4. Flag truly suspicious accounts with the detected pattern type
5. Clear false positive alerts with justification
**Scoring criteria:**
- Correctly flagging suspicious accounts (35%)
- Correctly identifying pattern types (20%)
- Correctly clearing false positives (25%)
- Evidence quality (justification) (10%)
- Investigation efficiency (10%)
**Accounts to review:** ACC-0001, ACC-0002, ACC-0009
**Max steps:** 50 | **Optimal steps:** ~10
"""

TASK_CONFIG = {
    "task_id": "easy",
    "max_steps": 50,
    "optimal_steps": 10,
    "description": TASK_DESCRIPTION,
}
