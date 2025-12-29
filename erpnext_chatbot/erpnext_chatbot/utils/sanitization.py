"""
Input Sanitization Utilities

Sanitize user inputs to prevent injection attacks.
"""

import re
import html
import frappe
from frappe import _
from typing import Any, Dict


def sanitize_user_input(text: str, max_length: int = 10000) -> str:
    """
    Sanitize user input text to prevent injection attacks.

    Args:
        text: Raw user input
        max_length: Maximum allowed length

    Returns:
        Sanitized text

    Raises:
        frappe.ValidationError: If input exceeds max length
    """
    if not text:
        return ""

    # Check length
    if len(text) > max_length:
        frappe.throw(
            _("Input exceeds maximum length of {0} characters").format(max_length),
            frappe.ValidationError
        )

    # Strip control characters (except newlines and tabs)
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)

    # Escape HTML entities to prevent XSS
    text = html.escape(text)

    # Remove potential SQL injection patterns
    text = _remove_sql_patterns(text)

    return text.strip()


def _remove_sql_patterns(text: str) -> str:
    """
    Remove common SQL injection patterns from text.
    Note: This is defense-in-depth - primary protection is parameterized queries.

    Args:
        text: Input text

    Returns:
        Text with SQL patterns removed
    """
    # Common SQL injection patterns
    sql_patterns = [
        r";\s*--",  # SQL comment
        r";\s*DROP\s+",  # DROP statement
        r";\s*DELETE\s+",  # DELETE statement
        r";\s*UPDATE\s+",  # UPDATE statement
        r";\s*INSERT\s+",  # INSERT statement
        r"UNION\s+SELECT",  # UNION injection
        r"OR\s+1\s*=\s*1",  # OR injection
        r"AND\s+1\s*=\s*1",  # AND injection
    ]

    for pattern in sql_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)

    return text


def sanitize_dict(data: Dict[str, Any], max_depth: int = 5) -> Dict[str, Any]:
    """
    Recursively sanitize dictionary values.

    Args:
        data: Dictionary to sanitize
        max_depth: Maximum recursion depth

    Returns:
        Sanitized dictionary
    """
    if max_depth <= 0:
        return data

    sanitized = {}
    for key, value in data.items():
        # Sanitize key
        safe_key = sanitize_user_input(str(key), max_length=100)

        # Sanitize value based on type
        if isinstance(value, str):
            sanitized[safe_key] = sanitize_user_input(value)
        elif isinstance(value, dict):
            sanitized[safe_key] = sanitize_dict(value, max_depth - 1)
        elif isinstance(value, list):
            sanitized[safe_key] = [
                sanitize_user_input(str(v)) if isinstance(v, str)
                else sanitize_dict(v, max_depth - 1) if isinstance(v, dict)
                else v
                for v in value
            ]
        else:
            sanitized[safe_key] = value

    return sanitized


def validate_date_format(date_str: str) -> bool:
    """
    Validate date string is in YYYY-MM-DD format.

    Args:
        date_str: Date string to validate

    Returns:
        True if valid format
    """
    if not date_str:
        return False

    pattern = r'^\d{4}-\d{2}-\d{2}$'
    return bool(re.match(pattern, date_str))


def validate_report_name(report_name: str) -> bool:
    """
    Validate report name is safe and exists.

    Args:
        report_name: Report name to validate

    Returns:
        True if valid and exists
    """
    if not report_name:
        return False

    # Check for path traversal
    if '..' in report_name or '/' in report_name or '\\' in report_name:
        return False

    # Check report exists
    return frappe.db.exists("Report", report_name)
