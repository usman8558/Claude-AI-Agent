# Quickstart: ERPNext Claude Chatbot Development

**Date**: 2025-12-29
**Feature**: 001-erpnext-claude-chatbot

## Prerequisites

- ERPNext 15.x installed via bench
- Python 3.10+
- Node.js 18+ (for Frappe asset building)
- Redis (for Frappe cache/rate limiting)
- Gemini API key (Google AI Studio or Vertex AI)

---

## Step 1: Set Up Development Environment

### Install ERPNext (if not already installed)

```bash
# Install bench
pip3 install frappe-bench

# Initialize bench with Frappe + ERPNext
bench init frappe-bench --frappe-branch version-15
cd frappe-bench
bench get-app erpnext --branch version-15
bench new-site mysite.local --install-app erpnext

# Set site as default
bench use mysite.local
```

---

## Step 2: Create Custom App

```bash
# Create new Frappe app
bench new-app erpnext_chatbot

# Follow prompts:
# - App Title: ERPNext Chatbot
# - App Description: AI-powered chatbot for ERPNext data queries
# - App Publisher: Your Name
# - App Email: your@email.com
# - App License: MIT

# Install app on site
bench --site mysite.local install-app erpnext_chatbot
```

---

## Step 3: Install Python Dependencies

Add to `erpnext_chatbot/requirements.txt`:
```
openai>=1.0.0
litellm>=1.0.0
tiktoken>=0.5.0
```

Install:
```bash
cd apps/erpnext_chatbot
pip3 install -r requirements.txt
```

---

## Step 4: Configure Gemini API Access

### Option A: LiteLLM Proxy (Development)

```bash
# Install LiteLLM
pip3 install 'litellm[proxy]'

# Start proxy
export GEMINI_API_KEY="your-gemini-api-key"
litellm --model gemini/gemini-2.5-flash --port 4000
```

Proxy runs at `http://localhost:4000` (OpenAI-compatible)

### Option B: Direct Configuration (Production)

Add to `sites/mysite.local/site_config.json`:
```json
{
  "chatbot_ai_provider": "gemini",
  "chatbot_ai_model": "gemini-2.5-flash",
  "chatbot_api_key": "your-gemini-api-key-here",
  "chatbot_api_base_url": "http://localhost:4000"
}
```

---

## Step 5: Create DocTypes

### Via Frappe Desk (GUI)

1. Navigate to `http://mysite.local:8000`
2. Login as Administrator
3. Go to **DocType List** → **New DocType**
4. Create each DocType following schemas in `data-model.md`:
   - Chat Session
   - Chat Message
   - Chat Audit Log
   - AI Tool Call Log

### Via Code (Automated)

Create JSON files in `erpnext_chatbot/ai_chatbot/doctype/<doctype_name>/<doctype_name>.json` (see `data-model.md` for schemas)

Run:
```bash
bench --site mysite.local migrate
```

---

## Step 6: Implement Core Services

### 6.1 Agent Orchestrator

Create `erpnext_chatbot/services/agent_orchestrator.py`:
```python
import openai
import frappe

def get_ai_client():
    """Initialize OpenAI client with Gemini endpoint"""
    return openai.OpenAI(
        api_key=frappe.conf.get("chatbot_api_key"),
        base_url=frappe.conf.get("chatbot_api_base_url", "http://localhost:4000")
    )

def process_message(session_id, user_message):
    """Process user message and return AI response"""
    client = get_ai_client()

    # Load session context (last 20 messages)
    messages = get_session_messages(session_id, limit=20)

    # Add user message
    messages.append({"role": "user", "content": user_message})

    # Call AI with tools
    response = client.chat.completions.create(
        model=frappe.conf.get("chatbot_ai_model", "gemini-2.5-flash"),
        messages=messages,
        tools=get_tool_definitions(),
        tool_choice="auto"
    )

    # Handle tool calls if present
    if response.choices[0].message.tool_calls:
        tool_results = execute_tools(response.choices[0].message.tool_calls, session_id)
        # ... (tool execution logic)

    return response.choices[0].message.content
```

### 6.2 Implement API Endpoints

Create `erpnext_chatbot/api/chat.py`:
```python
import frappe

@frappe.whitelist()
def create_session():
    """Create new chat session"""
    session = frappe.get_doc({
        "doctype": "Chat Session",
        "session_id": frappe.generate_hash(length=32),
        "user": frappe.session.user,
        "status": "Active"
    }).insert()

    return {"session_id": session.session_id}

@frappe.whitelist()
def send_message(session_id, message):
    """Send message and get AI response"""
    # Validate session ownership
    validate_session_ownership(session_id)

    # Rate limit check
    check_rate_limit(frappe.session.user)

    # Process message
    response = agent_orchestrator.process_message(session_id, message)

    return {"response": response}
```

---

## Step 7: Create UI Page

Create `erpnext_chatbot/ai_chatbot/page/chatbot/chatbot.js`:
```javascript
frappe.pages['chatbot'].on_page_load = function(wrapper) {
    let page = frappe.ui.make_app_page({
        parent: wrapper,
        title: 'AI Chatbot',
        single_column: true
    });

    let session_id = null;

    // Create session on load
    frappe.call({
        method: 'erpnext_chatbot.api.chat.create_session',
        callback: function(r) {
            session_id = r.message.session_id;
        }
    });

    // Send message handler
    function send_message(text) {
        frappe.call({
            method: 'erpnext_chatbot.api.chat.send_message',
            args: {session_id: session_id, message: text},
            callback: function(r) {
                append_message('assistant', r.message.response);
            }
        });
    }
};
```

---

## Step 8: Implement Agent Tools

Create `erpnext_chatbot/tools/finance_tools.py`:
```python
import frappe
from frappe.desk.query_report import run

def get_financial_report(report_name, company, from_date, to_date, periodicity="Monthly"):
    """Execute financial report with permission checks"""
    # Permission validation
    if not frappe.has_permission("GL Entry", ptype="read"):
        raise frappe.PermissionError("No access to financial data")

    # Execute report
    result = run(report_name, filters={
        "company": company or frappe.defaults.get_user_default("Company"),
        "from_date": from_date,
        "to_date": to_date,
        "periodicity": periodicity
    })

    return format_report_for_ai(result)
```

Register tools in `erpnext_chatbot/tools/__init__.py`:
```python
def get_tool_definitions():
    """Return OpenAI function calling schemas for all tools"""
    return [
        {
            "type": "function",
            "function": {
                "name": "get_financial_report",
                "description": "Retrieve financial reports like P&L, Balance Sheet",
                "parameters": {
                    # ... (schema from agent-tools.md)
                }
            }
        },
        # ... (other tools)
    ]
```

---

## Step 9: Run Tests

```bash
# Run all tests
bench --site mysite.local run-tests --app erpnext_chatbot

# Run specific test file
bench --site mysite.local run-tests --app erpnext_chatbot --module test_chat_session

# Run with coverage
bench --site mysite.local run-tests --app erpnext_chatbot --coverage
```

---

## Step 10: Start Development Server

```bash
# Start bench
bench start

# Access ERPNext at http://mysite.local:8000
# Navigate to AI Chatbot page
```

---

## Configuration Reference

### Site Config (`sites/mysite.local/site_config.json`)

```json
{
  "chatbot_ai_provider": "gemini",
  "chatbot_ai_model": "gemini-2.5-flash",
  "chatbot_api_key": "YOUR_GEMINI_API_KEY",
  "chatbot_api_base_url": "http://localhost:4000",
  "chatbot_rate_limit_per_minute": 20,
  "chatbot_session_timeout_hours": 24,
  "chatbot_retention_days": 90,
  "chatbot_audit_retention_days": 365
}
```

---

## Troubleshooting

### Issue: "Permission Denied" errors
**Solution**: Ensure user has required roles (Accounts User, Sales User) in User DocType

### Issue: AI not responding
**Solution**: Check LiteLLM proxy is running (`curl http://localhost:4000/health`)

### Issue: Rate limit errors
**Solution**: Increase `chatbot_rate_limit_per_minute` in site config

### Issue: Session not found
**Solution**: Check session hasn't expired (24-hour default timeout)

---

## Next Steps

1. Review implementation plan in `plan.md`
2. Generate tasks with `/sp.tasks`
3. Begin Phase 1: Foundation (app setup, DocTypes)
4. Follow TDD approach: Write tests before implementation

---

## Resources

- [Frappe Framework Docs](https://frappeframework.com/docs)
- [ERPNext Developer Guide](https://docs.erpnext.com/docs/v15/developer)
- [OpenAI Function Calling](https://platform.openai.com/docs/guides/function-calling)
- [Gemini API Docs](https://ai.google.dev/docs)
- [LiteLLM Docs](https://docs.litellm.ai/)
