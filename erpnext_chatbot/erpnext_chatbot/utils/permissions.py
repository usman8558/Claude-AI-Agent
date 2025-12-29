"""
Permission Utilities

Helper functions for validating ERPNext permissions and company access.
"""

import frappe
from frappe import _
from typing import Optional, List


def validate_permission(
    doctype: str,
    ptype: str = "read",
    user: Optional[str] = None,
    throw: bool = True
) -> bool:
    """
    Validate user has permission for a DocType.

    Args:
        doctype: The DocType to check
        ptype: Permission type (read/write/create/delete)
        user: User to check (defaults to current user)
        throw: Whether to throw exception on failure

    Returns:
        True if permission granted

    Raises:
        frappe.PermissionError: If throw=True and permission denied
    """
    if user is None:
        user = frappe.session.user

    # Administrator has all permissions
    if user == "Administrator":
        return True

    has_perm = frappe.has_permission(doctype, ptype=ptype, user=user)

    if not has_perm and throw:
        frappe.throw(
            _("You do not have {0} permission for {1}").format(ptype, doctype),
            frappe.PermissionError
        )

    return has_perm


def validate_company_access(
    company: str,
    user: Optional[str] = None,
    throw: bool = True
) -> bool:
    """
    Validate user has access to a company.

    Args:
        company: Company name to check
        user: User to check (defaults to current user)
        throw: Whether to throw exception on failure

    Returns:
        True if access granted

    Raises:
        frappe.PermissionError: If throw=True and access denied
    """
    if user is None:
        user = frappe.session.user

    # Administrator has access to all companies
    if user == "Administrator":
        return True

    # Get user's allowed companies
    allowed_companies = get_user_companies(user)

    # If no company restrictions, user has access to all
    if not allowed_companies:
        return True

    has_access = company in allowed_companies

    if not has_access and throw:
        frappe.throw(
            _("You do not have access to company {0}").format(company),
            frappe.PermissionError
        )

    return has_access


def get_user_companies(user: Optional[str] = None) -> List[str]:
    """
    Get list of companies user has access to.

    Args:
        user: User to check (defaults to current user)

    Returns:
        List of company names user can access
    """
    if user is None:
        user = frappe.session.user

    # Administrator has access to all companies
    if user == "Administrator":
        return frappe.get_all("Company", pluck="name")

    # Check User Permission for Company
    user_permissions = frappe.get_all(
        "User Permission",
        filters={
            "user": user,
            "allow": "Company"
        },
        pluck="for_value"
    )

    # Also check default company
    default_company = frappe.defaults.get_user_default("Company", user)
    if default_company and default_company not in user_permissions:
        user_permissions.append(default_company)

    return user_permissions


def get_user_default_company(user: Optional[str] = None) -> Optional[str]:
    """
    Get user's default company.

    Args:
        user: User to check (defaults to current user)

    Returns:
        Default company name or None
    """
    if user is None:
        user = frappe.session.user

    return frappe.defaults.get_user_default("Company", user)


def validate_report_access(
    report_name: str,
    user: Optional[str] = None,
    throw: bool = True
) -> bool:
    """
    Validate user has access to a report.

    Args:
        report_name: Name of the report
        user: User to check (defaults to current user)
        throw: Whether to throw exception on failure

    Returns:
        True if access granted

    Raises:
        frappe.PermissionError: If throw=True and access denied
    """
    if user is None:
        user = frappe.session.user

    # Administrator has access to all reports
    if user == "Administrator":
        return True

    # Check if report exists
    if not frappe.db.exists("Report", report_name):
        if throw:
            frappe.throw(
                _("Report not found: {0}").format(report_name),
                frappe.DoesNotExistError
            )
        return False

    # Get report's ref_doctype
    report = frappe.get_doc("Report", report_name)

    # Check permission on reference DocType
    if report.ref_doctype:
        return validate_permission(report.ref_doctype, "read", user, throw)

    # If no ref_doctype, check report-level permission
    return frappe.has_permission("Report", ptype="read", doc=report_name, user=user)


def check_role(
    role: str,
    user: Optional[str] = None
) -> bool:
    """
    Check if user has a specific role.

    Args:
        role: Role name to check
        user: User to check (defaults to current user)

    Returns:
        True if user has the role
    """
    if user is None:
        user = frappe.session.user

    if user == "Administrator":
        return True

    user_roles = frappe.get_roles(user)
    return role in user_roles
