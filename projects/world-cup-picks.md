---
layout: page
title: World Cup Picks
permalink: /projects/world-cup-picks/
---

<div style="display: flex; gap: 12px; align-items: flex-start; flex-wrap: wrap;">
  <img src="{{ "/assets/images/projects/world-cup-picks-web.png" | relative_url }}" alt="World Cup Picks web view" style="max-width: 100%; flex: 2 1 320px; border-radius: 8px;" />
  <img src="{{ "/assets/images/projects/world-cup-picks-mobile.png" | relative_url }}" alt="World Cup Picks mobile view" style="max-width: 100%; flex: 1 1 160px; border-radius: 8px;" />
</div>

Predict FIFA World Cup 2026 match results, compete on leaderboards, and see how your picks stack up against friends.

I built this as a side project to predict World Cup match outcomes with friends, and to get hands on with a few things I'd been wanting to try: the Next.js App Router, Supabase, and scheduling work directly from Postgres instead of bolting on external infrastructure.

### Live site

[worldcuppicks.co](https://www.worldcuppicks.co)

### Features

- No login required, just a randomly generated username to get started
- Custom leaderboards to compete with friends, plus head-to-head views
- Global realtime fan pulse showing how everyone is picking each match
- Points awarded based on real match odds, so picking an upset pays off more
- Push notifications so you don't miss a kickoff
- Live score and pick updates as matches play out
- Mobile friendly
- Multi language support
- Admin dashboard for setting up matches and entering scores

### Fun stats

- Users played: 76
- Matches predicted: 1,124
- Custom ladders created: 7
- Total notifications sent: 17

### Tech stack

- **Next.js** (App Router) for the frontend, with Server Components doing most of the rendering and Client Components reserved for the interactive bits like voting and live score updates.
- **Supabase** for the database, auth, and Realtime subscriptions that push live score and pick updates to the UI as matches play out.
- **Supabase Edge Functions** to send the actual push notifications, triggered by a database webhook.
- **next-intl** for multi language support.
- **Vercel** for hosting, with Sentry for error tracking and Vercel Analytics/Speed Insights for monitoring.

### More on how it's built

A couple of posts that go deeper into specific decisions on this project:

- [Using pg_cron for Match Notifications]({% post_url 2026-06-16-postgres-extensions %})
- [TIL: Server vs Client Components in Next.js]({% post_url 2026-06-08-nextjs-server-client-components %})
