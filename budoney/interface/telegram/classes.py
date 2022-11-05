from abc import abstractmethod
from typing import Type
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Message, Update
from telegram.ext import CallbackContext, CallbackQueryHandler, Handler

print_label: str = "[budoney :: Telegram Interface :: Classes]"

conversation_views: "dict[str, TelegramConversationView]" = {}


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
                print(type(key_data[2]))
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
        context.bot.answer_callback_query(callback_query_id = update.callback_query.id) # , show_alert = True, text="okay"
        if data in conversation_views:
            return conversation_views[data].state(update.callback_query.message, f"selected data: {data}", True)
        else:
            return conversation_views["wip"].state(update.callback_query.message, f"ERROR! This data doesn't exist: {data}", True)


class TelegramConversationFork:
    handler_type = "none"


class SimpleTelegramConversationFork(TelegramConversationFork):
    handler_type = "simple"

    def __init__(self, state: str):
        self.state = state
