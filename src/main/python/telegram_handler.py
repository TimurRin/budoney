from random import random
import json
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
    "categories": 1,
    "flow_sum": 2,
    "flow_method": 3,
    "flow_venue": 4,
}

main_entry_text = "Shall we begin?"
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
            states["flow_sum"]: [default_text_parse_handler()],
            states["flow_method"]: [CallbackQueryHandler(command_methods_callback)],
            states["flow_venue"]: [CallbackQueryHandler(command_venues_callback)],
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

    send_message_to_authorized(
        "Hello, I've just started, so I need you to type /start")

    print(print_label, "Started")
    updater.idle()


def default_text_parse_handler():
    return MessageHandler(
        Filters.text & auth_filter() & conversation_filter(), default_text_parse)


def send_message_to_authorized(message):
    print(print_label, "send_message_to_authorized", message)
    if not telegram_config["quiet_mode"]:
        for authorized in telegram_config["authorized"]:
            updater.bot.send_message(
                chat_id=authorized, text=message)


def send_info_message(message):
    print(print_label, "send_info_message", message)
    if not telegram_config["quiet_mode"]:
        for info_chat in telegram_config["info_chats"]:
            updater.bot.send_message(
                chat_id=info_chat, text=message)


def auth_filter():
    return Filters.user(user_id=telegram_config["authorized"])


def conversation_filter():
    return Filters.chat(chat_id=telegram_config["authorized"])


def add_command(name, callback):
    updater.dispatcher.add_handler(
        CommandHandler(name, callback, auth_filter() & conversation_filter()))


def default_keyboard():
    return [[]]
    # return [[telegram.InlineKeyboardButton(text="🔙 Back", callback_data="_BACK")]]


def command_start(update: Update, context: CallbackContext):
    update.message.reply_text(
        "🍏 Fresh start! " + main_entry_text, reply_markup=command_main_keyboard())
    return states["main"]


def command_main(update: Update, context: CallbackContext):
    update.callback_query.message.edit_text(
        main_entry_text, reply_markup=command_main_keyboard())
    return states["main"]


def command_main_keyboard():
    reply_keyboard = [[telegram.InlineKeyboardButton(
        text="Add flow entry", callback_data="flow_sum"), telegram.InlineKeyboardButton(
        text="See categories", callback_data="categories")]]
    return InlineKeyboardMarkup(reply_keyboard)


def command_main_callback(update: Update, context: CallbackContext):
    if update.callback_query.data == "categories":
        update.callback_query.message.edit_text("Select your category",
                                                reply_markup=command_categories_keyboard())
        return states["categories"]
    elif update.callback_query.data == "flow_sum":
        update.callback_query.message.edit_text("Enter sum")
        return states["flow_sum"]
    else:
        return states["main"]


def command_categories_keyboard():
    data = gsh.get_cached_data()

    reply_keyboard = default_keyboard()

    current_row = 0

    for category_id in data["categories"]["list"]:
        reply_keyboard[current_row].append(telegram.InlineKeyboardButton(
            text=data["categories"]["dict"][category_id]["emoji"] + " " + data["categories"]["dict"][category_id]["name"], callback_data=data["categories"]["dict"][category_id]["id"]))
        if len(reply_keyboard[current_row]) >= telegram_config["keyboard_size"]:
            reply_keyboard.append([])
            current_row = current_row + 1

    return InlineKeyboardMarkup(reply_keyboard)


def command_methods_keyboard():
    data = gsh.get_cached_data()

    reply_keyboard = default_keyboard()

    current_row = 0

    for category_id in data["methods"]["list"]:
        reply_keyboard[current_row].append(telegram.InlineKeyboardButton(
            text=data["methods"]["dict"][category_id]["name"], callback_data=data["methods"]["dict"][category_id]["id"]))
        if len(reply_keyboard[current_row]) >= telegram_config["keyboard_size"]:
            reply_keyboard.append([])
            current_row = current_row + 1

    return InlineKeyboardMarkup(reply_keyboard)


def command_venues_keyboard():
    data = gsh.get_cached_data()

    reply_keyboard = default_keyboard()

    current_row = 0

    for category_id in data["venues"]["list"]:
        reply_keyboard[current_row].append(telegram.InlineKeyboardButton(
            text=data["venues"]["dict"][category_id]["name"], callback_data=data["venues"]["dict"][category_id]["id"]))
        if len(reply_keyboard[current_row]) >= telegram_config["keyboard_size"]:
            reply_keyboard.append([])
            current_row = current_row + 1

    return InlineKeyboardMarkup(reply_keyboard)


def command_categories_callback(update: Update, context: CallbackContext):
    # print("command_categories_callback", update)

    if (update.callback_query.data != "_BACK"):
        data = gsh.get_cached_data()
        send_info_message(update.callback_query.from_user.first_name + " has selected " + data["categories"]["dict"][update.callback_query.data]["emoji"] + " "
                          + data["categories"]["dict"][update.callback_query.data]["name"] + " and everyone should be aware of it")

    return command_main(update, context)


def command_methods_callback(update: Update, context: CallbackContext):
    # print("command_categories_callback", update)

    if (update.callback_query.data != "_BACK"):
        data = gsh.get_cached_data()
        send_info_message(update.callback_query.from_user.first_name + " has selected " +
                          data["methods"]["dict"][update.callback_query.data]["name"] + " and everyone should be aware of it")

    update.callback_query.message.reply_text("Where?",
                                             reply_markup=command_venues_keyboard())
    return states["flow_venue"]


def command_venues_callback(update: Update, context: CallbackContext):
    # print("command_categories_callback", update)

    if (update.callback_query.data != "_BACK"):
        data = gsh.get_cached_data()
        send_info_message(update.callback_query.from_user.first_name + " has selected " +
                          data["venues"]["dict"][update.callback_query.data]["name"] + " and everyone should be aware of it")

    return command_main(update, context)


def command_help(update: Update, context: CallbackContext):
    update.message.reply_text("You'll get no help here. Run.")


def default_text_parse(update: Update, context: CallbackContext):
    print("command_main_text_parse", update.message.text)
    # context.bot.delete_message(update.message.chat_id, str(update.message.message_id))

    try:
        sum = float(update.message.text)

        update.message.reply_text("How?",
                                  reply_markup=command_methods_keyboard())

        return states["flow_method"]
    except ValueError:
        return states["main"]


def fallback(update: Update, context: CallbackContext):
    # print(print_label, "fallback", update)
    update.message.reply_text(error_text)


def fallback_callback_query_handler(update: Update, context: CallbackContext):
    # print(print_label, "fallback_callback_query_handler", update)
    update.callback_query.message.reply_text(error_text)


def send_info_to_chats():
    pass


print(print_label, "Loading Telegram configs...")
telegram_config = yaml_manager.load("config/local/telegram")

init()
