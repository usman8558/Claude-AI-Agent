# Agent Tools: ERPNext Claude Chatbot

**Date**: 2025-12-29
**Feature**: 001-erpnext-claude-chatbot

## Overview

AI agent tool definitions following OpenAI function calling schema. All tools enforce permission checks before data access.

---

## Tool 1: get_financial_report

**Purpose**: Execute ERPNext financial reports (P&L, Balance Sheet, Cash Flow)

**OpenAI Function Schema**:
```json
{
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
        "format": "date",
        "description": "Start date in YYYY-MM-DD format"
      },
      "to_date": {
        "type": "string",
        "format": "date",
        "description": "End date in YYYY-MM-DD format"
      },
      "periodicity": {
        "type": "string",
        "enum": ["Monthly", "Quarterly", "Yearly"],
        "default": "Monthly"
      }
    },
    "required": ["report_name", "from_date", "to_date"]
  }
}
```

**Permission Checks**:
- User must have "Accounts User" or "Accounts Manager" role
- Company must be in user's allowed companies
- Report-level permissions enforced by Frappe

**Implementation**:
```python
def get_financial_report(report_name, company, from_date, to_date, periodicity="Monthly"):
    # Validate permissions
    if not frappe.has_permission("GL Entry", ptype="read"):
        raise frappe.PermissionError("No access to financial data")

    # Validate company access
    if company and company not in frappe.defaults.get_user_default_as_list("Company"):
        raise frappe.PermissionError(f"No access to company {company}")

    # Execute report
    from frappe.desk.query_report import run
    result = run(report_name, filters={
        "company": company or frappe.defaults.get_user_default("Company"),
        "from_date": from_date,
        "to_date": to_date,
        "periodicity": periodicity
    })

    return format_report_output(result)
```

---

## Tool 2: query_customers

**Purpose**: Search and retrieve customer data with filters

**OpenAI Function Schema**:
```json
{
  "name": "query_customers",
  "description": "Search customers by territory, customer group, or other filters. Returns customer details with permission enforcement.",
  "parameters": {
    "type": "object",
    "properties": {
      "territory": {
        "type": "string",
        "description": "Filter by territory (e.g., 'United States', 'Europe')"
      },
      "customer_group": {
        "type": "string",
        "description": "Filter by customer group (e.g., 'Commercial', 'Residential')"
      },
      "disabled": {
        "type": "boolean",
        "default": false,
        "description": "Include disabled customers"
      },
      "limit": {
        "type": "integer",
        "default": 20,
        "maximum": 100,
        "description": "Max number of results"
      }
    },
    "required": []
  }
}
```

**Permission Checks**:
- User must have read permission on Customer doctype
- Company filters applied automatically

**Implementation**:
```python
def query_customers(territory=None, customer_group=None, disabled=False, limit=20):
    if not frappe.has_permission("Customer", ptype="read"):
        raise frappe.PermissionError("No access to customer data")

    filters = {"disabled": 0 if not disabled else ("in", [0, 1])}
    if territory:
        filters["territory"] = territory
    if customer_group:
        filters["customer_group"] = customer_group

    customers = frappe.get_list("Customer",
        filters=filters,
        fields=["name", "customer_name", "territory", "customer_group"],
        limit=limit
    )

    return {"customers": customers, "count": len(customers)}
```

---

## Tool 3: get_sales_data

**Purpose**: Retrieve sales orders and invoices for date range

**OpenAI Function Schema**:
```json
{
  "name": "get_sales_data",
  "description": "Get sales metrics including orders and invoices for a date range. Aggregates by company.",
  "parameters": {
    "type": "object",
    "properties": {
      "start_date": {
        "type": "string",
        "format": "date",
        "description": "Start date in YYYY-MM-DD format"
      },
      "end_date": {
        "type": "string",
        "format": "date",
        "description": "End date in YYYY-MM-DD format"
      },
      "company": {
        "type": "string",
        "description": "Company name (optional)"
      },
      "metric": {
        "type": "string",
        "enum": ["orders", "invoices", "both"],
        "default": "both",
        "description": "Which sales documents to include"
      }
    },
    "required": ["start_date", "end_date"]
  }
}
```

**Permission Checks**:
- Read permission on Sales Order and/or Sales Invoice
- Company restrictions applied

---

## Tool 4: execute_erp_report

**Purpose**: Generic report executor for any standard ERPNext report

**OpenAI Function Schema**:
```json
{
  "name": "execute_erp_report",
  "description": "Execute any standard ERPNext report by name with filters. Use this for reports not covered by specialized tools.",
  "parameters": {
    "type": "object",
    "properties": {
      "report_name": {
        "type": "string",
        "description": "Exact name of the ERPNext report"
      },
      "filters": {
        "type": "object",
        "description": "Report filters as key-value pairs"
      }
    },
    "required": ["report_name"]
  }
}
```

**Permission Checks**:
- Report-level permissions enforced
- DocType permissions checked for underlying data

---

## Tool Error Handling

All tools follow this error pattern:
```json
{
  "error": true,
  "error_type": "PermissionError",
  "message": "You don't have permission to access Customer data",
  "suggestion": "Contact your system administrator to request access"
}
```

**Error Types**:
- `PermissionError`: User lacks required permissions
- `ValidationError`: Invalid parameters or filters
- `NotFoundError`: Requested resource doesn't exist
- `RateLimitError`: Too many requests

---

## Tool Usage Guidelines

1. **Permission-First Design**: Every tool validates permissions before data access
2. **Company Isolation**: Automatic filtering by user's allowed companies
3. **Result Limits**: Default limit=20, max=100 to prevent overwhelming AI context
4. **Audit Logging**: All tool calls logged to AI Tool Call Log doctype
5. **Error Recovery**: Tools return structured errors that AI can explain to users

Next: See `api-endpoints.md` for HTTP APIs and `quickstart.md` for development setup.
