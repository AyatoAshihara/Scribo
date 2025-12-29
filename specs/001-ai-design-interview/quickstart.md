# Quickstart: AI Design Interview Wizard

## Overview
The AI Design Interview Wizard allows users to interactively design their thesis structure using an AI chat interface.

## Prerequisites
- AWS Credentials configured with access to Bedrock (Claude 3.5 Sonnet) and DynamoDB.
- `InterviewSessionsTable` created in DynamoDB (or local mock).

## Usage

### 1. Start the Interview
Open the Design Wizard for a problem. Click the "Start AI Interview" button in the header.

```javascript
// Frontend triggers
Alpine.store('interview').open('ST-2024-1');
```

### 2. Chatting
Type your response in the modal. The AI will stream the reply.

```http
POST /api/interview/chat/ST-2024-1
Content-Type: application/json

{
  "message": "I want to write about an agile transformation project."
}
```

### 3. Generating Design
When ready, click "Generate Design" or accept the AI's suggestion.

```http
POST /api/interview/generate/ST-2024-1
```

The response will contain the structured design. The frontend will prompt to overwrite existing fields.

## Development

### Running Locally
1. Ensure `AWS_PROFILE` is set.
2. Run `uvicorn main:app --reload`.
3. Access `http://localhost:8000/exam/ST/ST-2024-1/design`.

### Testing
- **Unit Tests**: `pytest tests/unit/test_interview.py`
- **E2E Tests**: `pytest tests/e2e/test_interview_flow.py`
