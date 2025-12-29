"""
Chat API Endpoints

Whitelisted Frappe API endpoints for chat session and message management.
All endpoints enforce session ownership and rate limiting.
"""

import frappe
from frappe import _
from typing import Optional

from erpnext_chatbot.erpnext_chatbot.services.session_manager import (
    create_session as _create_session,
    validate_session_ownership,
    get_user_sessions,
    close_session as _close_session,
    delete_session as _delete_session,
)
from erpnext_chatbot.erpnext_chatbot.services.rate_limiter import (
    check_rate_limit,
    get_remaining_requests,
)
from erpnext_chatbot.erpnext_chatbot.services.agent_orchestrator import process_message
from erpnext_chatbot.erpnext_chatbot.utils.sanitization import sanitize_user_input


@frappe.whitelist()
def create_session(company_context: Optional[str] = None) -> dict:
    """
    Create a new chat session for the current user.

    Args:
        company_context: Optional default company for queries

    Returns:
        Dictionary with session_id, status, created_at
    """
    try:
        result = _create_session(company_context=company_context)
        return {
            "success": True,
            "message": result
        }
    except Exception as e:
        frappe.log_error(f"Create session error: {str(e)}", "Chatbot API Error")
        return {
            "success": False,
            "error": str(e)
        }


@frappe.whitelist()
def send_message(session_id: str, message: str) -> dict:
    """
    Send a message to the chatbot and get AI response.

    Args:
        session_id: The chat session ID
        message: User's message/question

    Returns:
        Dictionary with AI response and metadata
    """
    try:
        # Rate limit check
        check_rate_limit(frappe.session.user, limit=20, window=60)

        # Validate session ownership
        validate_session_ownership(session_id)

        # Sanitize input
        clean_message = sanitize_user_input(message, max_length=10000)

        if not clean_message:
            return {
                "success": False,
                "error": "Message cannot be empty"
            }

        # Process message through agent
        result = process_message(
            session_id=session_id,
            user_message=clean_message,
            user=frappe.session.user
        )

        return {
            "success": result.get("success", False),
            "message": {
                "response": result.get("response"),
                "processing_time_ms": result.get("processing_time_ms"),
                "tools_called": result.get("tools_called", 0)
            }
        }

    except frappe.ValidationError as e:
        return {
            "success": False,
            "error": str(e)
        }
    except Exception as e:
        frappe.log_error(f"Send message error: {str(e)}", "Chatbot API Error")
        return {
            "success": False,
            "error": "An error occurred while processing your message. Please try again."
        }


@frappe.whitelist()
def get_session_history(
    session_id: str,
    limit: int = 50,
    offset: int = 0
) -> dict:
    """
    Get message history for a session.

    Args:
        session_id: The chat session ID
        limit: Maximum messages to return (default 50, max 100)
        offset: Number of messages to skip

    Returns:
        Dictionary with messages and total count
    """
    try:
        # Validate session ownership
        validate_session_ownership(session_id)

        # Enforce limits
        limit = min(int(limit), 100)
        offset = max(int(offset), 0)

        # Get messages
        from erpnext_chatbot.erpnext_chatbot.ai_chatbot.doctype.chat_message.chat_message import ChatMessage
        messages = ChatMessage.get_session_messages(session_id, limit=limit, offset=offset)

        # Get total count
        total_count = frappe.db.count("Chat Message", {"session_id": session_id})

        return {
            "success": True,
            "message": {
                "session_id": session_id,
                "messages": messages,
                "total_count": total_count
            }
        }

    except Exception as e:
        frappe.log_error(f"Get session history error: {str(e)}", "Chatbot API Error")
        return {
            "success": False,
            "error": str(e)
        }


@frappe.whitelist()
def get_sessions(status: Optional[str] = None, limit: int = 20) -> dict:
    """
    Get all chat sessions for the current user.

    Args:
        status: Filter by status (Active/Closed/Expired)
        limit: Maximum sessions to return

    Returns:
        Dictionary with sessions list
    """
    try:
        limit = min(int(limit), 50)
        sessions = get_user_sessions(status=status, limit=limit)

        return {
            "success": True,
            "message": {
                "sessions": sessions,
                "total_count": len(sessions)
            }
        }

    except Exception as e:
        frappe.log_error(f"Get sessions error: {str(e)}", "Chatbot API Error")
        return {
            "success": False,
            "error": str(e)
        }


@frappe.whitelist()
def close_session(session_id: str) -> dict:
    """
    Close a chat session.

    Args:
        session_id: The session to close

    Returns:
        Dictionary with updated session status
    """
    try:
        # Validate session ownership
        validate_session_ownership(session_id)

        result = _close_session(session_id)

        return {
            "success": True,
            "message": result
        }

    except Exception as e:
        frappe.log_error(f"Close session error: {str(e)}", "Chatbot API Error")
        return {
            "success": False,
            "error": str(e)
        }


@frappe.whitelist()
def delete_session(session_id: str) -> dict:
    """
    Delete a chat session and all related messages.
    Audit logs are retained for compliance.

    Args:
        session_id: The session to delete

    Returns:
        Confirmation dictionary
    """
    try:
        # Validate session ownership
        validate_session_ownership(session_id)

        result = _delete_session(session_id)

        return {
            "success": True,
            "message": result
        }

    except Exception as e:
        frappe.log_error(f"Delete session error: {str(e)}", "Chatbot API Error")
        return {
            "success": False,
            "error": str(e)
        }


@frappe.whitelist()
def get_rate_limit_status() -> dict:
    """
    Get current rate limit status for the user.

    Returns:
        Dictionary with remaining requests and reset time
    """
    try:
        status = get_remaining_requests(frappe.session.user)

        return {
            "success": True,
            "message": status
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@frappe.whitelist()
def get_new_messages(session_id: str, after_timestamp: Optional[str] = None) -> dict:
    """
    Poll for new messages after a timestamp.
    Used for UI polling to get assistant responses.

    Args:
        session_id: The chat session ID
        after_timestamp: Only return messages after this timestamp

    Returns:
        Dictionary with new messages
    """
    try:
        # Validate session ownership
        validate_session_ownership(session_id)

        filters = {"session_id": session_id}
        if after_timestamp:
            filters["timestamp"] = [">", after_timestamp]

        messages = frappe.get_all(
            "Chat Message",
            filters=filters,
            fields=["name", "role", "content", "timestamp", "token_count", "processing_time_ms"],
            order_by="timestamp asc",
            limit=10
        )

        return {
            "success": True,
            "message": {
                "messages": messages,
                "count": len(messages)
            }
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
