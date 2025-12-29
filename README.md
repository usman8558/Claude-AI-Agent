# ERPNext Chatbot

AI-powered chatbot for ERPNext that allows users to query financial and business data using natural language while strictly enforcing ERP permissions, auditability, and data integrity.

## Features

- **Natural Language Queries**: Ask questions like "What was our revenue last month?" or "Show me the profit and loss for Q4"
- **Permission Enforcement**: Respects ERPNext role-based permissions at every data access point
- **Session Management**: Isolated chat sessions with context awareness for follow-up questions
- **Audit Trail**: Complete logging of all AI interactions for compliance
- **Financial Reports**: Access Profit & Loss, Balance Sheet, Cash Flow, and other standard reports
- **Rate Limiting**: Per-user rate limits to prevent abuse

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        ERPNext UI                                │
│                    (Chatbot Page)                                │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Frappe API Layer                             │
│                  (@frappe.whitelist)                             │
│  • create_session  • send_message  • get_history                │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Agent Orchestrator                             │
│            (OpenAI SDK + Gemini 2.5 Flash)                       │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                      AI Tools Layer                              │
│  • Finance Tools (P&L, Revenue, Expenses)                        │
│  • Report Tools (Execute any ERPNext report)                     │
│  ╔═══════════════════════════════════════╗                       │
│  ║   Permission Checks at Every Access   ║                       │
│  ╚═══════════════════════════════════════╝                       │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Frappe ORM / Report API                       │
│           (Standard ERPNext Data Access)                         │
└─────────────────────────────────────────────────────────────────┘
```

## Installation

### Prerequisites

- ERPNext v15.x installed and running
- Python 3.10+
- Gemini API key (from Google AI Studio)

### Step 1: Get the App

```bash
cd frappe-bench
bench get-app https://github.com/your-repo/erpnext_chatbot.git
# OR copy the erpnext_chatbot folder to apps/
```

### Step 2: Install the App

```bash
bench --site your-site.local install-app erpnext_chatbot
```

### Step 3: Install Python Dependencies

```bash
cd apps/erpnext_chatbot
pip install -r requirements.txt
```

### Step 4: Configure API Key

Add the following to your `sites/your-site.local/site_config.json`:

```json
{
  "chatbot_api_key": "YOUR_GEMINI_API_KEY",
  "chatbot_api_base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
  "chatbot_ai_model": "gemini-2.0-flash"
}
```

### Step 5: Run Migrations

```bash
bench --site your-site.local migrate
bench --site your-site.local clear-cache
bench build --app erpnext_chatbot
```

### Step 6: Restart

```bash
bench restart
```

## Usage

1. Navigate to **AI Chatbot** in the ERPNext sidebar
2. Click **New Chat** to start a session
3. Ask questions like:
   - "What was our revenue last month?"
   - "Show me the profit and loss for Q4 2024"
   - "Who are our top customers this year?"
   - "What reports are available?"

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/method/erpnext_chatbot.api.chat.create_session` | POST | Create new chat session |
| `/api/method/erpnext_chatbot.api.chat.send_message` | POST | Send message and get AI response |
| `/api/method/erpnext_chatbot.api.chat.get_session_history` | GET | Get session messages |
| `/api/method/erpnext_chatbot.api.chat.get_sessions` | GET | List user's sessions |
| `/api/method/erpnext_chatbot.api.chat.close_session` | POST | Close a session |
| `/api/method/erpnext_chatbot.api.chat.delete_session` | POST | Delete a session |

## Configuration Options

| Setting | Default | Description |
|---------|---------|-------------|
| `chatbot_api_key` | (required) | Gemini API key |
| `chatbot_api_base_url` | Google AI endpoint | OpenAI-compatible API endpoint |
| `chatbot_ai_model` | gemini-2.0-flash | AI model to use |
| `chatbot_rate_limit_per_minute` | 20 | Max requests per minute per user |
| `chatbot_session_timeout_hours` | 24 | Session expiry time |
| `chatbot_retention_days` | 90 | Chat history retention period |

## Security

- **No Direct Database Access**: All data access goes through Frappe APIs
- **Permission Enforcement**: Every tool validates `frappe.has_permission()` before accessing data
- **Company Isolation**: Users only see data from companies they have access to
- **Session Isolation**: Each session is linked to a user and validates ownership
- **Audit Logging**: All AI interactions are logged with full details
- **Rate Limiting**: Per-user rate limits prevent abuse
- **Input Sanitization**: All user inputs are sanitized before processing

## DocTypes

| DocType | Description |
|---------|-------------|
| Chat Session | Conversation threads with metadata |
| Chat Message | Individual messages in sessions |
| Chat Audit Log | Compliance audit trail |
| AI Tool Call Log | Detailed tool invocation logs |

## Troubleshooting

### "Chatbot API key not configured"
Add `chatbot_api_key` to your site_config.json

### "Permission denied" errors
Ensure the user has appropriate roles (Accounts User, Sales User, etc.)

### "Rate limit exceeded"
Wait for the rate limit window to reset (default: 1 minute)

### Session expired
Sessions expire after 24 hours of inactivity. Start a new chat.

## License

MIT License

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## Support

For issues and feature requests, please open a GitHub issue.
