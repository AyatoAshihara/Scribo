"""
Scribo - IPA午後Ⅱ論述式試験 学習支援アプリケーション
FastAPI + htmx + Jinja2 構成

メインエントリーポイント
"""

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from starlette.middleware.base import BaseHTTPMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from config import get_settings
from routers import exams, answers, scoring

settings = get_settings()

# レート制限設定
limiter = Limiter(key_func=get_remote_address)


# =============================================================================
# セキュリティヘッダーミドルウェア
# =============================================================================
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """XSS、クリックジャッキング等を防ぐセキュリティヘッダーを追加"""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        # XSS対策
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        # リファラー情報漏洩防止
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        # CSP（CDNからのスクリプト読み込みを許可）
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://cdn.tailwindcss.com https://unpkg.com; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data:; "
            "connect-src 'self';"
        )
        return response


# FastAPIアプリケーション初期化
app = FastAPI(
    title=settings.app_name,
    description=settings.app_description,
    version="2.0.0",
)

# レート制限ハンドラー登録
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# セキュリティヘッダーミドルウェア追加
app.add_middleware(SecurityHeadersMiddleware)

# 静的ファイル（CSS, JS）
app.mount("/static", StaticFiles(directory="static"), name="static")

# Jinja2テンプレート
templates = Jinja2Templates(directory="templates")

# ルーター登録
app.include_router(exams.router, prefix="/api/exams", tags=["exams"])
app.include_router(answers.router, prefix="/api/answers", tags=["answers"])
app.include_router(scoring.router, prefix="/api/scoring", tags=["scoring"])


# =============================================================================
# ページルート（HTMLを返す）
# =============================================================================

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """トップページ - 試験一覧"""
    return templates.TemplateResponse(
        "pages/index.html",
        {"request": request, "title": "試験一覧"}
    )


@app.get("/exam/{exam_type}/{problem_id:path}", response_class=HTMLResponse)
async def problem_page(request: Request, exam_type: str, problem_id: str):
    """問題閲覧・回答ページ"""
    # URLエンコードされたproblem_idをデコード
    from urllib.parse import unquote
    decoded_problem_id = unquote(problem_id)
    
    return templates.TemplateResponse(
        "pages/problem.html",
        {
            "request": request,
            "title": "問題",
            "exam_type": exam_type,
            "problem_id": decoded_problem_id,
        }
    )


@app.get("/result/{submission_id}", response_class=HTMLResponse)
async def result_page(request: Request, submission_id: str):
    """採点結果ページ"""
    return templates.TemplateResponse(
        "pages/result.html",
        {
            "request": request,
            "title": "採点結果",
            "submission_id": submission_id,
        }
    )


@app.get("/health")
async def health_check():
    """ヘルスチェックエンドポイント（ALB用）"""
    return {"status": "healthy", "app": settings.app_name}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
