import datetime
import difflib
from math import ceil

import google_sheets_handler as gsh
import tasks_handler
import telegram
import utils.date_utils as date_utils
import utils.id_utils as id_utils
import utils.thread_utils as thread_utils
import utils.yaml_manager as yaml_manager
from telegram import InlineKeyboardMarkup, Message, Update
from telegram.ext import CallbackQueryHandler, ConversationHandler, Filters, Updater
from telegram.ext.callbackcontext import CallbackContext
from telegram.ext.commandhandler import CommandHandler
from telegram.ext.filters import Filters
from telegram.ext.messagehandler import MessageHandler
from telegram.ext.updater import Updater
from telegram.update import Update

print_label = "[telegram_handler]"


updater = None

states_count = 0
states_list = [
    "main",
    "wip",
    "finances",
    "transactions",
    "transaction_add_fast_type",
    "transaction_add_fast_sum",
    "transaction_add_fast_method",
    "transaction_add_fast_target",
    "transaction",
    "transaction_type",
    "transaction_date",
    "transaction_sum",
    "transaction_currency",
    "transaction_method",
    "transaction_target",
    "transaction_description",
    "merchants",
    "merchant",
    "merchant_name",
    "merchant_keywords",
    "merchant_category",
    "merchant_emoji",
    "methods",
    "method",
    "method_name",
    "method_emoji",
    "method_is_account",
    "method_is_mir",
    "method_is_credit",
    "method_is_cashback",
    "method_owner",
    "categories",
    "currencies",
    "tasks",
    "tasks_current",
    "task_current",
    "task_current_name",
    "task_current_due_to",
    "tasks_scheduled",
    "task_scheduled",
    "plants",
    "users",
]

states = {}

for state in states_list:
    states[state] = states_count
    states_count += 1

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
        entry_points=[CommandHandler("start", command_start)],
        states={
            states["main"]: [CallbackQueryHandler(handle_main)],
            states["wip"]: [CallbackQueryHandler(handle_wip)],
            states["finances"]: [CallbackQueryHandler(handle_finances)],
            states["transactions"]: [CallbackQueryHandler(handle_transactions)],
            states["transaction_add_fast_type"]: [
                CallbackQueryHandler(handle_transaction_add_fast_type)
            ],
            states["transaction_add_fast_sum"]: [
                MessageHandler(text_filters(), handle_transaction_add_fast_sum)
            ],
            states["transaction_add_fast_method"]: [
                CallbackQueryHandler(handle_transaction_add_fast_method)
            ],
            states["transaction_add_fast_target"]: [
                CallbackQueryHandler(handle_transaction_add_fast_merchant)
            ],
            states["transaction"]: [CallbackQueryHandler(handle_transaction)],
            states["transaction_type"]: [CallbackQueryHandler(handle_transaction_type)],
            states["transaction_date"]: [CallbackQueryHandler(handle_transaction_date)],
            states["transaction_sum"]: [
                MessageHandler(text_filters(), handle_transaction_sum)
            ],
            states["transaction_currency"]: [
                CallbackQueryHandler(handle_transaction_currency)
            ],
            states["transaction_method"]: [
                CallbackQueryHandler(handle_transaction_method)
            ],
            states["transaction_target"]: [
                CallbackQueryHandler(handle_transaction_target)
            ],
            states["transaction_description"]: [
                MessageHandler(text_filters(), handle_transaction_description)
            ],
            states["merchants"]: [CallbackQueryHandler(handle_merchants)],
            states["merchant"]: [CallbackQueryHandler(handle_merchant)],
            states["merchant_name"]: [
                MessageHandler(text_filters(), handle_merchant_name)
            ],
            states["merchant_keywords"]: [
                MessageHandler(text_filters(), handle_merchant_keywords)
            ],
            states["merchant_category"]: [
                CallbackQueryHandler(handle_merchant_category)
            ],
            states["merchant_emoji"]: [
                MessageHandler(text_filters(), handle_merchant_emoji)
            ],
            states["methods"]: [CallbackQueryHandler(handle_methods)],
            states["method"]: [CallbackQueryHandler(handle_method)],
            states["method_name"]: [MessageHandler(text_filters(), handle_method_name)],
            states["method_emoji"]: [
                MessageHandler(text_filters(), handle_method_emoji)
            ],
            states["method_is_account"]: [
                CallbackQueryHandler(handle_method_is_account)
            ],
            states["method_is_mir"]: [CallbackQueryHandler(handle_method_is_mir)],
            states["method_is_credit"]: [CallbackQueryHandler(handle_method_is_credit)],
            states["method_is_cashback"]: [
                CallbackQueryHandler(handle_method_is_cashback)
            ],
            states["method_owner"]: [CallbackQueryHandler(handle_method_owner)],
            states["categories"]: [CallbackQueryHandler(handle_categories)],
            states["currencies"]: [CallbackQueryHandler(handle_currencies)],
            states["tasks"]: [CallbackQueryHandler(handle_tasks)],
            states["tasks_current"]: [CallbackQueryHandler(handle_tasks_current)],
            states["task_current"]: [CallbackQueryHandler(handle_task_current)],
            states["task_current_name"]: [
                MessageHandler(text_filters(), handle_task_current_name)
            ],
            states["tasks_scheduled"]: [CallbackQueryHandler(handle_tasks_scheduled)],
            states["task_scheduled"]: [CallbackQueryHandler(handle_task_scheduled)],
            states["plants"]: [CallbackQueryHandler(handle_plants)],
            states["users"]: [CallbackQueryHandler(handle_users)],
        },
        fallbacks=[CommandHandler("start", command_start)],
    )

    updater.dispatcher.add_handler(conv_handler)

    print(print_label, "Setting Telegram commands...")
    add_command("help", command_help)
    add_command("update", command_update)

    print(print_label, "Setting Telegram handlers...")
    updater.dispatcher.add_handler(
        MessageHandler(
            Filters.command & auth_filter() & conversation_filter(), fallback
        )
    )
    updater.dispatcher.add_handler(
        MessageHandler(Filters.text & auth_filter() & conversation_filter(), fallback)
    )
    updater.dispatcher.add_handler(
        CallbackQueryHandler(fallback_callback_query_handler)
    )

    print(print_label, "Starting Telegram polling...")
    updater.start_polling()

    for authorized in telegram_config["authorized"]:
        if authorized not in authorized_data:
            authorized_data[authorized] = empty_user()

    send_message_to_authorized("Hello, I've just started, so I need you to type /start")

    print(print_label, "Started")

    if general_config["production_mode"]:
        tasks_handler.check_tasks()
    else:
        # tasks_handler.schedule_tasks()
        updater.idle()

    # thread_utils.run_io_tasks_in_parallel(
    #     [
    #         updater.idle,
    #         tasks_handler.check_tasks,
    #     ]
    # )

    print(print_label, "Started completely")


# local utils


def text_filters():
    return Filters.text & auth_filter() & conversation_filter()


def send_message_to_authorized(message):
    print(print_label, "send_message_to_authorized", message)
    if not general_config["quiet_mode"]:
        for authorized in telegram_config["authorized"]:
            updater.bot.send_message(chat_id=authorized, text=message)


def send_info_message(message):
    print(print_label, "send_info_message", message)
    if not general_config["quiet_mode"]:
        for info_chat in telegram_config["info_chats"]:
            updater.bot.send_message(chat_id=info_chat, text=message)


def auth_filter():
    return Filters.user(user_id=telegram_config["authorized"])


def conversation_filter():
    return Filters.chat(chat_id=telegram_config["authorized"])


def add_command(name, callback):
    updater.dispatcher.add_handler(
        CommandHandler(name, callback, auth_filter() & conversation_filter())
    )


def parse_sum_text(text: str):
    splitted = text.split(" ")
    try:
        return {
            "sum": float(splitted[0]),
            "currency": len(splitted) >= 2
            and splitted[1]
            or telegram_config["main_currency"],
        }
    except:
        return {"sum": 0, "currency": telegram_config["main_currency"]}


def display_text_method(method: dict, button=False):
    data = gsh.get_cached_data(["users"])

    owner_emoji = (
        method.get("owner", False)
        and (data["users"]["dict"][method["owner"]]["emoji"])
        or ""
    )
    method_name = method.get("name", "New method")
    method_emoji = method.get("emoji", False) and (" " + method["emoji"]) or ""
    method_is_account = method.get("is_account", False) and " Account" or ""
    method_is_mir = method.get("is_mir", False) and " MIR" or ""
    method_is_credit = method.get("is_credit", False) and " Credit" or ""
    method_is_cashback = method.get("is_cashback", False) and " Cashback" or ""

    return (
        owner_emoji
        + method_emoji
        + " "
        + method_name
        + method_is_account
        + method_is_mir
        + method_is_credit
        + method_is_cashback
    )


def display_text_add_transaction(add_transaction: dict):
    data = gsh.get_cached_data(["methods", "merchants"])

    text = ""

    if "type" in add_transaction:
        text = add_transaction["type"] + "\n"

    if (
        "date" in add_transaction
        and add_transaction["date"].date() != datetime.datetime.today().date()
    ):
        text = text + "(" + add_transaction["date"].strftime("%Y-%m-%d") + ") "

    text = (
        text
        + str("sum" in add_transaction and add_transaction["sum"] or 0)
        + " "
        + ("currency" in add_transaction and add_transaction["currency"] or "RUB")
    )
    try:
        if "method" in add_transaction:
            text = (
                text
                + " — "
                + display_text_method(
                    data["methods"]["dict"][add_transaction["method"]]
                )
            )

        if "type" in add_transaction and add_transaction["type"] == "TRANSFER":
            if "target_method" in add_transaction:
                text = (
                    text
                    + " > "
                    + display_text_method(
                        data["methods"]["dict"][add_transaction["target_method"]]
                    )
                )
            if "description" in add_transaction:
                text = text + " — " + add_transaction["description"]
        else:
            if (
                "merchant" in add_transaction
                and "description" in add_transaction
                and add_transaction["description"]
            ):
                text = (
                    text
                    + " — "
                    + data["merchants"]["dict"][add_transaction["merchant"]]["name"]
                    + " ("
                    + add_transaction["description"]
                    + ")"
                )
            elif "merchant" in add_transaction:
                text = (
                    text
                    + " — "
                    + data["merchants"]["dict"][add_transaction["merchant"]]["name"]
                )
            elif "description" in add_transaction and add_transaction["description"]:
                text = text + " — " + add_transaction["description"]
    except:
        pass
    return str(text)


def display_text_task_current(task_current: dict, short_info=False):
    task_current_overdue: str = (
        (
            (
                "due_to" in task_current
                and task_current["due_to"]
                and (task_current["due_to"].date() < datetime.datetime.today().date())
            )
            or (
                "scheduled_id" in task_current
                and task_current["scheduled_id"]
                and (task_current["created"].date() < datetime.datetime.today().date())
            )
        )
        and "⚠️"
        or ""
    )
    task_current_importance: str = (
        "importance" in task_current and task_current["importance"] and "🚩" or ""
    )
    task_current_urgency: str = (
        "urgency" in task_current and task_current["urgency"] and "⚡️" or ""
    )
    task_current_due_to: str = (
        "due_to" in task_current and task_current["due_to"] and "🗓" or ""
    )
    task_current_schedlued: str = (
        "scheduled_id" in task_current and task_current["scheduled_id"] and "🔁" or ""
    )

    task_current_name: str = task_current.get("name", "New task")

    if short_info:
        return (
            task_current_overdue
            + task_current_importance
            + task_current_urgency
            + task_current_due_to
            + task_current_schedlued
            + " "
            + task_current_name
        )
    else:
        return str(task_current)


def display_text_task_scheduled(task_scheduled: dict, short_info=False):
    task_scheduled_importance: str = (
        "importance" in task_scheduled and task_scheduled["importance"] and "🚩" or ""
    )
    task_scheduled_urgency: str = (
        "urgency" in task_scheduled and task_scheduled["urgency"] and "⚡️" or ""
    )
    task_scheduled_name = task_scheduled.get("name", "New task")
    if task_scheduled["scheduled"]:
        task_scheduled_span = "⚡️"
    else:
        task_scheduled_span = (
            "⏲"
            + str(
                max(
                    task_scheduled["recurring_value"]
                    - (task_scheduled["recurring_stage"] - 1),
                    1,
                )
            )
            + "d "
        )
    task_scheduled_done = "☑️" + str(task_scheduled["times_done"])

    if short_info:
        return (
            task_scheduled_importance
            + task_scheduled_urgency
            + task_scheduled_name
            + " "
            + task_scheduled_span
            + task_scheduled_done
        )
    else:
        return str(task_scheduled)


def get_transaction_target_type(transaction):
    return (
        ("type" in transaction and transaction["type"] == "TRANSFER")
        and "target_method"
        or "merchant"
    )


def transaction_submit(message: Message):
    data = authorized_data[message.chat.id]["transaction"]

    target = get_transaction_target_type(data)

    if (
        ("type" in data)
        and ("sum" in data and data["sum"] > 0)
        and ("currency" in data)
        and ("method" in data)
        and (data["type"] == "CORRECTION" or target in data)
    ):
        send_info_message(display_text_add_transaction(data))

        date = "date" in data and data["date"] or datetime.datetime.today()

        gsh.insert_into_sheet(
            ("transactions", date_utils.get_date_code(date)),
            [
                [
                    data["type"],
                    (date - datetime.datetime(1899, 12, 30)).days,
                    data["sum"],
                    data["currency"],
                    data["method"],
                    data["type"] != "CORRECTION" and data[target] or "",
                    "description" in data and data["description"] or "",
                ]
            ],
        )

        authorized_data[message.chat.id]["transaction"] = {}
        authorized_data[message.chat.id]["merchant_category"] = ""

        authorized_data[message.chat.id]["last_state"] = state_main

        return state_main(message)
    else:
        return state_transactions(message)


def merchant_submit(message: Message):
    data = authorized_data[message.chat.id]["merchant"]

    if "id" in data:
        send_info_message("New merchant: " + data["id"])

        gsh.insert_into_sheet(
            "merchants",
            [
                [
                    data["id"],
                    "name" in data and data["name"] or data["id"],
                    "keywords" in data and data["keywords"] or "",
                    "category" in data and data["category"] or "OTHER",
                    "emoji" in data and data["emoji"] or "",
                ]
            ],
        )

        authorized_data[message.chat.id]["merchant"] = {}
        authorized_data[message.chat.id]["transaction"]["merchant"] = data["id"]
        authorized_data[message.chat.id]["merchant_category"] = ""

        gsh.get_cached_data(["merchants"], update=True)

        return authorized_data[message.chat.id]["last_state"](message)
    else:
        return state_merchants(message)


def method_submit(message: Message):
    data = authorized_data[message.chat.id]["method"]

    if "id" in data:
        send_info_message(
            "New method: " + data["id"] + " — " + display_text_method(data)
        )

        gsh.insert_into_sheet(
            "methods",
            [
                [
                    data["id"],
                    "name" in data and data["name"] or data["id"],
                    "emoji" in data and data["emoji"] or "",
                    "is_account" in data and data["is_account"] and True or False,
                    "is_mir" in data and data["is_mir"] and True or False,
                    "is_credit" in data and data["is_credit"] and True or False,
                    "is_cashback" in data and data["is_cashback"] and True or False,
                    "owner" in data and data["owner"] or "SHARED",
                ]
            ],
        )

        authorized_data[message.chat.id]["method"] = {}
        authorized_data[message.chat.id]["transaction"]["method"] = data["id"]
        authorized_data[message.chat.id]["merchant_category"] = ""

        gsh.get_cached_data(["methods"], update=True)

        return authorized_data[message.chat.id]["last_state"](message)
    else:
        return state_methods(message)


def task_current_submit(message: Message):
    data = authorized_data[message.chat.id]["task_current"]

    if "id" in data:
        send_info_message("New current task: " + data["id"])

        due_to = "due_to" in data and data["due_to"] or ""

        gsh.insert_into_sheet(
            "tasks_current",
            [
                [
                    data["id"],
                    "name" in data and data["name"] or data["id"],
                    "importance" in data and data["importance"] and True or False,
                    "urgency" in data and data["urgency"] and True or False,
                    "scheduled_id" in data and data["scheduled_id"] or "",
                    (datetime.datetime.today() - datetime.datetime(1899, 12, 30)).days,
                    due_to,
                    "",
                ]
            ],
        )

        authorized_data[message.chat.id]["task_current"] = {}

        gsh.get_cached_data(["tasks_current"], update=True)

        return authorized_data[message.chat.id]["last_state"](message)
    else:
        return state_tasks_current(message)


# keyboard rows


def get_page_items(page, per_page, limit=None):
    return (((page * per_page) - per_page) + 1, limit or (page * per_page))


def format_page_items(page, per_page, limit=None):
    items = get_page_items(page, per_page, limit)
    return "{}-{}".format(items[0], items[1])


def keyboard_row_pagination(page_user_data):
    return [
        telegram.InlineKeyboardButton(
            text=(format_page_items(1, page_user_data["data"]["per_page"])),
            callback_data="_PAGE_START",
        ),
        telegram.InlineKeyboardButton(text="◀️", callback_data="_PAGE_BACK"),
        telegram.InlineKeyboardButton(text="▶️", callback_data="_PAGE_FORWARD"),
        telegram.InlineKeyboardButton(
            text=(
                format_page_items(
                    page_user_data["data"]["pages"],
                    page_user_data["data"]["per_page"],
                    limit=page_user_data["data"]["items"],
                )
            ),
            callback_data="_PAGE_END",
        ),
    ]


def keyboard_row_back():
    return [
        telegram.InlineKeyboardButton(text="⬅️ Back", callback_data=handler_data_back)
    ]


def keyboard_row_back_and_add():
    return [
        telegram.InlineKeyboardButton(text="⬅️ Back", callback_data=handler_data_back),
        telegram.InlineKeyboardButton(text="🆕 Add new", callback_data=handler_data_add),
    ]


def keyboard_row_back_and_submit():
    return [
        telegram.InlineKeyboardButton(text="⬅️ Back", callback_data=handler_data_back),
        telegram.InlineKeyboardButton(
            text="✅ Submit", callback_data=handler_data_submit
        ),
    ]


# full keyboards


def keyboard_main():
    reply_keyboard = [
        [
            telegram.InlineKeyboardButton(
                text="💸 Add transaction", callback_data="transaction_add_fast_type"
            ),
            telegram.InlineKeyboardButton(
                text="✍️🗒 New task", callback_data="task_current"
            ),
        ],
        [
            telegram.InlineKeyboardButton(text="💰 Finances", callback_data="finances"),
            telegram.InlineKeyboardButton(text="🗒⏰ Tasks", callback_data="tasks"),
            # telegram.InlineKeyboardButton(text="🌱 Plants", callback_data="plants"),
        ],
        [
            telegram.InlineKeyboardButton(text="👫 Users", callback_data="users"),
        ],
    ]
    return InlineKeyboardMarkup(reply_keyboard)


def keyboard_finances():
    reply_keyboard = [
        [
            telegram.InlineKeyboardButton(
                text="👛 Transactions", callback_data="transactions"
            ),
            telegram.InlineKeyboardButton(
                text="💸 Add transaction", callback_data="transaction_add_fast_type"
            ),
        ],
        [
            telegram.InlineKeyboardButton(
                text="🏪 Merchants", callback_data="merchants"
            ),
            telegram.InlineKeyboardButton(text="💳 Methods", callback_data="methods"),
        ],
        [
            telegram.InlineKeyboardButton(
                text="🏷 Categories", callback_data="categories"
            ),
            telegram.InlineKeyboardButton(
                text="💱 Currencies", callback_data="currencies"
            ),
        ],
    ]
    reply_keyboard.append(keyboard_row_back())
    return InlineKeyboardMarkup(reply_keyboard)


def keyboard_transactions():
    reply_keyboard = [keyboard_row_back_and_add()]

    return InlineKeyboardMarkup(reply_keyboard)


def keyboard_transaction_type():
    reply_keyboard = []

    reply_keyboard.append(
        [
            telegram.InlineKeyboardButton("Expense", callback_data="EXPENSE"),
            telegram.InlineKeyboardButton("Income", callback_data="INCOME"),
        ]
    )
    reply_keyboard.append(
        [
            telegram.InlineKeyboardButton("Transfer", callback_data="TRANSFER"),
            telegram.InlineKeyboardButton("Correction", callback_data="CORRECTION"),
        ]
    )
    reply_keyboard.append(keyboard_row_back())

    return InlineKeyboardMarkup(reply_keyboard)


def keyboard_transaction():
    reply_keyboard = []

    reply_keyboard.append(
        [
            telegram.InlineKeyboardButton("Edit type", callback_data="type"),
            telegram.InlineKeyboardButton("Edit date", callback_data="date"),
        ]
    )
    # telegram.InlineKeyboardButton("Edit currency", callback_data="currency")
    reply_keyboard.append(
        [telegram.InlineKeyboardButton("Edit sum", callback_data="sum")]
    )
    reply_keyboard.append(
        [
            telegram.InlineKeyboardButton("Edit method", callback_data="method"),
            telegram.InlineKeyboardButton("Edit target", callback_data="target"),
        ]
    )
    reply_keyboard.append(
        [
            telegram.InlineKeyboardButton(
                "Edit description", callback_data="description"
            ),
            telegram.InlineKeyboardButton(
                "Remove description", callback_data="description_remove"
            ),
        ]
    )
    reply_keyboard.append(keyboard_row_back_and_submit())

    return InlineKeyboardMarkup(reply_keyboard)


def keyboard_categories():
    data = gsh.get_cached_data(["categories"])

    reply_keyboard = [[]]

    current_row = 0

    for id in data["categories"]["list"]:
        reply_keyboard[current_row].append(
            telegram.InlineKeyboardButton(
                text=data["categories"]["dict"][id]["emoji"]
                + " "
                + data["categories"]["dict"][id]["name"],
                callback_data=id,
            )
        )
        if len(reply_keyboard[current_row]) >= 3:
            reply_keyboard.append([])
            current_row = current_row + 1

    reply_keyboard.append(keyboard_row_back())

    return InlineKeyboardMarkup(reply_keyboard)


def keyboard_categories_merchant_info():
    data = gsh.get_cached_data(["categories", "merchants"])

    reply_keyboard = [[]]

    current_row = 0

    for id in data["categories"]["list"]:
        if id in data["merchants"]["by_category"]:
            reply_keyboard[current_row].append(
                telegram.InlineKeyboardButton(
                    text=data["categories"]["dict"][id]["emoji"]
                    + " "
                    + data["categories"]["dict"][id]["name"]
                    + " ("
                    + str(len(data["merchants"]["by_category"][id]))
                    + ")",
                    callback_data=id,
                )
            )
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
        reply_keyboard[current_row].append(
            telegram.InlineKeyboardButton(
                text=display_text_method(data["methods"]["dict"][id]), callback_data=id
            )
        )
        if len(reply_keyboard[current_row]) >= 2:
            reply_keyboard.append([])
            current_row = current_row + 1

    reply_keyboard.append(keyboard_row_back_and_add())

    return InlineKeyboardMarkup(reply_keyboard)


def keyboard_method():
    reply_keyboard = []

    reply_keyboard.append(
        [
            telegram.InlineKeyboardButton("Edit name", callback_data="name"),
            telegram.InlineKeyboardButton("Edit emoji", callback_data="emoji"),
            telegram.InlineKeyboardButton("Edit owner", callback_data="owner"),
        ]
    )

    reply_keyboard.append(
        [
            telegram.InlineKeyboardButton("Is account", callback_data="is_account"),
            telegram.InlineKeyboardButton("Is MIR", callback_data="is_mir"),
            telegram.InlineKeyboardButton("Is credit", callback_data="is_credit"),
            telegram.InlineKeyboardButton("Has cashback", callback_data="is_cashback"),
        ]
    )

    reply_keyboard.append(keyboard_row_back_and_submit())

    return InlineKeyboardMarkup(reply_keyboard)


def keyboard_merchants(merchant_category: str):
    data = gsh.get_cached_data(["merchants", "categories"])

    reply_keyboard = [[]]

    current_row = 0

    for id in data["merchants"]["list"]:
        if (
            not merchant_category
            or merchant_category == data["merchants"]["dict"][id]["category"]
        ):
            reply_keyboard[current_row].append(
                telegram.InlineKeyboardButton(
                    text=(
                        data["merchants"]["dict"][id]["emoji"]
                        or data["categories"]["dict"][
                            data["merchants"]["dict"][id]["category"]
                        ]["emoji"]
                    )
                    + " "
                    + data["merchants"]["dict"][id]["name"],
                    callback_data=id,
                )
            )
            if len(reply_keyboard[current_row]) >= 3:
                reply_keyboard.append([])
                current_row = current_row + 1

    reply_keyboard.append(keyboard_row_back_and_add())

    return InlineKeyboardMarkup(reply_keyboard)


def keyboard_merchant():
    reply_keyboard = []

    reply_keyboard.append(
        [
            telegram.InlineKeyboardButton("Edit name", callback_data="name"),
            telegram.InlineKeyboardButton("Edit emoji", callback_data="emoji"),
            telegram.InlineKeyboardButton("Edit category", callback_data="category"),
        ]
    )

    reply_keyboard.append(keyboard_row_back_and_submit())

    return InlineKeyboardMarkup(reply_keyboard)


def keyboard_currencies():
    data = gsh.get_cached_data(["currencies"])

    reply_keyboard = [[]]

    current_row = 0

    for id in data["currencies"]["list"]:
        reply_keyboard[current_row].append(
            telegram.InlineKeyboardButton(
                text=data["currencies"]["dict"][id]["name"], callback_data=id
            )
        )
        if len(reply_keyboard[current_row]) >= 4:
            reply_keyboard.append([])
            current_row = current_row + 1

    reply_keyboard.append(keyboard_row_back())

    return InlineKeyboardMarkup(reply_keyboard)


def keyboard_tasks():
    reply_keyboard = [
        [
            telegram.InlineKeyboardButton(
                text="✍️🗒 New task", callback_data="task_current"
            ),
            # telegram.InlineKeyboardButton(
            #     text="✍️⏰ New scheduled task", callback_data="task_scheduled"),
        ],
        [
            telegram.InlineKeyboardButton(
                text="🗒 Current tasks", callback_data="tasks_current"
            ),
            telegram.InlineKeyboardButton(
                text="⏰ Scheduled tasks", callback_data="tasks_scheduled"
            ),
        ],
    ]
    reply_keyboard.append(keyboard_row_back())
    return InlineKeyboardMarkup(reply_keyboard)


def keyboard_tasks_current(page_user_data):
    data = gsh.get_cached_data(["tasks_current"])

    reply_keyboard = [[]]

    current_row = 0

    page_user_data["data"] = data["tasks_current"]["pagination"]

    if page_user_data["page"] > page_user_data["data"]["pages"]:
        page_user_data["page"] = page_user_data["data"]["pages"]

    items = get_page_items(
        page_user_data["page"],
        page_user_data["data"]["per_page"],
        limit=page_user_data["data"]["pages"] == page_user_data["page"]
        and page_user_data["data"]["items"]
        or None,
    )

    for number, id in enumerate(
        data["tasks_current"]["list"][(items[0] - 1) : items[1]], start=items[0]
    ):
        if not data["tasks_current"]["dict"][id]["done"]:
            reply_keyboard[current_row].append(
                telegram.InlineKeyboardButton(
                    text=(
                        str(number)
                        + ". "
                        + display_text_task_current(
                            data["tasks_current"]["dict"][id], True
                        )
                    ),
                    callback_data=id,
                )
            )
            if len(reply_keyboard[current_row]) >= 1:
                reply_keyboard.append([])
                current_row = current_row + 1
    if page_user_data["data"]["pages"] > 1:
        reply_keyboard.append(keyboard_row_pagination(page_user_data))
    reply_keyboard.append(keyboard_row_back_and_add())
    return InlineKeyboardMarkup(reply_keyboard)


def keyboard_task_current(data):
    reply_keyboard = []
    reply_keyboard.append(
        [telegram.InlineKeyboardButton("Edit name", callback_data="name")]
    )
    if "_NEW" not in data:
        reply_keyboard.append(
            [
                # telegram.InlineKeyboardButton(
                #     "🙅‍♀️ Ignore", callback_data="_TASK_IGNORE"
                # ),
                telegram.InlineKeyboardButton("🏆 Done", callback_data="_TASK_DONE"),
            ]
        )

    reply_keyboard.append(keyboard_row_back_and_submit())
    return InlineKeyboardMarkup(reply_keyboard)


def keyboard_tasks_scheduled():
    data = gsh.get_cached_data(["tasks_scheduled"])

    reply_keyboard = [[]]

    current_row = 0

    for id in data["tasks_scheduled"]["list"]:
        reply_keyboard[current_row].append(
            telegram.InlineKeyboardButton(
                text=display_text_task_scheduled(
                    data["tasks_scheduled"]["dict"][id], True
                ),
                callback_data=id,
            )
        )
        if len(reply_keyboard[current_row]) >= 1:
            reply_keyboard.append([])
            current_row = current_row + 1

    reply_keyboard.append(keyboard_row_back_and_add())
    return InlineKeyboardMarkup(reply_keyboard)


def keyboard_task_scheduled():
    reply_keyboard = []
    reply_keyboard.append(keyboard_row_back())
    return InlineKeyboardMarkup(reply_keyboard)


def keyboard_plants():
    reply_keyboard = [
        [
            telegram.InlineKeyboardButton(text="Plants", callback_data="plants_plants"),
            telegram.InlineKeyboardButton(text="Lots", callback_data="plants_lots"),
            telegram.InlineKeyboardButton(
                text="Plant types", callback_data="plant_types"
            ),
        ]
    ]
    reply_keyboard.append(keyboard_row_back())
    return InlineKeyboardMarkup(reply_keyboard)


def keyboard_users():
    data = gsh.get_cached_data(["users"])

    reply_keyboard = [[]]

    current_row = 0

    for id in data["users"]["list"]:
        reply_keyboard[current_row].append(
            telegram.InlineKeyboardButton(
                text=data["users"]["dict"][id]["name"], callback_data=id
            )
        )
        if len(reply_keyboard[current_row]) >= 3:
            reply_keyboard.append([])
            current_row = current_row + 1

    reply_keyboard.append(keyboard_row_back())

    return InlineKeyboardMarkup(reply_keyboard)


def keyboard_dates(date_offset: int):
    reply_keyboard = []

    today = datetime.datetime.today()

    dates = date_utils.date_range(
        today - datetime.timedelta(days=(date_offset * 7 + 6)),
        today - datetime.timedelta(days=(date_offset * 7)),
    )

    for date in dates:
        reply_keyboard.append(
            [
                telegram.InlineKeyboardButton(
                    date.strftime("%Y-%m-%d (%a)"),
                    callback_data=date.strftime("%Y_%m_%d"),
                )
            ]
        )

    control_buttons = [
        telegram.InlineKeyboardButton("⏪", callback_data="_DATE_REWIND_BACKWARD"),
        telegram.InlineKeyboardButton("⬅️", callback_data="_DATE_BACKWARD"),
    ]

    if date_offset > 0:
        control_buttons.append(
            telegram.InlineKeyboardButton("Today", callback_data="_DATE_TODAY")
        )
        if date_offset > 1:
            control_buttons.append(
                telegram.InlineKeyboardButton("➡️", callback_data="_DATE_FORWARD")
            )
            if date_offset > 2:
                control_buttons.append(
                    telegram.InlineKeyboardButton(
                        "⏩", callback_data="_DATE_REWIND_FORWARD"
                    )
                )

    reply_keyboard.append(control_buttons)

    reply_keyboard.append(keyboard_row_back())

    return InlineKeyboardMarkup(reply_keyboard)


def keyboard_with_back():
    return InlineKeyboardMarkup([keyboard_row_back()])


# commands


def command_start(update: Update, context: CallbackContext):
    if update.message.from_user.id in telegram_config["authorized"]:
        authorized_data[update.message.from_user.id] = empty_user()
        update.message.reply_text(
            "🍏 A fresh start! " + main_entry_text, reply_markup=keyboard_main()
        )
        return states["main"]
    else:
        update.message.reply_text(
            "👋 Hello there! This is a private instance of Budoney Household Management. If you want a personal Budoney instance, follow the link below",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        telegram.InlineKeyboardButton(
                            text="Budoney GitHub repository",
                            url="https://github.com/TimurRin/budoney",
                        )
                    ],
                ]
            ),
        )


def command_update(update: Update, context: CallbackContext):
    update.message.reply_text("Forcing data update, type /start")
    gsh.invalidate_all()


def command_help(update: Update, context: CallbackContext):
    update.message.reply_text("You'll get no help here. Run.")


# states


def state_main(message: Message):
    message.edit_text(main_entry_text, reply_markup=keyboard_main())
    return states["main"]


def state_main_reply(message: Message):
    message.reply_text(main_entry_text, reply_markup=keyboard_main())
    return states["main"]


def state_finances(message: Message):
    message.edit_text("Financial operations", reply_markup=keyboard_finances())
    return states["finances"]


def state_transactions(message: Message):
    message.edit_text("List of transactions", reply_markup=keyboard_transactions())
    return states["transactions"]


def state_transaction_add_fast_type(message: Message):
    message.edit_text(
        "Select transaction type", reply_markup=keyboard_transaction_type()
    )
    return states["transaction_add_fast_type"]


def state_transaction_add_fast_sum(message: Message):
    message.edit_text(
        "Enter transaction data in this sequence \(data in _italic_ may be ommited\): *sum* _currency_, _target_, _description_",
        parse_mode="MarkdownV2",
    )
    return states["transaction_add_fast_sum"]


def state_transaction_add_fast_method(message: Message):
    message.reply_text(
        display_text_add_transaction(authorized_data[message.chat.id]["transaction"])
        + ". How?",
        reply_markup=keyboard_methods(),
    )
    return states["transaction_add_fast_method"]


def state_transaction_add_fast_target(message: Message):
    if authorized_data[message.chat.id]["transaction"].get("type") == "TRANSFER":
        message.edit_text(
            display_text_add_transaction(
                authorized_data[message.chat.id]["transaction"]
            )
            + ". To what method?",
            reply_markup=keyboard_methods(),
        )
    else:
        message.edit_text(
            display_text_add_transaction(
                authorized_data[message.chat.id]["transaction"]
            )
            + ". Where?",
            reply_markup=(
                authorized_data[message.chat.id]["merchant_category"]
                and keyboard_merchants(
                    authorized_data[message.chat.id]["merchant_category"]
                )
                or keyboard_categories_merchant_info()
            ),
        )
    return states["transaction_add_fast_target"]


def state_transaction(message: Message):
    message.edit_text(
        display_text_add_transaction(authorized_data[message.chat.id]["transaction"]),
        reply_markup=keyboard_transaction(),
    )
    return states["transaction"]


def state_transaction_reply(message: Message):
    message.reply_text(
        display_text_add_transaction(authorized_data[message.chat.id]["transaction"]),
        reply_markup=keyboard_transaction(),
    )
    return states["transaction"]


def state_transaction_type(message: Message):
    message.edit_text("Transaction type", reply_markup=keyboard_transaction_type())
    return states["transaction_type"]


def state_transaction_date(message: Message):
    message.edit_text(
        "Transaction date",
        reply_markup=keyboard_dates(authorized_data[message.chat.id]["date_offset"]),
    )
    return states["transaction_date"]


def state_transaction_sum(message: Message):
    message.edit_text("Transaction sum")
    return states["transaction_sum"]


def state_transaction_currency(message: Message):
    message.edit_text("Transaction currency", reply_markup=keyboard_with_back())
    return states["transaction_currency"]


def state_transaction_method(message: Message):
    message.edit_text("Transaction method", reply_markup=keyboard_methods())
    return states["transaction_method"]


def state_transaction_target(message: Message):
    message.edit_text(
        "Transaction target",
        reply_markup=get_transaction_target_type(
            authorized_data[message.chat.id]["transaction"]
        )
        == "target_method"
        and keyboard_methods()
        or (
            authorized_data[message.chat.id]["merchant_category"]
            and keyboard_merchants(
                authorized_data[message.chat.id]["merchant_category"]
            )
            or keyboard_categories_merchant_info()
        ),
    )
    return states["transaction_target"]


def state_transaction_description(message: Message):
    message.edit_text("Transaction description")
    return states["transaction_description"]


def state_merchants(message: Message):
    message.edit_text(
        "List of merchants",
        reply_markup=keyboard_merchants(
            authorized_data[message.chat.id]["merchant_category"]
        ),
    )
    return states["merchants"]


def state_merchant(message: Message):
    message.edit_text(
        str(authorized_data[message.chat.id]["merchant"]),
        reply_markup=keyboard_merchant(),
    )
    return states["merchant"]


def state_merchant_reply(message: Message):
    message.reply_text(
        str(authorized_data[message.chat.id]["merchant"]),
        reply_markup=keyboard_merchant(),
    )
    return states["merchant"]


def state_merchant_name(message: Message):
    message.edit_text("Enter merchant name")
    return states["merchant_name"]


def state_merchant_emoji(message: Message):
    message.edit_text("Enter merchant emoji")
    return states["merchant_emoji"]


def state_merchant_category(message: Message):
    message.edit_text("Select merchant category", reply_markup=keyboard_categories())
    return states["merchant_category"]


def state_methods(message: Message):
    message.edit_text("List of methods", reply_markup=keyboard_methods())
    return states["methods"]


def state_method(message: Message):
    message.edit_text(
        display_text_method(authorized_data[message.chat.id]["method"]),
        reply_markup=keyboard_method(),
    )
    return states["method"]


def state_method_reply(message: Message):
    message.reply_text(
        display_text_method(authorized_data[message.chat.id]["method"]),
        reply_markup=keyboard_method(),
    )
    return states["method"]


def state_method_name(message: Message):
    message.edit_text("Enter method name")
    return states["method_name"]


def state_method_emoji(message: Message):
    message.edit_text("Enter method emoji")
    return states["method_emoji"]


def state_method_owner(message: Message):
    message.edit_text("Select method owner", reply_markup=keyboard_users())
    return states["method_owner"]


def state_categories(message: Message):
    message.edit_text("List of categories", reply_markup=keyboard_categories())
    return states["categories"]


def state_currencies(message: Message):
    message.edit_text("List of currencies", reply_markup=keyboard_currencies())
    return states["currencies"]


def state_tasks(message: Message):
    message.edit_text("Task manager", reply_markup=keyboard_tasks())
    return states["tasks"]


def state_tasks_current(message: Message):
    message.edit_text(
        "List of current tasks",
        reply_markup=keyboard_tasks_current(
            authorized_data[message.chat.id]["page_tasks_current"]
        ),
    )
    return states["tasks_current"]


def state_task_current(message: Message):
    message.edit_text(
        "Task: "
        + display_text_task_current(
            authorized_data[message.chat.id]["task_current"], True
        ),
        reply_markup=keyboard_task_current(
            data=authorized_data[message.chat.id]["task_current"]
        ),
    )
    return states["task_current"]


def state_task_current_reply(message: Message):
    message.reply_text(
        "Task: "
        + display_text_task_current(
            authorized_data[message.chat.id]["task_current"], True
        ),
        reply_markup=keyboard_task_current(
            data=authorized_data[message.chat.id]["task_current"]
        ),
    )
    return states["task_current"]


def state_task_current_name(message: Message):
    message.edit_text("Enter current task name")
    return states["task_current_name"]


def state_tasks_scheduled(message: Message):
    message.edit_text("List of scheduled task", reply_markup=keyboard_tasks_scheduled())
    return states["tasks_scheduled"]


def state_task_scheduled(message: Message):
    message.edit_text(
        "Scheduled task: "
        + display_text_task_scheduled(
            authorized_data[message.chat.id]["task_scheduled"]
        ),
        reply_markup=keyboard_task_scheduled(),
    )
    return states["task_scheduled"]


def state_plants(message: Message):
    message.edit_text("List of plants", reply_markup=keyboard_plants())
    return states["plants"]


def state_users(message: Message):
    message.edit_text("List of users", reply_markup=keyboard_users())
    return states["users"]


def state_wip(message: Message):
    message.edit_text("🏗️ This section is not ready", reply_markup=keyboard_with_back())
    return states["wip"]


# handlers


def handle_main(update: Update, context: CallbackContext):
    if update.callback_query.data == "transaction_add_fast_type":
        return state_transaction_add_fast_type(update.callback_query.message)
    elif update.callback_query.data == "task_current":
        if (
            "_NEW"
            not in authorized_data[update.callback_query.message.chat.id][
                "task_current"
            ]
        ):
            authorized_data[update.callback_query.message.chat.id]["task_current"] = {}
        authorized_data[update.callback_query.message.chat.id]["task_current"][
            "_NEW"
        ] = True
        authorized_data[update.callback_query.message.chat.id][
            "last_state"
        ] = state_main
        return state_task_current(update.callback_query.message)
    elif update.callback_query.data == "finances":
        return state_finances(update.callback_query.message)
    elif update.callback_query.data == "tasks":
        return state_tasks(update.callback_query.message)
    elif update.callback_query.data == "plants":
        return state_plants(update.callback_query.message)
    elif update.callback_query.data == "users":
        return state_users(update.callback_query.message)
    else:
        return state_wip(update.callback_query.message)


def handle_finances(update: Update, context: CallbackContext):
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
    elif update.callback_query.data == "currencies":
        return state_currencies(update.callback_query.message)
    else:
        return state_main(update.callback_query.message)


def handle_transactions(update: Update, context: CallbackContext):
    context.bot.answer_callback_query(callback_query_id=update.callback_query.id)
    if update.callback_query.data == handler_data_add:
        return state_transaction(update.callback_query.message)
    elif update.callback_query.data != handler_data_back:
        pass

    return state_finances(update.callback_query.message)


def handle_transaction_add_fast_type(update: Update, context: CallbackContext):
    context.bot.answer_callback_query(callback_query_id=update.callback_query.id)
    if update.callback_query.data != handler_data_back:
        authorized_data[update.callback_query.message.chat.id]["transaction"][
            "type"
        ] = update.callback_query.data
        return state_transaction_add_fast_sum(update.callback_query.message)
    else:
        return state_transactions(update.callback_query.message)


def handle_transaction_add_fast_sum(update: Update, context: CallbackContext):
    data = gsh.get_cached_data(["merchants", "currencies"])

    splitted = update.message.text.split(", ")

    sum_data = None
    merchant = None
    description = []

    for splitted_text in splitted:
        if not sum_data:
            sum_data = parse_sum_text(splitted_text)
        else:
            add_description = True
            if not merchant:
                merchant_ids = difflib.get_close_matches(
                    splitted_text, data["merchants"]["keywords"]["list"]
                )
                if len(merchant_ids) > 0:
                    merchant = (
                        merchant_ids[0] in data["merchants"]["keywords"]["dict"]
                        and data["merchants"]["keywords"]["dict"][merchant_ids[0]]
                    )
                    add_description = False

            if add_description:
                description.append(splitted_text)

    if sum_data:
        authorized_data[update.message.chat.id]["transaction"]["sum"] = sum_data["sum"]
        authorized_data[update.message.chat.id]["transaction"]["currency"] = sum_data[
            "currency"
        ]
    if len(description) > 0:
        authorized_data[update.message.chat.id]["transaction"][
            "description"
        ] = ", ".join(description)
    if merchant:
        authorized_data[update.message.chat.id]["transaction"]["merchant"] = merchant

    update.message.reply_text(
        display_text_add_transaction(
            authorized_data[update.message.chat.id]["transaction"]
        )
        + ". How?",
        reply_markup=keyboard_methods(),
    )

    return states["transaction_add_fast_method"]


def handle_transaction_add_fast_method(update: Update, context: CallbackContext):
    context.bot.answer_callback_query(callback_query_id=update.callback_query.id)
    if update.callback_query.data == handler_data_add:
        authorized_data[update.callback_query.message.chat.id]["method"]["_NEW"] = True
        authorized_data[update.callback_query.message.chat.id][
            "last_state"
        ] = state_transaction
        return state_method(update.callback_query.message)
    else:
        authorized_data[update.callback_query.message.chat.id]["transaction"][
            "method"
        ] = update.callback_query.data

        target = get_transaction_target_type(
            authorized_data[update.callback_query.message.chat.id]["transaction"]
        )

        if (
            authorized_data[update.callback_query.message.chat.id]["transaction"][
                "type"
            ]
            == "CORRECTION"
        ):
            return state_transaction(update.callback_query.message)
        elif (
            target
            not in authorized_data[update.callback_query.message.chat.id]["transaction"]
            or not authorized_data[update.callback_query.message.chat.id][
                "transaction"
            ][target]
        ):
            return state_transaction_add_fast_target(update.callback_query.message)
        else:
            return state_transaction(update.callback_query.message)


def handle_transaction_add_fast_merchant(update: Update, context: CallbackContext):
    context.bot.answer_callback_query(callback_query_id=update.callback_query.id)
    if update.callback_query.data == handler_data_add:
        authorized_data[update.callback_query.message.chat.id]["merchant"][
            "_NEW"
        ] = True
        authorized_data[update.callback_query.message.chat.id]["merchant"][
            "category"
        ] = authorized_data[update.callback_query.message.chat.id]["merchant_category"]
        authorized_data[update.callback_query.message.chat.id][
            "last_state"
        ] = state_transaction
        return state_merchant(update.callback_query.message)
    else:
        target_type = get_transaction_target_type(
            authorized_data[update.callback_query.message.chat.id]["transaction"]
        )
        if (
            target_type == "merchant"
            and not authorized_data[update.callback_query.message.chat.id][
                "merchant_category"
            ]
        ):
            authorized_data[update.callback_query.message.chat.id][
                "merchant_category"
            ] = update.callback_query.data
            return state_transaction_add_fast_target(update.callback_query.message)
        elif (
            update.callback_query.data == handler_data_back
            and target_type == "merchant"
            and authorized_data[update.callback_query.message.chat.id][
                "merchant_category"
            ]
        ):
            authorized_data[update.callback_query.message.chat.id][
                "merchant_category"
            ] = ""
            return state_transaction_add_fast_target(update.callback_query.message)
        else:
            authorized_data[update.callback_query.message.chat.id][
                "merchant_category"
            ] = ""
            authorized_data[update.callback_query.message.chat.id]["transaction"][
                target_type
            ] = update.callback_query.data
            return state_transaction(update.callback_query.message)


def handle_transaction(update: Update, context: CallbackContext):
    context.bot.answer_callback_query(callback_query_id=update.callback_query.id)
    if update.callback_query.data != handler_data_back:
        if update.callback_query.data == handler_data_submit:
            return transaction_submit(update.callback_query.message)
        elif update.callback_query.data == "type":
            return state_transaction_type(update.callback_query.message)
        elif update.callback_query.data == "date":
            return state_transaction_date(update.callback_query.message)
        elif update.callback_query.data == "sum":
            return state_transaction_sum(update.callback_query.message)
        elif update.callback_query.data == "currency":
            return state_transaction_currency(update.callback_query.message)
        elif update.callback_query.data == "method":
            return state_transaction_method(update.callback_query.message)
        elif update.callback_query.data == "target":
            return state_transaction_target(update.callback_query.message)
        elif update.callback_query.data == "description":
            return state_transaction_description(update.callback_query.message)
        elif update.callback_query.data == "description_remove":
            authorized_data[update.callback_query.message.chat.id]["transaction"][
                "description"
            ] = None
            return state_transaction(update.callback_query.message)

    return state_transactions(update.callback_query.message)


def handle_transaction_type(update: Update, context: CallbackContext):
    context.bot.answer_callback_query(callback_query_id=update.callback_query.id)
    if update.callback_query.data != handler_data_back:
        authorized_data[update.callback_query.message.chat.id]["transaction"][
            "type"
        ] = update.callback_query.data
    return state_transaction(update.callback_query.message)


def handle_transaction_date(update: Update, context: CallbackContext):
    context.bot.answer_callback_query(callback_query_id=update.callback_query.id)
    if update.callback_query.data == "_DATE_TODAY":
        authorized_data[update.callback_query.message.chat.id]["date_offset"] = 0
        return state_transaction_date(update.callback_query.message)
    elif update.callback_query.data == "_DATE_REWIND_BACKWARD":
        authorized_data[update.callback_query.message.chat.id]["date_offset"] += 4
        return state_transaction_date(update.callback_query.message)
    elif update.callback_query.data == "_DATE_BACKWARD":
        authorized_data[update.callback_query.message.chat.id]["date_offset"] += 1
        return state_transaction_date(update.callback_query.message)
    elif update.callback_query.data == "_DATE_FORWARD":
        authorized_data[update.callback_query.message.chat.id]["date_offset"] -= 1
        if authorized_data[update.callback_query.message.chat.id]["date_offset"] < 0:
            authorized_data[update.callback_query.message.chat.id]["date_offset"] = 0
        return state_transaction_date(update.callback_query.message)
    elif update.callback_query.data == "_DATE_REWIND_FORWARD":
        authorized_data[update.callback_query.message.chat.id]["date_offset"] -= 4
        if authorized_data[update.callback_query.message.chat.id]["date_offset"] < 0:
            authorized_data[update.callback_query.message.chat.id]["date_offset"] = 0
        return state_transaction_date(update.callback_query.message)

    else:
        try:
            authorized_data[update.callback_query.message.chat.id]["transaction"][
                "date"
            ] = datetime.datetime.strptime(update.callback_query.data, "%Y_%m_%d")
        finally:
            return state_transaction(update.callback_query.message)


def handle_transaction_date_text(update: Update, context: CallbackContext):
    try:
        authorized_data[update.message.chat.id]["transaction"][
            "date"
        ] = datetime.datetime.strptime(update.message.text, "%Y-%m-%d")
    finally:
        return state_transaction_reply(update.message)


def handle_transaction_sum(update: Update, context: CallbackContext):
    try:
        sum_data = parse_sum_text(update.message.text)

        if sum_data:
            authorized_data[update.message.chat.id]["transaction"]["sum"] = sum_data[
                "sum"
            ]
            authorized_data[update.message.chat.id]["transaction"][
                "currency"
            ] = sum_data["currency"]
    finally:
        return state_transaction_reply(update.message)


def handle_transaction_currency(update: Update, context: CallbackContext):
    context.bot.answer_callback_query(callback_query_id=update.callback_query.id)
    if update.callback_query.data != handler_data_back:
        authorized_data[update.callback_query.message.chat.id]["transaction"][
            "currency"
        ] = update.callback_query.data
    return state_transaction(update.callback_query.message)


def handle_transaction_method(update: Update, context: CallbackContext):
    context.bot.answer_callback_query(callback_query_id=update.callback_query.id)
    if update.callback_query.data == handler_data_add:
        authorized_data[update.callback_query.message.chat.id]["method"]["_NEW"] = True
        authorized_data[update.callback_query.message.chat.id][
            "last_state"
        ] = state_transaction
        return state_method(update.callback_query.message)
    elif update.callback_query.data != handler_data_back:
        authorized_data[update.callback_query.message.chat.id]["transaction"][
            "method"
        ] = update.callback_query.data
    return state_transaction(update.callback_query.message)


def handle_transaction_target(update: Update, context: CallbackContext):
    context.bot.answer_callback_query(callback_query_id=update.callback_query.id)
    target_type = get_transaction_target_type(
        authorized_data[update.callback_query.message.chat.id]["transaction"]
    )

    if update.callback_query.data == handler_data_add:
        if target_type == "target_method":
            authorized_data[update.callback_query.message.chat.id]["method"][
                "_NEW"
            ] = True
            authorized_data[update.callback_query.message.chat.id]["merchant"][
                "category"
            ] = authorized_data[update.callback_query.message.chat.id][
                "merchant_category"
            ]
            authorized_data[update.callback_query.message.chat.id][
                "last_state"
            ] = state_transaction
            return state_method(update.callback_query.message)
        else:
            authorized_data[update.callback_query.message.chat.id]["merchant"][
                "_NEW"
            ] = True
            authorized_data[update.callback_query.message.chat.id][
                "last_state"
            ] = state_transaction
            return state_merchant(update.callback_query.message)
    elif update.callback_query.data != handler_data_back:
        if (
            target_type == "merchant"
            and not authorized_data[update.callback_query.message.chat.id][
                "merchant_category"
            ]
        ):
            authorized_data[update.callback_query.message.chat.id][
                "merchant_category"
            ] = update.callback_query.data
            return state_transaction_target(update.callback_query.message)
        authorized_data[update.callback_query.message.chat.id]["transaction"][
            target_type
        ] = update.callback_query.data
    elif (
        update.callback_query.data == handler_data_back
        and target_type == "merchant"
        and authorized_data[update.callback_query.message.chat.id]["merchant_category"]
    ):
        authorized_data[update.callback_query.message.chat.id]["merchant_category"] = ""
        return state_transaction_target(update.callback_query.message)
    return state_transaction(update.callback_query.message)


def handle_transaction_description(update: Update, context: CallbackContext):
    authorized_data[update.message.chat.id]["transaction"][
        "description"
    ] = update.message.text
    return state_transaction_reply(update.message)


def handle_merchants(update: Update, context: CallbackContext):
    context.bot.answer_callback_query(callback_query_id=update.callback_query.id)
    if update.callback_query.data == handler_data_add:
        authorized_data[update.callback_query.message.chat.id]["merchant"][
            "_NEW"
        ] = True
        authorized_data[update.callback_query.message.chat.id][
            "last_state"
        ] = state_transaction
        return state_merchant(update.callback_query.message)
    elif update.callback_query.data != handler_data_back:
        data = gsh.get_cached_data(["merchants"])
        send_info_message(
            update.callback_query.from_user.first_name
            + " has selected "
            + data["merchants"]["dict"][update.callback_query.data]["name"]
            + " and everyone should be aware of it"
        )

    return state_finances(update.callback_query.message)


def handle_merchant(update: Update, context: CallbackContext):
    context.bot.answer_callback_query(callback_query_id=update.callback_query.id)
    if update.callback_query.data != handler_data_back:
        if update.callback_query.data == handler_data_submit:
            return merchant_submit(update.callback_query.message)
        elif update.callback_query.data == "name":
            return state_merchant_name(update.callback_query.message)
        elif update.callback_query.data == "emoji":
            return state_merchant_emoji(update.callback_query.message)
        elif update.callback_query.data == "category":
            return state_merchant_category(update.callback_query.message)

    return state_merchants(update.callback_query.message)


def handle_merchant_name(update: Update, context: CallbackContext):
    authorized_data[update.message.chat.id]["merchant"]["name"] = update.message.text
    if (
        "_NEW" in authorized_data[update.message.chat.id]["merchant"]
        or "id" not in authorized_data[update.message.chat.id]["merchant"]
    ):
        authorized_data[update.message.chat.id]["merchant"][
            "id"
        ] = id_utils.generate_id(
            gsh.get_cached_data(["merchants"])["merchants"]["dict"], update.message.text
        )

    return state_merchant_reply(update.message)


def handle_merchant_keywords(update: Update, context: CallbackContext):
    return state_merchant_reply(update.message)


def handle_merchant_category(update: Update, context: CallbackContext):
    context.bot.answer_callback_query(callback_query_id=update.callback_query.id)
    if update.callback_query.data != handler_data_back:
        authorized_data[update.callback_query.message.chat.id]["merchant"][
            "category"
        ] = update.callback_query.data

    return state_merchant(update.callback_query.message)


def handle_merchant_emoji(update: Update, context: CallbackContext):
    authorized_data[update.message.chat.id]["merchant"]["emoji"] = update.message.text
    return state_merchant_reply(update.message)


def handle_methods(update: Update, context: CallbackContext):
    context.bot.answer_callback_query(callback_query_id=update.callback_query.id)
    if update.callback_query.data == handler_data_add:
        authorized_data[update.callback_query.message.chat.id]["method"]["_NEW"] = True
        return state_method(update.callback_query.message)
    elif update.callback_query.data != handler_data_back:
        data = gsh.get_cached_data(["methods"])
        send_info_message(
            update.callback_query.from_user.first_name
            + " has selected "
            + data["methods"]["dict"][update.callback_query.data]["name"]
            + " and everyone should be aware of it"
        )

    return state_finances(update.callback_query.message)


def handle_method(update: Update, context: CallbackContext):
    context.bot.answer_callback_query(callback_query_id=update.callback_query.id)
    if update.callback_query.data != handler_data_back:
        method = authorized_data[update.callback_query.message.chat.id]["method"]

        if update.callback_query.data == handler_data_submit:
            return method_submit(update.callback_query.message)
        elif update.callback_query.data == "name":
            return state_method_name(update.callback_query.message)
        elif update.callback_query.data == "emoji":
            return state_method_emoji(update.callback_query.message)
        elif update.callback_query.data == "owner":
            return state_method_owner(update.callback_query.message)
        elif update.callback_query.data == "is_account":
            if "is_account" not in method:
                method["is_account"] = False
            method["is_account"] = not method["is_account"]
            if method["is_account"]:
                method["is_mir"] = False
                method["is_credit"] = False
                method["is_cashback"] = False
            return state_method(update.callback_query.message)
        elif update.callback_query.data == "is_mir":
            if "is_mir" not in method:
                method["is_mir"] = False
            method["is_mir"] = not method["is_mir"]
            if method["is_mir"]:
                method["is_account"] = False
            return state_method(update.callback_query.message)
        elif update.callback_query.data == "is_credit":
            if "is_credit" not in method:
                method["is_credit"] = False
            method["is_credit"] = not method["is_credit"]
            if method["is_credit"]:
                method["is_account"] = False
            return state_method(update.callback_query.message)
        elif update.callback_query.data == "is_cashback":
            if "is_cashback" not in method:
                method["is_cashback"] = False
            method["is_cashback"] = not method["is_cashback"]
            if method["is_cashback"]:
                method["is_account"] = False
            return state_method(update.callback_query.message)

    return state_methods(update.callback_query.message)


def handle_method_name(update: Update, context: CallbackContext):
    authorized_data[update.message.chat.id]["method"]["name"] = update.message.text
    if (
        "_NEW" in authorized_data[update.message.chat.id]["method"]
        or "id" not in authorized_data[update.message.chat.id]["method"]
    ):
        authorized_data[update.message.chat.id]["method"]["id"] = id_utils.generate_id(
            gsh.get_cached_data(["methods"])["methods"]["dict"], update.message.text
        )
    return state_method_reply(update.message)


def handle_method_emoji(update: Update, context: CallbackContext):
    authorized_data[update.message.chat.id]["method"]["emoji"] = update.message.text
    return state_method_reply(update.message)


def handle_method_is_account(update: Update, context: CallbackContext):
    context.bot.answer_callback_query(callback_query_id=update.callback_query.id)
    return state_method(update.callback_query.message)


def handle_method_is_mir(update: Update, context: CallbackContext):
    context.bot.answer_callback_query(callback_query_id=update.callback_query.id)
    return state_method(update.callback_query.message)


def handle_method_is_credit(update: Update, context: CallbackContext):
    context.bot.answer_callback_query(callback_query_id=update.callback_query.id)
    return state_method(update.callback_query.message)


def handle_method_is_cashback(update: Update, context: CallbackContext):
    context.bot.answer_callback_query(callback_query_id=update.callback_query.id)
    return state_method(update.callback_query.message)


def handle_method_owner(update: Update, context: CallbackContext):
    context.bot.answer_callback_query(callback_query_id=update.callback_query.id)
    if update.callback_query.data != handler_data_back:
        authorized_data[update.callback_query.message.chat.id]["method"][
            "owner"
        ] = update.callback_query.data

    return state_method(update.callback_query.message)


def handle_categories(update: Update, context: CallbackContext):
    context.bot.answer_callback_query(callback_query_id=update.callback_query.id)
    if update.callback_query.data == handler_data_add:
        pass
    elif update.callback_query.data != handler_data_back:
        data = gsh.get_cached_data(["categories"])
        send_info_message(
            update.callback_query.from_user.first_name
            + " has selected "
            + data["categories"]["dict"][update.callback_query.data]["emoji"]
            + " "
            + data["categories"]["dict"][update.callback_query.data]["name"]
            + " and everyone should be aware of it"
        )

    return state_finances(update.callback_query.message)


def handle_currencies(update: Update, context: CallbackContext):
    return state_finances(update.callback_query.message)


def handle_tasks(update: Update, context: CallbackContext):
    if update.callback_query.data != handler_data_back:
        if update.callback_query.data == "tasks_current":
            return state_tasks_current(update.callback_query.message)
        elif update.callback_query.data == "task_current":
            if (
                "_NEW"
                not in authorized_data[update.callback_query.message.chat.id][
                    "task_current"
                ]
            ):
                authorized_data[update.callback_query.message.chat.id][
                    "task_current"
                ] = {}
            authorized_data[update.callback_query.message.chat.id]["task_current"][
                "_NEW"
            ] = True
            authorized_data[update.callback_query.message.chat.id][
                "last_state"
            ] = state_tasks
            return state_task_current(update.callback_query.message)
        elif update.callback_query.data == "tasks_scheduled":
            return state_tasks_scheduled(update.callback_query.message)
        elif update.callback_query.data == "task_scheduled":
            return state_task_scheduled(update.callback_query.message)
    return state_main(update.callback_query.message)


def handle_tasks_current(update: Update, context: CallbackContext):
    if update.callback_query.data != handler_data_back:
        user_data = authorized_data[update.callback_query.message.chat.id]
        page_tasks_current = user_data["page_tasks_current"]
        if update.callback_query.data == handler_data_add:
            if "_NEW" not in user_data["task_current"]:
                user_data["task_current"] = {}
            user_data["task_current"]["_NEW"] = True
            user_data["last_state"] = state_tasks_current
            return state_task_current(update.callback_query.message)
        if update.callback_query.data == "_PAGE_START":
            if page_tasks_current["page"] != 1:
                page_tasks_current["page"] = 1
                return state_tasks_current(update.callback_query.message)
            else:
                return states["tasks_current"]
        elif update.callback_query.data == "_PAGE_BACK":
            old_page = page_tasks_current["page"]
            page_tasks_current["page"] = max(
                page_tasks_current["page"] - 1,
                1,
            )
            if old_page != page_tasks_current["page"]:
                return state_tasks_current(update.callback_query.message)
            else:
                return states["tasks_current"]
        elif update.callback_query.data == "_PAGE_FORWARD":
            old_page = page_tasks_current["page"]
            page_tasks_current["page"] = min(
                page_tasks_current["page"] + 1, page_tasks_current["data"]["pages"]
            )
            if old_page != page_tasks_current["page"]:
                return state_tasks_current(update.callback_query.message)
            else:
                return states["tasks_current"]
        elif update.callback_query.data == "_PAGE_END":
            if page_tasks_current["page"] != page_tasks_current["data"]["pages"]:
                page_tasks_current["page"] = page_tasks_current["data"]["pages"]
                return state_tasks_current(update.callback_query.message)
            else:
                return states["tasks_current"]
        else:
            data = gsh.get_cached_data(["tasks_current"])
            user_data["task_current"] = dict(
                data["tasks_current"]["dict"][update.callback_query.data]
            )
            return state_task_current(update.callback_query.message)
    return state_tasks(update.callback_query.message)


def handle_task_current(update: Update, context: CallbackContext):
    if update.callback_query.data != handler_data_back:
        if update.callback_query.data == handler_data_submit:
            return task_current_submit(update.callback_query.message)
        elif (
            update.callback_query.data == "_TASK_DONE"
            or update.callback_query.data == "_TASK_IGNORE"
        ):
            data = gsh.get_cached_data(["tasks_current", "tasks_scheduled"])
            task_current = authorized_data[update.callback_query.message.chat.id][
                "task_current"
            ]
            cell: gsh.gspread.Cell = gsh.sheets["tasks_current"].find(
                task_current["id"],
                in_column=1,
            )
            row = cell.row
            gsh.sheets["tasks_current"].update_cell(
                row,
                8,
                update.callback_query.data == "_TASK_DONE"
                and date_utils.get_today_text()
                or "IGNORED",
            )

            if task_current["scheduled_id"]:
                cell_scheduled: gsh.gspread.Cell = gsh.sheets["tasks_scheduled"].find(
                    task_current["scheduled_id"],
                    in_column=1,
                )
                row_scheduled = cell_scheduled.row
                if update.callback_query.data == "_TASK_DONE":
                    gsh.sheets["tasks_scheduled"].update_cell(
                        row_scheduled,
                        11,
                        data["tasks_scheduled"]["dict"][task_current["scheduled_id"]][
                            "times_done"
                        ]
                        + 1,
                    )
                gsh.sheets["tasks_scheduled"].update_cell(row_scheduled, 12, False)

            send_info_message(
                update.callback_query.from_user.first_name
                + " has "
                + (update.callback_query.data == "_TASK_DONE" and "done" or "ignored")
                + " task "
                + display_text_task_current(task_current, True)
            )

            gsh.get_cached_data(["tasks_current", "tasks_scheduled"], update=True)
        elif update.callback_query.data == "name":
            return state_task_current_name(update.callback_query.message)
    return state_tasks_current(update.callback_query.message)


def handle_task_current_name(update: Update, context: CallbackContext):
    authorized_data[update.message.chat.id]["task_current"][
        "name"
    ] = update.message.text
    if (
        "_NEW" in authorized_data[update.message.chat.id]["task_current"]
        or "id" not in authorized_data[update.message.chat.id]["task_current"]
    ):
        authorized_data[update.message.chat.id]["task_current"][
            "id"
        ] = id_utils.generate_id(
            gsh.get_cached_data(["tasks_current"])["tasks_current"]["dict"],
            update.message.text,
        )

    return state_task_current_reply(update.message)


def handle_tasks_scheduled(update: Update, context: CallbackContext):
    if update.callback_query.data != handler_data_back:
        data = gsh.get_cached_data(["tasks_scheduled"])
        authorized_data[update.callback_query.message.chat.id]["task_scheduled"] = dict(
            data["tasks_scheduled"]["dict"][update.callback_query.data]
        )
        return state_task_scheduled(update.callback_query.message)
    return state_tasks(update.callback_query.message)


def handle_task_scheduled(update: Update, context: CallbackContext):
    return state_tasks_scheduled(update.callback_query.message)


def handle_plants(update: Update, context: CallbackContext):
    return state_main(update.callback_query.message)


def handle_users(update: Update, context: CallbackContext):
    context.bot.answer_callback_query(callback_query_id=update.callback_query.id)
    return state_main(update.callback_query.message)


def handle_wip(update: Update, context: CallbackContext):
    context.bot.answer_callback_query(callback_query_id=update.callback_query.id)
    return state_main(update.callback_query.message)


# context.bot.delete_message(update.message.chat_id, str(update.message.message_id))

# fallbacks


def fallback(update: Update, context: CallbackContext):
    # print(print_label, "fallback", update)
    update.message.reply_text(error_text)


def fallback_callback_query_handler(update: Update, context: CallbackContext):
    # print(print_label, "fallback_callback_query_handler", update)
    update.callback_query.message.reply_text(error_text)


# other


def empty_user():
    return {
        "last_state": state_main,
        "transaction": {},
        "merchant": {},
        "method": {},
        "task_current": {},
        "task_scheduled": {},
        "page_tasks_current": {"page": 1},
        "date_offset": 0,
        "merchant_category": "",
    }


# init

print(print_label, "Loading configs...")
general_config = yaml_manager.load("config/local/general")
telegram_config = yaml_manager.load("config/local/telegram")


init()
