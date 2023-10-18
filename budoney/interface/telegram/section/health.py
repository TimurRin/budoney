from interface.telegram.classes import (
    DatabaseView,
    DefaultView,
)
from datetime import datetime
import utils.date_utils as date_utils


def _display_inline_pills_diary(record):
    text_parts = []

    text_parts.append(
        date_utils.get_relative_timestamp_text(
            record["date_taken"], today=datetime.today(), limit=30
        )
    )

    text_parts.append("—")

    text_parts.append(str(record.get("pill__name", "???")))
    text_parts.append(f"({str(record.get('dose', '???'))} mg)")

    text_parts.append("—")

    if f"owner__emoji" in record and record[f"patient__emoji"]:
        text_parts.append(record[f"patient__emoji"])
    text_parts.append(str(record.get("patient__name", "???")))

    return " ".join(text_parts)


def _display_inline_symptoms_diary(record):
    text_parts = []

    text_parts.append(
        date_utils.get_relative_timestamp_text(
            record["date_occurred"], today=datetime.today(), limit=30
        )
    )

    text_parts.append("—")

    if f"owner__emoji" in record and record[f"patient__emoji"]:
        text_parts.append(record[f"patient__emoji"])
    text_parts.append(str(record.get("patient__name", "???")))

    text_parts.append("—")

    text_parts.append(str(record.get("feelings", "???")))

    return " ".join(text_parts)


def _display_inline_glucose_diary(record):
    text_parts = []

    text_parts.append(
        date_utils.get_relative_timestamp_text(
            record["date_occurred"], today=datetime.today(), limit=30
        )
    )

    text_parts.append("—")

    text_parts.append(str(record.get("level", "???")) + " mmol/L")

    text_parts.append("—")

    if f"owner__emoji" in record and record[f"patient__emoji"]:
        text_parts.append(record[f"patient__emoji"])
    text_parts.append(str(record.get("patient__name", "???")))

    return " ".join(text_parts)


def _display_inline_body_temperature_diary(record):
    text_parts = []

    text_parts.append(
        date_utils.get_relative_timestamp_text(
            record["date_occurred"], today=datetime.today(), limit=30
        )
    )

    text_parts.append("—")

    text_parts.append(str(record.get("degrees", "???")) + " °C")

    text_parts.append("—")

    if f"owner__emoji" in record and record[f"patient__emoji"]:
        text_parts.append(record[f"patient__emoji"])
    text_parts.append(str(record.get("patient__name", "???")))

    return " ".join(text_parts)


def _display_inline_blood_pressure_diary(record):
    text_parts = []

    text_parts.append(
        date_utils.get_relative_timestamp_text(
            record["date_occurred"], today=datetime.today(), limit=30
        )
    )

    text_parts.append("—")
    text_parts.append(
        str(record.get("systolic", "???"))
        + "/"
        + str(record.get("diastolic", "???"))
        + " mmHg"
    )

    text_parts.append("—")

    if f"owner__emoji" in record and record[f"patient__emoji"]:
        text_parts.append(record[f"patient__emoji"])
    text_parts.append(str(record.get("patient__name", "???")))

    return " ".join(text_parts)


def _display_inline_pulse_diary(record):
    text_parts = []

    text_parts.append(
        date_utils.get_relative_timestamp_text(
            record["date_occurred"], today=datetime.today(), limit=30
        )
    )

    text_parts.append("—")

    text_parts.append(str(record.get("beats", "???")) + " bpm")

    text_parts.append("—")

    if f"owner__emoji" in record and record[f"patient__emoji"]:
        text_parts.append(record[f"patient__emoji"])
    text_parts.append(str(record.get("patient__name", "???")))

    return " ".join(text_parts)


def init():
    DefaultView(
        "health",
        [
            ["pills", "pills_diary"],
            # ["diseases_seasonal", "diseases_chronic"],
            ["symptoms_diary"],
            [
                "glucose_level_diary",
                "body_temperature_diary",
            ],
            ["blood_pressure_diary", "pulse_diary"],
        ],
    )
    DatabaseView(
        "pills",
        [
            {"column": "name", "type": "text"},
        ],
        inline_display=lambda record: f"{record.get('name', 'Unnamed pill')}",
        order_by=[
            ("name", False, None),
        ],
    )
    DatabaseView(
        "pills_diary",
        [
            {
                "column": "date_taken",
                "type": "timestamp",
                "autoset": lambda: int(datetime.today().timestamp()),
            },
            {
                "column": "pill",
                "type": "data",
                "data_type": "pills",
            },
            {"column": "dose", "type": "float", "request_frequent_data": True},
            {
                "column": "patient",
                "type": "data",
                "data_type": "people",
            },
            {"column": "notes", "type": "text", "skippable": True},
        ],
        inline_display=_display_inline_pills_diary,
        fast_type="required",
        order_by=[
            ("date_taken", True, None),
        ],
    )
    DatabaseView(
        "symptoms_diary",
        [
            {
                "column": "date_occurred",
                "type": "timestamp",
                "autoset": lambda: int(datetime.today().timestamp()),
            },
            {"column": "feelings", "type": "text"},
            {"column": "factors", "type": "text", "skippable": True},
            {
                "column": "patient",
                "type": "data",
                "data_type": "people",
            },
        ],
        inline_display=_display_inline_symptoms_diary,
        order_by=[
            ("date_occurred", True, None),
        ],
    )
    DatabaseView(
        "glucose_level_diary",
        [
            {
                "column": "date_occurred",
                "type": "timestamp",
                "autoset": lambda: int(datetime.today().timestamp()),
            },
            {"column": "level", "type": "float", "request_frequent_data": True},
            {
                "column": "patient",
                "type": "data",
                "data_type": "people",
            },
            {"column": "notes", "type": "text", "skippable": True},
        ],
        inline_display=_display_inline_glucose_diary,
        fast_type="required",
        order_by=[
            ("date_occurred", True, None),
        ],
    )
    DatabaseView(
        "body_temperature_diary",
        [
            {
                "column": "date_occurred",
                "type": "timestamp",
                "autoset": lambda: int(datetime.today().timestamp()),
            },
            {"column": "degrees", "type": "float", "request_frequent_data": True},
            {
                "column": "patient",
                "type": "data",
                "data_type": "people",
            },
            {"column": "notes", "type": "text", "skippable": True},
        ],
        inline_display=_display_inline_body_temperature_diary,
        fast_type="required",
        order_by=[
            ("date_occurred", True, None),
        ],
    )
    DatabaseView(
        "blood_pressure_diary",
        [
            {
                "column": "date_occurred",
                "type": "timestamp",
                "autoset": lambda: int(datetime.today().timestamp()),
            },
            {"column": "systolic", "type": "int", "request_frequent_data": True},
            {"column": "diastolic", "type": "int", "request_frequent_data": True},
            {
                "column": "patient",
                "type": "data",
                "data_type": "people",
            },
            {"column": "notes", "type": "text", "skippable": True},
        ],
        inline_display=_display_inline_blood_pressure_diary,
        fast_type="required",
        order_by=[
            ("date_occurred", True, None),
        ],
    )
    DatabaseView(
        "pulse_diary",
        [
            {
                "column": "date_occurred",
                "type": "timestamp",
                "autoset": lambda: int(datetime.today().timestamp()),
            },
            {"column": "beats", "type": "int", "request_frequent_data": True},
            {
                "column": "patient",
                "type": "data",
                "data_type": "people",
            },
            {"column": "notes", "type": "text", "skippable": True},
        ],
        inline_display=_display_inline_pulse_diary,
        fast_type="required",
        order_by=[
            ("date_occurred", True, None),
        ],
    )
