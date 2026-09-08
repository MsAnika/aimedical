# 4️⃣  Production Docker multistage image
# ---------- Build stage ----------
FROM python:3.12-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc && rm -rf /var/lib/apt/lists/*

COPY requirements.txt requirements-postgres.txt ./
RUN pip install --no-cache-dir -r requirements.txt \
                 -r requirements-postgres.txt

COPY app ./app
COPY ml ./ml

# ---------- Runtime stage ----------
FROM python:3.12-slim AS runtime

WORKDIR /app

COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=builder /usr/local/lib /usr/local/lib

COPY app ./app
COPY ml ./ml

COPY run.sh ./run.sh
RUN chmod +x ./run.sh

ENV DATABASE_URL postgresql+psycopg2://meddiag:meddiag@db:5432/meddiag
ENV SECRET_KEY change-me-to-a-long-random-string
ENV MODEL_DIR ./app/services/ml/models
ENV MEDIA_DIR ./media

EXPOSE 8000

CMD ["./run.sh"]