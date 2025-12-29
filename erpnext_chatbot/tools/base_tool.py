"""
Base Tool Class

Provides permission checking foundation for all AI tools.
All tools must inherit from this class to ensure permission enforcement.
"""

import time
import frappe
from frappe import _
from typing import Any, Dict, Optional, Callable
from functools import wraps

from erpnext_chatbot.erpnext_chatbot.utils.permissions import (
    validate_permission,
    validate_company_access,
    get_user_default_company,
)
from erpnext_chatbot.erpnext_chatbot.services.audit_logger import log_tool_call


class ToolExecutionError(Exception):
    """Custom exception for tool execution errors."""
    pass


class PermissionDeniedError(Exception):
    """Custom exception for permission denied errors."""
    pass


class BaseTool:
    """
    Base class for all AI agent tools.
    Provides permission checking and audit logging.
    """

    def __init__(
        self,
        session_id: str,
        audit_log_id: str,
        user: Optional[str] = None
    ):
        """
        Initialize tool with session context.

        Args:
            session_id: Current chat session ID
            audit_log_id: Parent audit log ID for tool call logging
            user: User executing the tool (defaults to current user)
        """
        self.session_id = session_id
        self.audit_log_id = audit_log_id
        self.user = user or frappe.session.user

    def check_permission(
        self,
        doctype: str,
        ptype: str = "read"
    ) -> bool:
        """
        Check if user has permission for a DocType.

        Args:
            doctype: DocType to check
            ptype: Permission type

        Returns:
            True if permission granted

        Raises:
            PermissionDeniedError: If permission denied
        """
        try:
            validate_permission(doctype, ptype, self.user, throw=True)
            return True
        except frappe.PermissionError as e:
            raise PermissionDeniedError(str(e))

    def check_company_access(self, company: str) -> bool:
        """
        Check if user has access to a company.

        Args:
            company: Company to check

        Returns:
            True if access granted

        Raises:
            PermissionDeniedError: If access denied
        """
        try:
            validate_company_access(company, self.user, throw=True)
            return True
        except frappe.PermissionError as e:
            raise PermissionDeniedError(str(e))

    def get_default_company(self) -> Optional[str]:
        """Get user's default company."""
        return get_user_default_company(self.user)

    def log_execution(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        execution_time_ms: int,
        result_status: str,
        result_summary: Optional[str] = None,
        error_details: Optional[str] = None,
        records_returned: int = 0
    ):
        """
        Log tool execution to audit trail.

        Args:
            tool_name: Name of the tool
            parameters: Tool parameters
            execution_time_ms: Execution time in milliseconds
            result_status: success/error/permission_denied
            result_summary: Summary of result
            error_details: Error message if failed
            records_returned: Number of records returned
        """
        log_tool_call(
            session_id=self.session_id,
            audit_log_id=self.audit_log_id,
            tool_name=tool_name,
            parameters=parameters,
            execution_time_ms=execution_time_ms,
            result_status=result_status,
            result_summary=result_summary,
            error_details=error_details,
            records_returned=records_returned
        )


def with_permission_check(doctype: str, ptype: str = "read"):
    """
    Decorator to add permission check to tool functions.

    Args:
        doctype: DocType to check permission for
        ptype: Permission type (read/write/create/delete)

    Usage:
        @with_permission_check("GL Entry", "read")
        def get_financial_data(...):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            user = kwargs.get("user") or frappe.session.user

            if user != "Administrator":
                if not frappe.has_permission(doctype, ptype=ptype, user=user):
                    raise PermissionDeniedError(
                        f"You do not have {ptype} permission for {doctype}"
                    )

            return func(*args, **kwargs)
        return wrapper
    return decorator


def with_company_check():
    """
    Decorator to validate company access.
    Expects 'company' in kwargs.

    Usage:
        @with_company_check()
        def get_company_data(..., company=None):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            company = kwargs.get("company")
            user = kwargs.get("user") or frappe.session.user

            if company and user != "Administrator":
                validate_company_access(company, user, throw=True)

            return func(*args, **kwargs)
        return wrapper
    return decorator


def with_audit_logging(tool_name: str):
    """
    Decorator to add audit logging to tool functions.
    Expects 'session_id' and 'audit_log_id' in kwargs.

    Usage:
        @with_audit_logging("get_financial_report")
        def get_financial_report(..., session_id=None, audit_log_id=None):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            session_id = kwargs.get("session_id")
            audit_log_id = kwargs.get("audit_log_id")

            start_time = time.time()
            result_status = "success"
            error_details = None
            records_returned = 0

            try:
                result = func(*args, **kwargs)

                # Count records if result is a list
                if isinstance(result, list):
                    records_returned = len(result)
                elif isinstance(result, dict) and "data" in result:
                    records_returned = len(result.get("data", []))

                return result

            except PermissionDeniedError as e:
                result_status = "permission_denied"
                error_details = str(e)
                raise

            except Exception as e:
                result_status = "error"
                error_details = str(e)
                raise

            finally:
                execution_time_ms = int((time.time() - start_time) * 1000)

                if session_id and audit_log_id:
                    # Filter out internal kwargs for logging
                    logged_params = {
                        k: v for k, v in kwargs.items()
                        if k not in ["session_id", "audit_log_id", "user"]
                    }

                    log_tool_call(
                        session_id=session_id,
                        audit_log_id=audit_log_id,
                        tool_name=tool_name,
                        parameters=logged_params,
                        execution_time_ms=execution_time_ms,
                        result_status=result_status,
                        error_details=error_details,
                        records_returned=records_returned
                    )

        return wrapper
    return decorator
