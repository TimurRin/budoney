from interface.telegram.classes import TelegramConversationFork


def keyboard_row_back() -> "list[tuple[str, str, TelegramConversationFork]]":
    return [("_BACK", "🔙 Back", TelegramConversationFork())]

# TODO: add ("_ADD", "➕ Add new") and ("_SUBMIT", "✅ Submit")
