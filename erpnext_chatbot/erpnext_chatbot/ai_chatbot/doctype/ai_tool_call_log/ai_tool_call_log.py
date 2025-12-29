"""
AI Tool Call Log DocType Controller

Detailed log of individual AI agent tool invocations.
Records are immutable after creation.
"""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime


class AIToolCallLog(Document):
    """
    AI Tool Call Log provides granular visibility into tool calls.
    Records are immutable after creation.
    """

    def before_insert(self):
        """Set execution_start before inserting."""
        if not self.execution_start:
            self.execution_start = now_datetime()

    def validate(self):
        """Prevent modifications to existing records."""
        if not self.is_new():
            frappe.throw(
                _("Tool call logs cannot be modified after creation"),
                frappe.ValidationError
            )

    def on_trash(self):
        """Prevent deletion of tool call logs."""
        frappe.throw(
            _("Tool call logs cannot be deleted"),
            frappe.ValidationError
        )
