---
id: 002
title: Create Implementation Plan
stage: plan
date: 2025-12-29
surface: agent
model: claude-sonnet-4-5
feature: 001-erpnext-claude-chatbot
branch: 001-erpnext-claude-chatbot
user: usman85580
command: /sp.plan
labels: ["planning", "architecture", "design", "erpnext", "chatbot"]
links:
  spec: specs/001-erpnext-claude-chatbot/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/001-erpnext-claude-chatbot/plan.md
  - specs/001-erpnext-claude-chatbot/research.md
  - specs/001-erpnext-claude-chatbot/data-model.md
  - specs/001-erpnext-claude-chatbot/contracts/api-endpoints.md
  - specs/001-erpnext-claude-chatbot/contracts/agent-tools.md
  - specs/001-erpnext-claude-chatbot/quickstart.md
  - CLAUDE.md (updated with tech stack)
tests:
  - N/A (planning artifacts)
---

## Prompt

## 3. Plan (Execution Strategy)

### Phase 1: Foundation
- Create custom Frappe app for AI chatbot.
- Define chat-related DocTypes.
- Configure Gemini API access via OpenAI-compatible endpoint.

### Phase 2: Session & Storage Layer
- Implement session creation and lifecycle management.
- Implement message persistence per session.
- Enforce user-session ownership.

### Phase 3: Agent Layer
- Define OpenAI Agent with strict instructions.
- Register ERP tools (Finance, Customers, Sales).
- Implement action routing and validation.

### Phase 4: ERP Integration
- Connect tools to ERPNext reports and ORM.
- Apply permission checks and company filters.
- Normalize ERP responses for AI summarization.

### Phase 5: User Interface
- Build ERPNext Page for chatbot.
- Implement session restoration.
- Display chat history per session.

### Phase 6: Governance & Hardening
- Add logging, error handling, and rate limits.
- Implement session expiry rules.
- Test security, permissions, and edge cases.

---

## Response snapshot

Created comprehensive implementation plan for ERPNext Claude Chatbot with complete architecture design:

**Plan Document** (`plan.md`):
- Technical Context: Python 3.10+, Frappe 15.x, OpenAI Agent SDK, Gemini 2.5 Flash via LiteLLM
- Constitution Check: All 10 principles validated and compliant
- Project Structure: Custom Frappe App architecture with DocTypes, services, tools, API, UI
- Performance targets: <5s simple queries, 50 concurrent sessions, 20 queries/min rate limit
- Complexity Tracking: No violations - all constitutional principles satisfied

**Phase 0: Research** (`research.md`):
- OpenAI Agent SDK + Gemini integration via LiteLLM proxy
- Frappe API patterns for permission-checked data access
- Session management using custom DocTypes with UUID
- Rate limiting via Frappe Cache (Redis-backed)
- UI integration via custom Frappe Page with short-polling
- Testing strategy using Frappe unittest framework

**Phase 1: Data Model** (`data-model.md`):
- Chat Session DocType: session_id (UUID), user link, status, timestamps, company context
- Chat Message DocType: session link, role, content, timestamp, token tracking
- Chat Audit Log DocType: compliance trail with data accessed, permission checks, errors
- AI Tool Call Log DocType: granular tool invocation tracking with parameters and results
- Relationships, indexes, validation rules, and retention policies defined

**Contracts**:
- API Endpoints (`api-endpoints.md`): 6 Frappe whitelisted endpoints for session/message management
- Agent Tools (`agent-tools.md`): 4 OpenAI function calling schemas for ERP data access

**Quickstart Guide** (`quickstart.md`): 10-step development setup from bench init to testing

**Constitution Compliance**: ✅ All 10 principles validated
- I & II: Frappe API-only access, no direct DB queries
- III & IV: OpenAI Agent SDK, Gemini via LiteLLM
- V: UUID session isolation with ownership validation
- VI: Dedicated DocTypes separate from transactional data
- VII: ERPNext as single source of truth (read-only chatbot)
- VIII: Comprehensive audit logging (Chat Audit Log + AI Tool Call Log)
- IX: Permission checks at every data access point
- X: Frappe conventions, type hints, docstrings, <10 cyclomatic complexity

## Outcome

- ✅ Impact: Created production-ready implementation plan with complete technical architecture, 6 design artifacts covering all phases from foundation to deployment
- 🧪 Tests: Testing strategy defined (Frappe unittest, permission tests, contract tests, integration tests)
- 📁 Files: plan.md, research.md, data-model.md, contracts/ (2 files), quickstart.md, updated CLAUDE.md
- 🔁 Next prompts: Run `/sp.tasks` to generate implementation task list organized by phase and user story
- 🧠 Reflection: Architecture successfully balances constitutional requirements (security, auditability, isolation) with ERPNext/Frappe best practices, providing clear path from development setup to production deployment

## Evaluation notes (flywheel)

- Failure modes observed: None - all constitutional gates passed, no violations detected
- Graders run and results (PASS/FAIL): Constitution Check PASS (10/10 principles compliant), Architecture Review PASS (follows Frappe conventions)
- Prompt variant (if applicable): Standard implementation planning workflow with Phase 0 (research) + Phase 1 (design artifacts)
- Next experiment (smallest change to try): Validate task generation maintains constitutional compliance and maps clearly to user stories from spec.md
