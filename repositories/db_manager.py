from datetime import datetime
import sqlite3
from pathlib import Path

DB_FILE = Path(__file__).resolve().parents[1] / "data" / "cards.db"

class DBManager:
    def __init__(self):  
        self.conn = sqlite3.connect(DB_FILE)
        self.conn.row_factory = sqlite3.Row
        self.add_datetime_column_if_not_exists()
    
    def get_all_cards(self):
        rows = self.conn.execute("SELECT * FROM Cards ORDER BY id").fetchall()
        return [dict(row) for row in rows]
    
    def update_card_status(self, card_id, have: int):
        """
        Обновляет количество карт и устанавливает время последнего изменения
        """
        current_time = datetime.now().isoformat()
        self.conn.execute(
            "UPDATE Cards SET have=?, datetime_updated=? WHERE id=?",
            (have, current_time, card_id),
        )
        self.conn.commit()
    
    def add_datetime_column_if_not_exists(self):
        """
        Добавляет колонку datetime_updated, если она не существует
        """
        columns = [column[1] for column in self.conn.execute("PRAGMA table_info(Cards)")]
        if "datetime_updated" not in columns:
            self.conn.execute("ALTER TABLE Cards ADD COLUMN datetime_updated TEXT")
            self.conn.commit()
    
    def close(self):
        self.conn.close()
