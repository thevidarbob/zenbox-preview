# $1 is the new theme name. ZenBox re-reads colors.toml on its next poll.
curl -sf "http://127.0.0.1:${ZENBOX_PORT:-8765}/api/theme" >/dev/null || true
