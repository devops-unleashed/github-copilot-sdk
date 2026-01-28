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
    try:
        session = await client.create_session({
            "agent_mode": True,
            "tools": [email_tool] # Add custom tool; MCP tools are built-in
        })
        print("Session created successfully.")
    except Exception as e:
        print(f"Error creating session: {e}", flush=True)
        raise

    # Event handlers
    def on_event(event):
        # Log all events for debugging
        event_type = event.type.value if hasattr(event.type, 'value') else str(event.type)
        print(f"\n[EVENT: {event_type}]", flush=True)
        
        if event_type == "assistant.message_delta":
            print(event.data.content, end='', flush=True)
        elif "error" in event_type.lower():
            print(f"[ERROR EVENT: {event_type}]", flush=True)
            if hasattr(event, 'data'):
                print(f"  Error details: {event.data}", flush=True)
        elif "tool" in event_type.lower():
            # Try to detect tool-related events
            print(f"[TOOL EVENT DETECTED: {event_type}]", flush=True)
            if hasattr(event, 'data'):
                if hasattr(event.data, 'tool_name'):
                    print(f"  Tool: {event.data.tool_name}", flush=True)
                if hasattr(event.data, 'arguments'):
                    print(f"  Arguments: {event.data.arguments}", flush=True)
                print(f"  Event data: {event.data}", flush=True)
        elif event_type not in ["pending_messages.modified"]:
            # Log other event types (skip the noisy pending_messages ones)
            print(f"  Event type: {event_type}", flush=True)
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
    
    # Send the prompt (returns turn ID immediately)
    print("Sending prompt...")
    turn_id = await session.send({"prompt": prompt})
    print(f"Prompt sent. Turn ID: {turn_id}")
    
    # Give the agent time to process and respond
    print("Waiting for agent to process (30 seconds)...")
    received_content = False
    completed = False
    
    def track_events(e):
        nonlocal received_content, completed
        event_type = e.type.value if hasattr(e.type, 'value') else str(e.type)
        
        if event_type == "assistant.message_delta":
            received_content = True
        
        if event_type in ["session.idle", "turn.done", "assistant.message.done"]:
            print(f"\n[COMPLETION EVENT: {event_type}]", flush=True)
            completed = True
    
    session.on(track_events)
    
    # Just wait for a fixed time period
    await asyncio.sleep(30)
    
    if completed:
        print("\nAgent processing completed successfully.")
    elif received_content:
        print("\nAgent sent content but no completion event received.")
    else:
        print("\n[WARNING] No response from agent within 30 seconds.")
        print("[INFO] Agent mode may not be functional in GitHub Actions CI environment.")
        print("[INFO] Consider running this script locally or using a different approach.")

    print("Destroying session...")
    await session.destroy()
    print("Stopping client...")
    await client.stop()
    print("Script finished successfully.")

asyncio.run(main())
