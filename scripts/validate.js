#!/usr/bin/env node

/**
 * Validate quotes/quotes.json schema and catch common issues.
 */

const fs = require('fs');
const path = require('path');

const QUOTES_PATH = path.join(__dirname, '..', 'quotes', 'quotes.json');

const VALID_CATEGORIES = [
  'grug', 'suffering', 'indie-hacker', 'unix', 'debugging',
  'complexity', 'shipping', 'career', 'wisdom', 'shitpost',
  'founder', 'tools', 'funny'
];

function validate() {
  const quotes = JSON.parse(fs.readFileSync(QUOTES_PATH, 'utf-8'));
  const errors = [];
  const warnings = [];
  const ids = new Set();

  for (let i = 0; i < quotes.length; i++) {
    const q = quotes[i];
    const prefix = `Quote #${i} (${q.id || 'NO ID'})`;

    // Required fields
    if (!q.id) errors.push(`${prefix}: missing 'id'`);
    if (!q.text) errors.push(`${prefix}: missing 'text'`);
    if (!q.author) errors.push(`${prefix}: missing 'author'`);
    if (!q.author_slug) errors.push(`${prefix}: missing 'author_slug'`);
    if (!q.categories || !q.categories.length) errors.push(`${prefix}: missing 'categories'`);
    if (!q.tags || !q.tags.length) errors.push(`${prefix}: missing 'tags'`);
    if (q.grug_level === undefined) errors.push(`${prefix}: missing 'grug_level'`);
    if (q.spiciness === undefined) errors.push(`${prefix}: missing 'spiciness'`);

    // Duplicate ID check
    if (q.id && ids.has(q.id)) errors.push(`${prefix}: duplicate ID`);
    if (q.id) ids.add(q.id);

    // Range checks
    if (q.grug_level < 1 || q.grug_level > 5) errors.push(`${prefix}: grug_level must be 1-5, got ${q.grug_level}`);
    if (q.spiciness < 1 || q.spiciness > 5) errors.push(`${prefix}: spiciness must be 1-5, got ${q.spiciness}`);

    // Category validation
    if (q.categories) {
      for (const cat of q.categories) {
        if (!VALID_CATEGORIES.includes(cat)) {
          warnings.push(`${prefix}: unknown category '${cat}' (valid: ${VALID_CATEGORIES.join(', ')})`);
        }
      }
    }

    // Slug format check
    if (q.id && !/^[a-z0-9-]+$/.test(q.id)) {
      errors.push(`${prefix}: id should be lowercase with hyphens only`);
    }
    if (q.author_slug && !/^[a-z0-9-]+$/.test(q.author_slug)) {
      errors.push(`${prefix}: author_slug should be lowercase with hyphens only`);
    }
  }

  // Report
  console.log(`\n📋 Validated ${quotes.length} quotes\n`);

  if (warnings.length) {
    console.log(`⚠️  ${warnings.length} warnings:`);
    warnings.forEach(w => console.log(`   ${w}`));
    console.log();
  }

  if (errors.length) {
    console.log(`❌ ${errors.length} errors:`);
    errors.forEach(e => console.log(`   ${e}`));
    process.exit(1);
  } else {
    console.log('✅ All quotes valid!');
    console.log(`   ${ids.size} unique quotes`);
    console.log(`   ${new Set(quotes.map(q => q.author_slug)).size} unique authors`);
    console.log(`   ${new Set(quotes.flatMap(q => q.categories)).size} categories used`);
    console.log(`   ${new Set(quotes.flatMap(q => q.tags)).size} unique tags`);
  }
}

validate();
