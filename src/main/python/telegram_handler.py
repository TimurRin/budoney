import json
import datetime
from random import random

import telegram
from telegram import (InlineKeyboardMarkup, Message, ReplyKeyboardMarkup,
                      ReplyKeyboardRemove, Update, bot)
from telegram.ext import (CallbackQueryHandler, ConversationHandler, Filters,
                          Handler, Updater)
from telegram.ext.callbackcontext import CallbackContext
from telegram.ext.commandhandler import CommandHandler
from telegram.ext.filters import Filters
from telegram.ext.messagehandler import MessageHandler
from telegram.ext.updater import Updater
from telegram.update import Update

import google_sheets_handler as gsh
import utils.transliterate as transliterate
import utils.date_utils as date_utils
import utils.yaml_manager as yaml_manager

print_label = "[telegram_handler]"

updater = None

states = {
    "main": 0,
    "wip": 1,

    "flows": 100,
    "flow_add_sum": 105,
    "flow_add_method": 106,
    "flow_add_venue": 107,

    "venues": 200,
    "venue_add_name": 205,
    "venue_add_category": 210,

    "methods": 300,
    "method_add_name": 305,
    "method_add_is_credit": 310,
    "method_add_owner": 315,

    "categories": 400,

    "currencies": 500,
}

main_entry_text = "Shall we begin?"
error_text = "This action has been skipped (due to old session or other error), type /start to restart a conversation..."

authorized_data = {}


def init():
    global updater
    print(print_label, "Starting Telegram updater...")
    updater = Updater(telegram_config["bot_token"], use_context=True)

    print(print_label, "Setting conversations...")
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', command_start)],
        states={
            states["main"]: [CallbackQueryHandler(handle_main)],
            states["wip"]: [CallbackQueryHandler(handle_wip)],
            states["flows"]: [CallbackQueryHandler(handle_flows)],
            states["flow_add_sum"]: [MessageHandler(text_filters(), handle_flow_add_sum)],
            states["flow_add_method"]: [CallbackQueryHandler(handle_flow_add_method)],
            states["flow_add_venue"]: [CallbackQueryHandler(handle_flow_add_venue)],
            states["venues"]: [CallbackQueryHandler(handle_venues)],
            states["venue_add_name"]: [MessageHandler(text_filters(), handle_venue_add_name)],
            states["venue_add_category"]: [CallbackQueryHandler(handle_venue_add_category)],
            states["methods"]: [CallbackQueryHandler(handle_methods)],
            states["method_add_name"]: [MessageHandler(text_filters(), handle_method_add_name)],
            states["method_add_is_credit"]: [CallbackQueryHandler(handle_method_add_is_credit)],
            states["method_add_owner"]: [CallbackQueryHandler(handle_method_add_owner)],
            states["categories"]: [CallbackQueryHandler(handle_categories)],
            states["currencies"]: [CallbackQueryHandler(handle_currencies)],
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

    for authorized in telegram_config["authorized"]:
        if authorized not in authorized_data:
            authorized_data[authorized] = {
                "flow_add": {}
            }

    send_message_to_authorized(
        "Hello, I've just started, so I need you to type /start")

    print(print_label, "Started")
    updater.idle()


# local utils


def text_filters():
    return Filters.text & auth_filter() & conversation_filter()


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


def check_common_data():
    pass


def display_text_add_flow(add_flow: dict):
    data = gsh.get_cached_data()

    text = str(add_flow["sum"]) + " RUB"
    try:
        if "method" in add_flow:
            text = text + " — " + \
                data["methods"]["dict"][add_flow["method"]]["name"]
        if "venue" in add_flow:
            text = text + " — " + \
                data["venues"]["dict"][add_flow["venue"]]["name"]
    except:
        pass
    return str(text)


# keyboards


def keyboard_template_default():
    return [[]]


def keyboard_template_with_back():
    return [[telegram.InlineKeyboardButton(text="🔙 Back", callback_data="_BACK")]]


def keyboard_main():
    reply_keyboard = [
        [
            telegram.InlineKeyboardButton(
                text="👛 Flows", callback_data="flows"),
            telegram.InlineKeyboardButton(
                text="💸 Add expense", callback_data="flow_add_sum"),
            telegram.InlineKeyboardButton(
                text="💰 Add income", callback_data="flow_add_sum"),
        ],
        [
            telegram.InlineKeyboardButton(
                text="🏪 Venues", callback_data="venues"),
        ],
        [
            telegram.InlineKeyboardButton(
                text="💳 Methods", callback_data="methods"),
        ],
        [
            telegram.InlineKeyboardButton(
                text="🏷 Categories", callback_data="categories"),
        ],
        [
            telegram.InlineKeyboardButton(
                text="💱 Currencies", callback_data="currencies"),
        ]
    ]
    return InlineKeyboardMarkup(reply_keyboard)


def keyboard_categories():
    data = gsh.get_cached_data()

    reply_keyboard = keyboard_template_with_back()

    current_row = 0

    for category_id in data["categories"]["list"]:
        reply_keyboard[current_row].append(telegram.InlineKeyboardButton(
            text=data["categories"]["dict"][category_id]["emoji"] + " " + data["categories"]["dict"][category_id]["name"], callback_data=data["categories"]["dict"][category_id]["id"]))
        if len(reply_keyboard[current_row]) >= telegram_config["keyboard_size"]:
            reply_keyboard.append([])
            current_row = current_row + 1

    return InlineKeyboardMarkup(reply_keyboard)


def keyboard_methods():
    data = gsh.get_cached_data()

    reply_keyboard = keyboard_template_with_back()

    current_row = 0

    for category_id in data["methods"]["list"]:
        reply_keyboard[current_row].append(telegram.InlineKeyboardButton(
            text=data["methods"]["dict"][category_id]["name"], callback_data=data["methods"]["dict"][category_id]["id"]))
        if len(reply_keyboard[current_row]) >= telegram_config["keyboard_size"]:
            reply_keyboard.append([])
            current_row = current_row + 1

    return InlineKeyboardMarkup(reply_keyboard)


def keyboard_venues():
    data = gsh.get_cached_data()

    reply_keyboard = keyboard_template_with_back()

    current_row = 0

    for category_id in data["venues"]["list"]:
        reply_keyboard[current_row].append(telegram.InlineKeyboardButton(
            text=data["venues"]["dict"][category_id]["name"], callback_data=data["venues"]["dict"][category_id]["id"]))
        if len(reply_keyboard[current_row]) >= telegram_config["keyboard_size"]:
            reply_keyboard.append([])
            current_row = current_row + 1

    return InlineKeyboardMarkup(reply_keyboard)


def keyboard_with_back():
    return InlineKeyboardMarkup(keyboard_template_with_back())


# commands

def command_start(update: Update, context: CallbackContext):
    update.message.reply_text(
        "🍏 Fresh start! " + main_entry_text, reply_markup=keyboard_main())
    return states["main"]


def command_help(update: Update, context: CallbackContext):
    update.message.reply_text("You'll get no help here. Run.")


# states

def state_main(message: Message):
    message.edit_text(
        main_entry_text, reply_markup=keyboard_main())
    return states["main"]


# handlers

def handle_main(update: Update, context: CallbackContext):
    if update.callback_query.data == "main":
        return states["main"]
    elif update.callback_query.data == "flows":
        update.callback_query.message.edit_text(
            "List of flows", reply_markup=keyboard_with_back())
        return states["flows"]
    elif update.callback_query.data == "flow_add_sum":
        update.callback_query.message.edit_text("Enter sum")
        return states["flow_add_sum"]
    elif update.callback_query.data == "venues":
        update.callback_query.message.edit_text("List of venues",
                                                reply_markup=keyboard_venues())
        return states["venues"]
    elif update.callback_query.data == "methods":
        update.callback_query.message.edit_text("List of methods",
                                                reply_markup=keyboard_methods())
        return states["methods"]
    elif update.callback_query.data == "categories":
        update.callback_query.message.edit_text("List of categories",
                                                reply_markup=keyboard_categories())
        return states["categories"]
    else:
        update.callback_query.message.edit_text("🏗️ This section is not ready",
                                                reply_markup=keyboard_with_back())
        return states["wip"]


def handle_flows(update: Update, context: CallbackContext):
    return state_main(update.callback_query.message)


def handle_flow_add_sum(update: Update, context: CallbackContext):
    try:
        sum = float(update.message.text)

        authorized_data[update.message.chat.id]["flow_add"]["sum"] = sum

        update.message.reply_text(display_text_add_flow(authorized_data[update.message.chat.id]["flow_add"]) + ". How?",
                                  reply_markup=keyboard_methods())

        return states["flow_add_method"]
    except ValueError:
        return state_main(update.message)


def handle_flow_add_method(update: Update, context: CallbackContext):
    authorized_data[update.callback_query.message.chat.id]["flow_add"]["method"] = update.callback_query.data

    update.callback_query.message.edit_text(display_text_add_flow(authorized_data[update.callback_query.message.chat.id]["flow_add"]) + ". Where?",
                                            reply_markup=keyboard_venues())

    return states["flow_add_venue"]


def handle_flow_add_venue(update: Update, context: CallbackContext):
    authorized_data[update.callback_query.message.chat.id]["flow_add"]["venue"] = update.callback_query.data

    send_info_message(display_text_add_flow(
        authorized_data[update.callback_query.message.chat.id]["flow_add"]))

    gsh.insert_into_flow_sheet(date_utils.get_today_flow_code(), [
        "EXPENSE",
        (datetime.datetime.today() - datetime.datetime(1899, 12, 30)).days,
        authorized_data[update.callback_query.message.chat.id]["flow_add"]["venue"],
        "",
        authorized_data[update.callback_query.message.chat.id]["flow_add"]["method"],
        authorized_data[update.callback_query.message.chat.id]["flow_add"]["sum"],
        "RUB"
    ])

    authorized_data[update.callback_query.message.chat.id]["flow_add"] = {}
    return state_main(update.callback_query.message)


def handle_venues(update: Update, context: CallbackContext):
    if (update.callback_query.data != "_BACK"):
        data = gsh.get_cached_data()
        send_info_message(update.callback_query.from_user.first_name + " has selected " +
                          data["venues"]["dict"][update.callback_query.data]["name"] + " and everyone should be aware of it")

    return state_main(update.callback_query.message)


def handle_venue_add_name(update: Update, context: CallbackContext):
    return state_main(update.callback_query.message)


def handle_venue_add_category(update: Update, context: CallbackContext):
    return state_main(update.callback_query.message)


def handle_methods(update: Update, context: CallbackContext):
    if (update.callback_query.data != "_BACK"):
        data = gsh.get_cached_data()
        send_info_message(update.callback_query.from_user.first_name + " has selected " +
                          data["methods"]["dict"][update.callback_query.data]["name"] + " and everyone should be aware of it")

    return state_main(update.callback_query.message)


def handle_method_add_name(update: Update, context: CallbackContext):
    return state_main(update.callback_query.message)


def handle_method_add_is_credit(update: Update, context: CallbackContext):
    return state_main(update.callback_query.message)


def handle_method_add_owner(update: Update, context: CallbackContext):
    return state_main(update.callback_query.message)


def handle_categories(update: Update, context: CallbackContext):
    if (update.callback_query.data != "_BACK"):
        data = gsh.get_cached_data()
        send_info_message(update.callback_query.from_user.first_name + " has selected " + data["categories"]["dict"][update.callback_query.data]["emoji"] + " "
                          + data["categories"]["dict"][update.callback_query.data]["name"] + " and everyone should be aware of it")

    return state_main(update.callback_query.message)


def handle_currencies(update: Update, context: CallbackContext):
    return state_main(update.callback_query.message)


def handle_wip(update: Update, context: CallbackContext):
    update.callback_query.message.edit_text(
        main_entry_text, reply_markup=keyboard_main())
    return states["main"]


# context.bot.delete_message(update.message.chat_id, str(update.message.message_id))

# fallbacks


def fallback(update: Update, context: CallbackContext):
    # print(print_label, "fallback", update)
    update.message.reply_text(error_text)


def fallback_callback_query_handler(update: Update, context: CallbackContext):
    # print(print_label, "fallback_callback_query_handler", update)
    update.callback_query.message.reply_text(error_text)


print(print_label, "Loading Telegram configs...")
telegram_config = yaml_manager.load("config/local/telegram")

init()
