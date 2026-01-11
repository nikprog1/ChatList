from PIL import Image, ImageDraw
import math

def draw_icon(size):
    """Рисует розу в квадрате."""
    # Создаем RGB изображение с белым фоном
    img = Image.new("RGB", (size, size), (255, 255, 255))  # Белый фон
    draw = ImageDraw.Draw(img)
    
    # Центр изображения
    center_x = size // 2
    center_y = size // 2
    
    # Размер розы (80% от размера с отступами)
    padding = int(size * 0.15)
    max_radius = (size - padding * 2) // 2
    
    # Цвета для розы
    rose_pink = (255, 20, 147)  # Deep Pink - основной цвет розы
    rose_red = (220, 20, 60)    # Crimson - для внутренних лепестков
    rose_dark = (199, 21, 133)  # Medium Violet Red - для глубины
    green_stem = (34, 139, 34)  # Forest Green - для стебля и листьев
    
    # Рисуем стебель
    stem_width = max(2, size // 64)
    stem_bottom = size - padding
    stem_top = center_y + max_radius // 2
    stem_left = center_x - stem_width // 2
    stem_right = center_x + stem_width // 2
    draw.rectangle([stem_left, stem_top, stem_right, stem_bottom], fill=green_stem)
    
    # Рисуем листья
    leaf_size = max_radius // 3
    # Левый лист
    leaf1_center_x = center_x - max_radius // 2
    leaf1_center_y = center_y + max_radius // 3
    draw_leaf(draw, leaf1_center_x, leaf1_center_y, leaf_size, green_stem, -45)
    # Правый лист
    leaf2_center_x = center_x + max_radius // 2
    leaf2_center_y = center_y + max_radius // 3
    draw_leaf(draw, leaf2_center_x, leaf2_center_y, leaf_size, green_stem, 45)
    
    # Рисуем розу - несколько слоев лепестков
    # Внешние лепестки (большие)
    outer_petals = 8
    outer_radius = max_radius
    for i in range(outer_petals):
        angle = (i * 360 / outer_petals) * math.pi / 180
        petal_x = center_x + int(math.cos(angle) * outer_radius * 0.6)
        petal_y = center_y + int(math.sin(angle) * outer_radius * 0.6)
        petal_size = max_radius // 2
        draw_petal(draw, petal_x, petal_y, petal_size, rose_pink, angle)
    
    # Средние лепестки
    mid_petals = 6
    mid_radius = max_radius * 0.5
    for i in range(mid_petals):
        angle = (i * 360 / mid_petals + 30) * math.pi / 180
        petal_x = center_x + int(math.cos(angle) * mid_radius * 0.5)
        petal_y = center_y + int(math.sin(angle) * mid_radius * 0.5)
        petal_size = max_radius // 3
        draw_petal(draw, petal_x, petal_y, petal_size, rose_red, angle)
    
    # Внутренние лепестки (маленькие)
    inner_petals = 4
    inner_radius = max_radius * 0.25
    for i in range(inner_petals):
        angle = (i * 360 / inner_petals + 45) * math.pi / 180
        petal_x = center_x + int(math.cos(angle) * inner_radius * 0.4)
        petal_y = center_y + int(math.sin(angle) * inner_radius * 0.4)
        petal_size = max_radius // 4
        draw_petal(draw, petal_x, petal_y, petal_size, rose_dark, angle)
    
    # Центр розы
    center_radius = max(3, size // 32)
    draw.ellipse([
        center_x - center_radius,
        center_y - center_radius,
        center_x + center_radius,
        center_y + center_radius
    ], fill=(255, 215, 0))  # Золотистый центр
    
    return img

def draw_petal(draw, x, y, size, color, angle):
    """Рисует один лепесток розы."""
    # Создаем эллипс для лепестка
    petal_width = size
    petal_height = size * 1.3
    
    # Координаты эллипса
    coords = [
        x - petal_width // 2,
        y - petal_height // 2,
        x + petal_width // 2,
        y + petal_height // 2
    ]
    
    # Для простоты рисуем эллипс (вращение не применяем для маленьких размеров)
    draw.ellipse(coords, fill=color)

def draw_leaf(draw, x, y, size, color, rotation_angle):
    """Рисует лист розы."""
    # Простой лист в виде эллипса
    leaf_width = size
    leaf_height = size * 1.5
    
    coords = [
        x - leaf_width // 2,
        y - leaf_height // 2,
        x + leaf_width // 2,
        y + leaf_height // 2
    ]
    
    draw.ellipse(coords, fill=color)

# Размеры иконки
sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
icons = [draw_icon(s) for s, _ in sizes]

# Изображения уже в RGB режиме, просто убеждаемся
rgb_icons = []
for icon in icons:
    # Убеждаемся, что изображение в RGB режиме (не палитра)
    if icon.mode != "RGB":
        rgb_img = icon.convert("RGB")
    else:
        rgb_img = icon
    rgb_icons.append(rgb_img)

# Сохранение с явным указанием формата и цветов
# ВАЖНО: Изображения уже в RGB режиме с красным фоном, что гарантирует
# сохранение цветов и избегает автоматической конвертации в градации серого
try:
    rgb_icons[0].save(
        "app.ico",
        format="ICO",
        sizes=sizes,
        append_images=rgb_icons[1:]
    )
    print("Иконка 'app.ico' создана!")
    print("   Дизайн: роза со стеблем и листьями")
    print("   Цвета: розовые и красные лепестки, зеленые листья и стебель")
except Exception as e:
    print(f"Ошибка при сохранении: {e}")
    # Альтернативный способ - сохранить каждое изображение отдельно
    print("Попытка альтернативного метода сохранения...")
    rgb_icons[0].save("app.ico", format="ICO")
    print("Иконка 'app.ico' создана (только один размер)")