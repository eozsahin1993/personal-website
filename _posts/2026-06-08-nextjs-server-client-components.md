---
layout: post
title: "TIL: Server vs Client Components in Next.js"
categories:
  - Posts
tags:
  - Today I learned
  - Next.js
  - React
---

For [worldcuppick.co](https://www.worldcuppick.co), my World Cup prediction site, I used Next.js for the frontend. It comes with file based routing and built in image optimization, and the App Router makes data fetching simple. What I didn't realize until I started building real pages was how much of the app could ship with zero client side JavaScript, because of how Server and Client Components work.

Coming from a React background where everything renders in the browser, my first instinct was to add `"use client"` to every file out of habit. Today I learned that's the wrong default, so I wanted to write about why, using a couple of components from the app.

### Server Components by default

Here's the page that lists a user's picks:

```tsx
export default async function PicksPage() {
  const [translate, user] = await Promise.all([getTranslations("picks"), getUser()]);
  if (!user) redirect("/");

  const [predictions, completedMatchCount] = await Promise.all([
    getUserPredictions(user.userId),
    getCompletedMatchCount(),
  ]);

  // ...compute stats from predictions...

  return (
    <div>
      <Heading>{translate("heading")}</Heading>
      <PicksStatsBanner stats={stats} />
      <PredictionList predictions={upcoming} />
    </div>
  );
}
```

No `useEffect`, no loading state, no client side data fetching library. It's an `async` function that awaits the data it needs and renders. This is the default for every component in the App Router unless you say otherwise. It runs on the server, and none of this code gets sent to the browser at all.

### Only the interactive part needs to be a Client Component

The match card is where this really clicked for me. A card shows team flags, localized names, the score, and a voting widget. Only one of those things is actually interactive: the voting widget needs to hold state for the current pick and listen for live score updates.

So `MatchCard` stays a Server Component. It resolves translations, locale, and country names, then renders the static shell:

```tsx
export default async function MatchCard(props: MatchCardModel) {
  const [t, locale, localizedRound] = await Promise.all([
    getTranslations("matchCard"),
    getLocale(),
    localizeRound(props.round),
  ]);

  return (
    <div>
      <TeamDisplay team={props.homeTeam} ... />
      <MatchCardScoreClient matchId={props.matchId} ... />
      <TeamDisplay team={props.awayTeam} ... />
      <MatchCardClient matchId={props.matchId} ... />
    </div>
  );
}
```

And `MatchCardClient` only owns the part that actually needs to run in the browser: local state for the pick, a realtime subscription for live score updates, and the click handlers:

```tsx
"use client";

export default function MatchCardClient({ matchId, homeTeam, awayTeam, initialPick, ... }: Props) {
  const [pick, setPick] = useState<Pick | null>(initialPick);
  const { status, home_points, draw_points, away_points } = useMatchesRealtime(matchId, { ... });

  async function handlePick(newPick: Pick) {
    setPick(newPick);
    await submitPrediction(matchId, newPick);
  }

  return votingOpen && !pick
    ? <VotingSelector onPick={handlePick} ... />
    : <VotingSummary pick={pick} ... />;
}
```

Everything above the `MatchCardClient` part (the flags, the translated team names, the round label) gets rendered to HTML on the server and never needs to be re run or hydrated as JavaScript. Only the voting widget ships JS to the browser.

### Why this matters

A few things became obvious once I started thinking about this split instead of defaulting to client everywhere:

- **Less JS shipped.** A page full of match cards mostly ships HTML, and the JS bundle only includes the bits that actually need interactivity. Since Server Component code never goes to the client, its dependencies don't get bundled either.
- **No hydration cost.** Client Components have to be downloaded, parsed, executed, and hydrated before they're interactive. Server Components skip all of that since they're already just HTML by the time they reach the browser.
- **Simpler data fetching.** Server Components can just await your data layer directly, so there's no loading spinners or client side fetch waterfalls for content that doesn't change per interaction.
- **Real content for crawlers.** The match cards and picks are real HTML in the response, not something that only shows up after JS runs, which is better for SEO and link previews.
- **Caching.** Server rendered output can be cached at the route level or at the CDN, so repeat visits don't redo the same data fetch and render every time.

For every component, I now ask whether it actually needs to run in the browser instead of assuming it does. Translations, formatting, and static markup almost never do.

Happy coding!
