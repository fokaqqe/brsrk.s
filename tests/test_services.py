import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from domain.filters import matches_advanced_filters, matches_main_filters, sort_cards
from services.deck_stats import format_deck_stats
from services.deck_storage import load_deck, save_deck


def card(card_id, name="Card", cost="2", ability=""):
    return SimpleNamespace(
        id=card_id, name=name, cost=cost, ability=ability, element="Огонь",
        health="10", moves="2", attack="1-2-3", class_="Воин",
        set_name="Base", cardtype="Существо", rarity="Обычная",
        datetime_updated=None, magic_resist=0, spell_resist=0,
        lightning_resist=0,
    )


class ServiceTests(unittest.TestCase):
    def test_deck_round_trip_and_copy_limit(self):
        cards = [card(1), card(2)]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "deck.json"
            save_deck(path, [cards[0], cards[0], cards[0], cards[0], cards[1]])
            loaded = load_deck(path, cards)
        self.assertEqual([item.id for item in loaded], [1, 1, 1, 2])

    def test_filters_and_sort(self):
        settings = {"cost_from": 2, "cost_to": 2, "cost_type": "Все", "class_text": "воин", "elements": [], "sets": [], "cardtypes": [], "rarities": []}
        self.assertTrue(matches_main_filters(card(1), settings))
        self.assertFalse(matches_main_filters(card(2, cost="3"), settings))
        self.assertFalse(matches_advanced_filters(card(1), ["magic_resist"]))
        self.assertEqual([item.id for item in sort_cards([card(2), card(1)], "ID")], [1, 2])

    def test_stats_for_empty_deck(self):
        self.assertEqual(format_deck_stats([]), "Колода пуста")


if __name__ == "__main__":
    unittest.main()
