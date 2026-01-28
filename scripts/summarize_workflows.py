import asyncio
import json
import sys
from pathlib import Path

# Add parent directory to path to import tools module
sys.path.insert(0, str(Path(__file__).parent.parent))

from copilot import CopilotClient
from tools.send_email import email_tool

# Repo list
REPOS = [
    "devops-unleashed/workflow-example-powershell"
]

async def main():
    client = CopilotClient()
    await client.start()

    # Create session with agent mode and custom tools (MCP tools auto-discovered)
    session = await client.create_session({
        "model": "gpt-5", # Or your available model
        "agent_mode": True,
        "tools": [email_tool] # Add custom tool; MCP tools are built-in
    })

    # Event handlers
    def on_event(event):
        if event.type.value == "assistant.message_delta":
            print(event.data.content, end='', flush=True)

    session.on(on_event)

    # Agent prompt for multi-repo query and actions
    prompt = f"""
    Monitor these repositories: {', '.join(REPOS)}.
    For each repo:
    1. Use MCP tools to list workflows.
    2. For each workflow, list workflow runs from the last 24 hours with status 'failure'.
    3. For each failed run, get run details, find the previous successful run (by listing runs and filtering), and list commits between the successful run's head_sha and the failed run's head_sha.
    4. Extract unique committer emails from those commits (use author.email if available, skip noreply).
    5. If there are committers, use the send_email tool to notify them with subject 'Workflow Failure in {repo}' and body including run ID, repo, and failure summary (from logs if needed).
    Only email if failures found. Summarize actions taken.
    """
    await session.send({"prompt": prompt})

    # Wait for completion
    done = asyncio.Event()
    session.on(lambda e: done.set() if e.type.value == "session.idle" else None)
    await done.wait()

    await session.destroy()
    await client.stop()

asyncio.run(main())
