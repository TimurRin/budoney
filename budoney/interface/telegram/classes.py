from abc import abstractmethod
from collections import deque
from typing import Any
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Message, Update
from telegram.ext import CallbackContext, CallbackQueryHandler, Handler

print_label: str = "[budoney :: Telegram Interface :: Classes]"


class TelegramUser:
    states_whore = deque()
    transaction = {}
    merchant = {}
    method = {}
    task_current = {}
    task_scheduled = {}


def kiki(telegram_user: TelegramUser, text: str):
    return f"{str(telegram_user.states_whore)}\n\n{text}"


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
                    callback_data=key_data[0], text=key_data[1]))
                handler = CallbackQueryHandler(self._simple_handling)
                handlers.append(handler)
                simple_handlers[key_data[0]] = handler

        self._keyboard = InlineKeyboardMarkup(keyboard)
        self.handlers = handlers
        self.simple_handlers = simple_handlers

    def state(self, message: Message, text: str, edit: bool):
        if edit:
            message.edit_text(text, reply_markup=self.keyboard())
        else:
            message.reply_text(text, reply_markup=self.keyboard())
        return self.state_name

    def keyboard(self) -> InlineKeyboardMarkup:
        return self._keyboard

    def _simple_handling(self, update: Update, context: CallbackContext):
        data: str = update.callback_query.data
        # , show_alert = True, text="okay"
        context.bot.answer_callback_query(
            callback_query_id=update.callback_query.id, show_alert=False, text=("state: " + data))

        telegram_user = telegram_users[update.callback_query.message.chat.id]

        if data == "_BACK":
            if len(telegram_user.states_whore) > 0:
                state = telegram_user.states_whore.pop()
            else:
                state = "main"
            return conversation_views[state].state(update.callback_query.message, kiki(telegram_user, f"guess whos back to {state}"), True)
        else:
            telegram_user.states_whore.append(self.state_name)
            if data in conversation_views:
                return conversation_views[data].state(update.callback_query.message, kiki(telegram_user, f"selected data: {data}"), True)
            else:
                return conversation_views["_WIP"].state(update.callback_query.message, kiki(
                    telegram_user, f"ERROR! This data doesn't exist: {data}. You will be returned to {telegram_user.states_whore[-1]}"
                ), True)


class TelegramConversationFork:
    handler_type: str = "none"


class SimpleTelegramConversationFork(TelegramConversationFork):
    handler_type = "simple"

    def __init__(self, state: str):
        self.state = state


telegram_users: "dict[Any, TelegramUser]" = {}
conversation_views: "dict[str, TelegramConversationView]" = {}
