# src/gui/constants.py

"""
Contains constant definitions used by the GUI, primarily for action configuration.
"""

MODIFIER_KEYS = [
    ("Control (Ctrl)", "ctrl"),
    ("Alt", "alt"),
    ("Shift", "shift"),
    ("Windows Key (Win)", "win")
]

COMMON_KEYS = [
    ("Enter", "enter"),
    ("Space", "space"),
    ("Escape", "esc"),
    ("Tab", "tab"),
    ("Backspace", "backspace"),
]

NAVIGATION_KEYS = [
    ("Up Arrow", "up"),
    ("Down Arrow", "down"),
    ("Left Arrow", "left"),
    ("Right Arrow", "right"),
    ("Home", "home"),
    ("End", "end"),
    ("Page Up", "pageup"),
    ("Page Down", "pagedown"),
    ("Insert", "insert"),
    ("Delete", "delete"),
]

ALPHANUMERIC_KEYS = \
    [(char, char.lower()) for char in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"] + \
    [(char, char) for char in "0123456789"]

FUNCTION_KEYS = [(f"F{i}", f"f{i}") for i in range(1, 13)]

SYMBOLS_KEYS = [
    ("` (Backtick)", "`"),
    ("- (Minus)", "-"),
    ("= (Equals)", "="),
    ("[ (Left Bracket)", "["),
    ("] (Right Bracket)", "]"),
    ("\ (Backslash)", "\\"),
    ("; (Semicolon)", ";"),
    ("' (Apostrophe)", "'"),
    (", (Comma)", ","),
    (". (Period)", "."),
    ("/ (Slash)", "/"),
]

NUMPAD_KEYS = [
    ("Numpad 0", "num0"),
    ("Numpad 1", "num1"),
    ("Numpad 2", "num2"),
    ("Numpad 3", "num3"),
    ("Numpad 4", "num4"),
    ("Numpad 5", "num5"),
    ("Numpad 6", "num6"),
    ("Numpad 7", "num7"),
    ("Numpad 8", "num8"),
    ("Numpad 9", "num9"),
    ("Numpad * (Multiply)", "*"),
    ("Numpad + (Add)", "+"),
    ("Numpad - (Subtract)", "-"),
    ("Numpad . (Decimal)", "."),
    ("Numpad / (Divide)", "/"),
]

KEY_GROUPS = [
    ("Common Keys", COMMON_KEYS),
    ("Navigation", NAVIGATION_KEYS),
    ("Letters", [(char, char.lower()) for char in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"]),
    ("Numbers (Top Row)", [(char, char) for char in "0123456789"]),
    ("Function Keys", FUNCTION_KEYS),
    ("Numpad", NUMPAD_KEYS),
    ("Symbols", SYMBOLS_KEYS),
]
