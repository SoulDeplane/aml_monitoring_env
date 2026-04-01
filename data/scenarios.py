"""Deterministic AML alert scenario generator.
Assembles customer profiles, transactions, and alerts into complete
scenarios for each difficulty tier.
"""

import random

from typing import Any, Dict, List

from .customers import generate_customer_profiles

from .transactions import generate_transactions


def _make_alert(
    alert_id: str,
    account_id: str,
    alert_type: str,
    description: str,
    risk_score: float,
    is_true_positive: bool,
) -> Dict[str, Any]:

    return {
        "alert_id": alert_id,
        "account_id": account_id,
        "alert_type": alert_type,
        "description": description,
        "risk_score": round(risk_score, 2),
        "status": "pending_review",
        "is_true_positive_ground_truth": is_true_positive,
    }


def generate_easy_scenario(rng: random.Random) -> Dict[str, Any]:
    """Easy: Detect obvious structuring across 3 accounts.
    3 alerts total: 2 true positives (structuring), 1 false positive.
    Patterns are straightforward — cash deposits just below $10K.
    """

    profiles = generate_customer_profiles(rng, count=10)

    transactions = generate_transactions(rng, profiles, days=30)

    review_accounts = ["ACC-0001", "ACC-0002", "ACC-0009"]

    alerts = [
        _make_alert(
            "AML-E001",
            "ACC-0001",
            "structuring",
            "Multiple cash deposits below $10,000 threshold detected within 7 days. Total: $47,230 across 5 deposits.",
            0.85,
            True,
        ),
        _make_alert(
            "AML-E002",
            "ACC-0002",
            "structuring",
            "Pattern of cash deposits in amounts between $8,000-$9,900 detected over 10 days.",
            0.78,
            True,
        ),
        _make_alert(
            "AML-E003",
            "ACC-0009",
            "high_volume",
            "Transaction volume exceeds expected monthly activity by 150%.",
            0.45,
            False,
        ),
    ]

    expected = {
        "ACC-0001": {"suspicious": True, "patterns": ["structuring"], "action": "flag"},
        "ACC-0002": {"suspicious": True, "patterns": ["structuring"], "action": "flag"},
        "ACC-0009": {"suspicious": False, "patterns": [], "action": "clear"},
    }

    return {
        "scenario_id": "AML-EASY-001",
        "title": "Cash Structuring Detection",
        "description": "Review 3 alerts for potential cash structuring (smurfing). Determine which accounts show genuine structuring patterns and which are false positives.",
        "alerts": alerts,
        "review_accounts": review_accounts,
        "profiles": {k: v for k, v in profiles.items() if k in review_accounts},
        "transactions": {k: v for k, v in transactions.items() if k in review_accounts},
        "expected": expected,
        "max_steps": 50,
        "optimal_steps": 10,
        "all_profiles": profiles,
        "all_transactions": transactions,
    }


def generate_medium_scenario(rng: random.Random) -> Dict[str, Any]:
    """Medium: Detect structuring + rapid movement + round-tripping across 5 accounts.
    5 alerts: 3 true positives, 2 false positives.
    Requires analyzing transaction patterns and cross-account relationships.
    """

    profiles = generate_customer_profiles(rng, count=15)

    transactions = generate_transactions(rng, profiles, days=60)

    review_accounts = ["ACC-0001", "ACC-0003", "ACC-0005", "ACC-0010", "ACC-0012"]

    alerts = [
        _make_alert(
            "AML-M001",
            "ACC-0001",
            "structuring",
            "Multiple sub-threshold cash deposits totaling $72,450 in 14 days.",
            0.82,
            True,
        ),
        _make_alert(
            "AML-M002",
            "ACC-0003",
            "rapid_movement",
            "Large wire transfers received and immediately forwarded. Funds held for less than 48 hours.",
            0.76,
            True,
        ),
        _make_alert(
            "AML-M003",
            "ACC-0005",
            "round_tripping",
            "Suspicious circular fund flows detected. $180,000 sent to offshore account returned through different entity.",
            0.88,
            True,
        ),
        _make_alert(
            "AML-M004",
            "ACC-0010",
            "velocity",
            "Unusual spike in wire transfer activity — 15 transfers in 3 days vs normal 2/month.",
            0.52,
            False,
        ),
        _make_alert(
            "AML-M005",
            "ACC-0012",
            "geographic_risk",
            "Multiple transactions involving high-risk jurisdiction (Cayman Islands).",
            0.48,
            False,
        ),
    ]

    expected = {
        "ACC-0001": {"suspicious": True, "patterns": ["structuring"], "action": "flag"},
        "ACC-0003": {
            "suspicious": True,
            "patterns": ["rapid_movement"],
            "action": "flag",
        },
        "ACC-0005": {
            "suspicious": True,
            "patterns": ["round_tripping"],
            "action": "file_sar",
        },
        "ACC-0010": {"suspicious": False, "patterns": [], "action": "clear"},
        "ACC-0012": {"suspicious": False, "patterns": [], "action": "clear"},
    }

    return {
        "scenario_id": "AML-MED-001",
        "title": "Multi-Pattern Transaction Review",
        "description": "Review 5 alerts spanning structuring, rapid fund movement, and round-tripping patterns. Distinguish true suspicious activity from legitimate high-volume business operations.",
        "alerts": alerts,
        "review_accounts": review_accounts,
        "profiles": {k: v for k, v in profiles.items() if k in review_accounts},
        "transactions": {k: v for k, v in transactions.items() if k in review_accounts},
        "expected": expected,
        "max_steps": 100,
        "optimal_steps": 20,
        "all_profiles": profiles,
        "all_transactions": transactions,
    }


def generate_hard_scenario(rng: random.Random) -> Dict[str, Any]:
    """Hard: Detect a money laundering network with layering and shell companies.
    8 alerts: 5 true positives, 3 false positives.
    Requires cross-account network analysis, shell company identification,
    layering detection, and filing SARs for the most egregious cases.
    The hard part: accounts ACC-0006 and ACC-0007 are connected through a
    layering network that's only visible when you trace transaction counterparties
    across multiple accounts. ACC-0008 uses network structuring with coordinated
    deposits from satellite accounts.
    """

    profiles = generate_customer_profiles(rng, count=25)

    transactions = generate_transactions(rng, profiles, days=90)

    review_accounts = [
        "ACC-0004",
        "ACC-0006",
        "ACC-0007",
        "ACC-0008",
        "ACC-0011",
        "ACC-0013",
        "ACC-0015",
        "ACC-0018",
    ]

    alerts = [
        _make_alert(
            "AML-H001",
            "ACC-0004",
            "combined_patterns",
            "Account shows both structuring and rapid movement patterns. Multiple sub-threshold deposits followed by immediate international wires.",
            0.91,
            True,
        ),
        _make_alert(
            "AML-H002",
            "ACC-0006",
            "layering",
            "Complex multi-hop international transfers. Funds received from 4 different entities and redistributed to 6 others across 3 jurisdictions.",
            0.87,
            True,
        ),
        _make_alert(
            "AML-H003",
            "ACC-0007",
            "shell_company",
            "Multiple large transfers to/from entities registered in offshore jurisdictions with no clear business purpose.",
            0.93,
            True,
        ),
        _make_alert(
            "AML-H004",
            "ACC-0008",
            "network_activity",
            "Account receiving coordinated sub-threshold transfers from 12 linked accounts, subsequently wired to offshore entity.",
            0.89,
            True,
        ),
        _make_alert(
            "AML-H005",
            "ACC-0011",
            "geographic_risk",
            "Wire transfers to multiple high-risk jurisdictions totaling $340,000 in 90 days.",
            0.58,
            False,
        ),
        _make_alert(
            "AML-H006",
            "ACC-0013",
            "velocity",
            "Transaction count 300% above historical average.",
            0.42,
            False,
        ),
        _make_alert(
            "AML-H007",
            "ACC-0015",
            "large_cash",
            "Series of cash deposits totaling $85,000 in 30 days.",
            0.55,
            False,
        ),
        _make_alert(
            "AML-H008",
            "ACC-0018",
            "layering",
            "International wire received, split into 3 domestic transfers, then consolidated and wired to BVI entity.",
            0.84,
            True,
        ),
    ]

    expected = {
        "ACC-0004": {
            "suspicious": True,
            "patterns": ["structuring", "rapid_movement"],
            "action": "file_sar",
        },
        "ACC-0006": {
            "suspicious": True,
            "patterns": ["layering"],
            "action": "file_sar",
        },
        "ACC-0007": {
            "suspicious": True,
            "patterns": ["layering", "shell_company"],
            "action": "file_sar",
        },
        "ACC-0008": {
            "suspicious": True,
            "patterns": ["network_structuring", "shell_company"],
            "action": "file_sar",
        },
        "ACC-0011": {"suspicious": False, "patterns": [], "action": "clear"},
        "ACC-0013": {"suspicious": False, "patterns": [], "action": "clear"},
        "ACC-0015": {"suspicious": False, "patterns": [], "action": "clear"},
        "ACC-0018": {
            "suspicious": True,
            "patterns": ["layering"],
            "action": "file_sar",
        },
    }

    network = {
        "ACC-0006": {
            "connected_accounts": ["ACC-0007", "ACC-0008"],
            "shared_counterparties": [
                "Vanguard Offshore Holdings Ltd",
                "Neptune Ventures BVI",
            ],
            "relationship": "Accounts share counterparties and transfer patterns suggest coordinated activity",
        },
        "ACC-0007": {
            "connected_accounts": ["ACC-0006"],
            "shared_counterparties": [
                "Cascade International Trust",
                "Vanguard Offshore Holdings Ltd",
            ],
            "relationship": "Recipient of layered funds from ACC-0006's network",
        },
        "ACC-0008": {
            "connected_accounts": ["ACC-0001", "ACC-0002", "ACC-0003", "ACC-0006"],
            "shared_counterparties": ["Stellar Global Trading Seychelles"],
            "relationship": "Hub account receiving consolidated sub-threshold deposits from satellite accounts",
        },
    }

    return {
        "scenario_id": "AML-HARD-001",
        "title": "Money Laundering Network Investigation",
        "description": "Investigate 8 alerts spanning a suspected money laundering network. Identify layering schemes, shell company transactions, and coordinated structuring operations. Distinguish these from legitimate high-risk but lawful business operations. File SARs for the most egregious cases.",
        "alerts": alerts,
        "review_accounts": review_accounts,
        "profiles": {k: v for k, v in profiles.items() if k in review_accounts},
        "transactions": {k: v for k, v in transactions.items() if k in review_accounts},
        "expected": expected,
        "network": network,
        "max_steps": 200,
        "optimal_steps": 35,
        "all_profiles": profiles,
        "all_transactions": transactions,
    }


def generate_scenario(task_id: str, seed: int = 42) -> Dict[str, Any]:
    """Generate a scenario for the given difficulty level."""

    rng = random.Random(seed)

    generators = {
        "easy": generate_easy_scenario,
        "medium": generate_medium_scenario,
        "hard": generate_hard_scenario,
    }

    return generators.get(task_id, generate_easy_scenario)(rng)
