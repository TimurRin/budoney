from collections import deque
from typing import Any
from telegram import (
    InlineKeyboardButton, InlineKeyboardMarkup, Message, Update)
from telegram.ext import CallbackContext, CallbackQueryHandler

print_label: str = "[budoney :: Telegram Interface :: Classes]"


class TelegramUser:
    name: str = "User"
    states_sequence = deque()
    transaction = {}
    merchant = {}
    method = {}
    task_current = {}
    task_scheduled = {}


def state_text_with_extras(telegram_user: TelegramUser, text: str):
    return f"👩‍💻 Debug: states_sequence <code>{str(telegram_user.states_sequence)}</code>\n\n{text}"


class TelegramConversationView:
    def __init__(self, state_name: str, keyboard_data: "list[list[tuple[str, str, TelegramConversationFork]]]") -> None:
        conversation_views[state_name] = self
        self.state_name = state_name
        self.state_id = 0

        keyboard = []
        handlers = []
        simple_handlers = {}

        for keyboard_line_data in keyboard_data:
            keyboard_line = []
            keyboard.append(keyboard_line)
            for key_data in keyboard_line_data:
                keyboard_line.append(InlineKeyboardButton(
                    callback_data=key_data[0], text=(key_data[1] or key_data[0])))
                handler = CallbackQueryHandler(self._simple_handling)
                handlers.append(handler)
                simple_handlers[key_data[0]] = handler

        self._keyboard = InlineKeyboardMarkup(keyboard)
        self.handlers = handlers
        self.simple_handlers = simple_handlers

    def state(self, message: Message, text: str, edit: bool):
        if edit:
            message.edit_text(
                text, reply_markup=self.keyboard(), parse_mode='html')
        else:
            message.reply_text(
                text, reply_markup=self.keyboard(), parse_mode='html')
        return self.state_name

    def keyboard(self) -> InlineKeyboardMarkup:
        return self._keyboard

    def _simple_handling(self, update: Update, context: CallbackContext):
        data: str = update.callback_query.data
        # , show_alert = True, text="okay"
        context.bot.answer_callback_query(
            callback_query_id=update.callback_query.id, show_alert=False, text=("state: " + data))

        telegram_user = telegram_users[update.callback_query.message.chat.id]

        print(print_label, self.state_name, update.callback_query.from_user.first_name,
              update.callback_query.from_user.id)

        if data == "_BACK":
            if len(telegram_user.states_sequence) > 0:
                state = telegram_user.states_sequence.pop()
            else:
                state = "main"
            return conversation_views[state].state(
                update.callback_query.message,
                state_text_with_extras(telegram_user, f"Nice to have you back at '<b>{state}</b>' state"), True)
        else:
            telegram_user.states_sequence.append(self.state_name)
            if data in conversation_views:
                return conversation_views[data].state(
                    update.callback_query.message,
                    state_text_with_extras(telegram_user, f"Current state is '<b>{data}</b>'"), True)
            else:
                return conversation_views["_WIP"].state(
                    update.callback_query.message, state_text_with_extras(
                        telegram_user,
                        f"⚠️ State '<b>{data}</b>' doesn't exist. Go back to '<b>{telegram_user.states_sequence[-1]}</b>' state"
                    ), True)


class TelegramConversationFork:
    handler_type: str = "none"


class EnumTelegramConversationFork(TelegramConversationFork):
    handler_type = "simple"

    def __init__(self, options: "tuple[str, str]"):
        self.options = options


SIMPLE_FORK = TelegramConversationFork()

telegram_users: "dict[Any, TelegramUser]" = {}
conversation_views: "dict[str, TelegramConversationView]" = {}
