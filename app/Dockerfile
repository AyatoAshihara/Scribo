# Scribo FastAPI アプリケーション
# マルチステージビルドで軽量イメージを作成

FROM python:3.12-slim as builder

WORKDIR /app

# 依存関係のインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 本番イメージ
FROM python:3.12-slim

WORKDIR /app

# curl をインストール（ヘルスチェック用）
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

# ビルダーからパッケージをコピー
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# アプリケーションコードをコピー
COPY . .

# ヘルスチェック用
EXPOSE 8000

# uvicorn起動
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
