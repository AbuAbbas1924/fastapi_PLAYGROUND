FROM python:3.14-alpine AS builder
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
ENV UV_LINK_MODE=copy
WORKDIR /app
# RUN apk add --no-cache gcc g++ musl-dev python3-dev make file
COPY . .
RUN uv sync --no-dev
EXPOSE 8000
# CMD ["uv", "run", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload", "--log-level", "info", "--workers", "1"]
CMD ["uv", "run", "fastapi", "dev", "--host", "0.0.0.0", "--port", "8000", "--reload"]