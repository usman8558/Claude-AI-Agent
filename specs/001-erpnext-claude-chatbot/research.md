# Research & Technology Decisions: ERPNext Claude Chatbot

**Date**: 2025-12-29
**Feature**: 001-erpnext-claude-chatbot
**Purpose**: Research technology choices and architectural patterns for implementing AI-powered chatbot in ERPNext

## Research Questions & Findings

### 1. OpenAI Agent SDK Integration with Gemini

#### Question
How to configure OpenAI Python client with custom `base_url` for Gemini-compatible endpoint? Does Gemini 2.5 Flash support function calling?

#### Decision
**Use OpenAI Python SDK v1.x with custom base URL pointing to Gemini-compatible endpoint (via proxy or native support)**

#### Rationale
- OpenAI Python SDK supports custom `base_url` parameter: `OpenAI(base_url="https://gemini-api-endpoint.com/v1", api_key="...")`
- Gemini 2.5 Flash supports function calling (tool usage) natively through Google AI SDK
- OpenAI-compatible endpoints for Gemini can be achieved via:
  - **Option A**: Direct Google AI SDK with function calling (preferred for native support)
  - **Option B**: LiteLLM proxy converting OpenAI format to Gemini format
  - **Option C**: Custom wrapper translating OpenAI agent SDK calls to Gemini API

**Selected Approach**: Use **LiteLLM proxy** for maximum compatibility
- LiteLLM provides OpenAI-compatible endpoint that translates to Gemini API
- Preserves OpenAI Agent SDK usage as required by constitution
- Configuration: `base_url="http://localhost:4000"` (LiteLLM proxy), API key for Gemini

#### Alternatives Considered
- **Direct Gemini SDK**: Rejected - violates Constitution Principle III (must use OpenAI Agent SDK)
- **Custom wrapper**: Rejected - adds unnecessary complexity and maintenance burden

#### Context Window & Token Limits
- **Gemini 2.5 Flash**: 1M token context window, 8K output tokens
- **Function calling**: Supported with up to 128 function definitions per request
- **Recommendation**: Limit chat history to last 20 messages (~4000 tokens) + function definitions (~2000 tokens) = ~6000 tokens total per request

---

### 2. Frappe API Best Practices

#### Question
Standard patterns for permission-checked data access? How to execute ERPNext standard reports programmatically?

#### Decision
**Use Frappe's ORM methods with explicit permission validation for all data access**

#### Rationale
- **Permission-checked queries**: Always wrap with `frappe.has_permission()` before access
  ```python
  if frappe.has_permission("Customer", ptype="read", user=frappe.session.user):
      customers = frappe.get_list("Customer", filters={"territory": "US"})
  else:
      raise frappe.PermissionError
  ```

- **ERPNext report execution**:
  ```python
  from frappe.desk.query_report import run

  result = run("Profit and Loss Statement", filters={
      "company": "Company A",
      "from_date": "2024-01-01",
      "to_date": "2024-12-31"
  })
  ```
  - Reports inherit permissions from their DocType definitions
  - No additional permission checks needed if report access is validated

- **Whitelisted API endpoints**: Use `@frappe.whitelist()` decorator
  ```python
  @frappe.whitelist()
  def send_message(session_id, message):
      # Validate session ownership
      session = frappe.get_doc("Chat Session", session_id)
      if session.user != frappe.session.user:
          frappe.throw("Unauthorized", frappe.PermissionError)
      # Process message...
  ```

#### Alternatives Considered
- **Raw SQL queries**: Rejected - violates Constitution Principles I & II
- **Direct ORM without permission checks**: Rejected - violates Constitution Principle IX

---

### 3. Session Management in Frappe

#### Question
How to store session state securely? Session expiry patterns? Concurrent access handling?

#### Decision
**Use custom DocType `Chat Session` with UUID primary key, user link, and scheduled cleanup job**

#### Rationale
- **Session creation**:
  ```python
  import uuid

  session = frappe.get_doc({
      "doctype": "Chat Session",
      "name": str(uuid.uuid4()),  # UUID as primary key
      "user": frappe.session.user,
      "status": "Active",
      "created_at": frappe.utils.now(),
      "last_activity": frappe.utils.now()
  }).insert()
  ```

- **Session validation**:
  ```python
  def validate_session_ownership(session_id):
      session = frappe.get_doc("Chat Session", session_id)
      if session.user != frappe.session.user:
          raise frappe.PermissionError("Session belongs to different user")
      if session.status == "Expired":
          raise frappe.ValidationError("Session has expired")
      return session
  ```

- **Session expiry**: Frappe scheduled job (cron-style)
  ```python
  # In hooks.py
  scheduler_events = {
      "hourly": [
          "erpnext_chatbot.services.session_manager.expire_inactive_sessions"
      ]
  }

  # In session_manager.py
  def expire_inactive_sessions():
      from frappe.utils import add_to_date, now
      expiry_threshold = add_to_date(now(), hours=-24)

      frappe.db.sql("""
          UPDATE `tabChat Session`
          SET status = 'Expired'
          WHERE last_activity < %s AND status = 'Active'
      """, (expiry_threshold,))
      frappe.db.commit()
  ```

- **Concurrent access**: Frappe handles locking automatically via `FOR UPDATE` in transactions
  - No additional locking needed for normal operations
  - Use `frappe.db.begin()` and `frappe.db.commit()` for atomic multi-document updates

#### Alternatives Considered
- **Redis-based sessions**: Rejected - adds external dependency, Frappe DocTypes sufficient
- **Auto-incrementing IDs**: Rejected - UUID provides better security (non-guessable)

---

### 4. Rate Limiting in Frappe

#### Question
Frappe's built-in rate limiting mechanisms? Custom implementation patterns?

#### Decision
**Implement custom rate limiter using Frappe Cache (Redis-backed) with sliding window algorithm**

#### Rationale
- Frappe provides `frappe.cache()` which uses Redis when available, falls back to memory
- Sliding window rate limiting implementation:
  ```python
  from frappe.utils import now_datetime
  import time

  def check_rate_limit(user, limit=20, window=60):
      """
      Args:
          user: Username to rate limit
          limit: Max requests per window (default 20)
          window: Time window in seconds (default 60)

      Raises:
          frappe.RateLimitExceededError if limit exceeded
      """
      cache_key = f"rate_limit:{user}"
      cache = frappe.cache()

      current_time = time.time()
      timestamps = cache.get(cache_key) or []

      # Remove timestamps outside current window
      timestamps = [ts for ts in timestamps if current_time - ts < window]

      if len(timestamps) >= limit:
          raise frappe.RateLimitExceededError(
              f"Rate limit exceeded: {limit} requests per {window} seconds"
          )

      # Add current timestamp
      timestamps.append(current_time)
      cache.set(cache_key, timestamps, expires_in_sec=window)
  ```

- **Usage in API endpoint**:
  ```python
  @frappe.whitelist()
  def send_message(session_id, message):
      check_rate_limit(frappe.session.user, limit=20, window=60)
      # Process message...
  ```

#### Alternatives Considered
- **Database-based rate limiting**: Rejected - slower, unnecessary DB load for transient data
- **Frappe's built-in rate limiter**: Limited functionality, doesn't support per-user sliding windows

---

### 5. UI Integration Patterns

#### Question
How to add custom pages to ERPNext navigation? Real-time chat UI patterns? WebSocket vs. polling?

#### Decision
**Create custom Frappe Page with JavaScript chat UI, use short-polling (3-second intervals) for message updates**

#### Rationale
- **Custom Page creation**:
  - Define in `erpnext_chatbot/ai_chatbot/page/chatbot/`
  - Frappe automatically registers and adds to workspace
  - Configuration in `chatbot.json`:
    ```json
    {
      "name": "Chatbot",
      "title": "AI Chatbot",
      "icon": "fa fa-comments",
      "module": "AI Chatbot",
      "standard": "Yes",
      "page_name": "chatbot"
    }
    ```

- **Chat UI pattern**: Single-page application with message list and input field
  - Use Frappe's built-in `frappe.call()` for API requests
  - Message list updates via polling every 3 seconds
  - Optimistic UI: Show user messages immediately, poll for assistant responses

- **Polling vs. WebSocket**:
  - **Selected**: Short-polling (3-second intervals)
    - Simple implementation, no additional infrastructure
    - Acceptable latency for chatbot use case
    - Frappe's HTTP caching reduces server load
  - **Rejected**: WebSockets
    - Requires additional server configuration (Socket.IO, channels)
    - Increases deployment complexity
    - Overkill for chatbot response times (5-15 seconds per query)

#### JavaScript Implementation Sketch
```javascript
frappe.pages['chatbot'].on_page_load = function(wrapper) {
    let page = frappe.ui.make_app_page({
        parent: wrapper,
        title: 'AI Chatbot',
        single_column: true
    });

    let session_id = null;
    let poll_interval = null;

    // Initialize session
    frappe.call({
        method: 'erpnext_chatbot.api.chat.create_session',
        callback: function(r) {
            session_id = r.message.session_id;
            start_polling();
        }
    });

    // Poll for new messages
    function start_polling() {
        poll_interval = setInterval(() => {
            frappe.call({
                method: 'erpnext_chatbot.api.chat.get_new_messages',
                args: {session_id: session_id, after_timestamp: last_message_time},
                callback: function(r) {
                    append_messages(r.message);
                }
            });
        }, 3000);
    }
};
```

#### Alternatives Considered
- **Embedded widget in existing pages**: Rejected - dedicated page provides better UX for conversations
- **Real-time updates (Socket.IO)**: Rejected - polling sufficient for chatbot latency requirements

---

### 6. Testing Strategy

#### Question
Frappe test framework conventions? Mocking patterns? Permission testing?

#### Decision
**Use Frappe's unittest framework with `frappe.set_user()` for permission testing, mock external API calls**

#### Rationale
- **Test structure**: Follow Frappe's conventions
  ```python
  # In test_chat_session.py
  import frappe
  import unittest

  class TestChatSession(unittest.TestCase):
      def setUp(self):
          # Create test user with specific roles
          self.test_user = frappe.get_doc({
              "doctype": "User",
              "email": "test@example.com",
              "roles": [{"role": "Accounts User"}]
          }).insert()

          frappe.set_user(self.test_user.email)

      def tearDown(self):
          frappe.set_user("Administrator")
          frappe.delete_doc("User", self.test_user.email)

      def test_create_session(self):
          session = create_chat_session()
          self.assertEqual(session.user, self.test_user.email)
          self.assertEqual(session.status, "Active")
  ```

- **Permission testing pattern**:
  ```python
  def test_unauthorized_session_access(self):
      # Create session as user A
      frappe.set_user("userA@example.com")
      session = create_chat_session()

      # Try to access as user B
      frappe.set_user("userB@example.com")
      with self.assertRaises(frappe.PermissionError):
          get_session_messages(session.name)
  ```

- **Mocking external APIs** (Gemini/OpenAI):
  ```python
  from unittest.mock import patch, Mock

  def test_agent_query(self):
      mock_response = Mock()
      mock_response.choices = [Mock(message=Mock(content="Test response"))]

      with patch('openai.ChatCompletion.create', return_value=mock_response):
          response = send_message(session_id, "What is our revenue?")
          self.assertIn("Test response", response)
  ```

- **Test categories**:
  - **Unit tests**: `tests/unit/` - Services, utilities, tools (mocked dependencies)
  - **Integration tests**: `tests/integration/` - API endpoints, DocType workflows
  - **Contract tests**: `tests/contract/` - AI tool input/output schemas
  - **Permission tests**: `tests/permission/` - RBAC enforcement across all operations

#### Alternatives Considered
- **pytest instead of unittest**: Rejected - Frappe's test runner expects unittest.TestCase
- **Integration tests against live Gemini API**: Rejected - slow, costly, non-deterministic

---

## Technology Stack Summary

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| **Language** | Python 3.10+ | Frappe Framework requirement |
| **Framework** | Frappe 15.x / ERPNext 15.x | Platform for custom app development |
| **AI Orchestration** | OpenAI Agent SDK (Python client) | Constitutional requirement (Principle III) |
| **AI Model** | Gemini 2.5 Flash via LiteLLM proxy | Constitutional requirement (Principle IV) |
| **Model Proxy** | LiteLLM | OpenAI-compatible endpoint for Gemini |
| **Data Access** | Frappe ORM + Report API | Constitutional requirement (Principles I & II) |
| **Storage** | MariaDB/PostgreSQL (via Frappe) | Standard ERPNext database |
| **Session Management** | Frappe DocTypes (Chat Session) | Native integration, no external dependencies |
| **Rate Limiting** | Frappe Cache (Redis-backed) | Built-in caching infrastructure |
| **UI Framework** | Frappe's JavaScript framework | Native ERPNext UI integration |
| **UI Update Pattern** | Short-polling (3s intervals) | Simple, sufficient for chatbot latency |
| **Testing** | Frappe unittest framework | Native test runner with Frappe context |
| **Audit Logging** | Frappe DocTypes (Chat Audit Log) | Constitutional requirement (Principle VIII) |

---

## Implementation Recommendations

### 1. Development Environment Setup
- Use Frappe's `bench` for development (`bench new-app erpnext_chatbot`)
- Install LiteLLM proxy for local development: `pip install litellm[proxy]`
- Configure Site Config with Gemini API key (encrypted field)

### 2. Dependency Management
- Add to `requirements.txt`:
  ```
  openai>=1.0.0
  litellm>=1.0.0  # For development/testing
  ```

### 3. Security Best Practices
- Store Gemini API key in Site Config's encrypted fields
- Validate session ownership before every operation
- Sanitize all user inputs before passing to AI model
- Log all tool calls with parameters for audit trail

### 4. Performance Optimization
- Limit chat history to last 20 messages per session
- Use Frappe's caching for frequently accessed data (customer lists, etc.)
- Implement exponential backoff for Gemini API retries
- Monitor token usage per session to prevent runaway costs

### 5. Testing Strategy
- Write tests for each tool before implementation (TDD approach)
- Permission tests for every data access path
- Mock external API calls in all automated tests
- Integration tests against test ERPNext instance with sample data

---

## Risks & Mitigation

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Gemini API rate limits exceeded | High | Medium | Implement queue with retry logic; cache responses where appropriate |
| Permission bypass in tool implementation | Critical | Low | Mandatory code review for all tools; comprehensive permission test suite |
| Session hijacking via UUID guessing | High | Very Low | Use cryptographically secure UUIDs (Python's uuid.uuid4()); validate ownership |
| Chat history storage growth | Medium | High | Implement automated cleanup job; enforce 90-day retention policy |
| LiteLLM proxy single point of failure | High | Low | Deploy redundant proxies; implement fallback to direct Gemini SDK if needed |
| UI polling overwhelming server | Medium | Low | Implement exponential backoff on errors; rate limit polling endpoints |

---

## Open Questions (For Review)

1. **Gemini API endpoint configuration**: Should we use LiteLLM proxy in production or direct Gemini API with custom wrapper?
   - **Recommendation**: LiteLLM for development, evaluate direct API for production (lower latency)

2. **Chat session timeout**: 24 hours reasonable, or should it vary by user role?
   - **Recommendation**: Start with 24 hours for all users, make configurable via Site Config later

3. **UI placement**: Dedicated page vs. sidebar widget available from all pages?
   - **Recommendation**: Start with dedicated page (simpler), add sidebar widget in Phase 2 if requested

4. **Audit log retention**: Should it match chat history (90 days) or longer for compliance?
   - **Recommendation**: Retain audit logs for 1 year (compliance standard), separate from chat cleanup

---

## Next Phase: Data Model Design

With technology decisions finalized, proceed to Phase 1: Design Artifacts
- **data-model.md**: DocType field definitions and relationships
- **contracts/**: API endpoints and agent tool schemas
- **quickstart.md**: Step-by-step development environment setup

All decisions in this document are validated against constitutional principles and ready for implementation.
