# crypto-sentiment-gauge

[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Python 3](https://img.shields.io/badge/python-3-blue)](scripts/gauge.py)
[![API key: not required](https://img.shields.io/badge/API%20key-not%20required-brightgreen)](reference/sentiment-rules.md)

Score the sentiment of a supplied crypto news/social corpus per
coin — bullish, bearish, or neutral, with the exact phrases behind
the score, the mood's trend over time, and hype/scam flags.

This skill does NOT predict prices. Sentiment is not price
direction. The gauge only judges the corpus it was given: it
cannot tell whether the corpus is representative or cherry-picked,
a loud minority can look like consensus, and the hype/scam flags
are pattern matches, not verdicts. Every number is recomputable
from the corpus with the transparent lexicon in `scripts/gauge.py`.

## Run the gauge

```bash
python3 scripts/gauge.py --input corpus.json --output report.json
```

Dependency-free Python 3, standard library only, no network, no
credentials. It reads only the corpus file given on the command
line and writes only the report file.

## Files

- `SKILL.md` — the skill instructions
- `scripts/gauge.py` — the sentiment gauge
- `reference/sentiment-rules.md` — corpus schema, the lexicon and
  scoring math, trend method, hype/scam flag rules, honest limits
- `examples/` — invented corpora and the reports the script
  generates from them (bullish BTC, bearish/mixed ETH, hype- and
  scam-laden MOONX)

## Honest limits

A score built on very few lexicon hits is volatile — the report
always shows the hit counts so the trader can see how thin the
evidence is. Past sentiment says nothing about the next price move.
