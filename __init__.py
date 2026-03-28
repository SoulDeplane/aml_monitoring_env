"""
AML Transaction Monitoring Environment for OpenEnv.

A real-world environment where an AI agent monitors financial transactions
to detect money laundering patterns including structuring, layering,
round-tripping, and suspicious network activity.

MCP Tools available:
- review_transactions: Get transaction history for an account
- check_customer_profile: Review KYC/customer info and risk profile
- analyze_pattern: Check for specific suspicious patterns
- get_network: Map transaction relationships between accounts
- flag_suspicious: Flag an account as suspicious with evidence
- file_sar: File a Suspicious Activity Report
- clear_alert: Dismiss an alert as legitimate
"""

from openenv.core.env_server.mcp_types import CallToolAction, ListToolsAction

from .client import AMLMonitoringEnv

__all__ = ["AMLMonitoringEnv", "CallToolAction", "ListToolsAction"]
