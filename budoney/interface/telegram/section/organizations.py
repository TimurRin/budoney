from interface.telegram.classes import (
    DatabaseTelegramConversationView,
)


def init():
    DatabaseTelegramConversationView(
        "organizations",
        [
            {"column": "name", "type": "text"},
            {"column": "keywords", "type": "text", "skippable": True},
            {"column": "category", "type": "data", "data_type": "financial_categories"},
            {"column": "emoji", "type": "text", "skippable": True},
        ],
        lambda record: f"{record.get('emoji', '') or ''}{record.get('name', 'Unnamed organization')}",
    )
