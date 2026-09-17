"""Filtering and sorting rules for the card catalogue."""

import re
from datetime import datetime


def matches_advanced_filters(card, active_filters):
    if not active_filters:
        return True

    for filter_key in active_filters:
        if filter_key == "lightning_resist":
            if not (getattr(card, "lightning_resist", 0) or getattr(card, "magic_resist", 0)):
                return False
        elif filter_key == "spell_resist":
            if not (getattr(card, "spell_resist", 0) or getattr(card, "magic_resist", 0)):
                return False
        elif getattr(card, filter_key, 0) != 1:
            return False
    return True


def matches_main_filters(card, settings):
    cost_from = settings.get("cost_from", 0)
    cost_to = settings.get("cost_to", 10)
    cost_type = settings.get("cost_type", "Все")

    if cost_from != 0 or cost_to != 10 or cost_type != "Все":
        match = re.match(r"(\d+)\s*\((Серебро|Золото)\)", card.cost or "")
        if match:
            cost_num, card_cost_type = int(match.group(1)), match.group(2)
        else:
            match = re.match(r"(\d+)", card.cost or "")
            cost_num = int(match.group(1)) if match else None
            card_cost_type = None

        if cost_num is None or not cost_from <= cost_num <= cost_to:
            return False
        if cost_type != "Все" and card_cost_type != cost_type:
            return False

    if settings.get("class_text") and settings["class_text"].lower() not in (getattr(card, "class_", "") or "").lower():
        return False
    if settings.get("elements") and card.element not in settings["elements"]:
        return False
    if settings.get("sets") and card.set_name not in settings["sets"]:
        return False
    if settings.get("cardtypes"):
        card_type = getattr(card, "cardtype", "") or ""
        if not any(value in card_type for value in settings["cardtypes"]):
            return False
    if settings.get("rarities") and getattr(card, "rarity", "") not in settings["rarities"]:
        return False
    return True


def _date_key(card):
    value = getattr(card, "datetime_updated", None)
    if not value or not isinstance(value, str):
        return datetime(1900, 1, 1)
    try:
        return datetime.fromisoformat(value.split(".")[0].replace("Z", ""))
    except (TypeError, ValueError):
        return datetime(1900, 1, 1)


def sort_cards(cards, sort_choice, descending=False):
    result = list(cards)
    if sort_choice == "ID":
        key = lambda card: card.id
    elif sort_choice == "Название":
        key = lambda card: card.name or ""
    elif sort_choice == "Стоимость":
        key = lambda card: int(re.match(r"(\d+)", card.cost or "0").group(1)) if re.match(r"(\d+)", card.cost or "0") else 0
    elif sort_choice == "Время добавления":
        key = lambda card: (_date_key(card), card.id)
    else:
        return result
    result.sort(key=key, reverse=descending)
    return result
