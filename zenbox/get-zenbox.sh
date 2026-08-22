#!/usr/bin/env bash
# One-shot install + launch for Omarchy. Run on the laptop:
#   curl -fsSL https://raw.githubusercontent.com/thevidarbob/zenbox-preview/main/zenbox/get-zenbox.sh | bash
set -euo pipefail

if ! command -v python3 >/dev/null; then
  echo "Need python3. On Omarchy: sudo pacman -S python" >&2
  exit 1
fi
if ! command -v curl >/dev/null; then
  echo "Need curl." >&2
  exit 1
fi

TMP="$(mktemp -d)"
trap 'rm -rf "${TMP}"' EXIT
cd "${TMP}"
echo "Downloading ZenBox…"
curl -fsSL https://github.com/thevidarbob/zenbox-preview/archive/refs/heads/main.tar.gz | tar -xz
cd zenbox-preview-main/zenbox
chmod +x install.sh omarchy/zenbox
./install.sh
export PATH="${HOME}/.local/bin:${PATH}"
if command -v hyprctl >/dev/null; then
  hyprctl reload >/dev/null 2>&1 || true
fi
echo
echo "Launching…  After this, Super+Shift+Z summons it."
exec "${HOME}/.local/bin/zenbox"
