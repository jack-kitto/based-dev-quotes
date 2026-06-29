#!/usr/bin/env python3
"""
based-dev-quotes: Telegram Submission Bot

A simple Telegram bot that lets anyone submit quotes.
Submissions are queued and periodically opened as PRs.

Commands:
  /submit <quote> — <author>   Submit a quote
  /random                       Get a random quote
  /today                        Get today's quote
  /stats                        Show dataset stats
  /help                         Show help

Setup:
  1. Create a bot via @BotFather on Telegram
  2. Set TELEGRAM_BOT_TOKEN env var
  3. Set GITHUB_TOKEN env var (for PR creation)
  4. Run: python3 scripts/telegram_bot.py

Submissions are saved to quotes/submissions.json and batched into PRs.
"""

import json
import os
import re
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent.parent
QUOTES_PATH = ROOT / "quotes" / "quotes.json"
SUBMISSIONS_PATH = ROOT / "quotes" / "submissions.json"

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
REPO_OWNER = "jack-kitto"
REPO_NAME = "based-dev-quotes"
API_BASE = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

HELP_TEXT = """🧠 *based\\-dev\\-quotes* — Submit quotes\\!

*Commands:*
`/submit <quote> — <author>` Submit a quote
`/submit <quote>` Submit \\(author: Unknown\\)
`/random` Get a random quote
`/today` Get today's quote
`/stats` Dataset stats
`/help` This message

*Example:*
`/submit Weeks of coding can save you hours of planning. — Unknown`

*What we're looking for:*
✅ Grug\\-brained wisdom, indie hacker truth, funny dev observations
❌ LinkedIn motivational garbage, AI\\-generated slop
"""


def tg_request(method: str, data: dict = None) -> dict | None:
    """Make a Telegram Bot API request."""
    url = f"{API_BASE}/{method}"
    if data:
        payload = json.dumps(data).encode()
        req = urllib.request.Request(url, data=payload, method="POST")
        req.add_header("Content-Type", "application/json")
    else:
        req = urllib.request.Request(url)

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())
    except (urllib.error.URLError, urllib.error.HTTPError) as e:
        print(f"TG API error: {e}", file=sys.stderr)
        return None


def send_message(chat_id: int, text: str, parse_mode: str = "MarkdownV2"):
    """Send a message to a Telegram chat."""
    tg_request("sendMessage", {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode
    })


def load_quotes() -> list[dict]:
    with open(QUOTES_PATH, encoding="utf-8") as f:
        return json.load(f)


def load_submissions() -> list[dict]:
    if SUBMISSIONS_PATH.exists():
        with open(SUBMISSIONS_PATH, encoding="utf-8") as f:
            return json.load(f)
    return []


def save_submissions(subs: list[dict]):
    with open(SUBMISSIONS_PATH, "w", encoding="utf-8") as f:
        json.dump(subs, f, indent=2, ensure_ascii=False)
        f.write("\n")


def escape_md(text: str) -> str:
    """Escape MarkdownV2 special characters."""
    special = r'_*[]()~`>#+-=|{}.!'
    return re.sub(f'([{re.escape(special)}])', r'\\\1', text)


def handle_submit(chat_id: int, text: str, username: str):
    """Handle a /submit command."""
    # Parse: /submit <quote> — <author>
    text = text.strip()
    if not text:
        send_message(chat_id, "Usage: `/submit <quote> — <author>`")
        return

    # Split on em dash or double hyphen
    parts = re.split(r'\s*[—–]\s*|\s*--\s*', text, maxsplit=1)
    quote_text = parts[0].strip().strip('"\'""''')
    author = parts[1].strip() if len(parts) > 1 else "Unknown"

    if len(quote_text) < 10:
        send_message(chat_id, "Quote too short\\! Give us something meatier\\. 🥩")
        return

    if len(quote_text) > 500:
        send_message(chat_id, "Quote too long\\! Keep it punchy\\. ✂️")
        return

    # Save submission
    submission = {
        "text": quote_text,
        "author": author,
        "submitted_by": f"@{username}" if username else "anonymous",
        "submitted_at": datetime.now(timezone.utc).isoformat(),
        "chat_id": chat_id,
        "status": "pending"
    }

    subs = load_submissions()
    subs.append(submission)
    save_submissions(subs)

    escaped_quote = escape_md(quote_text)
    escaped_author = escape_md(author)
    pending = len([s for s in subs if s["status"] == "pending"])

    send_message(
        chat_id,
        f"✅ Quote submitted\\!\n\n"
        f"_{escaped_quote}_\n"
        f"  — {escaped_author}\n\n"
        f"📋 {pending} quotes pending review"
    )


def handle_random(chat_id: int):
    """Send a random quote."""
    import random
    quotes = load_quotes()
    q = random.choice(quotes)
    text = escape_md(q["text"])
    author = escape_md(q["author"])
    cats = escape_md(", ".join(q.get("categories", [])))
    grug = "🪨" * q.get("grug_level", 1)

    send_message(
        chat_id,
        f"🎲 *Random Quote*\n\n"
        f"_{text}_\n"
        f"  — {author}\n\n"
        f"\\[{cats}\\] {grug}"
    )


def handle_today(chat_id: int):
    """Send today's quote."""
    import hashlib
    quotes = load_quotes()
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    idx = int(hashlib.sha256(today.encode()).hexdigest()[:8], 16) % len(quotes)
    q = quotes[idx]

    text = escape_md(q["text"])
    author = escape_md(q["author"])
    cats = escape_md(", ".join(q.get("categories", [])))

    send_message(
        chat_id,
        f"🌅 *Quote of the Day*\n\n"
        f"_{text}_\n"
        f"  — {author}\n\n"
        f"\\[{cats}\\]"
    )


def handle_stats(chat_id: int):
    """Send dataset stats."""
    quotes = load_quotes()
    subs = load_submissions()
    pending = len([s for s in subs if s["status"] == "pending"])

    authors = len(set(q["author_slug"] for q in quotes))
    categories = len(set(c for q in quotes for c in q.get("categories", [])))

    send_message(
        chat_id,
        f"📊 *based\\-dev\\-quotes Stats*\n\n"
        f"📝 {len(quotes)} quotes\n"
        f"👤 {authors} authors\n"
        f"📂 {categories} categories\n"
        f"📋 {pending} pending submissions"
    )


def handle_update(update: dict):
    """Process a single Telegram update."""
    msg = update.get("message", {})
    text = msg.get("text", "")
    chat_id = msg.get("chat", {}).get("id")
    username = msg.get("from", {}).get("username", "")

    if not chat_id or not text:
        return

    if text.startswith("/submit"):
        handle_submit(chat_id, text[7:].strip(), username)
    elif text.startswith("/random"):
        handle_random(chat_id)
    elif text.startswith("/today"):
        handle_today(chat_id)
    elif text.startswith("/stats"):
        handle_stats(chat_id)
    elif text.startswith("/help") or text.startswith("/start"):
        send_message(chat_id, HELP_TEXT)


def main():
    if not TELEGRAM_TOKEN:
        print("❌ Set TELEGRAM_BOT_TOKEN env var", file=sys.stderr)
        sys.exit(1)

    print("🤖 based-dev-quotes bot starting...", file=sys.stderr)

    # Get bot info
    me = tg_request("getMe")
    if me and me.get("ok"):
        bot_name = me["result"].get("username", "unknown")
        print(f"   Bot: @{bot_name}", file=sys.stderr)

    offset = 0
    while True:
        updates = tg_request("getUpdates", {
            "offset": offset,
            "timeout": 30,
            "allowed_updates": ["message"]
        })

        if updates and updates.get("ok"):
            for update in updates["result"]:
                offset = update["update_id"] + 1
                try:
                    handle_update(update)
                except Exception as e:
                    print(f"Error handling update: {e}", file=sys.stderr)

        time.sleep(1)


if __name__ == "__main__":
    main()
