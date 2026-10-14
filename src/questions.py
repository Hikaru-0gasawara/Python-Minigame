"""Trivia questions by Tier, drawn without repeats within one Expedition."""

import json
from pathlib import Path
import re
import unicodedata

import lang


TIERS = ("easy", "medium", "hard")
LETTERS = "ABCD"
BANKS = Path(__file__).resolve().parent.parent / "assets" / "questions"
FALLBACK = [
    {"question": "What is 2 + 2?", "answer": "4"},
    {"question": "What color is the sky on a clear day?", "answer": "blue"},
    {"question": "Which language is this game written in?", "answer": "python"},
]


def load_tier(tier):
    """Return (questions, used_fallback) for a Tier's question file in the chosen language."""
    try:
        data = json.loads((BANKS / lang.current / f"{tier}.json").read_text(encoding="utf-8"))
        if isinstance(data, list) and data:
            return data, False
    except (OSError, ValueError):
        pass
    return FALLBACK, True


def _fold(text):
    """What must match in an answer: not case, accents, the decimal mark, or a hyphen between words."""
    text = unicodedata.normalize("NFD", text.strip().lower().replace(",", "."))
    return re.sub(r"(?<=\w)-(?=\w)", " ", "".join(c for c in text if not unicodedata.combining(c)))


def is_correct(question, answer):
    """A multiple-choice Question (one with "options") also takes the letter of the right option."""
    options = question.get("options", ())
    letter = answer.strip().upper()
    if len(letter) == 1 and letter in LETTERS[:len(options)]:
        answer = options[LETTERS.index(letter)]
    return _fold(answer) == _fold(question["answer"])


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
