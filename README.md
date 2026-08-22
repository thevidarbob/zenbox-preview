# ZenBox preview

Omarchy inbox + Today Kanban demo.

## Open in the browser

https://htmlpreview.github.io/?https://raw.githubusercontent.com/thevidarbob/zenbox-preview/main/zenbox.html

## Install on an Omarchy machine

```bash
curl -fsSL -o zenbox-src.tar.gz https://github.com/thevidarbob/zenbox-preview/archive/refs/heads/main.tar.gz
tar -xzf zenbox-src.tar.gz
cd zenbox-preview-main/zenbox
chmod +x install.sh
./install.sh
hyprctl reload
zenbox
```

Then `Super+Shift+Z` summons it (420px right float). `n` adds a task. Python 3 + Chromium.

See `zenbox/README.md` for keys.
