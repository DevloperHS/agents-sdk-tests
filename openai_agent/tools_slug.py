from composio import Composio
from dotenv import load_dotenv
import os

load_dotenv()

api_key = os.getenv("COMPOSIO_API_KEY")
user_id = os.getenv("COMPOSIO_USER_ID")

composio = Composio(api_key=api_key)

tools = composio.tools.get("user_123", toolkits=["GITHUB", "exa", "googlesheets", "browser_tool" ])

print(tools)