"""
Agent Orchestrator Service

Orchestrates AI agent interactions using OpenAI SDK with Gemini backend.
Handles tool registration, message processing, and response generation.
"""

import json
import time
import frappe
from frappe import _
from frappe.utils import now_datetime
from typing import Optional, Dict, Any, List

from openai import OpenAI

from erpnext_chatbot.erpnext_chatbot.services.audit_logger import log_query, log_tool_call
from erpnext_chatbot.erpnext_chatbot.tools.finance_tools import FINANCE_TOOLS, TOOL_FUNCTIONS as FINANCE_TOOL_FUNCTIONS
from erpnext_chatbot.erpnext_chatbot.tools.report_tools import REPORT_TOOLS, TOOL_FUNCTIONS as REPORT_TOOL_FUNCTIONS


# Combine all tool functions
ALL_TOOL_FUNCTIONS = {**FINANCE_TOOL_FUNCTIONS, **REPORT_TOOL_FUNCTIONS}

# System prompt for the AI agent
SYSTEM_PROMPT = """You are an AI assistant for ERPNext, a business management system. Your role is to help users query financial and business data using natural language.

IMPORTANT RULES:
1. You can ONLY access data through the provided tools - never claim to have data you don't actually retrieve
2. Always use the appropriate tool to fetch data before answering questions
3. If a user asks about data you don't have a tool for, explain what tools are available
4. Respect user permissions - if a tool returns a permission error, explain this politely
5. Format numbers and currencies clearly
6. If data is missing or the query returns no results, say so clearly
7. You cannot create, update, or delete any ERPNext documents - you have read-only access
8. Always specify the date range or time period when discussing financial data

Available capabilities:
- Financial reports: Profit & Loss, Balance Sheet, Cash Flow
- Revenue and expense summaries
- Execute standard ERPNext reports
- List available reports

When users ask questions like "What's our revenue?", always ask for clarification on the time period if not specified."""


def get_ai_client() -> OpenAI:
    """
    Initialize OpenAI client with Gemini-compatible endpoint.

    Returns:
        Configured OpenAI client
    """
    api_key = frappe.conf.get("chatbot_api_key")
    base_url = frappe.conf.get("chatbot_api_base_url", "https://generativelanguage.googleapis.com/v1beta/openai/")

    if not api_key:
        frappe.throw(
            _("Chatbot API key not configured. Please set 'chatbot_api_key' in site_config.json"),
            frappe.ValidationError
        )

    return OpenAI(
        api_key=api_key,
        base_url=base_url
    )


def get_tool_definitions() -> List[Dict[str, Any]]:
    """
    Get all tool definitions for the AI agent.

    Returns:
        List of OpenAI function calling schemas
    """
    return FINANCE_TOOLS + REPORT_TOOLS


def process_message(
    session_id: str,
    user_message: str,
    user: Optional[str] = None
) -> Dict[str, Any]:
    """
    Process a user message and return AI response.

    Args:
        session_id: Chat session ID
        user_message: User's question
        user: User making the request (defaults to current user)

    Returns:
        Dictionary with response details
    """
    from erpnext_chatbot.erpnext_chatbot.ai_chatbot.doctype.chat_message.chat_message import ChatMessage

    user = user or frappe.session.user
    start_time = time.time()

    # Initialize tracking variables
    tools_called = 0
    data_accessed = []
    permission_checks_passed = True
    error_occurred = False
    error_message = None

    # Create audit log entry first (will be updated later)
    audit_log_id = log_query(
        session_id=session_id,
        query_text=user_message,
        permission_checks_passed=True,
        error_occurred=False,
        tools_called=0
    )

    try:
        # Load conversation context (last 20 messages)
        context_messages = ChatMessage.get_context_messages(session_id, limit=20)

        # Build messages array
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]
        messages.extend(context_messages)
        messages.append({"role": "user", "content": user_message})

        # Get AI client
        client = get_ai_client()
        model = frappe.conf.get("chatbot_ai_model", "gemini-2.0-flash")

        # Call AI with tools
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=get_tool_definitions(),
            tool_choice="auto",
            max_tokens=4096
        )

        assistant_message = response.choices[0].message

        # Handle tool calls if present
        if assistant_message.tool_calls:
            # Process each tool call
            tool_results = []

            for tool_call in assistant_message.tool_calls:
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)
                tools_called += 1

                # Execute tool
                tool_result = execute_tool(
                    tool_name=tool_name,
                    arguments=tool_args,
                    session_id=session_id,
                    audit_log_id=audit_log_id,
                    user=user
                )

                tool_results.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "content": tool_result["result"]
                })

                # Track data accessed
                data_accessed.append({
                    "tool": tool_name,
                    "arguments": tool_args
                })

                # Check for permission errors
                if tool_result.get("status") == "permission_denied":
                    permission_checks_passed = False

            # Add tool results to conversation
            messages.append(assistant_message)
            messages.extend(tool_results)

            # Get final response with tool results
            final_response = client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=4096
            )

            response_text = final_response.choices[0].message.content
            total_tokens = (
                (response.usage.total_tokens if response.usage else 0) +
                (final_response.usage.total_tokens if final_response.usage else 0)
            )
        else:
            # No tool calls, use direct response
            response_text = assistant_message.content
            total_tokens = response.usage.total_tokens if response.usage else 0

        # Calculate processing time
        processing_time_ms = int((time.time() - start_time) * 1000)

        # Store messages
        ChatMessage.create_message(
            session_id=session_id,
            role="user",
            content=user_message
        )

        ChatMessage.create_message(
            session_id=session_id,
            role="assistant",
            content=response_text,
            token_count=total_tokens,
            model_used=model,
            processing_time_ms=processing_time_ms
        )

        # Update audit log with final details
        _update_audit_log(
            audit_log_id=audit_log_id,
            response_summary=response_text[:500] if response_text else None,
            data_accessed=data_accessed,
            permission_checks_passed=permission_checks_passed,
            tools_called=tools_called,
            total_processing_time_ms=processing_time_ms
        )

        return {
            "success": True,
            "response": response_text,
            "processing_time_ms": processing_time_ms,
            "tools_called": tools_called,
            "token_count": total_tokens
        }

    except Exception as e:
        error_occurred = True
        error_message = str(e)
        processing_time_ms = int((time.time() - start_time) * 1000)

        # Log error
        frappe.log_error(f"Agent processing error: {error_message}", "Chatbot Error")

        # Update audit log with error
        _update_audit_log(
            audit_log_id=audit_log_id,
            error_occurred=True,
            error_message=error_message,
            total_processing_time_ms=processing_time_ms
        )

        # Return user-friendly error
        return {
            "success": False,
            "response": _get_user_friendly_error(e),
            "processing_time_ms": processing_time_ms,
            "tools_called": tools_called,
            "error": error_message
        }


def execute_tool(
    tool_name: str,
    arguments: Dict[str, Any],
    session_id: str,
    audit_log_id: str,
    user: str
) -> Dict[str, Any]:
    """
    Execute an AI tool with the given arguments.

    Args:
        tool_name: Name of the tool to execute
        arguments: Tool arguments
        session_id: Chat session ID
        audit_log_id: Parent audit log ID
        user: User making the request

    Returns:
        Dictionary with result and status
    """
    from erpnext_chatbot.erpnext_chatbot.tools.base_tool import PermissionDeniedError

    if tool_name not in ALL_TOOL_FUNCTIONS:
        return {
            "result": f"Error: Unknown tool '{tool_name}'",
            "status": "error"
        }

    tool_func = ALL_TOOL_FUNCTIONS[tool_name]

    try:
        # Add context to arguments
        arguments["session_id"] = session_id
        arguments["audit_log_id"] = audit_log_id
        arguments["user"] = user

        result = tool_func(**arguments)

        return {
            "result": result,
            "status": "success"
        }

    except PermissionDeniedError as e:
        return {
            "result": f"Permission denied: {str(e)}",
            "status": "permission_denied"
        }

    except Exception as e:
        frappe.log_error(f"Tool execution error for {tool_name}: {str(e)}", "Tool Execution Error")
        return {
            "result": f"Error executing {tool_name}: {str(e)}",
            "status": "error"
        }


def _update_audit_log(
    audit_log_id: str,
    response_summary: Optional[str] = None,
    data_accessed: Optional[List] = None,
    permission_checks_passed: bool = True,
    error_occurred: bool = False,
    error_message: Optional[str] = None,
    tools_called: int = 0,
    total_processing_time_ms: Optional[int] = None
):
    """Update audit log with final details."""
    try:
        if not audit_log_id:
            return

        updates = {}
        if response_summary is not None:
            updates["response_summary"] = response_summary
        if data_accessed is not None:
            updates["data_accessed"] = json.dumps(data_accessed)
        updates["permission_checks_passed"] = permission_checks_passed
        updates["error_occurred"] = error_occurred
        if error_message:
            updates["error_message"] = error_message
        updates["tools_called"] = tools_called
        if total_processing_time_ms is not None:
            updates["total_processing_time_ms"] = total_processing_time_ms

        frappe.db.set_value("Chat Audit Log", audit_log_id, updates, update_modified=False)
        frappe.db.commit()

    except Exception as e:
        frappe.log_error(f"Failed to update audit log: {str(e)}", "Audit Log Update Error")


def _get_user_friendly_error(error: Exception) -> str:
    """Convert exception to user-friendly error message."""
    error_str = str(error).lower()

    if "api key" in error_str:
        return "The AI service is not properly configured. Please contact your administrator."
    elif "rate limit" in error_str:
        return "The AI service is currently busy. Please try again in a few moments."
    elif "connection" in error_str or "timeout" in error_str:
        return "Unable to connect to the AI service. Please check your internet connection and try again."
    elif "permission" in error_str:
        return "You don't have permission to access the requested data."
    else:
        return "An error occurred while processing your request. Please try again or rephrase your question."
