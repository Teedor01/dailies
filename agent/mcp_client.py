from google.adk.tools.mcp_tool.mcp_toolset import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp.client.stdio import StdioServerParameters

from config import CLICKHOUSE_HOST, CLICKHOUSE_USER, CLICKHOUSE_PASSWORD, require_clickhouse


def get_clickhouse_mcp_toolset() -> McpToolset:
    require_clickhouse()

    server_env = {
        "CLICKHOUSE_HOST": CLICKHOUSE_HOST,
        "CLICKHOUSE_USER": CLICKHOUSE_USER,
        "CLICKHOUSE_PASSWORD": CLICKHOUSE_PASSWORD,
        "CLICKHOUSE_ENABLED": "true",
        "CHDB_ENABLED": "false",
        "CLICKHOUSE_MCP_SERVER_TRANSPORT": "stdio",
    }

    return McpToolset(
        connection_params=StdioConnectionParams(
            server_params=StdioServerParameters(
                command="python3",
                args=["-m", "mcp_clickhouse.main"],
                env=server_env,
            ),
            timeout=60.0,
        ),
       
        tool_filter=["list_databases", "list_tables", "run_query"],
    )
