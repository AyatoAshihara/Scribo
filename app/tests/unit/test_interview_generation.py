import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime
import json

from services.interview import InterviewService
from models.interview import InterviewSession, ChatMessage, Role, DesignProposal

# Mock data
MOCK_USER_ID = "demo-user"
MOCK_EXAM_ID = "test-exam"
MOCK_HISTORY = [
    ChatMessage(role=Role.ASSISTANT, content="Hello"),
    ChatMessage(role=Role.USER, content="I want to write about logistics."),
]
MOCK_PROPOSAL_JSON = {
    "theme": "Logistics Optimization",
    "breakdown": {"A": "Issue", "B": "Solution", "C": "Result"},
    "structure": [{"chapter": "1", "title": "Intro", "sections": ["s1"]}],
    "module_map": {"chapter1": ["m1"]},
    "reasoning": "Because it is good."
}

class TestInterviewServiceGeneration:
    
    @pytest.fixture
    def mock_dynamodb(self):
        with patch("boto3.resource") as mock:
            yield mock

    @pytest.fixture
    def mock_bedrock(self):
        with patch("boto3.client") as mock:
            yield mock

    @pytest.fixture
    def service(self, mock_dynamodb, mock_bedrock):
        # Reset singleton for testing
        InterviewService._dynamodb_resource = None
        InterviewService._bedrock_runtime = None
        InterviewService._table = None
        return InterviewService()

    def test_generate_design_proposal_success(self, service):
        # Mock get_session
        mock_session = InterviewSession(
            user_id=MOCK_USER_ID,
            exam_id=MOCK_EXAM_ID,
            history=MOCK_HISTORY
        )
        service.get_session = MagicMock(return_value=mock_session)
        service.update_proposal = MagicMock()

        # Mock Bedrock response
        mock_response_body = {
            "content": [{"text": json.dumps(MOCK_PROPOSAL_JSON)}]
        }
        service.bedrock_runtime.invoke_model.return_value = {
            "body": MagicMock(read=lambda: json.dumps(mock_response_body).encode("utf-8"))
        }

        # Execute
        proposal = service.generate_design_proposal(MOCK_USER_ID, MOCK_EXAM_ID)

        # Verify
        assert isinstance(proposal, DesignProposal)
        assert proposal.theme == "Logistics Optimization"
        assert proposal.breakdown["A"] == "Issue"
        
        # Verify Bedrock call
        service.bedrock_runtime.invoke_model.assert_called_once()
        call_args = service.bedrock_runtime.invoke_model.call_args
        assert "logistics" in json.loads(call_args.kwargs["body"])["messages"][0]["content"].lower()
        
        # Verify update_proposal called
        service.update_proposal.assert_called_once_with(MOCK_USER_ID, MOCK_EXAM_ID, proposal)

    def test_generate_design_proposal_markdown_stripping(self, service):
        # Mock get_session
        mock_session = InterviewSession(
            user_id=MOCK_USER_ID,
            exam_id=MOCK_EXAM_ID,
            history=MOCK_HISTORY
        )
        service.get_session = MagicMock(return_value=mock_session)
        service.update_proposal = MagicMock()

        # Mock Bedrock response with markdown code blocks
        json_str = json.dumps(MOCK_PROPOSAL_JSON)
        markdown_text = f"Here is the JSON:\n```json\n{json_str}\n```"
        
        mock_response_body = {
            "content": [{"text": markdown_text}]
        }
        service.bedrock_runtime.invoke_model.return_value = {
            "body": MagicMock(read=lambda: json.dumps(mock_response_body).encode("utf-8"))
        }

        # Execute
        proposal = service.generate_design_proposal(MOCK_USER_ID, MOCK_EXAM_ID)

        # Verify
        assert proposal.theme == "Logistics Optimization"

    def test_generate_design_proposal_session_not_found(self, service):
        service.get_session = MagicMock(return_value=None)
        
        with pytest.raises(ValueError, match="Session not found"):
            service.generate_design_proposal(MOCK_USER_ID, MOCK_EXAM_ID)

