from typing import List


def detect_line_separator(text: str) -> str:
    if -1 != text.find('\r\n'):
        return "\r\n"
    elif -1 != text.find('\r'):
        return "\r"
    else:
        return "\n"


def split_lines(text: str) -> List[str]:
    return text.split(detect_line_separator(text))
