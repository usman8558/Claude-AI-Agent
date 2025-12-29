"""
Response Formatter Utilities

Format ERPNext report data and query results for AI consumption.
"""

import json
from typing import Any, Dict, List, Optional
from frappe.utils import flt, fmt_money


def format_report_for_ai(
    result: Dict[str, Any],
    max_rows: int = 50,
    include_totals: bool = True
) -> str:
    """
    Format ERPNext report result for AI consumption.

    Args:
        result: Report result from frappe.desk.query_report.run()
        max_rows: Maximum rows to include in response
        include_totals: Whether to calculate and include totals

    Returns:
        Formatted string suitable for AI context
    """
    if not result:
        return "No data available."

    columns = result.get("columns", [])
    data = result.get("result", []) or result.get("data", [])
    report_summary = result.get("report_summary", [])

    if not data:
        return "The report returned no results for the given criteria."

    # Format output
    output_parts = []

    # Add column headers info
    col_names = [_get_column_label(col) for col in columns]

    # Limit rows
    if len(data) > max_rows:
        output_parts.append(f"Showing first {max_rows} of {len(data)} total rows.\n")
        data = data[:max_rows]

    # Format as readable table
    output_parts.append("| " + " | ".join(col_names) + " |")
    output_parts.append("|" + "|".join(["---"] * len(col_names)) + "|")

    for row in data:
        if isinstance(row, dict):
            row_values = [_format_value(row.get(col.get("fieldname", col) if isinstance(col, dict) else col, ""))
                         for col in columns]
        elif isinstance(row, (list, tuple)):
            row_values = [_format_value(val) for val in row]
        else:
            continue
        output_parts.append("| " + " | ".join(row_values) + " |")

    # Add report summary if available
    if report_summary:
        output_parts.append("\n**Summary:**")
        for item in report_summary:
            if isinstance(item, dict):
                label = item.get("label", "")
                value = item.get("value", "")
                output_parts.append(f"- {label}: {_format_value(value)}")

    # Calculate totals for numeric columns if requested
    if include_totals and data:
        totals = _calculate_totals(columns, data)
        if totals:
            output_parts.append("\n**Totals:**")
            for col_name, total in totals.items():
                output_parts.append(f"- {col_name}: {_format_value(total)}")

    return "\n".join(output_parts)


def format_list_for_ai(
    data: List[Dict[str, Any]],
    fields: Optional[List[str]] = None,
    max_items: int = 20
) -> str:
    """
    Format a list of documents for AI consumption.

    Args:
        data: List of dictionaries
        fields: Fields to include (None for all)
        max_items: Maximum items to include

    Returns:
        Formatted string suitable for AI context
    """
    if not data:
        return "No items found."

    # Limit items
    total_count = len(data)
    if len(data) > max_items:
        data = data[:max_items]

    # Determine fields to show
    if not fields and data:
        fields = list(data[0].keys())

    output_parts = []

    if total_count > max_items:
        output_parts.append(f"Showing {max_items} of {total_count} total items:\n")

    for i, item in enumerate(data, 1):
        item_parts = [f"{i}. "]
        for field in fields:
            value = item.get(field, "")
            if value:
                # Clean field name for display
                display_name = field.replace("_", " ").title()
                item_parts.append(f"{display_name}: {_format_value(value)}")
        output_parts.append(", ".join(item_parts[1:]))

    return "\n".join(output_parts)


def format_single_value(
    value: Any,
    label: Optional[str] = None,
    currency: bool = False,
    currency_symbol: str = "$"
) -> str:
    """
    Format a single value with optional label.

    Args:
        value: Value to format
        label: Optional label
        currency: Whether to format as currency
        currency_symbol: Currency symbol to use

    Returns:
        Formatted string
    """
    if currency:
        formatted = f"{currency_symbol}{flt(value):,.2f}"
    else:
        formatted = _format_value(value)

    if label:
        return f"{label}: {formatted}"
    return formatted


def _get_column_label(col: Any) -> str:
    """Extract column label from column definition."""
    if isinstance(col, dict):
        return col.get("label", col.get("fieldname", str(col)))
    return str(col)


def _format_value(value: Any) -> str:
    """Format a value for display."""
    if value is None:
        return "-"
    if isinstance(value, float):
        # Format numbers with appropriate precision
        if value == int(value):
            return f"{int(value):,}"
        return f"{value:,.2f}"
    if isinstance(value, int):
        return f"{value:,}"
    if isinstance(value, (list, dict)):
        return json.dumps(value)
    return str(value)


def _calculate_totals(columns: List[Any], data: List[Any]) -> Dict[str, float]:
    """Calculate totals for numeric columns."""
    totals = {}

    for col in columns:
        if isinstance(col, dict):
            fieldname = col.get("fieldname", "")
            fieldtype = col.get("fieldtype", "")
            label = col.get("label", fieldname)

            # Only sum numeric columns
            if fieldtype in ["Currency", "Float", "Int", "Percent"]:
                total = 0
                for row in data:
                    if isinstance(row, dict):
                        val = row.get(fieldname, 0)
                    elif isinstance(row, (list, tuple)):
                        idx = columns.index(col)
                        val = row[idx] if idx < len(row) else 0
                    else:
                        val = 0

                    if val:
                        total += flt(val)

                if total != 0:
                    totals[label] = total

    return totals


def summarize_for_context(
    text: str,
    max_length: int = 2000
) -> str:
    """
    Summarize text to fit within context window limits.

    Args:
        text: Text to summarize
        max_length: Maximum length

    Returns:
        Truncated text with indicator if truncated
    """
    if len(text) <= max_length:
        return text

    return text[:max_length - 50] + "\n\n[... truncated for brevity]"
