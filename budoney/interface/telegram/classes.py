from collections import deque
from typing import Any
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Message, Update
from telegram.ext import CallbackContext, CallbackQueryHandler, MessageHandler, Filters
from loc import localization
from database import DATABASE_DRIVER
import utils.date_utils as date_utils
from datetime import datetime, timedelta
import configs
import math

print_label: str = "[budoney :: Telegram Interface]"


def text_filters():
    return Filters.text & auth_filter() & conversation_filter()


def auth_filter():
    return Filters.user(user_id=configs.telegram["authorized"])


def conversation_filter():
    return Filters.chat(chat_id=configs.telegram["authorized"])


def check_record_params(state, telegram_user):
    if state.table_name not in telegram_user.records:
        telegram_user.records[state.table_name] = {}
    if state.table_name not in telegram_user.ignore_fast:
        telegram_user.ignore_fast[state.table_name] = {}
    for column in conversation_views[state.table_name].columns:
        if column["column"] not in telegram_user.records[state.table_name] and (
            column["column"] not in telegram_user.ignore_fast[state.table_name]
            or not telegram_user.ignore_fast[state.table_name][column["column"]]
        ):
            print(f"{column['column']} is not typed")
            return conversation_views[f"{state.table_name}_PARAM_{column['column']}"]
    print(f"everything is typed but {telegram_user.ignore_fast[state.table_name]}")
    return state


# records outer functions to reuse them


def _records_state_text(table_name, telegram_user):
    pagination = telegram_user.get_pagination(table_name)

    pagination.total = DATABASE_DRIVER.get_records_count(table_name)
    pagination.pages = math.ceil(pagination.total / pagination.limit)
    text = (
        pagination.total > 0
        and (
            pagination.total == 1
            and (f"Displaying <b>1</b> record")
            or (
                pagination.total > pagination.limit
                and (
                    f"Displaying <b>{pagination.offset+1}-{min(pagination.offset+pagination.limit, pagination.total)}</b> of <b>{pagination.total}</b> records"
                )
                or (f"Displaying <b>{pagination.total}</b> records")
            )
        )
        or "No records found"
    )
    return text


def link_tables(linked_tables, table_name, alias=None, record=None):
    for column in conversation_views[table_name].columns:
        if column["type"] == "data" and (not record or (column["column"] in record)):
            prefix = alias
            old_prefix = alias or table_name
            if not prefix:
                prefix = column["column"]
            else:
                prefix += "__" + column["column"]
            linked_tables.append(
                {
                    "name": column["data_type"],
                    "linkedBy": column["column"],
                    "alias": prefix,
                    "parent": old_prefix,
                }
            )
            linked_tables = link_tables(
                linked_tables, column["data_type"], alias=prefix
            )

    return linked_tables


def _get_records(
    table_name=None, pagination=None, external=None, record_id=None, one=None
):
    join_select = []

    linked_tables = link_tables([], table_name, record=external)

    print("_get_records", "linked_tables", linked_tables)

    for linked_table in linked_tables:
        for column in conversation_views[linked_table["name"]].columns:
            join_select.append(
                {"table": linked_table["alias"], "column": column["column"]}
            )

    print("_get_records", "join_select", join_select)

    result = DATABASE_DRIVER.get_records(
        table=table_name,
        external=external,
        join=linked_tables,
        join_select=join_select,
        offset=pagination and pagination.offset,
        limit=pagination and pagination.limit,
        record_id=record_id,
    )

    return one and (result and result[0] or {"_EMPTY": True}) or result


def _records_keyboard(table_name, keyboard, message: Message):
    pagination = telegram_users[message.chat.id].get_pagination(table_name)

    records = _get_records(table_name=table_name, pagination=pagination)
    for index, record in enumerate(records):
        keyboard.append(
            [
                InlineKeyboardButton(
                    callback_data=record["id"],
                    text=conversation_views[table_name].display_func
                    and conversation_views[table_name].display_func(record)
                    or str(record["id"]),
                )
            ]
        )

    if pagination.pages > 1:
        keyboard.append(
            [
                InlineKeyboardButton(
                    (pagination.offset > 0) and "⏪" or "🚫",
                    callback_data="_PAGE_REWIND",
                ),
                InlineKeyboardButton(
                    (pagination.offset > 0) and "◀️" or "🚫",
                    callback_data="_PAGE_BACKWARD",
                ),
                InlineKeyboardButton(
                    (pagination.offset < pagination.total - pagination.limit)
                    and "▶️"
                    or "🚫",
                    callback_data="_PAGE_FORWARD",
                ),
                InlineKeyboardButton(
                    (pagination.offset < pagination.total - pagination.limit)
                    and "⏩"
                    or "🚫",
                    callback_data="_PAGE_FASTFORWARD",
                ),
            ]
        )
    return keyboard


def _records_handle_pagination(table_name, update: Update, data):
    pagination = telegram_users[update.callback_query.message.chat.id].get_pagination(
        table_name
    )

    options_changed = False

    if data == "_PAGE_REWIND":
        if pagination.offset > 0:
            options_changed = True
            pagination.offset = 0
    elif data == "_PAGE_BACKWARD":
        if pagination.offset > 0:
            options_changed = True
            pagination.offset = max(pagination.offset - pagination.limit, 0)
    elif data == "_PAGE_FORWARD":
        if pagination.offset < pagination.total - pagination.limit:
            options_changed = True
            pagination.offset = min(
                pagination.offset + pagination.limit,
                pagination.total,
                pagination.total - pagination.limit,
            )
    elif data == "_PAGE_FASTFORWARD":
        if pagination.offset < pagination.total - pagination.limit:
            options_changed = True
            pagination.offset = pagination.total - pagination.limit

    return options_changed


def _records_handle_add(table_name, update: Update):
    return check_record_params(
        conversation_views[f"{table_name}_ADD"],
        telegram_users[update.callback_query.message.chat.id],
    )


class Pagination:
    def __init__(self) -> None:
        self.offset: int = 0
        self.limit: int = 5
        self.total: int = 0
        self.pages: int = 0


class TelegramUser:
    def __init__(self, name: str) -> None:
        self.name: str = name
        self.state: str = "none"
        self.states_sequence: deque = deque()
        self.operational_sequence: deque[deque] = deque()
        self.operational_sequence.append(deque())
        self.records: dict = dict()
        self.ignore_fast: dict[str, dict[str, bool]] = dict()
        self.pagination: dict[str, Pagination] = dict()
        self.date_offset: int = 0

    def get_pagination(self, table_name):
        if table_name not in self.pagination:
            self.pagination[table_name] = Pagination()
        return self.pagination[table_name]


class TelegramConversationView:
    def __init__(self, state_name: str) -> None:
        conversation_views[state_name] = self
        self.state_name = state_name
        self.skip_to_records = False
        self.handle_anything = False
        self.handlers = [
            CallbackQueryHandler(self._handle),
            MessageHandler(text_filters(), self._handle_typed),
        ]

    def state(self, message: Message, text: str, edit: bool):
        print(
            print_label,
            f"{message.chat.first_name} ({message.chat.id}) has moved from '{telegram_users[message.chat.id].state}' to '{self.state_name}'",
        )
        telegram_users[message.chat.id].state = self.state_name

        result_text = self.debug_text(telegram_users[message.chat.id]) or ""

        if text:
            result_text = result_text + text + "\n\n"

        result_text = result_text + f"<b>{self.state_name_text()}</b>"

        state_text = self.state_text(telegram_users[message.chat.id])
        if state_text:
            result_text = result_text + "\n\n" + state_text

        if edit:
            try:
                message.edit_text(
                    result_text, reply_markup=self.keyboard(message), parse_mode="html"
                )
            except:
                message.reply_text(
                    result_text, reply_markup=self.keyboard(message), parse_mode="html"
                )
        else:
            message.reply_text(
                result_text, reply_markup=self.keyboard(message), parse_mode="html"
            )
        return self.state_name

    def state_name_text(self):
        return localization["states"].get(self.state_name, self.state_name)

    def state_name_text_short(self):
        return self.state_name_text()

    def debug_text(self, user: TelegramUser):
        if configs.general["production_mode"]:
            return ""

        text = f"👩‍💻 Debug for {user.name}:\n"

        text = text + f"- states_sequence: <code>{str(user.states_sequence)}</code>\n"
        text = (
            text
            + f"- operational_sequence: <code>{str(user.operational_sequence)}</code>\n"
        )
        text = text + f"- state: <code>{str(user.state)}</code>\n"
        text = text + f"- records: <code>{str(user.records)}</code>\n"

        return text + "\n"

    def state_text(self, telegram_user):
        return ""

    def keyboard(self, message: Message) -> InlineKeyboardMarkup:
        pass

    def handle(self, update: Update, data):
        print(
            print_label,
            f"{update.callback_query.message.chat.first_name} ({update.callback_query.message.chat.id}) state {self.state_name} doesn't have handle",
        )

    def handle_records(self, update: Update):
        print(
            print_label,
            f"{update.callback_query.message.chat.first_name} ({update.callback_query.message.chat.id}) state {self.state_name} doesn't have handle_records",
        )

    def handle_pagination(self, update: Update):
        print(
            print_label,
            f"{update.callback_query.message.chat.first_name} ({update.callback_query.message.chat.id}) state {self.state_name} doesn't have handle_pagination",
        )

    def handle_date(self, update: Update):
        print(
            print_label,
            f"{update.callback_query.message.chat.first_name} ({update.callback_query.message.chat.id}) state {self.state_name} doesn't have handle_date",
        )

    def handle_add(self, update: Update):
        print(
            print_label,
            f"{update.callback_query.message.chat.first_name} ({update.callback_query.message.chat.id}) state {self.state_name} doesn't have handle_add",
        )

    def handle_next(self, update: Update):
        print(
            print_label,
            f"{update.callback_query.message.chat.first_name} ({update.callback_query.message.chat.id}) state {self.state_name} doesn't have handle_next",
        )

    def handle_skip(self, update: Update):
        print(
            print_label,
            f"{update.callback_query.message.chat.first_name} ({update.callback_query.message.chat.id}) state {self.state_name} doesn't have handle_skip",
        )

    def handle_cancel(self, update: Update):
        pass

    def _handle_cancel(self, update: Update, state):
        self.handle_cancel(update)
        return conversation_views[state].state(
            update.callback_query.message,
            "❌ Operation has been cancelled",
            True,
        )

    def handle_submit(self, update: Update, state):
        print(
            print_label,
            f"{update.callback_query.message.chat.first_name} ({update.callback_query.message.chat.id}) state {self.state_name} doesn't have handle_submit",
        )

    def handle_typed(self, update: Update):
        print(
            print_label,
            f"{update.message.chat.first_name} ({update.message.chat.id}) state {self.state_name} doesn't have handle_typed",
        )

    def _handle_typed(self, update: Update, context: CallbackContext):
        print("_handle_typed", self.state_name)
        telegram_users[update.message.chat.id].operational_sequence[-1].append(
            self.state_name
        )
        return self.handle_typed(update)

    def _handle(self, update: Update, context: CallbackContext):
        data: str = update.callback_query.data
        print("_handle", self.state_name, data)
        context.bot.answer_callback_query(callback_query_id=update.callback_query.id)

        telegram_user = telegram_users[update.callback_query.message.chat.id]

        if data == "_BACK":
            if len(telegram_user.operational_sequence[-1]) > 0:
                state = telegram_user.operational_sequence[-1].pop()
                if (
                    len(telegram_user.operational_sequence[-1]) == 0
                    and len(telegram_user.operational_sequence) > 1
                ):
                    telegram_user.operational_sequence.pop()
            elif len(telegram_user.states_sequence) > 0:
                state = telegram_user.states_sequence.pop()
            else:
                state = "main"
            return conversation_views[state].state(
                update.callback_query.message,
                "",
                True,
            )
        elif data == "_NEXT":
            telegram_user.operational_sequence[-1].append(self.state_name)
            return self.handle_next(update)
        elif data == "_SKIP":
            telegram_user.operational_sequence[-1].append(self.state_name)
            return self.handle_skip(update)
        elif (
            data == "_PAGE_REWIND"
            or data == "_PAGE_BACKWARD"
            or data == "_PAGE_FORWARD"
            or data == "_PAGE_FASTFORWARD"
        ):
            return self.handle_pagination(update, data)
        elif (
            data == "_DATE_TODAY" or data == "_DATE_BACKWARD" or data == "_DATE_FORWARD"
        ):
            return self.handle_date(update, data)
        elif data == "_CANCEL":
            if len(telegram_user.operational_sequence) > 0:
                if len(telegram_user.operational_sequence) > 1:
                    telegram_user.operational_sequence.pop()
                else:
                    telegram_user.operational_sequence[0].clear()
            if len(telegram_user.states_sequence[-1]) > 0:
                state = telegram_user.states_sequence.pop()
            elif len(telegram_user.states_sequence) > 0:
                state = telegram_user.states_sequence.pop()
            else:
                state = "main"
            return self._handle_cancel(update, state)
        elif data == "_SUBMIT":
            if len(telegram_user.operational_sequence) > 0:
                if len(telegram_user.operational_sequence) > 1:
                    telegram_user.operational_sequence.pop()
                else:
                    telegram_user.operational_sequence[0].clear()
            if len(telegram_user.states_sequence[-1]) > 0:
                state = telegram_user.states_sequence.pop()
            elif len(telegram_user.states_sequence) > 0:
                state = telegram_user.states_sequence.pop()
            else:
                state = "main"
            return self.handle_submit(
                update,
                state,
            )
        elif data == "_RECORDS":
            telegram_user.states_sequence.append(self.state_name)
            return self.handle_records(update)
        elif data == "_ADD":
            telegram_user.states_sequence.append(self.state_name)
            return self.handle_add(update)
        else:
            if data in conversation_views and conversation_views[data].skip_to_records:
                data = f"{data}_RECORDS"
            if telegram_users[update.callback_query.message.chat.id].state != data:
                if self.state_name in operational_states:
                    if (
                        len(telegram_user.operational_sequence[-1]) == 0
                        or telegram_user.operational_sequence[-1][-1] != self.state_name
                    ):
                        telegram_user.operational_sequence[-1].append(self.state_name)
                else:
                    if (
                        len(telegram_user.states_sequence) == 0
                        or telegram_user.states_sequence[-1] != self.state_name
                    ):
                        telegram_user.states_sequence.append(self.state_name)
            if data in conversation_views or self.handle_anything:
                return self.handle(update, data)
            else:
                return conversation_views["_WIP"].state(
                    update.callback_query.message,
                    f"⚠️ State '<b>{data}</b>' doesn't exist",
                    True,
                )


class DefaultTelegramConversationView(TelegramConversationView):
    def __init__(
        self,
        state_name: str,
        forks: "list[list[str]]",
    ) -> None:
        super().__init__(state_name)

        keyboard = []

        for forks_line in forks:
            keyboard_line = []
            keyboard.append(keyboard_line)
            for fork in forks_line:
                keyboard_line.append(
                    InlineKeyboardButton(
                        callback_data=fork,
                        text=localization["states"].get(fork, fork),
                    )
                )

        if state_name != "main":
            keyboard.append([back_button])

        self._keyboard = InlineKeyboardMarkup(keyboard)

    def keyboard(self, message: Message) -> InlineKeyboardMarkup:
        return self._keyboard

    def handle(self, update: Update, data):
        return conversation_views[data].state(
            update.callback_query.message,
            "",
            True,
        )


class DatabaseTelegramConversationView(TelegramConversationView):
    def __init__(self, state_name: str, columns: list[dict], display_func=None) -> None:
        super().__init__(state_name)
        self.columns = columns
        self.display_func = display_func

        keyboard = []

        aggregated_columns = []

        DATABASE_DRIVER.create_table(state_name, columns)

        skip_to_records = True

        for column in columns:
            if "aggregate" in column:
                if skip_to_records:
                    skip_to_records = False
                aggregated_columns.append(column["column"])
                code = f"{state_name}_STATS_{column['column']}"
                stats_view = DatabaseStatsTelegramConversationView(
                    code, state_name, column, columns
                )

                keyboard.append(
                    [
                        InlineKeyboardButton(
                            callback_data=code,
                            text=stats_view.state_name_text_short(),
                        )
                    ]
                )

        self.skip_to_records = skip_to_records

        special_handlers = {
            "get_records": GetRecordsTelegramConversationView(
                f"{state_name}_RECORDS", state_name
            ),
            "add_record": AddRecordTelegramConversationView(
                f"{state_name}_ADD", state_name
            ),
        }

        keyboard.append([back_button, records_button, add_button])

        self._keyboard = InlineKeyboardMarkup(keyboard)
        self._special_handlers = special_handlers

    def keyboard(self, message: Message) -> InlineKeyboardMarkup:
        return self._keyboard

    def handle(self, update: Update, data):
        return conversation_views[data].state(
            update.callback_query.message,
            "",
            True,
        )

    def handle_records(self, update: Update):
        return self._special_handlers["get_records"].state(
            update.callback_query.message,
            "",
            True,
        )

    def handle_add(self, update: Update):
        state = check_record_params(
            self._special_handlers["add_record"],
            telegram_users[update.callback_query.message.chat.id],
        )
        return state.state(
            update.callback_query.message,
            "",
            True,
        )


class DatabaseStatsTelegramConversationView(TelegramConversationView):
    def __init__(
        self, state_name: str, parent_state_name, agg_column, columns: list[dict]
    ) -> None:
        super().__init__(state_name)
        operational_states[state_name] = self
        self.parent_state_name = parent_state_name
        self.agg_column = agg_column
        self.columns = columns

    def state_name_text(self):
        return "Report: " + localization["states"].get(
            f"{self.parent_state_name}_PARAM_{self.agg_column['column']}",
            self.state_name,
        )

    def state_name_text_short(self):
        return "Report: " + localization["states"].get(
            f"{self.parent_state_name}_PARAM_SHORT_{self.agg_column['column']}",
            self.state_name,
        )

    def keyboard(self, message: Message) -> InlineKeyboardMarkup:
        keyboard = []

        for column in self.columns:
            if column["type"] == "data" or column["type"] == "date":
                code = f"{self.state_name}_GROUPBY_{column['column']}"
                info_view = InfoTelegramConversationView(
                    code, column, self.state_name, self.parent_state_name
                )
                keyboard.append(
                    [
                        InlineKeyboardButton(
                            callback_data=code,
                            text=info_view.state_name_text_short(),
                        )
                    ]
                )

        keyboard.append([back_button])

        return InlineKeyboardMarkup(keyboard)


class InfoTelegramConversationView(TelegramConversationView):
    def __init__(
        self, state_name: str, groupby_column, parent_state_name, grandparent_state_name
    ) -> None:
        super().__init__(state_name)
        operational_states[state_name] = self

        self.groupby_column = groupby_column
        self.parent_state_name = parent_state_name
        self.grandparent_state_name = grandparent_state_name

        keyboard = []

        keyboard.append([back_button])

        self._keyboard = InlineKeyboardMarkup(keyboard)

    def state_name_text(self):
        return (
            f"{conversation_views[self.parent_state_name].state_name_text()} by "
            + localization["states"].get(
                f"{self.grandparent_state_name}_PARAM_{self.groupby_column['column']}",
                self.state_name,
            )
        )

    def state_name_text_short(self):
        return f"{conversation_views[self.parent_state_name].state_name_text_short()} by " + localization[
            "states"
        ].get(
            f"{self.grandparent_state_name}_PARAM_SHORT_{self.groupby_column['column']}",
            self.state_name,
        )

    def keyboard(self, message: Message) -> InlineKeyboardMarkup:
        return self._keyboard


class GetRecordsTelegramConversationView(TelegramConversationView):
    def __init__(self, state_name: str, table_name) -> None:
        super().__init__(state_name)
        operational_states[state_name] = self
        self.table_name = table_name
        self.handle_anything = True

    def state_text(self, telegram_user):
        return _records_state_text(self.table_name, telegram_user)

    def keyboard(self, message: Message) -> InlineKeyboardMarkup:
        keyboard = _records_keyboard(self.table_name, [], message)
        keyboard.append([back_button, add_button])

        return InlineKeyboardMarkup(keyboard)

    def handle_pagination(self, update: Update, data):
        options_changed = _records_handle_pagination(self.table_name, update, data)

        print(
            self.table_name,
            "options_changed",
            options_changed,
        )

        if options_changed:
            return conversation_views[self.state_name].state(
                update.callback_query.message,
                "",
                True,
            )

    def handle_add(self, update: Update):
        state = _records_handle_add(self.table_name, update)
        return state.state(
            update.callback_query.message,
            "",
            True,
        )


class AddRecordTelegramConversationView(TelegramConversationView):
    def __init__(self, state_name: str, table_name) -> None:
        super().__init__(state_name)
        operational_states[state_name] = self
        self.table_name = table_name
        keyboard = []

        for column in conversation_views[table_name].columns:
            code = f"{table_name}_PARAM_{column['column']}"
            if column["type"] == "boolean":
                operational_states[code] = ChangeBooleanRecordTelegramConversationView(
                    code, state_name, table_name, column
                )
            elif column["type"] == "select":
                operational_states[code] = ChangeSelectRecordTelegramConversationView(
                    code, state_name, table_name, column
                )
            elif column["type"] == "data":
                operational_states[code] = ChangeDataRecordTelegramConversationView(
                    code, state_name, table_name, column
                )
            elif column["type"] == "date":
                operational_states[code] = ChangeDateRecordTelegramConversationView(
                    code, state_name, table_name, column
                )
            else:
                operational_states[code] = ChangeTextRecordTelegramConversationView(
                    code, state_name, table_name, column
                )
            keyboard.append(
                [
                    InlineKeyboardButton(
                        callback_data=code,
                        text=localization["states"].get(code, code),
                    )
                ]
            )

        special_handlers = {}

        keyboard.append([back_button, cancel_button, submit_button])

        self._keyboard = InlineKeyboardMarkup(keyboard)
        self._special_handlers = special_handlers

    def record_display(self, record):
        print(self.table_name, str(record.get("id", "?")))
        return (
            conversation_views[self.table_name].display_func
            and conversation_views[self.table_name].display_func(record)
            or str(record.get("id", "?"))
        )

    def state_text(self, telegram_user):
        return f"<u>Preview</u>\n{self.record_display(_get_records(table_name=self.table_name, external=telegram_user.records[self.table_name], one=True))}"

    def keyboard(self, message: Message) -> InlineKeyboardMarkup:
        return self._keyboard

    def handle(self, update: Update, data):
        return conversation_views[data].state(
            update.callback_query.message,
            "",
            True,
        )

    def handle_cancel(self, update: Update):
        print("cancel from AddRecordTelegramConversationView")
        telegram_users[update.callback_query.message.chat.id].records[
            self.table_name
        ].clear()
        telegram_users[update.callback_query.message.chat.id].ignore_fast[
            self.table_name
        ].clear()

    def handle_submit(self, update: Update, state):
        DATABASE_DRIVER.append_data(
            self.table_name,
            telegram_users[update.callback_query.message.chat.id].records[
                self.table_name
            ],
        )
        telegram_users[update.callback_query.message.chat.id].records[
            self.table_name
        ].clear()
        telegram_users[update.callback_query.message.chat.id].ignore_fast[
            self.table_name
        ].clear()
        return conversation_views[state].state(
            update.callback_query.message,
            "✅ The record has been added successfully",
            True,
        )


class ChangeRecordTelegramConversationView(TelegramConversationView):
    def __init__(
        self, state_name: str, parent_state_name: str, table_name, column
    ) -> None:
        super().__init__(state_name)
        operational_states[state_name] = self
        self.parent_state_name = parent_state_name
        self.table_name = table_name
        self.column = column
        self.handle_anything = True
        self._help_text = "Set your value below"

    def record_display(self, record):
        print(self.table_name, str(record.get("id", "?")))
        return (
            conversation_views[self.table_name].display_func
            and conversation_views[self.table_name].display_func(record)
            or str(record.get("id", "?"))
        )

    def state_name_text(self):
        return f"{localization['states'].get(self.parent_state_name, self.parent_state_name)} > {localization['states'].get(self.state_name, self.state_name)}"

    def state_name_text_short(self):
        return localization["states"].get(
            f"{self.table_name}_PARAM_SHORT_{self.column['column']}",
            super().state_name_text(),
        )

    def state_text(self, telegram_user):
        return f"<u>Preview</u>\n{self.record_display(_get_records(table_name=self.table_name, external=telegram_user.records[self.table_name], one=True))}\n\n<b><u>{self.state_name_text_short()}</u></b>: {self._help_text}"

    def verify_next(self, message: Message, data):
        check_record_params(
            conversation_views[self.parent_state_name],
            telegram_users[message.chat.id],
        )
        if (
            self.column["type"] == "number"
            or self.column["type"] == "data"
            # or self.column["type"] == "date"
        ):
            parsed_data = int(data)
        elif self.column["type"] == "float":
            parsed_data = float(data)
        elif self.column["type"] == "boolean":
            parsed_data = data == "_TRUE" and True or False
        else:
            parsed_data = data
        telegram_users[message.chat.id].records[self.table_name][
            self.column["column"]
        ] = parsed_data
        state = check_record_params(
            conversation_views[self.parent_state_name],
            telegram_users[message.chat.id],
        )
        print("next state is " + state.state_name)
        return state.state(
            message,
            f"✅ Successfully added <b>{data}</b> ({self.column['type']}) for column <b>{self.column['column']}</b>",
            True,
        )

    def handle(self, update: Update, data):
        return self.verify_next(update.callback_query.message, data)

    def handle_skip(self, update: Update):
        check_record_params(
            conversation_views[self.parent_state_name],
            telegram_users[update.callback_query.message.chat.id],
        )
        telegram_users[update.callback_query.message.chat.id].ignore_fast[
            self.table_name
        ][self.column["column"]] = True
        state = check_record_params(
            conversation_views[self.parent_state_name],
            telegram_users[update.callback_query.message.chat.id],
        )
        return state.state(
            update.callback_query.message,
            f"⚠️ Skipping column <i>{self.column['column']}</i>",
            False,
        )

    def handle_cancel(self, update: Update):
        print("cancel from ChangeRecordTelegramConversationView")
        telegram_users[update.callback_query.message.chat.id].records[
            self.table_name
        ].clear()
        telegram_users[update.callback_query.message.chat.id].ignore_fast[
            self.table_name
        ].clear()

    def handle_typed(self, update: Update):
        return self.verify_next(update.message, update.message.text)


class ChangeTextRecordTelegramConversationView(ChangeRecordTelegramConversationView):
    def __init__(
        self, state_name: str, parent_state_name: str, table_name, column
    ) -> None:
        super().__init__(state_name, parent_state_name, table_name, column)
        keyboard = []

        controls = [back_button, cancel_button]
        if "skippable" in column and column["skippable"]:
            controls.append(skip_button)
        keyboard.append(controls)

        self._keyboard = InlineKeyboardMarkup(keyboard)
        self._help_text = "Type your value below or skip it to the next value"

    def keyboard(self, message: Message) -> InlineKeyboardMarkup:
        return self._keyboard


class ChangeBooleanRecordTelegramConversationView(ChangeRecordTelegramConversationView):
    def __init__(
        self, state_name: str, parent_state_name: str, table_name, column
    ) -> None:
        super().__init__(state_name, parent_state_name, table_name, column)
        keyboard = []

        keyboard.append(
            [
                InlineKeyboardButton(
                    callback_data="_YES",
                    text="Yes",
                )
            ]
        )
        keyboard.append(
            [
                InlineKeyboardButton(
                    callback_data="_NO",
                    text="No",
                )
            ]
        )

        controls = [back_button, cancel_button]
        if "skippable" in column and column["skippable"]:
            controls.append(skip_button)
        keyboard.append(controls)

        self._keyboard = InlineKeyboardMarkup(keyboard)
        self._help_text = "Select your value below"

    def keyboard(self, message: Message) -> InlineKeyboardMarkup:
        return self._keyboard


class ChangeSelectRecordTelegramConversationView(ChangeRecordTelegramConversationView):
    def __init__(
        self, state_name: str, parent_state_name: str, table_name, column
    ) -> None:
        super().__init__(state_name, parent_state_name, table_name, column)
        keyboard = []

        for selectee in self.column["select"]:
            keyboard.append(
                [
                    InlineKeyboardButton(
                        callback_data=selectee,
                        text=selectee,
                    )
                ]
            )

        controls = [back_button, cancel_button]
        if "skippable" in column and column["skippable"]:
            controls.append(skip_button)
        keyboard.append(controls)

        self._keyboard = InlineKeyboardMarkup(keyboard)
        self._help_text = "Select your value below"

    def keyboard(self, message: Message) -> InlineKeyboardMarkup:
        return self._keyboard


class ChangeDataRecordTelegramConversationView(ChangeRecordTelegramConversationView):
    def __init__(
        self, state_name: str, parent_state_name: str, table_name, column
    ) -> None:
        super().__init__(state_name, parent_state_name, table_name, column)
        self._help_text = "Select your value below"

    def state_text(self, telegram_user):
        return (
            super().state_text(telegram_user)
            + "\n\n"
            + _records_state_text(self.column["data_type"], telegram_user)
        )

    def keyboard(self, message: Message) -> InlineKeyboardMarkup:
        keyboard = _records_keyboard(self.column["data_type"], [], message)

        controls = [back_button, cancel_button, add_button]
        if "skippable" in self.column and self.column["skippable"]:
            controls.append(skip_button)
        keyboard.append(controls)

        return InlineKeyboardMarkup(keyboard)

    def handle_pagination(self, update: Update, data):
        options_changed = _records_handle_pagination(
            self.column["data_type"], update, data
        )

        if options_changed:
            return conversation_views[self.state_name].state(
                update.callback_query.message,
                "",
                True,
            )

    def handle_add(self, update: Update):
        state = _records_handle_add(self.column["data_type"], update)
        print(state)
        telegram_users[
            update.callback_query.message.chat.id
        ].operational_sequence.append(deque())
        return state.state(
            update.callback_query.message,
            "",
            True,
        )


class ChangeDateRecordTelegramConversationView(ChangeRecordTelegramConversationView):
    def __init__(
        self, state_name: str, parent_state_name: str, table_name, column
    ) -> None:
        super().__init__(state_name, parent_state_name, table_name, column)
        self._help_text = "Select your value below"

    def keyboard(self, message: Message) -> InlineKeyboardMarkup:
        keyboard = []

        date_offset = telegram_users[message.chat.id].date_offset

        today = datetime.today()

        dates = date_utils.date_range(
            today - timedelta(days=(date_offset * 3 + 2)),
            today - timedelta(days=(date_offset * 3)),
        )

        for date in dates:
            date_string = date.strftime("%Y-%m-%d (%a)")
            days_ago = (today - date).days
            if days_ago == 0:
                date_string = f"{date_string}, today"
            elif days_ago == 1:
                date_string = f"{date_string}, yesterday"
            elif days_ago == -1:
                date_string = f"{date_string}, tomorrow"
            elif days_ago < 0:
                date_string = f"{date_string}, in {days_ago}d"
            else:
                date_string = f"{date_string}, {days_ago}d ago"
            keyboard.append(
                [
                    InlineKeyboardButton(
                        date_string,
                        callback_data=int(date.timestamp()),
                    )
                ]
            )

        keyboard.append(
            [
                # InlineKeyboardButton("⏪", callback_data="_DATE_REWIND_BACKWARD"),
                InlineKeyboardButton("◀️", callback_data="_DATE_BACKWARD"),
                InlineKeyboardButton(
                    date_offset > 0 and "Last 3d" or "🚫", callback_data="_DATE_TODAY"
                ),
                InlineKeyboardButton(
                    date_offset > 0 and "▶️" or "🚫", callback_data="_DATE_FORWARD"
                ),
                # InlineKeyboardButton(date_offset > 2 and "⏩" or "🚫", callback_data="_DATE_REWIND_FORWARD"),
            ]
        )

        controls = [back_button, cancel_button]
        if "skippable" in self.column and self.column["skippable"]:
            controls.append(skip_button)
        keyboard.append(controls)

        return InlineKeyboardMarkup(keyboard)

    def handle_date(self, update: Update, data):
        options_changed = False
        date_button = False

        if data == "_DATE_TODAY":
            if telegram_users[update.callback_query.message.chat.id].date_offset > 0:
                options_changed = True
                telegram_users[update.callback_query.message.chat.id].date_offset = 0
        elif data == "_DATE_BACKWARD":
            options_changed = True
            telegram_users[update.callback_query.message.chat.id].date_offset += 1
        elif data == "_DATE_FORWARD":
            if telegram_users[update.callback_query.message.chat.id].date_offset > 0:
                options_changed = True
                telegram_users[update.callback_query.message.chat.id].date_offset -= 1
                if (
                    telegram_users[update.callback_query.message.chat.id].date_offset
                    < 0
                ):
                    telegram_users[
                        update.callback_query.message.chat.id
                    ].date_offset = 0
        else:
            date_button = True

        if options_changed:
            return conversation_views[self.state_name].state(
                update.callback_query.message,
                "",
                True,
            )
        elif date_button:
            return self.verify_next(update.callback_query.message, data)


telegram_users: "dict[Any, TelegramUser]" = {}
conversation_views: "dict[str, TelegramConversationView]" = {}

operational_states = {}

# special handlers that don't have view
back_button = InlineKeyboardButton(
    callback_data="_BACK",
    text=localization["states"].get("_BACK", "_BACK"),
)
records_button = InlineKeyboardButton(
    callback_data="_RECORDS",
    text=localization["states"].get("_RECORDS", "_RECORDS"),
)
add_button = InlineKeyboardButton(
    callback_data="_ADD",
    text=localization["states"].get("_ADD", "_ADD"),
)
next_button = InlineKeyboardButton(
    callback_data="_NEXT",
    text=localization["states"].get("_NEXT", "_NEXT"),
)
skip_button = InlineKeyboardButton(
    callback_data="_SKIP",
    text=localization["states"].get("_SKIP", "_SKIP"),
)
cancel_button = InlineKeyboardButton(
    callback_data="_CANCEL",
    text=localization["states"].get("_CANCEL", "_CANCEL"),
)
submit_button = InlineKeyboardButton(
    callback_data="_SUBMIT",
    text=localization["states"].get("_SUBMIT", "_SUBMIT"),
)
