from interface.telegram.classes import (
    DefaultView,
)


def init():
    DefaultView(
        "health",
        [
            ["pills"],
            [
                "diseases",
            ],
            [
                "body_temperature",
            ],
        ],
    )
