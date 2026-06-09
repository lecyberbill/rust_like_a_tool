# Phase 3a — Multi-stage Dockerfile
# Stage 1: Build Rust binary
FROM rust:1.82-slim-bookworm AS builder
WORKDIR /app
COPY rust_muscle/ ./rust_muscle/
RUN apt-get update && apt-get install -y --no-install-recommends pkg-config libssl-dev && \
    rm -rf /var/lib/apt/lists/*
RUN cargo build --release --manifest-path rust_muscle/Cargo.toml

# Stage 2: Python runtime
FROM python:3.13-slim-bookworm
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates && \
    rm -rf /var/lib/apt/lists/*

COPY --from=builder /app/rust_muscle/target/release/rust_muscle /usr/local/bin/rust_muscle
COPY brain/ ./brain/
COPY vitrine/ ./vitrine/
COPY .env ./

RUN pip install --no-cache-dir websockets jsonschema pillow

EXPOSE 8765 8766

ENV RUST_BIN_PATH=/usr/local/bin/rust_muscle
ENV WFGY_ENV=prod

CMD ["python", "brain/orchestrator.py", "--server"]
