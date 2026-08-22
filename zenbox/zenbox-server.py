#!/usr/bin/env python3
"""ZenBox local API + static server. Stdlib only."""
from __future__ import annotations

import json
import os
import re
import sqlite3
import threading
import time
import uuid
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
WEB = ROOT / "web"
DATA_DIR = Path(os.environ.get("ZENBOX_DATA", Path.home() / ".local/share/zenbox"))
DB_PATH = DATA_DIR / "zenbox.db"
PORT = int(os.environ.get("ZENBOX_PORT", "8765"))
HOST = os.environ.get("ZENBOX_HOST", "127.0.0.1")

COLS = ["inbox_day", "agent_working", "needs_you", "waiting", "review", "done"]

SEED = [
    {
        "title": "Reply to Mansal about relaunch copy",
        "why_now": "He asked for sign-off by Friday",
        "summary": "Thread on relaunch email. Mansal wants OK on subject line and hero.",
        "source": "mail",
        "people": "Mansal",
        "urgency": "urgent",
        "priority": "P0",
        "lane": "inbound",
        "notepad": "Don't promise Friday if deck slips.",
        "feed": [{"who": "openrouter", "t": "Drafted a short yes + one tweak."}],
        "recs": ["Draft a short yes + one tweak", "Open full thread in Mail"],
        "request": {
            "q": "Ship copy Friday or Monday?",
            "opts": ["Friday", "Monday", "Need a call"],
        },
    },
    {
        "title": "Confirm Rosy kickoff deck owner",
        "why_now": "Due today · VOS",
        "summary": "Task assigned from kickoff. Confirm who owns slides before standup.",
        "source": "vos",
        "people": "Scott",
        "urgency": "normal",
        "priority": "P1",
        "lane": "inbound",
        "recs": ["Propose outline from Aug 20 notes", "List open questions for Mary"],
    },
    {
        "title": "Send Ian the carnivore SKUs you promised",
        "why_now": "From Tuesday call · Granola",
        "summary": "You said you'd send the SKU list after the design sync.",
        "source": "granola",
        "people": "Ian",
        "urgency": "normal",
        "priority": "P1",
        "lane": "inbound",
        "recs": ["Pull SKUs from last sheet", "Draft Slack message"],
        "request": {
            "q": "Which SKU sheet?",
            "opts": ["Last week Google sheet", "Ian Slack file", "I'll attach"],
        },
    },
    {
        "title": "FYI: warehouse inventory digest",
        "why_now": "CC only · no ask",
        "summary": "Weekly digest. No action detected.",
        "source": "mail",
        "people": "ops@",
        "urgency": "low",
        "priority": "P2",
        "lane": "inbound",
    },
    {
        "title": "Twilio BAA wording for Mo",
        "why_now": "Waiting on counsel",
        "summary": "Parked in Waiting so you can see the Today board.",
        "source": "slack",
        "people": "Mo",
        "urgency": "urgent",
        "priority": "P0",
        "lane": "today",
        "kanban_column": "waiting",
        "notepad": "Indemnity clause is the only open.",
        "feed": [{"who": "you", "t": "Parked until Scott replies."}],
        "recs": ["Ping Scott Friday if still quiet"],
    },
    {
        "title": "Rosy kickoff — slides in motion",
        "why_now": "Already on Today · demo",
        "summary": "Example Working card so the Kanban isn't empty.",
        "source": "vos",
        "people": "Scott",
        "urgency": "normal",
        "priority": "P1",
        "lane": "today",
        "kanban_column": "agent_working",
        "feed": [{"who": "openrouter", "t": "Moved to Working. Pulling Aug 20 notes."}],
    },
    {
        "title": "Write Q3 inventory note for warehouse",
        "why_now": "Parked last week",
        "summary": "Later backlog example. Ctrl+→ promotes it to Today.",
        "source": "manual",
        "people": "you",
        "urgency": "low",
        "priority": "P2",
        "lane": "later",
    },
]


def now() -> float:
    return time.time()


def connect() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    return con


def ensure_columns(con: sqlite3.Connection) -> None:
    cols = {r[1] for r in con.execute("pragma table_info(items)")}
    if "summary" not in cols:
        con.execute("alter table items add column summary text default ''")
    if "recs_json" not in cols:
        con.execute("alter table items add column recs_json text default '[]'")


def seed_items(con: sqlite3.Connection) -> None:
    for i, row in enumerate(SEED):
        t = now() - i * 90
        con.execute(
            """insert into items
            (id,title,why_now,summary,source,people,urgency,priority,lane,kanban_column,
             kanban_order,notepad,feed_json,request_json,recs_json,created_at,last_activity_at)
            values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                str(i + 1),
                row["title"],
                row.get("why_now", ""),
                row.get("summary", ""),
                row.get("source", "manual"),
                row.get("people", ""),
                row.get("urgency", "normal"),
                row.get("priority", "P1"),
                row.get("lane", "inbound"),
                row.get("kanban_column"),
                float(i),
                row.get("notepad", ""),
                json.dumps(row.get("feed", [])),
                json.dumps(row["request"]) if row.get("request") else None,
                json.dumps(row.get("recs", [])),
                t,
                t,
            ),
        )


def init_db() -> None:
    con = connect()
    con.executescript(
        """
        create table if not exists items (
          id text primary key,
          title text not null,
          why_now text default '',
          summary text default '',
          source text default 'manual',
          people text default '',
          urgency text default 'unsorted',
          priority text default 'P1',
          lane text default 'inbound',
          kanban_column text,
          kanban_order real default 0,
          notepad text default '',
          feed_json text default '[]',
          request_json text,
          recs_json text default '[]',
          created_at real not null,
          last_activity_at real not null
        );
        """
    )
    ensure_columns(con)
    n = con.execute("select count(*) from items").fetchone()[0]
    if n == 0:
        seed_items(con)
    con.commit()
    con.close()


def reset_demo() -> list[dict]:
    con = connect()
    con.execute("delete from items")
    seed_items(con)
    con.commit()
    con.close()
    return [it for it in list_items() if it["lane"] != "dropped"]


def item_to_dict(row: sqlite3.Row, include_notepad: bool = True) -> dict:
    d = dict(row)
    d["feed"] = json.loads(d.pop("feed_json") or "[]")
    raw_req = d.pop("request_json")
    d["request"] = json.loads(raw_req) if raw_req else None
    d["recs"] = json.loads(d.pop("recs_json") or "[]")
    if not include_notepad:
        d.pop("notepad", None)
    return d


def list_items() -> list[dict]:
    con = connect()
    rows = con.execute(
        "select * from items order by last_activity_at desc"
    ).fetchall()
    con.close()
    return [item_to_dict(r) for r in rows]


def get_item(item_id: str) -> dict | None:
    con = connect()
    row = con.execute("select * from items where id=?", (item_id,)).fetchone()
    con.close()
    return item_to_dict(row) if row else None


def create_item(body: dict) -> dict:
    item_id = uuid.uuid4().hex[:10]
    t = now()
    con = connect()
    con.execute(
        """insert into items
        (id,title,why_now,summary,source,people,urgency,priority,lane,kanban_column,
         kanban_order,notepad,feed_json,request_json,recs_json,created_at,last_activity_at)
        values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            item_id,
            body.get("title") or "Untitled",
            body.get("why_now") or "Captured just now",
            body.get("summary") or body.get("why_now") or "Captured just now",
            body.get("source") or "manual",
            body.get("people") or "you",
            "unsorted",
            body.get("priority") or "P1",
            "inbound",
            None,
            0,
            "",
            json.dumps([]),
            None,
            json.dumps(["Local capture. Agents plug in later."]),
            t,
            t,
        ),
    )
    con.commit()
    con.close()
    return get_item(item_id)  # type: ignore[return-value]


def update_item(item_id: str, body: dict) -> dict | None:
    cur = get_item(item_id)
    if not cur:
        return None
    lane = body.get("lane", cur["lane"])
    col = body.get("kanban_column", cur["kanban_column"])
    if lane == "today" and not col:
        col = "inbox_day"
    if lane != "today":
        col = None
    feed = cur["feed"]
    if body.get("feed_append"):
        feed = feed + [body["feed_append"]]
    notepad = cur["notepad"]
    if "notepad" in body:
        notepad = body["notepad"]
    request = cur["request"]
    if "request" in body:
        request = body["request"]
    con = connect()
    con.execute(
        """update items set title=?, why_now=?, source=?, people=?, urgency=?,
           priority=?, lane=?, kanban_column=?, notepad=?, feed_json=?,
           request_json=?, last_activity_at=? where id=?""",
        (
            body.get("title", cur["title"]),
            body.get("why_now", cur["why_now"]),
            body.get("source", cur["source"]),
            body.get("people", cur["people"]),
            body.get("urgency", cur["urgency"]),
            body.get("priority", cur["priority"]),
            lane,
            col,
            notepad,
            json.dumps(feed),
            json.dumps(request) if request else None,
            now(),
            item_id,
        ),
    )
    con.commit()
    con.close()
    return get_item(item_id)


def classify_async(item_id: str) -> None:
    """Local stub until OpenRouter is wired. Marks urgency after a beat."""

    def run() -> None:
        time.sleep(0.7)
        it = get_item(item_id)
        if not it or it["urgency"] != "unsorted":
            return
        title = it["title"].lower()
        if any(w in title for w in ("urgent", "asap", "unblock", "rsvp")):
            urg, pri = "urgent", "P0"
        elif any(w in title for w in ("newsletter", "digest", "fyi")):
            urg, pri = "low", "P2"
        else:
            urg, pri = "normal", "P1"
        update_item(
            item_id,
            {
                "urgency": urg,
                "priority": pri,
                "feed_append": {
                    "who": "openrouter",
                    "t": f"Classified {pri} / {urg} (local stub).",
                },
            },
        )

    threading.Thread(target=run, daemon=True).start()


THEME_PATHS = [
    Path.home() / ".config/omarchy/current/theme/colors.toml",
    Path.home() / ".local/state/omarchy/current/theme/colors.toml",
    Path.home() / ".config/omarchy/current/theme/alacritty.toml",
]


def theme_name() -> str:
    for path in (
        Path.home() / ".config/omarchy/current/theme",
        Path.home() / ".local/state/omarchy/current/theme",
    ):
        if path.exists():
            try:
                return path.resolve().name
            except OSError:
                return path.name
    return "tokyo-night"


def read_omarchy_theme() -> dict:
    colors: dict[str, str] = {
        "accent": "#7aa2f7",
        "selection": "#292e42",
        "muted": "#414868",
        "background": "#1a1b26",
        "dark_background": "#13141c",
        "darker_background": "#0e0e14",
        "lighter_background": "#24283b",
        "foreground": "#a9b1d6",
        "dark_foreground": "#565f89",
        "bright_foreground": "#c0caf5",
        "red": "#f7768e",
        "yellow": "#e0af68",
        "green": "#9ece6a",
        "cyan": "#449dab",
        "magenta": "#ad8ee6",
        "source": "fallback-tokyo-night",
        "name": "tokyo-night",
    }
    parsed: dict[str, str] = {}
    source = None
    for path in THEME_PATHS:
        if not path.exists():
            continue
        text = path.read_text(errors="ignore")
        for m in re.finditer(r'^([A-Za-z0-9_]+)\s*=\s*"([^"]+)"', text, re.M):
            parsed[m.group(1)] = m.group(2)
        source = str(path)
        break
    if parsed:
        alias = {
            "accent": "accent",
            "background": "background",
            "foreground": "foreground",
            "cursor": "bright_foreground",
            "color0": "muted",
            "color1": "red",
            "color2": "green",
            "color3": "yellow",
            "color5": "magenta",
            "color6": "cyan",
            "color8": "dark_foreground",
            "selection_background": "selection",
        }
        for src, dest in alias.items():
            if src in parsed:
                colors[dest] = parsed[src]
        if "background" in parsed:
            colors["dark_background"] = parsed["background"]
        colors.update({k: v for k, v in parsed.items() if k.startswith("color")})
    if source:
        colors["source"] = source
    colors["name"] = theme_name()
    return colors


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB), **kwargs)

    def log_message(self, fmt: str, *args) -> None:
        print(f"[zenbox] {self.address_string()} {fmt % args}")

    def _json(self, code: int, payload) -> None:
        data = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def _read_json(self) -> dict:
        n = int(self.headers.get("Content-Length") or 0)
        if not n:
            return {}
        return json.loads(self.rfile.read(n).decode() or "{}")

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path == "/api/health":
            return self._json(200, {"ok": True})
        if path == "/api/theme":
            theme = read_omarchy_theme()
            return self._json(200, theme)
        if path == "/api/items":
            return self._json(200, [it for it in list_items() if it["lane"] != "dropped"])
        if path.startswith("/api/items/"):
            item = get_item(path.split("/")[-1])
            return self._json(200, item) if item else self._json(404, {"error": "missing"})
        if path == "/":
            self.path = "/index.html"
        return super().do_GET()

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        body = self._read_json()
        if path == "/api/reset":
            return self._json(200, reset_demo())
        if path == "/api/items":
            item = create_item(body)
            classify_async(item["id"])
            return self._json(201, item)
        m = re.match(r"^/api/items/([^/]+)/lane$", path)
        if m:
            item = update_item(
                m.group(1),
                {
                    "lane": body.get("lane"),
                    "kanban_column": body.get("kanban_column"),
                    "feed_append": {
                        "who": "system",
                        "t": f"Moved to {body.get('lane')}.",
                    },
                },
            )
            if item and body.get("lane") == "today":
                update_item(
                    item["id"],
                    {
                        "feed_append": {
                            "who": "openrouter",
                            "t": "Today prep started (local stub).",
                        }
                    },
                )
                item = get_item(item["id"])
            return self._json(200, item) if item else self._json(404, {"error": "missing"})
        m = re.match(r"^/api/items/([^/]+)/answer$", path)
        if m:
            item = get_item(m.group(1))
            if not item:
                return self._json(404, {"error": "missing"})
            ans = body.get("answer") or ""
            item = update_item(
                m.group(1),
                {
                    "request": None,
                    "kanban_column": "agent_working",
                    "lane": "today",
                    "feed_append": {"who": "you", "t": f"Answered: {ans}"},
                },
            )
            return self._json(200, item)
        m = re.match(r"^/api/items/([^/]+)/comment$", path)
        if m:
            item = update_item(
                m.group(1),
                {"feed_append": {"who": body.get("who") or "you", "t": body.get("body") or ""}},
            )
            return self._json(200, item) if item else self._json(404, {"error": "missing"})
        return self._json(404, {"error": "nope"})

    def do_PATCH(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        body = self._read_json()
        m = re.match(r"^/api/items/([^/]+)$", path)
        if not m:
            return self._json(404, {"error": "nope"})
        item = update_item(m.group(1), body)
        return self._json(200, item) if item else self._json(404, {"error": "missing"})

    def do_DELETE(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        m = re.match(r"^/api/items/([^/]+)$", path)
        if not m:
            return self._json(404, {"error": "nope"})
        item = update_item(m.group(1), {"lane": "dropped"})
        return self._json(200, item) if item else self._json(404, {"error": "missing"})


def main() -> None:
    init_db()
    httpd = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"ZenBox http://{HOST}:{PORT}  db={DB_PATH}")
    httpd.serve_forever()


if __name__ == "__main__":
    main()
