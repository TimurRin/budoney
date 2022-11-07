from interface.telegram.classes import SIMPLE_FORK, TelegramConversationFork


def keyboard_row_back() -> "list[tuple[str, str, TelegramConversationFork]]":
    return [("_BACK", "🔙 Back", SIMPLE_FORK)]

# TODO: add ("_ADD", "➕ Add new") and ("_SUBMIT", "✅ Submit")
