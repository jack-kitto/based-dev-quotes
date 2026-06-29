# Contributing to based-dev-quotes

Thanks for wanting to add quotes! Here's how.

## Adding Quotes

1. Fork this repo
2. Edit `quotes/quotes.json`
3. Add your quote(s) following the schema below
4. Run `node scripts/validate.js` to check your additions
5. Open a PR

## Quote Schema

```json
{
  "id": "author-slug-short-description",
  "text": "The actual quote text.",
  "author": "Full Author Name",
  "author_slug": "author-name-lowercase",
  "source": "Where this quote is from (book, talk, blog, tweet)",
  "source_url": "https://optional-link-to-source.com",
  "categories": ["wisdom", "funny"],
  "tags": ["specific", "descriptive", "tags"],
  "grug_level": 3,
  "spiciness": 2
}
```

## Fields

| Field | Required | Description |
|-------|----------|-------------|
| `id` | ✅ | Unique slug: `author-short-description` (lowercase, hyphens) |
| `text` | ✅ | The quote itself |
| `author` | ✅ | Full name. Use "Unknown" for folklore/anonymous |
| `author_slug` | ✅ | Lowercase hyphenated author name |
| `source` | ✅ | Book, talk, blog post, tweet, "Programming folklore" |
| `source_url` | ❌ | Link to original source |
| `categories` | ✅ | Array from the list below |
| `tags` | ✅ | Array of descriptive tags (lowercase, hyphenated) |
| `grug_level` | ✅ | 1-5: How grug-brained / anti-complexity is this quote? |
| `spiciness` | ✅ | 1-5: How controversial / hot-takey is this quote? |

## Categories

| Category | Vibe |
|----------|------|
| `grug` | Anti-complexity, caveman wisdom, "just make it work" |
| `suffering` | Hard-won lessons from production pain |
| `indie-hacker` | Building in public, shipping fast, bootstrapping |
| `unix` | Do one thing well, pipes, text streams, philosophy |
| `debugging` | The reality of finding and fixing bugs |
| `complexity` | Fighting entropy, over-engineering, abstraction |
| `shipping` | Just deploy the damn thing |
| `career` | Real talk about the industry and growth |
| `wisdom` | Timeless CS / engineering philosophy |
| `shitpost` | Chaotic dev humor, hot takes |
| `founder` | Startup / bootstrapping / business truth |
| `tools` | Editor wars, language debates, framework drama |
| `funny` | Comedy, jokes, relatable humor |

## Grug Level Guide

| Level | Meaning |
|-------|---------|
| 1 | Academic / theoretical — big brain energy |
| 2 | Thoughtful but practical |
| 3 | Balanced — could go either way |
| 4 | Pragmatic, prefers simplicity |
| 5 | Full grug — "just use a function", anti-abstraction |

## Spiciness Guide

| Level | Meaning |
|-------|---------|
| 1 | Universally agreed, non-controversial |
| 2 | Mild take — most devs would nod |
| 3 | Warm take — some pushback expected |
| 4 | Hot take — will start a thread |
| 5 | Thermonuclear — mass mass discourse |

## What We're Looking For

✅ **Yes please:**
- Quotes that make a developer chuckle, nod, or feel seen
- Hard-won wisdom from real experience
- Grug-brained anti-complexity takes
- Indie hacker / bootstrapper truths
- Funny observations about dev life that hit different
- Obscure gems from old Usenet posts, mailing lists, conference talks

❌ **No thanks:**
- Generic motivational poster quotes ("Code is poetry")
- LinkedIn inspirational garbage
- AI-generated quotes
- Anything mean-spirited or punching down
- Marketing copy disguised as wisdom

## Quote Sources to Mine

Looking for quotes? Try these:
- [The Grug Brained Developer](https://grugbrain.dev/)
- [Hacker News](https://news.ycombinator.com/) top comments
- Conference talks (Strange Loop, GOTO, DevGAMM, PyCon)
- Books (Mythical Man-Month, SICP, Pragmatic Programmer)
- Classic blog posts (Joel on Software, Paul Graham, patio11)
- Linus Torvalds' mailing list rants
- Old Usenet archives (comp.lang.*)
- Dev Twitter/X threads
