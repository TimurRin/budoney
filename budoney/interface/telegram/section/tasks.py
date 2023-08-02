from interface.telegram.classes import (
    DatabaseTelegramConversationView,
    DefaultTelegramConversationView,
)
import utils.date_utils as date_utils


def _display_inline_current_task(record):
    text_parts = []

    if "date_completed" in record and record["date_completed"]:
        text_parts.append("[☑️")
        text_parts.append(
            date_utils.get_relative_timestamp(record["date_completed"]) + "]"
        )
    else:
        if "date_due" in record and record["date_due"]:
            text_parts.append("[🗓")
            text_parts.append(
                date_utils.get_relative_timestamp(record["date_due"]) + "]"
            )

        if "important" in record and record["important"]:
            text_parts.append("❗️")

        if "urgent" in record and record["urgent"]:
            text_parts.append("⚠️")

    if "recurring" in record and record["recurring"]:
        text_parts.append("🔁")

    text_parts.append(str(record.get("name", "???")))

    return " ".join(text_parts)


def init():
    DefaultTelegramConversationView(
        "tasks",
        [
            [
                "tasks_current",
                "tasks_recurring",
            ],
        ],
    )
    DatabaseTelegramConversationView(
        "tasks_current",
        [
            {"column": "name", "type": "text"},
            {"column": "important", "type": "boolean"},
            {"column": "urgent", "type": "boolean"},
            {
                "column": "recurring",
                "type": "data",
                "data_type": "tasks_recurring",
                "skippable": True,
            },
            {"column": "date_created", "type": "date"},
            {"column": "date_due", "type": "date", "skippable": True},
            {"column": "date_completed", "type": "date", "skippable": True},
        ],
        display_func=_display_inline_current_task,
        order_by=["date_created"],
    )
    DatabaseTelegramConversationView(
        "tasks_recurring",
        [
            {"column": "name", "type": "text"},
            {"column": "important", "type": "boolean"},
            {"column": "urgent", "type": "boolean"},
            {"column": "type", "type": "select", "select": ["DAILY"]},
            {"column": "occurrence", "type": "text"},
            {"column": "paused", "type": "boolean"},
        ],
    )
