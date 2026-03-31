"""Task 2: Medium — Multi-pattern detection with false positives."""

TASK_DESCRIPTION = """## Task: Multi-Pattern Transaction Review

You are a senior AML analyst reviewing alerts spanning multiple suspicious
activity patterns.

**Your goal:** Review 5 alerts and correctly classify each as suspicious
or legitimate. For suspicious accounts, identify the specific pattern(s).

**Patterns to look for:**
- **Structuring:** Multiple sub-$10K deposits to avoid CTR filing
- **Rapid movement:** Funds deposited and wired out within 48 hours
- **Round-tripping:** Money sent offshore and returned through different entities

**Key challenges:**
- Some alerts are FALSE POSITIVES (legitimate but unusual business)
- You must distinguish real patterns from seasonal spikes or normal intl business
- Check customer profiles to understand expected activity levels

**Investigation approach:**
1. Review each alert and check the customer profile
2. Analyze transaction patterns — look for timing, amounts, counterparties
3. Compare actual activity to expected monthly volume
4. For suspicious accounts: flag with pattern type and evidence
5. For legitimate accounts: clear with justification
6. File SARs for the most egregious cases (round-tripping)

**Scoring criteria:**
- True positive detection (25%)
- False positive avoidance (20%)
- Pattern type identification (20%)
- Correct disposition (flag/clear/SAR) (20%)
- Evidence quality (15%)

**Accounts to review:** ACC-0001, ACC-0003, ACC-0005, ACC-0010, ACC-0012
**Max steps:** 100 | **Optimal steps:** ~20
"""

TASK_CONFIG = {

    "task_id": "medium",

    "max_steps": 100,

    "optimal_steps": 20,

    "description": TASK_DESCRIPTION,

}

