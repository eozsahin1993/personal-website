---
layout: post
title: "Publishing to npm Without Storing a Token"
categories:
  - Posts
tags:
  - npm
  - DevOps
---

When setting up CI/CD for [RagPack](https://github.com/eozsahin1993/ragpack), I wanted to publish to npm from GitHub Actions without storing a long-lived token as a secret. Tokens are annoying: they expire, need rotating, and if they leak you have a problem. 

Turns out there is already a feature in npm called **trusted publishing**, and it uses OIDC to let GitHub Actions authenticate directly with npm, no `NPM_TOKEN` required.

Here's what the setup actually looks like, including a few things the docs gloss over.

### How it works

Instead of a static token, GitHub Actions gets a short-lived OIDC token for each run. npm verifies that token came from the specific repo and workflow you authorized, then allows the publish. The token is scoped to that single job and can't be extracted or reused.

### Requirements

- npm CLI **11.5.1** or later
- Node **22.14.0** or later

If you pin an older Node version in your workflow, it won't work.

### Step 1: Configure trusted publishers on npmjs.com

This is the step the docs bury. You need to do this **per package**, on the package's own settings page, not in your account settings.

Go to `npmjs.com/package/<your-package>`, click the **Settings** tab, find **Publishing access**, and add a trusted publisher. For GitHub Actions:

- **Owner:** your GitHub username or org
- **Repository:** the repo name
- **Workflow:** the filename of your workflow (e.g. `publish-cli.yml`)
- **Environment:** leave blank unless you use GitHub environments

If you have multiple packages in the same monorepo (like I do, a CLI and a JS SDK), you repeat this for each package but point to the respective workflow file.

### Step 2: Update your workflow

You need `id-token: write` permission so the job can request an OIDC token. Then just run `npm publish --provenance --access public`, no `NODE_AUTH_TOKEN`, no secrets.

```yaml
name: Publish CLI

on:
  push:
    tags: ['cli/v*.*.*']

jobs:
  publish:
    runs-on: ubuntu-latest
    permissions:
      id-token: write
      contents: read
    defaults:
      run:
        working-directory: cli

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: 22
          registry-url: https://registry.npmjs.org

      - run: npm ci

      - run: npm publish --provenance --access public
```

That's it. No secrets to manage.

### Keeping tags in sync with package.json

One gotcha with tag-triggered workflows: the tag is just a trigger. Nothing enforces that `cli/v0.2.0` matches `"version": "0.2.0"` in `package.json`. They can silently drift.

I added a version check step that fails the job early if they don't match:

```yaml
- name: Verify version matches tag
  run: |
    PKG_VERSION="v$(node -p "require('./package.json').version")"
    TAG_VERSION="${GITHUB_REF_NAME#cli/}"
    if [ "$PKG_VERSION" != "$TAG_VERSION" ]; then
      echo "Version mismatch: package.json=$PKG_VERSION tag=$TAG_VERSION"
      exit 1
    fi
```

The release process then becomes: bump the version in `package.json`, commit, push, tag. If the version and tag don't match you get a clear error instead of publishing the wrong version silently.

### First publish

One thing worth knowing: trusted publishing works for subsequent publishes but the package still needs to exist on npm first. For a brand new package, do a one-time manual publish from your machine:

```bash
npm login
npm publish --access public
```

After that, the CI workflow handles everything.

### The result

The packages page on npm now shows a provenance badge. Users can see exactly which commit and GitHub Actions run produced each version. And there are no tokens to rotate, expire, or accidentally commit.

Happy coding!
