---
layout: post
title: "TIL: Finding the Buggy Commit with Git Bisect"
categories:
  - Posts
tags:
  - Today I learned
  - React
  - Web
---

On a Thursday night right before the 4th of July, I was going through PRs when I suddenly realized that our standard charts had their top padding completely missing. Usually, this would be easy to spot, but our web code is pretty complicated, so in the first 15 minutes, we couldn't figure out the problem.

I thought, there must be an easier way to spot this issue than going through commits one by one. That's when I discovered the magical tool called `git bisect`.

### Git Bisect

How `git bisect` works is brilliant, and it probably saved me at least an hour. You start by identifying a commit in the history where everything was working correctly, and a bad commit (usually the current one) where the problem exists. Internally, it uses a binary search to find the faulty commit, so you don't have to check each commit individually.

For the geeks out there, binary search has a runtime complexity of **O(log n)** instead of the linear **O(n)** you'd get going commit by commit. So if I had 100 commits, with binary search, it would take me around \(\log_2 100 \approx 6.6\) attempts to find the culprit — pretty awesome!

### In action

Start the git bisect process:
```bash
git bisect start
```

Mark the current commit as bad:
```bash
git bisect bad
```

Mark a known good commit in history (for me, this was a commit from 4 days ago):
```bash
git bisect good <commit-hash>
```

Git will now check out a commit halfway between the good and bad commits and ask you to test it.

After testing, tell git whether this commit is good or bad:
```bash
git bisect good <commit-hash>
```
 or
```bash
git bisect bad <commit-hash>
```

Repeat this process until git finds the exact commit that introduced the issue.

In my case, I had 33 commits to check, and it took only 5 attempts to find the bad one — much faster than testing all commits one by one!

That's all for today. Happy coding!


