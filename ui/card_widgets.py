"""Reusable card and deck widgets."""

import os
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QSpinBox, QDialog, QMessageBox, QScrollArea, QGridLayout
from PyQt5.QtGui import QPixmap, QDrag
from PyQt5.QtCore import Qt, QSize, QRunnable, pyqtSignal, QObject, QMimeData, QTimer
from app_theme import COLORS, THUMB_SIZE, LARGE_SIZE, get_stylesheet
from services.deck_storage import save_deck as save_deck_file, load_deck as load_deck_file
from services.deck_stats import format_deck_stats
from services.image_paths import resolve_image_path
class SignalEmitter(QObject):
    image_ready = pyqtSignal(int)  # card_id


# ---------- Многопоточная загрузка ----------
class ImageLoader(QRunnable):
    def __init__(self, card, cache, signal):
        super().__init__()
        self.card = card
        self.cache = cache
        self.signal = signal

    def run(self):
        try:
            image_path = resolve_image_path(self.card.image_path)
            if image_path:
                pix = QPixmap(image_path).scaled(
                    THUMB_SIZE, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.cache[self.card.id] = pix
                self.signal.image_ready.emit(self.card.id)
        except Exception:
            pass


# ---------- CardWidget ----------
class CardWidget(QWidget):
    def __init__(self, card, db=None, pixmap_cache=None, refresh_callback=None, deck_mode=False, remove_callback=None):
        super().__init__()
        self.card = card
        self.db = db
        self.pixmap_cache = pixmap_cache if pixmap_cache is not None else {}
        self.refresh_callback = refresh_callback
        self.deck_mode = deck_mode
        self.remove_callback = remove_callback
        self.drag_start_pos = None
        self.open_dialogs = []
        self.is_insufficient = False  # новый флаг для отслеживания недостаточности карт
        self.init_ui()
        self.setProperty("class", "card-widget")

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        self.img_label = QLabel()
        # Keep the grid stable while images arrive from the background loader.
        self.img_label.setFixedSize(THUMB_SIZE)
        self.img_label.setAlignment(Qt.AlignCenter)
        self.img_label.setStyleSheet(f"""
            border: 2px solid {COLORS['border']};
            border-radius: 8px;
            background-color: {COLORS['bg_tertiary']};
        """)

        pix = self.pixmap_cache.get(self.card.id)
        if pix:
            self.img_label.setPixmap(pix)
        else:
            self.img_label.setText("📄")
            self.img_label.setStyleSheet(self.img_label.styleSheet() + f"""
                font-size: 24px;
                color: {COLORS['text_secondary']};
            """)
        layout.addWidget(self.img_label)

        self.name_label = QLabel(self.card.name or "")
        self.name_label.setAlignment(Qt.AlignCenter)
        self.name_label.setWordWrap(True)
        self.name_label.setFixedHeight(34)
        self.name_label.setStyleSheet(f"""
            font-size: 13px;
            font-weight: bold;
            color: {COLORS['text_primary']};
            padding: 4px;
            background-color: rgba(203, 166, 247, 0.1);
            border-radius: 6px;
        """)
        layout.addWidget(self.name_label)

        if not self.deck_mode:
            max_count = 5 if ("орда" in (self.card.ability or "").lower()) else 3
            self.have_spin = QSpinBox()
            self.have_spin.setRange(0, max_count)
            self.have_spin.setValue(getattr(self.card, "have", 0))
            self.have_spin.valueChanged.connect(self.on_have_changed)
            layout.addWidget(self.have_spin, alignment=Qt.AlignCenter)

        self.setLayout(layout)
        self.setFixedWidth(THUMB_SIZE.width() + 16)

    def set_insufficient_style(self, insufficient=False):
        """Установить стиль для карт с недостаточным количеством - подсвечиваем название"""
        self.is_insufficient = insufficient
        if insufficient:
            # Красный фон для названия карты
            self.name_label.setStyleSheet(f"""
                font-size: 13px;
                font-weight: bold;
                color: white;
                padding: 4px;
                background-color: {COLORS['error']};
                border-radius: 6px;
            """)
        else:
            # Обычный стиль названия
            self.name_label.setStyleSheet(f"""
                font-size: 13px;
                font-weight: bold;
                color: {COLORS['text_primary']};
                padding: 4px;
                background-color: rgba(203, 166, 247, 0.1);
                border-radius: 6px;
            """)

    def on_have_changed(self, val):
        self.card.have = val
        if self.db:
            try:
                # Обновляем с временной меткой
                self.db.update_card_status(self.card.id, val)
                # Обновляем datetime_updated в объекте карты
                from datetime import datetime
                self.card.datetime_updated = datetime.now().isoformat()
            except Exception:
                pass
        if callable(self.refresh_callback):
            try:
                self.refresh_callback()
            except Exception:
                pass

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_start_pos = event.pos()
        elif event.button() == Qt.RightButton and self.deck_mode and callable(self.remove_callback):
            try:
                self.remove_callback(self.card)
            except Exception:
                pass
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.LeftButton) or self.drag_start_pos is None:
            return
        distance = (event.pos() - self.drag_start_pos).manhattanLength()
        if distance >= QApplication.startDragDistance():
            drag = QDrag(self)
            mime = QMimeData()
            if self.deck_mode:
                # Для колоды добавляем специальный префикс
                mime.setText(f"deck:{self.card.id}")
            else:
                mime.setText(str(self.card.id))
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
        image_path = resolve_image_path(self.card.image_path)
        if image_path:
            dialog = QDialog(self)
            dialog.setWindowTitle(self.card.name or "")
            dialog.setAttribute(Qt.WA_DeleteOnClose)
            dialog.setStyleSheet(get_stylesheet())

            v = QVBoxLayout()
            pm = QPixmap(image_path).scaled(LARGE_SIZE, Qt.KeepAspectRatio, Qt.SmoothTransformation)
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
            self.open_dialogs.append(dialog)
            dialog.finished.connect(lambda _: self.open_dialogs.remove(dialog))


# ---------- DeckWidget ----------
class DeckWidget(QWidget):
    def __init__(self, pixmap_cache):
        super().__init__()
        self.pixmap_cache = pixmap_cache
        self.columns = 1
        self.cards = []
        self.card_counts = {}
        self.resize_timer = QTimer()
        self.resize_timer.setSingleShot(True)
        self.resize_timer.timeout.connect(self.delayed_refresh)
        self.show_availability = False  # новый флаг для показа наличия
        self.all_cards = []  # ссылка на все карты для проверки наличия
        self.init_ui()
        self.setAcceptDrops(True)

    def init_ui(self):
        v = QVBoxLayout()
        v.setContentsMargins(8, 8, 8, 8)
        v.setSpacing(12)

        # note: stats_label создаём, но НЕ добавляем в этот layout
        # (MainWindow сам может разместить эту метку в своем "controls" блоке)
        self.stats_label = QLabel("Колода пуста")
        self.stats_label.setAlignment(Qt.AlignCenter)
        self.stats_label.setProperty("class", "stats-label")
        self.stats_label.setMinimumHeight(80)

        # scroll area (тут только сетка карт)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.inner = QWidget()
        self.grid = QGridLayout()
        self.grid.setSpacing(12)
        self.grid.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        self.inner.setLayout(self.grid)
        self.scroll.setWidget(self.inner)
        v.addWidget(self.scroll)

        self.setLayout(v)

    def set_all_cards_reference(self, cards):
        """Установить ссылку на все карты для проверки наличия"""
        self.all_cards = cards

    def toggle_availability_check(self, enabled):
        """Переключить проверку наличия карт"""
        self.show_availability = enabled
        self.refresh()

    def auto_sort_deck(self):
        """Автосортировка колоды по ID"""
        if not self.cards:
            return
        
        # Сортируем по ID
        self.cards.sort(key=lambda card: card.id)
        self.refresh()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Используем таймер для предотвращения множественных обновлений
        self.resize_timer.start(100)  # 100ms задержка

    def delayed_refresh(self):
        self.update_columns()
        self.refresh()

    def update_columns(self):
        avail = self.scroll.viewport().width()
        if avail <= 0:
            return
        card_plus_gap = THUMB_SIZE.width() + 20
        cols = max(1, avail // card_plus_gap)
        if cols != self.columns:
            self.columns = cols

    def add_card(self, card):
        cid = card.id
        max_count = 5 if ("орда" in (card.ability or "").lower()) else 3
        if self.card_counts.get(cid, 0) >= max_count:
            QMessageBox.warning(self, "Нельзя добавить",
                                f"Нельзя иметь более {max_count} копий этой карты в колоде.")
            return

        self.cards.append(card)
        self.card_counts[cid] = self.card_counts.get(cid, 0) + 1
        self.refresh()
        # scroll to bottom so new cards are visible
        QTimer.singleShot(50, lambda: self.scroll.verticalScrollBar().setValue(
            self.scroll.verticalScrollBar().maximum()))

    def remove_card(self, card):
        cid = card.id
        if self.card_counts.get(cid, 0) == 0:
            return
        for i, c in enumerate(self.cards):
            if c.id == cid:
                self.cards.pop(i)
                break
        self.card_counts[cid] -= 1
        if self.card_counts[cid] == 0:
            del self.card_counts[cid]
        self.refresh()

    def move_card(self, from_index, to_index):
        """Перемещает карту внутри колоды"""
        if 0 <= from_index < len(self.cards) and 0 <= to_index < len(self.cards):
            card = self.cards.pop(from_index)
            self.cards.insert(to_index, card)
            self.refresh()

    def get_card_index_at_position(self, pos):
        """Находит индекс карты в позиции"""
        for i in range(self.grid.count()):
            item = self.grid.itemAt(i)
            if item and item.widget():
                widget_rect = item.widget().geometry()
                if widget_rect.contains(pos):
                    return i
        return -1

    def clear_deck(self):
        self.cards.clear()
        self.card_counts.clear()
        self.refresh()

    def refresh(self):
        # Очищаем grid аккуратно
        widgets_to_delete = []
        while self.grid.count():
            item = self.grid.takeAt(0)
            if item and item.widget():
                widgets_to_delete.append(item.widget())

        # Удаляем виджеты после очистки layout
        for widget in widgets_to_delete:
            widget.setParent(None)
            widget.deleteLater()

        # Заполняем grid
        row = col = 0
        for i, card in enumerate(self.cards):
            cw = CardWidget(card, pixmap_cache=self.pixmap_cache,
                            deck_mode=True, remove_callback=self.remove_card)
            cw.card_index = i  # Сохраняем индекс для drag&drop
            
            # Проверяем наличие карт, если включена проверка
            if self.show_availability:
                # Считаем, сколько раз эта карта встречается до текущей позиции включительно
                cards_used = sum(1 for c in self.cards[:i+1] if c.id == card.id)
                
                # Находим актуальную карту в списке all_cards для получения текущего have
                actual_card = next((c for c in self.all_cards if c.id == card.id), None)
                db_have = getattr(actual_card, 'have', 0) if actual_card else 0
                
                # Если использовано больше, чем есть в БД, подсвечиваем красным название
                if cards_used > db_have:
                    cw.set_insufficient_style(True)
                else:
                    cw.set_insufficient_style(False)
            else:
                cw.set_insufficient_style(False)
            
            self.grid.addWidget(cw, row, col)
            col += 1
            if col >= self.columns:
                col = 0
                row += 1

        self.update_stats()

    def update_stats(self):
        self.stats_label.setText(format_deck_stats(self.cards))

    # drag & drop
    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dropEvent(self, event):
        if not event.mimeData().hasText():
            event.ignore()
            return

        text = event.mimeData().text()

        # Проверяем, что карта из колоды или из каталога
        if text.startswith("deck:"):
            # Это перетаскивание внутри колоды
            try:
                card_id = int(text[5:])  # убираем префикс "deck:"
                # Находим индекс карты, которую перетаскиваем
                from_index = -1
                for i, card in enumerate(self.cards):
                    if card.id == card_id:
                        from_index = i
                        break

                if from_index == -1:
                    event.ignore()
                    return

                # Находим позицию, куда перетаскиваем
                drop_pos = event.pos()
                to_index = self.get_card_index_at_position(drop_pos)

                if to_index == -1:
                    to_index = len(self.cards) - 1

                # Перемещаем карту
                if from_index != to_index:
                    self.move_card(from_index, to_index)

                event.acceptProposedAction()

            except ValueError:
                event.ignore()
        else:
            # Это добавление из каталога
            try:
                cid = int(text)
                mainwin = self.window()
                card = next((c for c in getattr(mainwin, "cards", []) if c.id == cid), None)
                if card:
                    self.add_card(card)
                    event.acceptProposedAction()
                else:
                    event.ignore()
            except ValueError:
                event.ignore()

    def save_deck(self, path):
        save_deck_file(path, self.cards)

    def load_deck(self, path, all_cards):
        self.cards.clear()
        self.card_counts.clear()
        self.cards.extend(load_deck_file(path, all_cards))
        for card in self.cards:
            self.card_counts[card.id] = self.card_counts.get(card.id, 0) + 1
        self.refresh()


# ---------- MainWindow ----------
