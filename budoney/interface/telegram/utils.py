from interface.telegram.classes import TelegramConversationFork

forks = {
    "back": TelegramConversationFork("_BACK"),
    "add": TelegramConversationFork("_ADD"),
    "submit": TelegramConversationFork("_SUBMIT"),
}


def keyboard_back_button() -> TelegramConversationFork:
    return forks["back"]


def keyboard_add_button() -> TelegramConversationFork:
    return forks["add"]


def keyboard_submit_button() -> TelegramConversationFork:
    return TelegramConversationFork("_SUBMIT")
