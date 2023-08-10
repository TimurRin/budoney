from interface.telegram.classes import (
    DatabaseView,
    DefaultView,
)


def init():
    DefaultView(
        "plants",
        [
            ["plant_lots", "plant_species"],
            ["plant_registry", "plant_stages", "plant_replants"],
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
            {"column": "task", "type": "data", "data_type": "tasks_recurring", "skippable": True},
        ],
    )
    DatabaseView(
        "plant_stages",
        [
            {"column": "plant", "type": "data", "data_type": "plant_registry"},
            {"column": "date_occurence", "type": "date"},
            {
                "column": "stage",
                "type": "select",
                "select": [
                    "SPROUT",
                    "SEEDLING",
                    "PLANT",
                    "FLOWERS",
                    "PREMATURE_FRUITS",
                    "MATURE_FRUITS",
                ],
            },
        ],
    )
    DatabaseView(
        "plant_replants",
        [
            {"column": "plant", "type": "data", "data_type": "plant_registry"},
            {"column": "date_replanted", "type": "date"},
            {
                "column": "lot",
                "type": "data",
                "data_type": "plant_lots",
                "skippable": True,
            },
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
