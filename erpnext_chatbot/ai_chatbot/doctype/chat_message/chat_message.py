"""
Chat Message DocType Controller

Manages individual messages within chat sessions with session validation
and token counting.
"""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime


class ChatMessage(Document):
    """
    Chat Message represents a single message in a conversation.
    Messages have a role (user/assistant/system) and are linked to a session.
    """

    def before_insert(self):
        """Set timestamp and validate session before inserting."""
        if not self.timestamp:
            self.timestamp = now_datetime()

    def validate(self):
        """Validate message data before saving."""
        self._validate_session()
        self._validate_content_length()

    def _validate_session(self):
        """Ensure session exists and is active."""
        if not frappe.db.exists("Chat Session", self.session_id):
            frappe.throw(
                _("Chat session not found: {0}").format(self.session_id),
                frappe.DoesNotExistError
            )

        session_status = frappe.db.get_value("Chat Session", self.session_id, "status")
        if session_status != "Active":
            frappe.throw(
                _("Cannot add messages to a {0} session").format(session_status.lower()),
                frappe.ValidationError
            )

    def _validate_content_length(self):
        """Ensure content doesn't exceed maximum length."""
        max_length = 50000  # 50K characters max
        if len(self.content or "") > max_length:
            frappe.throw(
                _("Message content exceeds maximum length of {0} characters").format(max_length),
                frappe.ValidationError
            )

    def after_insert(self):
        """Update session statistics after message is created."""
        self._update_session_stats()

    def _update_session_stats(self):
        """Update the parent session's message count and token usage."""
        try:
            session = frappe.get_doc("Chat Session", self.session_id)
            session.increment_message_count(self.token_count or 0)
        except Exception as e:
            # Log but don't fail - session stats are non-critical
            frappe.log_error(
                f"Failed to update session stats for {self.session_id}: {str(e)}",
                "Chat Message Stats Update Error"
            )

    @staticmethod
    def get_session_messages(session_id: str, limit: int = 50, offset: int = 0) -> list:
        """
        Get messages for a session with pagination.

        Args:
            session_id: The session to fetch messages from
            limit: Maximum number of messages to return
            offset: Number of messages to skip

        Returns:
            List of message dictionaries
        """
        messages = frappe.get_all(
            "Chat Message",
            filters={"session_id": session_id},
            fields=["name", "role", "content", "timestamp", "token_count", "model_used", "processing_time_ms"],
            order_by="timestamp asc",
            limit=limit,
            start=offset
        )
        return messages

    @staticmethod
    def get_context_messages(session_id: str, limit: int = 20) -> list:
        """
        Get the most recent messages for AI context.

        Args:
            session_id: The session to fetch context from
            limit: Maximum number of messages (default 20 for context window)

        Returns:
            List of message dictionaries formatted for AI context
        """
        messages = frappe.get_all(
            "Chat Message",
            filters={"session_id": session_id},
            fields=["role", "content"],
            order_by="timestamp desc",
            limit=limit
        )
        # Reverse to get chronological order
        messages.reverse()
        return [{"role": m.role, "content": m.content} for m in messages]

    @staticmethod
    def create_message(
        session_id: str,
        role: str,
        content: str,
        token_count: int = 0,
        model_used: str = None,
        processing_time_ms: int = None
    ) -> "ChatMessage":
        """
        Create a new chat message.

        Args:
            session_id: Parent session ID
            role: Message role (user/assistant/system)
            content: Message content
            token_count: Number of tokens (for assistant messages)
            model_used: AI model name (for assistant messages)
            processing_time_ms: Processing time (for assistant messages)

        Returns:
            Created ChatMessage document
        """
        message = frappe.get_doc({
            "doctype": "Chat Message",
            "session_id": session_id,
            "role": role,
            "content": content,
            "token_count": token_count,
            "model_used": model_used,
            "processing_time_ms": processing_time_ms,
            "timestamp": now_datetime()
        })
        message.insert(ignore_permissions=True)
        return message
