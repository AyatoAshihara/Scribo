# Tasks: AI Design Interview Wizard

**Feature Branch**: `001-ai-design-interview`
**Status**: Draft

## Phase 1: Setup (Infrastructure)

- [x] T001 Update `backend/lib/backend-stack.ts` to create `InterviewSessionsTable` (PK: user_id, SK: exam_id)
- [x] T002 Update `backend/lib/backend-stack.ts` to grant DynamoDB read/write permissions to the backend Lambda
- [x] T003 Update `backend/lib/backend-stack.ts` to grant Bedrock `InvokeModel` permissions to the backend Lambda (if not already sufficient)
- [x] T004 Deploy CDK stack to create the new table

## Phase 2: Foundational (Backend Core)

- [x] T005 [P] Create Pydantic models in `app/models/interview.py` (`InterviewSession`, `ChatMessage`, `DesignProposal`)
- [x] T006 [P] Create `InterviewService` class in `app/services/interview.py` with methods for session management (get/create/update)
- [x] T007 Implement DynamoDB persistence logic in `InterviewService` (save/load history)
- [x] T008 Create `app/routers/interview.py` and register it in `app/main.py`
- [x] T009 Implement `GET /api/interview/sessions/{exam_id}` endpoint in `app/routers/interview.py`

## Phase 3: User Story 1 - AI Interview Initiation

**Goal**: User can open the interview modal and see the initial greeting.

- [x] T010 [US1] Create `app/templates/components/interview_modal.html` with the modal UI structure (DaisyUI)
- [x] T011 [US1] Include the modal template in `app/templates/pages/design_wizard.html`
- [x] T012 [US1] Create `app/static/js/interview.js` with Alpine.js component `interviewWizard`
- [x] T013 [US1] Implement `open(examId)` method in `interview.js` to fetch session and show modal
- [x] T014 [US1] Add "Start AI Interview" button to `app/templates/pages/design_wizard.html` header
- [x] T015 [US1] Implement logic in `InterviewService` to generate initial greeting if session is new

## Phase 4: User Story 2 - Interactive Interview Process

**Goal**: User can chat with the AI with streaming responses and persistence.

- [x] T016 [US2] Implement `POST /api/interview/chat/{exam_id}` endpoint with `StreamingResponse`
- [x] T017 [US2] Implement `generate_stream` method in `InterviewService` using `bedrock.invoke_model_with_response_stream`
- [x] T018 [US2] Implement prompt engineering for the interviewer persona (system prompt)
- [x] T019 [US2] Update `interview.js` to handle message sending and SSE stream consumption (`fetch` + `ReadableStreamDefaultReader`)
- [x] T020 [US2] Implement auto-scroll logic in `interview.js` during streaming
- [x] T021 [US2] Ensure chat history is persisted to DynamoDB after each turn in `InterviewService`

## Phase 5: User Story 3 - Design Generation & Application

**Goal**: AI generates structured design and populates the wizard fields.

- [x] T022 [US3] Implement `POST /api/interview/generate/{exam_id}` endpoint
- [x] T023 [US3] Implement `generate_design_proposal` method in `InterviewService` with specific JSON-output prompt
- [x] T024 [US3] Add "Generate Design" button to the chat modal header
- [x] T025 [US3] Implement `applyDesign(proposal)` method in `interview.js` to map data to the parent `designWizard` component
- [x] T026 [US3] Implement overwrite warning logic in `interview.js` (check if fields are dirty)
- [x] T027 [US3] Add logic for AI to suggest generation in the chat stream (e.g., by detecting a specific phrase like "設計書を作成しましょうか" in the response)

## Phase 6: Polish & Cross-Cutting

- [ ] T028 Add error handling for Bedrock timeouts/failures in `interview.js`
- [ ] T029 Add loading states (spinners) for non-streaming operations
- [ ] T030 Style the chat interface to match the application theme (Tailwind/DaisyUI)
- [ ] T031 Verify mobile responsiveness of the chat modal

## Dependencies

1. **Setup** (T001-T004) must be completed first.
2. **Foundational** (T005-T009) blocks all User Stories.
3. **US1** (T010-T015) blocks US2.
4. **US2** (T016-T021) blocks US3.

## Parallel Execution Opportunities

- **Backend/Frontend Split**: T005-T009 (Backend) can be done in parallel with T010-T012 (Frontend Skeleton).
- **Service/UI**: T017 (Bedrock Logic) can be developed while T019 (JS Streaming) is being implemented using a mock stream.
