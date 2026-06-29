#!/usr/bin/env python3
"""
based-dev-quotes: Process pending Telegram submissions

Takes pending submissions from quotes/submissions.json, runs them through
the LLM for scoring/categorization, and opens a PR.

Usage:
  python3 scripts/process_submissions.py
  python3 scripts/process_submissions.py --auto-merge

Can be run as a cron job or manually.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
SUBMISSIONS_PATH = ROOT / "quotes" / "submissions.json"


def main():
    if not SUBMISSIONS_PATH.exists():
        print("No submissions file found", file=sys.stderr)
        return

    with open(SUBMISSIONS_PATH, encoding="utf-8") as f:
        submissions = json.load(f)

    pending = [s for s in submissions if s.get("status") == "pending"]
    if not pending:
        print("No pending submissions", file=sys.stderr)
        return

    print(f"📋 Processing {len(pending)} pending submissions...", file=sys.stderr)

    # Convert submissions to candidate format for the extract pipeline
    candidates = []
    for s in pending:
        candidates.append({
            "raw_text": s["text"],
            "author": s["author"],
            "source": f"Community submission by {s.get('submitted_by', 'anonymous')}",
            "source_url": "",
            "platform": "telegram",
            "scraped_at": s.get("submitted_at", "")
        })

    # Write candidates to temp file
    import tempfile
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(candidates, f, indent=2)
        tmp_path = f.name

    # Run through extract pipeline
    import subprocess
    result = subprocess.run(
        ["python3", str(ROOT / "scripts" / "extract.py"), "--input", tmp_path],
        capture_output=True, text=True, cwd=str(ROOT)
    )

    if result.returncode != 0:
        print(f"❌ Extract failed: {result.stderr}", file=sys.stderr)
        return

    try:
        extracted = json.loads(result.stdout)
    except json.JSONDecodeError:
        print(f"❌ Failed to parse extract output", file=sys.stderr)
        return

    if not extracted:
        print("No quotes passed extraction filter", file=sys.stderr)
        # Mark all as rejected
        for s in submissions:
            if s.get("status") == "pending":
                s["status"] = "rejected"
        with open(SUBMISSIONS_PATH, "w", encoding="utf-8") as f:
            json.dump(submissions, f, indent=2, ensure_ascii=False)
            f.write("\n")
        return

    # Run through merge_pr
    import tempfile
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(extracted, f, indent=2)
        tmp_extract = f.name

    merge_args = ["python3", str(ROOT / "scripts" / "merge_pr.py"), "--input", tmp_extract]
    if "--auto-merge" in sys.argv:
        merge_args.append("--auto-merge")

    result = subprocess.run(merge_args, capture_output=True, text=True, cwd=str(ROOT))
    print(result.stderr, file=sys.stderr)

    # Mark submissions as processed
    for s in submissions:
        if s.get("status") == "pending":
            s["status"] = "processed"

    with open(SUBMISSIONS_PATH, "w", encoding="utf-8") as f:
        json.dump(submissions, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print(f"✅ Processed {len(pending)} submissions → {len(extracted)} quotes", file=sys.stderr)

    # Cleanup
    import os
    os.unlink(tmp_path)
    os.unlink(tmp_extract)


if __name__ == "__main__":
    main()
