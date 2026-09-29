# Blogs

Each `.md` file here is published at `sheikhfahan.com/notes/blogs/<file-name>`.
This README is not published.

## Frontmatter (optional)

Put this block at the very top of a post to control its share card (X, LinkedIn, Slack, …):

```md
---
title: Why I stopped using ORMs for everything
description: One or two sentences shown under the headline on the card.
date: 2026-09-29
image: ./orm-cover.jpg
---

# Why I stopped using ORMs for everything
...
```

| Field | Used for | If left out |
|---|---|---|
| `title` | Card headline, browser tab, `/notes` list | First `# ` heading, else the file name |
| `description` | Card text, `/notes` list (cut at 160 chars) | First paragraph of the post |
| `date` | Date shown and sort order on `/notes` (`YYYY-MM-DD`) | File modified time (unreliable on the live site) |
| `image` | Card image | Site default (autumn photo) |

Rules:
- One `key: value` per line; no nesting or multi-line values. Quotes around a value are optional.
- `image` is a path relative to the post (`./orm-cover.jpg`, `../images/x.png`) or a full `https://` URL.
  Local images must be inside this repo and jpg, jpeg, png, webp or gif. They're served at `/media/<path in this repo>`.
- Images inside a post work the same way: `![alt text](./pic.png)` with the file next to the post.
- Card images: 1200×630 (1.91:1), under 5 MB. X crops other shapes to fit.
- A wrong `image` path doesn't break the build; the post falls back to the default image and the build logs a warning.

Frontmatter works the same way in every note in this repo, not just blogs.
