# default agent

import asyncio
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions
import os
from composio import Composio
from dotenv import load_dotenv

load_dotenv()

async def chat_with_remote_mcp():
    api_key = os.getenv("COMPOSIO_API_KEY")
    if not api_key:
        raise RuntimeError("COMPOSIO_API_KEY is not set")

    composio = Composio(api_key=api_key)

    user_id = os.getenv("COMPOSIO_USER_ID") or os.getenv("USER_ID")
    if not user_id:
        raise RuntimeError(
            "Set COMPOSIO_USER_ID (or USER_ID) in the environment or .env — Composio needs a stable user id string."
        )

    # Create Tool Router session for Remote retrieval
    mcp_server = composio.create(
        user_id=user_id,
        toolkits=["github"],
    )

    url = mcp_server.mcp.url

    if not url:
        raise ValueError("Session URL not found")

    # Configure remote MCP server for Claude
    options = ClaudeAgentOptions(
        permission_mode="bypassPermissions",
        mcp_servers={
            "composio": {
                "type": "http",
                "url": url,
                "headers": {
                    "x-api-key": os.getenv("COMPOSIO_API_KEY")
                }
            }
        },
        system_prompt="You are a helpful assistant with access to Remote retrieval and Gmail tools via Composio.",
        max_turns=10
    )

    # Create client with context manager
    async with ClaudeSDKClient(options=options) as client:
        print("\nChat started. Type 'exit' or 'quit' to end.\n")

        # Main chat loop
        while True:
            user_input = input("You: ").strip()
            if user_input.lower() in {"exit", "quit"}:
                print("Goodbye!")
                break

            # Send query
            await client.query(user_input)

            # Receive and print response
            print("Claude: ", end="", flush=True)
            async for message in client.receive_response():
                if hasattr(message, "content"):
                    for block in message.content:
                        if hasattr(block, "text"):
                            print(block.text, end="", flush=True)
            print()

if __name__ == "__main__":
    asyncio.run(chat_with_remote_mcp())