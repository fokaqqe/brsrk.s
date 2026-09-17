"""JSON persistence for decks."""

import json
import os


def save_deck(path, cards):
    with open(path, "w", encoding="utf-8") as deck_file:
        json.dump([card.id for card in cards], deck_file, ensure_ascii=False)


def load_deck(path, all_cards):
    if not os.path.exists(path):
        return []

    with open(path, "r", encoding="utf-8") as deck_file:
        card_ids = json.load(deck_file)

    cards_by_id = {card.id: card for card in all_cards}
    counts = {}
    result = []
    for card_id in card_ids:
        card = cards_by_id.get(card_id)
        if card is None:
            continue
        max_count = 5 if "орда" in (card.ability or "").lower() else 3
        if counts.get(card_id, 0) < max_count:
            result.append(card)
            counts[card_id] = counts.get(card_id, 0) + 1
    return result
