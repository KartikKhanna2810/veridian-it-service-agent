import json
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"


def load_tickets():
    """Load the existing ticket queue."""
    with open(DATA_DIR / "tickets.json", "r", encoding="utf-8") as file:
        return json.load(file)


def save_tickets(tickets):
    """Save updated tickets."""
    with open(
        DATA_DIR / "tickets.json",
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(tickets, file, indent=2)


def generate_ticket_id(tickets):
    """Generate the next ticket ID."""

    numbers = []

    for ticket in tickets:
        ticket_id = ticket.get("ticket_id", "")

        if ticket_id.startswith("TK-"):
            try:
                numbers.append(int(ticket_id.replace("TK-", "")))
            except ValueError:
                pass

    next_number = max(numbers, default=1051) + 1

    return f"TK-{next_number}"


def create_ticket(
    employee,
    email,
    issue,
    decision,
    priority,
    next_action,
    sources
):
    """
    Create a structured ticket for an employee request.
    """

    tickets = load_tickets()

    ticket_id = generate_ticket_id(tickets)

    ticket = {
        "ticket_id": ticket_id,
        "employee": employee,
        "email": email,
        "issue_summary": issue,
        "status": "Open",
        "decision": decision,
        "priority": priority,
        "next_action": next_action,
        "sources": sources,
        "created_at": datetime.now().isoformat(timespec="seconds")
    }

    tickets.append(ticket)

    save_tickets(tickets)

    return ticket