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
    print("Initializing Copilot client...")
    client = CopilotClient()
    
    print("Starting Copilot client...")
    await client.start()
    print("Copilot client started successfully.")

    # Create session with agent mode and custom tools (MCP tools auto-discovered)
    print("Creating session with agent mode...")
    session = await client.create_session({
        "model": "gpt-5", # Or your available model
        "agent_mode": True,
        "tools": [email_tool] # Add custom tool; MCP tools are built-in
    })
    print("Session created successfully.")

    # Event handlers
    def on_event(event):
        # Log all events for debugging
        event_type = event.type.value if hasattr(event.type, 'value') else str(event.type)
        print(f"\n[EVENT: {event_type}]", flush=True)
        
        if event_type == "assistant.message_delta":
            print(event.data.content, end='', flush=True)
        elif "tool" in event_type.lower():
            # Try to detect tool-related events
            print(f"[TOOL EVENT DETECTED: {event_type}]", flush=True)
            if hasattr(event, 'data'):
                if hasattr(event.data, 'tool_name'):
                    print(f"  Tool: {event.data.tool_name}", flush=True)
                if hasattr(event.data, 'arguments'):
                    print(f"  Arguments: {event.data.arguments}", flush=True)
                # Print all data attributes for debugging
                print(f"  Event data: {event.data}", flush=True)
        else:
            # Log other event types with their data for debugging
            if hasattr(event, 'data'):
                print(f"  Data: {event.data}", flush=True)

    session.on(on_event)

    # Agent prompt for multi-repo query and actions
    print(f"\nSending prompt to monitor {len(REPOS)} repositories...")
    prompt = f"""
    Monitor these repositories: {', '.join(REPOS)}.
    For each repo:
    1. Use MCP tools to list workflows.
    2. For each workflow, list workflow runs from the last 24 hours with status 'failure'.
    3. For each failed run, get run details, find the previous successful run (by listing runs and filtering), and list commits between the successful run's head_sha and the failed run's head_sha.
    4. Extract unique committer emails from those commits (use author.email if available, skip noreply).
    5. If there are committers, use the send_email tool to notify them with subject 'Workflow Failure in {{repo}}' and body including run ID, repo, and failure summary (from logs if needed).
    Only email if failures found. Summarize actions taken.
    """
    
    try:
        # Send with timeout to prevent hanging in CI
        print("Sending prompt with 3-minute timeout...")
        response = await asyncio.wait_for(
            session.send({"prompt": prompt}),
            timeout=180
        )
        print("\nAgent response received successfully.")
        if response:
            print(f"Response: {response}")
    except asyncio.TimeoutError:
        print("\n[TIMEOUT] Agent did not respond within 3 minutes.", flush=True)
    except Exception as e:
        print(f"\n[ERROR] Agent execution failed: {e}", flush=True)

    print("Destroying session...")
    await session.destroy()
    print("Stopping client...")
    await client.stop()
    print("Script finished successfully.")

asyncio.run(main())
