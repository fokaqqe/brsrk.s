import sys
import os
from ui.draft_window import open_draft_dialog
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QListWidget, QListWidgetItem, QLabel, QSpinBox,
    QComboBox, QDialog, QLineEdit, QPushButton, QFileDialog,
    QGridLayout, QScrollArea, QMessageBox, QSplitter, QFrame,
    QSizePolicy, QCheckBox, QGroupBox
)
from PyQt5.QtGui import QPixmap, QDrag, QFont, QPalette, QColor
from PyQt5.QtCore import Qt, QSize, QRunnable, QThreadPool, pyqtSignal, QObject, QMimeData, QTimer

from domain.card import Card as CardModel
from domain.app_state import AppState
from repositories.card_repository import CardRepository
from services.deck_image_export import generate_deck_image_wrapper
from domain.filters import matches_advanced_filters, matches_main_filters, sort_cards
from services.deck_storage import save_deck as save_deck_file, load_deck as load_deck_file
from services.deck_stats import format_deck_stats
from services.image_paths import resolve_image_path
from ui.filter_dialogs import MainFiltersDialog, AdvancedFiltersDialog
from ui.card_widgets import SignalEmitter, ImageLoader, CardWidget, DeckWidget
from app_theme import COLORS as SHARED_COLORS, get_stylesheet as shared_get_stylesheet, CATALOG_CELL_SIZE

THUMB_SIZE = QSize(180, 270)
LARGE_SIZE = QSize(400, 600)
BATCH_SIZE = 100
MAX_LOADED = 2000

# Цветовая схема
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

# ---------- Стили ----------
def get_stylesheet():
    return f"""
    QMainWindow, QWidget {{
        background-color: {COLORS['bg_primary']};
        color: {COLORS['text_primary']};
        font-family: 'Segoe UI', 'Roboto', sans-serif;
    }}
    
    QLineEdit {{
        background-color: {COLORS['bg_secondary']};
        border: 2px solid {COLORS['border']};
        border-radius: 8px;
        padding: 8px 12px;
        font-size: 14px;
        color: {COLORS['text_primary']};
    }}
    
    QLineEdit:focus {{
        border-color: {COLORS['accent']};
        background-color: {COLORS['bg_tertiary']};
    }}
    
    QComboBox {{
        background-color: {COLORS['bg_secondary']};
        border: 2px solid {COLORS['border']};
        border-radius: 8px;
        padding: 8px 12px;
        font-size: 14px;
        color: {COLORS['text_primary']};
        min-width: 120px;
    }}
    
    QComboBox:hover {{
        border-color: {COLORS['accent_hover']};
        background-color: {COLORS['bg_tertiary']};
    }}
    
    QComboBox::drop-down {{
        border: none;
        width: 20px;
    }}
    
    QComboBox::down-arrow {{
        image: none;
        border-left: 5px solid transparent;
        border-right: 5px solid transparent;
        border-top: 5px solid {COLORS['text_secondary']};
    }}
    
    QSpinBox {{
        background-color: {COLORS['bg_secondary']};
        border: 2px solid {COLORS['border']};
        border-radius: 8px;
        padding: 8px;
        font-size: 14px;
        color: {COLORS['text_primary']};
        min-width: 60px;
    }}
    
    QSpinBox:focus {{
        border-color: {COLORS['accent']};
        background-color: {COLORS['bg_tertiary']};
    }}
    
    QPushButton {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                                   stop:0 {COLORS['accent']}, 
                                   stop:1 #9d7cd8);
        border: none;
        border-radius: 10px;
        padding: 10px 20px;
        font-size: 14px;
        font-weight: bold;
        color: white;
    }}
    
    QPushButton:hover {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                                   stop:0 {COLORS['accent_hover']}, 
                                   stop:1 #a78bfa);
    }}
    
    QPushButton:pressed {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                                   stop:0 #8b5cf6, 
                                   stop:1 #7c3aed);
    }}
    
    QLabel {{
        color: {COLORS['text_primary']};
        font-size: 14px;
        font-weight: 500;
    }}
    
    QListWidget {{
        background-color: {COLORS['bg_secondary']};
        border: 2px solid {COLORS['border']};
        border-radius: 12px;
        padding: 10px;
        selection-background-color: transparent;
    }}
    
    QScrollArea {{
        background-color: {COLORS['bg_secondary']};
        border: 2px solid {COLORS['border']};
        border-radius: 12px;
    }}
    
    QScrollBar:vertical {{
        background-color: {COLORS['bg_tertiary']};
        width: 12px;
        border-radius: 6px;
        margin: 0;
    }}
    
    QScrollBar::handle:vertical {{
        background-color: {COLORS['accent']};
        border-radius: 6px;
        min-height: 20px;
    }}
    
    QScrollBar::handle:vertical:hover {{
        background-color: {COLORS['accent_hover']};
    }}
    
    QSplitter::handle {{
        background-color: {COLORS['border']};
        width: 2px;
    }}
    
    .stats-label {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                                   stop:0 {COLORS['bg_tertiary']}, 
                                   stop:1 {COLORS['bg_secondary']});
        border: 2px solid {COLORS['border']};
        border-radius: 10px;
        padding: 12px;
        font-size: 16px;
        font-weight: bold;
        color: {COLORS['text_primary']};
    }}
    
    .card-widget {{
        background-color: {COLORS['bg_secondary']};
        border: 2px solid {COLORS['border']};
        border-radius: 12px;
        padding: 8px;
    }}
    
    .card-widget:hover {{
        border-color: {COLORS['accent']};
        background-color: {COLORS['bg_tertiary']};
    }}
    
    .card-widget-insufficient {{
        background-color: {COLORS['error']};
        border: 2px solid {COLORS['error']};
        border-radius: 12px;
        padding: 8px;
    }}
    
    .card-widget-insufficient:hover {{
        border-color: {COLORS['error']};
        background-color: #f87171;
    }}
    
    QCheckBox {{
        color: {COLORS['text_primary']};
        font-size: 12px;
        spacing: 8px;
    }}
    
    QCheckBox::indicator {{
        width: 18px;
        height: 18px;
        border: 2px solid {COLORS['border']};
        border-radius: 4px;
        background-color: {COLORS['bg_secondary']};
    }}
    
    QCheckBox::indicator:hover {{
        border-color: {COLORS['accent_hover']};
        background-color: {COLORS['bg_tertiary']};
    }}
    
    QCheckBox::indicator:checked {{
        background-color: {COLORS['accent']};
        border-color: {COLORS['accent']};
    }}
    
    QGroupBox {{
        color: {COLORS['text_primary']};
        font-size: 14px;
        font-weight: bold;
        border: 2px solid {COLORS['border']};
        border-radius: 8px;
        margin-top: 12px;
        padding-top: 8px;
    }}
    
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 8px;
        padding: 0 8px 0 8px;
        background-color: {COLORS['bg_primary']};
    }}
    """

# ---------- Диалог основных фильтров ----------
COLORS = SHARED_COLORS
get_stylesheet = shared_get_stylesheet

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.db = CardRepository()
        self.cards = [CardModel(d) for d in self.db.get_all_cards()]
        self.state = AppState(cards=self.cards, filtered_cards=self.cards.copy())
        self.filtered_cards = self.cards.copy()

        # dynamic batch state
        self.start_index = 0
        self.end_index = 0

        # Состояние расширенных фильтров
        self.active_advanced_filters = []
        
        # Состояние основных фильтров
        self.main_filter_settings = {
            'cost_from': 0,
            'cost_to': 10,
            'cost_type': 'Все',
            'class_text': '',
            'elements': [],
            'sets': [],
            'cardtypes': [],
            'rarities': []
        }

        self.pixmap_cache = {}
        self.loading_image_ids = set()
        self.signal = SignalEmitter()
        self.signal.image_ready.connect(self.on_image_ready)
        self.thread_pool = QThreadPool()

        self.init_ui()
        self.preload_images()
        self.apply_filters()

    def init_ui(self):
        self.setWindowTitle("brsrk.s")
        self.setStyleSheet(get_stylesheet())

        # Устанавливаем красивый шрифт
        font = QFont("Segoe UI", 10)
        font.setStyleHint(QFont.SansSerif)
        self.setFont(font)

        main_v = QVBoxLayout()
        main_v.setContentsMargins(12, 12, 12, 12)
        main_v.setSpacing(8)

        # ---------------- Header (title + toggle buttons) ----------------
        header_frame = QFrame()
        header_frame.setStyleSheet("QFrame { background: transparent; }")
        header_row = QHBoxLayout(header_frame)
        header_row.setContentsMargins(0, 0, 0, 0)

        title_lbl = QLabel("brsrk.s")
        title_lbl.setFont(QFont("Segoe UI", 14, QFont.Bold))
        header_row.addWidget(title_lbl)

        header_row.addStretch(1)

        # Toggle filters button
        self.toggle_filters_btn = QPushButton("Фильтры ▲")
        self.toggle_filters_btn.setCheckable(True)
        self.toggle_filters_btn.setChecked(True)
        self.toggle_filters_btn.setToolTip("Скрыть/показать панель фильтров")
        self.toggle_filters_btn.setMaximumWidth(140)
        self.toggle_filters_btn.toggled.connect(self.toggle_filters)

        # Toggle deck controls button
        self.toggle_deck_controls_btn = QPushButton("Управление колодой ▲")
        self.toggle_deck_controls_btn.setCheckable(True)
        self.toggle_deck_controls_btn.setChecked(True)
        self.toggle_deck_controls_btn.setToolTip("Скрыть/показать кнопки и статистику колоды")
        self.toggle_deck_controls_btn.setMaximumWidth(210)
        self.toggle_deck_controls_btn.toggled.connect(self.toggle_deck_controls)

        self.draft_btn = QPushButton("Раздача")
        self.draft_btn.setToolTip("Открыть окно раздачи карт")
        self.draft_btn.setMaximumWidth(120)
        self.draft_btn.clicked.connect(self.open_draft)

        header_row.addWidget(self.draft_btn)
        header_row.addWidget(self.toggle_filters_btn)
        header_row.addWidget(self.toggle_deck_controls_btn)

        main_v.addWidget(header_frame)

        # ---------------- Main vertical splitter: filters (top) + main area (middle) ----------------
        main_splitter = QSplitter(Qt.Vertical)
        main_splitter.setChildrenCollapsible(False)

        # --- Filters frame ---
        filters_frame = QFrame()
        filters_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_secondary']};
                border: 2px solid {COLORS['border']};
                border-radius: 12px;
                padding: 8px;
            }}
        """)
        top_row = QHBoxLayout(filters_frame)
        top_row.setSpacing(12)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Поиск по имени или способности...")
        self.search_input.textChanged.connect(self.apply_filters)
        top_row.addWidget(self.search_input)

        # Сортировка с направлением
        self.sort_combo = QComboBox()
        self.sort_combo.addItems([
            "ID",
            "Название",
            "Стоимость",
            "Время добавления"  # новый элемент сортировки
        ])
        self.sort_combo.currentIndexChanged.connect(self.apply_filters)
        top_row.addWidget(self.sort_combo)
        
        self.sort_direction = QComboBox()
        self.sort_direction.addItems(["По возрастанию", "По убыванию"])
        self.sort_direction.currentIndexChanged.connect(self.apply_filters)
        top_row.addWidget(self.sort_direction)

        top_row.addWidget(QLabel("Количество ≥"))
        self.have_filter = QSpinBox()
        self.have_filter.setRange(0, 5)
        self.have_filter.setValue(0)
        self.have_filter.valueChanged.connect(self.apply_filters)
        top_row.addWidget(self.have_filter)

        # Кнопка основных фильтров
        self.main_filters_btn = QPushButton("Основные")
        self.main_filters_btn.setToolTip("Открыть окно основных фильтров")
        self.main_filters_btn.setMaximumWidth(160)
        self.main_filters_btn.setMinimumWidth(160)
        self.main_filters_btn.clicked.connect(self.open_main_filters)
        top_row.addWidget(self.main_filters_btn)

        # Кнопка расширенных фильтров
        self.advanced_filters_btn = QPushButton("Расширенные")
        self.advanced_filters_btn.setToolTip("Открыть окно расширенных фильтров")
        self.advanced_filters_btn.setMaximumWidth(160)
        self.advanced_filters_btn.setMinimumWidth(160)
        self.advanced_filters_btn.clicked.connect(self.open_advanced_filters)
        top_row.addWidget(self.advanced_filters_btn)

        # Новая кнопка сброса всех фильтров
        self.reset_all_filters_btn = QPushButton("Сбросить")
        self.reset_all_filters_btn.setToolTip("Сбросить все основные и расширенные фильтры")
        self.reset_all_filters_btn.setMaximumWidth(160)
        self.reset_all_filters_btn.setMinimumWidth(160)
        self.reset_all_filters_btn.clicked.connect(self.reset_all_filters)

        # Делаем кнопку красной (аналогично кнопке очистки колоды)
        self.reset_all_filters_btn.setStyleSheet(self.reset_all_filters_btn.styleSheet() + f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                                           stop:0 {COLORS['error']}, 
                                           stop:1 #e11d48);
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                                           stop:0 #fda4af, 
                                           stop:1 #f87171);
            }}
        """)

        top_row.addWidget(self.reset_all_filters_btn)
        
        # Метка с количеством найденных карт
        self.results_count_label = QLabel("Найдено: 0")
        self.results_count_label.setFixedWidth(140)
        self.results_count_label.setAlignment(Qt.AlignCenter)
        self.results_count_label.setStyleSheet(f"""
            background-color: {COLORS['bg_tertiary']};
            border: 1px solid {COLORS['border']};
            border-radius: 6px;
            padding: 8px 12px;
            font-weight: bold;
            color: {COLORS['success']};
        """)
        top_row.addWidget(self.results_count_label)

        # Ограничения высоты панели фильтров
        filters_frame.setMaximumHeight(80)
        filters_frame.setMinimumHeight(80)
        filters_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        main_splitter.addWidget(filters_frame)

        # ---------------- Middle splitter: catalog (left) + deck (right) ----------------
        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)

        # LEFT: catalog list
        catalog_frame = QFrame()
        catalog_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_secondary']};
                border: 2px solid {COLORS['border']};
                border-radius: 12px;
            }}
        """)
        catalog_layout = QVBoxLayout(catalog_frame)
        catalog_layout.setContentsMargins(8, 8, 8, 8)
        catalog_layout.setSpacing(8)

        self.list_widget = QListWidget()
        self.list_widget.setViewMode(QListWidget.IconMode)
        self.list_widget.setResizeMode(QListWidget.Adjust)
        self.list_widget.setGridSize(CATALOG_CELL_SIZE)
        self.list_widget.setUniformItemSizes(True)
        self.list_widget.setSpacing(12)
        self.list_widget.setMovement(QListWidget.Static)
        self.list_widget.setDragEnabled(True)
        self.list_widget.verticalScrollBar().valueChanged.connect(self.on_scroll)
        catalog_layout.addWidget(self.list_widget)

        splitter.addWidget(catalog_frame)

        # RIGHT: deck area
        deck_frame = QFrame()
        deck_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_secondary']};
                border: 2px solid {COLORS['border']};
                border-radius: 12px;
            }}
        """)
        deck_layout = QVBoxLayout(deck_frame)
        deck_layout.setContentsMargins(8, 8, 8, 8)
        deck_layout.setSpacing(12)

        # btn_frame (кнопки)
        btn_frame = QFrame()
        btn_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_tertiary']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                padding: 4px;
            }}
        """)
        btn_row = QHBoxLayout(btn_frame)
        btn_row.setSpacing(8)

        self.save_btn = QPushButton("Сохранить")
        self.save_btn.clicked.connect(self.save_deck_dialog)
        self.save_btn.setToolTip("Сохранить колоду в файл")
        self.save_btn.setMinimumWidth(120)  # было 100, стало 85

        self.load_btn = QPushButton("Загрузить")
        self.load_btn.clicked.connect(self.load_deck_dialog)
        self.load_btn.setToolTip("Загрузить колоду из файла")
        self.load_btn.setMinimumWidth(120)  # было 100, стало 85
        
        # Новая кнопка "Наличие"
        self.availability_btn = QPushButton("Наличие")
        self.availability_btn.setCheckable(True)
        self.availability_btn.setChecked(False)
        self.availability_btn.setToolTip("Показать карты с недостаточным количеством красным фоном")
        self.availability_btn.clicked.connect(self.toggle_availability_check)
        self.availability_btn.setMinimumWidth(120)  # было 100, стало 85

        # Новая кнопка "Автосорт"
        self.autosort_btn = QPushButton("Автосорт")
        self.autosort_btn.setToolTip("Отсортировать колоду по ID карт")
        self.autosort_btn.clicked.connect(self.auto_sort_deck)
        self.autosort_btn.setMinimumWidth(120)  # было 100, стало 85

        self.clear_btn = QPushButton("Очистить")
        self.clear_btn.clicked.connect(self.on_clear_deck)
        self.clear_btn.setToolTip("Очистить всю колоду")
        self.clear_btn.setMinimumWidth(120)  # было 100, стало 85
        
        # окрашиваем кнопку очистки отдельно
        self.clear_btn.setStyleSheet(self.clear_btn.styleSheet() + f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                                           stop:0 {COLORS['error']}, 
                                           stop:1 #e11d48);
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                                           stop:0 #fda4af, 
                                           stop:1 #f87171);
            }}
        """)

        btn_row.addWidget(self.save_btn)
        btn_row.addWidget(self.load_btn)
        btn_row.addWidget(self.availability_btn)
        btn_row.addWidget(self.autosort_btn)
        btn_row.addWidget(self.clear_btn)

        # DECK_WIDGET: само содержимое колоды
        self.deck_widget = DeckWidget(self.pixmap_cache)
        self.deck_widget.set_all_cards_reference(self.cards)  # передаем ссылку на все карты

        # deck_controls_frame: содержит btn_frame + stats_label
        deck_controls_frame = QFrame()
        deck_controls_frame.setStyleSheet(f"""
            QFrame {{
                background-color: transparent;
            }}
        """)
        controls_layout = QVBoxLayout(deck_controls_frame)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setSpacing(8)
        controls_layout.addWidget(btn_frame)
        controls_layout.addWidget(self.deck_widget.stats_label)

        # сохраняем ссылку, чтобы можно было скрывать/показывать
        self._deck_controls_frame = deck_controls_frame

        # добавляем controls_frame и затем сам deck_widget
        deck_layout.addWidget(deck_controls_frame)
        deck_layout.addWidget(self.deck_widget, 1)

        splitter.addWidget(deck_frame)

        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)
        splitter.setSizes([800, 600])

        main_splitter.addWidget(splitter)

        # добавляем главный сплиттер в layout
        main_v.addWidget(main_splitter)
        self.setLayout(main_v)
        self.showMaximized()

        # сохраняем фильтр-фрейм для управления видимостью
        self._filters_frame = filters_frame
        self._main_splitter = main_splitter

    def refresh_card_data(self):
        """Обновляет данные карт из БД - нужно для обновления datetime_updated"""
        try:
            # Получаем свежие данные из БД
            fresh_data = {card["id"]: card for card in self.db.get_all_cards()}
            
            # Обновляем существующие объекты карт
            for card in self.cards:
                if card.id in fresh_data:
                    fresh_card_data = fresh_data[card.id]
                    # Обновляем have и datetime_updated
                    card.have = fresh_card_data.get("have", 0)
                    card.datetime_updated = fresh_card_data.get("datetime_updated", None)
        except Exception:
            pass

    def toggle_availability_check(self):
        """Переключить проверку наличия карт в колоде"""
        enabled = self.availability_btn.isChecked()
        
        # Обновляем данные карт перед проверкой наличия
        if enabled:
            self.refresh_card_data()
            # Обновляем ссылку на актуальные данные в deck_widget
            self.deck_widget.set_all_cards_reference(self.cards)
        
        self.deck_widget.toggle_availability_check(enabled)

    def auto_sort_deck(self):
        """Автосортировка колоды"""
        self.deck_widget.auto_sort_deck()
        QMessageBox.information(self, "Готово", "Колода отсортирована по ID!")

    # ---------- Main Filters ----------
    def open_main_filters(self):
        """Открыть окно основных фильтров"""
        dialog = MainFiltersDialog(self, self.cards)
        dialog.set_filter_settings(self.main_filter_settings)
        
        if dialog.exec_() == QDialog.Accepted:
            self.main_filter_settings = dialog.get_filter_settings()
            self.apply_filters()
            
            # Обновляем текст кнопки, показывая количество активных фильтров
            active_count = 0
            if (self.main_filter_settings.get('cost_from', 0) > 0 or
                self.main_filter_settings.get('cost_to', 10) < 10 or
                self.main_filter_settings.get('cost_type', 'Все') != 'Все'):
                active_count += 1
            if self.main_filter_settings['class_text']:
                active_count += 1
            active_count += len(self.main_filter_settings['elements'])
            active_count += len(self.main_filter_settings['sets'])
            active_count += len(self.main_filter_settings['cardtypes'])
            active_count += len(self.main_filter_settings['rarities'])
            
            if active_count > 0:
                self.main_filters_btn.setText(f"Основные ({active_count})")
            else:
                self.main_filters_btn.setText("Основные")

    # ---------- Advanced Filters ----------
    def open_advanced_filters(self):
        """Открыть окно расширенных фильтров"""
        dialog = AdvancedFiltersDialog(self)
        dialog.set_active_filters(self.active_advanced_filters)
        
        if dialog.exec_() == QDialog.Accepted:
            self.active_advanced_filters = dialog.get_active_filters()
            self.apply_filters()
            
            # Обновляем текст кнопки, показывая количество активных фильтров
            if self.active_advanced_filters:
                self.advanced_filters_btn.setText(f"Расширенные ({len(self.active_advanced_filters)})")
            else:
                self.advanced_filters_btn.setText("Расширенные")

    def check_advanced_filters(self, card):
        return matches_advanced_filters(card, self.active_advanced_filters)

    def check_main_filters(self, card):
        return matches_main_filters(card, self.main_filter_settings)

    def reset_all_filters(self):
        """Сбрасывает все фильтры (основные, расширенные, строку поиска и количество)"""
        # Сброс строки поиска и фильтра "Количество ≥"
        self.search_input.clear()
        self.have_filter.setValue(0)

        # Сброс основных фильтров
        self.main_filter_settings = {
            'cost_from': 0,
            'cost_to': 10,
            'cost_type': 'Все',
            'class_text': '',
            'elements': [],
            'sets': [],
            'cardtypes': [],
            'rarities': []
        }
        self.main_filters_btn.setText("Основные")

        # Сброс расширенных фильтров
        self.active_advanced_filters = []
        self.advanced_filters_btn.setText("Расширенные")

        # Применить изменения
        self.apply_filters()

    

    # ---------- Toggle handlers ----------
    def toggle_filters(self, visible: bool):
        try:
            self._filters_frame.setVisible(visible)
            # обновляем текст кнопки
            if visible:
                self.toggle_filters_btn.setText("Фильтры ▲")
            else:
                self.toggle_filters_btn.setText("Фильтры ▼")
        except Exception:
            pass

    def toggle_deck_controls(self, visible: bool):
        try:
            self._deck_controls_frame.setVisible(visible)
            if visible:
                self.toggle_deck_controls_btn.setText("Управление колодой ▲")
            else:
                self.toggle_deck_controls_btn.setText("Управление колодой ▼")
        except Exception:
            pass

    # ---------- Dynamic population (batch loading) ----------
    def populate_next_batch(self):
        if self.end_index >= len(self.filtered_cards):
            return

        batch = self.filtered_cards[self.end_index:self.end_index + BATCH_SIZE]
        self.load_images_for_cards(batch)
        for card in batch:
            # avoid duplicates in QList
            duplicate = False
            for i in range(self.list_widget.count()):
                w = self.list_widget.itemWidget(self.list_widget.item(i))
                if w and getattr(w, "card", None) and w.card.id == card.id:
                    duplicate = True
                    break
            if not duplicate:
                item = QListWidgetItem()
                w = CardWidget(card, db=self.db, pixmap_cache=self.pixmap_cache, 
                             refresh_callback=self.refresh_card_data)  # Добавляем callback
                item.setSizeHint(CATALOG_CELL_SIZE)
                self.list_widget.addItem(item)
                self.list_widget.setItemWidget(item, w)

        self.end_index += len(batch)

        # Ограничиваем количество загруженных виджетов
        while self.list_widget.count() > MAX_LOADED:
            item = self.list_widget.takeItem(0)
            if item:
                widget = self.list_widget.itemWidget(item)
                if widget:
                    widget.setParent(None)
                    widget.deleteLater()
            self.start_index += 1

    def populate_prev_batch(self):
        if self.start_index == 0:
            return

        next_start = max(self.start_index - BATCH_SIZE, 0)
        batch = self.filtered_cards[next_start:self.start_index]
        self.load_images_for_cards(batch)

        for i, card in enumerate(batch):
            item = QListWidgetItem()
            w = CardWidget(card, db=self.db, pixmap_cache=self.pixmap_cache,
                         refresh_callback=self.refresh_card_data)  # Добавляем callback
            item.setSizeHint(CATALOG_CELL_SIZE)
            self.list_widget.insertItem(i, item)
            self.list_widget.setItemWidget(item, w)

        self.start_index = next_start

        # Ограничиваем снизу
        while self.list_widget.count() > MAX_LOADED:
            item = self.list_widget.takeItem(self.list_widget.count() - 1)
            if item:
                widget = self.list_widget.itemWidget(item)
                if widget:
                    widget.setParent(None)
                    widget.deleteLater()
            self.end_index -= 1

    def on_scroll(self, value):
        sb = self.list_widget.verticalScrollBar()
        if value + sb.pageStep() >= sb.maximum() - 50:  # Предзагрузка
            self.populate_next_batch()
        if value <= sb.pageStep() + 50:  # Предзагрузка в обратную сторону
            self.populate_prev_batch()

    # ---------- Filters / search / sort ----------
    def apply_filters(self):
        try:
            s = self.search_input.text().lower()
            sort_choice = self.sort_combo.currentText()
            sort_desc = self.sort_direction.currentIndex() == 1  # 1 = По убыванию

            filtered = []
            for c in self.cards:
                # проверка фильтра "Количество ≥" (верхняя панель)
                if self.have_filter.value() > 0 and getattr(c, "have", 0) < self.have_filter.value():
                    continue

                # проверка основных фильтров (стоимость, класс, стихии и т.п.)
                if not self.check_main_filters(c):
                    continue

                # поиск по имени/способности
                if s:
                    name_match = s in (c.name or "").lower()
                    ability_match = s in (c.ability or "").lower()
                    if not (name_match or ability_match):
                        continue

                # проверка расширенных фильтров
                if not self.check_advanced_filters(c):
                    continue

                filtered.append(c)

            filtered = sort_cards(filtered, sort_choice, sort_desc)

            self.filtered_cards = filtered
            self.state.filtered_cards = filtered

            # Обновляем счетчик результатов
            self.results_count_label.setText(f"Найдено: {len(filtered)}")

            # Очищаем список аккуратно
            while self.list_widget.count() > 0:
                item = self.list_widget.takeItem(0)
                if item:
                    widget = self.list_widget.itemWidget(item)
                    if widget:
                        widget.setParent(None)
                        widget.deleteLater()

            self.start_index = 0
            self.end_index = 0
            self.populate_next_batch()

        except Exception:
            pass

    # ---------- Save / Load / Clear deck dialogs ----------
    def save_deck_dialog(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить колоду", "", "JSON files (*.json)")
        if not path:
            return
        
        try:
            # Сохраняем JSON колоды
            self.deck_widget.save_deck(path)
            
            # Получаем имя колоды из пути файла (без расширения)
            deck_name = os.path.splitext(os.path.basename(path))[0]
            
            # Генерируем изображение колоды
            try:
                stats_text = self.deck_widget.stats_label.text()
                image_path = generate_deck_image_wrapper(deck_name, self.deck_widget.cards, stats_text)
                
                if image_path:
                    QMessageBox.information(self, "Успех",
                                            f"Колода успешно сохранена!\n{path}\n\n"
                                            f"Изображение колоды создано:\n{image_path}")
                else:
                    QMessageBox.information(self, "Частичный успех",
                                            f"Колода успешно сохранена!\n{path}\n\n"
                                            f"Не удалось создать изображение колоды.")
            except Exception as img_error:
                QMessageBox.information(self, "Частичный успех",
                                        f"Колода успешно сохранена!\n{path}\n\n"
                                        f"Не удалось создать изображение колоды: {str(img_error)}")
                
        except Exception as e:
            QMessageBox.critical(self, "Ошибка",
                                 f"Не удалось сохранить колоду:\n{str(e)}")

    def load_deck_dialog(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Загрузить колоду", "", "JSON files (*.json)")
        if not path:
            return
        try:
            self.deck_widget.load_deck(path, self.cards)
            # The deck can contain cards that are outside the currently visible catalog batch.
            self.load_images_for_cards(self.deck_widget.cards)
            QMessageBox.information(self, "Успех",
                                    f"Колода успешно загружена!\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка",
                                 f"Не удалось загрузить колоду:\n{str(e)}")

    def on_clear_deck(self):
        reply = QMessageBox.question(
            self, "Очистить колоду",
            "Вы уверены, что хотите очистить всю колоду?\nЭто действие нельзя отменить.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No)

        if reply == QMessageBox.Yes:
            self.deck_widget.clear_deck()
            QMessageBox.information(self, "Готово", "Колода очищена!")

    # ---------- Preload images in background ----------
    def preload_images(self):
        self.load_images_for_cards(self.cards[:BATCH_SIZE])

    def load_images_for_cards(self, cards):
        """Queue only missing images for the cards currently entering the view."""
        for c in cards:
            if resolve_image_path(c.image_path):
                if c.id in self.pixmap_cache or c.id in self.loading_image_ids:
                    continue
                self.loading_image_ids.add(c.id)
                loader = ImageLoader(c, self.pixmap_cache, self.signal)
                self.thread_pool.start(loader)

    def on_image_ready(self, card_id):
        self.loading_image_ids.discard(card_id)
        try:
            # catalog thumbnails
            for i in range(self.list_widget.count()):
                item = self.list_widget.item(i)
                if not item:
                    continue
                w = self.list_widget.itemWidget(item)
                if w and getattr(w, "card", None) and w.card.id == card_id:
                    pm = self.pixmap_cache.get(card_id)
                    if pm:
                        w.img_label.setPixmap(pm)
                        # Убираем текст загрузки и обновляем стиль
                        w.img_label.setStyleSheet(f"""
                            border: 2px solid {COLORS['border']};
                            border-radius: 8px;
                            background-color: {COLORS['bg_tertiary']};
                        """)
                        item.setSizeHint(CATALOG_CELL_SIZE)
                    break

            # deck thumbnails (may be duplicates)
            if hasattr(self, "deck_widget"):
                for i in range(self.deck_widget.grid.count()):
                    it = self.deck_widget.grid.itemAt(i)
                    if not it:
                        continue
                    w = it.widget()
                    if w and getattr(w, "card", None) and w.card.id == card_id:
                        pm = self.pixmap_cache.get(card_id)
                        if pm:
                            w.img_label.setPixmap(pm)
                            w.img_label.setStyleSheet(f"""
                                border: 2px solid {COLORS['border']};
                                border-radius: 8px;
                                background-color: {COLORS['bg_tertiary']};
                            """)
        except Exception:
            pass

    def open_draft(self):
        """Открывает окно раздачи карт"""
        try:
            open_draft_dialog(self, self.deck_widget, self.pixmap_cache)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", 
                               f"Не удалось открыть окно раздачи:\n{str(e)}")

    def closeEvent(self, event):
        try:
            # Очищаем кеш изображений
            self.pixmap_cache.clear()
            # Останавливаем пул потоков
            self.thread_pool.waitForDone(3000)  # Ждем максимум 3 секунды
            # Закрываем БД
            self.db.close()
        except Exception:
            pass
        finally:
            event.accept()


# ---------- Запуск ----------
if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Устанавливаем глобальную тему
    app.setStyle('Fusion')

    # Настраиваем палитру для темной темы
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(COLORS['bg_primary']))
    palette.setColor(QPalette.WindowText, QColor(COLORS['text_primary']))
    palette.setColor(QPalette.Base, QColor(COLORS['bg_secondary']))
    palette.setColor(QPalette.AlternateBase, QColor(COLORS['bg_tertiary']))
    palette.setColor(QPalette.ToolTipBase, QColor(COLORS['bg_tertiary']))
    palette.setColor(QPalette.ToolTipText, QColor(COLORS['text_primary']))
    palette.setColor(QPalette.Text, QColor(COLORS['text_primary']))
    palette.setColor(QPalette.Button, QColor(COLORS['bg_secondary']))
    palette.setColor(QPalette.ButtonText, QColor(COLORS['text_primary']))
    palette.setColor(QPalette.BrightText, QColor(COLORS['accent']))
    palette.setColor(QPalette.Link, QColor(COLORS['accent']))
    palette.setColor(QPalette.Highlight, QColor(COLORS['accent']))
    palette.setColor(QPalette.HighlightedText, QColor('#000000'))
    app.setPalette(palette)

    w = MainWindow()
    w.show()
    sys.exit(app.exec_())
