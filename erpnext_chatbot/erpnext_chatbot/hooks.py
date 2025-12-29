"""
Frappe Hooks for ERPNext Chatbot

This file defines app configuration, scheduled jobs, and UI integrations.
"""

app_name = "erpnext_chatbot"
app_title = "ERPNext Chatbot"
app_publisher = "ERPNext Chatbot Team"
app_description = "AI-powered chatbot for querying financial and business data"
app_email = "admin@truetechterminal.com"
app_license = "MIT"

# Required Apps
required_apps = ["frappe", "erpnext"]

# App Includes
# -------------

# Include CSS in desktop
app_include_css = "/assets/erpnext_chatbot/css/chatbot.css"

# Include JS in desktop
app_include_js = "/assets/erpnext_chatbot/js/chatbot_widget.js"

# Home Pages
# ----------

# Application home page (will override Website Settings)
# home_page = "login"

# Website user home page (by Role)
# role_home_page = {
#     "Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# Add methods and filters to jinja environment
# jinja = {
#     "methods": "erpnext_chatbot.utils.jinja_methods",
#     "filters": "erpnext_chatbot.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "erpnext_chatbot.install.before_install"
# after_install = "erpnext_chatbot.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "erpnext_chatbot.uninstall.before_uninstall"
# after_uninstall = "erpnext_chatbot.uninstall.after_uninstall"

# Desk Notifications
# ------------------

# See frappe.core.notifications.get_notification_config

# notification_config = "erpnext_chatbot.notifications.get_notification_config"

# Permissions
# -----------

# Permissions evaluated in scripted ways

# permission_query_conditions = {
#     "Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }

# has_permission = {
#     "Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------

# Override standard doctype classes
# override_doctype_class = {
#     "ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------

# Hook on document methods and events
# doc_events = {
#     "*": {
#         "on_update": "method",
#         "on_cancel": "method",
#         "on_trash": "method"
#     }
# }

# Scheduled Tasks
# ---------------

scheduler_events = {
    # Expire inactive sessions every hour
    "hourly": [
        "erpnext_chatbot.services.session_manager.expire_inactive_sessions"
    ],
    # Clean up old sessions daily (90-day retention)
    "daily": [
        "erpnext_chatbot.services.session_manager.delete_old_sessions"
    ],
}

# Testing
# -------

# before_tests = "erpnext_chatbot.install.before_tests"

# Overriding Methods
# ------------------------------

# override_whitelisted_methods = {
#     "frappe.desk.doctype.event.event.get_events": "erpnext_chatbot.event.get_events"
# }

# Each overriding function accepts a `data` argument
# containing the data to be saved. You can alter the data
# here before it's saved to database.

# override_doctype_dashboards = {
#     "Task": "erpnext_chatbot.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------

# before_request = ["erpnext_chatbot.utils.before_request"]
# after_request = ["erpnext_chatbot.utils.after_request"]

# Job Events
# ----------

# before_job = ["erpnext_chatbot.utils.before_job"]
# after_job = ["erpnext_chatbot.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
#     {
#         "doctype": "{doctype_1}",
#         "filter_by": "{filter_by}",
#         "redact_fields": ["{field_1}", "{field_2}"],
#         "partial": 1,
#     },
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
#     "erpnext_chatbot.auth.validate"
# ]
