"""Domain representation of a card."""

from dataclasses import dataclass


@dataclass(init=False)
class Card:
    def __init__(self, data):
        self.id = data["id"]
        self.name = data["name"]
        self.rarity = data["rarity"]
        self.set_name = data["set_name"]
        self.number = data["number"]
        self.artist = data["artist"]
        self.element = data["element"]
        self.cost = data["cost"]
        self.health = data["health"]
        self.moves = data["moves"]
        self.attack = data["attack"]
        self.ability = data["ability"]
        self.image_path = data["image_path"]
        self.have = data.get("have", 0)
        self.class_ = data.get("class", "")
        self.class_input = data["class"]
        self.cardtype = data["cardtype"]
        self.datetime_updated = data.get("datetime_updated")

        for field in (
            "poison_resist", "throw_resist", "shoot_resist", "spell_resist",
            "lightning_resist", "magic_resist", "flying_resist", "defense_exp",
            "attack_exp", "shooting_exp", "regeneration", "armor",
            "direct_strike", "stability",
        ):
            setattr(self, field, self._to_flag(data.get(field, 0)))

    @staticmethod
    def _to_flag(value):
        return 1 if value else 0
