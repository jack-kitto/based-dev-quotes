# 🧠 based-dev-quotes

A free, static API of curated programming quotes for developers who've mass mass seen some things.

**No API key. No rate limits. No server. Just JSON on a CDN.**

> *"Weeks of coding can save you hours of planning."*
> — Programming folklore

---

## Quick Start

### Get today's quote

```bash
curl -s https://cdn.jsdelivr.net/gh/jack-kitto/based-dev-quotes@main/api/v1/today.json
```

```json
{
  "id": "knuth-premature-optimization",
  "text": "Premature optimization is the root of all evil.",
  "author": "Donald Knuth",
  "categories": ["wisdom", "complexity"],
  "grug_level": 3,
  "spiciness": 1
}
```

### JavaScript

```js
const quote = await fetch(
  'https://cdn.jsdelivr.net/gh/jack-kitto/based-dev-quotes@main/api/v1/today.json'
).then(r => r.json())

console.log(`${quote.text}\n  — ${quote.author}`)
```

### Python

```python
import httpx
quote = httpx.get("https://cdn.jsdelivr.net/gh/jack-kitto/based-dev-quotes@main/api/v1/today.json").json()
print(f'"{quote["text"]}"\n  — {quote["author"]}')
```

### Terminal MOTD (add to .bashrc / .zshrc)

```bash
# 💬 Dev quote of the day
curl -sf https://cdn.jsdelivr.net/gh/jack-kitto/based-dev-quotes@main/api/v1/today.json \
  | jq -r '"  💬 \"\(.text)\"\n    — \(.author)"' 2>/dev/null
```

---

## API Endpoints

All endpoints are static JSON files served via [jsDelivr CDN](https://www.jsdelivr.com/).

Base URL: `https://cdn.jsdelivr.net/gh/jack-kitto/based-dev-quotes@main/api/v1`

| Endpoint | Description |
|----------|-------------|
| [`/today.json`](api/v1/today.json) | Quote of the day (deterministic, same for everyone) |
| [`/random.json`](api/v1/random.json) | Random quote (rotated daily) |
| [`/random/{1-20}.json`](api/v1/random/) | Pre-shuffled random slots |
| [`/all.json`](api/v1/all.json) | Full dataset |
| [`/stats.json`](api/v1/stats.json) | Dataset statistics |
| [`/categories/index.json`](api/v1/categories/index.json) | List all categories |
| [`/categories/{slug}.json`](api/v1/categories/) | Quotes by category |
| [`/authors/index.json`](api/v1/authors/index.json) | List all authors |
| [`/authors/{slug}.json`](api/v1/authors/) | Quotes by author |
| [`/tags/index.json`](api/v1/tags/index.json) | List all tags |
| [`/tags/{slug}.json`](api/v1/tags/) | Quotes by tag |

### Client-side random

For true randomness, fetch `all.json` and pick client-side:

```js
const { quotes } = await fetch('.../all.json').then(r => r.json())
const random = quotes[Math.floor(Math.random() * quotes.length)]
```

Or pick a random slot (lighter, pseudo-random):

```js
const slot = Math.floor(Math.random() * 20) + 1
const quote = await fetch(`.../random/${slot}.json`).then(r => r.json())
```

---

## Categories

| Category | Vibe | Count |
|----------|------|-------|
| 🧠 `grug` | Anti-complexity, caveman wisdom | — |
| 🔥 `suffering` | Hard-won lessons from production | — |
| 🚀 `indie-hacker` | Building in public, shipping fast | — |
| 🐧 `unix` | Do one thing well | — |
| 🐛 `debugging` | The reality of the craft | — |
| 🏗️ `complexity` | Fighting entropy | — |
| 📦 `shipping` | Just deploy the damn thing | — |
| 💼 `career` | Real talk about the industry | — |
| 📜 `wisdom` | Timeless CS philosophy | — |
| 💩 `shitpost` | Chaotic dev humor | — |
| 🏴‍☠️ `founder` | Startup / bootstrapping truth | — |
| 🔧 `tools` | Editor wars, language debates | — |
| 😂 `funny` | Comedy, jokes, relatable humor | — |

---

## Quote Metadata

Every quote has two fun metadata fields:

### `grug_level` (1-5) 🧠

How grug-brained / anti-complexity is this quote?

| Level | Meaning |
|-------|---------|
| 1 | 🎓 Academic / theoretical |
| 2 | 🤔 Thoughtful but practical |
| 3 | ⚖️ Balanced |
| 4 | 🔨 Pragmatic, prefers simplicity |
| 5 | 🪨 Full grug — "just use a function" |

### `spiciness` (1-5) 🌶️

How controversial / hot-takey is this quote?

| Level | Meaning |
|-------|---------|
| 1 | ✅ Universally agreed |
| 2 | 😊 Mild take |
| 3 | 🤨 Warm take |
| 4 | 🔥 Hot take — will start a thread |
| 5 | ☢️ Thermonuclear — mass mass discourse |

---

## Use Cases

### 🖥️ Terminal MOTD
Every time you open a terminal, get a dev quote. See [cli/motd.sh](cli/motd.sh).

### 📝 GitHub README Badge
Show a rotating quote in your project README.

### 🤖 Slack / Discord Bot
Post a daily quote to your team's channel.

### 🧩 VS Code Extension
Show a quote on startup.

### 🐦 Twitter/X Bot
Auto-post daily quotes to dev Twitter.

### 🎲 CLI Tool
```bash
# One-liner: random quote in your terminal
bash <(curl -s https://raw.githubusercontent.com/jack-kitto/based-dev-quotes/main/cli/quote.sh)
```

---

## How It Works

This is a **static API** — there's no server. Here's the stack:

1. Quotes are curated in [`quotes/quotes.json`](quotes/quotes.json)
2. A [GitHub Action](.github/workflows/generate.yml) runs daily
3. It generates the API files in `api/v1/`
4. [jsDelivr](https://www.jsdelivr.com/) serves them as a free CDN
5. You `fetch()` a URL. That's it.

**Cost to run: $0.00/month. Forever.**

---

## Contributing

We need more quotes! Especially:
- Grug-brained wisdom
- Indie hacker / bootstrapper truth bombs
- Funny dev observations that hit different
- Obscure gems from old conference talks and mailing lists

**Not welcome:** LinkedIn motivational garbage, "code is art" platitudes, AI-generated slop.

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full guide.

---

## Automation

### 🤖 Auto-Scraping Pipeline

A weekly GitHub Action scrapes HN, Reddit, and dev communities, then uses an LLM to extract and score quotes. New quotes are opened as PRs for review.

**Setup:**
1. Add `OPENAI_API_KEY` to your repo's [Secrets](../../settings/secrets/actions)
2. Optionally set `OPENAI_BASE_URL` for custom LLM endpoints (OpenRouter, local, etc.)
3. Optionally set `QUOTE_MODEL` (default: `gpt-4o-mini`)
4. The Action runs every Monday at 6am UTC, or trigger manually via Actions tab

**Manual run:**
```bash
# Scrape → Extract → Open PR (full pipeline)
python3 scripts/scrape.py > /tmp/candidates.json
python3 scripts/extract.py --input /tmp/candidates.json > /tmp/new_quotes.json
python3 scripts/merge_pr.py --input /tmp/new_quotes.json

# Or auto-merge without PR
python3 scripts/merge_pr.py --input /tmp/new_quotes.json --auto-merge
```

### 🤖 Telegram Submission Bot

Let anyone submit quotes via Telegram. Submissions are queued and batched into PRs.

**Setup:**
1. Create a bot via [@BotFather](https://t.me/BotFather) on Telegram
2. Set `TELEGRAM_BOT_TOKEN` env var
3. Set `GITHUB_TOKEN` env var
4. Run: `python3 scripts/telegram_bot.py`

**Commands:**
- `/submit <quote> — <author>` — Submit a quote
- `/random` — Get a random quote
- `/today` — Quote of the day
- `/stats` — Dataset stats

**Process pending submissions:**
```bash
python3 scripts/process_submissions.py          # Opens PR
python3 scripts/process_submissions.py --auto-merge  # Direct merge
```

---

## License

MIT — do whatever you want with these quotes. Attribution appreciated but not required.

The quotes themselves belong to their respective authors. This project curates and serves them in a developer-friendly format.
