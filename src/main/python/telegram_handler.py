from random import random
import telegram
from telegram import Update, bot
from telegram.ext import Handler
from telegram.ext.updater import Updater
from telegram.update import Update
from telegram.ext.callbackcontext import CallbackContext
from telegram.ext.commandhandler import CommandHandler
from telegram.ext.messagehandler import MessageHandler
from telegram.ext.filters import Filters
from telegram.ext import Updater, MessageHandler, Filters, CallbackQueryHandler

import utils.yaml_manager as yaml_manager


def auth_filter():
    return Filters.user(user_id=telegram_config["authorized"])


def conversation_filter():
    return Filters.chat(chat_id=telegram_config["authorized"])


def add_command(name, callback):
    updater.dispatcher.add_handler(
        CommandHandler(name, callback, auth_filter() & conversation_filter()))


def command_start(update: Update, context: CallbackContext):
    update.message.reply_text(
        "Нажми /help, чтобы посмотреть доступные команды")


def command_help(update: Update, context: CallbackContext):
    update.message.reply_text("Нет никакой помощи. Беги.")


def any_text_input(update: Update, context: CallbackContext):
    print(update.message)
    update.message.reply_text(
        "ты хоть сам понял что ввёл?")


def command_unknown(update: Update, context: CallbackContext):
    print(update.message)
    update.message.reply_text(
        "ъуъ сам ты '%s'! get some /help" % update.message.text)


def send_info_to_chats():
    pass


print("Loading Telegram configs...")
telegram_config = yaml_manager.load("config/local/telegram")

print("Starting Telegram updater...")
updater = Updater(telegram_config["bot_token"], use_context=True)

print("Setting Telegram commands...")
add_command('start', command_start)
add_command('help', command_help)

print("Setting Telegram handlers...")
updater.dispatcher.add_handler(MessageHandler(
    Filters.command & auth_filter() & conversation_filter(), command_unknown))
updater.dispatcher.add_handler(MessageHandler(
    Filters.text & auth_filter() & conversation_filter(), any_text_input))

print("Starting Telegram polling...")
updater.start_polling()

print("Started")
updater.idle()
