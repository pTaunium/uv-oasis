#!/bin/sh
set -e

BASE_URL="${BASE_URL:-http://localhost:8080}"
# Remove trailing slash if present to prevent double slashes in URLs
BASE_URL="${BASE_URL%/}"

# If the external reverse proxy already rewrites the path (e.g., nginx rewrite-target),
# force Nginx inside the container to serve at the root path (/).
if [ "${PROXY_REWRITES_PATH:-false}" = "true" ]; then
    export URL_PREFIX=""
else
    # Extract path prefix from BASE_URL (e.g., https://example.com/uv-python -> /uv-python)
    export URL_PREFIX=$(echo "$BASE_URL" | sed -E 's|^https?://[^/]+||')
fi

# We rely on nginx's native /docker-entrypoint.sh to process /etc/nginx/templates/*.template
# which will automatically pick up URL_PREFIX and generate /etc/nginx/conf.d/default.conf

sed "s|{{BASE_URL}}|${BASE_URL}|g" \
    /usr/share/nginx/html/download-metadata.json.template \
    > /usr/share/nginx/html/download-metadata.json

echo "=== uv-oasis ==="
echo "BASE_URL: ${BASE_URL}"
echo "JSON endpoint: ${BASE_URL}/download-metadata.json"
echo "================"

exec /docker-entrypoint.sh nginx -g 'daemon off;'
