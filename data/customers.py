"""Customer and account profile data for AML scenarios.
Generates deterministic customer profiles, accounts, and KYC data.
"""

import random
from typing import Any, Dict, List

BUSINESS_TYPES = [
    "retail_store", "restaurant", "import_export", "real_estate",
    "consulting", "construction", "car_dealership", "jewelry_store",
    "money_service_business", "casino", "nonprofit", "law_firm",
    "gas_station", "laundromat", "convenience_store",
]
HIGH_RISK_COUNTRIES = [
    "Cayman Islands", "Panama", "British Virgin Islands", "Bermuda",
    "Isle of Man", "Liechtenstein", "Seychelles", "Mauritius",
]
NORMAL_COUNTRIES = [
    "United States", "Canada", "United Kingdom", "Germany",
    "France", "Japan", "Australia", "Singapore",
]
FIRST_NAMES = [
    "James", "Maria", "Robert", "Jennifer", "David", "Sarah", "Michael",
    "Linda", "William", "Patricia", "Richard", "Elizabeth", "Carlos",
    "Yuki", "Ahmed", "Wei", "Olga", "Raj", "Fatima", "Hans",
    "Elena", "Boris", "Lucia", "Dmitri", "Aisha", "Chen",
]
LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia",
    "Miller", "Davis", "Rodriguez", "Martinez", "Chen", "Wang",
    "Kim", "Nakamura", "Mueller", "Petrov", "Al-Rashid", "Patel",
    "Kowalski", "Andersson", "Romero", "Tanaka", "Fischer", "Ivanov",
]
COMPANY_NAMES = [
    "Meridian Trading Co", "Apex Global Ventures", "Silverstream Holdings",
    "Pacific Rim Exports", "Atlas Infrastructure Group", "Crescent Bay LLC",
    "Zenith Capital Partners", "Irongate Properties", "Coral Reef Imports",
    "Summit Ridge Consulting", "Blue Horizon Logistics", "Phoenix Rising Corp",
    "Golden Gate Enterprises", "Obsidian Group Ltd", "Emerald Isle Trading",
    "Titan Resources Inc", "Sapphire Coast Pty", "Nordic Star Holdings",
    "Red Rock Ventures", "Crystal Clear Services", "Pinnacle Investments",
    "Shadow Creek LLC", "Bright Future Foundation", "Oasis Development Co",
]
SHELL_COMPANY_NAMES = [
    "Vanguard Offshore Holdings Ltd", "Neptune Ventures BVI",
    "Cascade International Trust", "Horizon Asset Management Cayman",
    "Stellar Global Trading Seychelles", "Pinnacle Fiduciary Services",
]

def generate_customer_profiles(rng: random.Random, count: int = 25) -> Dict[str, Dict[str, Any]]:
    """Generate deterministic customer profiles.
    Creates a mix of individual and corporate accounts with varying risk levels.
    Some customers are legitimate, others are designed as suspicious for AML detection.
    Args:
        rng: Seeded Random instance.
        count: Number of customer profiles to generate.
    Returns:
        Dict mapping account_id to customer profile.
    """

    profiles = {}
    for i in range(count):
        account_id = f"ACC-{i + 1:04d}"
        is_corporate = rng.random() < 0.35
        is_suspicious = i < 8
        if is_corporate:
            if is_suspicious and rng.random() < 0.5:
                name = rng.choice(SHELL_COMPANY_NAMES)
                country = rng.choice(HIGH_RISK_COUNTRIES)
                business_type = rng.choice(["import_export", "consulting", "money_service_business"])
                risk_level = "high"
            else:
                name = rng.choice(COMPANY_NAMES)
                country = rng.choice(NORMAL_COUNTRIES)
                business_type = rng.choice(BUSINESS_TYPES)
                risk_level = rng.choice(["low", "low", "medium"])
            account_type = "corporate"
            kyc_status = rng.choice(["verified", "verified", "pending_review"]) if is_suspicious else "verified"
        else:
            first = rng.choice(FIRST_NAMES)
            last = rng.choice(LAST_NAMES)
            name = f"{first} {last}"
            country = rng.choice(HIGH_RISK_COUNTRIES) if (is_suspicious and rng.random() < 0.3) else rng.choice(NORMAL_COUNTRIES)
            business_type = None
            account_type = "individual"
            risk_level = "high" if is_suspicious else rng.choice(["low", "low", "low", "medium"])
            kyc_status = "verified"
        opened_days_ago = rng.randint(30, 3650)
        if is_suspicious and rng.random() < 0.4:
            opened_days_ago = rng.randint(10, 90)
        profiles[account_id] = {
            "account_id": account_id,
            "name": name,
            "account_type": account_type,
            "country": country,
            "business_type": business_type,
            "risk_level": risk_level,
            "kyc_status": kyc_status,
            "account_opened_days_ago": opened_days_ago,
            "is_pep": is_suspicious and rng.random() < 0.15,
            "previous_sars": rng.randint(0, 2) if is_suspicious else 0,
            "expected_monthly_volume": _expected_volume(rng, account_type, business_type, is_suspicious),
            "is_suspicious_ground_truth": is_suspicious,
        }
    return profiles

def _expected_volume(rng: random.Random, account_type: str, business_type: str | None, suspicious: bool) -> Dict[str, Any]:
    """Generate expected monthly transaction volume for a customer."""

    if account_type == "corporate":
        if business_type in ("money_service_business", "casino"):
            base = rng.randint(100000, 500000)
        elif business_type in ("import_export", "real_estate"):
            base = rng.randint(50000, 200000)
        else:
            base = rng.randint(10000, 80000)
    else:
        base = rng.randint(2000, 15000)
    return {
        "expected_monthly_credits": base,
        "expected_monthly_debits": int(base * rng.uniform(0.7, 1.1)),
        "expected_transaction_count": rng.randint(5, 50),
        "currency": "USD",
    }
