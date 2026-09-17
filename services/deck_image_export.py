import os
import sys
import re
from PIL import Image, ImageDraw, ImageFont
from typing import List
import locale
from pathlib import Path
from services.image_paths import resolve_image_path
locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8' if sys.platform != 'win32' else 'Russian_Russia.1251')


def clean_text_from_emojis(text):
    """Убирает смодзи из текста, оставляя только текст"""
    # Паттерн для удаления смодзи (Unicode символы)
    emoji_pattern = re.compile("["
                             u"\U0001F600-\U0001F64F"  # emoticons
                             u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                             u"\U0001F680-\U0001F6FF"  # transport & map symbols
                             u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                             u"\U00002700-\U000027BF"  # dingbats
                             u"\U0001f926-\U0001f937"
                             u"\U00010000-\U0010ffff"
                             u"\u2640-\u2642"
                             u"\u2600-\u2B55"
                             u"\u200d"
                             u"\u23cf"
                             u"\u23e9"
                             u"\u231a"
                             u"\ufe0f"  # dingbats
                             u"\u3030"
                             "]+", flags=re.UNICODE)
    
    # Убираем смодзи
    clean_text = emoji_pattern.sub(' ', text)  # заменяем на пробел вместо пустоты
    
    # Очищаем только лишние пробелы, НЕ трогаем переносы строк
    clean_text = re.sub(r'[ \t]+', ' ', clean_text)  # только пробелы и табы
    clean_text = clean_text.strip()
    
    return clean_text

def get_emoji_supporting_font(size):
    """Получает шрифт с поддержкой смодзи"""
    emoji_fonts = [
        # Windows
        "C:/Windows/Fonts/seguiemj.ttf",  # Segoe UI Emoji
        "C:/Windows/Fonts/NotoColorEmoji.ttf",
        # macOS
        "/System/Library/Fonts/Apple Color Emoji.ttc",
        "/Library/Fonts/Apple Color Emoji.ttc",
        # Linux
        "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf",
        "/usr/share/fonts/TTF/NotoColorEmoji.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    
    for font_path in emoji_fonts:
        try:
            if os.path.exists(font_path):
                return ImageFont.truetype(font_path, size)
        except Exception:
            continue
    
    # Если не найден специальный шрифт, возвращаем обычный
    return ImageFont.load_default()

def draw_text_with_emoji_fallback(draw, position, text, fill, font):
    """Рисует текст с попыткой рендеринга смодзи"""
    try:
        # Сначала пытаемся нарисовать весь текст обычным способом
        draw.text(position, text, fill=fill, font=font, anchor="mm")
    except Exception:
        # Если не получается, рисуем без смодзи
        clean_text = clean_text_from_emojis(text)
        draw.text(position, clean_text, fill=fill, font=font, anchor="mm")



class DeckImageGenerator:
    def __init__(self):
        # 4K разрешение в формате 4:3
        self.base_width = 2304
        self.base_height = 4300  # 4:3 соотношение
        
        # УВЕЛИЧЕННЫЕ размеры карт - основное изменение!
        self.card_width = 600   # Увеличено с 496
        self.card_height = 900  # Увеличено с 744
        
        # УМЕНЬШЕННЫЕ отступы и расстояния
        self.margin = 3          # Уменьшено с 5
        self.card_spacing = 15   # Уменьшено с 15
        self.header_height = 250 # Уменьшено с 250
        self.stats_height = 180  # Уменьшено с 180
        
        # Цвета из основного файла
        self.colors = {
            'bg_primary': '#1e1e2e',
            'bg_secondary': '#313244',
            'bg_tertiary': '#45475a',
            'accent': '#cba6f7',
            'accent_hover': '#b4befe',
            'text_primary': '#cdd6f4',
            'text_secondary': '#bac2de',
            'border': '#585b70',
            'success': '#a6e3a1',
        }
        
        # Создаем папку для изображений колод если её нет
        project_root = Path(__file__).resolve().parents[1]
        self.deck_images_path = str(project_root / "deckimages")
        os.makedirs(self.deck_images_path, exist_ok=True)
    
    def hex_to_rgb(self, hex_color):
        """Преобразует hex цвет в RGB"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def calculate_layout(self, card_count):
        """Вычисляет оптимальное расположение карт"""
        # Доступная ширина для карт
        available_width = self.base_width - 2 * self.margin
        # Доступная высота для карт (с учетом заголовка и статистики)
        available_height = self.base_height - self.header_height - self.stats_height - 2 * self.margin
        
        # ИЗМЕНЕНО: более агрессивные сетки для больших карт
        if card_count <= 20:
            # Для 20 карт: 4x5 сетка
            target_cols = 4
        elif card_count <= 25:
            # Для 25 карт: 5x5 сетка
            target_cols = 6
        elif card_count <= 30:
            # Для 30 карт: 6x5 сетка
            target_cols = 6
        elif card_count <= 35:
            # Для 35 карт: 7x5 сетка
            target_cols = 7
        elif card_count <= 40:
            # Для 40 карт: 8x5 сетка
            target_cols = 8
        elif card_count <= 45:
            # Для 45 карт: 9x5 сетка
            target_cols = 9
        else:
            # Для большего количества карт вычисляем динамически
            target_cols = min(10, (card_count + 4) // 5)
        
        # Максимальное количество карт в ряду с учетом доступной ширины
        max_possible_cols = (available_width + self.card_spacing) // (self.card_width + self.card_spacing)
        cards_per_row = min(target_cols, max_possible_cols)
        
        # Вычисляем количество строк
        rows = (card_count + cards_per_row - 1) // cards_per_row
        
        # Проверяем, помещаются ли все строки по высоте
        total_cards_height = rows * self.card_height + (rows - 1) * self.card_spacing
        
        if total_cards_height > available_height:
            # ИЗМЕНЕНО: менее агрессивное масштабирование, минимальный масштаб повышен
            scale_factor = available_height / total_cards_height
            scale_factor = max(scale_factor, 0.7)  # Минимальный масштаб 70% вместо 50%
            
            self.card_width = int(self.card_width * scale_factor)
            self.card_height = int(self.card_height * scale_factor)
            
            # Пересчитываем с новыми размерами
            max_possible_cols = (available_width + self.card_spacing) // (self.card_width + self.card_spacing)
            cards_per_row = min(target_cols, max_possible_cols)
            rows = (card_count + cards_per_row - 1) // cards_per_row
        
        return cards_per_row, rows
    
    def get_fallback_font(self, size):
        """Получает резервный шрифт если системный недоступен"""
        try:
            # Пытаемся загрузить системные шрифты (БЕЗ смодзи-шрифтов)
            font_paths = [
                "C:/Windows/Fonts/segoeui.ttf",  # Windows
                "C:/Windows/Fonts/arial.ttf",    # Windows альтернатива
                "/System/Library/Fonts/Helvetica.ttc",  # macOS
                "/System/Library/Fonts/Arial.ttf",       # macOS альтернатива
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",  # Linux
                "/usr/share/fonts/TTF/arial.ttf",  # Linux альтернатива
            ]
            
            for font_path in font_paths:
                if os.path.exists(font_path):
                    try:
                        font = ImageFont.truetype(font_path, size)
                        # Проверяем, может ли шрифт отрендерить русский текст
                        test_img = Image.new('RGB', (100, 100), (255, 255, 255))
                        test_draw = ImageDraw.Draw(test_img)
                        test_draw.text((10, 10), "Тест", fill=(0, 0, 0), font=font)
                        return font
                    except Exception:
                        continue
            
            # Если ничего не найдено, используем стандартный шрифт
            return ImageFont.load_default()
        except Exception:
            return ImageFont.load_default()
    
    def draw_text_safe(self, draw, position, text, fill, font):
        """Безопасно рисует текст, обрабатывая ошибки с кодировкой"""
        try:
            # Сначала пробуем нарисовать весь текст
            draw.text(position, text, fill=fill, font=font, anchor="mm")
        except Exception:
            try:
                # Если не получилось, очищаем от смодзи и пробуем снова
                clean_text = clean_text_from_emojis(text)
                draw.text(position, clean_text, fill=fill, font=font, anchor="mm")
            except Exception:
                # В крайнем случае рисуем заглушку
                draw.text(position, "[Ошибка отображения]", fill=fill, font=font, anchor="mm")
            
    def load_and_resize_card_image(self, card_image_path):
        """Загружает и изменяет размер изображения карты"""
        try:
            card_image_path = resolve_image_path(card_image_path)
            if not card_image_path:
                # Создаем заглушку для отсутствующих изображений
                placeholder = Image.new('RGB', (self.card_width, self.card_height), 
                                      self.hex_to_rgb(self.colors['bg_tertiary']))
                draw = ImageDraw.Draw(placeholder)
                font = self.get_fallback_font(20)
                draw.text((self.card_width//2, self.card_height//2), "НЕТ\nИЗОБРАЖЕНИЯ", 
                         fill=self.hex_to_rgb(self.colors['text_secondary']), 
                         font=font, anchor="mm")
                return placeholder
            
            card_img = Image.open(card_image_path)
            # Изменяем размер с сохранением пропорций
            card_img = card_img.resize((self.card_width, self.card_height), Image.Resampling.LANCZOS)
            return card_img
        except Exception:
            # Возвращаем заглушку
            placeholder = Image.new('RGB', (self.card_width, self.card_height), 
                                  self.hex_to_rgb(self.colors['bg_tertiary']))
            return placeholder
    
    def draw_gradient_background(self, draw, width, height):
        """Рисует градиентный фон"""
        bg_color = self.hex_to_rgb(self.colors['bg_primary'])
        secondary_color = self.hex_to_rgb(self.colors['bg_secondary'])
        
        for y in range(height):
            # Создаем градиент от bg_primary к bg_secondary
            ratio = y / height
            r = int(bg_color[0] * (1 - ratio) + secondary_color[0] * ratio)
            g = int(bg_color[1] * (1 - ratio) + secondary_color[1] * ratio)
            b = int(bg_color[2] * (1 - ratio) + secondary_color[2] * ratio)
            
            draw.line([(0, y), (width, y)], fill=(r, g, b))
    
    def generate_deck_image(self, deck_name, cards, stats_text, output_path=None):
        """Генерирует изображение колоды"""
        try:
            if not cards:
                raise ValueError("Колода пуста")
            
            card_count = len(cards)
            
            # Вычисляем макет
            cards_per_row, rows = self.calculate_layout(card_count)
            
            # Используем фиксированную высоту 4:3
            final_height = self.base_height
            
            # Создаем изображение
            img = Image.new('RGB', (self.base_width, final_height), 
                           self.hex_to_rgb(self.colors['bg_primary']))
            draw = ImageDraw.Draw(img)
            
            # Рисуем градиентный фон
            self.draw_gradient_background(draw, self.base_width, final_height)
            
            # Заголовок - УМЕНЬШЕННЫЙ размер шрифта для экономии места
            title_font = self.get_fallback_font(64)  # Уменьшено с 64
            title_y = self.margin + 20  # Уменьшено с 20
            
            # Рисуем фон для заголовка - УМЕНЬШЕННЫЙ
            title_bg_rect = [
                self.margin, title_y - 20,  # Уменьшено с 20
                self.base_width - self.margin, title_y + 80  # Уменьшено с 80
            ]
            draw.rounded_rectangle(title_bg_rect, radius=20,  # Уменьшено с 20
                                 fill=self.hex_to_rgb(self.colors['bg_secondary']),
                                 outline=self.hex_to_rgb(self.colors['accent']), width=3)  # Уменьшено с 3
            
            # Текст заголовка
            self.draw_text_safe(draw, (self.base_width // 2, title_y + 30), f"Колода: {deck_name}",  # Уменьшено с 30
                self.hex_to_rgb(self.colors['accent']), 
                title_font)
            
            # Статистика - УМЕНЬШЕННЫЕ размеры
            stats_y = title_y + 120  # Уменьшено с 120
            stats_font = self.get_fallback_font(32)  # Уменьшено с 32
            
            # Фон для статистики - УМЕНЬШЕННЫЙ
            stats_bg_rect = [
                self.margin, stats_y - 15,  # Уменьшено с 15
                self.base_width - self.margin, stats_y + self.stats_height - 30  # Уменьшено с 30
            ]
            draw.rounded_rectangle(stats_bg_rect, radius=15,  # Уменьшено с 15
                                 fill=self.hex_to_rgb(self.colors['bg_tertiary']),
                                 outline=self.hex_to_rgb(self.colors['border']), width=2)
            
            # Разбиваем статистику на строки - УМЕНЬШЕННЫЕ отступы
            clean_stats_text = clean_text_from_emojis(stats_text)
            stats_lines = clean_stats_text.strip().split('\n')
            line_height = 35  # Уменьшено с 35
            start_y = stats_y + 10  # Уменьшено с 10
            
            for i, line in enumerate(stats_lines):
                if i >= 4:  # Ограничиваем количество строк
                    break
                self.draw_text_safe(draw, (self.base_width // 2, start_y + i * line_height), line,
                         self.hex_to_rgb(self.colors['text_primary']),
                         stats_font)
            
            # Карты - центрируем по доступной области
            cards_start_y = stats_y + self.stats_height + 10  # Уменьшено с 20
            available_cards_height = self.base_height - cards_start_y - self.margin
            total_cards_height = rows * self.card_height + (rows - 1) * self.card_spacing
            
            # Центрируем карты вертикально в доступной области
            cards_y_offset = (available_cards_height - total_cards_height) // 2
            cards_start_y += max(0, cards_y_offset)
            
            # Вычисляем центрирование для карт по горизонтали
            total_cards_width = cards_per_row * self.card_width + (cards_per_row - 1) * self.card_spacing
            cards_start_x = (self.base_width - total_cards_width) // 2
            
            for i, card in enumerate(cards):
                row = i // cards_per_row
                col = i % cards_per_row
                
                # Для последней строки пересчитываем центрирование
                if row == rows - 1:
                    remaining_cards = card_count - row * cards_per_row
                    row_width = remaining_cards * self.card_width + (remaining_cards - 1) * self.card_spacing
                    x = (self.base_width - row_width) // 2 + col * (self.card_width + self.card_spacing)
                else:
                    x = cards_start_x + col * (self.card_width + self.card_spacing)
                
                y = cards_start_y + row * (self.card_height + self.card_spacing)
                
                # Загружаем и размещаем изображение карты
                card_img = self.load_and_resize_card_image(card.image_path)
                
                # Рисуем рамку вокруг карты - УМЕНЬШЕННАЯ
                border_rect = [x - 2, y - 2, x + self.card_width + 2, y + self.card_height + 3]  # Уменьшено с 3
                draw.rounded_rectangle(border_rect, radius=12,  # Уменьшено с 12
                                     fill=self.hex_to_rgb(self.colors['accent']), width=0)
                
                # Размещаем карту
                img.paste(card_img, (x, y))
            
            # Сохраняем изображение
            if output_path is None:
                output_path = os.path.join(self.deck_images_path, f"{deck_name}.jpg")
            
            # Конвертируем в RGB если нужно и сохраняем с высоким качеством
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            img.save(output_path, 'JPEG', quality=95, optimize=True)
            return output_path
            
        except Exception:
            raise

def generate_deck_image_wrapper(deck_name, cards, stats_text):
    """Обертка для использования в основном приложении"""
    try:
        generator = DeckImageGenerator()
        return generator.generate_deck_image(deck_name, cards, stats_text)
    except Exception:
        return None
