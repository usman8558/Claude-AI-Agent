# Testing Checklist: Graphs & Visualizations

**Feature**: AI Chatbot Response with Graphs & Visualizations
**Date**: 2025-12-30

## Test Scenarios

### Bar Chart Tests

- [ ] Query: "Show top 5 customers by revenue"
  - Expected: Bar chart with 5 data points
  - Labels: Customer names
  - Values: Revenue amounts

- [ ] Query: "Compare monthly expenses by department"
  - Expected: Grouped bar chart
  - Labels: Departments
  - Values: Expense amounts

### Line Chart Tests

- [ ] Query: "Show monthly sales trend for 2024"
  - Expected: Line chart with 12 data points
  - Labels: Month names (Jan-Dec)
  - Values: Monthly sales figures

- [ ] Query: "Revenue growth over the last 6 months"
  - Expected: Line chart with trend line
  - Labels: Last 6 months
  - Values: Revenue amounts

### Pie Chart Tests

- [ ] Query: "Show expense distribution by category"
  - Expected: Pie chart
  - Labels: Category names
  - Values: Percentages

- [ ] Query: "Market share by product category"
  - Expected: Pie or donut chart
  - Labels: Category names
  - Values: Percentage share

## Validation Checklist

### Data Validation

- [ ] Labels array contains strings
- [ ] Values array contains numbers
- [ ] Labels and values arrays have same length
- [ ] Minimum 2 data points for chart
- [ ] Maximum 50 data points enforced

### UI Validation

- [ ] Chart container renders correctly
- [ ] Chart title displays properly
- [ ] Chart type matches data characteristics
- [ ] Colors are visible and distinct
- [ ] Tooltips work on hover
- [ ] Responsive sizing on mobile

### Performance Validation

- [ ] Chart renders within 500ms
- [ ] No memory leaks on multiple chart renders
- [ ] Charts clean up properly on page refresh

### Error Handling

- [ ] Invalid chart data shows error message
- [ ] Chart.js loading errors handled gracefully
- [ ] Empty data shows fallback message

## Manual Testing Steps

1. **Setup**
   - [ ] Clear browser cache
   - [ ] Open ERPNext AI Chatbot page
   - [ ] Verify Chart.js loaded (check console)

2. **Bar Chart Test**
   - [ ] Type: "Show top 5 products by sales"
   - [ ] Verify bar chart appears below response
   - [ ] Verify labels are readable
   - [ ] Verify values formatted correctly

3. **Line Chart Test**
   - [ ] Type: "Show sales trend over last 6 months"
   - [ ] Verify line chart appears below response
   - [ ] Verify smooth line rendering
   - [ ] Verify axis labels present

4. **Pie Chart Test**
   - [ ] Type: "Show expense breakdown"
   - [ ] Verify pie chart appears below response
   - [ ] Verify legend displays correctly
   - [ ] Verify percentages in tooltips

5. **Error Case**
   - [ ] Type a query that returns insufficient data
   - [ ] Verify no chart rendered (graceful fallback)
   - [ ] Verify text response still displays

## Expected Data Format

```json
{
  "response_type": "text_with_chart",
  "text": "Here are your top 5 customers...",
  "chart": {
    "chart_type": "bar",
    "title": "Top 5 Customers by Revenue",
    "labels": ["Customer A", "Customer B", "Customer C", "Customer D", "Customer E"],
    "values": [125000, 98000, 76500, 54300, 42100],
    "colors": ["#2491eb", "#5e64ff", "#00c3b3", "#28c76f", "#ff6b6b"]
  }
}
```

## Browser Compatibility

- [ ] Chrome 90+
- [ ] Firefox 88+
- [ ] Safari 14+
- [ ] Edge 90+

## Notes

- Charts require Chart.js library (loaded via CDN)
- Maximum 50 data points per chart for performance
- Currency values formatted with K/M suffixes
- Pie charts auto-calculate percentages
