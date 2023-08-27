from typing import Any
from interface.telegram.classes import (
    DatabaseView,
    DefaultView,
)
import utils.date_utils as date_utils
from database import DATABASE_DRIVER
from datetime import datetime
from dispatcher.telegram import send_info_message


def _display_inline_current_task(record):
    text_parts = []

    if "date_completed" in record and record["date_completed"]:
        text_parts.append("[☑️")
        text_parts.append(
            date_utils.get_relative_timestamp_text(record["date_completed"]) + "]"
        )
    else:
        if "date_due" in record and record["date_due"]:
            days = date_utils.get_relative_timestamp(record["date_due"])
            text_parts.append((days < -3 and "⏳") or (days < 0 and "⌛️") or "⚠️⌛️")
            text_parts.append(
                date_utils.get_relative_timestamp_text(record["date_due"])
            )
        elif "date_created" in record and record["date_created"]:
            text_parts.append("🗓")
            text_parts.append(
                date_utils.get_relative_timestamp_text(record["date_created"])
            )

        if "important" in record and record["important"]:
            text_parts.append("‼️")

    if "recurring" in record and record["recurring"]:
        text_parts.append("🔁")

    text_parts.append(str(record.get("name", "???")))

    return " ".join(text_parts)


def _display_inline_scheduled_task(record):
    text_parts = []

    paused = "paused" in record and record["paused"]

    if paused:
        text_parts.append("⏸")
    else:
        if "important" in record and record["important"]:
            text_parts.append("‼️")

        if (
            "urgent" in record
            and record["urgent"] is not None
            and record["urgent"] >= 0
        ):
            text_parts.append("⚡️")

    text_parts.append(str(record.get("name", "???")))

    if not (paused) and "work_days" in record and "rest_days" in record:
        work_days = int(record["work_days"]) or 0
        rest_days = int(record["rest_days"]) or 0
        if work_days > 0:
            if rest_days > 0:
                if work_days == 1:
                    text_parts.append(f"[Every {rest_days+1}d]")
                else:
                    text_parts.append(f"[{work_days}/{rest_days} shift]")
            else:
                text_parts.append(f"[daily]")

    return " ".join(text_parts)


def _action_conditions_done_current_task(record):
    return "date_completed" not in record or not record["date_completed"]


def _action_process_done_current_task(record):
    update = {"date_completed": date_utils.get_today_day_timestamp()}
    DATABASE_DRIVER.replace_data(
        "tasks_current",
        record["id"],
        update,
    )
    send_info_message("✅ 🗒 Task completed: " + record["name"])


def _db_current_task_fast_type_processor(
    data: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    record = {}
    record_filters: dict[str, str] = {}

    if data:
        record["name"] = data

    return (record, record_filters)


def init():
    DefaultView(
        "tasks",
        [
            [
                "tasks_current",
                "tasks_recurring",
            ],
        ],
    )
    DatabaseView(
        "tasks_current",
        [
            {"column": "name", "type": "text"},
            {"column": "category", "type": "text", "skippable": True},
            {"column": "important", "type": "boolean"},
            {
                "column": "recurring",
                "type": "data",
                "data_type": "tasks_recurring",
                "skippable": True,
                "hidden": True,
            },
            {
                "column": "date_created",
                "type": "date",
                "autoset": lambda: datetime.today().timestamp(),
            },
            {"column": "date_due", "type": "date", "skippable": True, "future": True},
            {"column": "date_completed", "type": "date", "skippable": True},
        ],
        inline_display=_display_inline_current_task,
        fast_type="required",
        fast_type_processor=_db_current_task_fast_type_processor,
        order_by=[
            ("date_completed", True, "IS NOT NULL"),
            ("date_due", False, "IS NULL"),
            ("important", True, None),
            ("date_created", False, None),
        ],
        actions=[
            {
                "name": "done",
                "conditions": _action_conditions_done_current_task,
                "params": ["date_completed"],
                "process": _action_process_done_current_task,
            }
        ],
    )
    DatabaseView(
        "tasks_recurring",
        [
            {"column": "name", "type": "text"},
            {"column": "category", "type": "text"},
            {"column": "important", "type": "boolean"},
            {"column": "urgent", "type": "int", "skippable": True},
            {"column": "work_days", "type": "int", "min": 1},
            {"column": "rest_days", "type": "int", "min": 0},
            {"column": "weekdays", "type": "text", "skippable": True},
            {"column": "paused", "type": "boolean", "skippable": True},
        ],
        inline_display=_display_inline_scheduled_task,
        order_by=[
            ("paused", False, None),
            ("urgent", False, "IS NULL"),
            ("important", True, None),
            ("work_days", True, None),
            ("rest_days", False, None),
            ("name", False, None),
        ],
    )
