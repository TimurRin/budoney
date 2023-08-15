from interface.telegram.classes import (
    DatabaseLinkedReport,
    DatabaseView,
)


def init():
    DatabaseView(
        "people",
        [
            {"column": "name", "type": "text"},
            {"column": "emoji", "type": "text", "skippable": True},
        ],
        inline_display=lambda record: f"{record.get('emoji', '') or ''}{record.get('name', 'Unnamed user')}",
        order_by=[("name", False, None)],
        report_links=[
            DatabaseLinkedReport("income", "financial_account__owner"),
            DatabaseLinkedReport("expenses", "financial_account__owner"),
        ],
    )
