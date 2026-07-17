# Blog Posts

## Frontmatter

```yaml
---
layout: post
title: "Title in Title Case"
categories:
  - Posts
tags:
  - Tag One
  - Tag Two
---
```

Filename format: `YYYY-MM-DD-title-slug.md` — spell everything correctly (e.g. `postgres` not `postgress`).

Common tags: `Today I learned`, `Postgres`, `Next.js`, `React`, `Web`, `Git`, `DevOps`, `npm`

## Writing style

Plain, first-person, conversational. Anchor the post in a real moment or problem ("While building X, I ran into Y", "Today I learned..."). No marketing language.

**Avoid:**
- Em dashes (—). Use commas, periods, or plain connecting words instead.
- Flowery phrases: "perfect excuse", "real unblocker", "heavy lifting", "collapses into", "drilling this boundary deliberately"
- "let's" when you mean "lets" (common typo)
- "discuss about" — just "discuss"

**Capitalize proper nouns:** PostgreSQL, World Cup, API, Next.js, GitHub, AWS EventBridge, etc.

**Sign off:** end posts with `Happy coding!`

## Structure

- Use `###` (h3) for section headers, not h1 or h2
- Code blocks always include a language tag: ` ```sql `, ` ```tsx `, ` ```yaml `, ` ```bash `
- Bullet lists for multiple items (technical comparisons, pros/cons, steps)
- Numbered lists only when order matters
- Don't overuse inline code formatting in prose. Reserve backticks for the specific identifier a sentence is naming or introducing (a function, type, or flag), not every variable/keyword already shown in a code block above. A sentence with four or five backtick spans is harder to read, not clearer.

## TIL format (most posts follow this)

1. Open with the real moment that prompted the post (one paragraph)
2. Explain the concept or what you learned
3. Show a concrete code example from an actual project
4. Walk through what the code does
5. Close with a one-sentence takeaway + `Happy coding!`

## Linked projects

When referencing worldcuppicks.co, use: `[worldcuppicks.co](https://www.worldcuppicks.co)` (note the **s** at the end).
