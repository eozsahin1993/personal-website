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


def get_author_id(token):
    response = requests.get(
        "https://api.medium.com/v1/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    response.raise_for_status()
    return response.json()["data"]["id"]


def publish(token, author_id, title, content, tags):
    response = requests.post(
        f"https://api.medium.com/v1/users/{author_id}/posts",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        json={
            "title": title,
            "contentFormat": "markdown",
            "content": f"# {title}\n\n{content}",
            "tags": tags[:5],  # Medium max 5 tags
            "publishStatus": "public",
        },
    )
    response.raise_for_status()
    return response.json()["data"]


def main():
    if len(sys.argv) < 2:
        print("Usage: publish_to_medium.py <post-file>")
        sys.exit(1)

    filepath = sys.argv[1]
    token = os.environ.get("MEDIUM_TOKEN")
    if not token:
        print("MEDIUM_TOKEN not set")
        sys.exit(1)

    frontmatter, body = parse_post(filepath)

    if frontmatter.get("medium") is False:
        print(f"Skipping {filepath} (medium: false in frontmatter)")
        sys.exit(0)

    title = frontmatter.get("title", "").strip("\"'")
    tags = frontmatter.get("tags", [])

    author_id = get_author_id(token)
    post = publish(token, author_id, title, body, tags)
    print(f"Draft created: {post.get('url')}")


if __name__ == "__main__":
    main()
