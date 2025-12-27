"""
Scribo API ルーター
"""

from routers.exams import router as exams_router
from routers.answers import router as answers_router
from routers.scoring import router as scoring_router

__all__ = ["exams_router", "answers_router", "scoring_router"]
