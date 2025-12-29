"""
ERPNext Chatbot Tools

AI agent tools for accessing ERPNext data with permission enforcement.
"""

from erpnext_chatbot.tools.base_tool import BaseTool
from erpnext_chatbot.tools.finance_tools import (
    get_financial_report,
    get_profit_and_loss,
    get_balance_sheet,
)
from erpnext_chatbot.tools.report_tools import execute_report


def get_all_tools():
    """Get all available tool definitions for the agent."""
    from erpnext_chatbot.tools.finance_tools import FINANCE_TOOLS
    from erpnext_chatbot.tools.report_tools import REPORT_TOOLS

    return FINANCE_TOOLS + REPORT_TOOLS
