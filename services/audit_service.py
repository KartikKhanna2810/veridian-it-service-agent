import json
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

AUDIT_FILE = DATA_DIR / "audit_log.json"


def load_audit_log():
    """Load existing audit records."""

    if not AUDIT_FILE.exists():
        return []

    with open(
        AUDIT_FILE,
        "r",
        encoding="utf-8"
    ) as file:
        return json.load(file)


def save_audit_log(records):
    """Save audit records."""

    with open(
        AUDIT_FILE,
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            records,
            file,
            indent=2
        )


def create_audit_record(
    employee,
    issue,
    decision,
    priority,
    sources,
    next_action,
    ticket_id=None
):
    """
    Record the agent's decision and reasoning context.
    """

    records = load_audit_log()

    audit_id = f"AUD-{len(records) + 1:04d}"

    record = {
        "audit_id": audit_id,
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "employee": employee,
        "issue": issue,
        "decision": decision,
        "priority": priority,
        "sources": sources,
        "next_action": next_action,
        "ticket_id": ticket_id
    }

    records.append(record)

    save_audit_log(records)

    return record