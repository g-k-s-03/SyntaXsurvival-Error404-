import re


def sanitize_text(value: str) -> str:
    trimmed = value.strip()
    trimmed = re.sub(r"\s+", " ", trimmed)
    # Strip angle brackets to reduce script/html payload persistence.
    return trimmed.replace("<", "").replace(">", "")


def sanitize_optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    result = sanitize_text(value)
    return result or None
