import configs
from interface.telegram.classes import (conversation_views, telegram_users,
                                        TelegramConversationView, TelegramUser)
from interface.telegram.utils import keyboard_back_button
import interface.telegram.section.main as main_section
import interface.telegram.section.finances as finances_section
import interface.telegram.section.tasks as tasks_section
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    CallbackContext, CommandHandler, ConversationHandler)

print_label: str = "[budoney :: Telegram Interface]"
state_handlers = {}


def command_start(update: Update, context: CallbackContext):
    if update.message.from_user.id in configs.telegram["authorized"]:
        return conversation_views["main"].state(update.message, f"🤠 Hiya, {update.message.from_user.first_name}! Welcome to Budoney 🤗", False)
    else:
        update.message.reply_text("👋 Hello there! This is a private instance of Budoney Household Management. If you want a personal Budoney instance, follow the link below",
                                  reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(text="Budoney GitHub repository", url="https://github.com/TimurRin/budoney")]]))


for telegram_user_id in configs.telegram["authorized"]:
    if telegram_user_id not in telegram_users:
        telegram_users[telegram_user_id] = TelegramUser()


# Technical coversation views
TelegramConversationView("_WIP", [
    [keyboard_back_button()]
])

main_section.init()
finances_section.init()
tasks_section.init()

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
