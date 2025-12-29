"""
Report Tools

Generic report execution tool for running any ERPNext standard report.
"""

import frappe
from frappe import _
from typing import Optional, Dict, Any

from erpnext_chatbot.erpnext_chatbot.tools.base_tool import (
    with_audit_logging,
    PermissionDeniedError,
)
from erpnext_chatbot.erpnext_chatbot.utils.permissions import validate_report_access
from erpnext_chatbot.erpnext_chatbot.utils.response_formatter import format_report_for_ai
from erpnext_chatbot.erpnext_chatbot.utils.sanitization import validate_report_name


# OpenAI function calling schemas for report tools
REPORT_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "execute_report",
            "description": "Execute any standard ERPNext report by name with filters. Use this for reports not covered by specialized tools like Accounts Receivable, Sales Register, General Ledger, etc.",
            "parameters": {
                "type": "object",
                "properties": {
                    "report_name": {
                        "type": "string",
                        "description": "Exact name of the ERPNext report (e.g., 'Accounts Receivable', 'Sales Register', 'General Ledger')"
                    },
                    "filters": {
                        "type": "object",
                        "description": "Report filters as key-value pairs (e.g., {\"company\": \"My Company\", \"from_date\": \"2024-01-01\"})"
                    }
                },
                "required": ["report_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_available_reports",
            "description": "List available ERPNext reports that can be executed. Use this to discover what reports are available.",
            "parameters": {
                "type": "object",
                "properties": {
                    "module": {
                        "type": "string",
                        "description": "Filter by module (e.g., 'Accounts', 'Selling', 'Stock')"
                    }
                },
                "required": []
            }
        }
    }
]


@with_audit_logging("execute_report")
def execute_report(
    report_name: str,
    filters: Optional[Dict[str, Any]] = None,
    session_id: Optional[str] = None,
    audit_log_id: Optional[str] = None,
    user: Optional[str] = None
) -> str:
    """
    Execute an ERPNext report and return formatted results.

    Args:
        report_name: Name of the report to execute
        filters: Report filters as dictionary
        session_id: Chat session ID for audit logging
        audit_log_id: Parent audit log ID
        user: User making the request

    Returns:
        Formatted report data as string
    """
    from frappe.desk.query_report import run

    user = user or frappe.session.user

    # Validate report name
    if not validate_report_name(report_name):
        return f"Error: Report '{report_name}' not found or invalid."

    # Validate report access
    try:
        validate_report_access(report_name, user, throw=True)
    except frappe.PermissionError as e:
        raise PermissionDeniedError(f"You do not have permission to access the report '{report_name}'")

    # Clean and validate filters
    safe_filters = _validate_filters(filters or {}, user)

    try:
        result = run(report_name, filters=safe_filters, user=user)
        return format_report_for_ai(result, max_rows=50)
    except Exception as e:
        frappe.log_error(f"Report execution error for {report_name}: {str(e)}", "Report Execution Error")
        return f"Error executing report '{report_name}': {str(e)}"


@with_audit_logging("list_available_reports")
def list_available_reports(
    module: Optional[str] = None,
    session_id: Optional[str] = None,
    audit_log_id: Optional[str] = None,
    user: Optional[str] = None
) -> str:
    """
    List available reports the user can access.

    Args:
        module: Filter by module (Accounts, Selling, etc.)
        session_id: Chat session ID for audit logging
        audit_log_id: Parent audit log ID
        user: User making the request

    Returns:
        List of available reports as formatted string
    """
    user = user or frappe.session.user

    filters = {"disabled": 0}
    if module:
        filters["module"] = module

    reports = frappe.get_all(
        "Report",
        filters=filters,
        fields=["name", "module", "ref_doctype", "report_type"],
        order_by="module, name"
    )

    # Filter by permission
    accessible_reports = []
    for report in reports:
        try:
            if report.ref_doctype:
                if frappe.has_permission(report.ref_doctype, ptype="read", user=user):
                    accessible_reports.append(report)
            else:
                # No ref_doctype, include if user has report permission
                accessible_reports.append(report)
        except Exception:
            continue

    if not accessible_reports:
        return "No reports available for your access level."

    # Format output
    output_parts = ["**Available Reports:**\n"]

    current_module = None
    for report in accessible_reports:
        if report.module != current_module:
            current_module = report.module
            output_parts.append(f"\n**{current_module}:**")

        report_info = f"- {report.name}"
        if report.ref_doctype:
            report_info += f" (based on {report.ref_doctype})"
        output_parts.append(report_info)

    return "\n".join(output_parts)


def _validate_filters(filters: Dict[str, Any], user: str) -> Dict[str, Any]:
    """
    Validate and sanitize report filters.
    Ensures company access if company filter is present.

    Args:
        filters: Raw filters dictionary
        user: User making the request

    Returns:
        Validated filters
    """
    from erpnext_chatbot.erpnext_chatbot.utils.permissions import validate_company_access

    safe_filters = {}

    for key, value in filters.items():
        # Skip None values
        if value is None:
            continue

        # Validate company access
        if key.lower() == "company" and value:
            validate_company_access(value, user, throw=True)

        # Copy filter
        safe_filters[key] = value

    return safe_filters


# Common report shortcuts
COMMON_REPORTS = {
    "accounts_receivable": "Accounts Receivable",
    "accounts_payable": "Accounts Payable",
    "general_ledger": "General Ledger",
    "trial_balance": "Trial Balance",
    "sales_register": "Sales Register",
    "purchase_register": "Purchase Register",
    "stock_balance": "Stock Balance",
    "sales_analytics": "Sales Analytics",
}


def get_report_name(shortcut: str) -> Optional[str]:
    """Get full report name from shortcut."""
    return COMMON_REPORTS.get(shortcut.lower().replace(" ", "_"))


# Tool execution dispatcher
TOOL_FUNCTIONS = {
    "execute_report": execute_report,
    "list_available_reports": list_available_reports,
}
