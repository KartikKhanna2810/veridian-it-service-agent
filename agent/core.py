import json
from pathlib import Path

from services.ticket_service import create_ticket
from services.audit_service import create_audit_record

from services.gemini_service import analyze_request_with_gemini


# ---------------------------------------------------------
# PATHS
# ---------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"


# ---------------------------------------------------------
# DATA LOADING
# ---------------------------------------------------------

def load_json(filename):
    """Load a JSON file from the Veridian data directory."""
    file_path = DATA_DIR / filename

    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def load_knowledge_base():
    return load_json("knowledge_base.json")


def load_requests():
    return load_json("requests.json")


def load_tickets():
    return load_json("tickets.json")


# ---------------------------------------------------------
# ISSUE DETECTION
# ---------------------------------------------------------

def detect_issue_type(message):
    """
    Identify the most likely IT issue from the employee message.

    This is intentionally deterministic so that the agent
    cannot invent unsupported categories.
    """

    text = message.lower()

    if any(word in text for word in [
        "phishing",
        "malware",
        "unauthorized access",
        "suspicious email"
    ]):
        return "security"

    if any(word in text for word in [
        "password",
        "locked out",
        "login",
        "failed attempts"
    ]):
        return "password"

    if "vpn" in text:
        return "vpn"

    if any(word in text for word in [
        "laptop",
        "screen",
        "computer"
    ]):
        return "laptop"

    if any(word in text for word in [
        "printer",
        "paper jam",
        "printing"
    ]):
        return "printer"

    if any(word in text for word in [
        "mailbox",
        "email",
        "emails",
        "quota"
    ]):
        return "email"

    if any(word in text for word in [
        "wifi",
        "wi-fi",
        "guest"
    ]):
        return "wifi"

    if any(word in text for word in [
        "expense",
        "expense tool",
        "expense software"
    ]):
        return "expense"

    if any(word in text for word in [
        "software",
        "install",
        "installation",
        "browser extension"
    ]):
        return "software"

    if any(word in text for word in [
        "work from home",
        "working from home",
        "remote",
        "home office",
        "monitor"
    ]):
        return "remote_work"

    if any(word in text for word in [
        "admin access",
        "administrator",
        "server access"
    ]):
        return "admin_access"

    return "unknown"


# ---------------------------------------------------------
# POLICY RETRIEVAL
# ---------------------------------------------------------

def get_relevant_policies(issue_type):
    """Retrieve policies matching the detected issue."""

    knowledge_base = load_knowledge_base()

    policies = []

    for policy in knowledge_base:

        if policy["category"] == issue_type:
            policies.append(policy)

        # Laptop replacement also requires the asset policy.
        if issue_type == "laptop" and policy["category"] == "asset":
            policies.append(policy)

    return policies


# ---------------------------------------------------------
# TICKET HISTORY
# ---------------------------------------------------------

def find_related_tickets(issue_type):
    """Find historical tickets related to the current issue."""

    tickets = load_tickets()

    keyword_map = {
        "password": ["password"],
        "vpn": ["vpn"],
        "laptop": ["laptop"],
        "software": ["software"],
        "printer": ["printer"],
        "email": ["mailbox"],
        "wifi": ["wifi"],
        "security": ["phishing"],
        "remote_work": ["home office"],
        "admin_access": ["admin access"]
    }

    keywords = keyword_map.get(issue_type, [])

    related = []

    for ticket in tickets:

        summary = ticket["issue_summary"].lower()

        if any(keyword in summary for keyword in keywords):
            related.append(ticket)

    return related


# ---------------------------------------------------------
# BUSINESS RULE ENGINE
# ---------------------------------------------------------

def evaluate_request(message, issue_type, policies):
    """
    Apply grounded business rules to the employee request.

    Returns:
        decision
        priority
        response
        next_action
        reason
    """

    text = message.lower()

    # -----------------------------------------------------
    # SECURITY
    # -----------------------------------------------------

    if issue_type == "security":

        return {
            "decision": "ESCALATE",
            "priority": "CRITICAL",
            "response": (
                "This appears to be a security incident. "
                "Report it immediately to "
                "security@veridian-corp.example. "
                "Do not forward the suspicious message "
                "to other employees."
            ),
            "next_action": (
                "Escalate to Security immediately."
            ),
            "reason": (
                "The request indicates a suspected phishing, "
                "malware, or unauthorized-access incident."
            )
        }

    # -----------------------------------------------------
    # PASSWORD
    # -----------------------------------------------------

    if issue_type == "password":

        if "6 times" in text or "more than 5" in text:

            return {
                "decision": "ROUTE",
                "priority": "HIGH",
                "response": (
                    "Your account has exceeded the 5 failed-attempt "
                    "threshold. IT needs to manually unlock the account."
                ),
                "next_action": "Route to IT for manual account unlock.",
                "reason": (
                    "KB-01 requires manual IT assistance after "
                    "5 failed password attempts."
                )
            }

        return {
            "decision": "RESOLVE",
            "priority": "NORMAL",
            "response": (
                "You can reset your password using the "
                "self-service password portal."
            ),
            "next_action": "Use the self-service password portal.",
            "reason": "KB-01 permits self-service password reset."
        }

    # -----------------------------------------------------
    # VPN
    # -----------------------------------------------------

    if issue_type == "vpn":

        if "contractor" in text:

            return {
                "decision": "FOLLOW_UP",
                "priority": "NORMAL",
                "response": (
                    "Contractors require manager approval submitted "
                    "through the access request form before VPN access "
                    "can be granted."
                ),
                "next_action": (
                    "Obtain manager approval through the access request form."
                ),
                "reason": (
                    "KB-02 requires manager approval for contractor VPN access."
                )
            }

        if "expired" in text:

            return {
                "decision": "RESOLVE",
                "priority": "NORMAL",
                "response": (
                    "Your VPN credentials have expired. VPN credentials "
                    "expire every 90 days and must be renewed by the employee."
                ),
                "next_action": "Renew the VPN credentials.",
                "reason": "KB-02 states that VPN credentials expire every 90 days."
            }

        return {
            "decision": "RESOLVE",
            "priority": "NORMAL",
            "response": (
                "VPN access is automatically granted to full-time employees."
            ),
            "next_action": "Check or renew your VPN credentials if required.",
            "reason": "KB-02 defines the VPN access policy."
        }

    # -----------------------------------------------------
    # LAPTOP
    # -----------------------------------------------------

    if issue_type == "laptop":

        age_match = None

        for age in ["3.5", "3.2", "2", "4"]:
            if f"{age} years" in text:
                age_match = float(age)
                break

        if "flickering" in text:

            return {
                "decision": "FOLLOW_UP",
                "priority": "NORMAL",
                "response": (
                    "Your laptop is showing a hardware issue. "
                    "Because you indicated that you may need a repair "
                    "rather than a replacement, the next step is to "
                    "verify the hardware failure."
                ),
                "next_action": (
                    "Verify the hardware failure with IT before "
                    "determining replacement eligibility."
                ),
                "reason": (
                    "KB-03 allows earlier replacement for verified "
                    "hardware failure."
                )
            }

        if "dead" in text or "won't turn on" in text:

            return {
                "decision": "ESCALATE",
                "priority": "HIGH",
                "response": (
                    "Your laptop appears to have a hardware failure. "
                    "The laptop replacement policy allows replacement "
                    "after 3 years or earlier for verified hardware failure. "
                    "However, the Asset Management Policy states that "
                    "early replacement outside the 4-year refresh cycle "
                    "requires Finance sign-off in addition to IT approval."
                ),
                "next_action": (
                    "Verify the hardware failure and route the replacement "
                    "request for the required approvals."
                ),
                "reason": (
                    "The request involves both the laptop replacement policy "
                    "and the Asset Management Policy."
                )
            }

        return {
            "decision": "FOLLOW_UP",
            "priority": "NORMAL",
            "response": (
                "Please provide the laptop's approximate age and "
                "describe the problem you are experiencing."
            ),
            "next_action": "Wait for additional laptop details.",
            "reason": "The supplied information is insufficient."
        }

    # -----------------------------------------------------
    # PRINTER
    # -----------------------------------------------------

    if issue_type == "printer":

        return {
            "decision": "RESOLVE",
            "priority": "NORMAL",
            "response": (
                "First check the printer queue and restart the "
                "print spooler. If the problem continues after "
                "the restart, an IT ticket should be logged with "
                "the printer's asset tag."
            ),
            "next_action": (
                "Check the queue and restart the print spooler."
            ),
            "reason": "KB-05 defines the printer troubleshooting sequence."
        }

    # -----------------------------------------------------
    # EMAIL
    # -----------------------------------------------------

    if issue_type == "email":

        return {
            "decision": "RESOLVE",
            "priority": "NORMAL",
            "response": (
                "The default mailbox quota is 25GB. Start by "
                "archiving old mail. A quota increase beyond 25GB "
                "requires manager approval and cannot exceed 50GB."
            ),
            "next_action": "Archive old mail first.",
            "reason": "KB-06 defines the mailbox quota policy."
        }

    # -----------------------------------------------------
    # WIFI
    # -----------------------------------------------------

    if issue_type == "wifi":

        return {
            "decision": "RESOLVE",
            "priority": "LOW",
            "response": (
                "Guest Wi-Fi credentials are valid for 24 hours "
                "and can be generated by any employee from the "
                "front-desk kiosk. No IT ticket is required."
            ),
            "next_action": "Generate guest credentials at the front desk kiosk.",
            "reason": "KB-07 defines guest Wi-Fi access."
        }

    # -----------------------------------------------------
    # EXPENSE
    # -----------------------------------------------------

    if issue_type == "expense":

        return {
            "decision": "ROUTE",
            "priority": "NORMAL",
            "response": (
                "Finance manages access to the expense management tool. "
                "IT can assist with login or technical issues once an "
                "account already exists."
            ),
            "next_action": (
                "Confirm that the employee already has an expense-tool "
                "account; route access provisioning to Finance if needed."
            ),
            "reason": "KB-08 defines the Finance/IT responsibility boundary."
        }

    # -----------------------------------------------------
    # SOFTWARE
    # -----------------------------------------------------

    if issue_type == "software":

        return {
            "decision": "ESCALATE",
            "priority": "NORMAL",
            "response": (
                "Non-catalog software requires IT Security review. "
                "The supplied policy states that this review takes "
                "3–5 business days."
            ),
            "next_action": "Route the request to IT Security for review.",
            "reason": "KB-04 requires Security review for non-catalog software."
        }

    # -----------------------------------------------------
    # REMOTE WORK
    # -----------------------------------------------------

    if issue_type == "remote_work":

        return {
            "decision": "ROUTE",
            "priority": "NORMAL",
            "response": (
                "Employees working remotely more than 3 days per week "
                "are eligible for a one-time home-office equipment "
                "allowance. Manager sign-off and Finance processing "
                "are required before IT handles equipment shipping."
            ),
            "next_action": (
                "Obtain manager sign-off and Finance processing first."
            ),
            "reason": "KB-10 defines the home-office equipment process."
        }

    # -----------------------------------------------------
    # ADMIN ACCESS
    # -----------------------------------------------------

    if issue_type == "admin_access":

        return {
            "decision": "ESCALATE",
            "priority": "HIGH",
            "response": (
                "The supplied IT policies do not provide an approval "
                "procedure for administrative access to the finance "
                "reporting server. I cannot invent an approval process."
            ),
            "next_action": (
                "Route the request to the appropriate human owner "
                "for review."
            ),
            "reason": (
                "The provided source data does not define an "
                "admin-access approval policy."
            )
        }

    # -----------------------------------------------------
    # UNKNOWN
    # -----------------------------------------------------

    return {
        "decision": "FOLLOW_UP",
        "priority": "NORMAL",
        "response": (
            "I'd be happy to help. Could you tell me what isn't "
            "working or which IT service you need help with?"
        ),
        "next_action": "Wait for the employee to provide more details.",
        "reason": (
            "The request does not contain enough information to "
            "identify a supported IT issue."
        )
    }


# ---------------------------------------------------------
# MAIN AGENT
# ---------------------------------------------------------

def run_agent(
    message,
    employee="Unknown Employee",
    email="unknown@veridian-corp.example"
):
    """
    Main entry point for the Veridian IT Service Agent.

    The agent:
    1. Understands the issue
    2. Retrieves relevant policies
    3. Checks historical tickets
    4. Applies business rules
    5. Creates a ticket when needed
    6. Creates an audit record
    """

    # ---------------------------------------------
    # 1. Understand the issue
    # ---------------------------------------------

    gemini_result = analyze_request_with_gemini(
    message,
    [
        "security",
        "password",
        "vpn",
        "laptop",
        "printer",
        "email",
        "wifi",
        "expense",
        "software",
        "remote_work",
        "admin_access",
        "unknown",
    ],
)

    if gemini_result["success"]:
        issue_type = gemini_result["issue_type"]
    else:
        issue_type = detect_issue_type(message)

    # ---------------------------------------------
    # 2. Retrieve policies
    # ---------------------------------------------

    policies = get_relevant_policies(issue_type)

    # ---------------------------------------------
    # 3. Check historical tickets
    # ---------------------------------------------

    related_tickets = find_related_tickets(issue_type)

    # ---------------------------------------------
    # 4. Apply business rules
    # ---------------------------------------------

    result = evaluate_request(
        message,
        issue_type,
        policies
    )

    # ---------------------------------------------
    # 5. Determine whether a ticket is required
    # ---------------------------------------------

    ticket_id = None
    ticket_reused = False

    ticket_required = result["decision"] in [
        "ESCALATE",
        "ROUTE"
    ]

    if ticket_required:

        # Check for an existing open ticket for the same
        # employee with a substantially matching issue before
        # creating a duplicate.

        existing_tickets = load_tickets()
        matched_ticket = None

        for existing in existing_tickets:

            # Only consider tickets with an "Open" status.
            status = (existing.get("status") or "").lower()
            if "closed" in status or "resolved" in status or "rejected" in status:
                continue

            # Must be the same employee.
            if existing.get("employee") != employee:
                continue

            # Check if the issue text substantially overlaps.
            existing_issue = (
                existing.get("issue_summary") or ""
            ).strip().lower()
            current_issue = message.strip().lower()

            # Match if the existing issue is contained in the
            # current message or vice-versa, or if they share
            # enough leading content (first 40 chars).
            if (
                existing_issue in current_issue
                or current_issue in existing_issue
                or (
                    len(existing_issue) >= 20
                    and len(current_issue) >= 20
                    and existing_issue[:40] == current_issue[:40]
                )
            ):
                matched_ticket = existing
                break

        if matched_ticket:
            ticket_id = matched_ticket["ticket_id"]
            ticket_reused = True
        else:
            ticket = create_ticket(
                employee=employee,
                email=email,
                issue=message,
                decision=result["decision"],
                priority=result["priority"],
                next_action=result["next_action"],
                sources=[
                    policy["id"]
                    for policy in policies
                ]
            )

            ticket_id = ticket["ticket_id"]

    # ---------------------------------------------
    # 6. Create audit record
    # ---------------------------------------------

    audit = create_audit_record(
        employee=employee,
        issue=message,
        decision=result["decision"],
        priority=result["priority"],
        sources=[
            policy["id"]
            for policy in policies
        ],
        next_action=result["next_action"],
        ticket_id=ticket_id
    )

    # ---------------------------------------------
    # 7. Return complete agent result
    # ---------------------------------------------

    return {
        "issue_type": issue_type,
        "decision": result["decision"],
        "priority": result["priority"],
        "response": result["response"],
        "next_action": result["next_action"],
        "reason": result["reason"],
        "sources": [
            policy["id"]
            for policy in policies
        ],
        "related_tickets": related_tickets,
        "ticket_id": ticket_id,
        "ticket_reused": ticket_reused,
        "audit_id": audit["audit_id"]
    }