def detect_language(text: str) -> str:
    """Return a conservative language label without claiming unsupported translation."""
    if not text.strip():
        return "unknown"
    devanagari = sum("\u0900" <= char <= "\u097f" for char in text)
    latin = sum(char.isascii() and char.isalpha() for char in text)
    if devanagari > latin:
        return "hi"
    return "en"
