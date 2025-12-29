<!--
Sync Impact Report:
- Version change: [NEW FILE] → 1.0.0
- Modified principles: None (initial constitution)
- Added sections: All (initial constitution)
- Removed sections: None
- Templates requiring updates:
  ✅ plan-template.md (reviewed - no changes required, Constitution Check section ready)
  ✅ spec-template.md (reviewed - no changes required, requirements align)
  ✅ tasks-template.md (reviewed - no changes required, task structure compatible)
- Follow-up TODOs: None
-->

# ERPNext Claude Chatbot Constitution

## Purpose

Build an AI-powered chatbot inside ERPNext that allows users to query financial and business data using natural language, while strictly enforcing ERP permissions, auditability, and data integrity.

## Core Principles

### I. Database Access Isolation

The AI must never directly access the ERP database. All database queries and modifications must flow through authorized API layers that enforce permissions and maintain audit trails.

**Rationale**: Direct database access bypasses ERPNext's permission system, audit logging, and business logic validation. This principle ensures data integrity and security by maintaining a single point of control.

### II. API-First Data Access

All ERP data access must pass through Frappe APIs or standard ERPNext reports. No custom database queries or direct ORM access is permitted for AI operations.

**Rationale**: Frappe APIs provide built-in role-based access control, data validation, and audit logging. Using these standard interfaces ensures the chatbot respects all existing security policies and business rules without duplication.

### III. OpenAI Agent SDK for Orchestration

The OpenAI Agent SDK is used for orchestration and tool calling, providing a standardized interface for AI interactions.

**Rationale**: The OpenAI Agent SDK offers a mature, well-documented framework for building AI agents with tool-calling capabilities, reducing custom code and increasing maintainability.

### IV. Gemini 2.5 Flash via OpenAI-Compatible Endpoint

The underlying model is Gemini 2.5 Flash, accessed via an OpenAI-compatible endpoint to enable seamless integration while maintaining flexibility in model selection.

**Rationale**: OpenAI-compatible endpoints provide standardization while allowing use of alternative models like Gemini 2.5 Flash, which offers strong performance at lower cost. This approach prevents vendor lock-in.

### V. Session Isolation

Each chat must be isolated using a unique session ID. Sessions must not share state or context unless explicitly authorized.

**Rationale**: Session isolation prevents data leakage between users and conversations, ensuring privacy and compliance with data protection requirements. Each conversation maintains its own security context.

### VI. Dedicated Storage for Chat History

Chat history must be stored in dedicated DocTypes, separate from ERP transactional data. Chat records must not interfere with or pollute business transaction tables.

**Rationale**: Separation of concerns ensures chat metadata doesn't impact ERP performance or data integrity. Dedicated storage allows independent lifecycle management, retention policies, and query optimization for chat data.

### VII. Single Source of Truth

Exactly one source of truth exists: ERPNext. The AI chatbot is a read interface with limited write capabilities, never maintaining its own business data store.

**Rationale**: Multiple sources of truth lead to data inconsistency, synchronization problems, and audit failures. ERPNext remains authoritative for all business data.

### VIII. Deterministic and Auditable Operations

The system must be deterministic, auditable, and secure. All AI operations, decisions, and data access must be logged with sufficient detail for compliance audits.

**Rationale**: Business systems require reproducibility and accountability. Comprehensive audit trails enable troubleshooting, compliance verification, and security incident investigation.

### IX. Role-Based Access Control

Role-based access control must be enforced at every step. The chatbot must never bypass ERPNext's permission system or elevation of privileges.

**Rationale**: ERPNext's permission system embodies business authorization policies. The chatbot must respect these policies to maintain security and compliance, treating permissions as non-negotiable constraints.

### X. Production-Grade Standards

The solution must be production-grade, maintainable, and extensible. Code must follow ERPNext/Frappe conventions, include error handling, and support future enhancements.

**Rationale**: Production deployment requires reliability, observability, and evolvability. Adhering to framework conventions ensures the solution integrates cleanly and can be maintained by the broader development team.

## Architecture Constraints

### Technology Stack

- **Platform**: ERPNext (Frappe Framework)
- **AI Orchestration**: OpenAI Agent SDK
- **AI Model**: Gemini 2.5 Flash (via OpenAI-compatible endpoint)
- **Data Access**: Frappe REST API, ERPNext standard reports
- **Storage**: Frappe DocTypes (custom doctypes for chat sessions, messages, and audit logs)
- **Authentication**: Frappe session management and API authentication

### Security Requirements

- **Authentication**: All chatbot requests must include valid Frappe session or API credentials
- **Authorization**: Every data access must validate user permissions via Frappe's `has_permission()` checks
- **Audit Logging**: All AI interactions, tool calls, and data access must be logged with timestamps, user identity, and operation details
- **Data Sanitization**: All user inputs must be sanitized to prevent injection attacks
- **Secrets Management**: API keys, model endpoints, and credentials must be stored in encrypted configuration, never in code

### Performance Standards

- **Response Time**: p95 latency < 5 seconds for simple queries, < 15 seconds for complex multi-step operations
- **Concurrency**: Support at least 50 concurrent chat sessions without degradation
- **Rate Limiting**: Implement per-user rate limits to prevent abuse (e.g., 20 queries per minute)
- **Resource Limits**: Chatbot operations must not consume more than 20% of available system resources under normal load

### Data Governance

- **Retention Policy**: Chat history retained for 90 days by default, configurable per workspace
- **Data Classification**: Sensitive financial data must be masked in chat logs unless user has explicit view permissions
- **Data Residency**: All chat data stored in the same region/infrastructure as the ERPNext instance
- **Right to Deletion**: Users must be able to delete their chat history on request

## Development Workflow

### Code Standards

- Follow Frappe framework conventions for DocType definitions, API endpoints, and hooks
- Use Python type hints for all function signatures
- Implement comprehensive error handling with user-friendly error messages
- Write docstrings for all public functions and classes following Google style
- Maximum function complexity: 10 cyclomatic complexity
- Code coverage target: 80% for business logic

### Testing Requirements

- **Unit Tests**: All business logic functions must have unit tests with mocked dependencies
- **Integration Tests**: API endpoints must have integration tests against test ERPNext instance
- **Contract Tests**: AI tool definitions must have contract tests verifying input/output schemas
- **Permission Tests**: All data access paths must have tests verifying permission enforcement

### Deployment Process

- **Environment Parity**: Development, staging, and production environments must use identical configurations
- **Feature Flags**: New chatbot capabilities must be behind feature flags for gradual rollout
- **Rollback Plan**: Every deployment must include documented rollback procedure
- **Health Checks**: Implement `/health` endpoint for monitoring chatbot service availability
- **Observability**: Log all errors to centralized logging, expose metrics for response time and token usage

## Governance

### Amendment Process

1. Proposed amendments must be documented with rationale and impact analysis
2. Amendments affecting security or data access require security team review
3. Breaking changes require migration plan and backward compatibility strategy where feasible
4. All amendments must update this constitution file and increment version number
5. Constitution changes must be communicated to all team members before enforcement

### Compliance Verification

- All pull requests must reference constitution principles being followed
- Code reviews must verify adherence to API-first access and permission enforcement
- Quarterly audits of chat logs to verify audit trail completeness
- Monthly review of chatbot resource usage against performance standards

### Version Control

- **Version Format**: MAJOR.MINOR.PATCH semantic versioning
- **MAJOR**: Backward incompatible principle changes (e.g., removing a principle, changing data access model)
- **MINOR**: New principles added or material expansions (e.g., adding new security requirements)
- **PATCH**: Clarifications, wording improvements, non-semantic refinements

### Complexity Justification

Any violation of these principles (e.g., adding direct database access, bypassing permissions) must be explicitly justified in implementation plan with:

- Specific business need that cannot be met otherwise
- Risk assessment and mitigation strategy
- Approval from technical lead and security team
- Documentation of the exception in ADR

**Version**: 1.0.0 | **Ratified**: 2025-12-29 | **Last Amended**: 2025-12-29
