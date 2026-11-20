import re
import unicodedata


def remove_diacritics(text):
    """Bỏ dấu tiếng Việt: 'Hội thảo' -> 'hoi thao' (US-07-AC3, US-10-AC2)."""
    text = text.lower()
    text = text.replace('đ', 'd')
    nfd = unicodedata.normalize('NFD', text)
    return ''.join(ch for ch in nfd if not unicodedata.combining(ch))


def normalize_text(text):
    """Chuẩn hóa để so khớp tìm kiếm: bỏ dấu, chữ thường, gộp khoảng trắng."""
    return re.sub(r'\s+', ' ', remove_diacritics(text)).strip()
