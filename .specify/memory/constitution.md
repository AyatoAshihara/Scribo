<!--
Sync Impact Report:
- Version change: New -> 1.0.0
- List of modified principles: Initial creation of all principles.
- Added sections: Core Principles, Technology Standards, Development Workflow.
- Templates requiring updates: None.
- Follow-up TODOs: None.
-->

# Scribo Constitution
<!-- Example: Spec Constitution, TaskFlow Constitution, etc. -->

## Core Principles

### I. Strategic Learning Process
<!-- Example: I. Library-First -->
The application must enforce the "Asset Preparation → Strategic Planning → Execution & Feedback" cycle. Features should not merely support writing but must guide users through the correct IPA exam preparation process (e.g., modularizing experience, designing before writing).
<!-- Example: Every feature starts as a standalone library; Libraries must be self-contained, independently testable, documented; Clear purpose required - no organizational-only libraries -->

### II. Serverless & Stateless Architecture
<!-- Example: II. CLI Interface -->
The system runs on AWS Fargate (Spot) and DynamoDB. The application logic must be stateless to handle Spot interruptions gracefully. AI features utilize Amazon Bedrock directly.
<!-- Example: Every library exposes functionality via CLI; Text in/out protocol: stdin/args → stdout, errors → stderr; Support JSON + human-readable formats -->

### III. Cognitive Load Minimization
<!-- Example: III. Test-First (NON-NEGOTIABLE) -->
UX must minimize cognitive load using Progressive Disclosure. Adhere to the Doherty Threshold (feedback within 0.4s) and use Labor Illusion for long-running AI tasks (e.g., scoring).
<!-- Example: TDD mandatory: Tests written → User approved → Tests fail → Then implement; Red-Green-Refactor cycle strictly enforced -->

### IV. Two-Tier Testing Strategy
<!-- Example: IV. Integration Testing -->
Testing is strictly divided into:
1. **Unit Tests**: Fast, mock-based, for internal logic and validation.
2. **E2E Tests**: Slow, using **real AWS resources** (DynamoDB, Bedrock), for integration verification.
Mock-based integration tests are prohibited to avoid false positives/negatives with AWS SDKs.
<!-- Example: Focus areas requiring integration tests: New library contract tests, Contract changes, Inter-service communication, Shared schemas -->

### V. Infrastructure as Code
<!-- Example: V. Observability, VI. Versioning & Breaking Changes, VII. Simplicity -->
All infrastructure changes must be defined in AWS CDK (`backend/lib`). Manual console changes are prohibited except for emergency debugging. Deployments are automated via GitHub Actions.
<!-- Example: Text I/O ensures debuggability; Structured logging required; Or: MAJOR.MINOR.BUILD format; Or: Start simple, YAGNI principles -->

## Technology Standards
<!-- Example: Additional Constraints, Security Requirements, Performance Standards, etc. -->

- **Backend**: FastAPI (Python), Pydantic for validation.
- **Frontend**: htmx for server interactions, Alpine.js for client-side state, Tailwind CSS + DaisyUI for styling.
- **Infrastructure**: AWS CDK (TypeScript).
- **AI**: Amazon Bedrock (Claude 3.5 Sonnet) for generation and scoring.
<!-- Example: Technology stack requirements, compliance standards, deployment policies, etc. -->

## Development Workflow
<!-- Example: Development Workflow, Review Process, Quality Gates, etc. -->

- **Branching**: Feature branches (`feat/`, `fix/`) merged to `main` via PR.
- **Documentation**: `docs/` must be kept in sync with code changes.
- **CI/CD**: Automated build and deploy on push to `main`.
<!-- Example: Code review requirements, testing gates, deployment approval process, etc. -->

## Governance
<!-- Example: Constitution supersedes all other practices; Amendments require documentation, approval, migration plan -->

This Constitution supersedes all other documentation. Amendments require a Pull Request with a clear rationale and version bump. All code reviews must verify compliance with these principles.
<!-- Example: All PRs/reviews must verify compliance; Complexity must be justified; Use [GUIDANCE_FILE] for runtime development guidance -->

**Version**: 1.0.0 | **Ratified**: 2025-12-29 | **Last Amended**: 2025-12-29
<!-- Example: Version: 2.1.1 | Ratified: 2025-06-13 | Last Amended: 2025-07-16 -->
