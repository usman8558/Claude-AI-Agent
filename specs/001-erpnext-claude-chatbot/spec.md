# Feature Specification: ERPNext Claude Chatbot

**Feature Branch**: `001-erpnext-claude-chatbot`
**Created**: 2025-12-29
**Status**: Draft
**Input**: User description: "AI-powered chatbot inside ERPNext for querying financial and business data with natural language"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Financial Data Queries (Priority: P1)

A finance manager needs to quickly retrieve financial metrics without navigating through multiple ERPNext reports. They open the chatbot, ask "What was our profit for Q4 2024?", and receive an accurate answer with the data they're authorized to see.

**Why this priority**: This is the core value proposition - enabling natural language queries for financial data. Without this, the chatbot has no purpose.

**Independent Test**: Can be fully tested by asking predefined financial queries (revenue, profit, sales) and verifying responses match ERPNext standard reports with proper permission enforcement.

**Acceptance Scenarios**:

1. **Given** a logged-in user with Accounts User role, **When** they ask "Show me this month's revenue", **Then** the chatbot retrieves data from Sales Invoice report and displays the revenue figure for the current month
2. **Given** a user with limited company access (Company A only), **When** they ask "What's the total revenue?", **Then** the chatbot returns revenue for Company A only, respecting the user's company restrictions
3. **Given** a user without Accounts read permissions, **When** they ask "Show profit and loss", **Then** the chatbot responds with a permission error explaining they lack access to financial data
4. **Given** a user asks "Show customer payments in December", **When** the chatbot processes the query, **Then** it retrieves Payment Entry records for December using standard ERPNext reports

---

### User Story 2 - Session Management and Context (Priority: P2)

A user has an ongoing conversation with the chatbot about sales performance. They ask "What were our top 5 customers last quarter?", then follow up with "How much did they spend?" - expecting the chatbot to remember the context of "top 5 customers" from the previous question.

**Why this priority**: Context awareness makes conversations natural and efficient. Users shouldn't have to repeat information across queries.

**Independent Test**: Start a chat session, ask a question establishing context (e.g., "Show sales for Product X"), then ask a follow-up question using pronouns ("What about last month?"). Verify the chatbot maintains context within the session.

**Acceptance Scenarios**:

1. **Given** a user starts a new chat session, **When** they ask their first question, **Then** a unique session ID is created and linked to the logged-in user
2. **Given** an active chat session with conversation history, **When** the user asks a follow-up question referencing previous context, **Then** the chatbot uses the session history to interpret the question correctly
3. **Given** multiple open chat sessions by the same user, **When** they switch between sessions, **Then** each session maintains its own independent conversation history and context
4. **Given** a chat session that has been inactive for 24 hours, **When** the user returns to it, **Then** the session is either resumed with full context or marked as expired (configurable)

---

### User Story 3 - Customer and Sales Insights (Priority: P3)

A sales manager wants to understand customer behavior. They ask "Which customers haven't ordered in the last 6 months?" and the chatbot queries customer transaction history to provide a list of inactive customers.

**Why this priority**: Extends the chatbot's value beyond basic financial reporting to business intelligence and actionable insights.

**Independent Test**: Ask customer-related queries (customer list, purchase history, inactive customers) and verify responses match data from Customer and Sales Order doctypes with proper permission checks.

**Acceptance Scenarios**:

1. **Given** a user with Sales User role, **When** they ask "Show all customers in California", **Then** the chatbot queries the Customer doctype filtered by state and returns matching results
2. **Given** a user asks "Who are our top customers this year?", **When** the chatbot processes the query, **Then** it retrieves Sales Order data, aggregates by customer, and returns the top 10 customers by order value
3. **Given** a user without Customer read permissions, **When** they ask customer-related questions, **Then** the chatbot returns a permission error
4. **Given** a user asks "Which customers have overdue invoices?", **When** the chatbot processes the query, **Then** it uses standard ERPNext reports (Accounts Receivable) to identify customers with overdue balances

---

### User Story 4 - Chat History Persistence and Review (Priority: P4)

A user wants to review previous conversations with the chatbot to reference past answers or continue a discussion from a previous day. They access their chat history and can browse past sessions.

**Why this priority**: Enables users to build on previous insights and creates an audit trail of AI interactions with business data.

**Independent Test**: Conduct a chat session, close it, then reopen the chatbot interface and verify the previous session appears in history with all messages intact.

**Acceptance Scenarios**:

1. **Given** a completed chat session, **When** the user reopens the chatbot, **Then** they see a list of previous sessions with timestamps and preview of the first message
2. **Given** a user selects a previous session from history, **When** they click to open it, **Then** the full conversation loads with all messages in chronological order
3. **Given** a chat history older than the retention period (90 days default), **When** the system runs cleanup, **Then** expired chat sessions are deleted according to the retention policy
4. **Given** a user requests to delete their chat history, **When** they confirm deletion, **Then** all their chat sessions are permanently removed from the database

---

### Edge Cases

- What happens when a user asks a question about data they don't have permission to access? (Permission error with clear explanation)
- How does the system handle ambiguous queries like "Show me sales"? (Chatbot asks clarifying questions: which period? which product? all companies?)
- What happens if the Gemini API endpoint is unreachable? (Error message indicating AI service is temporarily unavailable, with fallback to manual report access)
- How does the chatbot respond to non-business queries like "What's the weather?"? (Politely explains it's designed for ERPNext business data queries only)
- What happens when a query would return thousands of records (e.g., "Show all invoices")? (Implements pagination or asks user to narrow the query by date/customer)
- How does the system handle concurrent sessions from the same user? (Each session remains independent with its own context)
- What happens if a user's permissions change mid-session? (Next query respects updated permissions; optionally warn user of permission changes)

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide a chatbot UI widget accessible from within ERPNext's main interface
- **FR-002**: System MUST create a unique session ID for each new chat conversation
- **FR-003**: System MUST link each chat session to the authenticated ERPNext user
- **FR-004**: System MUST use the OpenAI Agent SDK for orchestrating AI interactions and tool calling
- **FR-005**: System MUST connect to Gemini 2.5 Flash model via an OpenAI-compatible endpoint
- **FR-006**: System MUST access ERPNext data exclusively through Frappe REST APIs or standard ERPNext reports
- **FR-007**: System MUST enforce user permissions for all data access using Frappe's `has_permission()` checks
- **FR-008**: System MUST enforce company restrictions for all financial queries (users see only their authorized companies)
- **FR-009**: System MUST store chat sessions in a dedicated DocType (e.g., "Chat Session") separate from transactional data
- **FR-010**: System MUST store individual chat messages in a dedicated DocType (e.g., "Chat Message") linked to the session
- **FR-011**: System MUST audit log all AI interactions including user, timestamp, query, response, and data accessed
- **FR-012**: System MUST NOT generate or execute raw SQL queries under any circumstances
- **FR-013**: System MUST sanitize all user inputs to prevent injection attacks before processing
- **FR-014**: System MUST implement session expiration after a configurable period of inactivity (default: 24 hours)
- **FR-015**: System MUST support resuming active (non-expired) chat sessions
- **FR-016**: System MUST provide clear error messages when queries cannot be answered due to permissions, invalid data, or system errors
- **FR-017**: System MUST respect ERPNext's existing authentication and session management
- **FR-018**: System MUST retrieve financial data (Profit & Loss, Revenue, Expenses) using standard ERPNext reports (Profit and Loss Statement, General Ledger)
- **FR-019**: System MUST retrieve sales data (Sales Orders, Invoices, Customers) using standard ERPNext reports and Frappe ORM queries on Sales Order and Sales Invoice doctypes
- **FR-020**: System MUST implement rate limiting to prevent abuse (default: 20 queries per minute per user)
- **FR-021**: System MUST maintain conversation context within a session to handle follow-up questions
- **FR-022**: System MUST allow users to explicitly close/end a chat session
- **FR-023**: System MUST implement data retention policy for chat history (default: 90 days, configurable per workspace)
- **FR-024**: System MUST provide users ability to delete their own chat history on request
- **FR-025**: System MUST mask sensitive financial data in chat logs unless user has explicit view permissions for that data type

### Key Entities *(include if feature involves data)*

- **Chat Session**: Represents a conversation thread between a user and the chatbot. Attributes include: unique session ID, linked user, creation timestamp, last activity timestamp, session status (active/closed/expired), company context.
- **Chat Message**: Represents a single message in a conversation. Attributes include: linked session ID, message type (user/assistant), message content, timestamp, token count, AI model used, processing time.
- **Chat Audit Log**: Represents audit trail for AI interactions. Attributes include: session ID, user, timestamp, query text, response summary, data accessed (doctype/report names), permission checks performed, error/success status.
- **AI Tool Call Log**: Represents each tool invocation by the AI agent. Attributes include: session ID, tool name, tool parameters, execution time, result status, data returned (summary), errors encountered.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can receive accurate answers to financial queries (revenue, profit, expenses) in under 5 seconds for simple queries (single period, single company)
- **SC-002**: System correctly enforces permissions - users attempting to access unauthorized data receive clear permission errors 100% of the time
- **SC-003**: System handles at least 50 concurrent chat sessions without performance degradation (response time remains under 10 seconds)
- **SC-004**: 95% of user queries about standard ERPNext data (customers, invoices, sales orders) return accurate results matching standard report outputs
- **SC-005**: System maintains 99.9% uptime during business hours (excluding scheduled maintenance and external API failures)
- **SC-006**: Chatbot successfully maintains context for follow-up questions within a session at least 90% of the time
- **SC-007**: Zero incidents of unauthorized data access or permission bypass in production
- **SC-008**: All AI interactions are successfully audit-logged with complete traceability (user, query, data accessed)
- **SC-009**: Users can complete common tasks (check revenue, view top customers, find overdue invoices) 50% faster than using standard ERPNext navigation
- **SC-010**: Chat history is accessible and intact for the full retention period (90 days default) with no data loss
- **SC-011**: System consumes no more than 20% of server resources (CPU, memory) under normal load conditions
- **SC-012**: Response accuracy (answers matching ERPNext report data) exceeds 95% for queries within the chatbot's defined scope

## Assumptions

- ERPNext instance is version 14 or higher with standard Frappe framework
- OpenAI-compatible API endpoint for Gemini 2.5 Flash is available and accessible from the ERPNext server
- API credentials for the AI model endpoint are securely stored in ERPNext's encrypted configuration
- Users have stable internet connectivity for chatbot interactions
- ERPNext standard reports (Profit and Loss Statement, General Ledger, Sales Register, etc.) are configured and functional
- User roles and permissions are properly configured in ERPNext before chatbot deployment
- The chatbot's scope is limited to read-only queries; it does not create, update, or delete ERPNext transactional data
- Natural language processing quality depends on the underlying AI model (Gemini 2.5 Flash) capabilities
- The chatbot UI will be implemented as a custom ERPNext app/module following Frappe framework conventions

## Out of Scope

- Direct database queries or SQL generation
- Creating, updating, or deleting ERPNext transactional documents (read-only interface)
- Integration with external CRM, accounting, or business intelligence systems
- Voice-based chat interactions (text-only interface)
- Real-time alerts or proactive notifications (user must initiate queries)
- Multi-language support (English only in initial version)
- Complex analytical queries requiring custom report generation (limited to standard ERPNext reports)
- Training or fine-tuning the AI model (uses Gemini 2.5 Flash as-is)
- Mobile-specific app or interface (web UI only, responsive design assumed)
