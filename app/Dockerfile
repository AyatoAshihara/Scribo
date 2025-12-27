# Scribo FastAPI アプリケーション
# マルチステージビルドで軽量イメージを作成

FROM python:3.12-slim as builder

WORKDIR /app

# 依存関係のインストール
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# 本番イメージ
FROM python:3.12-slim

WORKDIR /app

# ビルダーからパッケージをコピー
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# アプリケーションコードをコピー
COPY . .

# 非rootユーザーで実行（セキュリティ）
RUN useradd --create-home appuser
USER appuser

# ヘルスチェック用
EXPOSE 8000

# uvicorn起動
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
