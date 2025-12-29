# Research: AI Design Interview Wizard

**Feature**: AI Design Interview Wizard
**Date**: 2025-12-29

## 1. DynamoDB Schema for Chat History

**Decision**: Create a separate `InterviewSessionsTable`.

**Rationale**:
- **Item Size Limit**: Chat history can grow large, potentially exceeding the 400KB limit of the existing `DesignsTable` if combined.
- **Access Patterns**: Chat history is only needed when the interview wizard is active, whereas the design document is accessed more frequently (e.g., list views, writing phase). Separating them optimizes Read Capacity Units (RCU).
- **Lifecycle**: Allows independent TTL policies (e.g., expire chat history after 30 days, keep designs indefinitely).

**Schema Design**:
- **Table Name**: `InterviewSessionsTable`
- **Partition Key (PK)**: `user_id` (String)
- **Sort Key (SK)**: `exam_id` (String)
- **Attributes**:
  - `history`: List of Map `[{"role": "user", "content": "..."}, ...]`
  - `updated_at`: String (ISO 8601)
  - `status`: String ("active", "completed")

## 2. FastAPI + Bedrock Streaming (SSE)

**Decision**: Use `StreamingResponse` with Server-Sent Events (SSE).

**Implementation Pattern**:
- Use `boto3.client("bedrock-runtime").invoke_model_with_response_stream`.
- Create a generator function that yields `data: {"text": "..."}\n\n` chunks.
- Return `StreamingResponse(generator, media_type="text/event-stream")`.

**Code Snippet**:
```python
async def chat_stream(request: ChatRequest):
    async def event_generator():
        response = bedrock.invoke_model_with_response_stream(...)
        for event in response['body']:
            chunk = json.loads(event['chunk']['bytes'])
            if chunk['type'] == 'content_block_delta':
                yield f"data: {json.dumps({'text': chunk['delta']['text']})}\n\n"
    return StreamingResponse(event_generator(), media_type="text/event-stream")
```

## 3. Alpine.js Streaming Consumption

**Decision**: Use `fetch` API with `ReadableStreamDefaultReader`.

**Implementation Pattern**:
- `fetch` the endpoint.
- Get `response.body.getReader()`.
- Loop `reader.read()` until done.
- Decode chunks and parse SSE format.
- Append text to Alpine.js reactive variable `messages[i].content`.

**Code Snippet**:
```javascript
const reader = response.body.getReader();
while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    const chunk = new TextDecoder().decode(value);
    // Parse "data: ..." and update UI
}
```

## 4. Alternatives Considered

- **Storing history in `DesignsTable`**: Rejected due to size limits and RCU inefficiency.
- **WebSocket**: Rejected in favor of SSE because communication is primarily one-way (server pushing tokens) after the initial request, and SSE is simpler to implement over standard HTTP/ALB without managing persistent socket connections.
