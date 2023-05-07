from typing import Union
from telegram.ext import ConversationHandler, Updater
import configs


print_label: str = "[budoney :: Telegram Dispatcher]"


def start(conversation: Union[ConversationHandler, None]):
    if conversation:
        print(print_label, "Adding coversation handler...")
        updater.dispatcher.add_handler(conversation)

    print(print_label, "Starting Telegram updater polling...")
    updater.start_polling()

    send_message_to_authorized("Hello, I've just started, so I need you to type /start")

    print(print_label, "Started")
    updater.idle()


def send_message_to_authorized(message):
    print(print_label, "send_message_to_authorized:", message)
    if not configs.general["quiet_mode"]:
        for authorized in configs.telegram["authorized"]:
            updater.bot.send_message(chat_id=authorized, text=message)


def send_info_message(message):
    print(print_label, "send_info_message:", message)
    if not configs.general["quiet_mode"]:
        for info_chat in configs.telegram["info_chats"]:
            updater.bot.send_message(chat_id=info_chat, text=message)


print(print_label, "Starting Telegram updater...")
updater = Updater(configs.telegram["bot_token"], use_context=True)
