from copilot import Tool
import sys
import traceback


def send_email_handler(args):
    """Handler function that sends email notifications. Wrapped with comprehensive error handling."""
    try:
        print("[send_email_handler] Starting execution...", flush=True)
        print(f"[send_email_handler] Received args: {args}", flush=True)
        
        recipients = args.get("recipients", []) # List of emails
        subject = args.get("subject", "Workflow Failure Notification")
        body = args.get("body", "A scheduled integration workflow has failed. Please check the repo.")

        if not recipients:
            error_msg = "No recipients provided."
            print(f"[send_email_handler] ERROR: {error_msg}", flush=True)
            return {"status": "error", "message": error_msg}

        output = f"[EMAIL OUTPUT FROM TOOL]\nTo: {', '.join(recipients)}\nSubject: {subject}\n\n{body}"
        print(output, flush=True)
        print(f"\n{'='*60}", flush=True)
        print("send_email tool executed successfully", flush=True)
        print(f"{'='*60}\n", flush=True)

        # Tool handlers should return a simple string (not dict) for MCP compatibility
        print(f"[send_email_handler] Returning output string", flush=True)
        return output
        
    except Exception as ex:
        error_msg = f"Exception in send_email_handler: {ex}"
        print(f"[send_email_handler] EXCEPTION: {error_msg}", flush=True)
        print(f"[send_email_handler] Traceback:\n{traceback.format_exc()}", flush=True)
        return {"status": "error", "message": error_msg, "exception": str(ex)}


# Define the custom tool schema for the agent
email_tool = Tool(
    name="send_email",
    description="Send an email notification to a list of committers about a workflow failure.",
    parameters={
        "type": "object",
        "properties": {
            "recipients": {"type": "array", "items": {"type": "string"}, "description": "List of email addresses."},
            "subject": {"type": "string", "description": "Email subject."},
            "body": {"type": "string", "description": "Email body with failure details."}
        },
        "required": ["recipients", "subject", "body"]
    },
    handler=send_email_handler
)
