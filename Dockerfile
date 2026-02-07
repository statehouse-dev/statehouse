# Statehouse daemon - multi-stage build
FROM rust:1.83-bookworm AS builder
RUN apt-get update && apt-get install -y --no-install-recommends \
    clang \
    libclang-dev \
    protobuf-compiler \
    libprotobuf-dev \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /build
COPY Cargo.toml ./
COPY crates/ crates/
RUN cargo build --release -p statehouse-daemon

# Runtime stage
FROM debian:bookworm-slim
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates && rm -rf /var/lib/apt/lists/*
COPY --from=builder /build/target/release/statehoused /usr/local/bin/
EXPOSE 50051
ENV STATEHOUSE_ADDR=0.0.0.0:50051
# In-memory by default so container works without a volume; unset for persistence and mount /data
ENV STATEHOUSE_USE_MEMORY=1
ENTRYPOINT ["statehoused"]
