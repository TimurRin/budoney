from abc import abstractmethod
import configs
from interface.telegram.classes import conversation_views, telegram_users, TelegramConversationView, TelegramUser
from interface.telegram.utils import keyboard_row_back
import interface.telegram.section.main as main_section
import interface.telegram.section.finances as finances_section
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Message, Update
from telegram.ext import (
    CallbackContext, CallbackQueryHandler, CommandHandler, ConversationHandler)
from telegram.ext.handler import Handler

print_label: str = "[budoney :: Telegram Interface]"
state_handlers = {}


def command_start(update: Update, context: CallbackContext):
    return conversation_views["main"].state(update.message, "Fresh start!", False)


for telegram_user_id in configs.telegram["authorized"]:
    if telegram_user_id not in telegram_users:
        telegram_users[telegram_user_id] = TelegramUser()


# Technical coversation views
TelegramConversationView("_WIP", [
    keyboard_row_back()
])

main_section.init()
finances_section.init()

for name in conversation_views:
    state_handlers[name] = conversation_views[name].handlers

print(state_handlers)

entry_point_handler = CommandHandler('start', command_start)

conversation = ConversationHandler(
    entry_points=[entry_point_handler],
    states=state_handlers,
    fallbacks=[entry_point_handler],
)

print(print_label,
      f"A conversation with {len(conversation_views)} view(s) has been created successfully")
