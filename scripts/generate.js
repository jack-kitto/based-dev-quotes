#!/usr/bin/env node

/**
 * based-dev-quotes static API generator
 *
 * Reads quotes/quotes.json and generates the full static API structure:
 *   api/v1/all.json          — full dataset
 *   api/v1/today.json        — deterministic quote of the day
 *   api/v1/random.json       — rotated on each generation
 *   api/v1/stats.json        — dataset stats
 *   api/v1/categories/{slug}.json
 *   api/v1/authors/{slug}.json
 *   api/v1/authors/index.json
 *   api/v1/tags/{slug}.json
 *   api/v1/tags/index.json
 */

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const QUOTES_PATH = path.join(__dirname, '..', 'quotes', 'quotes.json');
const API_DIR = path.join(__dirname, '..', 'api', 'v1');

// --- Helpers ---

function ensureDir(dir) {
  fs.mkdirSync(dir, { recursive: true });
}

function writeJSON(filepath, data) {
  ensureDir(path.dirname(filepath));
  fs.writeFileSync(filepath, JSON.stringify(data, null, 2) + '\n');
}

/**
 * Deterministic "quote of the day" based on date hash.
 * Same quote for everyone on the same day.
 */
function getQuoteOfTheDay(quotes) {
  const today = new Date().toISOString().split('T')[0]; // YYYY-MM-DD
  const hash = crypto.createHash('sha256').update(today).digest('hex');
  const index = parseInt(hash.slice(0, 8), 16) % quotes.length;
  return { ...quotes[index], _date: today };
}

/**
 * Pseudo-random quote (changes each generation run).
 */
function getRandomQuote(quotes) {
  const index = Math.floor(Math.random() * quotes.length);
  return { ...quotes[index], _generated_at: new Date().toISOString() };
}

/**
 * Group quotes by a key that may be a string or array.
 */
function groupBy(quotes, key) {
  const groups = {};
  for (const q of quotes) {
    const values = Array.isArray(q[key]) ? q[key] : [q[key]];
    for (const v of values) {
      if (!v) continue;
      const slug = typeof v === 'string' ? v.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, '') : v;
      if (!groups[slug]) groups[slug] = [];
      groups[slug].push(q);
    }
  }
  return groups;
}

// --- Main ---

function main() {
  console.log('📖 Loading quotes...');
  const quotes = JSON.parse(fs.readFileSync(QUOTES_PATH, 'utf-8'));
  console.log(`   Found ${quotes.length} quotes`);

  // Clean output directory
  if (fs.existsSync(API_DIR)) {
    fs.rmSync(API_DIR, { recursive: true });
  }

  // 1. all.json
  console.log('📝 Generating api/v1/all.json');
  writeJSON(path.join(API_DIR, 'all.json'), {
    total: quotes.length,
    generated_at: new Date().toISOString(),
    quotes
  });

  // 2. today.json (deterministic by date)
  console.log('🌅 Generating api/v1/today.json');
  const todayQuote = getQuoteOfTheDay(quotes);
  writeJSON(path.join(API_DIR, 'today.json'), todayQuote);
  console.log(`   Today's quote: "${todayQuote.text.slice(0, 60)}..." by ${todayQuote.author}`);

  // 3. random.json (changes each run)
  console.log('🎲 Generating api/v1/random.json');
  writeJSON(path.join(API_DIR, 'random.json'), getRandomQuote(quotes));

  // 4. Multiple random slots for pseudo-random client-side selection
  console.log('🎰 Generating api/v1/random/{1-20}.json');
  const shuffled = [...quotes].sort(() => Math.random() - 0.5);
  ensureDir(path.join(API_DIR, 'random'));
  for (let i = 0; i < Math.min(20, quotes.length); i++) {
    writeJSON(path.join(API_DIR, 'random', `${i + 1}.json`), shuffled[i]);
  }

  // 5. Categories
  console.log('📂 Generating api/v1/categories/');
  const categories = groupBy(quotes, 'categories');
  const categoryIndex = {};
  for (const [slug, catQuotes] of Object.entries(categories)) {
    categoryIndex[slug] = { count: catQuotes.length };
    writeJSON(path.join(API_DIR, 'categories', `${slug}.json`), {
      category: slug,
      count: catQuotes.length,
      quotes: catQuotes
    });
  }
  writeJSON(path.join(API_DIR, 'categories', 'index.json'), {
    total: Object.keys(categories).length,
    categories: categoryIndex
  });
  console.log(`   ${Object.keys(categories).length} categories`);

  // 6. Authors
  console.log('👤 Generating api/v1/authors/');
  const authors = groupBy(quotes, 'author_slug');
  const authorIndex = {};
  for (const [slug, authorQuotes] of Object.entries(authors)) {
    const name = authorQuotes[0].author;
    authorIndex[slug] = { name, count: authorQuotes.length };
    writeJSON(path.join(API_DIR, 'authors', `${slug}.json`), {
      author: name,
      slug,
      count: authorQuotes.length,
      quotes: authorQuotes
    });
  }
  writeJSON(path.join(API_DIR, 'authors', 'index.json'), {
    total: Object.keys(authors).length,
    authors: authorIndex
  });
  console.log(`   ${Object.keys(authors).length} authors`);

  // 7. Tags
  console.log('🏷️  Generating api/v1/tags/');
  const tags = groupBy(quotes, 'tags');
  const tagIndex = {};
  for (const [slug, tagQuotes] of Object.entries(tags)) {
    tagIndex[slug] = { count: tagQuotes.length };
    writeJSON(path.join(API_DIR, 'tags', `${slug}.json`), {
      tag: slug,
      count: tagQuotes.length,
      quotes: tagQuotes
    });
  }
  writeJSON(path.join(API_DIR, 'tags', 'index.json'), {
    total: Object.keys(tags).length,
    tags: tagIndex
  });
  console.log(`   ${Object.keys(tags).length} tags`);

  // 8. Stats
  console.log('📊 Generating api/v1/stats.json');
  const grugLevels = {};
  const spicyLevels = {};
  for (const q of quotes) {
    grugLevels[q.grug_level] = (grugLevels[q.grug_level] || 0) + 1;
    spicyLevels[q.spiciness] = (spicyLevels[q.spiciness] || 0) + 1;
  }
  writeJSON(path.join(API_DIR, 'stats.json'), {
    total_quotes: quotes.length,
    total_authors: Object.keys(authors).length,
    total_categories: Object.keys(categories).length,
    total_tags: Object.keys(tags).length,
    grug_level_distribution: grugLevels,
    spiciness_distribution: spicyLevels,
    generated_at: new Date().toISOString()
  });

  console.log('\n✅ Static API generated successfully!');
  console.log(`   ${quotes.length} quotes → ${Object.keys(categories).length} categories, ${Object.keys(authors).length} authors, ${Object.keys(tags).length} tags`);
}

main();
