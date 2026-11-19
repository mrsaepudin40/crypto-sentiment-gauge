---
name: crypto-sentiment-gauge
description: Score the sentiment of a supplied crypto news/social corpus per coin — bullish, bearish, or neutral — with cited phrases, trend over time, and hype and scam flags, using a transparent word lexicon. It never predicts a price.
summary: Score crypto sentiment per coin from a supplied corpus, with cited phrases, trend, and hype and scam flags.
version: 1.0.0
tags:
  - crypto
  - sentiment
  - news
  - social
  - mood
  - analysis
  - risk
  - trading
keywords:
  - crypto sentiment
  - mood score
  - bullish bearish
  - news sentiment
  - social sentiment
  - hype detection
  - scam flags
use_cases:
  - Score the sentiment of supplied crypto news or social posts per coin
  - Track how sentiment moved across the first and second half of a corpus
  - Flag hype and scam wording in a crypto corpus before acting on it
---

# Crypto Sentiment Gauge

Score the sentiment of a crypto news or social corpus the trader
supplies — per coin, from −100 to +100 — with the exact phrases
that moved the score, how the mood moved across the corpus, and
hype and scam flags. Every number is recomputable from the corpus
with the transparent lexicon in `reference/sentiment-rules.md`.

This skill does NOT predict prices. Sentiment is not price
direction: a bullish crowd can be wrong, a bearish crowd can be
early, and a loud minority can look like consensus. It scores
only the corpus it was given, and it never places an order.

Use this skill when the user asks how the mood reads for a coin,
whether sentiment is rising or falling across a set of posts, or
whether a corpus is full of hype or scam wording.

## The corpus

The trader supplies a corpus JSON file in the format in
`reference/sentiment-rules.md`. Required: an `items` list, each
item with a `text` field. Optional: a top-level `coin`, a per-item
`coin` (for multi-coin corpora), and a `source` note. The agent
must say where the corpus came from and what window it covers —
the gauge cannot check that, and it says so in every report.

## Run the gauge

```bash
python3 scripts/gauge.py --input corpus.json --output gauge.json
```

The script is dependency-free Python 3, standard library only, no
network, no credentials. It reads only the corpus file given on
the command line and writes only the report file. Read the report
back and present it to the trader in this order:

1. The score and label per coin, in plain words.
2. The counts: positive, negative, and neutral items, and the
   weighted hit totals the score came from.
3. The cited phrases — the exact short phrases that moved the
   score — so the trader can check the reading.
4. The trend: first-half versus second-half average, rising,
   falling, or flat.
5. The hype and scam flags, with the items that raised them.
6. The honest limit: sentiment is not price direction.

## How the score works

Each item's score is the sum of its matched positive word weights
minus its matched negative word weights. A coin's score is
100 × (positive hits − negative hits) ÷ (positive hits + negative
hits), rounded, in the range −100 to +100. Labels: +50 and above
strongly bullish, +20 to +49 bullish, −19 to +19 neutral, −20 to
−49 bearish, −50 and below strongly bearish. The full lexicon,
the trend method, and the flag rules are in
`reference/sentiment-rules.md`.

## Rules for the agent

- Never score text the trader did not supply. A corpus of three
  posts is a corpus of three posts — say so, do not pad it.
- Never present a score as a price call. A score of +80 is a mood
  reading, not a reason to buy.
- Never hide the cited phrases. If the score rests on two words
  in one post, the trader must see that.
- Never call a hype or scam flag a verdict. A flag means the
  wording matches a pattern; the project behind it may still be
  legitimate, and a clean corpus may still be a scam.
- When the corpus mixes coins, report each coin separately.
  Never average coins into one score.

## Honest limits

The gauge reads only the supplied corpus; it cannot verify that
the corpus is representative, that the sources are real, or that
the mood will last. Hype and scam flags are pattern matches, not
verdicts. A past score says nothing about the next post.
