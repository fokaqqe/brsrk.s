"""Deck summary calculations."""

import re


def format_deck_stats(cards):
    if not cards:
        return "Колода пуста"

    total = len(cards)
    elements = {}
    sum_cost = sum_health = sum_speed = 0
    attack_totals = [0, 0, 0]
    attack_count = 0

    for card in cards:
        if card.element:
            elements[card.element] = elements.get(card.element, 0) + 1
        cost_match = re.match(r"(\d+)", card.cost or "")
        if cost_match:
            sum_cost += int(cost_match.group(1))
        if card.health and str(card.health).isdigit():
            sum_health += int(card.health)
        if card.moves and str(card.moves).isdigit():
            sum_speed += int(card.moves)
        if card.attack:
            try:
                values = [int(value) for value in card.attack.split("-")]
                if len(values) == 3:
                    attack_totals = [left + right for left, right in zip(attack_totals, values)]
                    attack_count += 1
            except (TypeError, ValueError):
                continue

    average_cost = round(sum_cost / total, 2)
    average_health = round(sum_health / total, 2)
    average_speed = round(sum_speed / total, 2)
    average_attack = "0-0-0"
    if attack_count:
        average_attack = "-".join(str(round(value / attack_count, 2)) for value in attack_totals)

    element_text = ", ".join(f" {name}: {count}" for name, count in elements.items())
    return (f"Карт: {total} Стихии: {element_text}\n"
            f"Ср. стоимость: {average_cost} | HP: {average_health}\n"
            f"Ср. атака: {average_attack} | Скорость: {average_speed}")
