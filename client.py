"""Client for connecting to a remote AML Monitoring environment."""

from openenv.core.mcp_client import MCPToolClient


class AMLMonitoringEnv(MCPToolClient):
    """Client for connecting to a remote AML Monitoring environment.
    Example (async):
        >>> async with AMLMonitoringEnv(base_url="http://localhost:8000") as env:
        ...     result = await env.reset()
        ...     tools = await env.list_tools()
        ...     result = await env.call_tool("review_transactions", account_id="ACC-001")
    Example (sync):
        >>> with AMLMonitoringEnv(base_url="http://localhost:8000").sync() as env:
        ...     result = env.reset()
        ...     tools = env.list_tools()
    """

    pass
