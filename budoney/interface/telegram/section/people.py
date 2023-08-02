from interface.telegram.classes import (
    DatabaseView,
)


def init():
    DatabaseView(
        "people",
        [
            {"column": "name", "type": "text"},
            {"column": "emoji", "type": "text", "skippable": True},
        ],
        display_func=lambda record: f"{record.get('emoji', '') or ''}{record.get('name', 'Unnamed user')}",
        order_by=[("name", False, None)],
    )
