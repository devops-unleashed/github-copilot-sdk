from copilot import Tool
import traceback


def send_email_handler(args):
    try:
        # Extract arguments from SDK wrapper
        tool_args = args.get("arguments", args)
        recipients = tool_args.get("recipients", [])
        subject = tool_args.get("subject", "Workflow Failure Notification")
        body = tool_args.get("body", "A workflow has failed.")

        if not recipients:
            return {"status": "error", "message": "No recipients provided."}

        # Print email to logs
        output = f"\n{'='*60}\n[EMAIL NOTIFICATION]\nTo: {', '.join(recipients)}\nSubject: {subject}\n\n{body}\n{'='*60}\n"
        print(output, flush=True)
        return output
        
    except Exception as ex:
        print(f"send_email error: {ex}", flush=True)
        return {"status": "error", "message": str(ex)}


# Tool configuration
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
