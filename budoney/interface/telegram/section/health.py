from interface.telegram.classes import (
    DatabaseView,
    DefaultView,
)
from datetime import datetime
import utils.date_utils as date_utils

def _display_inline_pills(record):
    text_parts = []

    text_parts.append(str(record.get("name", "???")))
    if "brand" in record and record["brand"]:
        text_parts.append(f"({str(record.get('brand', '???'))})")

    # text_parts.append("—")

    # if f"intake_hours" in record and len(record[f"intake_hours"]):
    #     text_parts.append(len(record[f"intake_hours"]))
    return " ".join(text_parts)

def _display_inline_pills_diary(record):
    text_parts = []

    text_parts.append(
        date_utils.get_relative_timestamp_text(
            record["date_taken"], today=datetime.today(), limit=30
        )
    )

    text_parts.append("—")

    text_parts.append(str(record.get("pill__brand", record.get("pill__name", "Unknown pill"))))
    text_parts.append(f"({str(record.get('dose', '???'))} {str(record.get('pill__dosage_type', 'smth'))})")

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

    if "systolic" in record and record["systolic"] and "diastolic" in record and record["diastolic"]:
        text_parts.append("—")
        text_parts.append("diff " + str(record["systolic"] - record["diastolic"]))

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


def _display_inline_weight_diary(record):
    text_parts = []

    text_parts.append(
        date_utils.get_relative_timestamp_text(
            record["date_occurred"], today=datetime.today(), limit=30
        )
    )

    text_parts.append("—")

    text_parts.append(str(record.get("weight", "???")) + " kg")

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
            ["weight_diary", "symptoms_diary"],
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
            {"column": "name", "type": "text", "request_frequent_data": True},
            {"column": "brand", "type": "text", "skippable": True},
            {"column": "dosage_type", "type": "text", "request_frequent_data": True},
            # {"column": "intake_hours", "type": "array", "skippable": True},
        ],
        inline_display=_display_inline_pills,
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
                "column": "patient",
                "type": "data",
                "data_type": "people",
            },
            {
                "column": "pill",
                "type": "data",
                "data_type": "pills",
            },
            {
                "column": "dose",
                "type": "float",
                "request_frequent_data": True,
                "frequent_data_lookup": ["patient", "pill"],
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
            {
                "column": "patient",
                "type": "data",
                "data_type": "people",
            },
            {
                "column": "feelings",
                "type": "text",
                "request_frequent_data": True,
                "frequent_data_lookup": ["patient"],
            },
            {
                "column": "factors",
                "type": "text",
                "request_frequent_data": True,
                "frequent_data_lookup": ["patient"],
                "skippable": True,
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
            {
                "column": "patient",
                "type": "data",
                "data_type": "people",
            },
            {
                "column": "level",
                "type": "float",
                "request_frequent_data": True,
                "frequent_data_lookup": ["patient"],
            },
            {
                "column": "notes",
                "type": "text",
                "request_frequent_data": True,
                "frequent_data_lookup": ["patient"],
                "skippable": True,
            },
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
            {
                "column": "patient",
                "type": "data",
                "data_type": "people",
            },
            {
                "column": "degrees",
                "type": "float",
                "request_frequent_data": True,
                "frequent_data_lookup": ["patient"],
            },
            {
                "column": "notes",
                "type": "text",
                "request_frequent_data": True,
                "frequent_data_lookup": ["patient"],
                "skippable": True,
            },
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
            {
                "column": "patient",
                "type": "data",
                "data_type": "people",
            },
            {
                "column": "systolic",
                "type": "int",
                "request_frequent_data": True,
                "frequent_data_lookup": ["patient"],
            },
            {
                "column": "diastolic",
                "type": "int",
                "request_frequent_data": True,
                "frequent_data_lookup": ["patient"],
            },
            {
                "column": "notes",
                "type": "text",
                "request_frequent_data": True,
                "frequent_data_lookup": ["patient"],
                "skippable": True,
            },
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
            {
                "column": "patient",
                "type": "data",
                "data_type": "people",
            },
            {
                "column": "beats",
                "type": "int",
                "request_frequent_data": True,
                "frequent_data_lookup": ["patient"],
            },
            {
                "column": "notes",
                "type": "text",
                "request_frequent_data": True,
                "frequent_data_lookup": ["patient"],
                "skippable": True,
            },
        ],
        inline_display=_display_inline_pulse_diary,
        fast_type="required",
        order_by=[
            ("date_occurred", True, None),
        ],
    )
    DatabaseView(
        "weight_diary",
        [
            {
                "column": "date_occurred",
                "type": "timestamp",
                "autoset": lambda: int(datetime.today().timestamp()),
            },
            {
                "column": "patient",
                "type": "data",
                "data_type": "people",
            },
            {
                "column": "weight",
                "type": "float",
                "request_frequent_data": True,
                "frequent_data_lookup": ["patient"],
            },
            {
                "column": "notes",
                "type": "text",
                "request_frequent_data": True,
                "frequent_data_lookup": ["patient"],
                "skippable": True,
            },
        ],
        inline_display=_display_inline_weight_diary,
        fast_type="required",
        order_by=[
            ("date_occurred", True, None),
        ],
    )
