# Feature Specification: AI Design Interview Wizard

**Feature Branch**: `001-ai-design-interview`  
**Created**: 2025-12-29  
**Status**: Draft  
**Input**: User description: "論文設計ウィザードを生成AIとのチャットで作成できるようにしたい。生成AIがユーザーに必要な情報をインタビューし、回答によって設計書を作っていく。ユーザーはいきなり設計書作れといわれても、うまく作れないため。"

## Clarifications

### Session 2025-12-29

- Q: Where should chat history be stored? → A: Server-side persistence (DynamoDB).
- Q: How should the system handle applying the design if fields are already filled? → A: Warning & Overwrite (Check if fields are non-empty; if so, ask for confirmation).
- Q: How should the AI response be delivered to the user? → A: Streaming Responses (Display text incrementally via SSE/WebSocket).
- Q: What is the UI layout for the chat interface? → A: Dedicated "Interview" Mode (Modal/Overlay) that focuses attention.
- Q: How is the design generation triggered? → A: Hybrid (AI prompts when ready; user can also force it via a header button).

## User Scenarios & Testing

### User Story 1 - AI Interview Initiation (Priority: P1)

As a user who is unsure how to structure my thesis, I want to start an AI interview so that the AI can guide me through the necessary thinking process.

**Why this priority**: This is the entry point for the feature and addresses the core pain point of users not knowing where to start.

**Independent Test**: Can be tested by opening the Design Wizard and clicking a "Start AI Interview" button, verifying that a chat interface appears and the AI initiates the conversation relevant to the selected problem.

**Acceptance Scenarios**:

1. **Given** I am on the Design Wizard page for a specific problem, **When** I click "Start AI Interview", **Then** a chat interface opens as a focused modal overlay.
2. **Given** the chat interface opens, **When** the session starts, **Then** the AI sends a greeting and asks the first question relevant to the problem's context (e.g., "What kind of project would you like to write about for this problem?").

---

### User Story 2 - Interactive Interview Process (Priority: P1)

As a user, I want to answer the AI's questions in natural language so that I can explain my experience without worrying about the formal structure yet.

**Why this priority**: This is the core interaction mechanism. The AI needs to gather information effectively.

**Independent Test**: Can be tested by simulating a conversation. User sends a message, AI responds with a follow-up question or acknowledgement.

**Acceptance Scenarios**:

1. **Given** the AI has asked a question, **When** I type a response and send it, **Then** the message appears in the chat history.
2. **Given** I have sent a response, **When** the AI processes it, **Then** the AI replies with a relevant follow-up question to deepen the details needed for the thesis design (e.g., asking about specific challenges or solutions).
3. **Given** the interview is in progress, **When** I ask for clarification (e.g., "What do you mean?"), **Then** the AI explains the question in the context of the exam.

---

### User Story 3 - Design Generation & Application (Priority: P1)

As a user, I want the AI to generate a structured design document from our conversation so that I can have a solid starting point for my thesis.

**Why this priority**: This delivers the actual value of the feature—converting the chat into a structured output.

**Independent Test**: Can be tested by completing a short interview and verifying that the "Theme", "Breakdown", and "Chapter Structure" fields are populated with content derived from the chat.

**Acceptance Scenarios**:

1. **Given** the AI has gathered enough information, **When** the AI determines the interview is complete, **Then** the AI suggests generating the design.
2. **Given** the interview is in progress, **When** I click the "Generate Design" button in the header, **Then** the system prompts the AI to generate the design based on the information gathered so far.
3. **Given** the AI has generated a design proposal, **When** I click to apply it, **AND** the fields are not empty, **Then** the system shows a confirmation warning that existing content will be overwritten. **When** I confirm, **Then** the fields are populated.
4. **Given** the fields are populated, **When** I review them, **Then** I can still manually edit them if needed.

### Edge Cases

- What happens when the user provides irrelevant or nonsensical answers? (AI should politely steer back to the topic)
- What happens if the API call to Bedrock fails? (Show error message and allow retry)
- What happens if the user closes the chat mid-interview? (State should be preserved if possible, or warn about data loss)

## Requirements

### Functional Requirements

- **FR-001**: The system MUST provide a chat interface as a modal overlay within the Design Wizard page.
- **FR-002**: The system MUST use a Generative AI model to conduct the interview.
- **FR-003**: The AI MUST be provided with the context of the current exam problem (Problem Statement, Constraints).
- **FR-004**: The AI MUST be capable of asking progressive questions to gather information for:
  - Thesis Theme (Bone structure)
  - Section A (Background/Issues)
  - Section B (Solution/Action)
- **FR-005**: The system MUST allow the user to manually trigger "Design Generation" at any time via a UI button. The AI MUST also be able to suggest generation when it determines sufficient information has been gathered (e.g., by including a specific suggestion text or flag in the response).
- **FR-006**: The AI MUST output the design in a structured format containing `theme`, `breakdown` (A, B, C), and `structure` (chapters) when requested, matching the `DesignProposal` schema defined in the data model.
- **FR-008**: The chat history MUST be persisted to the server-side database to allow resuming sessions across page reloads or devices.
- **FR-009**: The system MUST stream AI responses to the client (e.g., via Server-Sent Events) to minimize perceived latency.

### Key Entities

- **InterviewSession**: Represents the state of the current chat (messages, status).
- **ChatMessage**: Individual messages with `role` (user/assistant), `content`, and `timestamp`.
- **DesignProposal**: The structured output generated by AI, matching the `Design` schema.

## Assumptions

- The existing Generative AI integration in the backend can be reused or extended for this chat purpose.
- The chat session data will be stored in the existing database infrastructure.
- The "Design Wizard" UI has space to accommodate a modal overlay.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Users can generate a complete design (Theme + Breakdown + Structure) within 10 minutes of chat interaction on average.
- **SC-002**: 80% of users accept the AI-generated design with minor or no edits.
- **SC-003**: The AI successfully extracts structured data from the conversation in 95% of attempts.
- **SC-004**: The chat interface response time (time to first token) is under 3 seconds.
