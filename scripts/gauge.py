#!/usr/bin/env python3
"""Crypto Sentiment Gauge: score the sentiment of a supplied crypto
news/social corpus per coin, with cited phrases, trend, and hype/scam
flags.

Dependency-free Python 3, standard library only. No network, no
credentials. Reads only the corpus file given with --input and writes
only the report file given with --output.

Scoring is transparent and recomputable: every lexicon word in
reference/sentiment-rules.md carries a weight. An item's score is the
sum of its matched positive weights minus its matched negative
weights. A coin's score is 100 * (pos - neg) / (pos + neg), in
[-100, +100]. Hype and scam markers are pattern matches, not
verdicts. Sentiment is not price direction.

Exit 0 on success. Exit 1 on a malformed corpus, with nothing
written.
"""

import argparse
import json
import re
import sys

NAME = "crypto-sentiment-gauge"

# Each entry: matched word/phrase -> weight. Counted per occurrence.
POSITIVE = {
    "bullish": 1, "rally": 1, "surge": 1, "surges": 1, "breakout": 2,
    "gains": 1, "gain": 1, "strong": 1, "strength": 1, "adoption": 1,
    "accumulation": 1, "accumulate": 1, "record high": 2,
    "all-time high": 2, "ath": 1, "recovery": 1, "recover": 1,
    "optimism": 1, "optimistic": 1, "confidence": 1, "inflows": 1,
    "buying": 1, "demand": 1, "growth": 1, "upgrade": 1,
    "partnership": 1, "approval": 1, "etf": 1, "bull run": 2,
}

NEGATIVE = {
    "bearish": 1, "crash": 2, "crashes": 2, "dump": 2, "dumps": 2,
    "plunge": 2, "selloff": 2, "sell-off": 2, "fear": 1, "panic": 1,
    "hack": 2, "hacked": 2, "exploit": 2, "rug": 2, "rugpull": 2,
    "collapse": 2, "bankrupt": 2, "bankruptcy": 2, "outflows": 1,
    "selling": 1, "weak": 1, "weakness": 1, "decline": 1, "drop": 1,
    "drops": 1, "fears": 1, "concern": 1, "concerns": 1, "lawsuit": 1,
    "ban": 1, "crackdown": 1,
}

# Hype markers: counted separately, never added to the score.
HYPE = {
    "moon": 1, "100x": 1, "1000x": 1, "rocket": 1, "parabolic": 1,
    "insane": 1, "explode": 1, "explodes": 1, "lambo": 1, "gem": 1,
    "to the moon": 1, "generational": 1,
}

URGENCY = {
    "now": 1, "hurry": 1, "last chance": 1, "don't miss": 1,
    "dont miss": 1, "act fast": 1, "limited time": 1,
    "before it's too late": 1, "buy now": 1,
}

# Scam patterns: regexes, case-insensitive. A match flags the item.
SCAM_PATTERNS = [
    (r"send\s+\d*\.?\d*\s*(eth|btc|bnb|usdt|sol)?\s*(and|to)?\s*get\s+2x",
     "send-X-get-2X"),
    (r"double your (crypto|eth|btc|money|investment)",
     "double-your-money"),
    (r"guaranteed (return|returns|profit|profits)",
     "guaranteed-returns"),
    (r"free giveaway.*send", "giveaway-asks-to-send"),
    (r"giveaway.*send.*(eth|btc|bnb|usdt|sol)", "giveaway-asks-to-send"),
    (r"elon musk.*giveaway", "celebrity-giveaway"),
    (r"verify your wallet.*send", "verify-wallet-send"),
    (r"send .* to (receive|get|claim) (double|2x)",
     "send-to-receive-double"),
]

HYPE_ITEM_THRESHOLD = 3      # hype markers in one item -> item is hype
HYPE_COIN_RATIO = 0.25       # share of hype items -> coin is hype-flagged
CAPS_WORD_MIN_LEN = 3        # shouting: words this long, all caps
CAPS_ITEM_THRESHOLD = 3      # shouting words in one item -> item is hype
TREND_MIN_ITEMS = 4
TREND_DELTA = 1.0


def fail(message):
    print(f"{NAME}: {message}", file=sys.stderr)
    sys.exit(1)


def count_matches(text, lexicon):
    """Return (weighted total, {entry: occurrences}) for a lexicon."""
    hits = {}
    for entry, weight in lexicon.items():
        pattern = r"\b" + re.escape(entry) + r"\b"
        n = len(re.findall(pattern, text))
        if n:
            hits[entry] = n
    total = sum(lexicon[e] * n for e, n in hits.items())
    return total, hits


def caps_shout_count(text):
    words = re.findall(r"[A-Za-z]{%d,}" % CAPS_WORD_MIN_LEN, text)
    return sum(1 for w in words if w.isupper())


def excerpt(text, phrase, width=60):
    low = text.lower()
    i = low.find(phrase.lower())
    if i < 0:
        return text[:width]
    start = max(0, i - 20)
    end = min(len(text), i + len(phrase) + 20)
    cut = text[start:end]
    return ("..." if start > 0 else "") + cut + ("..." if end < len(text) else "")


def score_item(item):
    text = item["text"].lower()
    pos, pos_hits = count_matches(text, POSITIVE)
    neg, neg_hits = count_matches(text, NEGATIVE)
    hype, hype_hits = count_matches(text, HYPE)
    urgency, _ = count_matches(text, URGENCY)
    caps = caps_shout_count(item["text"])
    scam = [name for pattern, name in SCAM_PATTERNS
            if re.search(pattern, text)]
    hype_markers = hype + urgency + caps
    return {
        "score": pos - neg,
        "pos": pos, "neg": neg,
        "pos_hits": pos_hits, "neg_hits": neg_hits,
        "hype_markers": hype_markers,
        "hype_hits": hype_hits,
        "caps": caps,
        "scam": scam,
        "is_hype": hype_markers >= HYPE_ITEM_THRESHOLD,
    }


def label(score):
    if score >= 50:
        return "strongly bullish"
    if score >= 20:
        return "bullish"
    if score <= -50:
        return "strongly bearish"
    if score <= -20:
        return "bearish"
    return "neutral"


def gauge_coin(coin, items):
    scored = []
    for idx, item in enumerate(items):
        r = score_item(item)
        r["index"] = idx
        r["text"] = item["text"]
        scored.append(r)
    total_pos = sum(r["pos"] for r in scored)
    total_neg = sum(r["neg"] for r in scored)
    denom = total_pos + total_neg
    score = round(100 * (total_pos - total_neg) / denom) if denom else 0
    n = len(scored)
    pos_items = sum(1 for r in scored if r["score"] > 0)
    neg_items = sum(1 for r in scored if r["score"] < 0)
    neu_items = n - pos_items - neg_items

    cited = []
    for r in scored:
        for entry, count in r["pos_hits"].items():
            cited.append({"phrase": entry, "weight": "+" + str(POSITIVE[entry]),
                          "item": r["index"],
                          "excerpt": excerpt(r["text"], entry)})
        for entry, count in r["neg_hits"].items():
            cited.append({"phrase": entry, "weight": "-" + str(NEGATIVE[entry]),
                          "item": r["index"],
                          "excerpt": excerpt(r["text"], entry)})
    cited = cited[:5]

    trend = None
    if n >= TREND_MIN_ITEMS:
        ordered = sorted(scored, key=lambda r: r["index"])
        half = n // 2
        first = ordered[:half]
        second = ordered[half:]
        first_avg = round(sum(r["score"] for r in first) / len(first), 2)
        second_avg = round(sum(r["score"] for r in second) / len(second), 2)
        delta = round(second_avg - first_avg, 2)
        if delta >= TREND_DELTA:
            direction = "rising"
        elif delta <= -TREND_DELTA:
            direction = "falling"
        else:
            direction = "flat"
        trend = {"first_half_avg": first_avg, "second_half_avg": second_avg,
                 "delta": delta, "direction": direction}
    else:
        trend = {"first_half_avg": None, "second_half_avg": None,
                 "delta": None, "direction": None,
                 "note": "Fewer than 4 items; no trend computed."}

    hype_items = [r["index"] for r in scored if r["is_hype"]]
    hype_flagged = len(hype_items) / n >= HYPE_COIN_RATIO if n else False
    scam_items = [{"item": r["index"], "patterns": r["scam"]}
                  for r in scored if r["scam"]]
    return {
        "coin": coin,
        "items": n,
        "score": score,
        "label": label(score),
        "positive_items": pos_items,
        "negative_items": neg_items,
        "neutral_items": neu_items,
        "positive_hits": total_pos,
        "negative_hits": total_neg,
        "cited_phrases": cited,
        "trend": trend,
        "hype": {"flagged": hype_flagged, "hype_items": hype_items,
                 "hype_item_share": round(len(hype_items) / n, 2) if n else 0},
        "scam": {"flagged": bool(scam_items), "items": scam_items},
    }


def main():
    parser = argparse.ArgumentParser(prog=NAME)
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    try:
        with open(args.input) as f:
            corpus = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        fail(f"cannot read corpus: {e}")

    if not isinstance(corpus, dict) or not isinstance(
            corpus.get("items"), list) or not corpus["items"]:
        fail("corpus has no items list, or the list is empty")

    default_coin = corpus.get("coin", "UNKNOWN")
    groups = {}
    order = []
    for item in corpus["items"]:
        if not isinstance(item, dict) or not isinstance(
                item.get("text"), str) or not item["text"].strip():
            fail("every corpus item needs a non-empty text field")
        coin = item.get("coin", default_coin)
        if coin not in groups:
            groups[coin] = []
            order.append(coin)
        groups[coin].append(item)

    coins = {coin: gauge_coin(coin, groups[coin]) for coin in order}
    report = {
        "coins": coins,
        "total_items": sum(len(v) for v in groups.values()),
        "note": ("Sentiment is not price direction. The score covers only "
                 "the supplied corpus; a loud minority can look like "
                 "consensus. Hype and scam flags are pattern matches, "
                 "not verdicts."),
    }
    with open(args.output, "w") as f:
        json.dump(report, f, indent=2)
        f.write("\n")
    for coin, g in coins.items():
        print(f"{coin}: score {g['score']} ({g['label']}), "
              f"{g['items']} items")


if __name__ == "__main__":
    main()
