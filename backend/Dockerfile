FROM python:3.11-slim

# git: 업로드(gitops) 시 clone/commit/tag/push 에 필요.
RUN apt-get update \
    && apt-get install -y --no-install-recommends git ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

# 감사 로그 SQLite 위치 (db.py 가 /app/data/audit.db 로 해석). 볼륨으로 마운트 권장.
RUN mkdir -p /app/data

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
