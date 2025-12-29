"""
Finance Tools

AI agent tools for accessing financial data from ERPNext.
All tools enforce permission checks before data access.
"""

import frappe
from frappe import _
from frappe.utils import getdate, add_months, get_first_day, get_last_day
from typing import Optional, Dict, Any, List

from erpnext_chatbot.tools.base_tool import (
    with_permission_check,
    with_company_check,
    with_audit_logging,
    PermissionDeniedError,
)
from erpnext_chatbot.utils.permissions import (
    validate_permission,
    validate_company_access,
    get_user_default_company,
)
from erpnext_chatbot.utils.response_formatter import (
    format_report_for_ai,
    format_single_value,
)


# OpenAI function calling schemas for finance tools
FINANCE_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_financial_report",
            "description": "Retrieve financial data from standard ERPNext reports like Profit and Loss Statement, Balance Sheet, or Cash Flow. Respects user's company permissions.",
            "parameters": {
                "type": "object",
                "properties": {
                    "report_name": {
                        "type": "string",
                        "enum": ["Profit and Loss Statement", "Balance Sheet", "Cash Flow"],
                        "description": "Name of the financial report to execute"
                    },
                    "company": {
                        "type": "string",
                        "description": "Company name (optional, defaults to user's default company)"
                    },
                    "from_date": {
                        "type": "string",
                        "description": "Start date in YYYY-MM-DD format"
                    },
                    "to_date": {
                        "type": "string",
                        "description": "End date in YYYY-MM-DD format"
                    },
                    "periodicity": {
                        "type": "string",
                        "enum": ["Monthly", "Quarterly", "Yearly"],
                        "description": "Report periodicity (default: Monthly)"
                    }
                },
                "required": ["report_name", "from_date", "to_date"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_revenue",
            "description": "Get total revenue for a company in a date range. Returns the sum of all income from Sales Invoice.",
            "parameters": {
                "type": "object",
                "properties": {
                    "company": {
                        "type": "string",
                        "description": "Company name (optional)"
                    },
                    "from_date": {
                        "type": "string",
                        "description": "Start date in YYYY-MM-DD format"
                    },
                    "to_date": {
                        "type": "string",
                        "description": "End date in YYYY-MM-DD format"
                    }
                },
                "required": ["from_date", "to_date"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_expenses",
            "description": "Get total expenses for a company in a date range.",
            "parameters": {
                "type": "object",
                "properties": {
                    "company": {
                        "type": "string",
                        "description": "Company name (optional)"
                    },
                    "from_date": {
                        "type": "string",
                        "description": "Start date in YYYY-MM-DD format"
                    },
                    "to_date": {
                        "type": "string",
                        "description": "End date in YYYY-MM-DD format"
                    }
                },
                "required": ["from_date", "to_date"]
            }
        }
    }
]


@with_permission_check("GL Entry", "read")
@with_company_check()
@with_audit_logging("get_financial_report")
def get_financial_report(
    report_name: str,
    from_date: str,
    to_date: str,
    company: Optional[str] = None,
    periodicity: str = "Monthly",
    session_id: Optional[str] = None,
    audit_log_id: Optional[str] = None,
    user: Optional[str] = None
) -> str:
    """
    Execute a financial report and return formatted results.

    Args:
        report_name: Name of the report (Profit and Loss Statement, Balance Sheet, Cash Flow)
        from_date: Start date (YYYY-MM-DD)
        to_date: End date (YYYY-MM-DD)
        company: Company name (optional)
        periodicity: Monthly/Quarterly/Yearly
        session_id: Chat session ID for audit logging
        audit_log_id: Parent audit log ID
        user: User making the request

    Returns:
        Formatted report data as string
    """
    from frappe.desk.query_report import run

    # Get company (use default if not provided)
    if not company:
        company = get_user_default_company(user)

    if not company:
        return "Error: No company specified and no default company found for your user."

    # Validate company access
    validate_company_access(company, user, throw=True)

    # Build filters based on report type
    filters = {
        "company": company,
        "from_fiscal_year": _get_fiscal_year(from_date),
        "to_fiscal_year": _get_fiscal_year(to_date),
        "periodicity": periodicity,
        "accumulated_values": 0,
        "include_default_book_entries": 1
    }

    if report_name in ["Profit and Loss Statement", "Cash Flow"]:
        filters["filter_based_on"] = "Date Range"
        filters["period_start_date"] = from_date
        filters["period_end_date"] = to_date

    try:
        result = run(report_name, filters=filters, user=user)
        return format_report_for_ai(result, max_rows=30)
    except Exception as e:
        frappe.log_error(f"Report execution error: {str(e)}", "Financial Report Error")
        return f"Error executing report: {str(e)}"


@with_permission_check("Sales Invoice", "read")
@with_company_check()
@with_audit_logging("get_revenue")
def get_revenue(
    from_date: str,
    to_date: str,
    company: Optional[str] = None,
    session_id: Optional[str] = None,
    audit_log_id: Optional[str] = None,
    user: Optional[str] = None
) -> str:
    """
    Get total revenue from Sales Invoices for a date range.

    Args:
        from_date: Start date (YYYY-MM-DD)
        to_date: End date (YYYY-MM-DD)
        company: Company name (optional)
        session_id: Chat session ID for audit logging
        audit_log_id: Parent audit log ID
        user: User making the request

    Returns:
        Revenue summary as string
    """
    if not company:
        company = get_user_default_company(user)

    filters = {
        "docstatus": 1,  # Submitted invoices only
        "posting_date": ["between", [from_date, to_date]]
    }

    if company:
        filters["company"] = company

    # Get total revenue
    result = frappe.db.get_all(
        "Sales Invoice",
        filters=filters,
        fields=["SUM(grand_total) as total_revenue", "COUNT(*) as invoice_count"]
    )

    if result and result[0].get("total_revenue"):
        total = result[0].get("total_revenue", 0)
        count = result[0].get("invoice_count", 0)

        # Get currency
        currency = frappe.db.get_value("Company", company, "default_currency") or "USD"

        return (
            f"Total Revenue from {from_date} to {to_date}:\n"
            f"- Amount: {currency} {total:,.2f}\n"
            f"- Number of invoices: {count}\n"
            f"- Company: {company or 'All companies'}"
        )
    else:
        return f"No revenue data found for the period {from_date} to {to_date}."


@with_permission_check("GL Entry", "read")
@with_company_check()
@with_audit_logging("get_expenses")
def get_expenses(
    from_date: str,
    to_date: str,
    company: Optional[str] = None,
    session_id: Optional[str] = None,
    audit_log_id: Optional[str] = None,
    user: Optional[str] = None
) -> str:
    """
    Get total expenses for a date range.

    Args:
        from_date: Start date (YYYY-MM-DD)
        to_date: End date (YYYY-MM-DD)
        company: Company name (optional)
        session_id: Chat session ID for audit logging
        audit_log_id: Parent audit log ID
        user: User making the request

    Returns:
        Expenses summary as string
    """
    if not company:
        company = get_user_default_company(user)

    # Get expense accounts
    expense_accounts = frappe.get_all(
        "Account",
        filters={
            "root_type": "Expense",
            "is_group": 0,
            "company": company
        },
        pluck="name"
    )

    if not expense_accounts:
        return f"No expense accounts found for company {company}."

    # Get total expenses from GL Entry
    filters = {
        "account": ["in", expense_accounts],
        "posting_date": ["between", [from_date, to_date]],
        "is_cancelled": 0
    }

    if company:
        filters["company"] = company

    result = frappe.db.get_all(
        "GL Entry",
        filters=filters,
        fields=["SUM(debit - credit) as total_expense"]
    )

    if result and result[0].get("total_expense"):
        total = result[0].get("total_expense", 0)
        currency = frappe.db.get_value("Company", company, "default_currency") or "USD"

        return (
            f"Total Expenses from {from_date} to {to_date}:\n"
            f"- Amount: {currency} {total:,.2f}\n"
            f"- Company: {company or 'All companies'}"
        )
    else:
        return f"No expense data found for the period {from_date} to {to_date}."


@with_permission_check("GL Entry", "read")
@with_company_check()
@with_audit_logging("get_profit_and_loss")
def get_profit_and_loss(
    from_date: str,
    to_date: str,
    company: Optional[str] = None,
    session_id: Optional[str] = None,
    audit_log_id: Optional[str] = None,
    user: Optional[str] = None
) -> str:
    """
    Get profit and loss summary for a date range.

    Args:
        from_date: Start date (YYYY-MM-DD)
        to_date: End date (YYYY-MM-DD)
        company: Company name (optional)

    Returns:
        P&L summary as string
    """
    return get_financial_report(
        report_name="Profit and Loss Statement",
        from_date=from_date,
        to_date=to_date,
        company=company,
        periodicity="Monthly",
        session_id=session_id,
        audit_log_id=audit_log_id,
        user=user
    )


@with_permission_check("GL Entry", "read")
@with_company_check()
@with_audit_logging("get_balance_sheet")
def get_balance_sheet(
    to_date: str,
    company: Optional[str] = None,
    session_id: Optional[str] = None,
    audit_log_id: Optional[str] = None,
    user: Optional[str] = None
) -> str:
    """
    Get balance sheet as of a specific date.

    Args:
        to_date: As-of date (YYYY-MM-DD)
        company: Company name (optional)

    Returns:
        Balance sheet summary as string
    """
    # Balance sheet is point-in-time, so from_date = start of fiscal year
    fiscal_year_start = _get_fiscal_year_start(to_date)

    return get_financial_report(
        report_name="Balance Sheet",
        from_date=fiscal_year_start,
        to_date=to_date,
        company=company,
        periodicity="Yearly",
        session_id=session_id,
        audit_log_id=audit_log_id,
        user=user
    )


def _get_fiscal_year(date_str: str) -> str:
    """Get fiscal year name for a date."""
    try:
        date = getdate(date_str)
        fiscal_year = frappe.db.get_value(
            "Fiscal Year",
            {
                "year_start_date": ["<=", date],
                "year_end_date": [">=", date]
            },
            "name"
        )
        return fiscal_year or str(date.year)
    except Exception:
        return str(getdate(date_str).year)


def _get_fiscal_year_start(date_str: str) -> str:
    """Get fiscal year start date for a given date."""
    try:
        date = getdate(date_str)
        fiscal_year = frappe.db.get_value(
            "Fiscal Year",
            {
                "year_start_date": ["<=", date],
                "year_end_date": [">=", date]
            },
            "year_start_date"
        )
        return str(fiscal_year) if fiscal_year else f"{date.year}-01-01"
    except Exception:
        return f"{getdate(date_str).year}-01-01"


# Tool execution dispatcher
TOOL_FUNCTIONS = {
    "get_financial_report": get_financial_report,
    "get_revenue": get_revenue,
    "get_expenses": get_expenses,
    "get_profit_and_loss": get_profit_and_loss,
    "get_balance_sheet": get_balance_sheet,
}
