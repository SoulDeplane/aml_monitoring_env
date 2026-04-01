"""Tests for deterministic data generation in the AML monitoring environment."""

import random
from aml_monitoring_env.data.customers import generate_customer_profiles
from aml_monitoring_env.data.transactions import generate_transactions
from aml_monitoring_env.data.scenarios import generate_scenario

def test_customer_generation_determinism():
    """Verify that using the same seed produces identical customer profiles."""
    rng1 = random.Random(42)
    profiles_1 = generate_customer_profiles(rng1, count=10)
    
    rng2 = random.Random(42)
    profiles_2 = generate_customer_profiles(rng2, count=10)
    
    assert profiles_1 == profiles_2
    assert len(profiles_1) == 10
    
    suspicious_count = sum(1 for p in profiles_1.values() if p["is_suspicious_ground_truth"])
    assert suspicious_count > 0

def test_transaction_generation_determinism():
    """Verify that transaction generation is deterministic and creates expected volume."""
    rng = random.Random(42)
    profiles = generate_customer_profiles(rng, count=5)
    
    rng1 = random.Random(99)
    txns_1 = generate_transactions(rng1, profiles, days=30)
    
    rng2 = random.Random(99)
    txns_2 = generate_transactions(rng2, profiles, days=30)
    
    assert txns_1 == txns_2
    assert len(txns_1) == 5
    
    for account_id, txn_list in txns_1.items():
        assert isinstance(txn_list, list)
        if len(txn_list) > 0:
            assert "amount" in txn_list[0]
            assert "transaction_id" in txn_list[0]

def test_scenario_generation():
    """Verify that full scenarios are generated correctly across difficulties."""
    easy = generate_scenario("easy", seed=42)
    assert easy["scenario_id"].startswith("AML-EASY")
    assert len(easy["alerts"]) == 3
    
    medium = generate_scenario("medium", seed=42)
    assert medium["scenario_id"].startswith("AML-MED")
    assert len(medium["alerts"]) == 5
    
    hard = generate_scenario("hard", seed=42)
    assert hard["scenario_id"].startswith("AML-HARD")
    assert len(hard["alerts"]) == 8
    assert "network" in hard
