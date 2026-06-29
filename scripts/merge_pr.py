#!/usr/bin/env python3
"""
based-dev-quotes: Merge new quotes and open a PR

Takes extracted quotes (from extract.py) and:
  1. Merges them into quotes/quotes.json
  2. Creates a new branch
  3. Commits the changes
  4. Opens a PR for review

Usage:
  python3 scripts/extract.py < candidates.json | python3 scripts/merge_pr.py
  python3 scripts/merge_pr.py --input new_quotes.json
  python3 scripts/merge_pr.py --input new_quotes.json --auto-merge  # skip PR, merge directly

Requires: git, GITHUB_TOKEN env var (for PR creation)
"""

import json
import os
import re
import subprocess
import sys
import urllib.request
import urllib.error
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent.parent
QUOTES_PATH = ROOT / "quotes" / "quotes.json"
REPO_OWNER = "jack-kitto"
REPO_NAME = "based-dev-quotes"


def run(cmd: str, check: bool = True) -> str:
    """Run a shell command and return stdout."""
    result = subprocess.run(
        cmd, shell=True, capture_output=True, text=True, cwd=str(ROOT)
    )
    if check and result.returncode != 0:
        print(f"❌ Command failed: {cmd}", file=sys.stderr)
        print(f"   stderr: {result.stderr}", file=sys.stderr)
        sys.exit(1)
    return result.stdout.strip()


def load_existing() -> list[dict]:
    with open(QUOTES_PATH, encoding="utf-8") as f:
        return json.load(f)


def save_quotes(quotes: list[dict]):
    with open(QUOTES_PATH, "w", encoding="utf-8") as f:
        json.dump(quotes, f, indent=2, ensure_ascii=False)
        f.write("\n")


def ensure_unique_ids(new_quotes: list[dict], existing: list[dict]) -> list[dict]:
    """Ensure all new quotes have unique IDs."""
    existing_ids = {q["id"] for q in existing}
    for q in new_quotes:
        base_id = q["id"]
        counter = 1
        while q["id"] in existing_ids:
            q["id"] = f"{base_id}-{counter}"
            counter += 1
        existing_ids.add(q["id"])
    return new_quotes


def create_pr(branch: str, title: str, body: str, token: str):
    """Create a GitHub PR via API."""
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/pulls"
    payload = json.dumps({
        "title": title,
        "body": body,
        "head": branch,
        "base": "main"
    }).encode()

    req = urllib.request.Request(url, data=payload, method="POST")
    req.add_header("Authorization", f"token {token}")
    req.add_header("Content-Type", "application/json")
    req.add_header("Accept", "application/vnd.github+json")

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())
            return result.get("html_url", "PR created")
    except urllib.error.HTTPError as e:
        body_text = e.read().decode()
        print(f"❌ Failed to create PR: {e.code} — {body_text[:200]}", file=sys.stderr)
        return None


def main():
    auto_merge = "--auto-merge" in sys.argv

    # Read new quotes from stdin or --input
    input_file = None
    for i, arg in enumerate(sys.argv[1:], 1):
        if arg == "--input" and i < len(sys.argv) - 1:
            input_file = sys.argv[i + 1]

    if input_file:
        with open(input_file, encoding="utf-8") as f:
            new_quotes = json.load(f)
    else:
        new_quotes = json.load(sys.stdin)

    if not new_quotes:
        print("No new quotes to merge", file=sys.stderr)
        return

    print(f"📥 Merging {len(new_quotes)} new quotes...", file=sys.stderr)

    # Load existing
    existing = load_existing()
    print(f"   Existing: {len(existing)} quotes", file=sys.stderr)

    # Ensure unique IDs
    new_quotes = ensure_unique_ids(new_quotes, existing)

    # Merge
    merged = existing + new_quotes
    print(f"   After merge: {len(merged)} quotes", file=sys.stderr)

    if auto_merge:
        # Direct merge to main
        save_quotes(merged)
        run("python3 scripts/generate.py")
        run('git add -A')
        run(f'git commit -m "🧠 Add {len(new_quotes)} new quotes (auto-merged)"')
        run('git push')
        print(f"✅ Auto-merged {len(new_quotes)} quotes to main", file=sys.stderr)
        return

    # Create branch and PR
    now = datetime.now(timezone.utc)
    branch = f"quotes/auto-{now.strftime('%Y%m%d-%H%M%S')}"

    run(f"git checkout -b {branch}")
    save_quotes(merged)

    # Regenerate API
    run("python3 scripts/generate.py")

    # Commit
    run("git add -A")

    # Build commit message with quote preview
    preview_lines = []
    for q in new_quotes[:5]:
        preview_lines.append(f'  - "{q["text"][:60]}..." — {q["author"]}')
    if len(new_quotes) > 5:
        preview_lines.append(f"  ... and {len(new_quotes) - 5} more")

    commit_msg = f"🧠 Add {len(new_quotes)} new quotes\n\n" + "\n".join(preview_lines)
    # Use a temp file to avoid shell quoting issues with quotes inside the message
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write(commit_msg)
        tmp_path = f.name
    try:
        run(f"git commit -F {tmp_path}")
    finally:
        os.unlink(tmp_path)
    run(f"git push -u origin {branch}")

    # Create PR
    token = os.environ.get("GITHUB_TOKEN", "")
    if token:
        pr_body = f"""## 🧠 {len(new_quotes)} New Quotes

Auto-extracted from developer communities.

### Preview

| Quote | Author | Categories | Grug | Spice |
|-------|--------|-----------|------|-------|
"""
        for q in new_quotes:
            text_preview = q["text"][:60] + ("..." if len(q["text"]) > 60 else "")
            cats = ", ".join(q.get("categories", []))
            note = q.get("extraction_note", "")
            pr_body += f'| "{text_preview}" | {q["author"]} | {cats} | {q.get("grug_level", "?")} | {q.get("spiciness", "?")} |\n'

        if any(q.get("extraction_note") for q in new_quotes):
            pr_body += "\n### Extraction Notes\n\n"
            for q in new_quotes:
                if q.get("extraction_note"):
                    pr_body += f'- **"{q["text"][:40]}..."**: {q["extraction_note"]}\n'

        pr_body += f"\n---\n_Auto-generated by the based-dev-quotes pipeline on {now.strftime('%Y-%m-%d %H:%M UTC')}_"

        pr_url = create_pr(
            branch=branch,
            title=f"🧠 Add {len(new_quotes)} new quotes",
            body=pr_body,
            token=token
        )
        if pr_url:
            print(f"✅ PR created: {pr_url}", file=sys.stderr)
    else:
        print("⚠️  No GITHUB_TOKEN — branch pushed but no PR created", file=sys.stderr)
        print(f"   Branch: {branch}", file=sys.stderr)

    # Switch back to main
    run("git checkout main")


if __name__ == "__main__":
    main()
