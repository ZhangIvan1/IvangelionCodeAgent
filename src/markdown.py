import re

# ANSI escape codes
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
ITALIC = "\033[3m"
UNDERLINE = "\033[4m"
CYAN = "\033[36m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
MAGENTA = "\033[35m"
GRAY = "\033[90m"
BG_GRAY = "\033[48;5;236m"
WHITE = "\033[97m"


def render_inline(text: str) -> str:
    # Bold: **text** or __text__
    text = re.sub(r"\*\*(.+?)\*\*", f"{BOLD}\\1{RESET}", text)
    text = re.sub(r"__(.+?)__", f"{BOLD}\\1{RESET}", text)
    # Inline code: `code`
    text = re.sub(r"`([^`]+)`", f"{CYAN}\\1{RESET}", text)
    # Italic: *text* or _text_
    text = re.sub(r"(?<!\w)\*([^*]+)\*(?!\w)", f"{ITALIC}\\1{RESET}", text)
    text = re.sub(r"(?<!\w)_([^_]+)_(?!\w)", f"{ITALIC}\\1{RESET}", text)
    return text

def render_code_block(code: str, language: str = "") -> str:
    if language:
        header = f"{GRAY}┌─ {language} {'─' * max(0, 40 - len(language))}┐{RESET}\n"
    else:
        header = f"{GRAY}┌{'─' * 44}┐{RESET}\n"

    lines = [f"{GRAY}│{RESET} {BG_GRAY}{WHITE}{line}{RESET}" for line in code.split("\n")]
    footer = f"\n{GRAY}└{'─' * 44}┘{RESET}"

    return header + "\n".join(lines) + footer

def render_heading(text: str, level: int) -> str:
    if level == 1:
        prefix = f"{BOLD}{MAGENTA}"
    elif level == 2:
        prefix = f"{BOLD}{GREEN}"
    else:
        prefix = f"{BOLD}{YELLOW}"
    return f"\n{prefix}{'#' * level} {text}{RESET}\n"


def render_list_item(text: str, indent: int = 0) -> str:
    pad = " " * indent
    return f"{pad}{GREEN}•{RESET} {render_inline(text)}"


def render_horizontal_rule() -> str:
    return f"{GRAY}{'─' * 48}{RESET}"

def render_markdown(markdown: str) -> str:
