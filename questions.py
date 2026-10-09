"""Trivia questions by Tier, drawn without repeats within one Expedition."""

import json
from pathlib import Path


TIERS = ("easy", "medium", "hard")
FALLBACK = [
    {"question": "What is 2 + 2?", "answer": "4"},
    {"question": "What color is the sky on a clear day?", "answer": "blue"},
    {"question": "Which language is this game written in?", "answer": "python"},
]


def load_tier(tier):
    """Return (questions, used_fallback) for a Tier's question file."""
    try:
        data = json.loads((Path(__file__).parent / f"{tier}_questions.json").read_text(encoding="utf-8"))
        if isinstance(data, list) and data:
            return data, False
    except (OSError, ValueError):
        pass
    return FALLBACK, True


def is_correct(question, answer):
    return answer.strip().lower() == question["answer"].strip().lower()


class QuestionBank:
    """One bank per Expedition: a Tier's pool refills only once exhausted."""

    def __init__(self):
        loaded = {tier: load_tier(tier) for tier in TIERS}
        self.tiers = {tier: questions for tier, (questions, _) in loaded.items()}
        self.fallback = any(fallback for _, fallback in loaded.values())
        self.unused = {tier: [] for tier in TIERS}

    def draw(self, tier, rng):
        pool = self.unused[tier]
        if not pool:
            pool.extend(self.tiers[tier])
        return pool.pop(rng.randrange(len(pool)))
