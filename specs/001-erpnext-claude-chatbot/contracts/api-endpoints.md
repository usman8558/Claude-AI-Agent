# API Endpoints: ERPNext Claude Chatbot

**Date**: 2025-12-29
**Feature**: 001-erpnext-claude-chatbot

## Overview

Frappe whitelisted API endpoints for chat session management and message processing. All endpoints enforce session ownership validation.

---

## 1. Create Session

**Endpoint**: `POST /api/method/erpnext_chatbot.api.chat.create_session`

**Purpose**: Initialize new chat session for current user

**Authentication**: Frappe session required

**Request**: Empty body

**Response**:
```json
{
  "message": {
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "Active",
    "created_at": "2024-12-29 10:30:00"
  }
}
```

**Validation**:
- User must be authenticated
- Auto-creates session linked to `frappe.session.user`
- Company context set from user's default company

---

## 2. Send Message

**Endpoint**: `POST /api/method/erpnext_chatbot.api.chat.send_message`

**Purpose**: Send user message and get AI response

**Authentication**: Frappe session required

**Request**:
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "What was our revenue last quarter?"
}
```

**Response**:
```json
{
  "message": {
    "user_message_id": "msg-001",
    "assistant_message_id": "msg-002",
    "assistant_response": "Your total revenue for Q4 2024 was $1.2M across all companies.",
    "processing_time_ms": 4500,
    "tools_called": 2
  }
}
```

**Validation**:
- Session must exist and be Active
- User must own the session
- Rate limit: 20 requests/minute per user
- Input sanitization applied to message content

**Error Responses**:
- 403: Permission denied (not session owner)
- 429: Rate limit exceeded
- 400: Session expired/closed

---

## 3. Get Session History

**Endpoint**: `GET /api/method/erpnext_chatbot.api.chat.get_session_history`

**Purpose**: Retrieve messages from a session

**Authentication**: Frappe session required

**Request**:
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "limit": 50,
  "offset": 0
}
```

**Response**:
```json
{
  "message": {
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "messages": [
      {
        "role": "user",
        "content": "What was our revenue last quarter?",
        "timestamp": "2024-12-29 10:31:00"
      },
      {
        "role": "assistant",
        "content": "Your total revenue for Q4 2024 was $1.2M.",
        "timestamp": "2024-12-29 10:31:05"
      }
    ],
    "total_count": 24
  }
}
```

**Validation**:
- User must own the session
- Pagination: max limit=100, default=50

---

## 4. Get User Sessions

**Endpoint**: `GET /api/method/erpnext_chatbot.api.chat.get_user_sessions`

**Purpose**: List all sessions for current user

**Authentication**: Frappe session required

**Request**:
```json
{
  "status": "Active",
  "limit": 20
}
```

**Response**:
```json
{
  "message": {
    "sessions": [
      {
        "session_id": "550e8400-e29b-41d4-a716-446655440000",
        "status": "Active",
        "created_at": "2024-12-29 10:30:00",
        "last_activity": "2024-12-29 10:35:00",
        "message_count": 12,
        "first_message_preview": "What was our revenue..."
      }
    ],
    "total_count": 5
  }
}
```

---

## 5. Close Session

**Endpoint**: `POST /api/method/erpnext_chatbot.api.chat.close_session`

**Purpose**: Mark session as closed (user-initiated)

**Authentication**: Frappe session required

**Request**:
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Response**:
```json
{
  "message": {
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "Closed"
  }
}
```

---

## 6. Delete Session

**Endpoint**: `POST /api/method/erpnext_chatbot.api.chat.delete_session`

**Purpose**: Permanently delete session and all related data

**Authentication**: Frappe session required

**Request**:
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Response**:
```json
{
  "message": {
    "deleted": true,
    "session_id": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

**Validation**:
- User must own the session
- Cascade deletes: Chat Messages (audit logs retained)

---

## Security & Rate Limiting

**All Endpoints**:
- Require valid Frappe session (cookie-based auth)
- Session ownership validated before any operation
- Input sanitization applied to all text fields
- Rate limits enforced via Frappe Cache (Redis)

**Rate Limits**:
- `send_message`: 20 requests/minute per user
- Other endpoints: 60 requests/minute per user

**Error Handling**:
- 401: Unauthenticated
- 403: Permission denied (not session owner)
- 429: Rate limit exceeded
- 500: Internal server error (logged to audit trail)
