#!/usr/bin/env python3
"""
Validate quotes/quotes.json schema and catch common issues.
Run via: python3 scripts/validate.py
"""

import json
import re
import sys
from pathlib import Path

QUOTES_PATH = Path(__file__).parent.parent / 'quotes' / 'quotes.json'

VALID_CATEGORIES = [
    'grug', 'suffering', 'indie-hacker', 'unix', 'debugging',
    'complexity', 'shipping', 'career', 'wisdom', 'shitpost',
    'founder', 'tools', 'funny', 'design', 'product', 'engineering',
    'business', 'entrepreneur', 'marketing', 'saas', 'users',
    'productivity', 'devops'
]


def validate():
    with open(QUOTES_PATH, encoding='utf-8') as f:
        quotes = json.load(f)

    errors = []
    warnings = []
    ids = set()

    for i, q in enumerate(quotes):
        prefix = f"Quote #{i} ({q.get('id', 'NO ID')})"

        # Required fields
        for field in ['id', 'text', 'author', 'author_slug', 'categories', 'tags']:
            if not q.get(field):
                errors.append(f"{prefix}: missing '{field}'")

        if q.get('grug_level') is None:
            errors.append(f"{prefix}: missing 'grug_level'")
        if q.get('spiciness') is None:
            errors.append(f"{prefix}: missing 'spiciness'")

        # Duplicate ID check
        qid = q.get('id')
        if qid:
            if qid in ids:
                errors.append(f"{prefix}: duplicate ID")
            ids.add(qid)

        # Range checks
        gl = q.get('grug_level', 0)
        sp = q.get('spiciness', 0)
        if not (1 <= gl <= 5):
            errors.append(f"{prefix}: grug_level must be 1-5, got {gl}")
        if not (1 <= sp <= 5):
            errors.append(f"{prefix}: spiciness must be 1-5, got {sp}")

        # Category validation
        for cat in q.get('categories', []):
            if cat not in VALID_CATEGORIES:
                warnings.append(f"{prefix}: unknown category '{cat}'")

        # Slug format
        if qid and not re.match(r'^[a-z0-9-]+$', qid):
            errors.append(f"{prefix}: id should be lowercase with hyphens only")
        slug = q.get('author_slug', '')
        if slug and not re.match(r'^[a-z0-9-]+$', slug):
            errors.append(f"{prefix}: author_slug should be lowercase with hyphens only")

    # Report
    print(f"\n📋 Validated {len(quotes)} quotes\n")

    if warnings:
        print(f"⚠️  {len(warnings)} warnings:")
        for w in warnings:
            print(f"   {w}")
        print()

    if errors:
        print(f"❌ {len(errors)} errors:")
        for e in errors:
            print(f"   {e}")
        sys.exit(1)
    else:
        all_cats = set(c for q in quotes for c in q.get('categories', []))
        all_tags = set(t for q in quotes for t in q.get('tags', []))
        all_authors = set(q['author_slug'] for q in quotes)
        print('✅ All quotes valid!')
        print(f'   {len(ids)} unique quotes')
        print(f'   {len(all_authors)} unique authors')
        print(f'   {len(all_cats)} categories used')
        print(f'   {len(all_tags)} unique tags')


if __name__ == '__main__':
    validate()
