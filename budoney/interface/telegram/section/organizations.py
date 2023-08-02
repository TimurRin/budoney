from interface.telegram.classes import (
    DatabaseView,
)


def _display_inline_organization(record):
    text_parts = []

    if "category__emoji" in record and record["category__emoji"]:
        text_parts.append(record["category__emoji"])

    if "emoji" in record and record["emoji"]:
        text_parts.append(record["emoji"])

    text_parts.append(str(record.get("name", "Generic organization")))

    if "category__name" in record and record["category__name"]:
        text_parts.append("(" + record["category__name"] + ")")

    return " ".join(text_parts)


def init():
    DatabaseView(
        "organizations",
        [
            {"column": "name", "type": "text"},
            {"column": "keywords", "type": "text", "skippable": True},
            {"column": "category", "type": "data", "data_type": "financial_categories"},
            {"column": "emoji", "type": "text", "skippable": True},
        ],
        display_func=_display_inline_organization,
        order_by=[("category__name", False, None), ("name", False, None)],
    )
