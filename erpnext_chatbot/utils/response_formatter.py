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


# =============================================================================
# Chart Formatting Functions
# =============================================================================

def format_report_for_chart(
    result: Dict[str, Any],
    label_column: str = None,
    value_column: str = None,
    max_points: int = 50
) -> Dict[str, Any]:
    """
    Format ERPNext report result for chart rendering.

    Args:
        result: Report result from frappe.desk.query_report.run()
        label_column: Column name for chart labels (auto-detected if None)
        value_column: Column name for chart values (auto-detected if None)
        max_points: Maximum number of data points

    Returns:
        Dictionary with labels and values arrays, or empty dict if insufficient data
    """
    if not result:
        return {}

    columns = result.get("columns", [])
    data = result.get("result", []) or result.get("data", [])

    if not data or len(data) < 2:
        return {}

    # Auto-detect columns if not specified
    if not label_column or not value_column:
        detected = _detect_chart_columns(columns, data)
        if not label_column:
            label_column = detected['label']
        if not value_column:
            value_column = detected['value']

    labels = []
    values = []

    for row in data:
        if isinstance(row, dict):
            label = row.get(label_column)
            value = row.get(value_column)
        elif isinstance(row, (list, tuple)):
            label = _get_column_value(columns, label_column, row)
            value = _get_column_value(columns, value_column, row)
        else:
            continue

        if label is not None and value is not None:
            try:
                labels.append(str(label))
                values.append(float(value))
            except (ValueError, TypeError):
                continue

        if len(labels) >= max_points:
            break

    if len(labels) < 2:
        return {}

    return {
        "labels": labels,
        "values": values
    }


def extract_chart_labels_values(
    data: List[Dict[str, Any]],
    label_field: str,
    value_field: str,
    max_points: int = 50
) -> Dict[str, Any]:
    """
    Extract labels and values from a list of dictionaries.

    Args:
        data: List of dictionaries
        label_field: Field name for labels
        value_field: Field name for values
        max_points: Maximum number of points

    Returns:
        Dictionary with labels and values arrays
    """
    labels = []
    values = []

    for item in data:
        if not isinstance(item, dict):
            continue

        label = item.get(label_field)
        value = item.get(value_field)

        if label is not None and value is not None:
            try:
                labels.append(str(label))
                values.append(float(value))
            except (ValueError, TypeError):
                continue

        if len(labels) >= max_points:
            break

    return {
        "labels": labels,
        "values": values,
        "count": len(labels)
    }


def detect_chart_type(query: str) -> str:
    """
    Detect appropriate chart type based on user query.

    Args:
        query: User's natural language query

    Returns:
        Chart type: 'bar', 'line', or 'pie'
    """
    query_lower = query.lower()

    # Chart type keywords
    line_keywords = ['trend', 'over time', 'growth', 'progress', 'evolution',
                     'history', 'months', 'years', 'quarterly', 'over the past']
    bar_keywords = ['top', 'comparison', 'ranking', 'by category', 'by department',
                    'by customer', 'by product', 'list', 'show me']
    pie_keywords = ['distribution', 'breakdown', 'share', 'percentage',
                    'proportion', 'composition', 'among']

    # Count matches
    line_score = sum(1 for kw in line_keywords if kw in query_lower)
    bar_score = sum(1 for kw in bar_keywords if kw in query_lower)
    pie_score = sum(1 for kw in pie_keywords if kw in query_lower)

    # Explicit chart type mentions
    if 'pie chart' in query_lower or 'donut chart' in query_lower:
        return 'pie'
    if 'bar chart' in query_lower:
        return 'bar'
    if 'line chart' in query_lower or 'trend' in query_lower:
        return 'line'

    # Default logic
    if bar_score >= line_score and bar_score >= pie_score:
        return 'bar'
    elif line_score > bar_score and line_score >= pie_score:
        return 'line'
    else:
        return 'pie'


def build_chart_metadata(
    chart_type: str,
    title: str,
    labels: List[str],
    values: List[float],
    x_axis_label: str = None,
    y_axis_label: str = None,
    colors: List[str] = None
) -> Dict[str, Any]:
    """
    Build complete chart metadata dictionary.

    Args:
        chart_type: Type of chart (bar, line, pie)
        title: Chart title
        labels: Array of labels
        values: Array of values
        x_axis_label: Optional X-axis label
        y_axis_label: Optional Y-axis label
        colors: Optional array of hex colors

    Returns:
        Chart metadata dictionary
    """
    default_colors = [
        '#2491eb', '#5e64ff', '#00c3b3', '#28c76f', '#ff6b6b',
        '#f9c846', '#743ee2', '#ea5455', '#a5a5a5', '#1a1a2e'
    ]

    return {
        "chart_type": chart_type,
        "title": title,
        "labels": labels,
        "values": values,
        "x_axis_label": x_axis_label,
        "y_axis_label": y_axis_label,
        "colors": colors or default_colors[:len(values)]
    }


def _detect_chart_columns(
    columns: List[Any],
    data: List[Any]
) -> Dict[str, str]:
    """
    Automatically detect label and value columns for charts.

    Args:
        columns: Column definitions
        data: Report data rows

    Returns:
        Dictionary with 'label' and 'value' column names
    """
    if not columns or not data:
        return {"label": None, "value": None}

    # Get first data row
    first_row = data[0]
    if not isinstance(first_row, dict):
        return {"label": None, "value": None}

    data_keys = list(first_row.keys())

    # Find likely value column (numeric)
    value_column = None
    label_column = None

    # Common value column names
    value_names = ['amount', 'total', 'revenue', 'sales', 'grand_total', 'value',
                   'quantity', 'count', 'percentage', 'balance', 'debit', 'credit']

    for key in data_keys:
        key_lower = key.lower()
        if any(vn in key_lower for vn in value_names):
            # Check if numeric
            try:
                if first_row[key] is not None and float(first_row[key]) != float('nan'):
                    value_column = key
                    break
            except (ValueError, TypeError):
                continue

    # If no value column found, use last numeric column
    if not value_column:
        for key in reversed(data_keys):
            try:
                if first_row[key] is not None:
                    float(first_row[key])
                    value_column = key
                    break
            except (ValueError, TypeError):
                continue

    # Find likely label column (non-numeric, used for grouping)
    label_names = ['name', 'customer', 'item', 'product', 'category', 'department',
                   'account', 'date', 'month', 'year', 'party', 'warehouse']

    for key in data_keys:
        if key == value_column:
            continue
        key_lower = key.lower()
        if any(ln in key_lower for ln in label_names):
            label_column = key
            break

    # If no label column found, use first non-value column
    if not label_column:
        for key in data_keys:
            if key != value_column:
                label_column = key
                break

    return {"label": label_column, "value": value_column}


def _get_column_value(
    columns: List[Any],
    column_name: str,
    row: tuple
) -> Any:
    """Get column value from row by column name."""
    for i, col in enumerate(columns):
        if isinstance(col, dict):
            fieldname = col.get('fieldname', col.get('label'))
        else:
            fieldname = str(col)

        if fieldname == column_name and i < len(row):
            return row[i]

    return None
