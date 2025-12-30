---
id: 001
title: Implement Graphs & Visualizations Feature
stage: implement
date: 2025-12-30
surface: agent
model: claude-sonnet-4-5
feature: 002-ai-chatbot-graphs
branch: 002-ai-chatbot-graphs
user: usman85580
command: /sp.implement
labels: ["implementation", "visualization", "charts", "erpnext", "chatbot", "backend", "frontend"]
links:
  spec: specs/002-ai-chatbot-graphs/spec.md
  plan: specs/002-ai-chatbot-graphs/plan.md
  tasks: specs/002-ai-chatbot-graphs/tasks.md
  adr: null
  pr: null
files:
  - specs/002-ai-chatbot-graphs/plan.md
  - specs/002-ai-chatbot-graphs/tasks.md
  - specs/002-ai-chatbot-graphs/contracts/chart-data.md
  - specs/002-ai-chatbot-graphs/checklists/testing.md
  - erpnext_chatbot/services/chart_data_builder.py
  - erpnext_chatbot/services/agent_orchestrator.py
  - erpnext_chatbot/utils/response_formatter.py
  - erpnext_chatbot/ai_chatbot/page/chatbot/chatbot.html
  - erpnext_chatbot/ai_chatbot/page/chatbot/chatbot.js
tests:
  - N/A (manual testing via ERPNext runtime)
---

## Prompt

/sp.implement

# Implementation Plan
## Graphs & Visualizations in ERPNext AI Chatbot

---

## Technology Stack

### Backend
- Frappe / ERPNext
- OpenAI Agent SDK
- Gemini 2.5 Flash (OpenAI-compatible endpoint)

### Frontend
- ERPNext Page
- JavaScript
- Chart.js (or frappe-charts)

---

## Backend Changes

### 1. Agent Instruction Update

Update the agent system prompt to allow chart responses:
```

## Response snapshot

Successfully implemented the Graphs & Visualizations feature for the ERPNext AI Chatbot:

**Feature Branch**: `002-ai-chatbot-graphs`

**Backend Changes**:
- Created `ChartDataBuilder` service (`erpnext_chatbot/services/chart_data_builder.py`)
  - Supports bar, line, and pie charts
  - Auto-detection of chart type based on query keywords
  - Aggregation helpers for report data
  - Max 50 data points for performance

- Updated `response_formatter.py` with chart utilities
  - `format_report_for_chart()` - Format report data for charts
  - `extract_chart_labels_values()` - Extract label/value pairs
  - `detect_chart_type()` - Infer chart type from query
  - `build_chart_metadata()` - Build complete chart config

- Updated `agent_orchestrator.py`
  - Enhanced `SYSTEM_PROMPT` with chart instructions
  - Added `{CHART_DATA}` marker format for chart JSON
  - Added `_parse_chart_from_response()` helper
  - Modified `process_message()` to include chart in response

**Frontend Changes**:
- Updated `chatbot.html`
  - Added Chart.js CDN (v4.4.1)
  - Added inline CSS for chart containers

- Updated `chatbot.js`
  - Added `charts` object to track Chart.js instances
  - Modified `append_message()` to accept chart data
  - Added `isValidChartData()` validation
  - Added `render_chart()` for Chart.js rendering
  - Added `get_chart_config()` for chart configuration
  - Added `destroy_chart()` for cleanup

**Data Contract**:
```json
{
  "response_type": "text_with_chart",
  "text": "Natural language explanation",
  "chart": {
    "chart_type": "bar|line|pie",
    "title": "Chart Title",
    "labels": ["Label1", "Label2", ...],
    "values": [100, 200, 300, ...],
    "colors": ["#2491eb", ...]
  }
}
```

**Documentation Created**:
- `specs/002-ai-chatbot-graphs/contracts/chart-data.md` - Chart data contract
- `specs/002-ai-chatbot-graphs/checklists/testing.md` - Testing checklist

## Outcome

- ✅ Impact: Implemented complete charts feature with bar, line, and pie chart support
- 🧪 Tests: Manual testing checklist created (requires ERPNext runtime)
- 📁 Files:
  - Created: chart_data_builder.py, chart-data.md, testing.md
  - Modified: agent_orchestrator.py, response_formatter.py, chatbot.html, chatbot.js
- 🔁 Next prompts: Test in ERPNext environment, then run `/sp.git.commit_pr`
- 🧠 Reflection: Implementation follows existing codebase patterns, Chart.js integrated via CDN, chart data passed through agent_orchestrator to frontend

## Evaluation notes (flywheel)

- Failure modes observed: None - implementation follows plan
- Graders run and results (PASS/FAIL): Code review PASS - all files implement required features
- Prompt variant (if applicable): Standard implementation workflow
- Next experiment (smallest change to try): Add support for additional chart types (radar, doughnut) as feature extension
