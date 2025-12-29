"""
Scribo API ルーター
"""

from routers.exams import router as exams_router
from routers.answers import router as answers_router
from routers.scoring import router as scoring_router
from routers.modules import router as modules_router
from routers.designs import router as designs_router

__all__ = ["exams_router", "answers_router", "scoring_router", "modules_router", "designs_router"]
