import asyncio
import datetime
import os
from dotenv import load_dotenv

from composio import Composio
from composio_openai_agents import OpenAIAgentsProvider
from agents import Agent, Runner, HostedMCPTool, SQLiteSession

load_dotenv()


def session_time_context() -> str:
    """Local wall-clock for time-of-day greeting (morning / afternoon / evening / night)."""
    now = datetime.datetime.now()
    h = now.hour
    if 5 <= h < 12:
        period = "morning"
    elif 12 <= h < 18:
        period = "afternoon"
    elif 18 <= h < 22:
        period = "evening"
    else:
        period = "night"
    return (
        f"Local datetime: {now.isoformat(timespec='minutes')}\n"
        f"Time period: {period} (use for a short, friendly greeting only)"
    )


api_key = os.getenv("COMPOSIO_API_KEY")
user_id = os.getenv("COMPOSIO_USER_ID")

if not api_key:
    raise RuntimeError("COMPOSIO_API_KEY is not set. Create a .env file with COMPOSIO_API_KEY=your_key")

# Initialize Composio
composio = Composio(api_key=api_key, provider=OpenAIAgentsProvider())

# Create Tool Router session (connection tools + wait so OAuth can finish before continuing)
session = composio.create(
    user_id=user_id,
    toolkits=["GITHUB", "exa", "googlesheets", "browser_tool" ],
    manage_connections={"enable": True, "wait_for_connections": True},
)
mcp_url = session.mcp.url

# Configure agent with MCP tool
agent = Agent(
    name="Assistant",
    model="gpt-5",
    instructions=(
        "You are a Job Search Agent powered by Composio Tool Router (MCP). You deliver a guided "
        "experience: greet, onboard with one question at a time, then run the job search workflow. "
        "Use only tools exposed in this MCP session.\n\n"
        "Phases (follow in order):\n"
        "1) ONBOARDING — You are not in full search mode yet. Track which step you are on (1–5). "
        "Each assistant turn asks at most ONE numbered onboarding question; wait for the user's reply "
        "before advancing. After step 5, briefly summarize their answers and ask if they are ready "
        "to start searching; only after they confirm, move to phase 2.\n"
        "2) SEARCH & EXECUTE — Run the job search process: discover roles, score vs profile, use Sheets, "
        "assist with applications via browser as already defined below.\n\n"
        "Onboarding questions (ask strictly one per turn, in this order):\n"
        "Q1: What role titles or job family are you targeting?\n"
        "Q2: What are your must-have skills or tech stack?\n"
        "Q3: Preferred location, timezone, or remote-only?\n"
        "Q4: Seniority (years or level) you are aiming for?\n"
        "Q5: Any constraints — salary expectations, visa/sponsorship needs, industries or companies to avoid? "
        "(User may say 'none' or 'N/A'.)\n\n"
        "Search & application behavior (phase 2 only, unless fixing connections):\n"
        "- Build a concise job profile from onboarding answers.\n"
        "- Use Exa tools to discover and evaluate postings: prefer structured discovery (research, "
        "answer with citations, or webset-style search) when you need current listings. Use explicit, "
        "time-bounded queries when freshness matters.\n"
        "- Use Google Sheets tools to maintain a shortlist: company, title, link, matched skills, "
        "rationale, optional score. Ask for spreadsheet id/name or tab if missing before writing.\n"
        "- Use the browser toolkit for application steps: clear step-by-step tasks, watch progress, "
        "share liveUrl when available. Prefer drafts over submit unless the user explicitly asks to submit.\n"
        "- Use GitHub tools only when the user ties it to job search.\n\n"
        "Connections (Composio — do not abandon the session):\n"
        "- If a toolkit needs authentication and a tool returns an error about missing, invalid, or "
        "expired connection, use any connection-management or OAuth/initiation tools this session "
        "provides (e.g. authorize, link, connect, or wait-for-connection helpers). Give the user "
        "clear, actionable steps: any redirect URL, link to open Composio dashboard, or auth "
        "instructions returned by tools.\n"
        "- After prompting the user to connect, wait for completion (this session may wait for "
        "connections); then retry the failed action or continue the flow. If something still fails, "
        "explain calmly, suggest checking Composio connected accounts for that toolkit, and retry "
        "or use another tool path — never end the chat abruptly.\n"
        "- Proactively initiate connection for a toolkit before first use if the session exposes a "
        "way to check or pre-authorize required toolkits (e.g. Google Sheets) once onboarding is done "
        "and before heavy search, so phase 2 does not stall.\n\n"
        "Operating rules:\n"
        "- Prefer tools over guessing URLs or postings; preserve links from tool results.\n"
        "- Summarize what you did, sheet updates, and next steps.\n"
        "- On tool failure or empty results: fix connections first if auth-related; otherwise narrow "
        "queries or ask one clarifying question.\n"
        "- Stay professional; never invent credentials or applications."
    ),
    tools=[
        HostedMCPTool(
            tool_config={
                "type": "mcp",
                "server_label": "tool_router",
                "server_url": mcp_url,
                "headers": {"x-api-key": api_key},
                "require_approval": "never",
            }
        )
    ],
)

print("\nComposio Tool Router session created.")

chat_session = SQLiteSession("conversation_openai_toolrouter")

print("\nChat started. Type your requests below.")
print("Commands: 'exit', 'quit', or 'q' to end\n")

async def main():
    opener = (
        f"{session_time_context()}\n\n"
        "Begin the session. Greet the user warmly for the time of day (use the time period above). "
        "In one short sentence, say you will ask a few quick questions one at a time before searching. "
        "Then ask ONLY onboarding Q1 from your instructions — nothing else in that message. "
        "Do not start the job search or call Exa/Sheets/browser search tools yet, except connection "
        "tools if you must prepare auth for later."
    )
    try:
        result = await Runner.run(agent, opener, session=chat_session)
        print(f"Assistant: {result.final_output}\n")
    except Exception as e:
        print(f"Error: {e}\n")

    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in {"exit", "quit", "q"}:
            print("Goodbye!")
            break

        try:
            result = await Runner.run(agent, user_input, session=chat_session)
            print(f"Assistant: {result.final_output}\n")
        except Exception as e:
            print(f"[Something went wrong — you can keep chatting. Details: {e}]\n")

asyncio.run(main())


# data generated : https://docs.google.com/spreadsheets/d/1x0EeC9TflAHBaVfIESSKAQ_qSOjimElD_Ln79VWPhh4/edit?gid=0#gid=0