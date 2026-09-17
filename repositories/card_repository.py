"""Card repository boundary for the application."""

from repositories.db_manager import DBManager


class CardRepository:
    def __init__(self):
        self._database = DBManager()

    def get_all(self):
        return self._database.get_all_cards()

    def get_all_cards(self):
        """Compatibility method used by the current UI during migration."""
        return self.get_all()

    def update_status(self, card_id, have):
        self._database.update_card_status(card_id, have)

    def update_card_status(self, card_id, have):
        return self.update_status(card_id, have)

    def close(self):
        self._database.close()
