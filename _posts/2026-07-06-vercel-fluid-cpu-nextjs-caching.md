---
layout: post
title: "Cutting Vercel Fluid CPU with Next.js Server-Side Caching"
categories:
  - Posts
tags:
  - Next.js
  - Vercel
  - Web
---

Got an email from Vercel about reaching limits and checked to see Fluid Active CPU spiking for [worldcuppicks.co](https://www.worldcuppicks.co). Obviously I don't want to go to premium, so I implemented certain measures to bring it down. We are in the knockout rounds now, so I wanted to get it sorted before things got worse.

### First identification

Going to the Vercel Observability tab, I was able to see which page was causing the heavy load. The home page function was clocking nearly 3 minutes of active CPU time per billing window while every other route measured in seconds. That pointed me straight at the problem: the home page was doing two full database fetches on every single visit, for every user, with no caching in between.

```ts
// This ran on every page visit, for every user
const [matches, predictions] = await Promise.all([
  getAllMatches(),
  getAllMatchPredictions(),
]);
```

`getAllMatches` joins across three tables. `getAllMatchPredictions` pulls aggregate pick stats. Both were uncached, so every visit hit the database from scratch.

The second culprit was Sentry. I had it configured with a `tunnelRoute` that proxies Sentry events through a Vercel function at `/monitoring`. Every page load was generating an extra function invocation. I disabled Sentry entirely for now and that brought the baseline down.

### The fix: unstable_cache

Next.js ships a function called `unstable_cache` that wraps any async function with a server-side cache. The result is shared across all users and all requests, not per session. The first request after a cache miss hits the database, and every subsequent request gets the cached result.

For matches I set `revalidate: false`, meaning the cache never expires on a timer:

```ts
export const getAllMatches = unstable_cache(
  async (): Promise<Match[]> => {
    const supabase = getOrCreateAdminClient();
    const { data } = await supabase
      .from("matches")
      .select(`*, home_team:teams!home_team_id(...), away_team:teams!away_team_id(...)`)
      .order("match_date", { ascending: true });
    return (data as Match[]) ?? [];
  },
  ["all-matches"],
  { revalidate: false, tags: ["matches"] }
);
```

Match data only changes when I update it from the admin panel, so a time-based TTL adds nothing. The admin server action calls `revalidateTag("matches")` the moment a match is saved, which busts the cache immediately:

```ts
const { error } = await supabase.from("matches").update(update).eq("id", matchId);
if (error) throw new Error("Failed to update match");
revalidatePath("/admin");
revalidateTag("matches");
revalidateTag("predictions");
```

For prediction stats I went with a one-hour TTL as a fallback:

```ts
export const getAllMatchPredictions = unstable_cache(
  async (): Promise<MatchPredictionStats[]> => {
    const supabase = getOrCreateAdminClient();
    const { data } = await supabase.from("match_predictions").select("*");
    return (data ?? []) as MatchPredictionStats[];
  },
  ["all-match-predictions"],
  { revalidate: 3600, tags: ["predictions"] }
);
```

### Why stale prediction stats are fine

The obvious concern is that cached prediction percentages go stale. Won't someone loading the page see wrong crowd percentages?

But the crowd percentage bar uses a Supabase realtime subscription on the client. The moment a pick is submitted, Supabase pushes the updated row to every connected browser over a WebSocket. The cached server data is only used for the initial SSR render. Within milliseconds of hydration, realtime takes over.

The user's own pick is handled via optimistic local state, so it's instant regardless:

```tsx
async function handlePick(newPick: Pick) {
  setPick(newPick); // instant, before the server action returns
  await submitPrediction(matchId, newPick);
}
```

### The key insight

`unstable_cache` is shared across all requests on the server, not per session. Without it, every page visit queries the database for the exact same data. With it, it's one query until the cache is busted. For match data that only changes when I update it from the admin panel, that's the right trade.

Happy coding!
