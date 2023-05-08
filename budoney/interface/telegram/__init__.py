import configs
from interface.telegram.classes import (
    conversation_views,
    telegram_users,
    DefaultTelegramConversationView,
    TelegramUser,
)

import interface.telegram.section.main as main_section
import interface.telegram.section.people as people_section
import interface.telegram.section.organizations as organizations_section
import interface.telegram.section.finances as finances_section
import interface.telegram.section.tasks as tasks_section
import interface.telegram.section.health as health_section
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext, CommandHandler, ConversationHandler

print_label: str = "[budoney :: Telegram Interface]"
state_handlers = {}


def command_start(update: Update, context: CallbackContext):
    if update.message.from_user.id in configs.telegram["authorized"]:
        telegram_users[update.message.from_user.id] = TelegramUser(
            update.message.from_user.first_name
        )
        print(
            print_label,
            f"{update.message.from_user.first_name} ({update.message.from_user.id}) has started a new session",
        )
        return conversation_views["main"].state(
            update.message,
            f"🤠 Hiya, {update.message.from_user.first_name}! Welcome to Budoney 🤗",
            False,
        )
    else:
        print(
            print_label,
            f"{update.message.from_user.first_name} ({update.message.from_user.id}) has tried to start a session, but they are not authorized",
        )
        update.message.reply_text(
            "👋 Hello there! This is a private instance of Budoney Household Management. If you want a personal Budoney instance, follow the link below",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text="Budoney GitHub repository",
                            url="https://github.com/TimurRin/budoney",
                        )
                    ]
                ]
            ),
        )


# Technical coversation views
DefaultTelegramConversationView("_WIP", [])

main_section.init()
people_section.init()
organizations_section.init()
finances_section.init()
tasks_section.init()
health_section.init()

for name in conversation_views:
    print(print_label, "conversation_view", name)
    if len(conversation_views[name].handlers) > 0:
        state_handlers[name] = conversation_views[name].handlers

entry_point_handler = CommandHandler("start", command_start)

conversation = ConversationHandler(
    entry_points=[entry_point_handler],
    states=state_handlers,
    fallbacks=[entry_point_handler],
)

print(
    print_label,
    f"A conversation with {len(conversation_views)} view(s) has been created successfully",
)
