# Implementation Plan: Graphs & Visualizations

**Feature Branch**: `002-ai-chatbot-graphs`
**Created**: 2025-12-30
**Status**: Draft

## Architecture Overview

### Technology Stack

#### Backend
- **Framework**: Frappe/ERPNext (Python)
- **AI SDK**: OpenAI Agent SDK
- **Model**: Gemini 2.5 Flash (OpenAI-compatible endpoint)
- **Data Access**: Frappe ORM, Standard Reports

#### Frontend
- **Framework**: ERPNext Page (Vanilla JS)
- **Charting Library**: Chart.js (included via CDN)
- **UI Components**: Bootstrap (via ERPNext)

---

## File Structure

```
specs/002-ai-chatbot-graphs/
├── plan.md
├── tasks.md
└── contracts/
    └── chart-data.md

erpnext_chatbot/
├── services/
│   ├── agent_orchestrator.py    # Modified: Update SYSTEM_PROMPT
│   └── chart_data_builder.py    # NEW: Build chart data from reports
├── utils/
│   └── response_formatter.py    # Modified: Add chart formatting
└── ai_chatbot/page/chatbot/
    ├── chatbot.js               # Modified: Chart rendering
    └── chatbot.css              # Modified: Chart container styles
```

---

## Key Changes

### 1. Backend Changes

#### Agent Instruction Update (agent_orchestrator.py)
- Update `SYSTEM_PROMPT` to enable chart responses
- Add chart type detection instructions
- Add structured output format for chart data

#### Chart Data Builder (NEW: chart_data_builder.py)
- Create service to generate chart-compatible data from reports
- Support aggregation for: bar, line, pie charts
- Handle label/value extraction and formatting

#### Response Formatter Update (response_formatter.py)
- Add `format_for_chart()` function
- Extract labels and values from report data
- Limit data points for performance

### 2. Frontend Changes

#### Chatbot JavaScript (chatbot.js)
- Detect chart metadata in responses
- Render Chart.js canvas when chart present
- Handle click events on chart elements

#### Chatbot CSS (chatbot.css)
- Add chart container styles
- Responsive chart sizing
- Animation for chart rendering

---

## Data Flow

```
User Query → Agent → Tool Execution → Report Data
                    ↓
              Chart Data Builder
                    ↓
            Structured Chart JSON
                    ↓
           Agent → Text + Chart Data
                    ↓
              Response API
                    ↓
          Frontend: Render + Display
```

---

## API Contract

### Response Format (Updated)

```python
{
    "success": True,
    "response": "Sales increased steadily...",
    "chart": {
        "chart_type": "line",
        "title": "Monthly Sales Trend",
        "labels": ["Jan", "Feb", "Mar", ...],
        "values": [120000, 135000, 150000, ...]
    },
    "processing_time_ms": 1250,
    "tools_called": 2,
    "token_count": 450
}
```

---

## Chart Type Detection Logic

| User Query Pattern | Chart Type | Example |
|-------------------|------------|---------|
| "trend", "over time", "growth" | line | "Show revenue trend over last 6 months" |
| "top N", "ranking", "comparison" | bar | "Top 5 customers by revenue" |
| "distribution", "breakdown", "share" | pie | "Expense distribution by category" |

---

## Dependencies

### External
- **Chart.js**: CDN (https://cdn.jsdelivr.net/npm/chart.js)
- No additional Python dependencies

### Internal (Existing)
- `erpnext_chatbot.services.agent_orchestrator`
- `erpnext_chatbot.utils.response_formatter`
- `erpnext_chatbot.tools.report_tools`

---

## Security Considerations

- All chart data respects ERPNext permissions (inherited from report tools)
- No raw SQL - data only from validated report results
- Chart data payloads size-limited (max 100 data points)
- Input sanitization on all user queries (existing)

---

## Performance Budget

- Chart data generation: < 100ms additional processing
- Frontend render: < 500ms
- Total response overhead: < 600ms beyond baseline
- Max chart data points: 50 labels, 50 values

---

## Extensibility

### Adding New Chart Types

1. **Backend**: Add chart type handler in `chart_data_builder.py`
2. **Frontend**: Add canvas renderer in `chatbot.js`
3. **Agent Prompt**: Document in `SYSTEM_PROMPT`

Example for Radar chart:
```python
def build_radar_chart(data, title):
    return {
        "chart_type": "radar",
        "title": title,
        "labels": [d["label"] for d in data],
        "values": [d["value"] for d in data]
    }
```
