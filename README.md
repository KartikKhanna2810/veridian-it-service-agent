# Veridian Internal Service Agent

An internal IT support agent prototype built for the **AIONOS hiring assignment — Assignment 2: Internal Service Agent (IT Support)**.

The application analyzes employee IT requests using the supplied Veridian Corp knowledge base and ticket context, uses **Google Gemini for natural-language request understanding**, applies deterministic policy rules for the final decision, creates or reuses tickets when required, and maintains an audit trail.

> **Important grounding principle:** Gemini is used as the natural-language understanding layer. The deterministic agent core remains the final authority for policy decisions. The agent uses only the material supplied in the assignment data pack and does not invent unsupported company procedures.

---

## Overview

The Veridian Internal Service Agent assists employees with common internal IT support requests.

### End-to-end flow

```text
Employee Request
       ↓
Streamlit UI
       ↓
Gemini — Natural-Language Understanding
       ↓
Issue Type + Structured Context
       ↓
Knowledge Base + Related Ticket Lookup
       ↓
Deterministic Policy Engine
       ↓
RESOLVE / FOLLOW_UP / ROUTE / ESCALATE
       ↓
Ticket Creation or Reuse (when required)
       ↓
Audit Record
       ↓
Final Response
```

If the Gemini request-understanding call is unavailable, the existing deterministic issue detector is used as a fallback.

---

## Key Capabilities

- Understands varied employee IT requests using Google Gemini.
- Maps requests to supported issue types such as:
  - Password
  - VPN
  - Laptop
  - Printer
  - Email
  - Guest Wi-Fi
  - Software
  - Security
  - Expense software
  - WFH equipment
  - Admin access
- Retrieves relevant policies from the supplied knowledge base.
- Applies deterministic business rules to produce:
  - `RESOLVE`
  - `FOLLOW_UP`
  - `ROUTE`
  - `ESCALATE`
- Shows the policy sources and reasoning behind the result.
- Looks up related historical tickets.
- Prevents duplicate creation by reusing a matching active ticket.
- Creates an audit record for every agent run.
- Provides Streamlit views for:
  - Agent
  - Employee Requests
  - Ticket Queue
  - Audit Log

---

## Gemini Integration

Google Gemini is integrated through the `google-genai` Python SDK.

### Gemini's responsibility

Gemini is responsible for **natural-language understanding only**:

1. Understand the employee's wording.
2. Identify the issue type from the allowed categories.
3. Extract a short factual summary/context.
4. Return structured information to the agent core.

### What Gemini does not decide

Gemini does **not** determine company policy outcomes.

The deterministic policy engine remains responsible for:

- Selecting relevant Veridian policies.
- Applying the supplied business rules.
- Determining the final decision.
- Setting priority.
- Determining the next action.
- Handling ticket creation/reuse.
- Maintaining source grounding.

This separation provides flexible language understanding while keeping policy decisions predictable and auditable.

---

## Policy Grounding

The supplied assignment data pack is the source of truth.

The prototype uses:

- **10 knowledge-base policies:** `KB-01` to `KB-10`
- **15 supplied employee requests:** `REQ-01` to `REQ-15`
- **10 original tickets:** `TK-1042` to `TK-1051`
- **Asset Management Policy**
- Local audit storage in `data/audit_log.json`

The agent does not invent approval workflows or policies that are not defined in the supplied material.

Examples of grounded behavior:

- Security incidents are escalated to the supplied security contact.
- Locked accounts after more than five failed password attempts are routed for manual IT unlock.
- Non-catalog software requires the supplied IT Security review.
- Contractor VPN access requires the supplied manager approval.
- Early laptop replacement depends on the supplied hardware-failure and asset-policy rules.
- Undefined administrative-access procedures are not invented.

---

## Architecture

```text
┌──────────────────────┐
│   Employee Request   │
│    Natural Language  │
└──────────┬───────────┘
           ↓
┌──────────────────────┐
│    Streamlit UI      │
└──────────┬───────────┘
           ↓
┌──────────────────────┐
│ Gemini Service       │
│ Natural-language     │
│ understanding        │
└──────────┬───────────┘
           ↓
┌──────────────────────┐
│ Agent Core           │
│ Deterministic Policy │
│ & Decision Engine    │
└───────┬───────┬──────┘
        │       │
        ↓       ↓
┌────────────┐ ┌────────────────┐
│ Knowledge  │ │ Ticket History │
│ Base       │ │ / Ticket       │
│ JSON       │ │ Service        │
└──────┬─────┘ └───────┬────────┘
       └───────┬───────┘
               ↓
       ┌────────────────┐
       │ Decision +     │
       │ Response       │
       └───────┬────────┘
               ↓
       ┌────────────────┐
       │ Audit Service  │
       │ audit_log.json │
       └────────────────┘
```

The repository also contains the standalone architecture diagram prepared for the submission.

---

## Project Structure

```text
veridian-it-service-agent/
├── agent/
│   ├── __init__.py
│   └── core.py
├── data/
│   ├── knowledge_base.json
│   ├── requests.json
│   ├── tickets.json
│   └── audit_log.json
├── services/
│   ├── __init__.py
│   ├── ticket_service.py
│   ├── audit_service.py
│   └── gemini_service.py
├── tests/
│   ├── test_agent.py
│   └── test_services.py
├── app.py
├── .env
├── .env.example
├── .gitignore
├── README.md
└── requirements.txt
```

---

## Ticket Management

The ticket service supports ticket creation and duplicate prevention.

For requests requiring routing or escalation:

1. Existing tickets are checked.
2. Closed, resolved, and rejected tickets are not treated as active duplicates.
3. A matching active ticket for the same employee can be reused.
4. Otherwise a new ticket is created with a generated ID.

Example:

```text
Existing active ticket → reuse
No matching active ticket → create new ticket
```

This prevents repeated analysis of the same issue from unnecessarily creating duplicate tickets.

---

## Audit Trail

Every agent run creates an audit record.

The audit record includes:

- Audit ID
- Timestamp
- Employee
- Issue
- Decision
- Priority
- Knowledge-base sources
- Next action
- Ticket ID, when applicable

Audit records are stored in:

```text
data/audit_log.json
```

---

## Streamlit Application

The Streamlit interface contains four main areas.

### Agent

- Select a supplied employee request.
- Edit the request if required.
- Analyze the request.
- View:
  - Decision
  - Priority
  - Issue type
  - Agent response
  - Next action
  - Reason
  - Knowledge-base sources
  - Related ticket history
  - Ticket creation/reuse
  - Audit record

### Employee Requests

Displays all 15 supplied employee requests and their initial context.

### Ticket Queue

Displays active and historical ticket information.

### Audit Log

Displays the agent interaction history and audit records.

---

## Testing

Representative scenarios were tested in the deployed application.

### Guest Wi-Fi — REQ-02

```text
Issue Type: Wi-Fi
Decision: RESOLVE
Priority: LOW
```

### Phishing — REQ-08

```text
Issue Type: Security
Decision: ESCALATE
Priority: CRITICAL
```

The phishing flow was also used to verify ticket creation and duplicate prevention.

### Laptop hardware issue — REQ-13

```text
Issue Type: Laptop
Decision: FOLLOW_UP
Priority: NORMAL
```

The agent identifies the laptop issue through the Gemini understanding layer, while the deterministic policy engine applies the supplied laptop-replacement policy.

### Full request evaluation

All 15 supplied employee requests were evaluated against the deterministic decision logic during development.

---

## Environment Variables

Create a local `.env` file:

```env
GEMINI_API_KEY=your_real_gemini_api_key
```

The real API key must **never** be committed to GitHub.

`.env` is included in `.gitignore`.

For Streamlit Community Cloud, configure the same variable through the application's **Secrets** settings.

The repository contains `.env.example` with placeholders only.

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/KartikKhanna2810/veridian-it-service-agent.git
cd veridian-it-service-agent
```

### 2. Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure the Gemini key

Create `.env` and add:

```env
GEMINI_API_KEY=your_real_gemini_api_key
```

### 5. Run the application

```bash
streamlit run app.py
```

If Streamlit is installed in the active environment but the `streamlit` command resolves to another Python installation, use:

```bash
python -m streamlit run app.py
```

---

## Technology Stack

| Component | Technology |
|---|---|
| Language | Python |
| Web UI | Streamlit |
| Natural-language understanding | Google Gemini API |
| Gemini SDK | `google-genai` |
| Policy engine | Deterministic Python rules |
| Data storage | JSON |
| Ticket service | Python service layer |
| Audit service | Python service layer |
| Deployment | Streamlit Community Cloud |

---

## Design Decisions

### 1. Gemini + deterministic policy engine

Gemini provides flexible understanding of employee language, while deterministic rules make the final policy decision.

This avoids delegating company-policy decisions to an unconstrained language model.

### 2. Source-grounded responses

The agent uses the supplied assignment data as its policy source and exposes the relevant source IDs in the UI.

### 3. No invented procedures

When the supplied material does not define an approval or handling procedure, the agent does not fabricate one.

### 4. Duplicate prevention

Active matching tickets are reused instead of repeatedly creating tickets for the same issue.

### 5. Auditability

Every run produces a traceable audit record containing the decision and supporting context.

### 6. Fallback behavior

If Gemini is unavailable, the deterministic issue detector can still classify supported requests so the application remains usable.

---

## Limitations / Future Improvements

- The current knowledge base is intentionally limited to the supplied assignment data.
- Ticket and audit data are stored locally as JSON for the prototype.
- Gemini is currently used for request understanding rather than final policy decisions.
- A production system could add:
  - More internal policies and service categories
  - Persistent database storage
  - Authentication and role-based access
  - Integration with a production ITSM platform
  - More comprehensive automated evaluation
  - Monitoring and usage analytics

---

## Demo

**Public Streamlit Demo**

https://veridian-it-service-agent-bnvtm4yhougnaddhfzsmsk.streamlit.app/

**GitHub Repository**

https://github.com/KartikKhanna2810/veridian-it-service-agent

### Suggested reviewer flow

```text
1. Open the public demo
2. Try Guest Wi-Fi
3. Try the phishing/security scenario
4. Re-run the same escalation to demonstrate ticket reuse
5. Open Ticket Queue
6. Open Audit Log
7. Try a laptop hardware scenario
```

---

## Assignment Deliverables

The repository is accompanied by:

- Public Streamlit demo
- GitHub repository
- Updated system architecture diagram
- 10-slide presentation
- Demonstration scenarios covering policy grounding, escalation, ticketing and auditability

---

## Project Status

**Completed prototype with Gemini integration.**

The current implementation combines:

> **Natural-language understanding → deterministic policy decisions → transparent responses → ticket management → audit trail**
