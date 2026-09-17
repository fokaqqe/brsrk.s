"""Mutable state shared by application-level controllers."""

from dataclasses import dataclass, field


@dataclass
class AppState:
    cards: list = field(default_factory=list)
    filtered_cards: list = field(default_factory=list)
    deck_cards: list = field(default_factory=list)
    main_filter_settings: dict = field(default_factory=dict)
    active_advanced_filters: list = field(default_factory=list)
