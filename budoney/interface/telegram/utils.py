from interface.telegram.classes import SIMPLE_FORK, TelegramConversationFork


def keyboard_back_button() -> "tuple[str, str, TelegramConversationFork]":
    return ("_BACK", "🔙 Back", SIMPLE_FORK)


def keyboard_add_button() -> "tuple[str, str, TelegramConversationFork]":
    return ("_ADD", "➕ Add new", SIMPLE_FORK)


def keyboard_submit_button() -> "tuple[str, str, TelegramConversationFork]":
    return ("_SUBMIT", "✅ Submit", SIMPLE_FORK)
