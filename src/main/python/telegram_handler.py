from random import random
import telegram
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, ReplyKeyboardRemove, bot
from telegram.ext import Handler
from telegram.ext.updater import Updater
from telegram.update import Update
from telegram.ext.callbackcontext import CallbackContext
from telegram.ext.commandhandler import CommandHandler
from telegram.ext.messagehandler import MessageHandler
from telegram.ext.filters import Filters
from telegram.ext import Updater, Filters, CallbackQueryHandler
from telegram.ext import ConversationHandler

import google_sheets_handler as gsh
import utils.yaml_manager as yaml_manager

print_label = "[telegram_handler]"

updater = None

states = {
    "main": 0,
    "categories": 1
}

main_entry_text = "Start typing a new expense or select a specific action"
error_text = "This action has been skipped (due to old session or other error), type /start to restart a conversation..."


def init():
    global updater
    print(print_label, "Starting Telegram updater...")
    updater = Updater(telegram_config["bot_token"], use_context=True)

    print(print_label, "Setting conversations...")
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', command_start)],
        states={
            states["main"]: [CallbackQueryHandler(command_main_callback)],
            states["categories"]: [CallbackQueryHandler(command_categories_callback)],
        },
        fallbacks=[CommandHandler('start', command_start)],
    )

    updater.dispatcher.add_handler(conv_handler)

    print(print_label, "Setting Telegram commands...")
    add_command('help', command_help)

    print(print_label, "Setting Telegram handlers...")
    updater.dispatcher.add_handler(MessageHandler(
        Filters.command & auth_filter() & conversation_filter(), fallback))
    updater.dispatcher.add_handler(MessageHandler(
        Filters.text & auth_filter() & conversation_filter(), fallback))
    updater.dispatcher.add_handler(
        CallbackQueryHandler(fallback_callback_query_handler))

    print(print_label, "Starting Telegram polling...")
    updater.start_polling()

    print(print_label, "Started")
    updater.idle()


def auth_filter():
    return Filters.user(user_id=telegram_config["authorized"])


def conversation_filter():
    return Filters.chat(chat_id=telegram_config["authorized"])


def add_command(name, callback):
    updater.dispatcher.add_handler(
        CommandHandler(name, callback, auth_filter() & conversation_filter()))


def default_keyboard():
    return [[telegram.InlineKeyboardButton(text="🔙Back", callback_data="_BACK")]]


def command_start(update: Update, context: CallbackContext):
    update.message.reply_text(
        "🍏Fresh start! " + main_entry_text, reply_markup=command_main_keyboard())
    return states["main"]


def command_main(update: Update, context: CallbackContext):
    update.callback_query.message.edit_text(
        main_entry_text, reply_markup=command_main_keyboard())
    return states["main"]


def command_main_keyboard():
    reply_keyboard = [[telegram.InlineKeyboardButton(
        text="See categories", callback_data="categories")]]
    return InlineKeyboardMarkup(reply_keyboard, one_time_keyboard=True)


def command_main_callback(update, context):
    if update.callback_query.data == "categories":
        return command_categories(update, context)
    else:
        return states["main"]


def command_categories(update: Update, context: CallbackContext):
    update.callback_query.message.edit_text("Select your category",
                                            reply_markup=command_categories_keyboard())
    return states["categories"]


def command_categories_keyboard():
    data = gsh.get_cached_data()

    reply_keyboard = default_keyboard()

    current_row = 0

    for category in data["categories"]:
        reply_keyboard[current_row].append(telegram.InlineKeyboardButton(
            text=category[2] + " " + category[1], callback_data=category[0]))
        if len(reply_keyboard[current_row]) >= telegram_config["keyboard_size"]:
            reply_keyboard.append([])
            current_row = current_row + 1

    return InlineKeyboardMarkup(
        reply_keyboard, resize_keyboard=True, one_time_keyboard=True)


def command_categories_callback(update, context):
    # print("command_categories_callback", update)
    return command_main(update, context)


def command_help(update: Update, context: CallbackContext):
    update.message.reply_text("You'll get no help here. Run.")


def fallback(update: Update, context: CallbackContext):
    # print(print_label, update.message)
    update.message.reply_text(error_text)


def fallback_callback_query_handler(update: Update, context: CallbackContext):
    print("fallback_callback_query_handler")
    update.callback_query.message.reply_text(error_text)


def send_info_to_chats():
    pass


print(print_label, "Loading Telegram configs...")
telegram_config = yaml_manager.load("config/local/telegram")

init()
