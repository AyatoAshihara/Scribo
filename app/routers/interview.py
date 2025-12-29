from fastapi import APIRouter, HTTPException, Path, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional

from services.interview import InterviewService
from models.interview import InterviewSession, DesignProposal

router = APIRouter()

# Dependency to get service
def get_interview_service():
    return InterviewService()

# 仮のユーザーID (認証実装までは固定)
DEMO_USER_ID = "demo-user"

@router.get("/sessions/{exam_id}", response_model=InterviewSession)
async def get_session(
    exam_id: str = Path(..., description="Exam ID"),
    service: InterviewService = Depends(get_interview_service)
):
    """
    Get interview session for a specific exam.
    If not found, creates a new one.
    """
    session = service.get_session(DEMO_USER_ID, exam_id)
    if not session:
        session = service.create_session(DEMO_USER_ID, exam_id)
    return session

class ChatRequest(BaseModel):
    message: str

@router.post("/chat/{exam_id}")
async def chat(
    request: ChatRequest,
    exam_id: str = Path(..., description="Exam ID"),
    service: InterviewService = Depends(get_interview_service)
):
    """
    Send a message to the AI interviewer and get a streaming response.
    """
    return StreamingResponse(
        service.generate_stream(DEMO_USER_ID, exam_id, request.message),
        media_type="text/event-stream"
    )

@router.post("/generate/{exam_id}", response_model=DesignProposal)
async def generate_design(
    exam_id: str = Path(..., description="Exam ID"),
    service: InterviewService = Depends(get_interview_service)
):
    """
    Generate a design proposal based on the interview history.
    """
    try:
        proposal = service.generate_design_proposal(DEMO_USER_ID, exam_id)
        return proposal
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
