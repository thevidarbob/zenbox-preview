# ZenBox — Omarchy app

Local inbox + Today Kanban. Fake demo data, one-off add, no Gmail/Supabase/OpenRouter yet.

## Install on the Omarchy machine

```bash
curl -fsSL -o zenbox-omarchy.tar.gz \
  https://github.com/thevidarbob/zenbox-preview/releases/latest/download/zenbox-omarchy.tar.gz
tar -xzf zenbox-omarchy.tar.gz
cd zenbox
chmod +x install.sh
./install.sh
hyprctl reload
zenbox
```

Or copy this `zenbox/` folder over (USB, scp) and run `./install.sh` from it.

Install writes only `~/.config/` and `~/.local/`. It never touches `~/.local/share/omarchy/`.

| Key | What |
|-----|------|
| `Super+Shift+Z` | Summon (floats 420px on the right) |
| `Super+Shift+Alt+Z` | Quick add |
| `Super+Space` | Walker → ZenBox |

Needs Python 3 (stdlib only) and Chromium (or `omarchy-launch-or-focus-webapp`).

## Try it

1. Inbox is a stack. `j` `k` move. **→** Today, **←** Later. **Ctrl+→** / **Ctrl+←** also start the agent.
2. `t` or the Today tab is the Kanban. On the board, **arrows navigate**. `1`–`6` move a card. Drag to reorder.
3. `w` expands the window in the browser preview. On the real 420px float, stay in the quadrant (Hyprland owns the size).
4. `n` adds. On Today it drops in the leftmost column. Anywhere else, Inbox.
5. `Enter` opens the card: notepad always visible (private), Needs you, agent feed, Escalate.

Captures persist in the browser profile (`localStorage`). The local server is only there to serve the app at `http://127.0.0.1:8765`.

## Keys

| Chord | Where | Action |
|-------|--------|--------|
| `→` / `←` | Inbox / Later | Park Today / Later |
| `Ctrl+→` / `Ctrl+←` | anywhere | Park + start agent |
| arrows / `j` `k` | Today board | Move focus |
| `n` | Today | Add under Today |
| `n` | Inbox / Later | Add to Inbox |
| `n` | open card | Focus notepad |
| `Enter` | | Open card |
| `i` `t` `b` | | Inbox / Today / Later |
| `w` | | Wide (browser preview) |
| `e` | | Escalate stub |
| `1`–`6` | Today | Jump column |

## Without install

```bash
cd zenbox
python3 zenbox-server.py
# http://127.0.0.1:8765          browser preview (fake desktop)
# http://127.0.0.1:8765/?native=1  app chrome only
```

## Not wired yet

Gmail, Supabase, OpenRouter, VOS/Granola, thermal print. Agent feed and Needs-you are the slots those will fill.
