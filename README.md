# Veridian Internal Service Agent

An internal IT support agent prototype built for the **AIONOS hiring assignment — Assignment 2: Internal Service Agent (IT Support)**.

The application analyzes employee IT requests using the supplied Veridian Corp knowledge base, determines an appropriate action, surfaces relevant policy sources and historical ticket context, creates or reuses tickets when required, and maintains an audit trail.

---

## Overview

The Veridian Internal Service Agent assists employees with common internal IT support requests.

The agent follows this workflow:

```text
Employee Request
       ↓
Issue Detection
       ↓
Knowledge Base Retrieval
       ↓
Related Ticket Lookup
       ↓
Policy-Based Decision
       ↓
Resolve / Follow Up / Route / Escalate
       ↓
Ticket Service
       ↓
Audit Record
```