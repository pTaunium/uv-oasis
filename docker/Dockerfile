# ============================================================
# Stage 1: Builder
# - Install deps, run build.py to download Python tarballs + generate JSON
# ============================================================
FROM --platform=$BUILDPLATFORM ghcr.io/astral-sh/uv:python3.14-alpine AS builder

# uv best practices
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV UV_NO_DEV=1

WORKDIR /app

# Intermediate layer: install dependencies first (Docker cache friendly)
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project

# Copy only the necessary python source code
COPY build.py /app/
COPY uv_oasis /app/uv_oasis

# Run build script: download tarballs + generate JSON
RUN uv run python build.py --output /app/dist

# ============================================================
# Stage 2: Runtime
# - Pure nginx static file server, no Python/uv needed
# ============================================================
FROM nginx:alpine

LABEL org.opencontainers.image.title="uv-oasis"
LABEL org.opencontainers.image.description="Offline Python mirror for uv in air-gapped environments"
LABEL org.opencontainers.image.licenses="MIT"
LABEL org.opencontainers.image.source="https://github.com/pTaunium/uv-oasis"

COPY docker/nginx.conf /etc/nginx/templates/default.conf.template
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Copy documentation and licenses
COPY LICENSE /usr/share/nginx/html/LICENSE
COPY README.md /usr/share/nginx/html/README.md

# Copy build artifacts from builder
COPY --from=builder /app/dist/assets /usr/share/nginx/html/assets
COPY --from=builder /app/dist/download-metadata.json.template /usr/share/nginx/html/

EXPOSE 8080

ENTRYPOINT ["/entrypoint.sh"]
