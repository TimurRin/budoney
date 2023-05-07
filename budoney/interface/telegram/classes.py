from collections import deque
from typing import Any
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Message, Update
from telegram.ext import CallbackContext, CallbackQueryHandler
from loc import localization

print_label: str = "[budoney :: Telegram Interface]"


class TelegramUser:
    name: str = "User"
    state: str = "none"
    states_sequence = deque()

    def __init__(self, name: str) -> None:
        self.name = name


class TelegramConversationView:
    def __init__(self, state_name: str) -> None:
        conversation_views[state_name] = self
        self.state_name = state_name
        self.handlers = [CallbackQueryHandler(self._handle)]

    def state(self, message: Message, text: str, edit: bool):
        print(
            print_label,
            f"{message.chat.first_name} ({message.chat.id}) has moved from '{telegram_users[message.chat.id].state}' to '{self.state_name}'",
        )
        telegram_users[message.chat.id].state = self.state_name
        text = f"👩‍💻 Debug for {telegram_users[message.chat.id].name}:\n- states_sequence: <code>{str(telegram_users[message.chat.id].states_sequence)}</code>\n\n{text}"
        if edit:
            message.edit_text(text, reply_markup=self.keyboard(), parse_mode="html")
        else:
            message.reply_text(text, reply_markup=self.keyboard(), parse_mode="html")
        return self.state_name

    def keyboard(self) -> InlineKeyboardMarkup:
        pass

    def handle(self, update: Update, data):
        pass

    def _handle(self, update: Update, context: CallbackContext):
        data: str = update.callback_query.data
        context.bot.answer_callback_query(callback_query_id=update.callback_query.id)

        telegram_user = telegram_users[update.callback_query.message.chat.id]

        if data == "_BACK":
            if len(telegram_user.states_sequence) > 0:
                state = telegram_user.states_sequence.pop()
            else:
                state = "main"
            return conversation_views[state].state(
                update.callback_query.message,
                f"Nice to have you back at '<b>{state}</b>' state",
                True,
            )
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
        forks: "list[list[TelegramConversationFork]]",
    ) -> None:
        super().__init__(state_name)

        keyboard = []

        for forks_line in forks:
            keyboard_line = []
            keyboard.append(keyboard_line)
            for fork in forks_line:
                keyboard_line.append(
                    InlineKeyboardButton(
                        callback_data=fork.name,
                        text=localization["states"].get(fork.name, fork.name),
                    )
                )

        if state_name is not "main":
            keyboard.append([back_button])

        self._keyboard = InlineKeyboardMarkup(keyboard)

    def keyboard(self) -> InlineKeyboardMarkup:
        return self._keyboard

    def handle(self, update: Update, data):
        return conversation_views[data].state(
            update.callback_query.message,
            f"Current state is '<b>{data}</b>'",
            True,
        )


class DatabaseTelegramConversationView(TelegramConversationView):
    def __init__(
        self,
        state_name: str,
    ) -> None:
        super().__init__(state_name)

    def keyboard(self) -> InlineKeyboardMarkup:
        keyboard = []
        keyboard.append([back_button])
        return InlineKeyboardMarkup(keyboard)

    def handle(self, update: Update, data):
        return conversation_views["_WIP"].state(
            update.callback_query.message,
            f"A placeholder for '<b>{data}</b>' database management",
            True,
        )


class TelegramConversationFork:
    name: str = "none"

    def __init__(self, name: str):
        self.name = name


telegram_users: "dict[Any, TelegramUser]" = {}
conversation_views: "dict[str, TelegramConversationView]" = {}
back_button = InlineKeyboardButton(
    callback_data="_BACK",
    text=localization["states"].get("_BACK", "_BACK"),
)
