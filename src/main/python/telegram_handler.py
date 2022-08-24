import datetime
import re
import difflib
import math
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

    "transactions": 100,
    "transaction_add_fast_type": 105,
    "transaction_add_fast_sum": 106,
    "transaction_add_fast_method": 107,
    "transaction_add_fast_merchant": 108,
    "transaction_add_fast_target_method": 109,
    "transaction": 110,
    "transaction_type": 111,
    "transaction_date": 112,
    "transaction_sum": 113,
    "transaction_currency": 114,
    "transaction_method": 115,
    "transaction_merchant": 116,
    "transaction_description": 117,

    "merchants": 200,
    "merchant": 201,
    "merchant_name": 202,
    "merchant_keywords": 203,
    "merchant_category": 204,
    "merchant_emoji": 205,

    "methods": 300,
    "method": 301,
    "method_name": 302,
    "method_is_mir": 303,
    "method_is_credit": 304,
    "method_is_cashback": 305,
    "method_owner": 306,

    "categories": 400,

    "currencies": 500,
}

main_entry_text = "Shall we begin?"
error_text = "This action has been skipped (due to old session or other error), type /start to restart a conversation..."

authorized_data = {}

handler_data_back = "_BACK"
handler_data_add = "_ADD"
handler_data_submit = "_SUBMIT"


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

            states["transactions"]: [CallbackQueryHandler(handle_transactions)],
            states["transaction_add_fast_type"]: [CallbackQueryHandler(handle_transaction_add_fast_type)],
            states["transaction_add_fast_sum"]: [MessageHandler(text_filters(), handle_transaction_add_fast_sum)],
            states["transaction_add_fast_method"]: [CallbackQueryHandler(handle_transaction_add_fast_method)],
            states["transaction_add_fast_merchant"]: [CallbackQueryHandler(handle_transaction_add_fast_merchant)],
            states["transaction_add_fast_target_method"]: [CallbackQueryHandler(handle_transaction_add_fast_target_method)],
            states["transaction"]: [CallbackQueryHandler(handle_transaction)],
            states["transaction_type"]: [CallbackQueryHandler(handle_transaction_type)],
            states["transaction_date"]: [CallbackQueryHandler(handle_transaction_date)],
            states["transaction_sum"]: [MessageHandler(text_filters(), handle_transaction_sum)],
            states["transaction_currency"]: [CallbackQueryHandler(handle_transaction_currency)],
            states["transaction_method"]: [CallbackQueryHandler(handle_transaction_method)],
            states["transaction_merchant"]: [CallbackQueryHandler(handle_transaction_merchant)],
            states["transaction_description"]: [MessageHandler(text_filters(), handle_transaction_description)],

            states["merchants"]: [CallbackQueryHandler(handle_merchants)],
            states["merchant"]: [CallbackQueryHandler(handle_merchant)],
            states["merchant_name"]: [MessageHandler(text_filters(), handle_merchant_name)],
            states["merchant_keywords"]: [MessageHandler(text_filters(), handle_merchant_keywords)],
            states["merchant_category"]: [CallbackQueryHandler(handle_merchant_category)],
            states["merchant_emoji"]: [MessageHandler(text_filters(), handle_merchant_emoji)],

            states["methods"]: [CallbackQueryHandler(handle_methods)],
            states["method"]: [CallbackQueryHandler(handle_method)],
            states["method_name"]: [MessageHandler(text_filters(), handle_method_name)],
            states["method_is_mir"]: [CallbackQueryHandler(handle_method_is_mir)],
            states["method_is_credit"]: [CallbackQueryHandler(handle_method_is_credit)],
            states["method_is_cashback"]: [CallbackQueryHandler(handle_method_is_cashback)],
            states["method_owner"]: [CallbackQueryHandler(handle_method_owner)],

            states["categories"]: [CallbackQueryHandler(handle_categories)],

            states["currencies"]: [CallbackQueryHandler(handle_currencies)],
        },
        fallbacks=[CommandHandler('start', command_start)],
    )

    updater.dispatcher.add_handler(conv_handler)

    print(print_label, "Setting Telegram commands...")
    add_command('help', command_help)
    add_command('update', command_update)

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
                "last_state": state_main,
                "transaction": {},
                "merchant": {},
                "method": {},
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


def generate_id(type: str, name: str):
    data = gsh.get_cached_data([type])
    # int(math.log10(n))+1

    transliterated = transliterate.russian_to_latin(name).upper()
    code = re.sub(r'[^A-Z0-9]+', '', transliterated)
    id = code[:7]
    id_len = len(id)

    if id not in data[type]["dict"]:
        return id
    else:
        loop = 0
        while(loop <= 999999):
            digits = loop > 0 and (int(math.log10(loop))+1) or 1
            temp_id = None
            if id_len + digits > 7:
                temp_id = id[:-digits] + str(loop)
            else:
                temp_id = id + str(loop)
            if temp_id not in data[type]["dict"]:
                return temp_id
            else:
                loop = loop + 1


def display_text_add_transaction(add_transaction: dict):
    data = gsh.get_cached_data(["methods", "merchants"])

    text = ""

    if "type" in add_transaction and add_transaction["type"] != "EXPENSE":
        text = add_transaction["type"] + " — "

    text = text + str("sum" in add_transaction and add_transaction["sum"] or 0) + " " + \
        ("currency" in add_transaction and add_transaction["currency"] or "RUB")
    try:
        if "method" in add_transaction:
            text = text + " — " + \
                data["methods"]["dict"][add_transaction["method"]]["name"]

        if "type" in add_transaction and add_transaction["type"] == "TRANSFER":
            if "target_method" in add_transaction:
                text = text + " > " + \
                    data["methods"]["dict"][add_transaction["target_method"]]["name"]
            if "description" in add_transaction:
                text = text + " — " + add_transaction["description"]
        else:
            if "merchant" in add_transaction and "description" in add_transaction:
                text = text + " — " + \
                    data["merchants"]["dict"][add_transaction["merchant"]]["name"] + \
                    " (" + add_transaction["description"] + ")"
            elif "merchant" in add_transaction:
                text = text + " — " + \
                    data["merchants"]["dict"][add_transaction["merchant"]]["name"]
            elif "description" in add_transaction:
                text = text + " — " + add_transaction["description"]
    except:
        pass
    return str(text)


def transaction_submit(message: Message):
    data = authorized_data[message.chat.id]["transaction"]

    target = ("type" in data and data["type"] ==
              "TRANSFER") and "target_method" or "merchant"

    if ("type" in data) and ("sum" in data and data["sum"] > 0) and ("currency" in data) and ("method" in data) and (data["type"] ==
                                                                                                                     "CORRECTION" or target in data):
        send_info_message(display_text_add_transaction(data))

        gsh.insert_into_transaction_sheet(date_utils.get_today_transaction_code(), [
            data["type"],
            (datetime.datetime.today() - datetime.datetime(1899, 12, 30)).days,
            data["sum"],
            data["currency"],
            data["method"],
            data["type"] != "CORRECTION" and data[target] or "",
            "description" in data and data["description"] or ""
        ])

        authorized_data[message.chat.id]["transaction"] = {}

        return state_main(message)
    else:
        return state_transactions(message)


def merchant_submit(message: Message):
    data = authorized_data[message.chat.id]["merchant"]

    if "id" in data:
        send_info_message("New merchant: " + data["id"])

        gsh.insert_into_sheet_name("merchants", [
            data["id"],
            "name" in data and data["name"] or data["id"],
            "keywords" in data and data["keywords"] or "",
            "category" in data and data["category"] or "OTHER",
            "emoji" in data and data["emoji"] or ""
        ])

        authorized_data[message.chat.id]["merchant"] = {}

        gsh.cached_data.pop("merchants", None)
        gsh.get_cached_data(["merchants"])

        return authorized_data[message.chat.id]["last_state"](message)
    else:
        return state_merchants(message)


def method_submit(message: Message):
    data = authorized_data[message.chat.id]["method"]

    if "id" in data:
        send_info_message("New method: " + data["id"])

        gsh.insert_into_sheet_name("methods", [
            data["id"],
            "name" in data and data["name"] or data["id"],
            "is_mir" in data and data["is_mir"] and "TRUE" or "FALSE",
            "is_credit" in data and data["is_credit"] and "TRUE" or "FALSE",
            "is_cashback" in data and data["is_cashback"] and "TRUE" or "FALSE",
            "owner" in data and data["owner"] or "SHARED"
        ])

        authorized_data[message.chat.id]["method"] = {}

        gsh.cached_data.pop("methods", None)
        gsh.get_cached_data(["methods"])

        return authorized_data[message.chat.id]["last_state"](message)
    else:
        return state_methods(message)


# keyboard rows


def keyboard_row_back():
    return [telegram.InlineKeyboardButton(text="🔙 Back", callback_data=handler_data_back)]


def keyboard_row_back_and_add():
    return [
        telegram.InlineKeyboardButton(
            text="🔙 Back", callback_data=handler_data_back),
        telegram.InlineKeyboardButton(
            text="➕ Add new", callback_data=handler_data_add)
    ]


def keyboard_row_back_and_submit():
    return [
        telegram.InlineKeyboardButton(
            text="🔙 Back", callback_data=handler_data_back),
        telegram.InlineKeyboardButton(
            text="✅ Submit", callback_data=handler_data_submit)
    ]


# full keyboards


def keyboard_main():
    reply_keyboard = [
        [
            telegram.InlineKeyboardButton(
                text="👛 Transactions", callback_data="transactions"),
            telegram.InlineKeyboardButton(
                text="💸 Add fast transaction", callback_data="transaction_add_fast_type"),
        ],
        [
            telegram.InlineKeyboardButton(
                text="🏪 Merchants", callback_data="merchants"),
        ],
        [
            telegram.InlineKeyboardButton(
                text="💳 Methods", callback_data="methods"),
        ],
        [
            telegram.InlineKeyboardButton(
                text="🏷 Categories", callback_data="categories"),
            telegram.InlineKeyboardButton(
                text="💱 Currencies", callback_data="currencies"),
            telegram.InlineKeyboardButton(
                text="👫 Users", callback_data="users"),
        ]
    ]
    return InlineKeyboardMarkup(reply_keyboard)


def keyboard_transactions():
    reply_keyboard = [keyboard_row_back_and_add()]

    return InlineKeyboardMarkup(reply_keyboard)


def keyboard_add_fast_type():
    reply_keyboard = []

    reply_keyboard.append([telegram.InlineKeyboardButton("Expense", callback_data="EXPENSE"),
                          telegram.InlineKeyboardButton("Income", callback_data="INCOME")])
    reply_keyboard.append([telegram.InlineKeyboardButton("Transfer", callback_data="TRANSFER"),
                          telegram.InlineKeyboardButton("Correction", callback_data="CORRECTION")])
    reply_keyboard.append(keyboard_row_back())

    return InlineKeyboardMarkup(reply_keyboard)


def keyboard_transaction():
    reply_keyboard = []

    # reply_keyboard.append([telegram.InlineKeyboardButton("Edit type", callback_data="_EDIT_TYPE"),
    #                       telegram.InlineKeyboardButton("Edit date", callback_data="_EDIT_DATE")])
    # reply_keyboard.append([telegram.InlineKeyboardButton("Edit sum", callback_data="_EDIT_SUM"),
    #                       telegram.InlineKeyboardButton("Edit currency", callback_data="_EDIT_CURRENCY")])
    # reply_keyboard.append([telegram.InlineKeyboardButton("Edit method", callback_data="_EDIT_METHOD"),
    #                       telegram.InlineKeyboardButton("Edit merchant", callback_data="_EDIT_MERCHANT")])
    # reply_keyboard.append([telegram.InlineKeyboardButton(
    #     "Edit description", callback_data="_EDIT_DESCRIPTION")])
    reply_keyboard.append(keyboard_row_back_and_submit())

    return InlineKeyboardMarkup(reply_keyboard)


def keyboard_categories():
    data = gsh.get_cached_data(["categories"])

    reply_keyboard = [[]]

    current_row = 0

    for id in data["categories"]["list"]:
        reply_keyboard[current_row].append(telegram.InlineKeyboardButton(
            text=data["categories"]["dict"][id]["emoji"] + " " + data["categories"]["dict"][id]["name"], callback_data=id))
        if len(reply_keyboard[current_row]) >= 3:
            reply_keyboard.append([])
            current_row = current_row + 1

    reply_keyboard.append(keyboard_row_back())

    return InlineKeyboardMarkup(reply_keyboard)


def keyboard_methods():
    data = gsh.get_cached_data(["methods"])

    reply_keyboard = [[]]

    current_row = 0

    for id in data["methods"]["list"]:
        reply_keyboard[current_row].append(telegram.InlineKeyboardButton(
            text=data["methods"]["dict"][id]["name"], callback_data=id))
        if len(reply_keyboard[current_row]) >= 2:
            reply_keyboard.append([])
            current_row = current_row + 1

    reply_keyboard.append(keyboard_row_back_and_add())

    return InlineKeyboardMarkup(reply_keyboard)


def keyboard_method():
    reply_keyboard = []

    reply_keyboard.append(keyboard_row_back_and_submit())

    return InlineKeyboardMarkup(reply_keyboard)


def keyboard_merchants():
    data = gsh.get_cached_data(["merchants", "categories"])

    reply_keyboard = [[]]

    current_row = 0

    for id in data["merchants"]["list"]:
        reply_keyboard[current_row].append(telegram.InlineKeyboardButton(
            text=(data["merchants"]["dict"][id]["emoji"] or data["categories"]["dict"][data["merchants"]["dict"][id]["category"]]["emoji"]) + " " + data["merchants"]["dict"][id]["name"], callback_data=id))
        if len(reply_keyboard[current_row]) >= 3:
            reply_keyboard.append([])
            current_row = current_row + 1

    reply_keyboard.append(keyboard_row_back_and_add())

    return InlineKeyboardMarkup(reply_keyboard)


def keyboard_merchant():
    reply_keyboard = []

    reply_keyboard.append([telegram.InlineKeyboardButton("Edit name", callback_data="_EDIT_NAME"),
                           telegram.InlineKeyboardButton("Edit category", callback_data="_EDIT_CATEGORY")])

    reply_keyboard.append(keyboard_row_back_and_submit())

    return InlineKeyboardMarkup(reply_keyboard)


def keyboard_with_back():
    return InlineKeyboardMarkup([keyboard_row_back()])


# commands

def command_start(update: Update, context: CallbackContext):
    update.message.reply_text(
        "🍏 A fresh start! " + main_entry_text, reply_markup=keyboard_main())
    return states["main"]


def command_update(update: Update, context: CallbackContext):
    update.message.reply_text("Forcing data update, type /start")
    gsh.invalidate_all()


def command_help(update: Update, context: CallbackContext):
    update.message.reply_text("You'll get no help here. Run.")


# states


def state_main(message: Message):
    message.edit_text(
        main_entry_text, reply_markup=keyboard_main())
    return states["main"]


def state_main_reply(message: Message):
    message.reply_text(
        main_entry_text, reply_markup=keyboard_main())
    return states["main"]


def state_transactions(message: Message):
    message.edit_text(
        "List of transactions", reply_markup=keyboard_transactions())
    return states["transactions"]


def state_transaction(message: Message):
    message.edit_text(
        display_text_add_transaction(authorized_data[message.chat.id]["transaction"]), reply_markup=keyboard_transaction())
    return states["transaction"]


def state_transaction_add_fast_type(message: Message):
    message.edit_text("Select transaction type",
                      reply_markup=keyboard_add_fast_type())
    return states["transaction_add_fast_type"]


def state_transaction_add_fast_sum(message: Message):
    message.edit_text(
        "Enter transaction data in this sequence \(data in _italic_ may be ommited\): _date_, _type_, *sum* _currency_, _method_, _merchant/target_, _description_",
        parse_mode='MarkdownV2')
    return states["transaction_add_fast_sum"]


def state_merchants(message: Message):
    message.edit_text("List of merchants",
                      reply_markup=keyboard_merchants())
    return states["merchants"]


def state_merchant(message: Message):
    message.edit_text(str(authorized_data[message.chat.id]["merchant"]),
                      reply_markup=keyboard_merchant())
    return states["merchant"]


def state_merchant_reply(message: Message):
    message.reply_text(str(authorized_data[message.chat.id]["merchant"]),
                       reply_markup=keyboard_merchant())
    return states["merchant"]


def state_merchant_name(message: Message):
    message.edit_text(
        "Enter merchant name")
    return states["merchant_name"]


def state_merchant_category(message: Message):
    message.edit_text("Select merchant category",
                      reply_markup=keyboard_categories())
    return states["merchant_category"]


def state_methods(message: Message):
    message.edit_text("List of methods",
                      reply_markup=keyboard_methods())
    return states["methods"]


def state_method(message: Message):
    message.edit_text("state_method",
                      reply_markup=keyboard_method())
    return states["method"]


def state_categories(message: Message):
    message.edit_text("List of categories",
                      reply_markup=keyboard_categories())
    return states["categories"]


def state_wip(message: Message):
    message.edit_text("🏗️ This section is not ready",
                      reply_markup=keyboard_with_back())
    return states["wip"]


# handlers


def handle_main(update: Update, context: CallbackContext):
    if update.callback_query.data == "transactions":
        return state_transactions(update.callback_query.message)
    elif update.callback_query.data == "transaction_add_fast_type":
        return state_transaction_add_fast_type(update.callback_query.message)
    elif update.callback_query.data == "merchants":
        return state_merchants(update.callback_query.message)
    elif update.callback_query.data == "methods":
        return state_methods(update.callback_query.message)
    elif update.callback_query.data == "categories":
        return state_categories(update.callback_query.message)
    else:
        return state_wip(update.callback_query.message)


def handle_transactions(update: Update, context: CallbackContext):
    if update.callback_query.data == handler_data_add:
        return state_transaction(update.callback_query.message)
    elif update.callback_query.data != handler_data_back:
        pass

    return state_main(update.callback_query.message)


def handle_transaction_add_fast_type(update: Update, context: CallbackContext):
    authorized_data[update.callback_query.message.chat.id]["transaction"]["type"] = update.callback_query.data
    return state_transaction_add_fast_sum(update.callback_query.message)


def handle_transaction_add_fast_sum(update: Update, context: CallbackContext):
    try:
        data = gsh.get_cached_data(["currencies"])

        splitted = update.message.text.split(", ")

        sum = float(splitted[0])

        currency_presented = len(
            splitted) >= 2 and splitted[1].upper() in data["currencies"]["dict"]
        currency = currency_presented and splitted[1] or telegram_config["main_currency"]

        description = currency_presented and len(splitted) >= 3 and (", ".join(
            splitted[2:])) or len(splitted) >= 2 and (", ".join(splitted[1:])) or None

        authorized_data[update.message.chat.id]["transaction"]["sum"] = sum
        authorized_data[update.message.chat.id]["transaction"]["currency"] = currency
        if description:
            authorized_data[update.message.chat.id]["transaction"]["description"] = description

        update.message.reply_text(display_text_add_transaction(authorized_data[update.message.chat.id]["transaction"]) + ". How?",
                                  reply_markup=keyboard_methods())

        return states["transaction_add_fast_method"]
    except ValueError:
        return state_main_reply(update.message)


def handle_transaction_add_fast_method(update: Update, context: CallbackContext):
    if update.callback_query.data == handler_data_add:
        authorized_data[update.callback_query.message.chat.id]["last_state"] = state_transaction
        return state_merchant(update.callback_query.message)
    else:
        authorized_data[update.callback_query.message.chat.id]["transaction"]["method"] = update.callback_query.data

        if authorized_data[update.callback_query.message.chat.id]["transaction"]["type"] == "TRANSFER":
            update.callback_query.message.edit_text(display_text_add_transaction(
                authorized_data[update.callback_query.message.chat.id]["transaction"]) + ". To what method?", reply_markup=keyboard_methods())

            return states["transaction_add_fast_target_method"]
        elif authorized_data[update.callback_query.message.chat.id]["transaction"]["type"] == "CORRECTION":
            return state_transaction(update.callback_query.message)
        else:
            update.callback_query.message.edit_text(display_text_add_transaction(authorized_data[update.callback_query.message.chat.id]["transaction"]) + ". Where?",
                                                    reply_markup=keyboard_merchants())

            return states["transaction_add_fast_merchant"]


def handle_transaction_add_fast_merchant(update: Update, context: CallbackContext):
    if update.callback_query.data == handler_data_add:
        authorized_data[update.callback_query.message.chat.id]["last_state"] = state_transaction
        return state_merchant(update.callback_query.message)
    else:
        authorized_data[update.callback_query.message.chat.id]["transaction"]["merchant"] = update.callback_query.data
        return state_transaction(update.callback_query.message)


def handle_transaction_add_fast_target_method(update: Update, context: CallbackContext):
    if update.callback_query.data == handler_data_add:
        authorized_data[update.callback_query.message.chat.id]["last_state"] = state_transaction
        return state_merchant(update.callback_query.message)
    else:
        authorized_data[update.callback_query.message.chat.id]["transaction"]["target_method"] = update.callback_query.data
        return state_transaction(update.callback_query.message)


def handle_transaction(update: Update, context: CallbackContext):
    if update.callback_query.data != handler_data_back:
        if update.callback_query.data == handler_data_submit:
            return transaction_submit(update.callback_query.message)

    return state_transactions(update.callback_query.message)


def handle_transaction_type(update: Update, context: CallbackContext):
    return state_transaction(update.callback_query.message)


def handle_transaction_date(update: Update, context: CallbackContext):
    return state_transaction(update.callback_query.message)


def handle_transaction_sum(update: Update, context: CallbackContext):
    return state_transaction(update.callback_query.message)


def handle_transaction_currency(update: Update, context: CallbackContext):
    return state_transaction(update.callback_query.message)


def handle_transaction_method(update: Update, context: CallbackContext):
    return state_transaction(update.callback_query.message)


def handle_transaction_merchant(update: Update, context: CallbackContext):
    return state_transaction(update.callback_query.message)


def handle_transaction_description(update: Update, context: CallbackContext):
    return state_transaction(update.callback_query.message)


def handle_merchants(update: Update, context: CallbackContext):
    if update.callback_query.data == handler_data_add:
        authorized_data[update.callback_query.message.chat.id]["merchant"]["_NEW"] = True
        return state_merchant(update.callback_query.message)
    elif update.callback_query.data != handler_data_back:
        data = gsh.get_cached_data(["merchants"])
        send_info_message(update.callback_query.from_user.first_name + " has selected " +
                          data["merchants"]["dict"][update.callback_query.data]["name"] + " and everyone should be aware of it")

    return state_main(update.callback_query.message)


def handle_merchant(update: Update, context: CallbackContext):
    if update.callback_query.data != handler_data_back:
        if update.callback_query.data == handler_data_submit:
            return merchant_submit(update.callback_query.message)
        elif update.callback_query.data == "_EDIT_NAME":
            return state_merchant_name(update.callback_query.message)
        elif update.callback_query.data == "_EDIT_CATEGORY":
            return state_merchant_category(update.callback_query.message)

    return state_merchants(update.callback_query.message)


def handle_merchant_name(update: Update, context: CallbackContext):
    authorized_data[update.message.chat.id]["merchant"]["name"] = update.message.text
    if "_NEW" in authorized_data[update.message.chat.id]["merchant"] or "id" not in authorized_data[update.message.chat.id]["merchant"]:
        authorized_data[update.message.chat.id]["merchant"]["id"] = generate_id(
            "merchants", update.message.text)

    return state_merchant_reply(update.message)


def handle_merchant_keywords(update: Update, context: CallbackContext):
    return state_merchant_reply(update.message)


def handle_merchant_category(update: Update, context: CallbackContext):
    if update.callback_query.data != handler_data_back:
        authorized_data[update.callback_query.message.chat.id]["merchant"]["category"] = update.callback_query.data

    return state_merchant(update.callback_query.message)


def handle_merchant_emoji(update: Update, context: CallbackContext):
    return state_merchant_reply(update.message)


def handle_methods(update: Update, context: CallbackContext):
    if update.callback_query.data == handler_data_add:
        authorized_data[update.callback_query.message.chat.id]["method"]["_NEW"] = True
        return state_method(update.callback_query.message)
    elif update.callback_query.data != handler_data_back:
        data = gsh.get_cached_data(["methods"])
        send_info_message(update.callback_query.from_user.first_name + " has selected " +
                          data["methods"]["dict"][update.callback_query.data]["name"] + " and everyone should be aware of it")

    return state_main(update.callback_query.message)


def handle_method(update: Update, context: CallbackContext):
    if update.callback_query.data != handler_data_back:
        if update.callback_query.data == handler_data_submit:
            return method_submit(update.callback_query.message)

    return state_methods(update.callback_query.message)


def handle_method_name(update: Update, context: CallbackContext):
    return state_method(update.callback_query.message)


def handle_method_is_mir(update: Update, context: CallbackContext):
    return state_method(update.callback_query.message)


def handle_method_is_credit(update: Update, context: CallbackContext):
    return state_method(update.callback_query.message)


def handle_method_is_cashback(update: Update, context: CallbackContext):
    return state_method(update.callback_query.message)


def handle_method_owner(update: Update, context: CallbackContext):
    return state_method(update.callback_query.message)


def handle_categories(update: Update, context: CallbackContext):
    if update.callback_query.data == handler_data_add:
        pass
    elif update.callback_query.data != handler_data_back:
        data = gsh.get_cached_data(["categories"])
        send_info_message(update.callback_query.from_user.first_name + " has selected " + data["categories"]["dict"][update.callback_query.data]["emoji"] + " "
                          + data["categories"]["dict"][update.callback_query.data]["name"] + " and everyone should be aware of it")

    return state_main(update.callback_query.message)


def handle_currencies(update: Update, context: CallbackContext):
    return state_main(update.callback_query.message)


def handle_wip(update: Update, context: CallbackContext):
    return state_main(update.callback_query.message)


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
