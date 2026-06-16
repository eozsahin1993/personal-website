---
layout: post
title: "Using pg_cron for Match Notifications"
categories:
  - Posts
tags:
  - Postgres
---

While working on my side project, [worldcuppicks.co](https://www.worldcuppicks.co) (a site where you predict World Cup games), I needed to add web push notifications. To build this, I used a Postgres extension I'd been wanting to try: `pg_cron`. It ended up doing more than I expected, so I wanted to write about it.

`pg_cron` lets you schedule cron jobs directly inside the database. World Cup matches kick off on a fixed schedule, and I wanted a notification to fire 10 minutes before each one. I could have wired this up externally, with something like AWS EventBridge, but doing it inside Postgres turned out to be much simpler.

### Why pg_cron?

Deciding whether to fire a notification, and what to put in it, depends entirely on the match schedule, which already lives in the database. An external scheduler would just turn around and hit an API to ask the database the same question. So instead of standing up a separate service for that, it only takes a few lines of SQL:

```sql
CREATE EXTENSION IF NOT EXISTS pg_cron;

SELECT cron.schedule(
  'notify-upcoming-matches',
  '50 * * * *',
  $$
    INSERT INTO match_notifications (match_id, status, scheduled_at)
    SELECT
      id, 'scheduled', now()
    FROM matches
    WHERE
      match_date BETWEEN now() AND now() + interval '20 minutes'
      AND id NOT IN (SELECT match_id FROM match_notifications)
    ON CONFLICT DO NOTHING;
  $$
);
```

This job fires at exactly the 50th minute of every hour and inserts a row into `match_notifications` for each match that's about to kick off and hasn't been notified yet. From there, all you need is a database webhook on INSERTs to that table, which calls a lambda/edge function to actually send the push notification.

Normally, scheduling something like this needs separate infrastructure, but with pg_cron it lives entirely inside Postgres. Happy coding!
