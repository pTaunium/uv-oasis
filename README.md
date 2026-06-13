# uv-oasis 🏝️

Offline Python distribution mirror for [uv](https://docs.astral.sh/uv/) in **air-gapped environments**.

Downloads selected [python-build-standalone](https://github.com/astral-sh/python-build-standalone) distributions, packages them into a Docker image with nginx, and serves them as a drop-in replacement for uv's default Python download source.

## Supported Python Versions

| Minor | Platforms                                | Variants             |
| ----- | ---------------------------------------- | -------------------- |
| 3.14  | linux-x86_64 (gnu, musl), windows-x86_64 | normal, freethreaded |
| 3.13  | linux-x86_64 (gnu, musl), windows-x86_64 | normal, freethreaded |
| 3.12  | linux-x86_64 (gnu, musl), windows-x86_64 | normal               |
| 3.11  | linux-x86_64 (gnu, musl), windows-x86_64 | normal               |
| 3.10  | linux-x86_64 (gnu, musl), windows-x86_64 | normal               |
| 3.9   | linux-x86_64 (gnu, musl), windows-x86_64 | normal               |
| 3.8   | linux-x86_64 (gnu), windows-x86_64       | normal               |

> Only the **latest stable patch** of each minor version is included.
> Freethreaded builds are available from Python 3.13+.

## Quick Start

### Pull and run

```bash
docker run -d -p 8080:8080 \
  -e BASE_URL=http://localhost:8080 \
  --name uv-oasis \
  ghcr.io/pTaunium/uv-oasis:latest
```

### Configure uv

```bash
export UV_PYTHON_DOWNLOADS_JSON_URL=http://localhost:8080/download-metadata.json
uv python install 3.13
```

## Air-Gapped Deployment

```bash
# 1. On a machine with internet access:
docker pull ghcr.io/pTaunium/uv-oasis:latest
docker save ghcr.io/pTaunium/uv-oasis:latest -o uv-oasis.tar

# 2. Transfer uv-oasis.tar to the air-gapped environment

# 3. On the air-gapped machine:
docker load -i uv-oasis.tar
docker run -d -p 8080:8080 \
  -e BASE_URL=http://python-mirror.internal:8080 \
  --name uv-oasis \
  ghcr.io/pTaunium/uv-oasis:latest

# 4. Configure uv on developer machines:
export UV_PYTHON_DOWNLOADS_JSON_URL=http://python-mirror.internal:8080/download-metadata.json
uv python install 3.13
```

## Docker Compose

```yaml
services:
  uv-oasis:
    image: ghcr.io/pTaunium/uv-oasis:latest
    ports:
      - "8080:8080"
    environment:
      - BASE_URL=http://python-mirror.internal:8080
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "-s", "http://localhost:8080/health"]
      interval: 30s
      timeout: 5s
      retries: 3
```

## Kubernetes (with Ingress)

To deploy `uv-oasis` behind a Kubernetes Ingress, you need a Deployment, a Service, and an Ingress resource.

**Awesome Feature:** The Docker container automatically configures its internal Nginx routing based on the path provided in your `BASE_URL`. If you set `BASE_URL="https://mirror.company.internal/uv-python"`, the container will automatically serve files at `/uv-python/...`. This means **you do NOT need complex rewrite rules** in your Ingress controller!

_(If your Ingress or Reverse Proxy **already strips the path**, you can set `PROXY_REWRITES_PATH: "true"` to disable this automatic internal routing.)_

```yaml
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: uv-oasis
spec:
  replicas: 1
  selector:
    matchLabels:
      app: uv-oasis
  template:
    metadata:
      labels:
        app: uv-oasis
    spec:
      containers:
        - name: uv-oasis
          image: ghcr.io/<your-username>/uv-oasis:latest
          ports:
            - containerPort: 8080
          env:
            # Set this to the exact URL the clients will use.
            # The container automatically extracts the path (/uv-python) and configures Nginx.
            - name: BASE_URL
              value: "https://mirror.company.internal/uv-python"
            # - name: PROXY_REWRITES_PATH
            #   value: "false"
          readinessProbe:
            httpGet:
              # The health check automatically adapts to the sub-path
              path: /uv-python/health
              port: 8080
---
apiVersion: v1
kind: Service
metadata:
  name: uv-oasis
spec:
  selector:
    app: uv-oasis
  ports:
    - port: 80
      targetPort: 8080
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: uv-oasis
spec:
  rules:
    - host: mirror.company.internal
      http:
        paths:
          # Simple prefix match is all you need!
          - path: /uv-python
            pathType: Prefix
            backend:
              service:
                name: uv-oasis
                port:
                  number: 80
```

## Environment Variables

| Variable              | Default                 | Description                                                                                                                                                                                                                                |
| --------------------- | ----------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `BASE_URL`            | `http://localhost:8080` | Base URL used in the JSON index. Set this to the URL that clients will use to reach the mirror.                                                                                                                                            |
| `PROXY_REWRITES_PATH` | `false`                 | Set to `true` if your external Reverse Proxy / Ingress automatically strips the sub-path (e.g., using `rewrite-target`). This tells the internal Nginx to serve files at the root `/` while still keeping the sub-path in the JSON output. |

### Client-side

> **Note:** This feature requires **uv >= 0.9.10** (support for HTTP/HTTPS URLs was introduced in 0.9.10).

| Variable                       | Description                                                                  |
| ------------------------------ | ---------------------------------------------------------------------------- |
| `UV_PYTHON_DOWNLOADS_JSON_URL` | Set to `http://<mirror-host>:8080/download-metadata.json` to use the mirror. |

## Architecture

```
┌──────────────────────────────────────────────────┐
│  Docker Image (nginx:alpine)                     │
│                                                  │
│  /download-metadata.json ← JSON index            │
│  /assets/*.tar.gz      ← Python tarballs         │
│  /health               ← Health check endpoint   │
│                                                  │
│  entrypoint.sh: replaces {{BASE_URL}} at startup │
└──────────────────────────────────────────────────┘

Client (uv):
  UV_PYTHON_DOWNLOADS_JSON_URL=http://mirror:8080/download-metadata.json
  → uv reads JSON → downloads tar.gz from same server
```

## Building from Source

```bash
# Install dependencies
uv sync

# Preview what will be downloaded
uv run python build.py --dry-run

# Build (download tarballs + generate JSON)
uv run python build.py --output ./dist

# Build Docker image
docker build -f docker/Dockerfile -t uv-oasis:latest .
```

## API Endpoints

| Endpoint                  | Method | Description                                               |
| ------------------------- | ------ | --------------------------------------------------------- |
| `/download-metadata.json` | GET    | JSON index compatible with `UV_PYTHON_DOWNLOADS_JSON_URL` |
| `/assets/{filename}`      | GET    | Python standalone build tarballs                          |
| `/health`                 | GET    | Returns `200 ok` for health checks                        |

## License & Credits

This project downloads and redistributes binaries from:

- **[python-build-standalone](https://github.com/astral-sh/python-build-standalone)** by [Astral](https://astral.sh/) — Licensed under the [Python Software Foundation License](https://docs.python.org/3/license.html).
- **[uv](https://github.com/astral-sh/uv)** by [Astral](https://astral.sh/) — The JSON metadata format is derived from uv's `download-metadata.json`.

This project itself is licensed under the MIT License. See [LICENSE](LICENSE) for details.
