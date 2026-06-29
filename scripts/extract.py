#!/usr/bin/env python3
"""
based-dev-quotes: LLM Quote Extraction Pipeline

Takes raw scraped candidates (from scrape.py) and uses an LLM to:
  1. Filter: Is this actually a quotable statement?
  2. Extract: Clean up the quote text
  3. Score: grug_level, spiciness
  4. Categorize: categories + tags
  5. Deduplicate: Against existing quotes

Requires OPENROUTER_API_KEY env var.
Optionally set QUOTE_MODEL (default: google/gemini-2.5-flash).

Usage:
  python3 scripts/scrape.py | python3 scripts/extract.py
  python3 scripts/extract.py < candidates.json
  python3 scripts/extract.py --input candidates.json
"""

import json
import os
import re
import sys
import urllib.request
import urllib.error
from pathlib import Path

ROOT = Path(__file__).parent.parent
QUOTES_PATH = ROOT / "quotes" / "quotes.json"

# --- Config ---

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
MODEL = os.environ.get("QUOTE_MODEL", "google/gemini-2.5-flash")

EXTRACTION_PROMPT = """You are a quote curator for "based-dev-quotes" — a developer quotes API with a specific voice: grug-brained, indie hacker, anti-complexity, real engineering wisdom, and genuinely funny dev humor.

You will receive a batch of raw text candidates scraped from developer communities. For each one, decide:

1. **Is it quotable?** A good quote is:
   - A standalone insight, observation, or joke that works without context
   - Pithy, memorable, or genuinely funny
   - About programming, software engineering, startups, indie hacking, or dev culture
   - NOT a question, NOT a conversation fragment, NOT generic advice

2. **If quotable**, extract and clean it:
   - Trim to the quotable core (remove "I think...", "IMO...", conversational fluff)
   - Fix obvious typos but preserve voice/style
   - Keep it concise — ideally 1-3 sentences

3. **Score it**:
   - grug_level (1-5): How anti-complexity / pragmatic is it? 1=academic, 5=full grug
   - spiciness (1-5): How controversial? 1=universally agreed, 5=thermonuclear take

4. **Categorize it**:
   - categories: from [grug, suffering, indie-hacker, unix, debugging, complexity, shipping, career, wisdom, shitpost, founder, tools, funny]
   - tags: 2-5 descriptive lowercase hyphenated tags

IMPORTANT: Be selective. Only extract quotes that are genuinely good — you should reject 70-80% of candidates. Quality over quantity.

Respond with a JSON array of extracted quotes. For rejected candidates, don't include them. Each accepted quote:

```json
{
  "text": "The cleaned quote text",
  "author": "Original author (username if from social media)",
  "author_slug": "lowercase-hyphenated",
  "source": "Where it came from",
  "source_url": "URL if available",
  "categories": ["wisdom", "funny"],
  "tags": ["specific", "tags"],
  "grug_level": 3,
  "spiciness": 2,
  "extraction_note": "Brief note on why this quote is good (for review)"
}
```

Respond ONLY with the JSON array. No markdown fences, no explanation outside the array. If nothing is quotable, respond with [].
"""


def load_existing_quotes() -> list[dict]:
    """Load existing quotes for dedup."""
    if QUOTES_PATH.exists():
        with open(QUOTES_PATH, encoding="utf-8") as f:
            return json.load(f)
    return []


def call_llm(prompt: str, content: str) -> str:
    """Call OpenAI-compatible API."""
    if not OPENROUTER_API_KEY:
        print("❌ OPENROUTER_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    url = f"{OPENROUTER_BASE_URL}/chat/completions"
    payload = json.dumps({
        "model": MODEL,
        "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": content}
        ],
        "temperature": 0.3,
        "max_tokens": 4096
    }).encode()

    req = urllib.request.Request(url, data=payload, method="POST")
    req.add_header("Authorization", f"Bearer {OPENROUTER_API_KEY}")
    req.add_header("Content-Type", "application/json")
    req.add_header("HTTP-Referer", "https://github.com/jack-kitto/based-dev-quotes")
    req.add_header("X-Title", "based-dev-quotes")

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read())
            content = result["choices"][0]["message"]["content"]
            if content is None:
                raise ValueError(f"LLM returned null content: {json.dumps(result)[:500]}")
            return content
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"❌ LLM API error {e.code}: {body[:200]}", file=sys.stderr)
        sys.exit(1)


def generate_id(quote: dict) -> str:
    """Generate a slug ID for a quote."""
    author = quote.get("author_slug", "unknown")
    # Take first few words of the quote
    words = re.sub(r'[^a-z0-9\s]', '', quote["text"].lower()).split()[:4]
    slug = "-".join(words)
    return f"{author}-{slug}"[:64]


def deduplicate(new_quotes: list[dict], existing_quotes: list[dict]) -> list[dict]:
    """Remove quotes that are too similar to existing ones."""
    existing_texts = set()
    for q in existing_quotes:
        # Normalize for comparison
        normalized = re.sub(r'[^a-z0-9\s]', '', q["text"].lower()).strip()
        existing_texts.add(normalized)
        # Also add shorter versions (first 50 chars) for fuzzy matching
        if len(normalized) > 50:
            existing_texts.add(normalized[:50])

    deduped = []
    for q in new_quotes:
        normalized = re.sub(r'[^a-z0-9\s]', '', q["text"].lower()).strip()
        # Check exact and prefix match
        if normalized in existing_texts:
            print(f"  ⏭️  Skipping duplicate: \"{q['text'][:50]}...\"", file=sys.stderr)
            continue
        if len(normalized) > 50 and normalized[:50] in existing_texts:
            print(f"  ⏭️  Skipping near-duplicate: \"{q['text'][:50]}...\"", file=sys.stderr)
            continue
        deduped.append(q)
        existing_texts.add(normalized)

    return deduped


def main():
    # Read candidates from stdin or --input flag
    input_file = None
    for i, arg in enumerate(sys.argv[1:], 1):
        if arg == "--input" and i < len(sys.argv) - 1:
            input_file = sys.argv[i + 1]

    if input_file:
        with open(input_file, encoding="utf-8") as f:
            candidates = json.load(f)
    else:
        candidates = json.load(sys.stdin)

    if not candidates:
        print("No candidates to process", file=sys.stderr)
        json.dump([], sys.stdout)
        return

    print(f"📥 Processing {len(candidates)} candidates through LLM...", file=sys.stderr)
    print(f"   Model: {MODEL}", file=sys.stderr)
    print(f"   API: OpenRouter", file=sys.stderr)

    # Load existing quotes for dedup
    existing = load_existing_quotes()
    print(f"   Existing quotes: {len(existing)}", file=sys.stderr)

    # Process in batches of 20 (to stay within token limits)
    BATCH_SIZE = 20
    all_extracted = []

    for i in range(0, len(candidates), BATCH_SIZE):
        batch = candidates[i:i + BATCH_SIZE]
        print(f"\n🔄 Processing batch {i // BATCH_SIZE + 1} ({len(batch)} candidates)...", file=sys.stderr)

        # Format candidates for the LLM
        batch_text = json.dumps([{
            "raw_text": c["raw_text"],
            "author": c["author"],
            "source": c["source"],
            "source_url": c.get("source_url", ""),
            "platform": c.get("platform", ""),
            "score": c.get("score", 0)
        } for c in batch], indent=2)

        # Call LLM
        response = call_llm(EXTRACTION_PROMPT, batch_text)

        # Parse response — handle markdown fences if present
        if response is None:
            print(f"   ❌ LLM returned empty response for batch, skipping", file=sys.stderr)
            continue
        clean_response = response.strip()
        if clean_response.startswith("```"):
            clean_response = re.sub(r'^```(?:json)?\s*', '', clean_response)
            clean_response = re.sub(r'\s*```$', '', clean_response)

        try:
            extracted = json.loads(clean_response)
            if not isinstance(extracted, list):
                extracted = [extracted]
            print(f"   ✅ Extracted {len(extracted)} quotes from batch", file=sys.stderr)
            all_extracted.extend(extracted)
        except json.JSONDecodeError as e:
            print(f"   ❌ Failed to parse LLM response: {e}", file=sys.stderr)
            print(f"   Raw response: {clean_response[:200]}...", file=sys.stderr)

    # Deduplicate against existing
    print(f"\n🔍 Deduplicating {len(all_extracted)} extracted quotes...", file=sys.stderr)
    deduped = deduplicate(all_extracted, existing)
    print(f"   {len(deduped)} new unique quotes after dedup", file=sys.stderr)

    # Generate IDs and clean up
    for q in deduped:
        q["id"] = generate_id(q)
        # Remove extraction_note from final output (it's just for review)
        q.setdefault("source", "Community sourced")

    # Output
    print(f"\n📊 Final: {len(deduped)} new quotes extracted", file=sys.stderr)
    json.dump(deduped, sys.stdout, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()
