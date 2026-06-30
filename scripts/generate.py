#!/usr/bin/env python3
"""
based-dev-quotes static API generator (Python version)

Reads quotes/quotes.json and generates the full static API in api/v1/.
Run via: python3 scripts/generate.py
"""

import json
import hashlib
import random
import os
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent.parent
QUOTES_PATH = ROOT / 'quotes' / 'quotes.json'
API_DIR = ROOT / 'api' / 'v1'


def write_json(filepath: Path, data):
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write('\n')


def slugify(s: str) -> str:
    return re.sub(r'(^-|-$)', '', re.sub(r'[^a-z0-9]+', '-', s.lower()))


def group_by(quotes: list, key: str) -> dict:
    groups = {}
    for q in quotes:
        values = q.get(key, [])
        if not isinstance(values, list):
            values = [values]
        for v in values:
            if not v:
                continue
            slug = v if key == 'author_slug' else slugify(str(v))
            groups.setdefault(slug, []).append(q)
    return groups


def main():
    print('📖 Loading quotes...')
    with open(QUOTES_PATH, encoding='utf-8') as f:
        quotes = json.load(f)
    print(f'   Found {len(quotes)} quotes')

    now = datetime.now(timezone.utc).isoformat()
    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')

    # Clean output
    if API_DIR.exists():
        shutil.rmtree(API_DIR)

    # 1. all.json
    print('📝 Generating api/v1/all.json')
    write_json(API_DIR / 'all.json', {
        'total': len(quotes),
        'generated_at': now,
        'quotes': quotes
    })

    # 2. today.json — deterministic by date
    print('🌅 Generating api/v1/today.json')
    hash_hex = hashlib.sha256(today.encode()).hexdigest()
    today_idx = int(hash_hex[:8], 16) % len(quotes)
    today_quote = {**quotes[today_idx], '_date': today}
    write_json(API_DIR / 'today.json', today_quote)
    print(f'   Today: "{today_quote["text"][:60]}..." — {today_quote["author"]}')

    # 3. random.json — changes each run
    print('🎲 Generating api/v1/random.json')
    rand_quote = {**random.choice(quotes), '_generated_at': now}
    write_json(API_DIR / 'random.json', rand_quote)

    # 4. Random slots
    print('🎰 Generating api/v1/random/{1-20}.json')
    shuffled = quotes[:]
    random.shuffle(shuffled)
    for i in range(min(20, len(quotes))):
        write_json(API_DIR / 'random' / f'{i + 1}.json', shuffled[i])

    # 5. Categories
    print('📂 Generating api/v1/categories/')
    categories = group_by(quotes, 'categories')
    cat_index = {}
    for slug, cat_quotes in sorted(categories.items()):
        cat_index[slug] = {'count': len(cat_quotes)}
        write_json(API_DIR / 'categories' / f'{slug}.json', {
            'category': slug,
            'count': len(cat_quotes),
            'quotes': cat_quotes
        })
    write_json(API_DIR / 'categories' / 'index.json', {
        'total': len(categories),
        'categories': cat_index
    })
    print(f'   {len(categories)} categories')

    # 6. Authors
    print('👤 Generating api/v1/authors/')
    authors = group_by(quotes, 'author_slug')
    author_index = {}
    for slug, author_quotes in sorted(authors.items()):
        name = author_quotes[0]['author']
        author_index[slug] = {'name': name, 'count': len(author_quotes)}
        write_json(API_DIR / 'authors' / f'{slug}.json', {
            'author': name,
            'slug': slug,
            'count': len(author_quotes),
            'quotes': author_quotes
        })
    write_json(API_DIR / 'authors' / 'index.json', {
        'total': len(authors),
        'authors': author_index
    })
    print(f'   {len(authors)} authors')

    # 7. Tags
    print('🏷️  Generating api/v1/tags/')
    tags = group_by(quotes, 'tags')
    tag_index = {}
    for slug, tag_quotes in sorted(tags.items()):
        tag_index[slug] = {'count': len(tag_quotes)}
        write_json(API_DIR / 'tags' / f'{slug}.json', {
            'tag': slug,
            'count': len(tag_quotes),
            'quotes': tag_quotes
        })
    write_json(API_DIR / 'tags' / 'index.json', {
        'total': len(tags),
        'tags': tag_index
    })
    print(f'   {len(tags)} tags')

    # 8. Stats
    print('📊 Generating api/v1/stats.json')
    grug_dist = {}
    spicy_dist = {}
    for q in quotes:
        gl = str(q['grug_level'])
        sp = str(q['spiciness'])
        grug_dist[gl] = grug_dist.get(gl, 0) + 1
        spicy_dist[sp] = spicy_dist.get(sp, 0) + 1

    write_json(API_DIR / 'stats.json', {
        'total_quotes': len(quotes),
        'total_authors': len(authors),
        'total_categories': len(categories),
        'total_tags': len(tags),
        'grug_level_distribution': dict(sorted(grug_dist.items())),
        'spiciness_distribution': dict(sorted(spicy_dist.items())),
        'generated_at': now
    })

    # 9. Version file (content-based cache buster)
    quotes_hash = hashlib.md5(json.dumps(quotes, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:12]
    write_json(API_DIR / 'version.json', {
        'version': quotes_hash,
        'generated_at': now,
        'total_quotes': len(quotes)
    })

    file_count = sum(len(files) for _, _, files in os.walk(API_DIR))
    print(f'\n✅ Static API generated!')
    print(f'   {len(quotes)} quotes → {file_count} JSON files')
    print(f'   {len(categories)} categories, {len(authors)} authors, {len(tags)} tags')


if __name__ == '__main__':
    main()
