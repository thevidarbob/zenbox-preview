# ZenBox — Omarchy app

Local inbox + Today Kanban. Fake demo data. Your adds persist. No Gmail yet.

## On the Omarchy laptop

1. Open a terminal (`Super+Enter` on stock Omarchy).
2. Paste this **one line** and press Enter:

```bash
curl -fsSL https://raw.githubusercontent.com/thevidarbob/zenbox-preview/main/zenbox/get-zenbox.sh | bash
```

3. Wait. A Chromium app window titled **Inbox** should open on the right.
4. After that, **`Super+Shift+Z`** summons it. **`n`** adds a task.

Needs `python3` and Chromium (both already on Omarchy). Writes only `~/.local/` and `~/.config/`.

### If the window never appears

```bash
export PATH="$HOME/.local/bin:$PATH"
python3 ~/.local/share/zenbox/app/zenbox-server.py &
chromium --app="http://127.0.0.1:8765/?native=1" --class=zenbox
```

### Even simpler — no install, just open the file

```bash
curl -fsSL -o ~/Downloads/zenbox.html https://raw.githubusercontent.com/thevidarbob/zenbox-preview/main/zenbox.html
chromium --app="file://$HOME/Downloads/zenbox.html?native=1"
```

That’s the same UI. No hotkey until you run the installer.

## Keys

| Chord | Where | Action |
|-------|--------|--------|
| `→` / `←` | Inbox / Later | Park Today / Later |
| `Ctrl+→` / `Ctrl+←` | anywhere | Park + start agent |
| arrows / `j` `k` | Today board | Move focus |
| `n` | Today | Add under Today |
| `n` | Inbox / Later | Add to Inbox |
| `Enter` | | Open card |
| `t` | | Today Kanban |
| `w` | browser | Wide preview |
| `1`–`6` | Today | Jump column |
| `Super+Shift+Z` | desktop | Summon (after install) |
