import streamlit as st
import json
from pathlib import Path

from agent.core import run_agent, load_requests, load_tickets, load_knowledge_base
from services.audit_service import load_audit_log

# ---------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

st.set_page_config(
    page_title="Veridian IT Service Desk",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------
# CUSTOM STYLES
# ---------------------------------------------------------

st.markdown("""
<style>
    /* ---- Global ---- */
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
    }

    /* ---- Sidebar branding ---- */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f1b2d 0%, #1a2942 100%);
    }
    [data-testid="stSidebar"] * {
        color: #e0e6ed !important;
    }
    [data-testid="stSidebar"] .stRadio label {
        font-size: 0.95rem;
    }
    [data-testid="stSidebar"] hr {
        border-color: rgba(255,255,255,0.12);
    }

    /* ---- Metric cards ---- */
    [data-testid="stMetric"] {
        background: #f0f2f6;
        border: 1px solid #d1d5db;
        border-radius: 10px;
        padding: 14px 18px;
    }
    [data-testid="stMetric"] label {
        font-size: 0.78rem !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #475569 !important;
    }
    [data-testid="stMetric"] [data-testid="stMetricValue"] {
        font-size: 1.15rem !important;
        font-weight: 600;
        color: #1e293b !important;
    }

    /* ---- Decision badge helpers ---- */
    .badge {
        display: inline-block;
        padding: 4px 14px;
        border-radius: 6px;
        font-size: 0.82rem;
        font-weight: 600;
        letter-spacing: 0.03em;
    }
    .badge-resolve  { background: #dcfce7; color: #166534; }
    .badge-escalate { background: #fee2e2; color: #991b1b; }
    .badge-route    { background: #fef3c7; color: #92400e; }
    .badge-follow   { background: #dbeafe; color: #1e40af; }

    .badge-critical { background: #fee2e2; color: #991b1b; }
    .badge-high     { background: #ffedd5; color: #9a3412; }
    .badge-normal   { background: #e0e7ff; color: #3730a3; }
    .badge-low      { background: #f0fdf4; color: #166534; }

    .badge-open     { background: #dbeafe; color: #1d4ed8; }
    .badge-active   { background: #fef3c7; color: #92400e; }
    .badge-closed   { background: #f1f5f9; color: #64748b; }

    /* ---- Section headers ---- */
    .section-header {
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #94a3b8;
        font-weight: 600;
        margin-bottom: 4px;
    }

    /* ---- Card container ---- */
    .info-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 20px 24px;
        margin-bottom: 12px;
    }

    /* ---- Expander tweaks ---- */
    .streamlit-expanderHeader {
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------
# HELPER FUNCTIONS
# ---------------------------------------------------------

def decision_badge(decision):
    """Return HTML badge for a decision value."""
    css_map = {
        "RESOLVE": "badge-resolve",
        "ESCALATE": "badge-escalate",
        "ROUTE": "badge-route",
        "FOLLOW_UP": "badge-follow",
    }
    css = css_map.get(decision, "badge-follow")
    label = decision.replace("_", " ") if decision else "—"
    return f'<span class="badge {css}">{label}</span>'


def priority_badge(priority):
    """Return HTML badge for a priority value."""
    css_map = {
        "CRITICAL": "badge-critical",
        "HIGH": "badge-high",
        "NORMAL": "badge-normal",
        "LOW": "badge-low",
    }
    css = css_map.get(priority, "badge-normal")
    label = priority if priority else "—"
    return f'<span class="badge {css}">{label}</span>'


def status_badge(status):
    """Return HTML badge for a ticket status."""
    s = (status or "").lower()
    if "closed" in s or "resolved" in s or "rejected" in s:
        return f'<span class="badge badge-closed">{status}</span>'
    elif "open" in s or "active" in s or "pending" in s or "escalated" in s:
        return f'<span class="badge badge-active">{status}</span>'
    else:
        return f'<span class="badge badge-open">{status}</span>'


# ---------------------------------------------------------
# SIDEBAR
# ---------------------------------------------------------

with st.sidebar:
    # Branding
    st.markdown("""
    <div style="text-align:center; padding: 8px 0 4px 0;">
        <div style="font-size: 2rem;">🛡️</div>
        <div style="font-size: 1.2rem; font-weight: 700; letter-spacing: 0.02em; margin-top: 2px;">
            VERIDIAN
        </div>
        <div style="font-size: 0.78rem; letter-spacing: 0.12em; opacity: 0.7; margin-top: -2px;">
            IT SERVICE DESK
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # Navigation
    page = st.radio(
        "Navigation",
        ["🤖  Agent", "📋  Employee Requests", "🎫  Ticket Queue", "📝  Audit Log"],
        label_visibility="collapsed",
    )

    st.markdown("---")

    # System status
    st.markdown("""
    <div style="padding: 10px 0 6px 0;">
        <div style="display: flex; align-items: center; gap: 8px;">
            <span style="display: inline-block; width: 8px; height: 8px;
                         background: #22c55e; border-radius: 50%;
                         box-shadow: 0 0 6px #22c55e;"></span>
            <span style="font-size: 0.82rem; opacity: 0.85;">Agent Online</span>
        </div>
        <div style="font-size: 0.72rem; opacity: 0.5; margin-top: 6px;">
            Veridian Corp · Internal Use Only
        </div>
    </div>
    """, unsafe_allow_html=True)


# ---------------------------------------------------------
# PAGE: AGENT
# ---------------------------------------------------------

if "Agent" in page:
    st.markdown("## 🤖 Internal Service Agent")
    st.caption(
        "Veridian IT Service Desk — Analyzes employee IT requests using the "
        "Veridian knowledge base, retrieves relevant policies, checks ticket "
        "history, and provides grounded decisions."
    )

    st.markdown("---")

    # Load employee requests from data
    requests_data = load_requests()

    # Build selection options
    request_options = {
        f"{r['request_id']}  —  {r['employee']}": idx
        for idx, r in enumerate(requests_data)
    }

    selected_label = st.selectbox(
        "Select an employee request",
        options=list(request_options.keys()),
        index=0,
    )

    selected_idx = request_options[selected_label]
    selected_request = requests_data[selected_idx]

    # Show employee info
    col_emp, col_email = st.columns(2)
    with col_emp:
        st.text_input("Employee", value=selected_request["employee"], disabled=True)
    with col_email:
        st.text_input("Email", value=selected_request["email"], disabled=True)

    # Editable request text
    request_text = st.text_area(
        "Request",
        value=selected_request["request"],
        height=100,
    )

    # Analyze button
    analyze_clicked = st.button("⚡  Analyze Request", type="primary", use_container_width=True)

    if analyze_clicked:
        with st.spinner("Analyzing request against Veridian policies…"):
            result = run_agent(
                message=request_text,
                employee=selected_request["employee"],
                email=selected_request["email"],
            )

        st.markdown("---")
        st.markdown("### Analysis Results")

        # ---- Top-level decision metrics ----
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Decision", result["decision"])
        with col2:
            st.metric("Priority", result["priority"])
        with col3:
            st.metric("Issue Type", result["issue_type"].replace("_", " ").title())

        # ---- Visual decision + priority badges ----
        st.markdown(
            f"<div style='margin: 8px 0 16px 0;'>"
            f"{decision_badge(result['decision'])}  &nbsp; "
            f"{priority_badge(result['priority'])}"
            f"</div>",
            unsafe_allow_html=True,
        )

        # ---- Agent Response ----
        st.markdown('<p class="section-header">Agent Response</p>', unsafe_allow_html=True)
        st.info(result["response"], icon="💬")

        # ---- Next Action + Reason ----
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown('<p class="section-header">Next Action</p>', unsafe_allow_html=True)
            st.markdown(f"> {result['next_action']}")
        with col_b:
            st.markdown('<p class="section-header">Reason</p>', unsafe_allow_html=True)
            st.markdown(f"> {result['reason']}")

        # ---- Knowledge Base Sources ----
        st.markdown('<p class="section-header">Knowledge Base Sources</p>', unsafe_allow_html=True)
        if result["sources"]:
            kb = load_knowledge_base()
            kb_map = {item["id"]: item for item in kb}
            source_cols = st.columns(min(len(result["sources"]), 4))
            for i, src_id in enumerate(result["sources"]):
                with source_cols[i % len(source_cols)]:
                    kb_item = kb_map.get(src_id)
                    if kb_item:
                        st.markdown(
                            f"**{src_id}** — {kb_item['title']}"
                        )
                        st.caption(kb_item["policy"][:120] + ("…" if len(kb_item["policy"]) > 120 else ""))
                    else:
                        st.markdown(f"**{src_id}**")
        else:
            st.caption("No knowledge base sources matched.")

        # ---- Related Tickets ----
        st.markdown('<p class="section-header">Related Ticket History</p>', unsafe_allow_html=True)
        if result["related_tickets"]:
            for t in result["related_tickets"]:
                st.markdown(
                    f"&nbsp;&nbsp; 🎫 **{t['ticket_id']}** — {t['issue_summary']} — "
                    f"{status_badge(t['status'])}",
                    unsafe_allow_html=True,
                )
        else:
            st.caption("No related historical tickets found.")

        # ---- Ticket & Audit IDs ----
        st.markdown("---")
        col_t, col_au = st.columns(2)
        with col_t:
            if result["ticket_id"]:
                if result.get("ticket_reused"):
                    st.warning(
                        f"🎫  Existing ticket reused: **{result['ticket_id']}**",
                        icon="🔄",
                    )
                else:
                    st.success(
                        f"🎫  Ticket Created: **{result['ticket_id']}**",
                        icon="✅",
                    )
            else:
                st.caption("ℹ️  No ticket created (resolved directly).")
        with col_au:
            st.success(f"📝  Audit Record: **{result['audit_id']}**", icon="✅")


# ---------------------------------------------------------
# PAGE: EMPLOYEE REQUESTS
# ---------------------------------------------------------

elif "Employee Requests" in page:
    st.markdown("## 📋 Employee Requests")
    st.caption(
        "All open IT requests submitted by Veridian Corp employees. "
        "These requests are loaded from the organization's request queue."
    )

    st.markdown("---")

    requests_data = load_requests()

    # Summary metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Requests", len(requests_data))
    with col2:
        not_started = sum(1 for r in requests_data if r.get("initial_action", "").startswith("Not started"))
        st.metric("Not Started", not_started)
    with col3:
        in_progress = len(requests_data) - not_started
        st.metric("In Progress / Waiting", in_progress)

    st.markdown("")

    # Requests as expanders
    for req in requests_data:
        action = req.get("initial_action", "—")
        icon = "🟢" if "Not started" in action else ("🟡" if "progress" in action.lower() or "waiting" in action.lower() else "🔴")

        with st.expander(f"{icon}  **{req['request_id']}** — {req['employee']}  •  {req.get('date_opened', '')}"):
            st.markdown(f"**Employee:** {req['employee']}")
            st.markdown(f"**Email:** {req['email']}")
            st.markdown(f"**Date Opened:** {req.get('date_opened', '—')}")
            st.markdown(f"**Initial Action:** {action}")
            st.markdown("---")
            st.markdown(f"**Request:**")
            st.markdown(f"> {req['request']}")


# ---------------------------------------------------------
# PAGE: TICKET QUEUE
# ---------------------------------------------------------

elif "Ticket Queue" in page:
    st.markdown("## 🎫 Ticket Queue")
    st.caption(
        "Displays the current IT service ticket queue including historical tickets "
        "and tickets created by the agent during analysis."
    )

    st.markdown("---")

    tickets = load_tickets()

    # Classify tickets
    active_tickets = []
    closed_tickets = []
    for t in tickets:
        s = (t.get("status") or "").lower()
        if "closed" in s or "resolved" in s or "rejected" in s:
            closed_tickets.append(t)
        else:
            active_tickets.append(t)

    # Summary
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Tickets", len(tickets))
    with col2:
        st.metric("Active / Open", len(active_tickets))
    with col3:
        st.metric("Closed", len(closed_tickets))

    st.markdown("")

    # ---- ACTIVE TICKETS ----
    st.markdown("### 🔵 Active Tickets")

    if active_tickets:
        for t in active_tickets:
            with st.expander(
                f"**{t['ticket_id']}** — {t.get('employee', '—')}  •  "
                f"{t.get('issue_summary', '')[:60]}"
            ):
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown(f"**Ticket ID:** {t['ticket_id']}")
                    st.markdown(f"**Employee:** {t.get('employee', '—')}")
                    if t.get("email"):
                        st.markdown(f"**Email:** {t['email']}")
                    st.markdown(f"**Issue:** {t.get('issue_summary', '—')}")
                with c2:
                    st.markdown(
                        f"**Status:** {status_badge(t.get('status', '—'))}",
                        unsafe_allow_html=True,
                    )
                    if t.get("decision"):
                        st.markdown(
                            f"**Decision:** {decision_badge(t['decision'])}",
                            unsafe_allow_html=True,
                        )
                    if t.get("priority"):
                        st.markdown(
                            f"**Priority:** {priority_badge(t['priority'])}",
                            unsafe_allow_html=True,
                        )
                    if t.get("next_action"):
                        st.markdown(f"**Next Action:** {t['next_action']}")
                    if t.get("sources"):
                        st.markdown(f"**Sources:** {', '.join(t['sources'])}")
                    if t.get("created_at"):
                        st.markdown(f"**Created:** {t['created_at']}")
    else:
        st.caption("No active tickets at this time.")

    st.markdown("")

    # ---- CLOSED TICKETS ----
    st.markdown("### ⚪ Closed Tickets")

    if closed_tickets:
        for t in closed_tickets:
            with st.expander(
                f"**{t['ticket_id']}** — {t.get('employee', '—')}  •  "
                f"{t.get('issue_summary', '')[:60]}"
            ):
                st.markdown(f"**Ticket ID:** {t['ticket_id']}")
                st.markdown(f"**Employee:** {t.get('employee', '—')}")
                st.markdown(f"**Issue:** {t.get('issue_summary', '—')}")
                st.markdown(
                    f"**Status:** {status_badge(t.get('status', '—'))}",
                    unsafe_allow_html=True,
                )
    else:
        st.caption("No closed tickets.")


# ---------------------------------------------------------
# PAGE: AUDIT LOG
# ---------------------------------------------------------

elif "Audit Log" in page:
    st.markdown("## 📝 Audit Log")
    st.caption(
        "Every agent interaction produces an immutable audit record. "
        "This log demonstrates full traceability of decisions, policies applied, "
        "and tickets created."
    )

    st.markdown("---")

    audit_records = load_audit_log()

    # Summary
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Records", len(audit_records))
    with col2:
        escalations = sum(1 for r in audit_records if r.get("decision") == "ESCALATE")
        st.metric("Escalations", escalations)
    with col3:
        with_ticket = sum(1 for r in audit_records if r.get("ticket_id"))
        st.metric("With Ticket", with_ticket)

    st.markdown("")

    if audit_records:
        # Show most recent first
        for record in reversed(audit_records):
            with st.expander(
                f"**{record['audit_id']}** — {record.get('employee', '—')}  •  "
                f"{record.get('timestamp', '')}"
            ):
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown(f"**Audit ID:** {record['audit_id']}")
                    st.markdown(f"**Timestamp:** {record.get('timestamp', '—')}")
                    st.markdown(f"**Employee:** {record.get('employee', '—')}")
                    st.markdown(f"**Issue:** {record.get('issue', '—')}")
                with c2:
                    st.markdown(
                        f"**Decision:** {decision_badge(record.get('decision', '—'))}",
                        unsafe_allow_html=True,
                    )
                    st.markdown(
                        f"**Priority:** {priority_badge(record.get('priority', '—'))}",
                        unsafe_allow_html=True,
                    )
                    sources = record.get("sources", [])
                    st.markdown(f"**Sources:** {', '.join(sources) if sources else '—'}")
                    st.markdown(f"**Next Action:** {record.get('next_action', '—')}")
                    ticket = record.get("ticket_id")
                    st.markdown(f"**Ticket ID:** {ticket if ticket else '—  (no ticket created)'}")
    else:
        st.info("No audit records yet. Analyze a request on the Agent page to create the first record.")

