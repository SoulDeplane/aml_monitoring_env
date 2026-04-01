"""Integration tests verifying environment tool dispatch and states."""

from aml_monitoring_env.server.environment import AMLMonitoringEnvironment
from openenv.core.env_server.mcp_types import CallToolAction, ListToolsAction

def test_environment_reset_and_initial_state():
    """Verify resetting the environment provides a fresh valid state."""
    env = AMLMonitoringEnvironment()
    obs = env.reset(seed=42, task_id="easy")
    
    assert not obs.done
    assert "alerts" in obs.metadata
    assert "review_accounts" in obs.metadata
    assert len(obs.metadata["review_accounts"]) == 3
    assert env.state.step_count == 0

def test_environment_tool_dispatch():
    """Verify that calling an MCP tool correctly updates the environment state."""
    env = AMLMonitoringEnvironment()
    obs = env.reset(seed=42)
    acc_id = obs.metadata["review_accounts"][0]
    
    action = CallToolAction(
        tool_name="check_customer_profile",
        arguments={"account_id": acc_id}
    )
    
    obs2 = env.step(action)
    assert env.state.step_count == 1
    assert hasattr(obs2, "result")

def test_environment_completion_check():
    """Verify that the episode finishes when all accounts are cleared or flagged."""
    env = AMLMonitoringEnvironment()
    obs = env.reset(seed=42)
    accounts = obs.metadata["review_accounts"]
    
    final_obs = None
    for acc in accounts:
        act = CallToolAction(
            tool_name="clear_alert",
            arguments={"account_id": acc, "justification": "test"}
        )
        final_obs = env.step(act)
        
    assert env._done is True
