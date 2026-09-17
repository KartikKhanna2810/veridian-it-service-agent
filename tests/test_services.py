from services.ticket_service import create_ticket
from services.audit_service import create_audit_record


employee = "Test Employee"
email = "test@veridian-corp.example"

issue = "My printer is not working."

decision = "RESOLVE"
priority = "NORMAL"

next_action = (
    "Check the printer queue and restart the print spooler."
)

sources = ["KB-05"]


ticket = create_ticket(
    employee=employee,
    email=email,
    issue=issue,
    decision=decision,
    priority=priority,
    next_action=next_action,
    sources=sources
)


audit = create_audit_record(
    employee=employee,
    issue=issue,
    decision=decision,
    priority=priority,
    sources=sources,
    next_action=next_action,
    ticket_id=ticket["ticket_id"]
)


print("\n========== TICKET ==========")

print(ticket)

print("\n========== AUDIT ==========")

print(audit)

print("\n============================")