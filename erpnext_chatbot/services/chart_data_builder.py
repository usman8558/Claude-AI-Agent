"""
Chart Data Builder Service

Builds chart-compatible data from ERPNext reports and query results.
Supports bar, line, and pie charts with proper data aggregation.
"""

import json
import frappe
from typing import Dict, Any, List, Optional, Tuple
from collections import defaultdict


# Default color palette (ERPNext theme)
DEFAULT_COLORS = [
    '#2491eb',  # Primary blue
    '#5e64ff',  # Purple
    '#00c3b3',  # Teal
    '#28c76f',  # Green
    '#ff6b6b',  # Coral red
    '#f9c846',  # Yellow
    '#743ee2',  # Deep purple
    '#ea5455',  # Red
    '#a5a5a5',  # Gray
    '#1a1a2e',  # Dark blue
]

# Chart type detection keywords
CHART_TYPE_KEYWORDS = {
    'line': ['trend', 'over time', 'growth', 'progress', 'evolution', 'history', 'months', 'years', 'quarterly'],
    'bar': ['top', 'comparison', 'ranking', 'by category', 'by department', 'by customer', 'by product'],
    'pie': ['distribution', 'breakdown', 'share', 'percentage', 'proportion', 'composition', 'among']
}

# Constraints
MAX_DATA_POINTS = 50
MIN_DATA_POINTS = 2


class ChartDataBuilder:
    """
    Builds structured chart data from ERPNext reports and query results.
    """

    def __init__(self):
        self.max_data_points = MAX_DATA_POINTS

    def build_chart_data(
        self,
        data: List[Dict[str, Any]],
        labels_field: str,
        values_field: str,
        chart_type: str = 'bar',
        title: Optional[str] = None,
        x_axis_label: Optional[str] = None,
        y_axis_label: Optional[str] = None,
        colors: Optional[List[str]] = None,
        limit: int = MAX_DATA_POINTS
    ) -> Optional[Dict[str, Any]]:
        """
        Build chart data from a list of dictionaries.

        Args:
            data: List of dictionaries with label and value fields
            labels_field: Field name for labels
            values_field: Field name for values
            chart_type: Type of chart (bar, line, pie)
            title: Optional chart title
            x_axis_label: Optional X-axis label
            y_axis_label: Optional Y-axis label
            colors: Optional list of hex color codes
            limit: Maximum number of data points

        Returns:
            Chart data dictionary or None if insufficient data
        """
        if not data or len(data) < MIN_DATA_POINTS:
            return None

        # Extract and limit data
        extracted_data = self._extract_data(data, labels_field, values_field, limit)

        if not extracted_data or len(extracted_data) < MIN_DATA_POINTS:
            return None

        labels = [item['label'] for item in extracted_data]
        values = [item['value'] for item in extracted_data]

        return {
            'chart_type': chart_type,
            'title': title or f'{values_field.title()} by {labels_field.title()}',
            'labels': labels,
            'values': values,
            'x_axis_label': x_axis_label,
            'y_axis_label': y_axis_label,
            'colors': colors or DEFAULT_COLORS[:len(values)]
        }

    def build_from_report_result(
        self,
        report_result: Dict[str, Any],
        label_column: str,
        value_column: str,
        chart_type: str = 'bar',
        title: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Build chart data from an ERPNext report result.

        Args:
            report_result: Result from frappe.desk.query_report.run()
            label_column: Column name to use for labels
            value_column: Column name to use for values
            chart_type: Type of chart
            title: Optional chart title

        Returns:
            Chart data dictionary or None
        """
        if not report_result:
            return None

        data = report_result.get('result') or report_result.get('data', [])
        columns = report_result.get('columns', [])

        if not data:
            return None

        # Convert data to list of dicts if needed
        if isinstance(data, list) and len(data) > 0:
            if isinstance(data[0], (list, tuple)):
                # Convert from list of lists using column info
                data = self._convert_list_of_lists(data, columns)

        # Build chart data
        return self.build_chart_data(
            data=data,
            labels_field=label_column,
            values_field=value_column,
            chart_type=chart_type,
            title=title
        )

    def _extract_data(
        self,
        data: List[Dict[str, Any]],
        labels_field: str,
        values_field: str,
        limit: int
    ) -> List[Dict[str, Any]]:
        """Extract label-value pairs from data."""
        result = []

        for item in data:
            if isinstance(item, dict):
                label = item.get(labels_field)
                value = item.get(values_field)

                # Skip if label or value is missing
                if label is None or value is None:
                    continue

                # Convert value to float
                try:
                    value = float(value)
                except (ValueError, TypeError):
                    continue

                result.append({'label': str(label), 'value': value})

                if len(result) >= limit:
                    break

        return result

    def _convert_list_of_lists(
        self,
        data: List[Any],
        columns: List[Any]
    ) -> List[Dict[str, Any]]:
        """Convert list of lists to list of dicts using column info."""
        result = []

        for row in data:
            if isinstance(row, (list, tuple)):
                row_dict = {}
                for i, col in enumerate(columns):
                    if isinstance(col, dict):
                        fieldname = col.get('fieldname', col.get('label', str(i)))
                    else:
                        fieldname = str(col)

                    if i < len(row):
                        row_dict[fieldname] = row[i]

                result.append(row_dict)

        return result

    def aggregate_for_bar_chart(
        self,
        data: List[Dict[str, Any]],
        label_field: str,
        value_field: str,
        sort_by: str = 'value',
        ascending: bool = False,
        limit: int = MAX_DATA_POINTS
    ) -> Optional[Dict[str, Any]]:
        """
        Aggregate data for bar chart with sorting.

        Args:
            data: List of dictionaries
            label_field: Field for category labels
            value_field: Field for numeric values
            sort_by: Sort by 'value' or 'label'
            ascending: Sort ascending if True
            limit: Maximum number of bars

        Returns:
            Chart data dictionary
        """
        # Extract and aggregate
        aggregated = defaultdict(float)
        for item in data:
            if isinstance(item, dict):
                label = str(item.get(label_field, 'Unknown'))
                try:
                    value = float(item.get(value_field, 0))
                    aggregated[label] += value
                except (ValueError, TypeError):
                    continue

        # Sort
        if sort_by == 'value':
            sorted_items = sorted(aggregated.items(), key=lambda x: x[1], reverse=not ascending)
        else:
            sorted_items = sorted(aggregated.items(), key=lambda x: x[0], reverse=not ascending)

        # Take top N
        sorted_items = sorted_items[:limit]

        if len(sorted_items) < MIN_DATA_POINTS:
            return None

        labels = [item[0] for item in sorted_items]
        values = [item[1] for item in sorted_items]

        return {
            'chart_type': 'bar',
            'title': f'{value_field.title()} by {label_field.title()}',
            'labels': labels,
            'values': values,
            'x_axis_label': label_field.title(),
            'y_axis_label': value_field.title(),
            'colors': DEFAULT_COLORS[:len(values)]
        }

    def aggregate_for_line_chart(
        self,
        data: List[Dict[str, Any]],
        time_field: str,
        value_field: str,
        limit: int = MAX_DATA_POINTS
    ) -> Optional[Dict[str, Any]]:
        """
        Aggregate data for line chart (time series).

        Args:
            data: List of dictionaries with time and value fields
            time_field: Field for time period labels
            value_field: Field for numeric values
            limit: Maximum number of points

        Returns:
            Chart data dictionary
        """
        # Sort by time field (assuming chronological order in data)
        sorted_data = []
        for item in data:
            if isinstance(item, dict):
                time_val = item.get(time_field)
                value = item.get(value_field)
                if time_val is not None and value is not None:
                    try:
                        sorted_data.append({
                            'time': str(time_val),
                            'value': float(value)
                        })
                    except (ValueError, TypeError):
                        continue

        if len(sorted_data) < MIN_DATA_POINTS:
            return None

        # Limit
        sorted_data = sorted_data[:limit]

        labels = [item['time'] for item in sorted_data]
        values = [item['value'] for item in sorted_data]

        return {
            'chart_type': 'line',
            'title': f'{value_field.title()} Over Time',
            'labels': labels,
            'values': values,
            'x_axis_label': time_field.title(),
            'y_axis_label': value_field.title(),
            'colors': [DEFAULT_COLORS[0]]  # Single color for line
        }

    def calculate_distribution(
        self,
        data: List[Dict[str, Any]],
        category_field: str,
        value_field: str,
        limit: int = MAX_DATA_POINTS
    ) -> Optional[Dict[str, Any]]:
        """
        Calculate distribution for pie chart.

        Args:
            data: List of dictionaries
            category_field: Field for category labels
            value_field: Field for numeric values
            limit: Maximum number of segments

        Returns:
            Chart data dictionary
        """
        # Aggregate by category
        aggregated = defaultdict(float)
        for item in data:
            if isinstance(item, dict):
                category = str(item.get(category_field, 'Other'))
                try:
                    value = float(item.get(value_field, 0))
                    aggregated[category] += value
                except (ValueError, TypeError):
                    continue

        # Calculate percentages
        total = sum(aggregated.values())
        if total == 0:
            return None

        # Sort by value descending and limit
        sorted_items = sorted(aggregated.items(), key=lambda x: x[1], reverse=True)
        sorted_items = sorted_items[:limit]

        # Calculate percentages
        percentages = [(cat, (val / total) * 100) for cat, val in sorted_items]

        if len(percentages) < MIN_DATA_POINTS:
            return None

        labels = [item[0] for item in percentages]
        values = [round(item[1], 2) for item in percentages]

        return {
            'chart_type': 'pie',
            'title': f'{value_field.title()} Distribution by {category_field}',
            'labels': labels,
            'values': values,
            'colors': DEFAULT_COLORS[:len(values)],
            'description': f'Total: {total:,.0f}'
        }

    def detect_chart_type(self, query: str, data: List[Dict] = None) -> str:
        """
        Detect appropriate chart type based on user query.

        Args:
            query: User's natural language query
            data: Optional data preview for pattern detection

        Returns:
            Detected chart type: 'bar', 'line', or 'pie'
        """
        query_lower = query.lower()

        # Check keywords
        line_score = sum(1 for kw in CHART_TYPE_KEYWORDS['line'] if kw in query_lower)
        bar_score = sum(1 for kw in CHART_TYPE_KEYWORDS['bar'] if kw in query_lower)
        pie_score = sum(1 for kw in CHART_TYPE_KEYWORDS['pie'] if kw in query_lower)

        # Check for explicit chart type mentions
        if 'pie chart' in query_lower or 'donut chart' in query_lower:
            return 'pie'
        if 'bar chart' in query_lower:
            return 'bar'
        if 'line chart' in query_lower or 'trend' in query_lower:
            return 'line'

        # Default to bar if scores are equal or bar has higher score
        if bar_score >= line_score and bar_score >= pie_score:
            return 'bar'
        elif line_score > bar_score and line_score >= pie_score:
            return 'line'
        else:
            return 'pie'

    def format_chart_response(
        self,
        text: str,
        chart_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Format a complete response with chart data.

        Args:
            text: Natural language explanation
            chart_data: Chart data dictionary

        Returns:
            Complete response object
        """
        return {
            'response_type': 'text_with_chart',
            'text': text,
            'chart': chart_data
        }

    def parse_chart_from_text(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Try to parse chart data embedded in text response.

        Args:
            text: Response text that may contain chart JSON

        Returns:
            Parsed chart data or None
        """
        # Look for JSON-like patterns
        import re

        # Try to find JSON object with chart_type
        json_pattern = r'\{[^{}]*"chart_type"[^{}]*\}'
        match = re.search(json_pattern, text)

        if match:
            try:
                chart_data = json.loads(match.group())
                # Validate required fields
                if 'chart_type' in chart_data and 'labels' in chart_data and 'values' in chart_data:
                    return chart_data
            except (json.JSONDecodeError, KeyError):
                pass

        return None


# Convenience functions
def build_chart_from_report(
    report_name: str,
    filters: Dict[str, Any],
    label_column: str,
    value_column: str,
    chart_type: str = 'bar'
) -> Optional[Dict[str, Any]]:
    """
    Build chart data directly from an ERPNext report.

    Args:
        report_name: Name of the report
        filters: Report filters
        label_column: Column for labels
        value_column: Column for values
        chart_type: Type of chart

    Returns:
        Chart data dictionary
    """
    try:
        result = frappe.desk.query_report.run(report_name, filters=filters)

        builder = ChartDataBuilder()
        return builder.build_from_report_result(
            report_result=result,
            label_column=label_column,
            value_column=value_column,
            chart_type=chart_type
        )
    except Exception as e:
        frappe.log_error(f"Failed to build chart from report {report_name}: {str(e)}")
        return None


def create_sales_trend_chart(
    from_date: str,
    to_date: str,
    group_by: str = 'month'
) -> Optional[Dict[str, Any]]:
    """
    Create a sales trend line chart.

    Args:
        from_date: Start date (YYYY-MM-DD)
        to_date: End date (YYYY-MM-DD)
        group_by: Time grouping ('month', 'week', 'day')

    Returns:
        Chart data dictionary
    """
    try:
        # Get sales data from Sales Invoice report
        result = frappe.desk.query_report.run(
            'Sales Invoice',
            filters={
                'from_date': from_date,
                'to_date': to_date,
                'status': ['!=', 'Cancelled']
            }
        )

        # Build line chart
        builder = ChartDataBuilder()
        return builder.build_from_report_result(
            report_result=result,
            label_column='posting_date',
            value_column='grand_total',
            chart_type='line',
            title='Sales Trend'
        )
    except Exception as e:
        frappe.log_error(f"Failed to create sales trend chart: {str(e)}")
        return None


def create_top_customers_chart(
    from_date: str,
    to_date: str,
    limit: int = 10
) -> Optional[Dict[str, Any]]:
    """
    Create a top customers bar chart.

    Args:
        from_date: Start date
        to_date: End date
        limit: Number of customers to show

    Returns:
        Chart data dictionary
    """
    try:
        # Get sales analytics report
        result = frappe.desk.query_report.run(
            'Sales Analytics',
            filters={
                'from_date': from_date,
                'to_date': to_date,
                'group_by': 'Customer'
            }
        )

        # Build bar chart
        builder = ChartDataBuilder()
        return builder.aggregate_for_bar_chart(
            data=result.get('result', []),
            label_field='customer',
            value_field='total_sales',
            sort_by='value',
            ascending=False,
            limit=limit
        )
    except Exception as e:
        frappe.log_error(f"Failed to create top customers chart: {str(e)}")
        return None
