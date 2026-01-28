from copilot import Tool


def send_email_handler(args):
    recipients = args.get("recipients", []) # List of emails
    subject = args.get("subject", "Workflow Failure Notification")
    body = args.get("body", "A scheduled integration workflow has failed. Please check the repo.")

    if not recipients:
        return {"status": "error", "message": "No recipients provided."}

    output = f"[EMAIL OUTPUT]\nTo: {', '.join(recipients)}\nSubject: {subject}\n\n{body}"
    print(output)

    return {"status": "success", "message": output}


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
