"""
Chat Session DocType Controller

Manages chat session lifecycle with UUID generation, user validation,
and session ownership enforcement.
"""

import uuid
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime


class ChatSession(Document):
    """
    Chat Session represents a conversation thread between a user and the AI chatbot.
    Each session is isolated, linked to a single user, and maintains its own context.
    """

    def before_insert(self):
        """Generate UUID and set initial values before inserting."""
        if not self.session_id:
            self.session_id = str(uuid.uuid4())

        if not self.user:
            self.user = frappe.session.user

        if not self.created_at:
            self.created_at = now_datetime()

        if not self.last_activity:
            self.last_activity = now_datetime()

        if not self.company_context:
            # Set default company from user preferences
            self.company_context = frappe.defaults.get_user_default("Company")

    def validate(self):
        """Validate session data before saving."""
        self._validate_user_ownership()
        self._validate_status_transition()

    def _validate_user_ownership(self):
        """Ensure user cannot be changed after creation."""
        if not self.is_new() and self.has_value_changed("user"):
            frappe.throw(
                _("Session owner cannot be changed after creation"),
                frappe.ValidationError
            )

    def _validate_status_transition(self):
        """Validate status transitions - cannot reactivate expired sessions."""
        if not self.is_new():
            old_status = self.get_doc_before_save().status if self.get_doc_before_save() else None
            if old_status == "Expired" and self.status == "Active":
                frappe.throw(
                    _("Cannot reactivate an expired session"),
                    frappe.ValidationError
                )

    def update_last_activity(self):
        """Update last_activity timestamp when a new message is added."""
        self.last_activity = now_datetime()
        self.save(ignore_permissions=True)

    def increment_message_count(self, token_count: int = 0):
        """Increment message count and add tokens."""
        self.message_count = (self.message_count or 0) + 1
        self.total_tokens = (self.total_tokens or 0) + token_count
        self.last_activity = now_datetime()
        self.save(ignore_permissions=True)

    def close_session(self):
        """Close the session (user-initiated)."""
        if self.status == "Expired":
            frappe.throw(_("Cannot close an expired session"))
        self.status = "Closed"
        self.save()

    def expire_session(self):
        """Mark session as expired (system-initiated)."""
        if self.status == "Active":
            self.status = "Expired"
            self.save(ignore_permissions=True)

    @staticmethod
    def validate_session_ownership(session_id: str, user: str = None) -> "ChatSession":
        """
        Validate that the user owns the session.

        Args:
            session_id: The session ID to validate
            user: The user to validate against (defaults to current user)

        Returns:
            ChatSession document if valid

        Raises:
            frappe.PermissionError: If user doesn't own the session
            frappe.DoesNotExistError: If session doesn't exist
        """
        if user is None:
            user = frappe.session.user

        if not frappe.db.exists("Chat Session", session_id):
            frappe.throw(
                _("Chat session not found: {0}").format(session_id),
                frappe.DoesNotExistError
            )

        session = frappe.get_doc("Chat Session", session_id)

        if session.user != user and user != "Administrator":
            frappe.throw(
                _("You do not have permission to access this chat session"),
                frappe.PermissionError
            )

        return session

    @staticmethod
    def is_session_active(session_id: str) -> bool:
        """Check if session is active and not expired."""
        if not frappe.db.exists("Chat Session", session_id):
            return False

        status = frappe.db.get_value("Chat Session", session_id, "status")
        return status == "Active"
