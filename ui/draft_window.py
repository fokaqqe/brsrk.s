# draft_module.py — обновлённый
import sys
import os
import re
import random
from collections import Counter
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLabel, QWidget, QFrame, QMessageBox,
    QScrollArea, QSplitter, QApplication
)
from PyQt5.QtGui import QPixmap, QDrag, QFont
from PyQt5.QtCore import Qt, QMimeData, QTimer, QSize

# Импорт констант из main.py, с fallback'ом
try:
    from app_theme import COLORS, THUMB_SIZE, LARGE_SIZE, get_stylesheet
except Exception:
    COLORS = {
        'bg_primary': '#1e1e2e',
        'bg_secondary': '#313244',
        'bg_tertiary': '#45475a',
        'accent': '#cba6f7',
        'accent_hover': '#b4befe',
        'text_primary': '#cdd6f4',
        'text_secondary': '#bac2de',
        'border': '#585b70',
        'success': '#a6e3a1',
        'warning': '#f9e2af',
        'error': '#f38ba8'
    }
    THUMB_SIZE = QSize(180, 270)
    LARGE_SIZE = QSize(400, 600)
    def get_stylesheet():
        return ""

# Единые размеры слотов (отряд и доступные карты будут одинаковыми)
SLOT_MIN_W = max(120, int(THUMB_SIZE.width() * 0.8) + 10)
SLOT_MIN_H = max(180, int(THUMB_SIZE.height() * 0.8) + 40)

MONEY_TABLE = {
    (0, "defense"): (25, 23),
    (1, "defense"): (25, 23),
    (2, "defense"): (24, 23),
    (3, "defense"): (23, 23),
    (4, "defense"): (22, 23),
    (5, "defense"): (21, 23),
    (0, "attack"): (24, 22),
    (1, "attack"): (24, 22),
    (2, "attack"): (23, 22),
    (3, "attack"): (22, 22),
    (4, "attack"): (21, 22),
    (5, "attack"): (20, 22),
}


class DraftCardWidget(QWidget):
    """Виджет карты для раздачи с поддержкой drag&drop"""
    def __init__(self, card, pixmap_cache=None, is_in_squad=False):
        super().__init__()
        self.card = card
        self.pixmap_cache = pixmap_cache or {}
        self.is_in_squad = is_in_squad  # Флаг: находится ли карта в отряде
        self.drag_start_pos = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        self.img_label = QLabel()
        self.img_label.setAlignment(Qt.AlignCenter)
        self.img_label.setStyleSheet(f"""
            border: 2px solid {COLORS['border']};
            border-radius: 6px;
            background-color: {COLORS['bg_tertiary']};
        """)

        draft_size = (int(THUMB_SIZE.width() * 0.8), int(THUMB_SIZE.height() * 0.8))

        pix = self.pixmap_cache.get(getattr(self.card, "id", None))
        if pix:
            scaled_pix = pix.scaled(draft_size[0], draft_size[1], Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.img_label.setPixmap(scaled_pix)
        else:
            self.img_label.setText("📄")
            self.img_label.setMinimumSize(draft_size[0], draft_size[1])
            self.img_label.setStyleSheet(self.img_label.styleSheet() + f"""
                font-size: 20px;
                color: {COLORS['text_secondary']};
            """)

        layout.addWidget(self.img_label)

        self.name_label = QLabel(self.card.name or "")
        self.name_label.setAlignment(Qt.AlignCenter)
        self.name_label.setWordWrap(True)
        self.name_label.setStyleSheet(f"""
            font-size: 11px;
            font-weight: bold;
            color: {COLORS['text_primary']};
            padding: 2px;
            background-color: rgba(203, 166, 247, 0.1);
            border-radius: 4px;
        """)
        layout.addWidget(self.name_label)

        self.setLayout(layout)
        self.setProperty("class", "draft-card-widget")

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_start_pos = event.pos()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.LeftButton) or self.drag_start_pos is None:
            return

        distance = (event.pos() - self.drag_start_pos).manhattanLength()
        if distance >= QApplication.startDragDistance():
            drag = QDrag(self)
            mime = QMimeData()
            # Всегда используем _draft_id для уникальной идентификации
            draft_key = getattr(self.card, "_draft_id", None)
            if draft_key is None:
                return

            # Определяем тип drag операции в зависимости от того, где находится карта
            if self.is_in_squad:
                mime.setText(f"squad:{draft_key}")  # Карта из отряда
            else:
                mime.setText(f"draft:{draft_key}")  # Карта из раздачи
                
            drag.setMimeData(mime)
            drag.exec(Qt.CopyAction | Qt.MoveAction)
            self.drag_start_pos = None

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.drag_start_pos is not None:
            moved = (event.pos() - self.drag_start_pos).manhattanLength()
            if moved < QApplication.startDragDistance():
                self.open_large_image()
        self.drag_start_pos = None
        super().mouseReleaseEvent(event)

    def open_large_image(self):
        if getattr(self.card, "image_path", None) and os.path.exists(self.card.image_path):
            dialog = QDialog(self)
            dialog.setWindowTitle(self.card.name or "")
            dialog.setAttribute(Qt.WA_DeleteOnClose)
            dialog.setStyleSheet(get_stylesheet())

            v = QVBoxLayout()
            pm = QPixmap(self.card.image_path).scaled(LARGE_SIZE, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            lbl = QLabel()
            lbl.setPixmap(pm)
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet(f"""
                border: 3px solid {COLORS['accent']};
                border-radius: 12px;
                background-color: {COLORS['bg_secondary']};
                padding: 10px;
            """)
            v.addWidget(lbl)
            dialog.setLayout(v)
            dialog.resize(min(pm.width() + 40, LARGE_SIZE.width() + 40),
                         min(pm.height() + 80, LARGE_SIZE.height() + 80))
            dialog.show()


class DraftCardSlot(QWidget):
    """Слот для карт в секции 'Доступные карты'"""
    def __init__(self, row, col):
        super().__init__()
        self.row = row
        self.col = col
        self.card = None
        self.card_widget = None
        self.init_ui()

    def init_ui(self):
        self.setMinimumSize(SLOT_MIN_W, SLOT_MIN_H)
        self.setStyleSheet(f"""
            QWidget {{
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                background-color: {COLORS['bg_tertiary']};
            }}
        """)
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(2, 2, 2, 2)
        self.placeholder_label = QLabel("Пусто")
        self.placeholder_label.setAlignment(Qt.AlignCenter)
        self.placeholder_label.setStyleSheet(f"""
            color: {COLORS['text_secondary']};
            font-size: 10px;
            border: none;
            background: transparent;
        """)
        self.layout.addWidget(self.placeholder_label)
        self.setLayout(self.layout)

    def set_card(self, card, pixmap_cache):
        self.card = card
        self.placeholder_label.hide()
        if self.card_widget:
            self.card_widget.setParent(None)
            self.card_widget.deleteLater()
        self.card_widget = DraftCardWidget(card, pixmap_cache, is_in_squad=False)
        self.layout.addWidget(self.card_widget)

    def remove_card(self):
        self.card = None
        if self.card_widget:
            self.card_widget.setParent(None)
            self.card_widget.deleteLater()
            self.card_widget = None
        self.placeholder_label.show()


class DraftSlotWidget(QWidget):
    """Слот в сетке отряда (который принимает карты)"""
    def __init__(self, row, col):
        super().__init__()
        self.row = row
        self.col = col
        self.card = None
        self.card_widget = None
        self.init_ui()

    def init_ui(self):
        self.setAcceptDrops(True)
        self.setMinimumSize(SLOT_MIN_W, SLOT_MIN_H)
        self.setStyleSheet(f"""
            QWidget {{
                border: 2px dashed {COLORS['border']};
                border-radius: 8px;
                background-color: {COLORS['bg_secondary']};
            }}
            QWidget:hover {{
                border-color: {COLORS['accent']};
                background-color: {COLORS['bg_tertiary']};
            }}
        """)
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(2, 2, 2, 2)
        self.placeholder_label = QLabel("Перетащите\nкарту")
        self.placeholder_label.setAlignment(Qt.AlignCenter)
        self.placeholder_label.setStyleSheet(f"""
            color: {COLORS['text_secondary']};
            font-size: 12px;
            border: none;
            background: transparent;
        """)
        self.layout.addWidget(self.placeholder_label)
        self.setLayout(self.layout)

    def dragEnterEvent(self, event):
        mime_text = event.mimeData().text()
        if event.mimeData().hasText() and (mime_text.startswith("draft:") or mime_text.startswith("squad:")):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        mime_text = event.mimeData().text()
        if event.mimeData().hasText() and (mime_text.startswith("draft:") or mime_text.startswith("squad:")):
            event.acceptProposedAction()

    def dropEvent(self, event):
        mime_text = event.mimeData().text()
        if not event.mimeData().hasText() or not (mime_text.startswith("draft:") or mime_text.startswith("squad:")):
            event.ignore()
            return
            
        try:
            draft_window = self.window()
            
            if mime_text.startswith("draft:"):
                # Карта из раздачи - обычная покупка
                draft_id = int(mime_text[6:])
                if hasattr(draft_window, 'place_card_in_slot') and callable(draft_window.place_card_in_slot):
                    success = draft_window.place_card_in_slot(self, draft_id)
                    if success:
                        event.acceptProposedAction()
                    else:
                        event.ignore()
                else:
                    event.ignore()
                    
            elif mime_text.startswith("squad:"):
                # Карта из отряда - перемещение между слотами
                draft_id = int(mime_text[6:])
                if hasattr(draft_window, 'move_card_between_slots') and callable(draft_window.move_card_between_slots):
                    success = draft_window.move_card_between_slots(self, draft_id)
                    if success:
                        event.acceptProposedAction()
                    else:
                        event.ignore()
                else:
                    event.ignore()
                    
        except Exception:
            event.ignore()

    def set_card(self, card, pixmap_cache):
        self.card = card
        self.placeholder_label.hide()
        if self.card_widget:
            self.card_widget.setParent(None)
            self.card_widget.deleteLater()
        # Важно: указываем is_in_squad=True для карт в отряде
        self.card_widget = DraftCardWidget(card, pixmap_cache, is_in_squad=True)
        self.layout.addWidget(self.card_widget)
        self.setStyleSheet(f"""
            QWidget {{
                border: 2px solid {COLORS['accent']};
                border-radius: 8px;
                background-color: {COLORS['bg_tertiary']};
            }}
        """)

    def remove_card(self):
        self.card = None
        if self.card_widget:
            self.card_widget.setParent(None)
            self.card_widget.deleteLater()
            self.card_widget = None
        self.placeholder_label.show()
        self.setStyleSheet(f"""
            QWidget {{
                border: 2px dashed {COLORS['border']};
                border-radius: 8px;
                background-color: {COLORS['bg_secondary']};
            }}
            QWidget:hover {{
                border-color: {COLORS['accent']};
                background-color: {COLORS['bg_tertiary']};
            }}
        """)

    def mouseDoubleClickEvent(self, event):
        if self.card:
            draft_window = self.window()
            if hasattr(draft_window, 'return_card_to_draft') and callable(draft_window.return_card_to_draft):
                draft_id = getattr(self.card, "_draft_id", None)
                if draft_id:
                    draft_window.return_card_to_draft(draft_id)
        super().mouseDoubleClickEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton and self.card:
            draft_window = self.window()
            if hasattr(draft_window, 'return_card_to_draft') and callable(draft_window.return_card_to_draft):
                draft_id = getattr(self.card, "_draft_id", None)
                if draft_id:
                    draft_window.return_card_to_draft(draft_id)
        super().mousePressEvent(event)


class DraftWindow(QDialog):
    """Окно раздачи карт"""
    def __init__(self, parent, deck_cards, pixmap_cache, side_choice):
        super().__init__(parent)
        self.deck_cards = deck_cards.copy()
        self.pixmap_cache = pixmap_cache or {}
        self.side_choice = side_choice
        self._next_draft_uid = 1
        self.draft_cards = []
        self.available_draft_cards = []
        self.slots = []
        self.draft_slots = []
        # деньги
        self.gold_coins = 0
        self.silver_coins = 0

        try:
            if len(self.deck_cards) < 15:
                raise ValueError("Недостаточно карт для раздачи")
            
            selected_cards = random.sample(self.deck_cards, 15)
            
            # Создаем копии объектов карт, чтобы каждая имела свой уникальный _draft_id
            import copy
            self.draft_cards = []
            for i, card in enumerate(selected_cards):
                # Создаем поверхностную копию карты
                card_copy = copy.copy(card)
                self.draft_cards.append(card_copy)
            
            self._assign_draft_uids(self.draft_cards)
            self.available_draft_cards = list(self.draft_cards)

            # сетка слотов 5x3
            self.slots = []
            for r in range(3):
                row_slots = []
                for c in range(5):
                    row_slots.append(DraftSlotWidget(r, c))
                self.slots.append(row_slots)

            self.init_money()
            # сохраняем стартовые значения, чтобы потом считать сколько потрачено
            self.initial_gold = self.gold_coins
            self.initial_silver = self.silver_coins
            self.init_ui()
            self.update_money_display()
            self.refresh_draft_cards()

        except Exception as e:
            QMessageBox.critical(parent, "Ошибка", f"Не удалось создать окно раздачи: {str(e)}")
            raise

    def _assign_draft_uids(self, cards):
        for c in cards:
            new_id = self._next_draft_uid
            setattr(c, "_draft_id", new_id)
            self._next_draft_uid += 1

    def init_money(self):
        # Стартовые деньги основаны на 0 элементах в пустом отряде
        element_count = 0
        money_table = {
            (0, "defense"): (25, 23), (0, "attack"): (24, 22),
            (1, "defense"): (25, 23), (1, "attack"): (24, 22),
            (2, "defense"): (24, 23), (2, "attack"): (23, 22),
            (3, "defense"): (23, 23), (3, "attack"): (22, 22),
            (4, "defense"): (22, 23), (4, "attack"): (21, 22),
            (5, "defense"): (21, 23), (5, "attack"): (20, 22),
        }
        self.gold_coins, self.silver_coins = money_table.get((element_count, self.side_choice), (20, 20))

    def init_ui(self):
        self.setWindowTitle(f"Раздача - {self.side_choice.title()}")
        self.setStyleSheet(get_stylesheet())
        self.setWindowState(Qt.WindowMaximized)
        self.setModal(True)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(8)

        title_label = QLabel(f"Раздача карт - {self.side_choice.upper()}")
        title_label.setFont(QFont("Segoe UI", 16, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet(f"color: {COLORS['accent']}; margin: 10px;")
        main_layout.addWidget(title_label)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)

        # левая - отряд
        left_frame = QFrame()
        left_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_secondary']};
                border: 2px solid {COLORS['border']};
                border-radius: 12px;
            }}
        """)
        left_layout = QVBoxLayout(left_frame)
        left_layout.setContentsMargins(16, 16, 16, 16)
        squad_label = QLabel("Отряд (5x3)")
        squad_label.setFont(QFont("Segoe UI", 14, QFont.Bold))
        squad_label.setAlignment(Qt.AlignCenter)
        left_layout.addWidget(squad_label)

        grid_widget = QWidget()
        grid_layout = QGridLayout(grid_widget)
        grid_layout.setSpacing(8)
        for r in range(3):
            for c in range(5):
                grid_layout.addWidget(self.slots[r][c], r, c)
        left_layout.addWidget(grid_widget)
        splitter.addWidget(left_frame)

        # правая - доступные карты
        right_frame = QFrame()
        right_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_secondary']};
                border: 2px solid {COLORS['border']};
                border-radius: 12px;
            }}
        """)
        right_layout = QVBoxLayout(right_frame)
        right_layout.setContentsMargins(16, 16, 16, 16)
        draft_label = QLabel("Доступные карты (5x3)")
        draft_label.setFont(QFont("Segoe UI", 14, QFont.Bold))
        draft_label.setAlignment(Qt.AlignCenter)
        right_layout.addWidget(draft_label)

        draft_grid_widget = QWidget()
        self.draft_grid_layout = QGridLayout(draft_grid_widget)
        self.draft_grid_layout.setSpacing(8)
        self.draft_grid_layout.setAlignment(Qt.AlignCenter)

        self.draft_slots = []
        for r in range(3):
            row_slots = []
            for c in range(5):
                slot = DraftCardSlot(r, c)
                self.draft_grid_layout.addWidget(slot, r, c)
                row_slots.append(slot)
            self.draft_slots.append(row_slots)

        right_layout.addWidget(draft_grid_widget)
        splitter.addWidget(right_frame)

        # равные пропорции 50/50
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)

        main_layout.addWidget(splitter)

        bottom_frame = QFrame()
        bottom_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_tertiary']};
                border: 2px solid {COLORS['border']};
                border-radius: 8px;
                padding: 8px;
            }}
        """)
        bottom_layout = QHBoxLayout(bottom_frame)

        self.money_label = QLabel()
        self.money_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        self.money_label.setStyleSheet(f"""
            color: {COLORS['warning']};
            background-color: {COLORS['bg_secondary']};
            border: 1px solid {COLORS['border']};
            border-radius: 6px;
            padding: 8px 16px;
        """)
        bottom_layout.addWidget(self.money_label)
        bottom_layout.addStretch()

        self.redraft_btn = QPushButton("Перераздача (-1 золотой)")
        self.redraft_btn.clicked.connect(self.redraft)
        self.redraft_btn.setMinimumWidth(200)
        bottom_layout.addWidget(self.redraft_btn)

        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(self.accept)
        close_btn.setMinimumWidth(120)
        bottom_layout.addWidget(close_btn)

        main_layout.addWidget(bottom_frame)
        self.setLayout(main_layout)

    def refresh_draft_cards(self):
        try:
            for r in range(3):
                for c in range(5):
                    self.draft_slots[r][c].remove_card()
            idx = 0
            for r in range(3):
                for c in range(5):
                    if idx < len(self.available_draft_cards):
                        card = self.available_draft_cards[idx]
                        self.draft_slots[r][c].set_card(card, self.pixmap_cache)
                        idx += 1
        except Exception:
            pass

    def parse_card_cost(self, card):
        """Возвращает (gold, silver) стоимости — если не распознал, (0,0)"""
        if not hasattr(card, 'cost') or not card.cost:
            return 0, 0
        cost_str = str(card.cost).strip()

        gold_patterns = [r'(\d+)\s*\(Золото\)', r'(\d+)\s*\(золото\)', r'(\d+)\s*з\b', r'(\d+)\s*З\b']
        silver_patterns = [r'(\d+)\s*\(Серебро\)', r'(\d+)\s*\(серебро\)', r'(\d+)\s*с\b', r'(\d+)\s*С\b']

        for p in gold_patterns:
            m = re.search(p, cost_str)
            if m:
                return int(m.group(1)), 0
        for p in silver_patterns:
            m = re.search(p, cost_str)
            if m:
                return 0, int(m.group(1))
        simple = re.search(r'^(\d+)$', cost_str)
        if simple:
            return 0, int(simple.group(1))
        return 0, 0

    def can_afford(self, need_gold, need_silver):
        """Проверяет, хватает ли средств. Серебро можно заменить золотом (1:1),
           но золото за золото должно быть доступно (т. е. need_gold покрывается только золотом).
        """
        if need_gold < 0 or need_silver < 0:
            return False

        # если нужен только золото
        if need_silver == 0:
            return self.gold_coins >= need_gold

        # общее серебро эквивалент (серебро + золото как серебро)
        total_as_silver = self.silver_coins + self.gold_coins

        # если нужен только серебро — допускается покрытие золотом
        if need_gold == 0:
            return total_as_silver >= need_silver

        # если нужно и то и то: недостающее серебро покрывается золотом,
        # но к требуемому золоту прибавляется использованное для покрытия серебра
        silver_deficit = max(0, need_silver - self.silver_coins)
        required_gold = need_gold + silver_deficit
        return self.gold_coins >= required_gold

    def spend_money(self, cost_gold, cost_silver, card=None):
        """Списывает деньги. Если серебра не хватает, покрываем золотом.
           Сохраняем фактическую структуру оплаты в card._payment = (gold_spent, silver_spent).
        """
        gold_spent = 0
        silver_spent = 0

        # сначала списываем обязательную "золотую" часть
        if cost_gold > 0:
            to_take = min(self.gold_coins, cost_gold)
            self.gold_coins -= to_take
            gold_spent += to_take
            # Если to_take < cost_gold — значит недостаток золота; это означает,
            # что can_afford должен был предотвратить такую покупку.
            if to_take < cost_gold:
                # На всякий случай: попытаемся компенсировать недостающее золото серебром (не основной сценарий).
                silver_deficit = cost_gold - to_take
                if self.silver_coins >= silver_deficit:
                    self.silver_coins -= silver_deficit
                    silver_spent += silver_deficit
                else:
                    # некорректная ситуация — оставим как есть
                    pass

        # затем списываем серебро с заменой на золото при необходимости
        if cost_silver > 0:
            if self.silver_coins >= cost_silver:
                self.silver_coins -= cost_silver
                silver_spent += cost_silver
            else:
                # используем всё серебро, а остальное покрываем золотом
                available_silver = self.silver_coins
                silver_spent += available_silver
                self.silver_coins = 0
                deficit = cost_silver - available_silver
                gold_cover = min(self.gold_coins, deficit)
                self.gold_coins -= gold_cover
                gold_spent += gold_cover
                # если gold_cover < deficit => некорректная ситуация (can_afford должна была пропустить)

        # сохраняем структуру оплаты в карту (если предоставлена)
        if card is not None:
            setattr(card, "_payment", (gold_spent, silver_spent))

    def place_card_in_slot(self, slot_widget, draft_id):
        """Размещает карту в слоте отряда по draft_id (временный _draft_id или id)"""
        try:
            # находим карту в available_draft_cards ТОЛЬКО по _draft_id
            card_to_place = None
            for card in self.available_draft_cards:
                if getattr(card, "_draft_id", None) == draft_id:
                    card_to_place = card
                    break
            if not card_to_place:
                return False

            cost_gold, cost_silver = self.parse_card_cost(card_to_place)
            if not self.can_afford(cost_gold, cost_silver):
                QMessageBox.warning(self, "Недостаточно средств",
                                    f"Недостаточно денег для размещения карты {card_to_place.name}")
                return False

            # если в слоте что-то было — возвращаем его
            if slot_widget.card:
                old_draft_id = getattr(slot_widget.card, "_draft_id", None)
                if old_draft_id:
                    self.return_card_to_draft(old_draft_id)

            # тратим деньги и запоминаем оплату в объекте карты
            self.spend_money(cost_gold, cost_silver, card=card_to_place)

            # размещаем карту в слоте
            slot_widget.set_card(card_to_place, self.pixmap_cache)

            # убираем этот объект из available_draft_cards ТОЛЬКО по _draft_id
            for i, c in enumerate(self.available_draft_cards):
                if getattr(c, "_draft_id", None) == draft_id:
                    del self.available_draft_cards[i]
                    break

            # очищаем отображение фиксированных слотов ТОЛЬКО по _draft_id
            for r in range(3):
                for c in range(5):
                    ds = self.draft_slots[r][c]
                    if ds.card and getattr(ds.card, "_draft_id", None) == draft_id:
                        ds.remove_card()
                        break

            self.refresh_draft_cards()
            self.update_money_display()
            self.recalc_money()
            return True

        except Exception:
            return False

    def move_card_between_slots(self, target_slot, draft_id):
        """Перемещает карту между слотами отряда без затрат денег"""
        try:
            # Находим исходный слот с этой картой ТОЛЬКО по _draft_id
            source_slot = None
            card_to_move = None
            for r, row in enumerate(self.slots):
                for c, slot in enumerate(row):
                    if slot.card:
                        card_draft_id = getattr(slot.card, "_draft_id", "MISSING")
                        if card_draft_id == draft_id:
                            source_slot = slot
                            card_to_move = slot.card
                            
            if not source_slot or not card_to_move:
                return False
                
            # Если целевой слот занят, меняем карты местами
            if target_slot.card:
                temp_card = target_slot.card
                target_slot.remove_card()
                source_slot.remove_card()
                
                # Размещаем карты в новых позициях
                target_slot.set_card(card_to_move, self.pixmap_cache)
                source_slot.set_card(temp_card, self.pixmap_cache)
            else:
                # Просто перемещаем карту в пустой слот
                source_slot.remove_card()
                target_slot.set_card(card_to_move, self.pixmap_cache)
                
            return True
            
        except Exception:
            return False

    def return_card_to_draft(self, draft_id):
        """Возвращает карту из слота обратно в раздачу и возмещает ту оплату, которая была сделана"""
        try:
            slot_with_card = None
            # Находим слот с картой ТОЛЬКО по _draft_id
            for row in self.slots:
                for slot in row:
                    if slot.card and getattr(slot.card, "_draft_id", None) == draft_id:
                        slot_with_card = slot
                        break
                if slot_with_card:
                    break

            if not slot_with_card:
                return False

            card = slot_with_card.card

            # Если есть запись о том, что именно было потрачено — возвращаем эти значения
            if hasattr(card, "_payment"):
                gold_spent, silver_spent = getattr(card, "_payment")
                self.gold_coins += gold_spent
                self.silver_coins += silver_spent
                try:
                    delattr(card, "_payment")
                except Exception:
                    # если delattr не работает (pyqt property edge) — присвоим None
                    setattr(card, "_payment", None)
            else:
                # fallback — вернём номинальную стоимость (на случай, если карта не была куплена "через" систему)
                cg, cs = self.parse_card_cost(card)
                self.gold_coins += cg
                self.silver_coins += cs

            # убираем карту из слота
            slot_with_card.remove_card()

            # добавляем объект обратно в доступные карты
            self.available_draft_cards.append(card)

            self.refresh_draft_cards()
            self.update_money_display()
            self.recalc_money()
            return True

        except Exception:
            return False

    def update_money_display(self):
        self.money_label.setText(f"Деньги: {self.gold_coins} золотых, {self.silver_coins} серебряных")

    def redraft(self):
        """Перераздача: возвращаем все размещённые карты, возмещаем реальные оплаты, тратим 1 золото и даём новые 15 карт"""
        if self.gold_coins < 1:
            QMessageBox.warning(self, "Недостаточно средств", "Недостаточно золотых монет для перераздачи")
            return

        reply = QMessageBox.question(self, "Перераздача",
                                     "Потратить 1 золотой на перераздачу?\nВсе размещённые карты вернутся в раздачу.",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply != QMessageBox.Yes:
            return

        try:
            # Собираем все карты из слотов (объекты)
            cards_to_return = []
            for row in self.slots:
                for slot in row:
                    if slot.card:
                        cards_to_return.append(slot.card)

            # Возвращаем реальные оплаты (если были)
            for card in cards_to_return:
                if hasattr(card, "_payment") and getattr(card, "_payment") is not None:
                    g_spent, s_spent = getattr(card, "_payment")
                    self.gold_coins += g_spent
                    self.silver_coins += s_spent
                    try:
                        delattr(card, "_payment")
                    except Exception:
                        setattr(card, "_payment", None)
                else:
                    # fallback — если карта из draft_cards — вернуть номинал
                    if card in self.draft_cards:
                        cg, cs = self.parse_card_cost(card)
                        self.gold_coins += cg
                        self.silver_coins += cs

            # очищаем слоты
            for row in self.slots:
                for slot in row:
                    if slot.card:
                        slot.remove_card()

            # тратим 1 золотой
            self.gold_coins -= 1

            if len(self.deck_cards) < 15:
                QMessageBox.warning(self, "Ошибка", "В колоде недостаточно карт для перераздачи")
                return

            # новая раздача
            selected_cards = random.sample(self.deck_cards, 15)
            
            # Создаем копии объектов карт для новой раздачи
            import copy
            self.draft_cards = []
            for i, card in enumerate(selected_cards):
                card_copy = copy.copy(card)
                self.draft_cards.append(card_copy)
            
            # сбрасываем uid помощи избегания пересечений (не обязательно, но удобно)
            self._next_draft_uid = 1
            self._assign_draft_uids(self.draft_cards)
            self.available_draft_cards = list(self.draft_cards)

            self.refresh_draft_cards()
            self.update_money_display()
            self.recalc_money()

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Произошла ошибка при перераздаче: {str(e)}")
            

    def recalc_money(self):
        """Пересчитывает золото и серебро на основе уникальных стихий в отряде"""
        try:
            elements = set()
            for row in self.slots:
                for slot in row:
                    if slot.card and hasattr(slot.card, "element"):
                        elem = str(slot.card.element).strip().lower()
                        if elem and elem != "нейтральная":
                            elements.add(elem)

            element_count = min(len(elements), 5)
            base_gold, base_silver = MONEY_TABLE.get((element_count, self.side_choice), (20, 20))

            # считаем сколько уже потрачено (от базового стартового)
            spent_gold = self.initial_gold - self.gold_coins
            spent_silver = self.initial_silver - self.silver_coins

            # обновляем стартовые значения
            self.initial_gold, self.initial_silver = base_gold, base_silver

            # пересчитываем текущее количество денег
            self.gold_coins = max(0, self.initial_gold - spent_gold)
            self.silver_coins = max(0, self.initial_silver - spent_silver)

            self.update_money_display()
        except Exception:
            pass

def open_draft_dialog(parent, deck_widget, pixmap_cache):
    """Открывает диалог выбора стороны и затем окно раздачи"""
    try:
        if len(deck_widget.cards) < 30:
            QMessageBox.warning(parent, "Недостаточно карт",
                                "В колоде должно быть минимум 30 карт для раздачи.")
            return

        dialog = QDialog(parent)
        dialog.setWindowTitle("Выбор стороны")
        dialog.setStyleSheet(get_stylesheet())
        dialog.setModal(True)
        dialog.resize(400, 200)

        layout = QVBoxLayout()
        layout.setSpacing(20)

        title_label = QLabel("Выберите сторону для раздачи:")
        title_label.setFont(QFont("Segoe UI", 14))
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        buttons_layout = QHBoxLayout()

        attack_btn = QPushButton("Атака")
        attack_btn.setMinimumSize(150, 50)
        attack_btn.setFont(QFont("Segoe UI", 12))
        attack_btn.clicked.connect(lambda: dialog.done(1))

        defense_btn = QPushButton("Защита")
        defense_btn.setMinimumSize(150, 50)
        defense_btn.setFont(QFont("Segoe UI", 12))
        defense_btn.clicked.connect(lambda: dialog.done(2))

        buttons_layout.addWidget(attack_btn)
        buttons_layout.addWidget(defense_btn)
        layout.addLayout(buttons_layout)
        dialog.setLayout(layout)

        result = dialog.exec_()
        if result == 1:
            dw = DraftWindow(parent, deck_widget.cards, pixmap_cache, "attack")
            dw.exec_()
        elif result == 2:
            dw = DraftWindow(parent, deck_widget.cards, pixmap_cache, "defense")
            dw.exec_()

    except Exception as e:
        QMessageBox.critical(parent, "Ошибка", f"Общая ошибка при открытии раздачи: {str(e)}")
