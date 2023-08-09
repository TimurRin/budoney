from interface.telegram.classes import (
    DatabaseView,
    DefaultView,
)


def init():
    DefaultView(
        "plants",
        [
            ["plant_species", "plant_lots"],
            ["plant_registry", "plant_replants"],
        ],
    )
    DatabaseView(
        "plant_registry",
        [
            {"column": "name", "type": "text", "skippable": True},
            {"column": "species", "type": "data", "data_type": "plant_species"},
            {"column": "date_died", "type": "date", "skippable": True},
            {"column": "note", "type": "text", "skippable": True},
        ],
    )
    DatabaseView(
        "plant_lots",
        [
            {"column": "name", "type": "text"},
        ],
    )
    DatabaseView(
        "plant_replants",
        [
            {"column": "plant", "type": "data", "data_type": "plant_registry"},
            {"column": "date_replanted", "type": "date"},
            {"column": "lot", "type": "text", "skippable": True},
            {"column": "note", "type": "text", "skippable": True},
        ],
    )
    DatabaseView(
        "plant_species",
        [
            {"column": "name", "type": "text"},
            {"column": "kind", "type": "text"},
            {"column": "latin", "type": "text", "skippable": True},
            {"column": "emoji", "type": "text", "skippable": True},
        ],
    )
