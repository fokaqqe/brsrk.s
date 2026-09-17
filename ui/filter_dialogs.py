"""Filter dialogs."""

from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QPushButton, QLabel, QSpinBox, QComboBox, QLineEdit, QCheckBox, QGroupBox
from app_theme import get_stylesheet
class MainFiltersDialog(QDialog):
    def __init__(self, parent=None, cards=None):
        super().__init__(parent)
        self.cards = cards or []
        self.setWindowTitle("Основные фильтры")
        self.setModal(True)
        self.setStyleSheet(get_stylesheet())
        self.resize(800, 700)
        
        # Словарь для хранения состояния чекбоксов
        self.element_checkboxes = {}
        self.set_checkboxes = {}
        self.cardtype_checkboxes = {}
        self.rarity_checkboxes = {}
        
        self.init_ui()
        
    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(16)
        
        # Скролл область для фильтров
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setSpacing(12)
        
        # Группа "Стоимость"
        cost_group = QGroupBox("Стоимость")
        cost_layout = QHBoxLayout(cost_group)

        cost_layout.addWidget(QLabel("От"))
        self.cost_from = QSpinBox()
        self.cost_from.setRange(0, 10)
        self.cost_from.setValue(0)
        cost_layout.addWidget(self.cost_from)

        cost_layout.addWidget(QLabel("До"))
        self.cost_to = QSpinBox()
        self.cost_to.setRange(0, 10)
        self.cost_to.setValue(10)
        cost_layout.addWidget(self.cost_to)

        # Тип стоимости (Все / Серебро / Золото)
        self.cost_type_combo = QComboBox()
        self.cost_type_combo.addItems(["Все", "Серебро", "Золото"])
        cost_layout.addWidget(self.cost_type_combo)

        scroll_layout.addWidget(cost_group)
        
        # Группа стихий
        elements_group = QGroupBox("Стихии")
        elements_layout = QGridLayout(elements_group)
        elements_layout.setSpacing(8)
        
        elements = sorted(set(c.element for c in self.cards if c.element))
        for i, element in enumerate(elements):
            checkbox = QCheckBox(element)
            self.element_checkboxes[element] = checkbox
            elements_layout.addWidget(checkbox, i // 3, i % 3)
        
        scroll_layout.addWidget(elements_group)
        
        # Группа выпусков
        sets_group = QGroupBox("Выпуски")
        sets_layout = QGridLayout(sets_group)
        sets_layout.setSpacing(8)
        
        sets = list(dict.fromkeys(c.set_name for c in self.cards if c.set_name))
        n = len(sets)
        rows = (n + 1) // 2  # сколько строк будет в первом столбце

        for i, set_name in enumerate(sets):
            row = i % rows       # строка (идём вниз)
            col = i // rows      # столбец (сначала 0, потом 1)
            checkbox = QCheckBox(set_name)
            self.set_checkboxes[set_name] = checkbox
            sets_layout.addWidget(checkbox, row, col)

        
        scroll_layout.addWidget(sets_group)
        
        # Группа класса
        class_group = QGroupBox("Класс")
        class_layout = QHBoxLayout(class_group)
        self.class_input = QLineEdit()
        self.class_input.setPlaceholderText("Поиск по полю 'class'...")
        class_layout.addWidget(self.class_input)
        
        scroll_layout.addWidget(class_group)
        
        # Группа типов карт
        cardtype_group = QGroupBox("Тип карты")
        cardtype_layout = QGridLayout(cardtype_group)
        cardtype_layout.setSpacing(8)
        
        cardtypes = [
            "Существо",
            "Существо – Летающее", 
            "Существо – Паразит",
            "Существо – Компаньон",
            "Местность",
            "Артефакт"
        ]
        
        for i, cardtype in enumerate(cardtypes):
            checkbox = QCheckBox(cardtype)
            self.cardtype_checkboxes[cardtype] = checkbox
            cardtype_layout.addWidget(checkbox, i // 2, i % 2)
        
        scroll_layout.addWidget(cardtype_group)
        
        # Группа редкости
        rarity_group = QGroupBox("Редкость")
        rarity_layout = QGridLayout(rarity_group)
        rarity_layout.setSpacing(8)
        
        rarities = ["Частая", "Необычная", "Редкая", "Ультраредкая"]
        
        for i, rarity in enumerate(rarities):
            checkbox = QCheckBox(rarity)
            self.rarity_checkboxes[rarity] = checkbox
            rarity_layout.addWidget(checkbox, i // 2, i % 2)
        
        scroll_layout.addWidget(rarity_group)
        
        scroll.setWidget(scroll_widget)
        main_layout.addWidget(scroll)
        
        # Кнопки управления
        buttons_layout = QHBoxLayout()
        
        clear_all_btn = QPushButton("Сбросить все")
        clear_all_btn.clicked.connect(self.clear_all_filters)
        buttons_layout.addWidget(clear_all_btn)
        
        buttons_layout.addStretch()
        
        cancel_btn = QPushButton("Отмена")
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)
        
        apply_btn = QPushButton("Применить")
        apply_btn.clicked.connect(self.accept)
        buttons_layout.addWidget(apply_btn)
        
        main_layout.addLayout(buttons_layout)
        self.setLayout(main_layout)
    
    def clear_all_filters(self):
        """Сбросить все чекбоксы и поля"""
        self.cost_from.setValue(0)
        self.cost_to.setValue(10)
        self.cost_type_combo.setCurrentIndex(0)
        self.class_input.clear()
        
        for checkbox in self.element_checkboxes.values():
            checkbox.setChecked(False)
        for checkbox in self.set_checkboxes.values():
            checkbox.setChecked(False)
        for checkbox in self.cardtype_checkboxes.values():
            checkbox.setChecked(False)
        for checkbox in self.rarity_checkboxes.values():
            checkbox.setChecked(False)
    
    def get_filter_settings(self):
        """Получить настройки фильтров"""
        # нормализуем тип стоимости (без эмодзи)
        type_text = self.cost_type_combo.currentText()
        
        return {
            'cost_from': self.cost_from.value(),
            'cost_to': self.cost_to.value(),
            'cost_type': type_text,
            'class_text': self.class_input.text(),
            'elements': [k for k, v in self.element_checkboxes.items() if v.isChecked()],
            'sets': [k for k, v in self.set_checkboxes.items() if v.isChecked()],
            'cardtypes': [k for k, v in self.cardtype_checkboxes.items() if v.isChecked()],
            'rarities': [k for k, v in self.rarity_checkboxes.items() if v.isChecked()]
        }

    
    def set_filter_settings(self, settings):
        """Установить настройки фильтров"""
        self.cost_from.setValue(settings.get('cost_from', 0))
        self.cost_to.setValue(settings.get('cost_to', 10))
        cost_type = settings.get('cost_type', 'Все')
        self.cost_type_combo.setCurrentText(cost_type)

        self.class_input.setText(settings.get('class_text', ''))
        
        for element in settings.get('elements', []):
            if element in self.element_checkboxes:
                self.element_checkboxes[element].setChecked(True)
        
        for set_name in settings.get('sets', []):
            if set_name in self.set_checkboxes:
                self.set_checkboxes[set_name].setChecked(True)
                
        for cardtype in settings.get('cardtypes', []):
            if cardtype in self.cardtype_checkboxes:
                self.cardtype_checkboxes[cardtype].setChecked(True)
                
        for rarity in settings.get('rarities', []):
            if rarity in self.rarity_checkboxes:
                self.rarity_checkboxes[rarity].setChecked(True)


# ---------- Диалог расширенных фильтров ----------
class AdvancedFiltersDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Расширенные фильтры")
        self.setModal(True)
        self.setStyleSheet(get_stylesheet())
        self.resize(600, 500)
        
        # Словарь для хранения состояния чекбоксов
        self.checkboxes = {}
        
        self.init_ui()
        
    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(16)
        
        # Скролл область для фильтров
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setSpacing(12)
        
        # Группа защит
        protection_group = QGroupBox("Защиты")
        protection_layout = QGridLayout(protection_group)
        protection_layout.setSpacing(8)
        
        protection_filters = [
            ("poison_resist", "Защ. от яда"),
            ("throw_resist", "Защ. от метания"),
            ("shoot_resist", "Защ. от выстрелов"),
            ("spell_resist", "Защ. от заклинаний"),
            ("lightning_resist", "Защ. от разрядов"),
            ("magic_resist", "Защ. от магии"),
            ("flying_resist", "Защ. от летающих"),
        ]
        
        for i, (key, label) in enumerate(protection_filters):
            checkbox = QCheckBox(label)
            self.checkboxes[key] = checkbox
            protection_layout.addWidget(checkbox, i // 2, i % 2)
        
        scroll_layout.addWidget(protection_group)
        
        # Группа опыта
        experience_group = QGroupBox("Опыт")
        experience_layout = QGridLayout(experience_group)
        experience_layout.setSpacing(8)
        
        experience_filters = [
            ("defense_exp", "Опыт в защите"),
            ("attack_exp", "Опыт в атаке"),
            ("shooting_exp", "Опыт в стрельбе"),
        ]
        
        for i, (key, label) in enumerate(experience_filters):
            checkbox = QCheckBox(label)
            self.checkboxes[key] = checkbox
            experience_layout.addWidget(checkbox, i // 2, i % 2)
        
        scroll_layout.addWidget(experience_group)
        
        # Группа особых способностей
        special_group = QGroupBox("Особые способности")
        special_layout = QGridLayout(special_group)
        special_layout.setSpacing(8)
        
        special_filters = [
            ("regeneration", "Регенерация"),
            ("armor", "Броня"),
            ("direct_strike", "Направленный удар"),
            ("stability", "Стойкость"),
        ]
        
        for i, (key, label) in enumerate(special_filters):
            checkbox = QCheckBox(label)
            self.checkboxes[key] = checkbox
            special_layout.addWidget(checkbox, i // 2, i % 2)
        
        scroll_layout.addWidget(special_group)
        
        scroll.setWidget(scroll_widget)
        main_layout.addWidget(scroll)
        
        # Кнопки управления
        buttons_layout = QHBoxLayout()
        
        clear_all_btn = QPushButton("Сбросить все")
        clear_all_btn.clicked.connect(self.clear_all_filters)
        buttons_layout.addWidget(clear_all_btn)
        
        buttons_layout.addStretch()
        
        cancel_btn = QPushButton("Отмена")
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)
        
        apply_btn = QPushButton("Применить")
        apply_btn.clicked.connect(self.accept)
        buttons_layout.addWidget(apply_btn)
        
        main_layout.addLayout(buttons_layout)
        self.setLayout(main_layout)
    
    def clear_all_filters(self):
        """Сбросить все чекбоксы"""
        for checkbox in self.checkboxes.values():
            checkbox.setChecked(False)
    
    def get_active_filters(self):
        """Получить список активных фильтров"""
        active = []
        for key, checkbox in self.checkboxes.items():
            if checkbox.isChecked():
                active.append(key)
        return active
    
    def set_active_filters(self, filters):
        """Установить активные фильтры"""
        for key, checkbox in self.checkboxes.items():
            checkbox.setChecked(key in filters)

# ---------- Сигнал ----------
