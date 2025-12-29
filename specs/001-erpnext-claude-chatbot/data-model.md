# Data Model: ERPNext Claude Chatbot

**Date**: 2025-12-29
**Feature**: 001-erpnext-claude-chatbot
**Purpose**: Define DocType schemas and data relationships for chat management

## Overview

This document defines four custom DocTypes for managing AI chatbot interactions in ERPNext:

1. **Chat Session** - Conversation threads between users and AI
2. **Chat Message** - Individual messages within sessions
3. **Chat Audit Log** - Compliance audit trail for AI operations
4. **AI Tool Call Log** - Detailed log of agent tool invocations

All DocTypes follow Frappe framework conventions and enforce constitutional principles (session isolation, dedicated storage, auditability).

---

## 1. Chat Session DocType

### Purpose
Represents a conversation thread between a user and the AI chatbot. Each session is isolated, linked to a single user, and maintains its own context.

### DocType Configuration

```json
{
  "name": "Chat Session",
  "module": "AI Chatbot",
  "doctype": "DocType",
  "engine": "InnoDB",
  "is_submittable": 0,
  "track_changes": 1,
  "autoname": "Prompt",
  "fields": [
    {
      "fieldname": "session_id",
      "label": "Session ID",
      "fieldtype": "Data",
      "reqd": 1,
      "unique": 1,
      "read_only": 1,
      "description": "UUID identifying this chat session"
    },
    {
      "fieldname": "user",
      "label": "User",
      "fieldtype": "Link",
      "options": "User",
      "reqd": 1,
      "read_only": 1,
      "description": "ERPNext user who owns this session"
    },
    {
      "fieldname": "status",
      "label": "Status",
      "fieldtype": "Select",
      "options": "Active\nClosed\nExpired",
      "default": "Active",
      "reqd": 1,
      "description": "Session lifecycle status"
    },
    {
      "fieldname": "created_at",
      "label": "Created At",
      "fieldtype": "Datetime",
      "reqd": 1,
      "read_only": 1,
      "description": "Session creation timestamp"
    },
    {
      "fieldname": "last_activity",
      "label": "Last Activity",
      "fieldtype": "Datetime",
      "reqd": 1,
      "description": "Timestamp of last message in session"
    },
    {
      "fieldname": "company_context",
      "label": "Company Context",
      "fieldtype": "Link",
      "options": "Company",
      "description": "Default company for ERP queries in this session"
    },
    {
      "fieldname": "message_count",
      "label": "Message Count",
      "fieldtype": "Int",
      "default": 0,
      "read_only": 1,
      "description": "Total messages in this session"
    },
    {
      "fieldname": "total_tokens",
      "label": "Total Tokens",
      "fieldtype": "Int",
      "default": 0,
      "read_only": 1,
      "description": "Cumulative token usage for this session"
    }
  ],
  "permissions": [
    {
      "role": "System Manager",
      "read": 1,
      "write": 1,
      "create": 1,
      "delete": 1
    },
    {
      "role": "All",
      "read": 1,
      "write": 1,
      "create": 1,
      "delete": 1,
      "if_owner": 1
    }
  ]
}
```

### Field Descriptions

| Field | Type | Purpose | Validation Rules |
|-------|------|---------|------------------|
| `session_id` | Data (UUID) | Unique session identifier | UUID v4 format, immutable |
| `user` | Link (User) | Session owner | Must match creating user, immutable |
| `status` | Select | Lifecycle state | Active/Closed/Expired |
| `created_at` | Datetime | Creation timestamp | Auto-set on insert, immutable |
| `last_activity` | Datetime | Last message time | Updated on every message |
| `company_context` | Link (Company) | Default company for queries | Optional, validates user has company access |
| `message_count` | Int | Total messages | Auto-incremented, read-only |
| `total_tokens` | Int | Token usage tracking | Auto-incremented, read-only |

### Business Rules

1. **Session Creation**:
   - `session_id` generated as UUID v4 on insert
   - `user` set to `frappe.session.user` automatically
   - `created_at` and `last_activity` set to current timestamp
   - `status` defaults to "Active"
   - `company_context` set to user's default company if not specified

2. **Session Validation**:
   - User can only access their own sessions (enforced by `if_owner` permission)
   - Cannot modify `session_id`, `user`, or `created_at` after creation
   - Cannot reactivate `Expired` sessions

3. **Session Expiry** (via scheduled job):
   - Sessions with `last_activity` > 24 hours ago → status changed to "Expired"
   - Expired sessions cannot receive new messages
   - Users can manually close sessions (status → "Closed")

4. **Deletion Policy**:
   - Sessions older than 90 days (configurable) deleted automatically
   - Deleting session cascades to related messages, audit logs, tool call logs

---

## 2. Chat Message DocType

### Purpose
Represents individual messages within a chat session. Messages have a role (user or assistant) and store the content, timestamp, and token usage.

### DocType Configuration

```json
{
  "name": "Chat Message",
  "module": "AI Chatbot",
  "doctype": "DocType",
  "engine": "InnoDB",
  "is_submittable": 0,
  "track_changes": 0,
  "autoname": "hash",
  "fields": [
    {
      "fieldname": "session_id",
      "label": "Session ID",
      "fieldtype": "Link",
      "options": "Chat Session",
      "reqd": 1,
      "read_only": 1,
      "description": "Parent chat session"
    },
    {
      "fieldname": "role",
      "label": "Role",
      "fieldtype": "Select",
      "options": "user\nassistant\nsystem",
      "reqd": 1,
      "read_only": 1,
      "description": "Message sender role"
    },
    {
      "fieldname": "content",
      "label": "Content",
      "fieldtype": "Long Text",
      "reqd": 1,
      "read_only": 1,
      "description": "Message text content"
    },
    {
      "fieldname": "timestamp",
      "label": "Timestamp",
      "fieldtype": "Datetime",
      "reqd": 1,
      "read_only": 1,
      "description": "Message creation time"
    },
    {
      "fieldname": "token_count",
      "label": "Token Count",
      "fieldtype": "Int",
      "default": 0,
      "read_only": 1,
      "description": "Tokens consumed by this message"
    },
    {
      "fieldname": "model_used",
      "label": "Model Used",
      "fieldtype": "Data",
      "read_only": 1,
      "description": "AI model name (e.g., 'gemini-2.5-flash')"
    },
    {
      "fieldname": "processing_time_ms",
      "label": "Processing Time (ms)",
      "fieldtype": "Int",
      "read_only": 1,
      "description": "Time taken to generate response"
    }
  ],
  "permissions": [
    {
      "role": "System Manager",
      "read": 1,
      "write": 1,
      "create": 1,
      "delete": 1
    },
    {
      "role": "All",
      "read": 1,
      "create": 1,
      "if_owner": 1,
      "permlevel": 0
    }
  ]
}
```

### Field Descriptions

| Field | Type | Purpose | Validation Rules |
|-------|------|---------|------------------|
| `session_id` | Link (Chat Session) | Parent session | Must exist, user must own session |
| `role` | Select | Sender type | user/assistant/system |
| `content` | Long Text | Message text | Required, max 10,000 characters |
| `timestamp` | Datetime | Creation time | Auto-set on insert, immutable |
| `token_count` | Int | Token usage | Calculated after AI response |
| `model_used` | Data | AI model identifier | Set for assistant messages only |
| `processing_time_ms` | Int | Response latency | Set for assistant messages only |

### Business Rules

1. **Message Creation**:
   - User messages: Created immediately when user submits query
   - Assistant messages: Created after AI model responds
   - System messages: Created for errors, warnings, context changes
   - `timestamp` auto-set to current time
   - Session's `last_activity` updated to message timestamp
   - Session's `message_count` incremented

2. **Session Validation**:
   - Cannot add messages to "Closed" or "Expired" sessions
   - User can only add messages to sessions they own
   - Messages are immutable after creation (no edits)

3. **Token Accounting**:
   - User messages: Token count estimated on insert (using tiktoken or similar)
   - Assistant messages: Token count from AI model response metadata
   - Session's `total_tokens` updated when message created

4. **Context Window Management**:
   - When loading session history for AI context, fetch last 20 messages only
   - Older messages retained for audit but not sent to AI model

---

## 3. Chat Audit Log DocType

### Purpose
Comprehensive audit trail for compliance. Logs every AI interaction with details about the query, response, and data accessed.

### DocType Configuration

```json
{
  "name": "Chat Audit Log",
  "module": "AI Chatbot",
  "doctype": "DocType",
  "engine": "InnoDB",
  "is_submittable": 0,
  "track_changes": 0,
  "autoname": "hash",
  "fields": [
    {
      "fieldname": "session_id",
      "label": "Session ID",
      "fieldtype": "Link",
      "options": "Chat Session",
      "reqd": 1,
      "read_only": 1,
      "description": "Associated chat session"
    },
    {
      "fieldname": "user",
      "label": "User",
      "fieldtype": "Link",
      "options": "User",
      "reqd": 1,
      "read_only": 1,
      "description": "User who made the query"
    },
    {
      "fieldname": "timestamp",
      "label": "Timestamp",
      "fieldtype": "Datetime",
      "reqd": 1,
      "read_only": 1,
      "description": "When the query was processed"
    },
    {
      "fieldname": "query_text",
      "label": "Query Text",
      "fieldtype": "Long Text",
      "reqd": 1,
      "read_only": 1,
      "description": "User's original question"
    },
    {
      "fieldname": "response_summary",
      "label": "Response Summary",
      "fieldtype": "Text",
      "read_only": 1,
      "description": "First 500 chars of AI response"
    },
    {
      "fieldname": "data_accessed",
      "label": "Data Accessed",
      "fieldtype": "JSON",
      "read_only": 1,
      "description": "List of DocTypes/reports accessed"
    },
    {
      "fieldname": "permission_checks_passed",
      "label": "Permission Checks Passed",
      "fieldtype": "Check",
      "default": 0,
      "read_only": 1,
      "description": "Whether all permission validations succeeded"
    },
    {
      "fieldname": "error_occurred",
      "label": "Error Occurred",
      "fieldtype": "Check",
      "default": 0,
      "read_only": 1,
      "description": "Whether query processing failed"
    },
    {
      "fieldname": "error_message",
      "label": "Error Message",
      "fieldtype": "Text",
      "read_only": 1,
      "description": "Error details if query failed"
    },
    {
      "fieldname": "tools_called",
      "label": "Tools Called",
      "fieldtype": "Int",
      "default": 0,
      "read_only": 1,
      "description": "Number of tool invocations"
    },
    {
      "fieldname": "total_processing_time_ms",
      "label": "Total Processing Time (ms)",
      "fieldtype": "Int",
      "read_only": 1,
      "description": "End-to-end query processing time"
    }
  ],
  "permissions": [
    {
      "role": "System Manager",
      "read": 1,
      "write": 0,
      "create": 1,
      "delete": 0
    }
  ]
}
```

### Field Descriptions

| Field | Type | Purpose | Validation Rules |
|-------|------|---------|------------------|
| `session_id` | Link (Chat Session) | Parent session | Must exist |
| `user` | Link (User) | Query author | Auto-set from session |
| `timestamp` | Datetime | Processing time | Auto-set on insert |
| `query_text` | Long Text | Original user query | Immutable |
| `response_summary` | Text | Response preview | First 500 characters |
| `data_accessed` | JSON | Access log | Array of {doctype, filters, count} |
| `permission_checks_passed` | Check | Access validation | True if all checks passed |
| `error_occurred` | Check | Failure flag | True if query failed |
| `error_message` | Text | Error details | Set if error_occurred=true |
| `tools_called` | Int | Tool invocation count | Number of agent tool calls |
| `total_processing_time_ms` | Int | Latency metric | Milliseconds from query to response |

### Business Rules

1. **Audit Log Creation**:
   - Created for **every** user query, even if it fails
   - Logged in exception-safe manner (errors don't prevent logging)
   - `data_accessed` JSON structure:
     ```json
     [
       {"doctype": "Customer", "operation": "get_list", "filters": {"territory": "US"}, "count": 15},
       {"report": "Profit and Loss Statement", "company": "Company A", "date_range": "2024-Q4"}
     ]
     ```

2. **Permission Tracking**:
   - `permission_checks_passed` = true only if ALL permission validations succeeded
   - If any permission check fails, log details in `error_message`

3. **Retention Policy**:
   - Audit logs retained for 1 year (longer than chat history for compliance)
   - Separate cleanup job from chat session cleanup

4. **Access Control**:
   - Only System Managers can read audit logs
   - No edit or delete permissions (immutable audit trail)

---

## 4. AI Tool Call Log DocType

### Purpose
Detailed log of individual AI agent tool invocations. Provides granular visibility into which tools were called, with what parameters, and what they returned.

### DocType Configuration

```json
{
  "name": "AI Tool Call Log",
  "module": "AI Chatbot",
  "doctype": "DocType",
  "engine": "InnoDB",
  "is_submittable": 0,
  "track_changes": 0,
  "autoname": "hash",
  "fields": [
    {
      "fieldname": "session_id",
      "label": "Session ID",
      "fieldtype": "Link",
      "options": "Chat Session",
      "reqd": 1,
      "read_only": 1,
      "description": "Associated chat session"
    },
    {
      "fieldname": "audit_log_id",
      "label": "Audit Log ID",
      "fieldtype": "Link",
      "options": "Chat Audit Log",
      "reqd": 1,
      "read_only": 1,
      "description": "Parent audit log entry"
    },
    {
      "fieldname": "tool_name",
      "label": "Tool Name",
      "fieldtype": "Data",
      "reqd": 1,
      "read_only": 1,
      "description": "Name of the tool called (e.g., 'get_financial_report')"
    },
    {
      "fieldname": "parameters",
      "label": "Parameters",
      "fieldtype": "JSON",
      "read_only": 1,
      "description": "Tool input parameters as JSON"
    },
    {
      "fieldname": "execution_start",
      "label": "Execution Start",
      "fieldtype": "Datetime",
      "reqd": 1,
      "read_only": 1,
      "description": "Tool invocation timestamp"
    },
    {
      "fieldname": "execution_time_ms",
      "label": "Execution Time (ms)",
      "fieldtype": "Int",
      "read_only": 1,
      "description": "Tool execution duration"
    },
    {
      "fieldname": "result_status",
      "label": "Result Status",
      "fieldtype": "Select",
      "options": "success\nerror\npermission_denied",
      "reqd": 1,
      "read_only": 1,
      "description": "Tool execution outcome"
    },
    {
      "fieldname": "result_summary",
      "label": "Result Summary",
      "fieldtype": "Text",
      "read_only": 1,
      "description": "Summary of tool output (first 1000 chars)"
    },
    {
      "fieldname": "error_details",
      "label": "Error Details",
      "fieldtype": "Text",
      "read_only": 1,
      "description": "Error message if status=error"
    },
    {
      "fieldname": "records_returned",
      "label": "Records Returned",
      "fieldtype": "Int",
      "default": 0,
      "read_only": 1,
      "description": "Number of records returned by tool"
    }
  ],
  "permissions": [
    {
      "role": "System Manager",
      "read": 1,
      "write": 0,
      "create": 1,
      "delete": 0
    }
  ]
}
```

### Field Descriptions

| Field | Type | Purpose | Validation Rules |
|-------|------|---------|------------------|
| `session_id` | Link (Chat Session) | Parent session | Must exist |
| `audit_log_id` | Link (Chat Audit Log) | Parent audit entry | Must exist |
| `tool_name` | Data | Tool identifier | Matches registered tool name |
| `parameters` | JSON | Tool inputs | Structured tool parameters |
| `execution_start` | Datetime | Call timestamp | Auto-set on insert |
| `execution_time_ms` | Int | Latency | Calculated from start to end |
| `result_status` | Select | Outcome | success/error/permission_denied |
| `result_summary` | Text | Output preview | First 1000 characters |
| `error_details` | Text | Failure reason | Set if result_status != success |
| `records_returned` | Int | Result count | Number of records in output |

### Business Rules

1. **Tool Call Logging**:
   - Every tool invocation creates a log entry
   - Logged before tool execution begins (with partial data)
   - Updated after tool completes (with results/errors)
   - Multiple tool calls per query create multiple log entries

2. **Parameter Sanitization**:
   - Sensitive parameters (API keys, passwords) redacted in logs
   - `parameters` JSON structure example:
     ```json
     {
       "report_name": "Profit and Loss Statement",
       "filters": {"company": "Company A", "from_date": "2024-01-01", "to_date": "2024-12-31"},
       "user": "user@example.com"
     }
     ```

3. **Result Handling**:
   - `result_summary` truncated to 1000 characters (full results not stored)
   - `records_returned` used for performance monitoring (detect expensive queries)
   - `result_status` used for error rate tracking

4. **Retention Policy**:
   - Same retention as Chat Audit Log (1 year)
   - Linked to parent audit log (cascade delete)

---

## Data Relationships

```
┌──────────────┐
│ Chat Session │
│ (1)          │
└──────┬───────┘
       │
       │ 1:N
       │
       ├───────────────┬──────────────────┬──────────────────┐
       │               │                  │                  │
       ▼               ▼                  ▼                  ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│Chat Message  │ │Chat Audit Log│ │AI Tool Call  │ │User          │
│(N)           │ │(N)           │ │Log (N)       │ │(1)           │
└──────────────┘ └──────┬───────┘ └──────────────┘ └──────────────┘
                        │
                        │ 1:N
                        │
                        ▼
                 ┌──────────────┐
                 │AI Tool Call  │
                 │Log (N)       │
                 └──────────────┘
```

### Relationship Details

1. **Chat Session → Chat Message** (1:N)
   - One session contains multiple messages
   - Messages cannot exist without parent session
   - Delete cascade: Deleting session deletes all messages

2. **Chat Session → Chat Audit Log** (1:N)
   - One session generates multiple audit logs (one per query)
   - Audit logs can exist after session deleted (longer retention)
   - No cascade delete (audit logs independent after creation)

3. **Chat Audit Log → AI Tool Call Log** (1:N)
   - One user query may invoke multiple tools
   - Tool call logs always linked to parent audit log
   - Delete cascade: Deleting audit log deletes tool call logs

4. **Chat Session → User** (N:1)
   - Each session owned by exactly one user
   - User can have multiple sessions
   - No cascade delete (sessions independent from user lifecycle)

---

## Indexes & Performance

### Chat Session
- **Primary Key**: `session_id` (UUID, indexed automatically)
- **Index on `user`**: Fast retrieval of user's sessions
- **Index on `status`**: Filter active/expired sessions efficiently
- **Index on `last_activity`**: Support session expiry queries

### Chat Message
- **Primary Key**: Auto-generated hash
- **Index on `session_id`**: Fast retrieval of session messages
- **Index on `timestamp`**: Support chronological ordering
- **Composite Index**: `(session_id, timestamp)` for paginated message fetching

### Chat Audit Log
- **Primary Key**: Auto-generated hash
- **Index on `user`**: Support compliance queries by user
- **Index on `timestamp`**: Time-range audit queries
- **Index on `session_id`**: Link to session context

### AI Tool Call Log
- **Primary Key**: Auto-generated hash
- **Index on `audit_log_id`**: Link to parent audit log
- **Index on `tool_name`**: Analyze tool usage patterns
- **Index on `result_status`**: Track error rates

---

## Data Validation & Constraints

### Chat Session
- `session_id` must be valid UUID v4 format
- `user` must reference existing User doctype
- `status` transitions: Active → Closed/Expired (no reversal)
- `last_activity` must be >= `created_at`

### Chat Message
- `session_id` must reference existing active Chat Session
- `role` must be user/assistant/system
- `content` max length: 10,000 characters
- `timestamp` must match session's `last_activity` (updated atomically)

### Chat Audit Log
- All fields immutable after creation
- `data_accessed` must be valid JSON array
- At least one of `error_occurred` or `permission_checks_passed` must be set

### AI Tool Call Log
- All fields immutable after creation
- `parameters` must be valid JSON object
- `result_status` determines presence of `error_details` (required if status=error)

---

## Next Steps

With data model defined, proceed to:
1. **contracts/** - API endpoint specifications and agent tool schemas
2. **quickstart.md** - Development environment setup guide

All DocType definitions ready for implementation following Frappe conventions and constitutional principles.
