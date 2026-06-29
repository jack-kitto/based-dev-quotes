#!/usr/bin/env python3
"""
based-dev-quotes: Quote scraper

Scrapes candidate quotes from:
  - Hacker News (top comments from front page stories)
  - Reddit r/programming, r/ExperiencedDevs, r/webdev (top comments)
  - Curated RSS/Atom feeds (dev blogs)

Outputs raw candidates to stdout as JSON for the LLM pipeline to process.
"""

import json
import sys
import urllib.request
import urllib.error
import time
from datetime import datetime, timezone


USER_AGENT = "based-dev-quotes/1.0 (https://github.com/jack-kitto/based-dev-quotes)"
HEADERS = {"User-Agent": USER_AGENT}


def fetch_json(url: str, headers: dict | None = None) -> dict | list | None:
    """Fetch JSON from a URL with error handling."""
    hdrs = {**HEADERS, **(headers or {})}
    req = urllib.request.Request(url, headers=hdrs)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read())
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError) as e:
        print(f"  ⚠️  Failed to fetch {url}: {e}", file=sys.stderr)
        return None


def fetch_text(url: str) -> str | None:
    """Fetch raw text from a URL."""
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except (urllib.error.URLError, urllib.error.HTTPError) as e:
        print(f"  ⚠️  Failed to fetch {url}: {e}", file=sys.stderr)
        return None


# --- Hacker News ---

def scrape_hn_top_comments(max_stories: int = 15, max_comments_per_story: int = 10) -> list[dict]:
    """
    Fetch top HN stories, then grab top-level comments.
    Returns list of {text, author, source, source_url}.
    """
    print("📰 Scraping Hacker News...", file=sys.stderr)
    candidates = []

    # Get top story IDs
    story_ids = fetch_json("https://hacker-news.firebaseio.com/v0/topstories.json")
    if not story_ids:
        return candidates

    for story_id in story_ids[:max_stories]:
        story = fetch_json(f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json")
        if not story or story.get("type") != "story":
            continue

        story_title = story.get("title", "")
        story_url = f"https://news.ycombinator.com/item?id={story_id}"

        # Only look at programming/tech stories
        kid_ids = story.get("kids", [])[:max_comments_per_story]

        for kid_id in kid_ids:
            comment = fetch_json(f"https://hacker-news.firebaseio.com/v0/item/{kid_id}.json")
            if not comment or comment.get("dead") or comment.get("deleted"):
                continue

            text = comment.get("text", "")
            author = comment.get("by", "Unknown")

            # Skip very short or very long comments (quotes are usually 1-3 sentences)
            # Strip HTML tags for length check
            import re
            clean = re.sub(r'<[^>]+>', '', text)
            if len(clean) < 30 or len(clean) > 500:
                continue

            candidates.append({
                "raw_text": clean,
                "author": author,
                "source": f"Hacker News — {story_title}",
                "source_url": story_url,
                "platform": "hackernews",
                "scraped_at": datetime.now(timezone.utc).isoformat()
            })

        time.sleep(0.1)  # Be nice to the API

    print(f"  Found {len(candidates)} HN candidates", file=sys.stderr)
    return candidates


# --- Reddit ---

def scrape_reddit_comments(subreddit: str, max_posts: int = 10, max_comments: int = 10) -> list[dict]:
    """
    Fetch top posts from a subreddit, then grab top comments.
    Uses old.reddit.com JSON API (no auth needed).
    """
    print(f"📰 Scraping r/{subreddit}...", file=sys.stderr)
    candidates = []

    # Reddit rate limits aggressively without OAuth — be conservative
    url = f"https://www.reddit.com/r/{subreddit}/hot.json?limit={max_posts}"
    data = fetch_json(url, headers={"User-Agent": USER_AGENT})
    if not data or "data" not in data:
        return candidates

    for post in data["data"].get("children", []):
        post_data = post.get("data", {})
        post_title = post_data.get("title", "")
        post_id = post_data.get("id", "")
        permalink = post_data.get("permalink", "")

        # Fetch comments
        comments_url = f"https://www.reddit.com{permalink}.json?limit={max_comments}&sort=top"
        comments_data = fetch_json(comments_url, headers={"User-Agent": USER_AGENT})
        if not comments_data or len(comments_data) < 2:
            time.sleep(2)  # Reddit rate limit
            continue

        for comment in comments_data[1].get("data", {}).get("children", []):
            c = comment.get("data", {})
            if comment.get("kind") != "t1":
                continue

            body = c.get("body", "")
            author = c.get("author", "Unknown")
            score = c.get("score", 0)

            # Only high-scoring comments (likely good content)
            if score < 20:
                continue

            # Length filter
            if len(body) < 30 or len(body) > 500:
                continue

            candidates.append({
                "raw_text": body,
                "author": f"u/{author}",
                "source": f"Reddit r/{subreddit} — {post_title}",
                "source_url": f"https://reddit.com{permalink}",
                "platform": "reddit",
                "score": score,
                "scraped_at": datetime.now(timezone.utc).isoformat()
            })

        time.sleep(2)  # Reddit rate limit

    print(f"  Found {len(candidates)} r/{subreddit} candidates", file=sys.stderr)
    return candidates


# --- Main ---

def main():
    all_candidates = []

    # Hacker News
    all_candidates.extend(scrape_hn_top_comments(max_stories=15, max_comments_per_story=8))

    # Reddit subreddits
    for sub in ["programming", "ExperiencedDevs", "webdev", "cscareerquestions"]:
        all_candidates.extend(scrape_reddit_comments(sub, max_posts=8, max_comments=8))
        time.sleep(3)  # Extra delay between subreddits

    print(f"\n📊 Total candidates scraped: {len(all_candidates)}", file=sys.stderr)

    # Output as JSON
    json.dump(all_candidates, sys.stdout, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()
