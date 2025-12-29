"""
Audit Logger Service

Exception-safe audit logging for compliance.
Logs are created even if the main operation fails.
"""

import json
import frappe
from frappe.utils import now_datetime
from typing import Optional, Any


def log_query(
    session_id: str,
    query_text: str,
    response_summary: Optional[str] = None,
    data_accessed: Optional[list] = None,
    permission_checks_passed: bool = True,
    error_occurred: bool = False,
    error_message: Optional[str] = None,
    tools_called: int = 0,
    total_processing_time_ms: Optional[int] = None
) -> Optional[str]:
    """
    Create an audit log entry for a user query.
    Exception-safe: will log errors but not fail.

    Args:
        session_id: The session ID
        query_text: User's original question
        response_summary: First 500 chars of AI response
        data_accessed: List of DocTypes/reports accessed
        permission_checks_passed: Whether all permissions succeeded
        error_occurred: Whether query failed
        error_message: Error details if failed
        tools_called: Number of tool invocations
        total_processing_time_ms: End-to-end processing time

    Returns:
        Audit log ID if created, None if failed
    """
    try:
        user = frappe.session.user

        # Truncate response summary to 500 chars
        if response_summary and len(response_summary) > 500:
            response_summary = response_summary[:500] + "..."

        audit_log = frappe.get_doc({
            "doctype": "Chat Audit Log",
            "session_id": session_id,
            "user": user,
            "timestamp": now_datetime(),
            "query_text": query_text,
            "response_summary": response_summary,
            "data_accessed": json.dumps(data_accessed) if data_accessed else None,
            "permission_checks_passed": permission_checks_passed,
            "error_occurred": error_occurred,
            "error_message": error_message,
            "tools_called": tools_called,
            "total_processing_time_ms": total_processing_time_ms
        })
        audit_log.insert(ignore_permissions=True)
        frappe.db.commit()

        return audit_log.name

    except Exception as e:
        # Log the failure but don't raise - audit logging should never block main flow
        frappe.log_error(
            f"Failed to create audit log for session {session_id}: {str(e)}",
            "Audit Log Creation Error"
        )
        return None


def log_tool_call(
    session_id: str,
    audit_log_id: str,
    tool_name: str,
    parameters: Optional[dict] = None,
    execution_time_ms: Optional[int] = None,
    result_status: str = "success",
    result_summary: Optional[str] = None,
    error_details: Optional[str] = None,
    records_returned: int = 0
) -> Optional[str]:
    """
    Create a tool call log entry.
    Exception-safe: will log errors but not fail.

    Args:
        session_id: The session ID
        audit_log_id: Parent audit log ID
        tool_name: Name of the tool called
        parameters: Tool input parameters
        execution_time_ms: Tool execution duration
        result_status: success/error/permission_denied
        result_summary: Summary of tool output (first 1000 chars)
        error_details: Error message if status=error
        records_returned: Number of records returned

    Returns:
        Tool call log ID if created, None if failed
    """
    try:
        # Sanitize parameters (remove sensitive data)
        safe_parameters = _sanitize_parameters(parameters) if parameters else None

        # Truncate result summary to 1000 chars
        if result_summary and len(result_summary) > 1000:
            result_summary = result_summary[:1000] + "..."

        tool_log = frappe.get_doc({
            "doctype": "AI Tool Call Log",
            "session_id": session_id,
            "audit_log_id": audit_log_id,
            "tool_name": tool_name,
            "parameters": json.dumps(safe_parameters) if safe_parameters else None,
            "execution_start": now_datetime(),
            "execution_time_ms": execution_time_ms,
            "result_status": result_status,
            "result_summary": result_summary,
            "error_details": error_details,
            "records_returned": records_returned
        })
        tool_log.insert(ignore_permissions=True)
        frappe.db.commit()

        return tool_log.name

    except Exception as e:
        # Log the failure but don't raise
        frappe.log_error(
            f"Failed to create tool call log for {tool_name}: {str(e)}",
            "Tool Call Log Creation Error"
        )
        return None


def _sanitize_parameters(parameters: dict) -> dict:
    """
    Remove sensitive data from parameters before logging.

    Args:
        parameters: Raw parameters dictionary

    Returns:
        Sanitized parameters with sensitive values redacted
    """
    sensitive_keys = [
        "api_key", "password", "secret", "token", "credential",
        "authorization", "auth"
    ]

    safe_params = {}
    for key, value in parameters.items():
        key_lower = key.lower()
        if any(sensitive in key_lower for sensitive in sensitive_keys):
            safe_params[key] = "[REDACTED]"
        elif isinstance(value, dict):
            safe_params[key] = _sanitize_parameters(value)
        else:
            safe_params[key] = value

    return safe_params


def get_query_audit_trail(
    session_id: Optional[str] = None,
    user: Optional[str] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    limit: int = 100
) -> list:
    """
    Retrieve audit trail for compliance review.

    Args:
        session_id: Filter by session
        user: Filter by user
        from_date: Filter from date
        to_date: Filter to date
        limit: Maximum records to return

    Returns:
        List of audit log entries
    """
    filters = {}

    if session_id:
        filters["session_id"] = session_id
    if user:
        filters["user"] = user
    if from_date:
        filters["timestamp"] = [">=", from_date]
    if to_date:
        if "timestamp" in filters:
            filters["timestamp"] = ["between", [from_date, to_date]]
        else:
            filters["timestamp"] = ["<=", to_date]

    audit_logs = frappe.get_all(
        "Chat Audit Log",
        filters=filters,
        fields=[
            "name", "session_id", "user", "timestamp", "query_text",
            "response_summary", "permission_checks_passed", "error_occurred",
            "tools_called", "total_processing_time_ms"
        ],
        order_by="timestamp desc",
        limit=limit
    )

    return audit_logs
