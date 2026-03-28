"""Task 3: Hard — Money laundering network investigation."""

TASK_DESCRIPTION = """## Task: Money Laundering Network Investigation

You are the lead investigator on a suspected money laundering operation.

**Your goal:** Investigate 8 alerts across a network of accounts. Identify
the laundering network, trace fund flows, detect shell companies, and file
Suspicious Activity Reports (SARs) for confirmed violations — while avoiding
false positives on legitimate businesses.

**Key challenges:**
- Some accounts are CONNECTED through a layering network (not obvious from
  individual account review alone)
- Shell companies in offshore jurisdictions are used as intermediaries
- Coordinated structuring across multiple "smurf" accounts feeds a hub
- 3 of the 8 alerts are FALSE POSITIVES — legitimate businesses that trigger
  rules due to normal high-risk but lawful operations
- You must use the network analysis tool to map relationships between accounts

**Patterns to detect:**
- **Structuring + rapid movement (combined)**
- **Multi-hop layering** across 3+ entities/jurisdictions
- **Shell company transactions** with no clear business purpose
- **Network structuring** — coordinated sub-threshold deposits from satellite accounts

**Investigation approach:**
1. Review all 8 alerts for initial triage
2. Check customer profiles — look for offshore registration, new accounts, PEPs
3. Analyze transactions for each account
4. USE THE NETWORK TOOL to map relationships between suspicious accounts
5. Trace fund flows across the network
6. Flag suspicious accounts and identify the laundering typology
7. File SARs for accounts involved in confirmed money laundering
8. Clear false positives with evidence of legitimate business purpose

**Scoring criteria:**
- True positive detection — flagging all suspicious accounts (20%)
- False positive avoidance — not flagging legitimate accounts (15%)
- Pattern identification accuracy (15%)
- Network connections identified (15%)
- SAR filing decisions (10%)
- Evidence quality and completeness (15%)
- Investigation efficiency (10%)

**Accounts to review:** ACC-0004, ACC-0006, ACC-0007, ACC-0008, ACC-0011,
ACC-0013, ACC-0015, ACC-0018
**Max steps:** 200 | **Optimal steps:** ~35
"""

TASK_CONFIG = {
    "task_id": "hard",
    "max_steps": 200,
    "optimal_steps": 35,
    "description": TASK_DESCRIPTION,
}
