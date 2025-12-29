---
id: 001
title: Initialize Project Constitution
stage: constitution
date: 2025-12-29
surface: agent
model: claude-sonnet-4-5
feature: none
branch: master
user: usman85580
command: /sp.constitution
labels: ["constitution", "initialization", "governance", "principles"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - .specify/memory/constitution.md
tests:
  - N/A (documentation only)
---

## Prompt

## 1. Constitution (Governing Principles)

### Purpose
Build an AI-powered chatbot inside ERPNext that allows users to query financial and business data using natural language, while strictly enforcing ERP permissions, auditability, and data integrity.

### Core Principles
1. AI must never directly access the ERP database.
2. All ERP data access must pass through Frappe APIs or standard ERPNext reports.
3. The OpenAI Agent SDK is used for orchestration and tool calling.
4. The underlying model is Gemini 2.5 Flash, accessed via an OpenAI-compatible endpoint.
5. Each chat must be isolated using a unique session ID.
6. Chat history must be stored in dedicated DocTypes, separate from ERP transactional data.
7. Exactly one source of truth exists: ERPNext.
8. The system must be deterministic, auditable, and secure.
9. Role-based access control must be enforced at every step.
10. The solution must be production-grade, maintainable, and extensible.

## Response snapshot

Created the ERPNext Claude Chatbot Constitution (v1.0.0) with comprehensive governance framework:

**Core Principles (10)**:
- I. Database Access Isolation
- II. API-First Data Access
- III. OpenAI Agent SDK for Orchestration
- IV. Gemini 2.5 Flash via OpenAI-Compatible Endpoint
- V. Session Isolation
- VI. Dedicated Storage for Chat History
- VII. Single Source of Truth
- VIII. Deterministic and Auditable Operations
- IX. Role-Based Access Control
- X. Production-Grade Standards

**Additional Sections**:
- Architecture Constraints (Technology Stack, Security Requirements, Performance Standards, Data Governance)
- Development Workflow (Code Standards, Testing Requirements, Deployment Process)
- Governance (Amendment Process, Compliance Verification, Version Control, Complexity Justification)

All template placeholders filled with concrete values. No unresolved tokens remaining.

## Outcome

- ✅ Impact: Created initial project constitution establishing 10 core principles for ERPNext chatbot development with comprehensive governance framework
- 🧪 Tests: N/A (documentation artifact)
- 📁 Files: Created `.specify/memory/constitution.md` (v1.0.0)
- 🔁 Next prompts: Run `/sp.specify` to create feature specification adhering to constitutional principles
- 🧠 Reflection: Constitution successfully captures security-first approach with clear separation between AI layer and ERP data layer, emphasizing audit trails and permission enforcement

## Evaluation notes (flywheel)

- Failure modes observed: None - constitution template successfully populated with all required fields
- Graders run and results (PASS/FAIL): Manual validation PASS - no unresolved placeholders, all sections coherent, version control established
- Prompt variant (if applicable): Standard constitution initialization workflow
- Next experiment (smallest change to try): Validate constitution compliance during `/sp.plan` execution to ensure architectural decisions align with principles
