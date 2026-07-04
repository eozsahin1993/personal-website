#!/usr/bin/env python3
import sys
import os
import re
import yaml
import requests


def parse_post(filepath):
    with open(filepath, "r") as f:
        content = f.read()

    match = re.match(r"^---\n(.*?)\n---\n(.*)", content, re.DOTALL)
    if not match:
        print(f"No frontmatter found in {filepath}, skipping.")
        sys.exit(0)

    frontmatter = yaml.safe_load(match.group(1))
    body = match.group(2).strip()
    return frontmatter, body


def sanitize_tags(tags):
    # dev.to tags must be alphanumeric (no spaces/punctuation) and max 4
    cleaned = []
    for tag in tags:
        slug = re.sub(r"[^a-zA-Z0-9]", "", tag)
        if slug:
            cleaned.append(slug)
    return cleaned[:4]


def publish(token, title, content, tags):
    response = requests.post(
        "https://dev.to/api/articles",
        headers={
            "api-key": token,
            "Content-Type": "application/json",
        },
        json={
            "article": {
                "title": title,
                "body_markdown": f"# {title}\n\n{content}",
                "tags": sanitize_tags(tags),
                "published": True,
            }
        },
    )
    response.raise_for_status()
    return response.json()


def main():
    if len(sys.argv) < 2:
        print("Usage: publish_to_devto.py <post-file>")
        sys.exit(1)

    filepath = sys.argv[1]
    token = os.environ.get("DEVTO_TOKEN")
    if not token:
        print("DEVTO_TOKEN not set")
        sys.exit(1)

    frontmatter, body = parse_post(filepath)

    if frontmatter.get("devto") is False:
        print(f"Skipping {filepath} (devto: false in frontmatter)")
        sys.exit(0)

    title = frontmatter.get("title", "").strip("\"'")
    tags = frontmatter.get("tags", [])

    post = publish(token, title, body, tags)
    print(f"Published: {post.get('url')}")


if __name__ == "__main__":
    main()
