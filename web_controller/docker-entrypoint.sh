set -eu

TEMPLATE="/usr/share/nginx/html/env.template.js"
OUT="/usr/share/nginx/html/env.js"
if [ -f "$TEMPLATE" ]; then
  echo "[entrypoint] Generating env.js from template"
  envsubst '${VITE_DISCORD_CLIENT_ID} ${VITE_DISCORD_BOT_URL}' < "$TEMPLATE" > "$OUT"
else
  echo "[entrypoint] No env.template.js found, skipping"
fi

exec nginx -g 'daemon off;'
