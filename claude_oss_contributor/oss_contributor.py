"""
OSS contributor loop: Claude + Composio (GitHub + web search).

Run (from repo root or this directory):
  python -m claude_agent.oss_contributor
  python claude_agent/oss_contributor.py

Requires the same .env as agent.py: COMPOSIO_API_KEY, COMPOSIO_USER_ID (or USER_ID),
ANTHROPIC_API_KEY. GitHub must be connected in Composio (`composio add github`).

Optional: OSS_COMPOSIO_TOOLKITS — comma-separated toolkit slugs (default:
github, composio_search). Do not add remote_retrieval for OSS work: that toolkit is for
IT equipment return logistics only (see https://docs.composio.dev/toolkits/remote_retrieval).
"""

from __future__ import annotations

import asyncio
import os
from pathlib import Path

from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions
from composio import Composio
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

# GitHub: PRs, issues, files. composio_search: discover repos/issues on the web.
DEFAULT_TOOLKITS = ["github", "composio_search"]


def _toolkits() -> list[str]:
    raw = os.getenv("OSS_COMPOSIO_TOOLKITS")
    if raw:
        return [t.strip() for t in raw.split(",") if t.strip()]
    return list(DEFAULT_TOOLKITS)


OSS_SYSTEM_PROMPT = """You are an expert open-source contributor using Composio tools.

Your mission when the user asks:
1) Discovery — Use web/search tools (e.g. composio search) to find a suitable issue in a \
smaller or lesser-known repo: open "good first issue" / help-wanted items, or small bugs. \
Prefer issues that are scoped and documented.
2) Repo rules — Before writing code, use GitHub tools to read CONTRIBUTING.md, CODE_OF_CONDUCT.md, \
.github/PULL_REQUEST_TEMPLATE*, issue/PR templates, and any style guide. Follow them exactly.
3) Implementation — Match existing project patterns (structure, naming, tests, error handling). \
Keep the change minimal and reviewable. Run tests or linters via available tools when possible.
4) Pull request — Open a PR that: references the issue, uses the project's title/body conventions, \
and explains what changed and how you tested it. If the project requires DCO, sign-off, or \
AI-disclosure, comply.
5) Quality bar — Do not add generic boilerplate, obvious AI filler comments, or unrelated refactors. \
Write code that looks like it belongs in that codebase.

If the user only wants to chat or plan, help without making unsolicited destructive changes.

Stay within tool capabilities; if something is not possible via tools, say so clearly."""


async def chat_with_oss_stack() -> None:
    api_key = os.getenv("COMPOSIO_API_KEY")
    if not api_key:
        raise RuntimeError("COMPOSIO_API_KEY is not set")

    composio = Composio(api_key=api_key)

    user_id = os.getenv("COMPOSIO_USER_ID") or os.getenv("USER_ID")
    if not user_id:
        raise RuntimeError(
            "Set COMPOSIO_USER_ID (or USER_ID) in the environment or .env — Composio needs a stable user id string."
        )

    kits = _toolkits()
    mcp_server = composio.create(
        user_id=user_id,
        toolkits=kits,
    )

    url = mcp_server.mcp.url
    if not url:
        raise ValueError("Session URL not found")

    options = ClaudeAgentOptions(
        permission_mode="bypassPermissions",
        mcp_servers={
            "composio": {
                "type": "http",
                "url": url,
                "headers": {
                    "x-api-key": os.getenv("COMPOSIO_API_KEY", ""),
                },
            }
        },
        system_prompt=OSS_SYSTEM_PROMPT,
        max_turns=int(os.getenv("OSS_MAX_TURNS", "40")),
    )

    print(
        "\nOSS contributor mode (Claude + Composio). "
        f"Toolkits: {', '.join(kits)}\n"
        "Describe a goal (e.g. find a small issue and prep a PR), or type 'exit' / 'quit'.\n"
    )

    async with ClaudeSDKClient(options=options) as client:
        while True:
            user_input = input("You: ").strip()
            if user_input.lower() in {"exit", "quit"}:
                print("Goodbye!")
                break

            await client.query(user_input)

            print("Claude: ", end="", flush=True)
            async for message in client.receive_response():
                if hasattr(message, "content"):
                    for block in message.content:
                        if hasattr(block, "text"):
                            print(block.text, end="", flush=True)
            print()


def main() -> None:
    asyncio.run(chat_with_oss_stack())


if __name__ == "__main__":
    main()
