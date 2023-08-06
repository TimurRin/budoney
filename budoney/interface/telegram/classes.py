import abc
from collections import deque
from typing import Any, Callable
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Message, Update
from telegram.ext import CallbackContext, CallbackQueryHandler, MessageHandler, Filters
from loc import localization
from database import DATABASE_DRIVER
from dispatcher.telegram import send_info_message
import utils.date_utils as date_utils
import utils.string_utils as string_utils
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


def default_display(record) -> str:
    return "id" in record and record["id"] or "?"


def check_record_params(state, telegram_user):
    if state.table_name not in telegram_user.records:
        telegram_user.records[state.table_name] = {}
    if state.table_name not in telegram_user.records_data:
        telegram_user.records_data[state.table_name] = dict(
            telegram_user.records[state.table_name]
        )
    if state.table_name not in telegram_user.ignore_fast:
        telegram_user.ignore_fast[state.table_name] = {}
    for column in database_views[state.table_name].columns:
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
    for column in database_views[table_name].columns:
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
    table_name=None,
    pagination=None,
    search=None,
    external=None,
    record_id=None,
    no_join=None,
):
    table_select = []
    join_select = []
    search_columns = []

    if table_name:
        if not external:
            table_select.append("id")
        for column in database_views[table_name].columns:
            if not external or (
                column["column"] in external and external[column["column"]]
            ):
                if column["type"] == "text":
                    search_columns.append(table_name + "." + column["column"])
                table_select.append(column["column"])

    linked_tables = not no_join and link_tables([], table_name, record=external) or []

    for linked_table in linked_tables:
        for column in database_views[linked_table["name"]].columns:
            if column["type"] == "text":
                search_columns.append(linked_table["alias"] + "." + column["column"])
            join_select.append(
                {"table": linked_table["alias"], "column": column["column"]}
            )

    result = DATABASE_DRIVER.get_records(
        table=table_name,
        table_select=table_select,
        external=external,
        join=linked_tables,
        join_select=join_select,
        search=search,
        search_columns=search_columns,
        offset=pagination and pagination.offset,
        limit=pagination and pagination.limit,
        order_by=table_name and database_views[table_name].order_by,
        record_id=record_id,
    )

    return result


def _records_keyboard(table_name, keyboard, message: Message):
    pagination = telegram_users[message.chat.id].get_pagination(table_name)
    search = telegram_users[message.chat.id].get_search(table_name)

    if len(search[0]) > 0:
        keyboard.append(
            [
                InlineKeyboardButton(
                    callback_data="_CLEAR_SEARCH",
                    text=f"Clear search: {search[0]}",
                )
            ]
        )

    records = _get_records(
        table_name=table_name, pagination=pagination, search=search[1]
    )
    for index, record in enumerate(records):
        keyboard.append(
            [
                InlineKeyboardButton(
                    callback_data=record["id"],
                    text=database_views[table_name].display_inline_func(record)
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
    elif data == "_CLEAR_SEARCH":
        options_changed = True
        telegram_users[update.callback_query.message.chat.id].search[table_name] = (
            "",
            set(),
        )

    return options_changed


def _records_handle_add(table_name, update: Update):
    fast_type_processor = database_views[table_name].fast_type_processor
    if fast_type_processor:
        return conversation_views[f"{table_name}_FAST_TYPE"]
    else:
        return check_record_params(
            conversation_views[f"{table_name}_EDIT"],
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
        self.records_data: dict = dict()
        self.ignore_fast: dict[str, dict[str, bool]] = dict()
        self.pagination: dict[str, Pagination] = dict()
        self.search: dict[str, tuple[str, set]] = dict()
        self.date_offset: int = 0

    def get_pagination(self, table_name):
        if table_name not in self.pagination:
            self.pagination[table_name] = Pagination()
        return self.pagination[table_name]

    def get_search(self, table_name):
        if table_name not in self.search:
            self.search[table_name] = ("", set())
        return self.search[table_name]

    def is_operational(self):
        return (
            len(self.operational_sequence) > 1 or len(self.operational_sequence[0]) > 0
        )

    def clear_edits(self, table_name):
        if table_name in self.records:
            del self.records[table_name]
        if table_name in self.records_data:
            del self.records_data[table_name]
        if table_name in self.ignore_fast:
            del self.ignore_fast[table_name]


class View:
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
        # text = text + f"- records_data: <code>{str(user.records_data)}</code>\n"

        return text + "\n"

    def state_text(self, telegram_user):
        return ""

    @abc.abstractmethod
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

    def handle_pagination(self, update: Update, data):
        print(
            print_label,
            f"{update.callback_query.message.chat.first_name} ({update.callback_query.message.chat.id}) state {self.state_name} doesn't have handle_pagination",
        )

    def handle_date(self, update: Update, data):
        print(
            print_label,
            f"{update.callback_query.message.chat.first_name} ({update.callback_query.message.chat.id}) state {self.state_name} doesn't have handle_date",
        )

    def handle_add(self, update: Update):
        print(
            print_label,
            f"{update.callback_query.message.chat.first_name} ({update.callback_query.message.chat.id}) state {self.state_name} doesn't have handle_add",
        )

    def handle_edit(self, update: Update):
        print(
            print_label,
            f"{update.callback_query.message.chat.first_name} ({update.callback_query.message.chat.id}) state {self.state_name} doesn't have handle_edit",
        )

    def handle_remove(self, update: Update):
        print(
            print_label,
            f"{update.callback_query.message.chat.first_name} ({update.callback_query.message.chat.id}) state {self.state_name} doesn't have handle_remove",
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

    def handle_typed(self, update: Update, data):
        print(
            print_label,
            f"{update.message.chat.first_name} ({update.message.chat.id}) state {self.state_name} doesn't have handle_typed",
        )

    def _handle_typed(self, update: Update, context: CallbackContext):
        print("_handle_typed", self.state_name)
        return self.handle_typed(update, update.message.text)

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
            or data == "_CLEAR_SEARCH"
        ):
            return self.handle_pagination(update, data)
        elif (
            data == "_DATE_TODAY" or data == "_DATE_BACKWARD" or data == "_DATE_FORWARD"
        ):
            return self.handle_date(update, data)
        elif data == "_CANCEL":
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
        elif data == "_EDIT":
            # telegram_user.states_sequence.append(self.state_name)
            return self.handle_edit(update)
        elif data == "_REMOVE":
            return self.handle_remove(update)
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
            elif data in shortcuts and shortcuts[data]:
                if shortcuts[data][0] == "add":
                    add_view = _records_handle_add(shortcuts[data][1], update)
                    return add_view.state(
                        update.callback_query.message,
                        "",
                        True,
                    )
            return conversation_views["_WIP"].state(
                update.callback_query.message,
                f"⚠️ State '<b>{data}</b>' doesn't exist",
                True,
            )


class DefaultView(View):
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


class DatabaseView(View):
    def __init__(
        self,
        state_name: str,
        columns: list[dict],
        display_inline_func: Callable[[dict[str, Any]], str] = default_display,
        display_full_func: Callable[[dict[str, Any]], str] | None = None,
        fast_type_processor: Callable[[str], dict[str, Any]] | None = None,
        order_by: list[tuple[str, bool, str | None]] | None = None,
    ) -> None:
        super().__init__(state_name)
        database_views[state_name] = self
        self.columns = columns
        self.display_inline_func: Callable[[dict[str, Any]], str] = display_inline_func
        self.display_full_func: Callable[[dict[str, Any]], str] = (
            display_full_func or display_inline_func
        )
        self.fast_type_processor: Callable[
            [str], dict[str, Any]
        ] | None = fast_type_processor
        if order_by == None:
            order_by = []
        self.order_by: list[tuple[str, bool, str | None]] = order_by

        keyboard = []

        aggregated_columns = []

        DATABASE_DRIVER.create_table(state_name, columns)

        skip_to_records = True

        for column in columns:
            if "aggregate" in column:
                # if skip_to_records:
                #     skip_to_records = False
                aggregated_columns.append(column["column"])
                code = f"{state_name}_STATS_{column['column']}"
                stats_view = DatabaseStatsView(code, state_name, column, columns)

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
            "get_records": ListRecordsView(f"{state_name}_RECORDS", state_name),
            "add_record": RecordView(f"{state_name}_RECORD", state_name),
            "edit_record": EditRecordView(f"{state_name}_EDIT", state_name),
        }
        shortcuts[f"{state_name}_ADD"] = ("add", state_name)
        if self.fast_type_processor:
            special_handlers["fast_type"] = FastTypeRecordView(
                f"{state_name}_FAST_TYPE", state_name
            )

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
        state = _records_handle_add(self.state_name, update)
        return state.state(
            update.callback_query.message,
            "",
            True,
        )


class DatabaseStatsView(View):
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
                info_view = InfoView(
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


class InfoView(View):
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


class ListRecordsView(View):
    def __init__(self, state_name: str, table_name) -> None:
        super().__init__(state_name)
        self.table_name = table_name
        self.handle_anything = True

    def state_text(self, telegram_user):
        return _records_state_text(self.table_name, telegram_user)

    def keyboard(self, message: Message) -> InlineKeyboardMarkup:
        keyboard = _records_keyboard(self.table_name, [], message)
        keyboard.append([back_button, add_button])

        return InlineKeyboardMarkup(keyboard)

    def handle(self, update: Update, data):
        telegram_users[update.callback_query.message.chat.id].records[
            self.table_name
        ] = _get_records(table_name=self.table_name, record_id=data, no_join=True)[0]
        telegram_users[update.callback_query.message.chat.id].records_data[
            self.table_name
        ] = _get_records(
            table_name=self.table_name,
            external=telegram_users[update.callback_query.message.chat.id].records[
                self.table_name
            ],
        )[
            0
        ]
        return conversation_views[self.table_name + "_RECORD"].state(
            update.callback_query.message,
            "",
            True,
        )

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

    def handle_typed(self, update: Update, data):
        search = telegram_users[update.message.chat.id].get_search(self.table_name)
        if search[0] != data:
            telegram_users[update.message.chat.id].search[self.table_name] = (
                data,
                string_utils.sql_search(data),
            )
            pagination = telegram_users[update.message.chat.id].get_pagination(
                self.table_name
            )
            pagination.offset = 0
            return conversation_views[self.state_name].state(
                update.message,
                "",
                True,
            )


class RecordView(View):
    def __init__(self, state_name: str, table_name) -> None:
        super().__init__(state_name)
        operational_states[state_name] = self
        self.table_name = table_name

    def record_display(self, record):
        print(self.table_name, str(record.get("id", "?")))
        return database_views[self.table_name].display_full_func(record) or str(
            record.get("id", "?")
        )

    def state_text(self, telegram_user):
        record_data = telegram_user.records_data[self.table_name]
        return f"<i>{'id' in record_data and ('Viewing record ID ' + str(record_data['id'])) or 'New record'}</i>\n{self.record_display(record_data)}"

    def keyboard(self, message: Message) -> InlineKeyboardMarkup:
        keyboard = []

        for column in database_views[self.table_name].columns:
            display = False
            code = f"{self.table_name}_PARAM_{column['column']}"
            code_text = f"{self.table_name}_PARAM_SHORT_{column['column']}"
            text = localization["states"].get(code_text, column["column"])
            if (
                column["column"]
                in telegram_users[message.chat.id].records[self.table_name]
                and telegram_users[message.chat.id].records[self.table_name][
                    column["column"]
                ]
            ):
                if column["type"] == "data":
                    display = True
                    relevant = {
                        k.replace(column["column"] + "__", ""): v
                        for k, v in telegram_users[message.chat.id]
                        .records_data[self.table_name]
                        .items()
                        if k.startswith(column["column"] + "__")
                    }
                    text_value = database_views[
                        column["data_type"]
                    ].display_inline_func(relevant)
                    if text_value:
                        text = f"Go to: {text} [{text_value}]"
            if display:
                keyboard.append(
                    [
                        InlineKeyboardButton(
                            callback_data=code,
                            text=text,
                        )
                    ]
                )

        controls = [back_button, edit_button]

        keyboard.append(controls)

        return InlineKeyboardMarkup(keyboard)

    def handle_edit(self, update: Update):
        return conversation_views[self.table_name + "_EDIT"].state(
            update.callback_query.message,
            "",
            True,
        )


class FastTypeRecordView(View):
    def __init__(self, state_name: str, table_name) -> None:
        super().__init__(state_name)
        operational_states[state_name] = self
        self.table_name = table_name
        self.handle_anything = True

    def state_text(self, telegram_user) -> str:
        return "Select an appropriate template or type data to work with"

    def keyboard(self, message: Message) -> InlineKeyboardMarkup:
        keyboard = []

        keyboard.append(
            [
                InlineKeyboardButton(
                    callback_data="_ALL",
                    text="Enter all params",
                )
            ]
        )

        controls = [back_button]

        keyboard.append(controls)

        return InlineKeyboardMarkup(keyboard)

    def handle(self, update: Update, data):
        if data == "_ALL":
            pass
        return check_record_params(
            conversation_views[f"{self.table_name}_EDIT"],
            telegram_users[update.callback_query.message.chat.id],
        ).state(
            update.callback_query.message,
            "",
            True,
        )

    def handle_typed(self, update: Update, data):
        proc = database_views[self.table_name].fast_type_processor
        if proc is not None:
            telegram_users[update.message.chat.id].records[self.table_name] = proc(data)
            telegram_users[update.message.chat.id].records_data[
                self.table_name
            ] = _get_records(
                table_name=self.table_name,
                external=telegram_users[update.message.chat.id].records[
                    self.table_name
                ],
            )[
                0
            ]
        return check_record_params(
            conversation_views[f"{self.table_name}_EDIT"],
            telegram_users[update.message.chat.id],
        ).state(
            update.message,
            "",
            True,
        )


class EditRecordView(View):
    def __init__(self, state_name: str, table_name) -> None:
        super().__init__(state_name)
        operational_states[state_name] = self
        self.table_name = table_name

        for column in database_views[table_name].columns:
            code = f"{table_name}_PARAM_{column['column']}"
            if column["type"] == "boolean":
                EditBooleanRecordValueView(code, state_name, table_name, column)
            elif column["type"] == "select":
                EditSelectRecordValueView(code, state_name, table_name, column)
            elif column["type"] == "data":
                EditDataRecordValueView(code, state_name, table_name, column)
            elif column["type"] == "date":
                EditDateRecordValueView(code, state_name, table_name, column)
            else:
                EditTextRecordValueView(code, state_name, table_name, column)

    def record_display(self, record):
        print(self.table_name, str(record.get("id", "?")))
        return database_views[self.table_name].display_full_func(record) or str(
            record.get("id", "?")
        )

    def state_text(self, telegram_user):
        record_data = telegram_user.records_data[self.table_name]
        return f"<i>{'id' in record_data and ('Editing record ID ' + str(record_data['id'])) or 'New record'}</i>\n{self.record_display(record_data)}"

    def keyboard(self, message: Message) -> InlineKeyboardMarkup:
        keyboard = []

        for column in database_views[self.table_name].columns:
            code = f"{self.table_name}_PARAM_{column['column']}"
            code_text = f"{self.table_name}_PARAM_SHORT_{column['column']}"
            text = localization["states"].get(code_text, column["column"])
            if (
                column["column"]
                in telegram_users[message.chat.id].records[self.table_name]
                and telegram_users[message.chat.id].records[self.table_name][
                    column["column"]
                ]
            ):
                value = telegram_users[message.chat.id].records[self.table_name][
                    column["column"]
                ]
                if column["type"] == "date":
                    date_timestamp = datetime.fromtimestamp(value)
                    date_string = f"{date_timestamp.strftime('%Y-%m-%d (%a)')}, {date_utils.get_relative_timestamp(value)}"
                    text = f"{text} [{date_string}]"
                elif column["type"] == "data":
                    relevant = {
                        k.replace(column["column"] + "__", ""): v
                        for k, v in telegram_users[message.chat.id]
                        .records_data[self.table_name]
                        .items()
                        if k.startswith(column["column"] + "__")
                    }
                    text_value = database_views[
                        column["data_type"]
                    ].display_inline_func(relevant)
                    if text_value:
                        text = f"{text} [{text_value}]"
                else:
                    text_value = str(value)
                    if value:
                        text = f"{text} [{text_value}]"
            keyboard.append(
                [
                    InlineKeyboardButton(
                        callback_data=code,
                        text=text,
                    )
                ]
            )

        controls = []
        if telegram_users[message.chat.id].is_operational():
            controls.append(back_button)
        controls.append(cancel_button)
        controls.append(submit_button)

        keyboard.append(controls)

        return InlineKeyboardMarkup(keyboard)

    def handle(self, update: Update, data):
        return conversation_views[data].state(
            update.callback_query.message,
            "",
            True,
        )

    def handle_cancel(self, update: Update):
        print("cancel from EditRecordView")
        telegram_users[update.callback_query.message.chat.id].clear_edits(
            self.table_name
        )

    def handle_submit(self, update: Update, state):
        record = telegram_users[update.callback_query.message.chat.id].records[
            self.table_name
        ]
        if "id" in record:
            DATABASE_DRIVER.replace_data(
                self.table_name,
                record["id"],
                record,
            )
        else:
            DATABASE_DRIVER.append_data(
                self.table_name,
                record,
            )
            if database_views[self.table_name].display_full_func:
                send_info_message(
                    database_views[self.table_name].display_full_func(
                        telegram_users[
                            update.callback_query.message.chat.id
                        ].records_data[self.table_name]
                    )
                )

        telegram_users[update.callback_query.message.chat.id].clear_edits(
            self.table_name
        )
        return conversation_views[state].state(
            update.callback_query.message,
            "✅ The record has been added successfully",
            True,
        )


class EditRecordValueView(View):
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
        return database_views[self.table_name].display_full_func(record) or str(
            record.get("id", "?")
        )

    def state_name_text_short(self):
        return localization["states"].get(
            f"{self.table_name}_PARAM_SHORT_{self.column['column']}",
            super().state_name_text(),
        )

    def state_text(self, telegram_user):
        record_data = telegram_user.records_data[self.table_name]
        return f"<i>{'id' in record_data and ('Editing record ID ' + str(record_data['id'])) or 'New record'}</i>\n{self.record_display(record_data)}\n\n<b><u>{self.state_name_text_short()}</u></b>: {self._help_text}"

    def _keyboard_controls(self, telegram_user, add=False):
        controls = []
        if telegram_user.is_operational():
            controls.append(back_button)
        controls.append(cancel_button)
        if add:
            controls.append(add_button)
        if "skippable" in self.column and self.column["skippable"]:
            if (
                "id" in telegram_user.records[self.table_name]
                and telegram_user.records[self.table_name]["id"]
            ):
                controls.append(remove_button)
            else:
                controls.append(skip_button)
        return controls

    def verify_next(self, message: Message, data):
        check_record_params(
            conversation_views[self.parent_state_name],
            telegram_users[message.chat.id],
        )
        if (
            self.column["type"] == "int"
            or self.column["type"] == "data"
            or self.column["type"] == "date"
        ):
            parsed_data = int(data)
        elif self.column["type"] == "float":
            parsed_data = float(data)
        elif self.column["type"] == "boolean":
            parsed_data = data == "_YES" and 1 or 0
        else:
            parsed_data = data
        telegram_users[message.chat.id].records[self.table_name][
            self.column["column"]
        ] = parsed_data
        telegram_users[message.chat.id].records_data[self.table_name] = _get_records(
            table_name=self.table_name,
            external=telegram_users[message.chat.id].records[self.table_name],
        )[0]

        if "set" in self.column and self.column["set"]:
            for setee in self.column["set"]:
                telegram_users[message.chat.id].records[self.table_name][
                    setee["column"]
                ] = telegram_users[message.chat.id].records_data[self.table_name][
                    setee["from"]
                ]
            telegram_users[message.chat.id].records_data[
                self.table_name
            ] = _get_records(
                table_name=self.table_name,
                external=telegram_users[message.chat.id].records[self.table_name],
            )[
                0
            ]

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

    def handle_remove(self, update: Update):
        check_record_params(
            conversation_views[self.parent_state_name],
            telegram_users[update.callback_query.message.chat.id],
        )
        telegram_users[update.callback_query.message.chat.id].records[self.table_name][
            self.column["column"]
        ] = None
        telegram_users[update.callback_query.message.chat.id].ignore_fast[
            self.table_name
        ][self.column["column"]] = True
        state = check_record_params(
            conversation_views[self.parent_state_name],
            telegram_users[update.callback_query.message.chat.id],
        )
        return state.state(
            update.callback_query.message,
            f"⚠️ Removing column <i>{self.column['column']}</i>",
            True,
        )

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
            True,
        )

    def handle_cancel(self, update: Update):
        print("cancel from EditRecordView")
        telegram_users[update.callback_query.message.chat.id].clear_edits(
            self.table_name
        )

    def handle_typed(self, update: Update, data):
        return self.verify_next(update.message, data)


class EditTextRecordValueView(EditRecordValueView):
    def __init__(
        self, state_name: str, parent_state_name: str, table_name, column
    ) -> None:
        super().__init__(state_name, parent_state_name, table_name, column)
        self._help_text = "Type your value below or skip it to the next value"

    def keyboard(self, message: Message) -> InlineKeyboardMarkup:
        keyboard = []

        controls = self._keyboard_controls(telegram_users[message.chat.id])
        keyboard.append(controls)

        return InlineKeyboardMarkup(keyboard)


class EditBooleanRecordValueView(EditRecordValueView):
    def __init__(
        self, state_name: str, parent_state_name: str, table_name, column
    ) -> None:
        super().__init__(state_name, parent_state_name, table_name, column)

        self._help_text = "Select your value below"

    def keyboard(self, message: Message) -> InlineKeyboardMarkup:
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

        controls = self._keyboard_controls(telegram_users[message.chat.id])
        keyboard.append(controls)

        return InlineKeyboardMarkup(keyboard)


class EditSelectRecordValueView(EditRecordValueView):
    def __init__(
        self, state_name: str, parent_state_name: str, table_name, column
    ) -> None:
        super().__init__(state_name, parent_state_name, table_name, column)
        self._help_text = "Select your value below"

    def keyboard(self, message: Message) -> InlineKeyboardMarkup:
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

        controls = self._keyboard_controls(telegram_users[message.chat.id])
        keyboard.append(controls)

        return InlineKeyboardMarkup(keyboard)


class EditDataRecordValueView(EditRecordValueView):
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

        controls = self._keyboard_controls(telegram_users[message.chat.id], add=True)
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


class EditDateRecordValueView(EditRecordValueView):
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
            date_string = f"{date.strftime('%Y-%m-%d (%a)')}, {date_utils.get_relative_timestamp(date.timestamp(), today=today)}"
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

        controls = self._keyboard_controls(telegram_users[message.chat.id])
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
conversation_views: "dict[str, View]" = {}
database_views: "dict[str, DatabaseView]" = {}

shortcuts = {}

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
edit_button = InlineKeyboardButton(
    callback_data="_EDIT",
    text=localization["states"].get("_EDIT", "_EDIT"),
)
remove_button = InlineKeyboardButton(
    callback_data="_REMOVE",
    text=localization["states"].get("_REMOVE", "_REMOVE"),
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
