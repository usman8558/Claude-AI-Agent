# Tasks: ERPNext Claude Chatbot

**Input**: Design documents from `/specs/001-erpnext-claude-chatbot/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are OPTIONAL - only included if explicitly requested in feature specification

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- **Custom Frappe App**: `erpnext_chatbot/` at repository root
- App module: `erpnext_chatbot/erpnext_chatbot/`
- DocTypes: `erpnext_chatbot/erpnext_chatbot/ai_chatbot/doctype/<doctype_name>/`
- Services: `erpnext_chatbot/erpnext_chatbot/services/`
- Tools: `erpnext_chatbot/erpnext_chatbot/tools/`
- API: `erpnext_chatbot/erpnext_chatbot/api/`
- Tests: `erpnext_chatbot/tests/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Initialize ERPNext development environment with bench
- [ ] T002 Create custom Frappe app `erpnext_chatbot` using `bench new-app`
- [ ] T003 [P] Add Python dependencies to erpnext_chatbot/requirements.txt (openai>=1.0.0, litellm>=1.0.0, tiktoken>=0.5.0)
- [ ] T004 [P] Install app on ERPNext site using `bench install-app erpnext_chatbot`
- [ ] T005 [P] Configure Site Config with Gemini API credentials in sites/<site>/site_config.json
- [ ] T006 [P] Set up LiteLLM proxy for development (optional for local testing)
- [ ] T007 [P] Create app module structure in erpnext_chatbot/erpnext_chatbot/ with __init__.py, hooks.py, modules.txt

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T008 Create Chat Session DocType in erpnext_chatbot/erpnext_chatbot/ai_chatbot/doctype/chat_session/chat_session.json (session_id UUID, user link, status, timestamps, company_context)
- [ ] T009 [P] Create Chat Message DocType in erpnext_chatbot/erpnext_chatbot/ai_chatbot/doctype/chat_message/chat_message.json (session_id link, role, content, timestamp, token_count)
- [ ] T010 [P] Create Chat Audit Log DocType in erpnext_chatbot/erpnext_chatbot/ai_chatbot/doctype/chat_audit_log/chat_audit_log.json (session_id, user, query_text, data_accessed JSON, permissions)
- [ ] T011 [P] Create AI Tool Call Log DocType in erpnext_chatbot/erpnext_chatbot/ai_chatbot/doctype/ai_tool_call_log/ai_tool_call_log.json (session_id, tool_name, parameters JSON, result_status)
- [ ] T012 Create Chat Session Python controller in erpnext_chatbot/erpnext_chatbot/ai_chatbot/doctype/chat_session/chat_session.py (UUID generation, user validation)
- [ ] T013 [P] Create Chat Message Python controller in erpnext_chatbot/erpnext_chatbot/ai_chatbot/doctype/chat_message/chat_message.py (session validation, token counting)
- [ ] T014 [P] Create Chat Audit Log Python controller in erpnext_chatbot/erpnext_chatbot/ai_chatbot/doctype/chat_audit_log/chat_audit_log.py (immutable logging)
- [ ] T015 [P] Create AI Tool Call Log Python controller in erpnext_chatbot/erpnext_chatbot/ai_chatbot/doctype/ai_tool_call_log/ai_tool_call_log.py (immutable logging)
- [ ] T016 Run migrations using `bench migrate` to create DocType tables
- [ ] T017 Implement session_manager.py service in erpnext_chatbot/erpnext_chatbot/services/session_manager.py (create_session, validate_session_ownership, expire_inactive_sessions)
- [ ] T018 [P] Implement rate_limiter.py service in erpnext_chatbot/erpnext_chatbot/services/rate_limiter.py (check_rate_limit using Frappe Cache with sliding window)
- [ ] T019 [P] Implement audit_logger.py service in erpnext_chatbot/erpnext_chatbot/services/audit_logger.py (log_query, log_tool_call with exception safety)
- [ ] T020 [P] Create base_tool.py in erpnext_chatbot/erpnext_chatbot/tools/base_tool.py (permission checking base class with frappe.has_permission validation)
- [ ] T021 [P] Implement permissions.py utility in erpnext_chatbot/erpnext_chatbot/utils/permissions.py (validate_permission, validate_company_access helpers)
- [ ] T022 [P] Implement sanitization.py utility in erpnext_chatbot/erpnext_chatbot/utils/sanitization.py (sanitize_user_input to prevent injection attacks)
- [ ] T023 Configure scheduled job for session expiry in erpnext_chatbot/erpnext_chatbot/hooks.py (hourly cron for expire_inactive_sessions)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Financial Data Queries (Priority: P1) 🎯 MVP

**Goal**: Enable finance managers to query financial metrics using natural language with permission enforcement

**Independent Test**: Ask predefined financial queries (revenue, profit, sales) and verify responses match ERPNext standard reports with proper permission enforcement

### Implementation for User Story 1

- [ ] T024 [P] [US1] Create finance_tools.py in erpnext_chatbot/erpnext_chatbot/tools/finance_tools.py
- [ ] T025 [US1] Implement get_financial_report tool in erpnext_chatbot/erpnext_chatbot/tools/finance_tools.py (execute P&L, Balance Sheet, Cash Flow with permission checks)
- [ ] T026 [US1] Implement report_tools.py in erpnext_chatbot/erpnext_chatbot/tools/report_tools.py (generic ERPNext report executor using frappe.desk.query_report.run)
- [ ] T027 [US1] Implement response_formatter.py utility in erpnext_chatbot/erpnext_chatbot/utils/response_formatter.py (format ERP report data for AI consumption)
- [ ] T028 [US1] Create agent_orchestrator.py service in erpnext_chatbot/erpnext_chatbot/services/agent_orchestrator.py (OpenAI client initialization, tool registration, message processing)
- [ ] T029 [US1] Register financial tools in agent_orchestrator.py using OpenAI function calling schema
- [ ] T030 [US1] Implement tool execution handler in agent_orchestrator.py (execute_tools function with audit logging)
- [ ] T031 [US1] Create chat.py API endpoint in erpnext_chatbot/erpnext_chatbot/api/chat.py
- [ ] T032 [US1] Implement create_session API endpoint in erpnext_chatbot/erpnext_chatbot/api/chat.py (whitelisted with @frappe.whitelist decorator)
- [ ] T033 [US1] Implement send_message API endpoint in erpnext_chatbot/erpnext_chatbot/api/chat.py (session validation, rate limiting, agent orchestration, audit logging)
- [ ] T034 [US1] Add permission enforcement in send_message API for financial queries (validate Accounts User role, company access)
- [ ] T035 [US1] Create basic chatbot.html UI template in erpnext_chatbot/erpnext_chatbot/ai_chatbot/page/chatbot/chatbot.html
- [ ] T036 [US1] Implement chatbot.js JavaScript in erpnext_chatbot/erpnext_chatbot/ai_chatbot/page/chatbot/chatbot.js (session creation, message sending, polling for responses)
- [ ] T037 [US1] Create chatbot.json page configuration in erpnext_chatbot/erpnext_chatbot/ai_chatbot/page/chatbot/chatbot.json (register page in ERPNext)
- [ ] T038 [US1] Add chatbot.css styles in erpnext_chatbot/erpnext_chatbot/public/css/chatbot.css (chat interface styling)
- [ ] T039 [US1] Test financial query: "Show me this month's revenue" with Accounts User role (verify response matches Sales Invoice report)
- [ ] T040 [US1] Test financial query: "What's the total revenue?" with company restrictions (verify only authorized company data returned)
- [ ] T041 [US1] Test permission denial: User without Accounts permissions queries profit and loss (verify permission error message)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Session Management and Context (Priority: P2)

**Goal**: Enable conversation continuity with context awareness across multiple messages

**Independent Test**: Start a chat session, ask a question establishing context (e.g., "Show sales for Product X"), then ask a follow-up question using pronouns ("What about last month?"). Verify the chatbot maintains context within the session.

### Implementation for User Story 2

- [ ] T042 [P] [US2] Implement get_session_history API endpoint in erpnext_chatbot/erpnext_chatbot/api/chat.py (retrieve messages for session with pagination)
- [ ] T043 [P] [US2] Implement get_user_sessions API endpoint in erpnext_chatbot/erpnext_chatbot/api/chat.py (list all sessions for current user with status filter)
- [ ] T044 [US2] Enhance agent_orchestrator.py to load last 20 messages as context in erpnext_chatbot/erpnext_chatbot/services/agent_orchestrator.py
- [ ] T045 [US2] Update send_message API to append conversation history before agent call in erpnext_chatbot/erpnext_chatbot/api/chat.py
- [ ] T046 [US2] Implement session restoration in chatbot.js (load existing session on page reload)
- [ ] T047 [US2] Add session switcher UI component in chatbot.html (dropdown to switch between active sessions)
- [ ] T048 [US2] Implement session expiry check in session_manager.py (validate session not expired before processing)
- [ ] T049 [US2] Add last_activity timestamp update in Chat Session controller (updated on every message)
- [ ] T050 [US2] Test context retention: Ask "Show sales for Product X" then "What about last month?" (verify AI interprets "last month" in context of Product X)
- [ ] T051 [US2] Test session isolation: Create two sessions, verify messages don't leak between sessions
- [ ] T052 [US2] Test session expiry: Create session, wait 24+ hours (or mock timestamp), verify session marked as expired

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Customer and Sales Insights (Priority: P3)

**Goal**: Extend chatbot to business intelligence queries for customer behavior and sales analysis

**Independent Test**: Ask customer-related queries (customer list, purchase history, inactive customers) and verify responses match data from Customer and Sales Order doctypes with proper permission checks.

### Implementation for User Story 3

- [ ] T053 [P] [US3] Create sales_tools.py in erpnext_chatbot/erpnext_chatbot/tools/sales_tools.py
- [ ] T054 [US3] Implement query_customers tool in erpnext_chatbot/erpnext_chatbot/tools/sales_tools.py (search customers by territory, customer_group with frappe.get_list and permission checks)
- [ ] T055 [US3] Implement get_sales_data tool in erpnext_chatbot/erpnext_chatbot/tools/sales_tools.py (retrieve Sales Orders and Invoices for date range with company filters)
- [ ] T056 [US3] Implement get_top_customers helper in erpnext_chatbot/erpnext_chatbot/tools/sales_tools.py (aggregate sales by customer with ordering)
- [ ] T057 [US3] Implement get_inactive_customers helper in erpnext_chatbot/erpnext_chatbot/tools/sales_tools.py (find customers with no orders in N months)
- [ ] T058 [US3] Register sales tools in agent_orchestrator.py using OpenAI function calling schema
- [ ] T059 [US3] Add permission checks for Sales User role in sales tools (validate frappe.has_permission("Customer", "read"))
- [ ] T060 [US3] Test customer query: "Show all customers in California" with Sales User role (verify results filtered by state)
- [ ] T061 [US3] Test aggregation query: "Who are our top customers this year?" (verify top 10 by order value)
- [ ] T062 [US3] Test permission denial: User without Customer permissions queries customers (verify permission error)

**Checkpoint**: At this point, User Stories 1, 2, AND 3 should all work independently

---

## Phase 6: User Story 4 - Chat History Persistence and Review (Priority: P4)

**Goal**: Enable users to review previous conversations and continue discussions from past sessions

**Independent Test**: Conduct a chat session, close it, then reopen the chatbot interface and verify the previous session appears in history with all messages intact.

### Implementation for User Story 4

- [ ] T063 [P] [US4] Implement close_session API endpoint in erpnext_chatbot/erpnext_chatbot/api/chat.py (update session status to "Closed")
- [ ] T064 [P] [US4] Implement delete_session API endpoint in erpnext_chatbot/erpnext_chatbot/api/chat.py (cascade delete session and messages, retain audit logs)
- [ ] T065 [US4] Add session list view in chatbot.html (display previous sessions with timestamps and first message preview)
- [ ] T066 [US4] Implement load_session function in chatbot.js (fetch and display all messages from selected session)
- [ ] T067 [US4] Add session deletion UI in chatbot.html (delete button with confirmation dialog)
- [ ] T068 [US4] Implement cleanup job for expired sessions in erpnext_chatbot/erpnext_chatbot/services/session_manager.py (delete sessions older than 90 days)
- [ ] T069 [US4] Configure scheduled job for session cleanup in erpnext_chatbot/erpnext_chatbot/hooks.py (daily cron for delete_old_sessions)
- [ ] T070 [US4] Test session history: Complete a chat session, reopen chatbot, verify session appears in list with correct preview
- [ ] T071 [US4] Test session restore: Open previous session from list, verify all messages load in chronological order
- [ ] T072 [US4] Test session deletion: Delete a session, verify all related messages deleted but audit logs retained
- [ ] T073 [US4] Test cleanup job: Run scheduled job, verify sessions older than retention period are deleted

**Checkpoint**: All user stories should now be independently functional

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T074 [P] Add comprehensive error handling in agent_orchestrator.py (try-except blocks with user-friendly error messages)
- [ ] T075 [P] Add error handling for Gemini API failures in agent_orchestrator.py (retry logic with exponential backoff)
- [ ] T076 [P] Implement input validation in all API endpoints (sanitize inputs before processing)
- [ ] T077 [P] Add logging for all API requests in chat.py (log user, endpoint, timestamp, response time)
- [ ] T078 [P] Add token usage tracking in agent_orchestrator.py (record tokens per message in Chat Message DocType)
- [ ] T079 [P] Optimize context window management (limit to last 20 messages, implement truncation logic)
- [ ] T080 [P] Add response time monitoring in send_message API (track processing_time_ms in Chat Message)
- [ ] T081 [P] Implement graceful degradation for rate limit errors (return clear message with retry-after time)
- [ ] T082 [P] Add unit tests for session_manager.py in erpnext_chatbot/tests/unit/test_session_manager.py
- [ ] T083 [P] Add unit tests for rate_limiter.py in erpnext_chatbot/tests/unit/test_rate_limiter.py
- [ ] T084 [P] Add unit tests for audit_logger.py in erpnext_chatbot/tests/unit/test_audit_logger.py
- [ ] T085 [P] Add unit tests for finance_tools.py in erpnext_chatbot/tests/unit/test_finance_tools.py (mock Frappe API calls)
- [ ] T086 [P] Add integration test for create_session + send_message flow in erpnext_chatbot/tests/integration/test_chat_flow.py
- [ ] T087 [P] Add permission test for unauthorized data access in erpnext_chatbot/tests/permission/test_rbac.py (verify frappe.PermissionError raised)
- [ ] T088 [P] Document API endpoints in erpnext_chatbot/README.md (usage examples for each endpoint)
- [ ] T089 [P] Add inline code comments for complex logic (agent orchestration, tool execution, permission checks)
- [ ] T090 [P] Create deployment guide in erpnext_chatbot/DEPLOYMENT.md (production setup, LiteLLM proxy configuration, site config)
- [ ] T091 Run full test suite using `bench run-tests --app erpnext_chatbot`
- [ ] T092 Verify constitutional compliance (review all data access points, confirm no direct SQL, validate audit logging complete)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-6)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3 → P4)
- **Polish (Phase 7)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable
- **User Story 4 (P4)**: Can start after Foundational (Phase 2) - Builds on session management from US2 but independently testable

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before API endpoints
- API endpoints before UI
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel (T003, T004, T005, T006, T007)
- All Foundational tasks marked [P] can run in parallel within their dependencies (T009-T015, T018-T022)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models/services within a story marked [P] can run in parallel (T024, T027 in US1; T042, T043 in US2; T053, T054, T055 in US3)
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# After Foundational phase completes, launch these tasks together for US1:

Task T024: Create finance_tools.py (parallel)
Task T027: Create response_formatter.py utility (parallel)

# Then after those complete:
Task T025: Implement get_financial_report
Task T026: Implement report_tools.py

# Then:
Task T028: Create agent_orchestrator.py
Task T029: Register financial tools
Task T030: Implement tool execution handler

# Then:
Task T031: Create chat.py API
Task T032: Implement create_session
Task T033: Implement send_message

# UI can start in parallel once API endpoints exist:
Task T035, T036, T037, T038: Create chatbot UI components (parallel)

# Finally:
Task T039-T041: Test financial queries
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T007)
2. Complete Phase 2: Foundational (T008-T023) - CRITICAL - blocks all stories
3. Complete Phase 3: User Story 1 (T024-T041)
4. **STOP and VALIDATE**: Test User Story 1 independently with financial queries
5. Deploy/demo if ready

**Result**: Working chatbot that answers financial queries with permission enforcement - core value delivered

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (adds context awareness)
4. Add User Story 3 → Test independently → Deploy/Demo (adds customer insights)
5. Add User Story 4 → Test independently → Deploy/Demo (adds history review)
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together (sequential dependencies)
2. Once Foundational is done:
   - Developer A: User Story 1 (T024-T041)
   - Developer B: User Story 2 (T042-T052)
   - Developer C: User Story 3 (T053-T062)
3. Stories complete and integrate independently
4. Everyone converges on Polish phase (T074-T092)

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- All file paths use custom Frappe app structure: `erpnext_chatbot/`
- DocType controllers must implement validation and permission checks
- API endpoints must be whitelisted with `@frappe.whitelist()` decorator
- All tools must inherit from base_tool.py for permission enforcement
- Audit logging must be exception-safe (logged even if main operation fails)
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
