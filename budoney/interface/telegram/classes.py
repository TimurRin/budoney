import abc
from collections import deque
from typing import Any, Callable
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Message, Update
from telegram.ext import CallbackContext, CallbackQueryHandler, MessageHandler, Filters
from loc import translate
from database import DATABASE_DRIVER
from dispatcher.telegram import send_info_message
import utils.date_utils as date_utils
from utils.version import cf_version
from datetime import datetime, timedelta
import configs
import math

print_label: str = "[budoney :: Telegram Interface]"


class Pagination:
    def __init__(self) -> None:
        self.offset: int = 0
        self.limit: int = 5
        self.total: int = -1
        self.pages: int = 0


class TelegramUser:
    def __init__(self, name: str) -> None:
        self.name: str = name
        self.state: str = "none"
        self.state_sequences: deque[deque] = deque()
        self.state_sequences.append(deque())
        self.records: dict = dict()
        self.records_data: dict = dict()
        self.records_extra: dict = dict()
        self.filters: dict[str, tuple[list[str], list[str | int | float]]] = dict()
        self.ignore_fast: dict[str, dict[str, bool]] = dict()
        self.pagination: dict[str, Pagination] = dict()
        self.search: dict[str, tuple[str, list[str]]] = dict()
        self.date_offset: int = 0
        self.year: int = 0
        self.last_query: tuple[str, list[Any]] = ("", [])

    def get_filters(self, table_name):
        if table_name not in self.filters:
            self.filters[table_name] = (list(), list())
        return self.filters[table_name]

    def get_pagination(self, table_name):
        if table_name not in self.pagination:
            self.pagination[table_name] = Pagination()
        return self.pagination[table_name]

    def get_search(self, table_name) -> tuple[str, list[str]]:
        if table_name not in self.search:
            self.search[table_name] = ("", list())
        return self.search[table_name]

    def add_new_sequence(self):
        self.state_sequences.append(deque())

    def add_to_current_sequence(self, state_name):
        if (
            len(self.state_sequences[-1]) == 0
            or self.state_sequences[-1][-1] != state_name
        ):
            self.state_sequences[-1].append(state_name)

    def add_to_new_sequence(self, state_name):
        self.add_new_sequence()
        self.add_to_current_sequence(state_name)

    def back_in_sequence(self) -> str:
        if len(self.state_sequences[-1]) > 0:
            state = self.state_sequences[-1].pop()
            if len(self.state_sequences[-1]) == 0:
                if len(self.state_sequences) > 1:
                    self.state_sequences.pop()
                else:
                    self.state_sequences[0].clear()
        else:
            state = "main"
        return state

    def drop_last_sequence(self) -> str:
        if len(self.state_sequences) > 1:
            self.state_sequences.pop()
        else:
            self.state_sequences[0].clear()
        if len(self.state_sequences[-1]) > 0:
            state = self.state_sequences[-1].pop()
        else:
            state = "main"
        return state

    def clear_edits(self, table_name):
        if table_name in self.records:
            del self.records[table_name]
        if table_name in self.records_data:
            del self.records_data[table_name]
        if table_name in self.records_extra:
            del self.records_extra[table_name]
        if table_name in self.ignore_fast:
            del self.ignore_fast[table_name]

        if table_name in self.pagination and self.pagination[table_name]:
            self.pagination[table_name].total = -1
        self.temp_pagination = Pagination()

    def clear_sequences(self):
        self.state_sequences: deque[deque] = deque()
        self.state_sequences.append(deque())


class DatabaseReport:
    def __init__(
        self,
        select: list[tuple[str, str | None]],
        group_by: list[str],
        order_by: list[tuple[str, bool, str | None]],
        local_display: Callable[[list[dict[str, Any]]], str],
        foreign_display: Callable[[list[dict[str, Any]]], str],
        layer_display: Callable[..., str],
        foreign_date: str | None = None,
    ) -> None:
        self.select: list[tuple[str, str | None]] = select
        self.group_by: list[str] = group_by
        self.order_by: list[tuple[str, bool, str | None]] = order_by
        self.local_display: Callable[[list[dict[str, Any]]], str] = local_display
        self.foreign_display: Callable[[list[dict[str, Any]]], str] = foreign_display
        self.layer_display: Callable[..., str] = layer_display
        self.foreign_date: str | None = foreign_date


class DatabaseLinkedReport:
    def __init__(
        self,
        table: str,
        link_by: str,
    ) -> None:
        self.table: str = table
        self.link_by: str = link_by


class View:
    def __init__(self, state_name: str) -> None:
        conversation_views[state_name] = self
        self.state_name = state_name
        self.skip_to_records = False
        self.handle_anything = False
        self.no_sequence = False
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

        result_text = (
            result_text
            + f"<b>{self.state_name_text(telegram_users[message.chat.id])}</b>"
        )

        # result_text = (
        #     result_text
        #     + f"<code>{(' ' * 80)}&#x200D;</code>"
        # )

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

    def state_name_text(self, telegram_user: TelegramUser):
        return translate(self.state_name)

    def debug_text(self, user: TelegramUser):
        if configs.general["production_mode"]:
            return ""

        text = f"👩‍💻 Debug for {user.name}:\n"

        text = text + f"- state_sequences: <code>{str(user.state_sequences)}</code>\n"
        text = text + f"- state: <code>{str(user.state)}</code>\n"
        # text = text + f"- records: <code>{str(user.records)}</code>\n"
        # text = text + f"- records_data: <code>{str(user.records_data)}</code>\n"

        return text + "\n"

    def state_text(self, telegram_user):
        return ""

    @abc.abstractmethod
    def keyboard(self, message: Message) -> InlineKeyboardMarkup:
        pass

    def go_home(self, update: Update, telegram_user: TelegramUser):
        telegram_user.clear_sequences()
        return conversation_views["main"].state(
            update.callback_query.message,
            "",
            True,
        )

    def go_back(self, update: Update, telegram_user: TelegramUser):
        return conversation_views[telegram_user.back_in_sequence()].state(
            update.callback_query.message,
            "",
            True,
        )

    def handle(self, update: Update, data: str):
        print(
            print_label,
            f"{update.callback_query.message.chat.first_name} ({update.callback_query.message.chat.id}) state {self.state_name} doesn't have handle ({str(data)})",
        )

    def handle_records(self, update: Update):
        print(
            print_label,
            f"{update.callback_query.message.chat.first_name} ({update.callback_query.message.chat.id}) state {self.state_name} doesn't have handle_records",
        )

    def handle_jump(self, update: Update, jump_table, jump_record_id):
        print(
            print_label,
            f"{update.callback_query.message.chat.first_name} ({update.callback_query.message.chat.id}) state {self.state_name} doesn't have handle_jump",
        )

    def handle_filter(self, update: Update, action, filter_table, a1, a2, a3):
        print(
            print_label,
            f"{update.callback_query.message.chat.first_name} ({update.callback_query.message.chat.id}) state {self.state_name} doesn't have handle_filter",
        )

    def handle_action(self, update: Update, action_id):
        print(
            print_label,
            f"{update.callback_query.message.chat.first_name} ({update.callback_query.message.chat.id}) state {self.state_name} doesn't have handle_action",
        )

    def handle_pagination(self, update: Update, data: str):
        print(
            print_label,
            f"{update.callback_query.message.chat.first_name} ({update.callback_query.message.chat.id}) state {self.state_name} doesn't have handle_pagination ({str(data)})",
        )

    def handle_date(self, update: Update, data: str):
        print(
            print_label,
            f"{update.callback_query.message.chat.first_name} ({update.callback_query.message.chat.id}) state {self.state_name} doesn't have handle_date ({str(data)})",
        )

    @abc.abstractmethod
    def handle_add(self, update: Update) -> str:
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

    def handle_report_layers(self, update: Update, data: str):
        print(
            print_label,
            f"{update.callback_query.message.chat.first_name} ({update.callback_query.message.chat.id}) state {self.state_name} doesn't have handle_report_layers",
        )

    def handle_records_filters(self, update: Update, data: str):
        print(
            print_label,
            f"{update.callback_query.message.chat.first_name} ({update.callback_query.message.chat.id}) state {self.state_name} doesn't have handle_records_filters",
        )

    def handle_records_sort(self, update: Update, data: str) -> None:
        print(
            print_label,
            f"{update.callback_query.message.chat.first_name} ({update.callback_query.message.chat.id}) state {self.state_name} doesn't have handle_records_sort",
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
            translate("_OPERATION_CANCELLED"),
            True,
        )

    def handle_submit(self, update: Update, state):
        print(
            print_label,
            f"{update.callback_query.message.chat.first_name} ({update.callback_query.message.chat.id}) state {self.state_name} doesn't have handle_submit",
        )

    def handle_typed(self, update: Update, data: str):
        print(
            print_label,
            f"{update.message.chat.first_name} ({update.message.chat.id}) state {self.state_name} doesn't have handle_typed",
        )

    def _handle_typed(self, update: Update, context: CallbackContext):
        print(print_label, "_handle_typed", self.state_name)
        return self.handle_typed(update, update.message.text)

    def _handle(self, update: Update, context: CallbackContext):
        data: str = update.callback_query.data
        print(print_label, "_handle", self.state_name, data)
        context.bot.answer_callback_query(callback_query_id=update.callback_query.id)

        telegram_user = telegram_users[update.callback_query.message.chat.id]

        data_pagination = (
            data == "_PAGE_REWIND"
            or data == "_PAGE_BACKWARD"
            or data == "_PAGE_FORWARD"
            or data == "_PAGE_FASTFORWARD"
            or data == "_CLEAR_SEARCH"
            or data == "_CLEAR_FILTERS"
        )

        if data == "_HOME":
            return self.go_home(update, telegram_user)
        elif data == "_BACK":
            return self.go_back(update, telegram_user)
        elif data == "_NEXT":
            telegram_user.add_to_current_sequence(self.state_name)
            return self.handle_next(update)
        elif data == "_SKIP":
            telegram_user.add_to_current_sequence(self.state_name)
            return self.handle_skip(update)
        elif data_pagination:
            return self.handle_pagination(update, data)
        elif (
            data == "_DATE_TODAY" or data == "_DATE_BACKWARD" or data == "_DATE_FORWARD"
        ):
            return self.handle_date(update, data)
        elif data == "_CANCEL":
            return self._handle_cancel(update, telegram_user.drop_last_sequence())
        elif data == "_SUBMIT":
            return self.handle_submit(
                update,
                telegram_user.drop_last_sequence(),
            )
        elif data == "_RECORDS":
            telegram_user.add_to_current_sequence(self.state_name)
            return self.handle_records(update)
        elif data == "_ADD":
            telegram_user.add_to_current_sequence(self.state_name)
            added_state = self.handle_add(update)
            telegram_user.add_to_new_sequence(added_state)
            return added_state
        elif data == "_EDIT":
            telegram_user.add_to_new_sequence(self.state_name)
            return self.handle_edit(update)
        elif data == "_REMOVE":
            return self.handle_remove(update)
        elif data == "_REPORT_LAYERS":
            return self.handle_report_layers(update, data)
        elif data == "_RECORDS_FILTERS":
            return self.handle_records_filters(update, data)
        elif data == "_RECORDS_SORT":
            return self.handle_records_sort(update, data)
        else:
            if data in conversation_views and conversation_views[data].skip_to_records:
                data = f"{data}_RECORDS"
            print(
                print_label,
                "state",
                telegram_users[update.callback_query.message.chat.id].state,
                "data",
                data,
            )
            data_split = data.split("__")
            if data_split[0] == "action" and len(data_split) == 2:
                return self.handle_action(update, int(data_split[1]))
            elif data_split[0] == "jump" and len(data_split) == 3:
                telegram_user.add_to_new_sequence(self.state_name)
                return self.handle_jump(update, data_split[1], int(data_split[2]))
            elif data_split[0] == "filter" and len(data_split) == 6:
                if data_split[1] == "jump":
                    telegram_user.add_to_new_sequence(self.state_name)
                else:
                    telegram_user.back_in_sequence()
                return self.handle_filter(
                    update,
                    data_split[1],
                    data_split[2],
                    data_split[3],
                    data_split[4],
                    data_split[5],
                )
            if (
                not self.no_sequence
                and telegram_users[update.callback_query.message.chat.id].state != data
            ):
                telegram_user.add_to_current_sequence(self.state_name)
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
                f"⚠️ {translate('_NO_STATE')}: <b>{data}</b>",
                True,
            )


class DefaultView(View):
    def __init__(
        self, state_name: str, forks: "list[list[str]]", extra_info=None
    ) -> None:
        super().__init__(state_name)
        self.extra_info = extra_info

        keyboard = []

        for forks_line in forks:
            keyboard_line = []
            keyboard.append(keyboard_line)
            for fork in forks_line:
                keyboard_line.append(
                    InlineKeyboardButton(
                        callback_data=fork,
                        text=translate(fork),
                    )
                )

        if state_name != "main":
            keyboard.append([back_button, home_button])

        self._keyboard = InlineKeyboardMarkup(keyboard)

    def state_text(self, telegram_user):
        if self.extra_info:
            lines = []
            for row in self.extra_info:
                lines.append(row())
            return "\n".join(lines) + "\n" + (self.state_name == "main" and cf_version or "")
        return self.state_name == "main" and cf_version or ""

    def keyboard(self, message: Message) -> InlineKeyboardMarkup:
        return self._keyboard

    def handle(self, update: Update, data: str):
        return conversation_views[data].state(
            update.callback_query.message,
            "",
            True,
        )


class ActionView(View):
    def __init__(
        self, state_name: str, actions: "list[tuple[str, Callable[[], str]]]"
    ) -> None:
        super().__init__(state_name)
        self.handle_anything = True
        self.no_sequence = True
        self.actions = actions
        keyboard = []

        for index, action in enumerate(actions):
            keyboard.append(
                [
                    InlineKeyboardButton(
                        callback_data=index,
                        text=translate(f"{state_name}_ACTION_{action[0]}"),
                    )
                ]
            )

        keyboard.append([back_button, home_button])

        self._keyboard = InlineKeyboardMarkup(keyboard)

    def keyboard(self, message: Message) -> InlineKeyboardMarkup:
        return self._keyboard

    def handle(self, update: Update, data: str):
        try:
            index = int(data)
        except:
            return conversation_views["main"].state(
                update.callback_query.message,
                "Error",
                True,
            )
        return conversation_views[self.state_name].state(
            update.callback_query.message,
            self.actions[index][1]() + " [" + datetime.now().isoformat() + "]",
            True,
        )


class DatabaseView(View):
    def __init__(
        self,
        state_name: str,
        columns: list[dict],
        inline_display: Callable[[dict[str, Any]], str] | None = None,
        extended_display: Callable[[dict[str, Any]], str] | None = None,
        fast_type: str | None = None,
        fast_type_processor: Callable[
            [str],
            tuple[dict[str, Any], dict[str, tuple[list[str], list[str | int | float]]]],
        ]
        | None = None,
        order_by: list[tuple[str, bool, str | None]] | None = None,
        report: DatabaseReport | None = None,
        report_links: list[DatabaseLinkedReport] | None = None,
        extra_info=None,
        actions=None,
    ) -> None:
        super().__init__(state_name)
        database_views[state_name] = self
        self.columns = columns
        if not inline_display:
            inline_display = default_display
        self.inline_display: Callable[[dict[str, Any]], str] = inline_display
        self.extended_display: Callable[[dict[str, Any]], str] = (
            extended_display or inline_display
        )
        self.fast_type: str | None = fast_type
        self.fast_type_processor: Callable[
            [str],
            tuple[dict[str, Any], dict[str, tuple[list[str], list[str | int | float]]]],
        ] | None = fast_type_processor
        if order_by == None:
            order_by = []
        self.order_by: list[tuple[str, bool, str | None]] = order_by
        self.report: DatabaseReport | None = report
        self.report_links: list[DatabaseLinkedReport] | None = report_links
        self.extra_info = extra_info
        self.actions = actions

        keyboard = []

        DATABASE_DRIVER.create_table(state_name, columns)

        self.skip_to_records = True

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

        keyboard.append([back_button, home_button, records_button, add_button])

        self._keyboard = InlineKeyboardMarkup(keyboard)
        self._special_handlers = special_handlers

    def keyboard(self, message: Message) -> InlineKeyboardMarkup:
        return self._keyboard

    def handle(self, update: Update, data: str):
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

    def handle_add(self, update: Update) -> str:
        state = _records_handle_add(self.state_name, update)
        return state.state(
            update.callback_query.message,
            "",
            True,
        )


class ListRecordsView(View):
    def __init__(self, state_name: str, table_name) -> None:
        super().__init__(state_name)
        self.table_name = table_name
        self.handle_anything = True

    def state_name_text(self, telegram_user: TelegramUser):
        return f"{translate(self.table_name)} > {translate('_HEADER_RECORDS')}"

    def state_text(self, telegram_user):
        text = _records_state_text(self.table_name, telegram_user)

        report = database_views[self.table_name].report
        if report:
            data = DATABASE_DRIVER.get_report(
                telegram_user.last_query[0],
                telegram_user.last_query[1],
                report.select,
                report.group_by,
                report.order_by,
                [],
            )
            text += "\n\n" + report.local_display(data)

        return text

    def keyboard(self, message: Message) -> InlineKeyboardMarkup:
        keyboard = _records_keyboard(self.table_name, [], message)
        keyboard.append([back_button, home_button, add_button])

        return InlineKeyboardMarkup(keyboard)

    def handle(self, update: Update, data: str):
        telegram_users[update.callback_query.message.chat.id].records[
            self.table_name
        ] = _get_records(
            _get_records_query(
                table_name=self.table_name, record_ids=[data], no_join=True
            )
        )[
            0
        ]
        telegram_users[update.callback_query.message.chat.id].records_data[
            self.table_name
        ] = _get_records(
            _get_records_query(
                table_name=self.table_name,
                external=telegram_users[update.callback_query.message.chat.id].records[
                    self.table_name
                ],
            )
        )[
            0
        ]
        return conversation_views[self.table_name + "_RECORD"].state(
            update.callback_query.message,
            "",
            True,
        )

    def handle_pagination(self, update: Update, data: str):
        options_changed = _records_handle_pagination(self.table_name, update, data)

        print(
            print_label,
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

    def handle_add(self, update: Update) -> str:
        state = _records_handle_add(self.table_name, update)
        return state.state(
            update.callback_query.message,
            "",
            True,
        )

    def handle_typed(self, update: Update, data: str):
        return _records_handle_typed(
            self.state_name,
            self.table_name,
            update,
            telegram_users[update.message.chat.id],
            data,
        )


class RecordView(View):
    def __init__(self, state_name: str, table_name) -> None:
        super().__init__(state_name)
        operational_states[state_name] = self
        self.table_name = table_name
        self.handle_anything = True

    def state_name_text(self, telegram_user: TelegramUser):
        # record_data = telegram_user.records_data[self.table_name]
        # return f"{translate(self.table_name, self.table_name)} > {'id' in record_data and ('ID ' + str(record_data['id'])) or translate('_HEADER_NEW', '_HEADER_NEW')}"
        return f"{translate(self.table_name)} > {translate('_RECORD')}"

    def record_display(self, record):
        return database_views[self.table_name].extended_display(record) or str(
            record.get("id", "?")
        )

    def state_text(self, telegram_user):
        record_data = telegram_user.records_data[self.table_name]

        text = [
            self.record_display(record_data),
        ]

        report_links = database_views[self.table_name].report_links

        if "id" in record_data and report_links and len(report_links) > 0:
            for report_link in report_links:
                linked_report_query: tuple[str, list[Any]] = _get_records_query(
                    table_name=report_link.table
                )
                report = database_views[report_link.table].report
                if report:
                    conditions = [f"{report_link.link_by} = {record_data['id']}"]
                    if report.foreign_date:
                        conditions.append(
                            f"{report.foreign_date} >= {date_utils.get_current_month_first_day_timestamp()}"
                        )

                    data = DATABASE_DRIVER.get_report(
                        linked_report_query[0],
                        linked_report_query[1],
                        report.select,
                        report.group_by,
                        report.order_by,
                        conditions,
                    )
                    report_text = report.foreign_display(data)
                    if report_text:
                        text.append(report_text)

        extra_info = database_views[self.table_name].extra_info
        if extra_info:
            for row in extra_info:
                text.append(row(record_data))

        return "\n\n".join(text)

    def keyboard(self, message: Message) -> InlineKeyboardMarkup:
        record_data = telegram_users[message.chat.id].records_data[self.table_name]

        keyboard = []

        for column in database_views[self.table_name].columns:
            text = translate(f"{self.table_name}_PARAM_{column['column']}")
            line = []
            if (
                column["column"]
                in telegram_users[message.chat.id].records[self.table_name]
                and telegram_users[message.chat.id].records[self.table_name][
                    column["column"]
                ]
            ):
                if column["type"] == "data":
                    line.append(
                        InlineKeyboardButton(
                            callback_data=f"jump__{column['data_type']}__{record_data[column['column']]}",
                            text=f"{translate('_GO_TO')}: {text}",
                        )
                    )
                    line.append(
                        InlineKeyboardButton(
                            callback_data=f"filter__stay__{self.table_name}__{column['column']}__equals__{record_data[column['column']]}",
                            text=f"{translate('_FILTER_BY')}: {text}",
                        )
                    )
                elif "filtrable" in column and column["filtrable"]:
                    line.append(
                        InlineKeyboardButton(
                            callback_data=f"filter__stay__{self.table_name}__{column['column']}__equals__{record_data[column['column']]}",
                            text=f"{translate('_FILTER_BY')}: {text}",
                        )
                    )

            if len(line):
                keyboard.append(line)

        for database in database_views:
            if self.table_name != database:
                for column in database_views[database].columns:
                    if (
                        column["type"] == "data"
                        and column["data_type"] == self.table_name
                    ):
                        text1 = translate(f"{database}")
                        text2 = translate(f"{database}_PARAM_{column['column']}")
                        keyboard.append(
                            [
                                InlineKeyboardButton(
                                    callback_data=f"filter__jump__{database}__{column['column']}__equals__{record_data['id']}",
                                    text=f"{translate('_GO_TO')}: {text1} ({text2})",
                                )
                            ]
                        )

        actions = database_views[self.table_name].actions
        if actions:
            for index, action in enumerate(actions):
                if (
                    "conditions" not in action
                    or action["conditions"]
                    and action["conditions"](record_data)
                ):
                    keyboard.append(
                        [
                            InlineKeyboardButton(
                                callback_data=f"action__{index}",
                                text=translate(
                                    f"{self.table_name}_ACTION_{action['name']}",
                                ),
                            )
                        ]
                    )

        controls = [back_button, home_button, edit_button]

        keyboard.append(controls)

        return InlineKeyboardMarkup(keyboard)

    def handle_jump(self, update: Update, jump_table, jump_record_id):
        telegram_users[update.callback_query.message.chat.id].records[
            jump_table
        ] = _get_records(
            _get_records_query(
                table_name=jump_table,
                record_ids=[jump_record_id],
                no_join=True,
            )
        )[
            0
        ]
        telegram_users[update.callback_query.message.chat.id].records_data[
            jump_table
        ] = _get_records(
            _get_records_query(
                table_name=jump_table,
                external=telegram_users[update.callback_query.message.chat.id].records[
                    jump_table
                ],
            )
        )[
            0
        ]
        return conversation_views[jump_table + "_RECORD"].state(
            update.callback_query.message,
            "",
            True,
        )

    def handle_filter(self, update: Update, action, filter_table, a1, a2, a3):
        telegram_users[update.callback_query.message.chat.id].filters[filter_table] = (
            [f"{a1} = ?"],
            [a3],
        )
        pagination = telegram_users[
            update.callback_query.message.chat.id
        ].get_pagination(filter_table)
        pagination.offset = 0
        pagination.total = -1
        return conversation_views[filter_table + "_RECORDS"].state(
            update.callback_query.message,
            "",
            True,
        )

    def handle_action(self, update: Update, action_id):
        actions = database_views[self.table_name].actions
        if actions:
            action = actions[action_id]
            action["process"](
                telegram_users[update.callback_query.message.chat.id].records_data[
                    self.table_name
                ]
            )
            pagination = telegram_users[
                update.callback_query.message.chat.id
            ].get_pagination(self.table_name)
            # pagination.offset = 0
            pagination.total = -1
            return self.go_back(
                update, telegram_users[update.callback_query.message.chat.id]
            )

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

    def state_name_text(self, telegram_user: TelegramUser):
        return f"{translate(self.table_name)} > {translate('_HEADER_FAST_TYPE')}"

    def state_text(self, telegram_user) -> str:
        return translate("_FAST_TYPE")

    def keyboard(self, message: Message) -> InlineKeyboardMarkup:
        keyboard = []

        keyboard.append(
            [
                InlineKeyboardButton(
                    callback_data="_ALL",
                    text=translate("_FAST_TYPE_ALL"),
                ),
                InlineKeyboardButton(
                    callback_data="_REQUIRED",
                    text=translate("_FAST_TYPE_REQUIRED"),
                ),
                InlineKeyboardButton(
                    callback_data="_NONE",
                    text=translate("_FAST_TYPE_NONE"),
                ),
            ]
        )

        controls = [back_button, home_button]

        keyboard.append(controls)

        return InlineKeyboardMarkup(keyboard)

    def handle(self, update: Update, data: str):
        if data == "_ALL":
            pass
        elif data == "_REQUIRED":
            telegram_users[update.callback_query.message.chat.id].ignore_fast[
                self.table_name
            ] = {}
            telegram_users[update.callback_query.message.chat.id].ignore_fast[
                self.table_name
            ]["_NON_REQUIRED"] = True
        elif data == "_NONE":
            telegram_users[update.callback_query.message.chat.id].ignore_fast[
                self.table_name
            ] = {}
            telegram_users[update.callback_query.message.chat.id].ignore_fast[
                self.table_name
            ]["_EVERYTHING"] = True
        return check_record_params(
            conversation_views[f"{self.table_name}_EDIT"],
            telegram_users[update.callback_query.message.chat.id],
        ).state(
            update.callback_query.message,
            "",
            True,
        )

    def handle_typed(self, update: Update, data: str):
        if (
            database_views[self.table_name].fast_type
            and database_views[self.table_name].fast_type == "required"
        ):
            telegram_users[update.message.chat.id].ignore_fast[self.table_name] = {}
            telegram_users[update.message.chat.id].ignore_fast[self.table_name][
                "_NON_REQUIRED"
            ] = True
        proc = database_views[self.table_name].fast_type_processor
        if proc is not None:
            result = proc(data)
            print(print_label, "handle_typed", "result", result)
            if result[0]:
                if self.table_name in telegram_users[update.message.chat.id].records:
                    telegram_users[update.message.chat.id].records[
                        self.table_name
                    ].update(result[0])
                else:
                    telegram_users[update.message.chat.id].records[
                        self.table_name
                    ] = result[0]
                telegram_users[update.message.chat.id].records_data[
                    self.table_name
                ] = _get_records(
                    _get_records_query(
                        table_name=self.table_name,
                        external=telegram_users[update.message.chat.id].records[
                            self.table_name
                        ],
                    )
                )[
                    0
                ]
            if result[1]:
                telegram_users[update.message.chat.id].records_extra[
                    self.table_name
                ] = result[1]
                telegram_users[update.message.chat.id].filters = {}
                for filter_table in result[1]:
                    telegram_users[update.message.chat.id].filters[
                        filter_table
                    ] = result[1][filter_table]
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
            elif column["type"] == "year_month":
                EditDateYearMonthRecordValueView(code, state_name, table_name, column)
            elif column["type"] == "date":
                EditDateRecordValueView(code, state_name, table_name, column)
            elif column["type"] == "timestamp":
                EditTimestampRecordValueView(code, state_name, table_name, column)
            else:
                EditTextRecordValueView(code, state_name, table_name, column)

    def state_name_text(self, telegram_user: TelegramUser):
        record_data = telegram_user.records_data[self.table_name]

        return f"{translate(self.table_name)} > {'id' in record_data and (translate('_HEADER_EDIT') + ' ID ' + str(record_data['id'])) or translate('_HEADER_NEW')}"

    def record_display(self, record):
        print(print_label, self.table_name, str(record.get("id", "?")))
        return database_views[self.table_name].extended_display(record) or str(
            record.get("id", "?")
        )

    def state_text(self, telegram_user):
        record_data = telegram_user.records_data[self.table_name]
        return self.record_display(record_data)

    def keyboard(self, message: Message) -> InlineKeyboardMarkup:
        keyboard = []

        display_submit = True

        for column in database_views[self.table_name].columns:
            code = f"{self.table_name}_PARAM_{column['column']}"
            code_text = f"{self.table_name}_PARAM_{column['column']}"
            text = translate(code_text)
            if column["column"] in telegram_users[message.chat.id].records[
                self.table_name
            ] and (
                telegram_users[message.chat.id].records[self.table_name][
                    column["column"]
                ]
                or telegram_users[message.chat.id].records[self.table_name][
                    column["column"]
                ]
                == 0
                or telegram_users[message.chat.id].records[self.table_name][
                    column["column"]
                ]
                == False
            ):
                value = telegram_users[message.chat.id].records[self.table_name][
                    column["column"]
                ]
                if column["type"] == "date":
                    date_timestamp = datetime.fromtimestamp(value)
                    date_string = f"{date_timestamp.strftime('%Y-%m-%d (%a)')}, {date_utils.get_relative_timestamp_text(value)}"
                    text = f"{text} [{date_string}]"
                elif column["type"] == "timestamp":
                    date_timestamp = datetime.fromtimestamp(value)
                    date_string = f"{date_timestamp.strftime('%a, %Y-%m-%d %H:%M:%S')}, {date_utils.get_relative_date_text(date_timestamp, today=datetime.today())}"
                    text = f"{text} [{date_string}]"
                elif column["type"] == "year_month":
                    date_timestamp = datetime.fromtimestamp(value)
                    date_string = f"{date_timestamp.strftime('%Y-%m')}"
                    text = f"{text} [{date_string}]"
                elif column["type"] == "data":
                    relevant = {
                        k.replace(column["column"] + "__", ""): v
                        for k, v in telegram_users[message.chat.id]
                        .records_data[self.table_name]
                        .items()
                        if k.startswith(column["column"] + "__")
                    }
                    text_value = database_views[column["data_type"]].inline_display(
                        relevant
                    )
                    text = f"{text} [{str(text_value)}]"
                else:
                    text = f"{text} [{str(value)}]"
            elif "skippable" not in column or not column["skippable"]:
                display_submit = False

            keyboard.append(
                [
                    InlineKeyboardButton(
                        callback_data=code,
                        text=text,
                    )
                ]
            )

        controls = []
        # if telegram_users[message.chat.id].is_operational():
        controls.append(back_button)
        controls.append(home_button)
        controls.append(cancel_button)
        if display_submit:
            controls.append(submit_button)

        keyboard.append(controls)

        return InlineKeyboardMarkup(keyboard)

    def handle(self, update: Update, data: str):
        return conversation_views[data].state(
            update.callback_query.message,
            "",
            True,
        )

    def handle_cancel(self, update: Update):
        print(print_label, "cancel from EditRecordView")
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
            if database_views[self.table_name].extended_display:
                send_info_message(
                    database_views[self.table_name].extended_display(
                        telegram_users[
                            update.callback_query.message.chat.id
                        ].records_data[self.table_name]
                    )
                )

        for column in database_views[self.table_name].columns:
            if column["type"] == "data" and column["column"] in record:
                DATABASE_DRIVER.update_entry_usage(
                    column["data_type"], record[column["column"]]
                )

        telegram_users[update.callback_query.message.chat.id].clear_edits(
            self.table_name
        )
        return conversation_views[state].state(
            update.callback_query.message,
            f"✅ {translate('_RECORD_ADDED')}",
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
        self._help_text = _input_value_text(column)

    def state_name_text(self, telegram_user: TelegramUser):
        record_data = telegram_user.records_data[self.table_name]
        return f"{translate(self.table_name)} > {'id' in record_data and (translate('_HEADER_EDIT') + ' ID ' + str(record_data['id'])) or translate('_HEADER_NEW')}"

    def record_display(self, record):
        print(print_label, self.table_name, str(record.get("id", "?")))
        return database_views[self.table_name].extended_display(record) or str(
            record.get("id", "?")
        )

    def state_text(self, telegram_user):
        record_data = telegram_user.records_data[self.table_name]
        param = f"{self.table_name}_PARAM_{self.column['column']}"
        return f"{self.record_display(record_data)}\n\n<b><u>{translate(param)}</u></b>: {self._help_text}"

    def _keyboard_controls(self, telegram_user, add=False):
        controls = []
        # if telegram_user.is_operational():
        controls.append(back_button)
        controls.append(home_button)
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

    def verify_next(self, message: Message, data: str, edit: bool):
        check_record_params(
            conversation_views[self.parent_state_name],
            telegram_users[message.chat.id],
        )
        if (
            self.column["type"] == "int"
            or self.column["type"] == "data"
            or self.column["type"] == "date"
            or self.column["type"] == "timestamp"
            or self.column["type"] == "year_month"
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
            _get_records_query(
                table_name=self.table_name,
                external=telegram_users[message.chat.id].records[self.table_name],
            )
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
                _get_records_query(
                    table_name=self.table_name,
                    external=telegram_users[message.chat.id].records[self.table_name],
                )
            )[
                0
            ]

        state = check_record_params(
            conversation_views[self.parent_state_name],
            telegram_users[message.chat.id],
        )
        print(print_label, "next state is " + state.state_name)
        return state.state(
            message,
            f"{translate('_RECORD_PARAM_ADDED')}: {self.column['type']} <b>{data}</b> ({self.column['column']})",
            edit,
        )

    def handle(self, update: Update, data: str):
        return self.verify_next(update.callback_query.message, data, True)

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
            f"⚠️ {translate('_RECORD_PARAM_CLEARED')}: {self.column['column']}",
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
            f"{translate('_RECORD_PARAM_SKIPPED')}: {self.column['column']}",
            True,
        )

    def handle_cancel(self, update: Update):
        print(print_label, "cancel from EditRecordView")
        telegram_users[update.callback_query.message.chat.id].clear_edits(
            self.table_name
        )

    def handle_typed(self, update: Update, data: str):
        return self.verify_next(update.message, data, False)


class EditTextRecordValueView(EditRecordValueView):
    def __init__(
        self, state_name: str, parent_state_name: str, table_name, column
    ) -> None:
        super().__init__(state_name, parent_state_name, table_name, column)
        self.freqValues = []
        self._help_text = _input_value_text(column)

    def keyboard(self, message: Message) -> InlineKeyboardMarkup:
        keyboard = []

        if (
            "request_frequent_data" in self.column
            and self.column["request_frequent_data"]
        ):
            where_clause = []
            if (
                "frequent_data_lookup" in self.column
                and self.column["frequent_data_lookup"]
            ):
                for lookup_column in self.column["frequent_data_lookup"]:
                    if (
                        lookup_column
                        in telegram_users[message.chat.id].records[self.table_name]
                        and telegram_users[message.chat.id].records[self.table_name][
                            lookup_column
                        ]
                    ):
                        where_clause.append(
                            f"{lookup_column} = {telegram_users[message.chat.id].records[self.table_name][lookup_column]}"
                        )
            self.freqValues = DATABASE_DRIVER.get_data(
                f"SELECT [{self.column['column']}] AS freqValue, COUNT([{self.column['column']}]) AS freqCount FROM {self.table_name} {where_clause and ('WHERE ' + ' AND '.join(where_clause)) or ''} GROUP BY freqValue ORDER BY freqCount DESC LIMIT ?",
                [15],
            )

            for index, freqValue in enumerate(self.freqValues):
                if not keyboard or len(keyboard[-1]) >= 3:
                    keyboard.append([])

                keyboard[-1].append(
                    InlineKeyboardButton(
                        callback_data=str(index),
                        text=f"{freqValue['freqValue']} ({freqValue['freqCount']})",
                    )
                )

        controls = self._keyboard_controls(telegram_users[message.chat.id])
        keyboard.append(controls)

        return InlineKeyboardMarkup(keyboard)

    def handle(self, update: Update, data: str):
        return self.verify_next(
            update.callback_query.message, self.freqValues[int(data)]["freqValue"], True
        )


class EditBooleanRecordValueView(EditRecordValueView):
    def __init__(
        self, state_name: str, parent_state_name: str, table_name, column
    ) -> None:
        super().__init__(state_name, parent_state_name, table_name, column)

        self._help_text = _input_value_text(column)

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
        self._help_text = _input_value_text(column)

    def keyboard(self, message: Message) -> InlineKeyboardMarkup:
        keyboard = []

        for selectee in self.column["select"]:
            keyboard.append(
                [
                    InlineKeyboardButton(
                        callback_data=selectee,
                        text=(
                            "select_key" in self.column
                            and translate(
                                f"SELECT_{self.column['select_key']}_{selectee}",
                            )
                            or selectee
                        ),
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
        self._help_text = _input_value_text(column)

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

    def handle_pagination(self, update: Update, data: str):
        options_changed = _records_handle_pagination(
            self.column["data_type"], update, data
        )

        if options_changed:
            return conversation_views[self.state_name].state(
                update.callback_query.message,
                "",
                True,
            )

    def handle_add(self, update: Update) -> str:
        state = _records_handle_add(self.column["data_type"], update)
        print(print_label, state)
        return state.state(
            update.callback_query.message,
            "",
            True,
        )

    def handle_typed(self, update: Update, data: str):
        return _records_handle_typed(
            self.state_name,
            self.column["data_type"],
            update,
            telegram_users[update.message.chat.id],
            data,
        )


class EditDateYearMonthRecordValueView(EditRecordValueView):
    def __init__(
        self, state_name: str, parent_state_name: str, table_name, column
    ) -> None:
        super().__init__(state_name, parent_state_name, table_name, column)
        self.future: bool = (
            column and "future" in column and column["future"] and True or False
        )
        self._help_text = _input_value_text(column)

    def current_timestamp(self):
        return date_utils.get_current_month_first_day()

    def keyboard(self, message: Message) -> InlineKeyboardMarkup:
        keyboard = []

        today = self.current_timestamp()

        year = today.year - telegram_users[message.chat.id].date_offset

        line = []

        for date in date_utils.year_month_range((year, 1), (year, 12)):
            date_string = f"{date.strftime('%Y-%m')}"
            line.append(
                InlineKeyboardButton(
                    date_string,
                    callback_data=int(date.timestamp()),
                )
            )
            if len(line) == 4:
                keyboard.append(line)
                line = []

        keyboard.append(
            [
                InlineKeyboardButton(
                    ("◀️ " + str(year - 1)), callback_data="_DATE_BACKWARD"
                ),
                InlineKeyboardButton(
                    (year != today.year) and translate("_TODAY") or "🚫",
                    callback_data="_DATE_TODAY",
                ),
                InlineKeyboardButton(
                    (year > 0 or self.future) and (str(year + 1) + " ▶️") or "🚫",
                    callback_data="_DATE_FORWARD",
                ),
            ]
        )

        controls = self._keyboard_controls(telegram_users[message.chat.id])
        keyboard.append(controls)

        return InlineKeyboardMarkup(keyboard)

    def handle_date(self, update: Update, data: str):
        options_changed = False
        date_button = False

        if data == "_DATE_TODAY":
            if telegram_users[update.callback_query.message.chat.id].date_offset != 0:
                options_changed = True
                telegram_users[update.callback_query.message.chat.id].date_offset = 0
        elif data == "_DATE_BACKWARD":
            options_changed = True
            telegram_users[update.callback_query.message.chat.id].date_offset += 1
        elif data == "_DATE_FORWARD":
            if (
                telegram_users[update.callback_query.message.chat.id].date_offset > 0
                or self.future
            ):
                telegram_users[update.callback_query.message.chat.id].date_offset -= 1
                if (
                    telegram_users[update.callback_query.message.chat.id].date_offset
                    < 0
                    and not self.future
                ):
                    telegram_users[
                        update.callback_query.message.chat.id
                    ].date_offset = 0
                else:
                    options_changed = True
        else:
            date_button = True

        if options_changed:
            return conversation_views[self.state_name].state(
                update.callback_query.message,
                "",
                True,
            )
        elif date_button:
            return self.verify_next(update.callback_query.message, data, True)

    def handle_typed(self, update: Update, data: str):
        try:
            date = datetime.strptime(data, "%Y-%m").timestamp()
            return self.verify_next(update.message, str(int(date)), False)
        except:
            return conversation_views[self.state_name].state(
                update.message,
                f"{translate('_DATE_WRONG')} YYYY-MM",
                False,
            )


class EditDateRecordValueView(EditRecordValueView):
    def __init__(
        self, state_name: str, parent_state_name: str, table_name, column
    ) -> None:
        super().__init__(state_name, parent_state_name, table_name, column)
        self.future: bool = (
            column and "future" in column and column["future"] and True or False
        )
        self._help_text = _input_value_text(column)

    def current_timestamp(self):
        return date_utils.get_today_midnight()

    def keyboard(self, message: Message) -> InlineKeyboardMarkup:
        keyboard = []

        date_offset = telegram_users[message.chat.id].date_offset

        today = self.current_timestamp()

        dates = date_utils.date_range(
            today - timedelta(days=(date_offset * 3 + 2)),
            today - timedelta(days=(date_offset * 3)),
        )

        for date in dates:
            date_string = f"{date.strftime('%Y-%m-%d (%a)')}, {date_utils.get_relative_timestamp_text(date.timestamp(), today=today)}"
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
                    (date_offset != 0) and "Last 3d" or "🚫",
                    callback_data="_DATE_TODAY",
                ),
                InlineKeyboardButton(
                    (date_offset > 0 or self.future) and "▶️" or "🚫",
                    callback_data="_DATE_FORWARD",
                ),
                # InlineKeyboardButton(date_offset > 2 and "⏩" or "🚫", callback_data="_DATE_REWIND_FORWARD"),
            ]
        )

        controls = self._keyboard_controls(telegram_users[message.chat.id])
        keyboard.append(controls)

        return InlineKeyboardMarkup(keyboard)

    def handle_date(self, update: Update, data: str):
        options_changed = False
        date_button = False

        if data == "_DATE_TODAY":
            if telegram_users[update.callback_query.message.chat.id].date_offset != 0:
                options_changed = True
                telegram_users[update.callback_query.message.chat.id].date_offset = 0
        elif data == "_DATE_BACKWARD":
            options_changed = True
            telegram_users[update.callback_query.message.chat.id].date_offset += 1
        elif data == "_DATE_FORWARD":
            if (
                telegram_users[update.callback_query.message.chat.id].date_offset > 0
                or self.future
            ):
                telegram_users[update.callback_query.message.chat.id].date_offset -= 1
                if (
                    telegram_users[update.callback_query.message.chat.id].date_offset
                    < 0
                    and not self.future
                ):
                    telegram_users[
                        update.callback_query.message.chat.id
                    ].date_offset = 0
                else:
                    options_changed = True
        else:
            date_button = True

        if options_changed:
            return conversation_views[self.state_name].state(
                update.callback_query.message,
                "",
                True,
            )
        elif date_button:
            return self.verify_next(update.callback_query.message, data, True)

    def handle_typed(self, update: Update, data: str):
        try:
            date = datetime.strptime(data, "%Y-%m-%d").timestamp()
            return self.verify_next(update.message, str(int(date)), False)
        except:
            return conversation_views[self.state_name].state(
                update.message,
                f"{translate('_DATE_WRONG')} YYYY-MM-DD",
                False,
            )


class EditTimestampRecordValueView(EditDateRecordValueView):
    def __init__(
        self, state_name: str, parent_state_name: str, table_name, column
    ) -> None:
        super().__init__(state_name, parent_state_name, table_name, column)

    def current_timestamp(self):
        return datetime.today()

    def handle_typed(self, update: Update, data: str):
        try:
            date = datetime.strptime(data, "%Y-%m-%d %H:%M:%S").timestamp()
            return self.verify_next(update.message, str(int(date)), False)
        except:
            try:
                date = datetime.strptime(data, "%Y-%m-%d").timestamp()
                return self.verify_next(update.message, str(int(date)), False)
            except:
                return conversation_views[self.state_name].state(
                    update.message,
                    f"{translate('_DATE_WRONG')} YYYY-MM-DD [HH:MM:SS]",
                    False,
                )


telegram_users: "dict[Any, TelegramUser]" = {}
conversation_views: "dict[str, View]" = {}
database_views: "dict[str, DatabaseView]" = {}

shortcuts = {}

operational_states = {}

# special handlers that don't have view
home_button = InlineKeyboardButton(
    callback_data="_HOME",
    text=translate("_HOME"),
)
back_button = InlineKeyboardButton(
    callback_data="_BACK",
    text=translate("_BACK"),
)
records_button = InlineKeyboardButton(
    callback_data="_RECORDS",
    text=translate("_RECORDS"),
)
add_button = InlineKeyboardButton(
    callback_data="_ADD",
    text=translate("_ADD"),
)
edit_button = InlineKeyboardButton(
    callback_data="_EDIT",
    text=translate("_EDIT"),
)
remove_button = InlineKeyboardButton(
    callback_data="_REMOVE",
    text=translate("_REMOVE"),
)
next_button = InlineKeyboardButton(
    callback_data="_NEXT",
    text=translate("_NEXT"),
)
skip_button = InlineKeyboardButton(
    callback_data="_SKIP",
    text=translate("_SKIP"),
)
cancel_button = InlineKeyboardButton(
    callback_data="_CANCEL",
    text=translate("_CANCEL"),
)
submit_button = InlineKeyboardButton(
    callback_data="_SUBMIT",
    text=translate("_SUBMIT"),
)


def text_filters():
    return Filters.text & auth_filter() & conversation_filter()


def auth_filter():
    return Filters.user(user_id=configs.telegram["authorized"])


def conversation_filter():
    return Filters.chat(chat_id=configs.telegram["authorized"])


def default_display(record) -> str:
    return str("id" in record and record["id"] or "?")


def check_record_params(state, telegram_user: TelegramUser):
    if state.table_name not in telegram_user.records:
        telegram_user.records[state.table_name] = {}
    if state.table_name not in telegram_user.records_data:
        telegram_user.records_data[state.table_name] = dict(
            telegram_user.records[state.table_name]
        )
    if state.table_name not in telegram_user.records_extra:
        telegram_user.records_extra[state.table_name] = {}
    if state.table_name not in telegram_user.ignore_fast:
        telegram_user.ignore_fast[state.table_name] = {}

    pagination = telegram_user.get_pagination(state.table_name)
    pagination.total = -1
    pagination.offset = 0

    if "_EVERYTHING" not in telegram_user.ignore_fast[state.table_name]:
        for column in database_views[state.table_name].columns:
            if column["column"] not in telegram_user.records[state.table_name]:
                if (
                    ("skippable" not in column)
                    or not column["skippable"]  # column["skippable"] == "checking"
                ) or (
                    (
                        "_NON_REQUIRED"
                        not in telegram_user.ignore_fast[state.table_name]
                        or column["skippable"] == "checking"
                    )
                    and (
                        column["column"]
                        not in telegram_user.ignore_fast[state.table_name]
                        or not telegram_user.ignore_fast[state.table_name][
                            column["column"]
                        ]
                    )
                ):
                    print(
                        print_label,
                        "check_record_params",
                        f"{column['column']} is not typed",
                    )
                    return conversation_views[
                        f"{state.table_name}_PARAM_{column['column']}"
                    ]
    print(
        print_label,
        "check_record_params",
        f"everything is typed but {telegram_user.ignore_fast[state.table_name]}",
    )
    return state


# records outer functions to reuse them


def _records_state_text(table_name, telegram_user: TelegramUser):
    filters = telegram_user.get_filters(table_name)
    pagination: Pagination = telegram_user.get_pagination(table_name)
    search: tuple[str, list[str]] = telegram_user.get_search(table_name)

    search_result = (
        search[0] and DATABASE_DRIVER.search([table_name], [search[0]]) or []
    )

    record_ids = [v["entry_id"] for v in search_result]

    query: tuple[str, list[Any]] = _get_records_query(
        table_name=table_name, record_ids=record_ids, conditions=filters
    )
    telegram_user.last_query = query

    if pagination.total == -1:
        pagination.total = DATABASE_DRIVER.get_records_count(
            table_name, query[0], query[1]
        )
    pagination.pages = math.ceil(pagination.total / pagination.limit)
    text = (
        pagination.total > 0
        and (
            f"{translate('_RECORD_DISPLAY')}: <b>{pagination.offset+1}-{min(pagination.offset+pagination.limit, pagination.total)}</b> / <b>{pagination.total}</b>"
        )
        or translate("_RECORD_NO_DISPLAY")
    )
    if len(filters[0]):
        text = f"{text}\n{translate('_RECORDS_FILTERS')}: {len(filters[0])}"
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


def _get_records_query(
    table_name=None,
    external=None,
    record_ids=None,
    no_join=None,
    conditions: tuple[list[str], list[Any]] | None = None,
    ignore_order=None,
):
    table_select = []
    join_select = []
    search_columns = []

    if table_name:
        if not external or ("id" in external and external["id"]):
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

    order_by = (
        table_name
        and not ignore_order
        and list(database_views[table_name].order_by)
        or []
    )

    if table_name and not external and not no_join and not ignore_order:
        linked_tables.append(
            {
                "custom": f'LEFT JOIN entries_usage ON entries_usage.table_name = "{table_name}" AND entries_usage.entry_id = {table_name}.id'
            }
        )
        order_by.insert(0, ("entries_usage.last_date", True, None))

    query = DATABASE_DRIVER.get_records_query(
        table=table_name,
        table_select=table_select,
        external=external,
        join=linked_tables,
        join_select=join_select,
        order_by=order_by,  # type: ignore
        conditions=conditions,
        record_ids=record_ids,
    )

    return query


def _get_records(
    query,
    pagination=None,
):
    result = DATABASE_DRIVER.get_records(
        query[0],
        query[1],
        offset=pagination and pagination.offset,
        limit=pagination and pagination.limit,
    )

    return result


def _records_keyboard(table_name, keyboard, message: Message):
    filters = telegram_users[message.chat.id].get_filters(table_name)
    pagination = telegram_users[message.chat.id].get_pagination(table_name)
    search = telegram_users[message.chat.id].get_search(table_name)

    clear_line = []

    if len(search[0]):
        clear_line.append(
            InlineKeyboardButton(
                callback_data="_CLEAR_SEARCH",
                text=f"{translate('_CLEAR_SEARCH')}: {search[0]}",
            )
        )

    if len(filters[0]):
        clear_line.append(
            InlineKeyboardButton(
                callback_data="_CLEAR_FILTERS",
                text=translate("_CLEAR_FILTERS"),
            )
        )

    if len(clear_line):
        keyboard.append(clear_line)

    records = _get_records(
        telegram_users[message.chat.id].last_query, pagination=pagination
    )
    for record in records:
        keyboard.append(
            [
                InlineKeyboardButton(
                    callback_data=record["id"],
                    text=database_views[table_name].inline_display(record)
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

    if pagination.total > 0:
        extra_buttons = [
            # InlineKeyboardButton(
            #     translate("_RECORDS_FILTERS", "filters"),
            #     callback_data="_RECORDS_FILTERS",
            # ),
            # InlineKeyboardButton(
            #     translate("_RECORDS_SORT"),
            #     callback_data="_RECORDS_SORT",
            # ),
        ]

        # report_links = database_views[table_name].report_links
        # if report_links and len(report_links) > 0:
        #     extra_buttons.append(
        #         InlineKeyboardButton(
        #             f"📊 Overlays ({len(report_links)})",
        #             callback_data="_REPORT_LAYERS",
        #         )
        #     )

        if len(extra_buttons):
            keyboard.append(extra_buttons)
    return keyboard


def _records_handle_pagination(table_name, update: Update, data: str):
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
                pagination.offset + pagination.limit, pagination.total
            )
    elif data == "_PAGE_FASTFORWARD":
        if pagination.offset < pagination.total:
            options_changed = True
            pagination.offset = (
                math.floor(pagination.total / pagination.limit) * pagination.limit
            )
    elif data == "_CLEAR_SEARCH":
        options_changed = True
        pagination.offset = 0
        pagination.total = -1
        telegram_users[update.callback_query.message.chat.id].search[table_name] = (
            "",
            list(),
        )
    elif data == "_CLEAR_FILTERS":
        options_changed = True
        pagination.offset = 0
        pagination.total = -1
        telegram_users[update.callback_query.message.chat.id].filters[table_name] = (
            list(),
            list(),
        )

    return options_changed


def _records_handle_add(table_name, update: Update):
    telegram_users[update.callback_query.message.chat.id].clear_edits(table_name)
    for column in database_views[table_name].columns:
        if "autoset" in column and column["autoset"]:
            if (
                table_name
                not in telegram_users[update.callback_query.message.chat.id].records
            ):
                telegram_users[update.callback_query.message.chat.id].records[
                    table_name
                ] = {}

            telegram_users[update.callback_query.message.chat.id].records[table_name][
                column["column"]
            ] = column["autoset"]()
    fast_type_processor = database_views[table_name].fast_type_processor
    if fast_type_processor:
        return conversation_views[f"{table_name}_FAST_TYPE"]
    else:
        if (
            database_views[table_name].fast_type
            and database_views[table_name].fast_type == "required"
        ):
            telegram_users[update.callback_query.message.chat.id].ignore_fast[
                table_name
            ] = {}
            telegram_users[update.callback_query.message.chat.id].ignore_fast[
                table_name
            ]["_NON_REQUIRED"] = True
        return check_record_params(
            conversation_views[f"{table_name}_EDIT"],
            telegram_users[update.callback_query.message.chat.id],
        )


def _records_handle_typed(
    state_name,
    table_name,
    update: Update,
    telegram_user: TelegramUser,
    data,
):
    search = telegram_user.get_search(table_name)
    print(print_label, "_records_handle_typed", str(search[0]), "-", data)
    if search[0] != data:
        telegram_user.search[table_name] = (
            data,
            [],  # string_utils.sql_search(data)
        )
        pagination = telegram_user.get_pagination(table_name)
        pagination.offset = 0
        pagination.total = -1
        return conversation_views[state_name].state(
            update.message,
            "",
            False,
        )


def _input_value_text(column):
    actions = []
    if column["type"] != "data":
        actions.append(translate("_INPUT_VALUE_ACTION_enter"))
    if (
        ("request_frequent_data" in column and column["request_frequent_data"])
        or column["type"] == "select"
        or column["type"] == "data"
        or column["type"] == "date"
        or column["type"] == "timestamp"
        or column["type"] == "year_month"
    ):
        actions.append(translate("_INPUT_VALUE_ACTION_select"))
    if "skippable" in column and column["skippable"]:
        actions.append(translate("_INPUT_VALUE_ACTION_skip"))

    if column["type"] == "text":
        column_type = "text"
    elif column["type"] == "boolean":
        column_type = "boolean"
    elif column["type"] == "select":
        column_type = "select"
    elif column["type"] == "data":
        column_type = "data"
    elif (
        column["type"] == "date"
        or column["type"] == "timestamp"
        or column["type"] == "year_month"
    ):
        column_type = "date"
    else:
        column_type = "value"

    return "/".join(actions) + " " + translate("_INPUT_VALUE_TYPE_" + column_type)


def revalidate_search_cache():
    for db_name in database_views:
        query: tuple[str, list[Any]] = _get_records_query(
            table_name=db_name, no_join=True, ignore_order=True
        )
        records = DATABASE_DRIVER.get_records(query[0], query[1])
        for record in records:
            DATABASE_DRIVER._revalidate_search_cache(db_name, record["id"], record)
    DATABASE_DRIVER.commit()
