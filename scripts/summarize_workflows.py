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
                # Capture tool results
                if hasattr(event.data, 'result'):
                    print(f"  Result: {event.data.result}", flush=True)
                if hasattr(event.data, 'output'):
                    print(f"  Output: {event.data.output}", flush=True)
                # Show full content for tool completions
                if event_type == "tool.execution_complete" and hasattr(event.data, 'content'):
                    print(f"  Content: {event.data.content}", flush=True)
        elif event_type not in ["pending_messages.modified"]:
            # Log other event types (skip the noisy pending_messages ones)
            print(f"  Event type: {event_type}", flush=True)
            if hasattr(event, 'data') and hasattr(event.data, 'content') and event.data.content:
                # Show content for message events
                print(f"  Content: {event.data.content[:200]}...", flush=True)

    session.on(on_event)

    # Agent prompt for multi-repo query and actions
    print(f"\nSending prompt to monitor {len(REPOS)} repositories...")
    prompt = f"""
    Monitor these repositories: {', '.join(REPOS)}.
    
    IMPORTANT: At the end, ALWAYS call the send_email tool with a test message, even if there are no failures.
    
    Tasks:
    1. Use MCP tools to list workflows.
    2. For each workflow, list workflow runs from the last 24 hours with status 'failure'.
    3. For each failed run, get run details, find the previous successful run (by listing runs and filtering), and list commits between the successful run's head_sha and the failed run's head_sha.
    4. Extract unique committer emails from those commits (use author.email if available, skip noreply).
    5. Call the send_email tool to notify:
       - If there are failures: notify committers with subject 'Workflow Failure in {{repo}}' and body including run ID, repo, and failure summary
       - If NO failures found: call send_email with recipients=['test@example.com'], subject='Workflow Monitor Test - No Failures', body='Test run completed. No workflow failures found in the last 24 hours.'
    
    You MUST call send_email in either case. Summarize actions taken.
    """
    
    # Send the prompt (returns turn ID immediately)
    print("Sending prompt...")
    turn_id = await session.send({"prompt": prompt})
    print(f"Prompt sent. Turn ID: {turn_id}")
    
    # Give the agent time to process and respond (increased for complex multi-step tasks)
    print("Waiting for agent to complete (up to 3 minutes)...")
    received_content = False
    completed = False
    send_email_called = False
    
    def track_events(e):
        nonlocal received_content, completed, send_email_called
        event_type = e.type.value if hasattr(e.type, 'value') else str(e.type)
        
        if event_type == "assistant.message_delta":
            received_content = True
        
        # Detect if send_email tool was called
        if event_type == "tool.execution_start" and hasattr(e, 'data'):
            if hasattr(e.data, 'tool_name') and e.data.tool_name == "send_email":
                send_email_called = True
                print(f"\n[✓] send_email tool called!", flush=True)
        
        # Look for final completion after all turns
        if event_type in ["session.idle", "turn.done", "assistant.message.done"]:
            print(f"\n[Potential completion event: {event_type}]", flush=True)
            completed = True
    
    session.on(track_events)
    
    # Wait longer for multi-step agent tasks (3 minutes)
    await asyncio.sleep(180)
    
    print(f"\n{'='*60}")
    if send_email_called:
        print("✓ SUCCESS: send_email tool was called by the agent")
    elif completed:
        print("Agent processing completed but send_email was not called.")
        print("This may mean no failures were found or no valid committer emails.")
    elif received_content:
        print("Agent sent content but processing may still be ongoing.")
    else:
        print("No response from agent - this should not happen now that auth is working.")
    print(f"{'='*60}")

    print("Destroying session...")
    await session.destroy()
    print("Stopping client...")
    await client.stop()
    print("Script finished successfully.")

asyncio.run(main())
