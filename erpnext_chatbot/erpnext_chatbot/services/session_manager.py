"""
Session Manager Service

Handles chat session lifecycle: creation, validation, expiry, and cleanup.
"""

import uuid
import frappe
from frappe import _
from frappe.utils import now_datetime, add_to_date, get_datetime
from typing import Optional


def create_session(company_context: Optional[str] = None) -> dict:
    """
    Create a new chat session for the current user.

    Args:
        company_context: Optional company to use as default for queries

    Returns:
        Dictionary with session details
    """
    user = frappe.session.user

    if not company_context:
        company_context = frappe.defaults.get_user_default("Company")

    session = frappe.get_doc({
        "doctype": "Chat Session",
        "session_id": str(uuid.uuid4()),
        "user": user,
        "status": "Active",
        "created_at": now_datetime(),
        "last_activity": now_datetime(),
        "company_context": company_context,
        "message_count": 0,
        "total_tokens": 0
    })
    session.insert(ignore_permissions=True)

    return {
        "session_id": session.session_id,
        "status": session.status,
        "created_at": str(session.created_at),
        "company_context": session.company_context
    }


def validate_session_ownership(session_id: str, user: Optional[str] = None) -> dict:
    """
    Validate that the user owns the session and it's active.

    Args:
        session_id: The session ID to validate
        user: The user to validate against (defaults to current user)

    Returns:
        Session document as dictionary

    Raises:
        frappe.PermissionError: If user doesn't own the session
        frappe.DoesNotExistError: If session doesn't exist
        frappe.ValidationError: If session is not active
    """
    if user is None:
        user = frappe.session.user

    if not frappe.db.exists("Chat Session", session_id):
        frappe.throw(
            _("Chat session not found: {0}").format(session_id),
            frappe.DoesNotExistError
        )

    session = frappe.get_doc("Chat Session", session_id)

    # Validate ownership (except for Administrator)
    if session.user != user and user != "Administrator":
        frappe.throw(
            _("You do not have permission to access this chat session"),
            frappe.PermissionError
        )

    # Validate session is active
    if session.status != "Active":
        frappe.throw(
            _("This chat session is {0} and cannot be used").format(session.status.lower()),
            frappe.ValidationError
        )

    return {
        "session_id": session.session_id,
        "user": session.user,
        "status": session.status,
        "company_context": session.company_context,
        "message_count": session.message_count,
        "total_tokens": session.total_tokens
    }


def get_user_sessions(
    user: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 20
) -> list:
    """
    Get all chat sessions for a user.

    Args:
        user: The user to fetch sessions for (defaults to current user)
        status: Filter by status (Active/Closed/Expired)
        limit: Maximum number of sessions to return

    Returns:
        List of session dictionaries
    """
    if user is None:
        user = frappe.session.user

    filters = {"user": user}
    if status:
        filters["status"] = status

    sessions = frappe.get_all(
        "Chat Session",
        filters=filters,
        fields=[
            "session_id", "status", "created_at", "last_activity",
            "message_count", "company_context"
        ],
        order_by="last_activity desc",
        limit=limit
    )

    # Add first message preview for each session
    for session in sessions:
        first_message = frappe.get_all(
            "Chat Message",
            filters={"session_id": session.session_id, "role": "user"},
            fields=["content"],
            order_by="timestamp asc",
            limit=1
        )
        if first_message:
            preview = first_message[0].content[:100]
            session["first_message_preview"] = preview + "..." if len(first_message[0].content) > 100 else preview
        else:
            session["first_message_preview"] = ""

    return sessions


def close_session(session_id: str) -> dict:
    """
    Close a chat session (user-initiated).

    Args:
        session_id: The session to close

    Returns:
        Updated session details
    """
    session = frappe.get_doc("Chat Session", session_id)

    # Validate ownership
    if session.user != frappe.session.user and frappe.session.user != "Administrator":
        frappe.throw(
            _("You do not have permission to close this session"),
            frappe.PermissionError
        )

    if session.status == "Expired":
        frappe.throw(_("Cannot close an expired session"))

    session.status = "Closed"
    session.save()

    return {
        "session_id": session.session_id,
        "status": session.status
    }


def delete_session(session_id: str) -> dict:
    """
    Delete a chat session and all related messages.
    Audit logs are retained for compliance.

    Args:
        session_id: The session to delete

    Returns:
        Confirmation dictionary
    """
    session = frappe.get_doc("Chat Session", session_id)

    # Validate ownership
    if session.user != frappe.session.user and frappe.session.user != "Administrator":
        frappe.throw(
            _("You do not have permission to delete this session"),
            frappe.PermissionError
        )

    # Delete all messages (but not audit logs - they're retained)
    frappe.db.delete("Chat Message", {"session_id": session_id})

    # Delete the session
    frappe.delete_doc("Chat Session", session_id, ignore_permissions=True)

    return {
        "deleted": True,
        "session_id": session_id
    }


def expire_inactive_sessions():
    """
    Scheduled job: Expire sessions inactive for more than 24 hours.
    Called hourly by the scheduler.
    """
    expiry_threshold = add_to_date(now_datetime(), hours=-24)

    inactive_sessions = frappe.get_all(
        "Chat Session",
        filters={
            "status": "Active",
            "last_activity": ["<", expiry_threshold]
        },
        pluck="name"
    )

    for session_id in inactive_sessions:
        try:
            session = frappe.get_doc("Chat Session", session_id)
            session.status = "Expired"
            session.save(ignore_permissions=True)
            frappe.db.commit()
        except Exception as e:
            frappe.log_error(
                f"Failed to expire session {session_id}: {str(e)}",
                "Session Expiry Error"
            )

    if inactive_sessions:
        frappe.logger().info(f"Expired {len(inactive_sessions)} inactive chat sessions")


def delete_old_sessions():
    """
    Scheduled job: Delete sessions older than retention period (90 days default).
    Called daily by the scheduler.
    """
    retention_days = frappe.db.get_single_value("System Settings", "chatbot_retention_days") or 90
    retention_threshold = add_to_date(now_datetime(), days=-retention_days)

    old_sessions = frappe.get_all(
        "Chat Session",
        filters={
            "created_at": ["<", retention_threshold]
        },
        pluck="name"
    )

    for session_id in old_sessions:
        try:
            # Delete messages first
            frappe.db.delete("Chat Message", {"session_id": session_id})
            # Delete session
            frappe.delete_doc("Chat Session", session_id, ignore_permissions=True, force=True)
            frappe.db.commit()
        except Exception as e:
            frappe.log_error(
                f"Failed to delete old session {session_id}: {str(e)}",
                "Session Cleanup Error"
            )

    if old_sessions:
        frappe.logger().info(f"Deleted {len(old_sessions)} old chat sessions")
