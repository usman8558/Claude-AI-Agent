# Chart Data Contract

**Version**: 1.0
**Last Updated**: 2025-12-30

## Overview

This document defines the contract for chart data exchanged between the AI backend and the ERPNext frontend.

## Data Flow

```
AI Agent → Structured Output → Backend Parser → Chart Data Object → Frontend Renderer
```

## JSON Schema

### Chart Response Object

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "response_type": {
      "type": "string",
      "enum": ["text", "text_with_chart"],
      "description": "Indicates whether the response includes a chart"
    },
    "text": {
      "type": "string",
      "description": "Natural language explanation of the data"
    },
    "chart": {
      "type": "object",
      "description": "Chart metadata and data",
      "properties": {
        "chart_type": {
          "type": "string",
          "enum": ["bar", "line", "pie"],
          "description": "Type of chart to render"
        },
        "title": {
          "type": "string",
          "description": "Title displayed above the chart"
        },
        "labels": {
          "type": "array",
          "items": { "type": "string" },
          "description": "X-axis labels for bar/line, segment labels for pie"
        },
        "values": {
          "type": "array",
          "items": { "type": "number" },
          "description": "Data values corresponding to labels"
        },
        "description": {
          "type": "string",
          "description": "Optional description of the chart"
        },
        "x_axis_label": {
          "type": "string",
          "description": "Optional X-axis label"
        },
        "y_axis_label": {
          "type": "string",
          "description": "Optional Y-axis label"
        },
        "colors": {
          "type": "array",
          "items": { "type": "string" },
          "description": "Optional custom colors (hex codes)"
        }
      },
      "required": ["chart_type", "labels", "values"]
    }
  },
  "required": ["response_type", "text"]
}
```

## Chart Types

### Bar Chart

**Use Case**: Comparisons, rankings, top N lists

**Example**:
```json
{
  "response_type": "text_with_chart",
  "text": "Here are your top 5 customers by revenue this quarter:",
  "chart": {
    "chart_type": "bar",
    "title": "Top 5 Customers by Revenue",
    "labels": ["Customer A", "Customer B", "Customer C", "Customer D", "Customer E"],
    "values": [125000, 98000, 76500, 54300, 42100],
    "x_axis_label": "Customer",
    "y_axis_label": "Revenue ($)"
  }
}
```

**Best For**:
- "Top 10 products by sales"
- "Revenue by department"
- "Comparison of monthly expenses"

### Line Chart

**Use Case**: Trends over time, growth patterns

**Example**:
```json
{
  "response_type": "text_with_chart",
  "text": "Your monthly sales have shown steady growth over the past 6 months:",
  "chart": {
    "chart_type": "line",
    "title": "Monthly Sales Trend",
    "labels": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
    "values": [120000, 135000, 150000, 165000, 180000, 195000],
    "x_axis_label": "Month",
    "y_axis_label": "Sales ($)"
  }
}
```

**Best For**:
- "Sales trend over last 6 months"
- "Revenue growth year over year"
- "Expense trends by quarter"

### Pie Chart

**Use Case**: Distribution, proportions, shares

**Example**:
```json
{
  "response_with_chart",
  "text": "Here's how your expenses are distributed across categories:",
  "chart": {
    "chart_type": "pie",
   _type": "text "title": "Expense Distribution by Category",
    "labels": ["Payroll", "Marketing", "Operations", "IT", "Travel"],
    "values": [45, 20, 15, 12, 8],
    "description": "Percentage breakdown of total expenses"
  }
}
```

**Best For**:
- "Expense distribution"
- "Revenue by product category"
- "Market share by region"

## Constraints

| Constraint | Value | Notes |
|------------|-------|-------|
| Max labels | 50 | Performance optimization |
| Max values | 50 | Must match labels count |
| Min data points | 2 | Required for meaningful chart |
| Value type | number | Integers or floats |
| Label type | string | Max 100 characters each |

## Error Handling

### Invalid Chart Data

If chart data is malformed, the frontend should:
1. Log the error to console
2. Display the text response only
3. Show a warning icon indicating chart could not be rendered

```javascript
// Frontend error handling example
function parseChartData(rawResponse) {
  try {
    // Try to extract chart JSON from response
    const chartMatch = rawResponse.match(/\{[\s\S]*?"chart_type"[\s\S]*?\}/);
    if (chartMatch) {
      return JSON.parse(chartMatch[0]);
    }
    return null;
  } catch (e) {
    console.warn('Failed to parse chart data:', e);
    return null;
  }
}
```

## Frontend Integration

### Chart.js Configuration

```javascript
const chartDefaults = {
  responsive: true,
  maintainAspectRatio: true,
  plugins: {
    legend: {
      position: 'bottom'
    }
  },
  animation: {
    duration: 500
  }
};
```

### Color Palette

Default colors for charts (ERPNext theme):

```javascript
const chartColors = [
  '#2491eb',  // Primary blue
  '#5e64ff',  // Purple
  '#743ee2',  // Deep purple
  '#00c3b3',  // Teal
  '#ff6b6b',  // Coral red
  '#f9c846',  // Yellow
  '#28c76f',  // Green
  '#ea5455'   // Red
];
```

## Examples

### Complete Bar Chart Response

```json
{
  "response_type": "text_with_chart",
  "text": "**Top 5 Customers by Revenue - Q4 2024**\n\nCustomer A leads with $125,000 in revenue, followed by Customer B at $98,000. The top 5 customers together contributed $391,900 in total revenue.",
  "chart": {
    "chart_type": "bar",
    "title": "Top 5 Customers by Revenue",
    "labels": ["Customer A", "Customer B", "Customer C", "Customer D", "Customer E"],
    "values": [125000, 98000, 76500, 54300, 42100],
    "x_axis_label": "Customer",
    "y_axis_label": "Revenue ($)",
    "colors": ["#2491eb", "#5e64ff", "#00c3b3", "#28c76f", "#ff6b6b"]
  }
}
```

### Complete Line Chart Response

```json
{
  "response_type": "text_with_chart",
  "text": "**Monthly Revenue Trend - 2024**\n\nRevenue has grown consistently from $120,000 in January to $195,000 in June, representing a 62.5% increase over 6 months.",
  "chart": {
    "chart_type": "line",
    "title": "Monthly Revenue Trend",
    "labels": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
    "values": [120000, 135000, 150000, 165000, 180000, 195000],
    "x_axis_label": "Month",
    "y_axis_label": "Revenue ($)"
  }
}
```

### Complete Pie Chart Response

```json
{
  "response_type": "text_with_chart",
  "text": "**Expense Distribution - November 2024**\n\nPayroll accounts for the largest share (45%) of expenses, followed by Marketing (20%) and Operations (15%).",
  "chart": {
    "chart_type": "pie",
    "title": "Expense Distribution by Category",
    "labels": ["Payroll", "Marketing", "Operations", "IT", "Travel"],
    "values": [45, 20, 15, 12, 8],
    "description": "Percentage of total expenses"
  }
}
```
