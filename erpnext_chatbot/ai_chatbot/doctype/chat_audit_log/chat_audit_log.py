"""
Chat Audit Log DocType Controller

Immutable audit trail for compliance. All records are read-only after creation.
"""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime


class ChatAuditLog(Document):
    """
    Chat Audit Log maintains a compliance audit trail for all AI interactions.
    Records are immutable after creation.
    """

    def before_insert(self):
        """Set timestamp before inserting."""
        if not self.timestamp:
            self.timestamp = now_datetime()

    def validate(self):
        """Prevent modifications to existing records."""
        if not self.is_new():
            frappe.throw(
                _("Audit logs cannot be modified after creation"),
                frappe.ValidationError
            )

    def on_trash(self):
        """Prevent deletion of audit logs."""
        frappe.throw(
            _("Audit logs cannot be deleted"),
            frappe.ValidationError
        )
