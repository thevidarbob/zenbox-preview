#!/usr/bin/env bash
# Install ZenBox into the current user's Omarchy/XDG locations.
# Safe to re-run. Never writes to ~/.local/share/omarchy/.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APPDIR="${HOME}/.local/share/zenbox/app"
DATADIR="${HOME}/.local/share/zenbox"
BINDIR="${HOME}/.local/bin"
APP_MENU="${HOME}/.local/share/applications"
ICON_DIR="${HOME}/.local/share/icons/hicolor/scalable/apps"
UNIT_DIR="${HOME}/.config/systemd/user"
HYPR="${HOME}/.config/hypr"
HOOK="${HOME}/.config/omarchy/hooks/theme-set"
MARKER="# zenbox-theme-set"

echo "ZenBox → ${APPDIR}"
mkdir -p "${APPDIR}" "${DATADIR}" "${BINDIR}" "${APP_MENU}" "${ICON_DIR}" "${UNIT_DIR}"

if command -v rsync >/dev/null; then
  rsync -a --delete \
    --exclude '.git' \
    --exclude 'data' \
    --exclude '__pycache__' \
    "${ROOT}/" "${APPDIR}/"
else
  rm -rf "${APPDIR}"
  mkdir -p "${APPDIR}"
  cp -a "${ROOT}/." "${APPDIR}/"
  rm -rf "${APPDIR}/.git" "${APPDIR}/data" "${APPDIR}/__pycache__"
fi

chmod +x "${APPDIR}/omarchy/zenbox" "${APPDIR}/install.sh"
ln -sfn "${APPDIR}/omarchy/zenbox" "${BINDIR}/zenbox"

cp "${APPDIR}/omarchy/zenbox.desktop" "${APP_MENU}/ZenBox.desktop"
sed -i "s|^Exec=.*|Exec=${BINDIR}/zenbox|" "${APP_MENU}/ZenBox.desktop"
cp "${APPDIR}/omarchy/zenbox.svg" "${ICON_DIR}/zenbox.svg"
if command -v update-desktop-database >/dev/null; then
  update-desktop-database "${APP_MENU}" >/dev/null 2>&1 || true
fi

cp "${APPDIR}/omarchy/zenbox.service" "${UNIT_DIR}/zenbox.service"
if command -v systemctl >/dev/null; then
  systemctl --user daemon-reload || true
  systemctl --user enable --now zenbox.service || true
fi

if [[ -f "${HYPR}/hyprland.lua" ]]; then
  mkdir -p "${HYPR}"
  cp "${APPDIR}/omarchy/zenbox.lua" "${HYPR}/zenbox.lua"
  mkdir -p "${HYPR}/hypr"
  cp "${APPDIR}/omarchy/zenbox.lua" "${HYPR}/hypr/zenbox.lua"
  if ! grep -q 'require("hypr.zenbox")' "${HYPR}/hyprland.lua"; then
    printf '\nrequire("hypr.zenbox")\n' >>"${HYPR}/hyprland.lua"
    echo "Appended require(\"hypr.zenbox\") to ~/.config/hypr/hyprland.lua"
  fi
elif [[ -f "${HYPR}/hyprland.conf" || -f "${HYPR}/bindings.conf" ]]; then
  mkdir -p "${HYPR}"
  cp "${APPDIR}/omarchy/zenbox.conf" "${HYPR}/zenbox.conf"
  CONF="${HYPR}/hyprland.conf"
  if [[ -f "${CONF}" ]] && ! grep -q 'hypr/zenbox.conf' "${CONF}"; then
    printf '\nsource = %s\n' "${HYPR}/zenbox.conf" >>"${CONF}"
    echo "Sourced ~/.config/hypr/zenbox.conf from hyprland.conf"
  fi
else
  mkdir -p "${HYPR}"
  cp "${APPDIR}/omarchy/zenbox.lua" "${HYPR}/zenbox.lua"
  cp "${APPDIR}/omarchy/zenbox.conf" "${HYPR}/zenbox.conf"
  echo "No Hyprland config yet — copied both Lua and .conf drop-ins."
fi

mkdir -p "$(dirname "${HOOK}")"
if [[ ! -f "${HOOK}" ]]; then
  printf '#!/usr/bin/env bash\nTHEME_NAME=${1:-}\n' >"${HOOK}"
  chmod +x "${HOOK}"
fi
if ! grep -q "${MARKER}" "${HOOK}"; then
  {
    echo ""
    echo "${MARKER}"
    cat "${APPDIR}/omarchy/theme-set-hook.sh"
  } >>"${HOOK}"
  chmod +x "${HOOK}"
  echo "Hooked theme-set so ZenBox picks up Omarchy colors."
fi

if ! command -v zenbox >/dev/null; then
  echo "Note: ${BINDIR} is not on PATH. Add it, or call ${BINDIR}/zenbox directly."
fi

echo
echo "Installed."
echo "  Super+Shift+Z  summon ZenBox (right quadrant)"
echo "  Super+Space    Walker → ZenBox"
echo "  Super+Shift+Alt+Z  quick add"
echo
echo "If Hyprland is running: hyprctl reload"
echo "Open now: zenbox"
echo "Data: ${DATADIR}/zenbox.db"
