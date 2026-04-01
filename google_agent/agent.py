

import os
import warnings
from pathlib import Path

from composio import Composio
from composio_google import GoogleProvider
from dotenv import load_dotenv
from google.adk.agents.llm_agent import Agent
from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPConnectionParams
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset

load_dotenv()
warnings.filterwarnings("ignore", message=".*BaseAuthenticatedTool.*")

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
COMPOSIO_API_KEY = os.getenv("COMPOSIO_API_KEY")
COMPOSIO_USER_ID = os.getenv("COMPOSIO_USER_ID")

if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY is not set in the environment.")
if not COMPOSIO_API_KEY:
    raise ValueError("COMPOSIO_API_KEY is not set in the environment.")
if not COMPOSIO_USER_ID:
    raise ValueError("COMPOSIO_USER_ID is not set in the environment.")

composio_client = Composio(
    api_key=COMPOSIO_API_KEY,
    provider=GoogleProvider(),
    timeout=120,
    max_retries=5,
)

composio_session = composio_client.create(
    user_id=COMPOSIO_USER_ID,
    toolkits=["gmail"],
)

COMPOSIO_MCP_URL = composio_session.mcp.url


composio_toolset = McpToolset(
    connection_params=StreamableHTTPConnectionParams(
        url=COMPOSIO_MCP_URL,
        headers={"x-api-key": COMPOSIO_API_KEY},
        timeout=30.0,
        sse_read_timeout=600.0,
    )
)

root_agent = Agent(
    model="gemini-2.5-flash", # change model for accuracy
    name="composio_agent",
    description="An agent that uses Composio tools to perform actions.",
    instruction=(
        "You are a helpful assistant connected to Composio. "
        "You have the following tools available: "
        "COMPOSIO_SEARCH_TOOLS, COMPOSIO_MULTI_EXECUTE_TOOL, "
        "COMPOSIO_MANAGE_CONNECTIONS, COMPOSIO_REMOTE_BASH_TOOL, COMPOSIO_REMOTE_WORKBENCH. "
        "Use these tools to help users with Remote retrieval operations."
    ),  
    tools=[composio_toolset],
)

print("\nAgent setup complete. You can now run this agent directly ;)")