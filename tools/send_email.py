from copilot import Tool
import sys
import traceback


def send_email_handler(args):
    """Handler function that sends email notifications."""
    try:
        # SDK wraps the actual tool arguments in an 'arguments' key
        tool_args = args.get("arguments", args)
        
        recipients = tool_args.get("recipients", []) # List of emails
        subject = tool_args.get("subject", "Workflow Failure Notification")
        body = tool_args.get("body", "A scheduled integration workflow has failed. Please check the repo.")

        if not recipients:
            error_msg = "No recipients provided."
            print(f"[send_email] ERROR: {error_msg}", flush=True)
            return {"status": "error", "message": error_msg}

        output = f"\n{'='*60}\n[EMAIL NOTIFICATION]\nTo: {', '.join(recipients)}\nSubject: {subject}\n\n{body}\n{'='*60}\n"
        print(output, flush=True)
        return output
        
    except Exception as ex:
        error_msg = f"send_email exception: {ex}"
        print(error_msg, flush=True)
        print(traceback.format_exc(), flush=True)
        return {"status": "error", "message": error_msg}


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
