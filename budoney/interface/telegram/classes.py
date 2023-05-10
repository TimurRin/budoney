from collections import deque
from typing import Any
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Message, Update
from telegram.ext import CallbackContext, CallbackQueryHandler, MessageHandler, Filters
from loc import localization
from database import DATABASE_DRIVER
import configs

print_label: str = "[budoney :: Telegram Interface]"


def text_filters():
    return Filters.text & auth_filter() & conversation_filter()


def auth_filter():
    return Filters.user(user_id=configs.telegram["authorized"])


def conversation_filter():
    return Filters.chat(chat_id=configs.telegram["authorized"])


class TelegramUser:
    name: str = "User"
    state: str = "none"
    states_sequence = deque()
    operational_sequence = deque()

    def __init__(self, name: str) -> None:
        self.name = name


class TelegramConversationView:
    def __init__(self, state_name: str) -> None:
        conversation_views[state_name] = self
        self.state_name = state_name
        self.handlers = [
            CallbackQueryHandler(self._handle),
            MessageHandler(text_filters(), self.handle_typed),
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
            + f"{localization['states'].get(self.state_name, self.state_name)}"
        )

        state_text = self.state_text()
        if state_text:
            result_text = result_text + "\n\n" + state_text

        if edit:
            message.edit_text(
                result_text, reply_markup=self.keyboard(), parse_mode="html"
            )
        else:
            message.reply_text(
                result_text, reply_markup=self.keyboard(), parse_mode="html"
            )
        return self.state_name

    def debug_text(self, user):
        if configs.general["production_mode"]:
            return ""

        text = f"👩‍💻 Debug for {user.name}:\n"

        text = text + f"- states_sequence: <code>{str(user.states_sequence)}</code>\n"
        text = (
            text
            + f"- operational_sequence: <code>{str(user.operational_sequence)}</code>\n"
        )

        return text + "\n"

    def state_text(self):
        return ""

    def keyboard(self) -> InlineKeyboardMarkup:
        pass

    def handle(self, update: Update, data):
        pass

    def handle_records(self, update: Update):
        pass

    def handle_add(self, update: Update):
        pass

    def handle_submit(self, update: Update):
        pass

    def handle_typed(self, update: Update, context: CallbackContext):
        print(
            print_label,
            f"{update.message.chat.first_name} ({update.message.chat.id}) has illegaly typed in state {self.state_name}",
        )

    def _handle(self, update: Update, context: CallbackContext):
        data: str = update.callback_query.data
        context.bot.answer_callback_query(callback_query_id=update.callback_query.id)

        telegram_user = telegram_users[update.callback_query.message.chat.id]

        if data == "_BACK":
            if len(telegram_user.operational_sequence) > 0:
                state = telegram_user.operational_sequence.pop()
            elif len(telegram_user.states_sequence) > 0:
                state = telegram_user.states_sequence.pop()
            else:
                state = "main"
            return conversation_views[state].state(
                update.callback_query.message,
                "",
                True,
            )
        elif data == "_SUBMIT":
            telegram_user.operational_sequence.clear()
            if len(telegram_user.states_sequence) > 0:
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
            telegram_user.states_sequence.append(self.state_name)
            if data in conversation_views:
                return self.handle(update, data)
            else:
                return conversation_views["_WIP"].state(
                    update.callback_query.message,
                    f"⚠️ State '<b>{data}</b>' doesn't exist. Go back to '<b>{telegram_user.states_sequence[-1]}</b>' state",
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

    def keyboard(self) -> InlineKeyboardMarkup:
        return self._keyboard

    def handle(self, update: Update, data):
        return conversation_views[data].state(
            update.callback_query.message,
            "",
            True,
        )


class DatabaseTelegramConversationView(TelegramConversationView):
    def __init__(self, state_name: str, columns: list[list]) -> None:
        super().__init__(state_name)

        keyboard = []

        for column in columns:
            if column["type"] == "data":
                code = f"{state_name}_GROUPBY_{column['column']}"
                InfoTelegramConversationView(code, state_name)
                keyboard.append(
                    [
                        InlineKeyboardButton(
                            callback_data=code,
                            text=localization["states"].get(code, code),
                        )
                    ]
                )

        special_handlers = {
            "get_records": GetRecordsTelegramConversationView(
                f"{state_name}_RECORDS", state_name
            ),
            "add_record": AddRecordTelegramConversationView(
                f"{state_name}_ADD", state_name, columns
            ),
        }

        keyboard.append([back_button, records_button, add_button])

        self._keyboard = InlineKeyboardMarkup(keyboard)
        self._special_handlers = special_handlers

    def keyboard(self) -> InlineKeyboardMarkup:
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
        return self._special_handlers["add_record"].state(
            update.callback_query.message,
            "",
            True,
        )


class InfoTelegramConversationView(TelegramConversationView):
    def __init__(self, state_name: str, table_name) -> None:
        super().__init__(state_name)

        keyboard = []

        keyboard.append([back_button])

        self._keyboard = InlineKeyboardMarkup(keyboard)

    def keyboard(self) -> InlineKeyboardMarkup:
        return self._keyboard


class GetRecordsTelegramConversationView(TelegramConversationView):
    def __init__(self, state_name: str, table_name) -> None:
        super().__init__(state_name)
        self.table_name = table_name

    def keyboard(self) -> InlineKeyboardMarkup:
        keyboard = []

        records = DATABASE_DRIVER.get_records(self.table_name)
        for record in records:
            keyboard.append(
                [InlineKeyboardButton(callback_data=record["id"], text=record["id"])]
            )

        keyboard.append([back_button, add_button])

        return InlineKeyboardMarkup(keyboard)

    def handle(self, update: Update, data):
        return conversation_views["_WIP"].state(
            update.callback_query.message,
            "No support for view yet",
            True,
        )

    def handle_add(self, update: Update):
        return conversation_views[f"{self.table_name}_ADD"].state(
            update.callback_query.message,
            "",
            True,
        )


class AddRecordTelegramConversationView(TelegramConversationView):
    def __init__(self, state_name: str, table_name, columns: list[list]) -> None:
        super().__init__(state_name)
        self.table_name = table_name
        keyboard = []

        for column in columns:
            code = f"{state_name}_{column['column']}"
            InfoTelegramConversationView(code, state_name)
            keyboard.append(
                [
                    InlineKeyboardButton(
                        callback_data=code,
                        text=localization["states"].get(code, code),
                    )
                ]
            )

        special_handlers = {}

        keyboard.append([back_button, submit_button])

        self._keyboard = InlineKeyboardMarkup(keyboard)
        self._special_handlers = special_handlers
        self._columns = columns

    def keyboard(self) -> InlineKeyboardMarkup:
        return self._keyboard

    def handle(self, update: Update, data):
        return conversation_views["_WIP"].state(
            update.callback_query.message,
            "No support for change yet",
            True,
        )

    def handle_submit(self, update: Update, state):
        DATABASE_DRIVER.append_data(self.table_name, {})
        return conversation_views[state].state(
            update.callback_query.message,
            "✅ The record has been added successfully",
            True,
        )


telegram_users: "dict[Any, TelegramUser]" = {}
conversation_views: "dict[str, TelegramConversationView]" = {}

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
submit_button = InlineKeyboardButton(
    callback_data="_SUBMIT",
    text=localization["states"].get("_SUBMIT", "_SUBMIT"),
)
