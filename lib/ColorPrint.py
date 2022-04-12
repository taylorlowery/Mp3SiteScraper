from enum import Enum


class TextColor(Enum):
    DEFAULT = 0
    BLACK = 30
    RED = 31
    GREEN = 32
    YELLOW = 33
    BLUE = 34
    PURPLE = 35
    CYAN = 36
    WHITE = 37
    BRIGHT_BLACK = 90
    BRIGHT_RED = 91
    BRIGHT_GREEN = 92
    BRIGHT_YELLOW = 93
    BRIGHT_BLUE = 94
    BRIGHT_PURPLE = 95
    BRIGHT_CYAN = 96
    BRIGHT_WHITE = 97


class BackgroundColor(Enum):
    DEFAULT = 1
    BLACK = 40
    RED = 41
    GREEN = 42
    YELLOW = 43
    BLUE = 44
    PURPLE = 45
    CYAN = 46
    WHITE = 47
    BRIGHT_BLACK = 100
    BRIGHT_RED = 101
    BRIGHT_GREEN = 102
    BRIGHT_YELLOW = 103
    BRIGHT_BLUE = 104
    BRIGHT_PURPLE = 105
    BRIGHT_CYAN = 106
    BRIGHT_WHITE = 107


class TextStyle(Enum):
    NORMAL = 0
    BOLD = 1
    LIGHT = 2
    ITALIC = 3
    UNDERLINE = 4
    BLINK = 5


def color_print(text: str, text_color: TextColor = TextColor.DEFAULT,
                background_color: BackgroundColor = BackgroundColor.DEFAULT,
                text_style: TextStyle = TextStyle.NORMAL, end="\n"):
    print(f"\033[{text_style.value};{text_color.value};{background_color.value}m {text} \033[0;0m", end=end)


def print_error(text: str, error_type: str = ""):
    if len(error_type) > 0:
        color_print(error_type, TextColor.BRIGHT_WHITE, BackgroundColor.BRIGHT_RED, TextStyle.BLINK, ": ")
    color_print(text)


def print_success(text: str):
    color_print(text, TextColor.GREEN, BackgroundColor.DEFAULT, TextStyle.BOLD, end="\n")


def print_warning(text: str, prefix: str = ""):
    if len(prefix) > 0:
        color_print(prefix, text_color=TextColor.YELLOW, background_color=BackgroundColor.DEFAULT, text_style=TextStyle.NORMAL, end=": ")
    color_print(text=text, text_color=TextColor.YELLOW, background_color=BackgroundColor.DEFAULT, text_style=TextStyle.NORMAL, end="\n")
