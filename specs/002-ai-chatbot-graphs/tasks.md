# Implementation Tasks: Graphs & Visualizations

**Feature Branch**: `002-ai-chatbot-graphs`
**Last Updated**: 2025-12-30

## Task Phases

1. **Setup**: Project initialization and configuration
2. **Backend Core**: Chart data generation and agent updates
3. **Frontend**: Chart rendering implementation
4. **Integration**: End-to-end testing and polish

---

## Phase 1: Setup

### Task 1.1: Create feature directory structure

**Description**: Create the feature directory structure for the graphs feature.

**Steps**:
1. Create `specs/002-ai-chatbot-graphs/contracts/` directory
2. Create `specs/002-ai-chatbot-graphs/checklists/` directory

**Files Modified**:
- (Directory creation only)

**Acceptance Criteria**:
- [x] `specs/002-ai-chatbot-graphs/contracts/` exists
- [x] `specs/002-ai-chatbot-graphs/checklists/` exists

---

### Task 1.2: Create chart data contract

**Description**: Create the contract document defining the chart data format.

**Steps**:
1. Create `specs/002-ai-chatbot-graphs/contracts/chart-data.md`
2. Document the JSON structure for chart data
3. Document supported chart types and their requirements

**Files Created**:
- `specs/002-ai-chatbot-graphs/contracts/chart-data.md`

**Acceptance Criteria**:
- [x] Chart data contract created
- [x] All 3 chart types documented (bar, line, pie)
- [x] JSON structure validated

---

### Task 1.3: Verify ignore files

**Description**: Verify that the project has appropriate ignore files.

**Steps**:
1. Check for `.gitignore` existence and content
2. Add any missing patterns if needed

**Files to Check**:
- `.gitignore`

**Acceptance Criteria**:
- [x] `.gitignore` exists and is valid

---

## Phase 2: Backend Core

### Task 2.1: Create ChartDataBuilder service

**Description**: Create the ChartDataBuilder service to generate chart-compatible data from reports.

**Steps**:
1. Create `erpnext_chatbot/services/chart_data_builder.py`
2. Implement `build_chart_data()` function
3. Implement aggregation helpers for bar, line, pie charts
4. Add type detection based on data characteristics

**Files Created**:
- `erpnext_chatbot/services/chart_data_builder.py`

**Acceptance Criteria**:
- [x] `ChartDataBuilder` class created
- [x] `build_chart_data()` function supports bar, line, pie
- [x] Label/value extraction works correctly
- [x] Max 50 data points enforced

---

### Task 2.2: Update response_formatter.py

**Description**: Add chart formatting utilities to response_formatter.py.

**Steps**:
1. Add `format_report_for_chart()` function
2. Add `extract_chart_labels_values()` function
3. Add chart type inference helper

**Files Modified**:
- `erpnext_chatbot/utils/response_formatter.py`

**Acceptance Criteria**:
- [x] `format_report_for_chart()` implemented
- [x] `extract_chart_labels_values()` implemented
- [x] Tests pass with sample report data

---

### Task 2.3: Update agent SYSTEM_PROMPT

**Description**: Update the agent system prompt to enable chart responses.

**Steps**:
1. Modify `SYSTEM_PROMPT` in `agent_orchestrator.py`
2. Add chart type detection instructions
3. Add structured output format for chart data
4. Add examples for each chart type

**Files Modified**:
- `erpnext_chatbot/services/agent_orchestrator.py`

**Acceptance Criteria**:
- [x] SYSTEM_PROMPT updated with chart instructions
- [x] Bar chart examples added
- [x] Line chart examples added
- [x] Pie chart examples added

---

### Task 2.4: Modify process_message for chart response

**Description**: Update process_message() to handle chart data in responses.

**Steps**:
1. Detect chart JSON in assistant response
2. Parse chart data if present
3. Include chart in return dictionary
4. Handle errors gracefully

**Files Modified**:
- `erpnext_chatbot/services/agent_orchestrator.py`

**Acceptance Criteria**:
- [x] Chart data detected in responses
- [x] Chart included in return object
- [x] Backward compatible with non-chart responses

---

## Phase 3: Frontend

### Task 3.1: Add Chart.js to chatbot page

**Description**: Include Chart.js library in the chatbot page.

**Steps**:
1. Add Chart.js CDN to `chatbot.html`
2. Verify Chart.js loads correctly

**Files Modified**:
- `erpnext_chatbot/ai_chatbot/page/chatbot/chatbot.html`

**Acceptance Criteria**:
- [x] Chart.js CDN included
- [x] Library loads without errors

---

### Task 3.2: Update chatbot.css for charts

**Description**: Add CSS styles for chart containers.

**Steps**:
1. Create chart container styles
2. Add responsive sizing
3. Add loading animation styles

**Files Modified**:
- `erpnext_chatbot/ai_chatbot/page/chatbot/chatbot.html` (inline styles)

**Acceptance Criteria**:
- [x] Chart container styles added
- [x] Responsive chart sizing works
- [x] Chart loading state styled

---

### Task 3.3: Update append_message for chart rendering

**Description**: Modify append_message() to detect and render charts.

**Steps**:
1. Add chart metadata detection to response handling
2. Create chart container in message
3. Initialize Chart.js instance
4. Handle chart update on new messages

**Files Modified**:
- `erpnext_chatbot/ai_chatbot/page/chatbot/chatbot.js`

**Acceptance Criteria**:
- [x] Chart metadata detected in responses
- [x] Chart rendered in chat message
- [x] Multiple charts supported
- [x] Chart destroys on page refresh

---

### Task 3.4: Add chart rendering helper methods

**Description**: Add helper methods for chart rendering.

**Steps**:
1. Add `render_chart()` method
2. Add `get_chart_config()` method
3. Add `destroy_chart()` method

**Files Modified**:
- `erpnext_chatbot/ai_chatbot/page/chatbot/chatbot.js`

**Acceptance Criteria**:
- [x] `render_chart()` implemented
- [x] `get_chart_config()` handles bar, line, pie
- [x] `destroy_chart()` cleans up instances

---

## Phase 4: Integration & Testing

### Task 4.1: Update API chat.py if needed

**Description**: Verify API layer passes chart data correctly.

**Steps**:
1. Check `api/chat.py` for response handling
2. Ensure chart data flows through to frontend

**Files Modified** (if needed):
- `erpnext_chatbot/api/chat.py`

**Acceptance Criteria**:
- [x] Chart data passes through API (no changes needed - agent_orchestrator returns chart)
- [x] No data loss for chart metadata

---

### Task 4.2: Create implementation test scenarios

**Description**: Create test scenarios for chart functionality.

**Steps**:
1. Create test queries for each chart type
2. Document expected chart data structure
3. Create visual test checklist

**Files Created**:
- `specs/002-ai-chatbot-graphs/checklists/testing.md`

**Acceptance Criteria**:
- [x] Bar chart test scenario documented
- [x] Line chart test scenario documented
- [x] Pie chart test scenario documented

---

### Task 4.3: Verify integration

**Description**: Verify end-to-end chart rendering.

**Steps**:
1. Test bar chart with "Top 5 customers"
2. Test line chart with "Monthly sales trend"
3. Test pie chart with "Expense distribution"
4. Document results

**Acceptance Criteria**:
- [ ] All 3 chart types render correctly (requires ERPNext runtime testing)
- [ ] No console errors
- [ ] Responsive behavior verified

---

## Task Dependencies

```
Phase 1 (Setup)
├── 1.1 Create feature directory structure
├── 1.2 Create chart data contract
└── 1.3 Verify ignore files
         │
         ▼
Phase 2 (Backend Core) [P] - 2.1, 2.2 can run in parallel
├── 2.1 Create ChartDataBuilder service
├── 2.2 Update response_formatter.py
├── 2.3 Update agent SYSTEM_PROMPT ───────┐
└── 2.4 Modify process_message ───────────┤
                                          │ Requires 2.3
         │                                │
         ▼                                ▼
Phase 3 (Frontend) [P] - 3.1, 3.2 can run in parallel
├── 3.1 Add Chart.js to chatbot page      │
├── 3.2 Update chatbot.css for charts     │
├── 3.3 Update append_message ────────────┤
└── 3.4 Add chart helpers ────────────────┤
                                          │
         │                                │
         ▼                                ▼
Phase 4 (Integration)
├── 4.1 Update API if needed
├── 4.2 Create test scenarios
└── 4.3 Verify integration
```

---

## Quick Reference

| Task | Status | Blocked By |
|------|--------|------------|
| 1.1 | - | - |
| 1.2 | - | - |
| 1.3 | - | - |
| 2.1 | - | 1.1 |
| 2.2 | - | 1.1 |
| 2.3 | - | 1.1 |
| 2.4 | - | 2.3 |
| 3.1 | - | 2.4 |
| 3.2 | - | 2.4 |
| 3.3 | - | 3.1, 3.2 |
| 3.4 | - | 3.3 |
| 4.1 | - | 3.3 |
| 4.2 | - | 3.3 |
| 4.3 | - | 4.1, 4.2 |
