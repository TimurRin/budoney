from random import random
import telegram
from telegram import Update, ReplyKeyboardMarkup, bot
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


def init():
    global updater
    print(print_label, "Starting Telegram updater...")
    updater = Updater(telegram_config["bot_token"], use_context=True)

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', command_start)],
        states={
            states["main"]: [MessageHandler(Filters.text & ~Filters.command, command_start)],
            states["categories"]: [MessageHandler(Filters.text & ~Filters.command, command_categories)],
        },
        fallbacks=[CommandHandler('cancel', command_cancel)],
    )

    updater.dispatcher.add_handler(conv_handler)

    # print(print_label, "Setting Telegram commands...")
    # add_command('start', command_start)
    add_command('help', command_help)

    print(print_label, "Setting Telegram handlers...")
    updater.dispatcher.add_handler(MessageHandler(
        Filters.command & auth_filter() & conversation_filter(), command_unknown))
    updater.dispatcher.add_handler(MessageHandler(
        Filters.text & auth_filter() & conversation_filter(), any_text_input))

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


def command_start(update: Update, context: CallbackContext):
    reply_keyboard = [['See categories']]
    markup_key = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    update.message.reply_text("What do you want?", reply_markup=markup_key)
    return states["categories"]


def command_categories(update: Update, context: CallbackContext):
    data = gsh.get_cached_data()
    reply_keyboard = [[data["categories"][0][0], data["categories"][1][0], data["categories"][2][0]], [
        data["categories"][3][0], data["categories"][4][0], data["categories"][5][0]]]
    markup_key = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    update.message.reply_text("Select your category", reply_markup=markup_key)
    return states["main"]


def command_help(update: Update, context: CallbackContext):
    update.message.reply_text("Нет никакой помощи. Беги.")


def command_cancel(update: Update, context: CallbackContext):
    update.message.reply_text("Нет никакой отмены. Беги.")


def any_text_input(update: Update, context: CallbackContext):
    print(print_label, update.message)
    update.message.reply_text(
        "ты хоть сам понял что ввёл?")


def command_unknown(update: Update, context: CallbackContext):
    print(print_label, update.message)
    update.message.reply_text(
        "ъуъ сам ты '%s'! get some /help" % update.message.text)


def send_info_to_chats():
    pass


print(print_label, "Loading Telegram configs...")
telegram_config = yaml_manager.load("config/local/telegram")

init()
