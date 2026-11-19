# Sentiment rules

## Corpus schema

```json
{
  "coin": "BTC",
  "window": "2026-11-19",
  "source": "agent-supplied headlines from X and news sites",
  "items": [
    {"text": "Bitcoin rally continues as ETF inflows surge.", "coin": "BTC"},
    {"text": "Traders fear a dump after the exchange hack."}
  ]
}
```

- `items` (required): a non-empty list. Each item needs a
  non-empty `text` string.
- `coin` (optional, top-level): the coin the corpus is about.
  A per-item `coin` overrides it; items without one use the
  top-level coin, or `UNKNOWN`.
- `window` and `source` (optional): free text the agent uses to
  say what the corpus covers and where it came from. The gauge
  does not verify either.

## The lexicon and the scoring math

The lexicon lives in `scripts/gauge.py` and is part of the skill:
positive words, negative words, hype markers, urgency words, and
scam patterns. Matching is case-insensitive, whole-word for single
words, substring for phrases. Each occurrence counts.

- Positive words carry weight +1, strong positives +2
  (`breakout`, `record high`, `all-time high`, `bull run`).
- Negative words carry weight −1, strong negatives −2
  (`crash`, `dump`, `plunge`, `selloff`, `hack`, `exploit`,
  `rug`, `collapse`, `bankrupt`).
- An item's score is the sum of its matched positive weights
  minus its matched negative weights. Example: "Bitcoin rally
  continues as ETF inflows surge" matches `rally` (+1), `etf`
  (+1), `inflows` (+1), `surge` (+1) = item score +4.
- A coin's score is `round(100 * (pos - neg) / (pos + neg))`
  where `pos` and `neg` are the coin's total weighted positive
  and negative hits. With no hits at all the score is 0. The
  range is −100 to +100.
- Labels: +50 and above strongly bullish, +20 to +49 bullish,
  −19 to +19 neutral, −20 to −49 bearish, −50 and below
  strongly bearish.
- Cited phrases: up to 5 matched phrases per coin, each with its
  weight, the item index, and a short exact excerpt, so any
  reader can re-check the score from the corpus.

## Trend

Items are read in corpus order (chronological as supplied). The
corpus is split into a first half and a second half; the trend is
the second half's average item score minus the first half's.
Rising when the delta is +1.0 or more, falling when −1.0 or less,
flat otherwise. Fewer than 4 items: no trend is computed, and the
report says so.

## Hype flags

Hype markers are counted separately and never added to the score:
superlatives (`moon`, `100x`, `1000x`, `rocket`, `parabolic`,
`insane`, `explode`, `lambo`, `gem`, `to the moon`,
`generational`), urgency words (`now`, `hurry`, `last chance`,
`don't miss`, `act fast`, `limited time`, `before it's too
late`, `buy now`), and shouting (words of 3+ letters in ALL
CAPS). An item is a hype item at 3 or more markers. A coin is
hype-flagged when 25% or more of its items are hype items. The
report lists the hype items and their share.

## Scam flags

Scam patterns are case-insensitive regexes over the item text:
send-X-get-2X, double-your-money, guaranteed returns, giveaways
that ask the reader to send coins, celebrity giveaways, and
verify-your-wallet-then-send wording. Any matching item raises
the coin's scam flag, and the report lists the item index and the
pattern name. A flag is a pattern match, not a verdict.

## Honest limits

- The gauge scores only the supplied corpus. It cannot tell
  whether the corpus is representative, cherry-picked, or fake.
- A loud minority can look like consensus: 20 posts from one
  account count the same as 20 posts from 20 accounts unless the
  agent says otherwise.
- Hype and scam flags are pattern matches. Hype wording can
  appear in honest excitement; a clean corpus can still be a
  scam.
- Sentiment is not price direction. A bullish score is a mood
  reading, not a buy signal.
