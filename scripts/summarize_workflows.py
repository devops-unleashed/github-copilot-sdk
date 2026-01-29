import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from copilot import CopilotClient
from tools.send_email import email_tool

# Repositories to monitor
REPOS = ["devops-unleashed/workflow-example-powershell"]


async def main():
    # Initialize client
    print("Initializing Copilot client...")
    client = CopilotClient()
    await client.start()
    print("Copilot client started.")

    # Create session with agent mode and custom tool
    session = await client.create_session({"agent_mode": True, "tools": [email_tool]})
    print("Session created.")

    # Event handler
    def on_event(event):
        event_type = event.type.value if hasattr(event.type, 'value') else str(event.type)
        
        if event_type == "assistant.message_delta":
            print(event.data.content, end='', flush=True)
        elif "error" in event_type.lower():
            print(f"\n[ERROR: {event_type}]", flush=True)
        elif event_type == "tool.execution_start" and hasattr(event.data, 'tool_name'):
            print(f"\n[Tool: {event.data.tool_name}]", flush=True)
        elif event_type == "tool.execution_complete":
            status = "✓" if getattr(event.data, 'success', None) else "✗"
            print(f"[Tool complete: {status}]", flush=True)

    session.on(on_event)

    # Send agent prompt
    print(f"\nMonitoring {len(REPOS)} repositories...")
    prompt = f"""
    Monitor these repositories: {', '.join(REPOS)}.
    
    IMPORTANT: At the end, ALWAYS call the send_email tool with a test message, even if there are no failures.
    
    Tasks:
    1. Use MCP tools to list workflows.
    2. For each workflow, list workflow runs from the last 24 hours with status 'failure'.
    3. For each failed run, get run details, find the previous successful run (by listing runs and filtering), and list commits between the successful run's head_sha and the failed run's head_sha.
    4. Extract unique committer emails from those commits (use author.email if available, skip noreply).
    5. Call the send_email tool to notify:
       - If there are failures: notify committers with subject 'Workflow Failure in {{{{repo}}}}' and body including run ID, repo, and failure summary
       - If NO failures found: call send_email with recipients=['test@example.com'], subject='Workflow Monitor Test - No Failures', body='Test run completed. No workflow failures found in the last 24 hours.'
    
    You MUST call send_email in either case. Summarize actions taken.
    """
    
    turn_id = await session.send({"prompt": prompt})
    print(f"Prompt sent. Turn ID: {turn_id}")
    
    # Track completion
    send_email_called = False
    
    def track_events(e):
        nonlocal send_email_called
        event_type = e.type.value if hasattr(e.type, 'value') else str(e.type)
        if event_type == "tool.execution_start" and hasattr(e.data, 'tool_name'):
            if e.data.tool_name == "send_email":
                send_email_called = True
                print(f"\n[✓] send_email called!", flush=True)
    
    session.on(track_events)
    
    # Wait for completion (3 minutes)
    print("Waiting for agent (up to 3 minutes)...")
    await asyncio.sleep(180)
    
    # Report status
    print(f"\n{'='*60}")
    print("✓ SUCCESS" if send_email_called else "⚠ WARNING: send_email not called")
    print(f"{'='*60}")

    # Cleanup
    await session.destroy()
    await client.stop()
    print("Done.")


if __name__ == "__main__":
    asyncio.run(main())
