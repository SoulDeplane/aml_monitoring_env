"""Deterministic transaction data generator for AML scenarios.

Generates realistic financial transactions with controlled suspicious patterns.
All generation uses random.Random(seed) for reproducibility.
"""

import random
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from .customers import generate_customer_profiles


# Transaction types
TRANSACTION_TYPES = [
    "wire_transfer", "ach_transfer", "cash_deposit", "cash_withdrawal",
    "check_deposit", "internal_transfer", "foreign_wire", "atm_withdrawal",
]

# Legitimate transaction descriptions
LEGITIMATE_DESCRIPTIONS = [
    "Payroll deposit", "Rent payment", "Utility bill", "Grocery purchase",
    "Insurance premium", "Mortgage payment", "Supplier invoice #{num}",
    "Client payment #{num}", "Equipment purchase", "Software subscription",
    "Travel expenses", "Consulting fee", "Sales revenue", "Tax payment",
    "Loan repayment", "Investment contribution", "Dividend distribution",
]

# Suspicious transaction descriptions (generic to avoid detection)
SUSPICIOUS_DESCRIPTIONS = [
    "Business consulting", "Advisory services", "Commission payment",
    "Management fee", "Trade settlement", "Capital contribution",
    "Service agreement", "Project funding", "Interim payment",
]


def generate_transactions(
    rng: random.Random,
    profiles: Dict[str, Dict[str, Any]],
    days: int = 90,
    base_date: Optional[datetime] = None,
) -> Dict[str, List[Dict[str, Any]]]:
    """Generate transaction histories for all accounts.

    Args:
        rng: Seeded Random instance.
        profiles: Customer profiles from generate_customer_profiles().
        days: Number of days of history to generate.
        base_date: Reference date (defaults to 2024-03-15).

    Returns:
        Dict mapping account_id to list of transactions.
    """
    if base_date is None:
        base_date = datetime(2024, 3, 15)

    all_transactions = {}
    account_ids = list(profiles.keys())

    for account_id, profile in profiles.items():
        is_suspicious = profile["is_suspicious_ground_truth"]
        txns = []

        if is_suspicious:
            txns = _generate_suspicious_transactions(
                rng, account_id, profile, account_ids, days, base_date
            )
        else:
            txns = _generate_legitimate_transactions(
                rng, account_id, profile, account_ids, days, base_date
            )

        # Sort by date
        txns.sort(key=lambda x: x["date"])
        all_transactions[account_id] = txns

    return all_transactions


def _generate_legitimate_transactions(
    rng: random.Random,
    account_id: str,
    profile: Dict[str, Any],
    all_account_ids: List[str],
    days: int,
    base_date: datetime,
) -> List[Dict[str, Any]]:
    """Generate normal, legitimate transaction patterns."""
    expected = profile["expected_monthly_volume"]
    monthly_count = expected["expected_transaction_count"]
    total_count = int(monthly_count * (days / 30))

    txns = []
    for i in range(total_count):
        date = base_date - timedelta(days=rng.randint(0, days))
        amount = round(rng.uniform(50, expected["expected_monthly_credits"] / monthly_count * 2), 2)
        is_credit = rng.random() < 0.5

        desc = rng.choice(LEGITIMATE_DESCRIPTIONS).replace("{num}", str(rng.randint(1000, 9999)))

        txns.append({
            "transaction_id": f"TXN-{account_id}-{i + 1:05d}",
            "account_id": account_id,
            "date": date.strftime("%Y-%m-%d"),
            "time": f"{rng.randint(8, 18):02d}:{rng.randint(0, 59):02d}:{rng.randint(0, 59):02d}",
            "type": rng.choice(["ach_transfer", "check_deposit", "internal_transfer", "wire_transfer"]),
            "direction": "credit" if is_credit else "debit",
            "amount": amount,
            "currency": "USD",
            "counterparty": _random_counterparty(rng, all_account_ids, account_id, external=True),
            "description": desc,
            "country_origin": profile["country"],
            "country_destination": profile["country"],
            "is_suspicious_ground_truth": False,
            "pattern_type": None,
        })

    return txns


def _generate_suspicious_transactions(
    rng: random.Random,
    account_id: str,
    profile: Dict[str, Any],
    all_account_ids: List[str],
    days: int,
    base_date: datetime,
) -> List[Dict[str, Any]]:
    """Generate transactions with embedded suspicious patterns."""
    txns = []

    # Add some legitimate transactions as cover
    legit_count = rng.randint(10, 25)
    for i in range(legit_count):
        date = base_date - timedelta(days=rng.randint(0, days))
        amount = round(rng.uniform(100, 5000), 2)
        desc = rng.choice(LEGITIMATE_DESCRIPTIONS).replace("{num}", str(rng.randint(1000, 9999)))
        txns.append({
            "transaction_id": f"TXN-{account_id}-L{i + 1:04d}",
            "account_id": account_id,
            "date": date.strftime("%Y-%m-%d"),
            "time": f"{rng.randint(8, 18):02d}:{rng.randint(0, 59):02d}:{rng.randint(0, 59):02d}",
            "type": rng.choice(["ach_transfer", "check_deposit"]),
            "direction": rng.choice(["credit", "debit"]),
            "amount": amount,
            "currency": "USD",
            "counterparty": _random_counterparty(rng, all_account_ids, account_id, external=True),
            "description": desc,
            "country_origin": profile["country"],
            "country_destination": profile["country"],
            "is_suspicious_ground_truth": False,
            "pattern_type": None,
        })

    # Determine which suspicious patterns to apply
    idx = int(account_id.split("-")[1])  # 1-based index
    patterns = _get_patterns_for_account(idx, rng)

    for pattern_type in patterns:
        suspicious_txns = _generate_pattern(
            rng, account_id, profile, all_account_ids, pattern_type, days, base_date
        )
        txns.extend(suspicious_txns)

    return txns


def _get_patterns_for_account(idx: int, rng: random.Random) -> List[str]:
    """Assign suspicious patterns to accounts deterministically."""
    pattern_map = {
        1: ["structuring"],                          # Easy: cash structuring
        2: ["structuring"],                          # Easy: more structuring
        3: ["rapid_movement"],                       # Easy: rapid in/out
        4: ["structuring", "rapid_movement"],        # Medium: combined
        5: ["round_tripping"],                       # Medium: circular flows
        6: ["layering"],                             # Hard: multi-hop layering
        7: ["layering", "shell_company"],            # Hard: layering + shells
        8: ["network_structuring", "shell_company"], # Hard: network-based
    }
    return pattern_map.get(idx, [])


def _generate_pattern(
    rng: random.Random,
    account_id: str,
    profile: Dict[str, Any],
    all_account_ids: List[str],
    pattern_type: str,
    days: int,
    base_date: datetime,
) -> List[Dict[str, Any]]:
    """Generate transactions matching a specific suspicious pattern."""

    if pattern_type == "structuring":
        return _pattern_structuring(rng, account_id, profile, days, base_date)
    elif pattern_type == "rapid_movement":
        return _pattern_rapid_movement(rng, account_id, profile, all_account_ids, days, base_date)
    elif pattern_type == "round_tripping":
        return _pattern_round_tripping(rng, account_id, profile, all_account_ids, days, base_date)
    elif pattern_type == "layering":
        return _pattern_layering(rng, account_id, profile, all_account_ids, days, base_date)
    elif pattern_type == "shell_company":
        return _pattern_shell_company(rng, account_id, profile, days, base_date)
    elif pattern_type == "network_structuring":
        return _pattern_network_structuring(rng, account_id, profile, all_account_ids, days, base_date)
    return []


def _pattern_structuring(
    rng: random.Random, account_id: str, profile: Dict, days: int, base_date: datetime
) -> List[Dict]:
    """Structuring: Multiple cash deposits just below $10,000 threshold.

    Classic smurfing pattern — split large amounts into sub-threshold deposits.
    """
    txns = []
    # Generate 5-10 deposits just under $10,000 within a short window
    num_deposits = rng.randint(5, 10)
    window_start = base_date - timedelta(days=rng.randint(5, 30))

    for i in range(num_deposits):
        day_offset = rng.randint(0, 7)
        amount = round(rng.uniform(8200, 9900), 2)  # Just under $10K

        txns.append({
            "transaction_id": f"TXN-{account_id}-S{i + 1:04d}",
            "account_id": account_id,
            "date": (window_start + timedelta(days=day_offset)).strftime("%Y-%m-%d"),
            "time": f"{rng.randint(9, 16):02d}:{rng.randint(0, 59):02d}:{rng.randint(0, 59):02d}",
            "type": "cash_deposit",
            "direction": "credit",
            "amount": amount,
            "currency": "USD",
            "counterparty": "CASH",
            "description": "Cash deposit",
            "country_origin": profile["country"],
            "country_destination": profile["country"],
            "is_suspicious_ground_truth": True,
            "pattern_type": "structuring",
        })

    return txns


def _pattern_rapid_movement(
    rng: random.Random, account_id: str, profile: Dict,
    all_ids: List[str], days: int, base_date: datetime
) -> List[Dict]:
    """Rapid movement: Large sum deposited and immediately wired out.

    Funds pass through the account within 24-48 hours (pass-through).
    """
    txns = []
    num_cycles = rng.randint(3, 6)

    for i in range(num_cycles):
        amount = round(rng.uniform(15000, 75000), 2)
        deposit_date = base_date - timedelta(days=rng.randint(5, 60))
        withdrawal_date = deposit_date + timedelta(days=rng.randint(0, 2))

        # Deposit
        txns.append({
            "transaction_id": f"TXN-{account_id}-RM{i * 2 + 1:04d}",
            "account_id": account_id,
            "date": deposit_date.strftime("%Y-%m-%d"),
            "time": f"{rng.randint(9, 14):02d}:{rng.randint(0, 59):02d}:00",
            "type": "wire_transfer",
            "direction": "credit",
            "amount": amount,
            "currency": "USD",
            "counterparty": _random_counterparty(rng, all_ids, account_id),
            "description": rng.choice(SUSPICIOUS_DESCRIPTIONS),
            "country_origin": rng.choice(["United States", "United Kingdom", "Singapore"]),
            "country_destination": profile["country"],
            "is_suspicious_ground_truth": True,
            "pattern_type": "rapid_movement",
        })

        # Quick withdrawal (90-95% of deposit)
        out_amount = round(amount * rng.uniform(0.90, 0.95), 2)
        txns.append({
            "transaction_id": f"TXN-{account_id}-RM{i * 2 + 2:04d}",
            "account_id": account_id,
            "date": withdrawal_date.strftime("%Y-%m-%d"),
            "time": f"{rng.randint(14, 17):02d}:{rng.randint(0, 59):02d}:00",
            "type": "foreign_wire",
            "direction": "debit",
            "amount": out_amount,
            "currency": "USD",
            "counterparty": _random_counterparty(rng, all_ids, account_id),
            "description": rng.choice(SUSPICIOUS_DESCRIPTIONS),
            "country_origin": profile["country"],
            "country_destination": rng.choice(HIGH_RISK_COUNTRIES),
            "is_suspicious_ground_truth": True,
            "pattern_type": "rapid_movement",
        })

    return txns


def _pattern_round_tripping(
    rng: random.Random, account_id: str, profile: Dict,
    all_ids: List[str], days: int, base_date: datetime
) -> List[Dict]:
    """Round-tripping: Money sent out and comes back through a different channel.

    A → B → C → A pattern disguised as separate transactions.
    """
    txns = []
    num_trips = rng.randint(2, 4)
    intermediaries = [_random_counterparty(rng, all_ids, account_id) for _ in range(3)]

    for i in range(num_trips):
        amount = round(rng.uniform(20000, 100000), 2)
        start_date = base_date - timedelta(days=rng.randint(10, 60))

        # Leg 1: Send out
        txns.append({
            "transaction_id": f"TXN-{account_id}-RT{i * 3 + 1:04d}",
            "account_id": account_id,
            "date": start_date.strftime("%Y-%m-%d"),
            "time": f"{rng.randint(9, 14):02d}:{rng.randint(0, 59):02d}:00",
            "type": "wire_transfer",
            "direction": "debit",
            "amount": amount,
            "currency": "USD",
            "counterparty": intermediaries[0],
            "description": rng.choice(SUSPICIOUS_DESCRIPTIONS),
            "country_origin": profile["country"],
            "country_destination": rng.choice(HIGH_RISK_COUNTRIES),
            "is_suspicious_ground_truth": True,
            "pattern_type": "round_tripping",
        })

        # Leg 2: Comes back (slightly different amount, different source)
        return_amount = round(amount * rng.uniform(0.92, 0.98), 2)
        return_date = start_date + timedelta(days=rng.randint(5, 15))
        txns.append({
            "transaction_id": f"TXN-{account_id}-RT{i * 3 + 2:04d}",
            "account_id": account_id,
            "date": return_date.strftime("%Y-%m-%d"),
            "time": f"{rng.randint(10, 16):02d}:{rng.randint(0, 59):02d}:00",
            "type": "foreign_wire",
            "direction": "credit",
            "amount": return_amount,
            "currency": "USD",
            "counterparty": intermediaries[rng.randint(1, 2)],
            "description": rng.choice(SUSPICIOUS_DESCRIPTIONS),
            "country_origin": rng.choice(HIGH_RISK_COUNTRIES),
            "country_destination": profile["country"],
            "is_suspicious_ground_truth": True,
            "pattern_type": "round_tripping",
        })

    return txns


def _pattern_layering(
    rng: random.Random, account_id: str, profile: Dict,
    all_ids: List[str], days: int, base_date: datetime
) -> List[Dict]:
    """Layering: Complex multi-hop transactions to obscure origin.

    Multiple transfers split across intermediary accounts to distance
    the funds from their source.
    """
    txns = []
    num_layers = rng.randint(3, 6)

    for i in range(num_layers):
        amount = round(rng.uniform(10000, 50000), 2)
        layer_date = base_date - timedelta(days=rng.randint(3, 45))

        # Receive from one entity
        txns.append({
            "transaction_id": f"TXN-{account_id}-LY{i * 2 + 1:04d}",
            "account_id": account_id,
            "date": layer_date.strftime("%Y-%m-%d"),
            "time": f"{rng.randint(9, 13):02d}:{rng.randint(0, 59):02d}:00",
            "type": rng.choice(["wire_transfer", "foreign_wire"]),
            "direction": "credit",
            "amount": amount,
            "currency": "USD",
            "counterparty": _random_counterparty(rng, all_ids, account_id),
            "description": rng.choice(SUSPICIOUS_DESCRIPTIONS),
            "country_origin": rng.choice(HIGH_RISK_COUNTRIES + NORMAL_COUNTRIES),
            "country_destination": profile["country"],
            "is_suspicious_ground_truth": True,
            "pattern_type": "layering",
        })

        # Send to different entity (split or full, different day)
        out_date = layer_date + timedelta(days=rng.randint(1, 4))
        num_splits = rng.randint(1, 3)
        remaining = amount
        for j in range(num_splits):
            split_amount = round(remaining / (num_splits - j) * rng.uniform(0.8, 1.2), 2)
            split_amount = min(split_amount, remaining)
            remaining -= split_amount

            txns.append({
                "transaction_id": f"TXN-{account_id}-LY{i * 2 + 2:04d}-{j}",
                "account_id": account_id,
                "date": out_date.strftime("%Y-%m-%d"),
                "time": f"{rng.randint(14, 17):02d}:{rng.randint(0, 59):02d}:00",
                "type": "wire_transfer",
                "direction": "debit",
                "amount": split_amount,
                "currency": "USD",
                "counterparty": _random_counterparty(rng, all_ids, account_id),
                "description": rng.choice(SUSPICIOUS_DESCRIPTIONS),
                "country_origin": profile["country"],
                "country_destination": rng.choice(HIGH_RISK_COUNTRIES),
                "is_suspicious_ground_truth": True,
                "pattern_type": "layering",
            })

    return txns


def _pattern_shell_company(
    rng: random.Random, account_id: str, profile: Dict,
    days: int, base_date: datetime
) -> List[Dict]:
    """Shell company: Transactions with known shell company entities."""
    from .customers import SHELL_COMPANY_NAMES

    txns = []
    num_txns = rng.randint(4, 8)

    for i in range(num_txns):
        amount = round(rng.uniform(25000, 200000), 2)
        txn_date = base_date - timedelta(days=rng.randint(5, 60))

        txns.append({
            "transaction_id": f"TXN-{account_id}-SC{i + 1:04d}",
            "account_id": account_id,
            "date": txn_date.strftime("%Y-%m-%d"),
            "time": f"{rng.randint(9, 17):02d}:{rng.randint(0, 59):02d}:00",
            "type": "foreign_wire",
            "direction": rng.choice(["credit", "debit"]),
            "amount": amount,
            "currency": "USD",
            "counterparty": rng.choice(SHELL_COMPANY_NAMES),
            "description": rng.choice(SUSPICIOUS_DESCRIPTIONS),
            "country_origin": rng.choice(HIGH_RISK_COUNTRIES),
            "country_destination": rng.choice(HIGH_RISK_COUNTRIES),
            "is_suspicious_ground_truth": True,
            "pattern_type": "shell_company",
        })

    return txns


def _pattern_network_structuring(
    rng: random.Random, account_id: str, profile: Dict,
    all_ids: List[str], days: int, base_date: datetime
) -> List[Dict]:
    """Network structuring: Coordinated deposits across related accounts.

    Multiple accounts making similar-sized deposits at similar times,
    then consolidating into one account.
    """
    from .customers import SHELL_COMPANY_NAMES as _SHELL_NAMES
    txns = []
    # This account receives consolidated funds from multiple "smurfs"
    num_inflows = rng.randint(5, 12)

    for i in range(num_inflows):
        amount = round(rng.uniform(7500, 9800), 2)  # Sub-threshold
        txn_date = base_date - timedelta(days=rng.randint(3, 20))

        txns.append({
            "transaction_id": f"TXN-{account_id}-NS{i + 1:04d}",
            "account_id": account_id,
            "date": txn_date.strftime("%Y-%m-%d"),
            "time": f"{rng.randint(10, 16):02d}:{rng.randint(0, 59):02d}:00",
            "type": "internal_transfer",
            "direction": "credit",
            "amount": amount,
            "currency": "USD",
            "counterparty": rng.choice([aid for aid in all_ids if aid != account_id]),
            "description": "Transfer from linked account",
            "country_origin": profile["country"],
            "country_destination": profile["country"],
            "is_suspicious_ground_truth": True,
            "pattern_type": "network_structuring",
        })

    # Large outflow after consolidation
    total_inflow = sum(t["amount"] for t in txns)
    txns.append({
        "transaction_id": f"TXN-{account_id}-NS-OUT",
        "account_id": account_id,
        "date": base_date.strftime("%Y-%m-%d"),
        "time": f"{rng.randint(14, 17):02d}:{rng.randint(0, 59):02d}:00",
        "type": "foreign_wire",
        "direction": "debit",
        "amount": round(total_inflow * 0.95, 2),
        "currency": "USD",
        "counterparty": rng.choice(_SHELL_NAMES),
        "description": rng.choice(SUSPICIOUS_DESCRIPTIONS),
        "country_origin": profile["country"],
        "country_destination": rng.choice(HIGH_RISK_COUNTRIES),
        "is_suspicious_ground_truth": True,
        "pattern_type": "network_structuring",
    })

    return txns


def _random_counterparty(rng: random.Random, all_ids: List[str], exclude_id: str, external: bool = False) -> str:
    """Generate a counterparty reference."""
    if external or rng.random() < 0.6:
        from .customers import COMPANY_NAMES, FIRST_NAMES, LAST_NAMES
        if rng.random() < 0.5:
            return rng.choice(COMPANY_NAMES)
        return f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}"
    else:
        candidates = [aid for aid in all_ids if aid != exclude_id]
        return rng.choice(candidates) if candidates else "EXTERNAL"


# Import from customers for _pattern_shell_company
from .customers import HIGH_RISK_COUNTRIES, NORMAL_COUNTRIES
