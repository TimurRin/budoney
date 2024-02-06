from interface.telegram.classes import DefaultView


def init():
    DefaultView(
        "main",
        [
            ["transfers_ADD", "tasks_current_ADD"],
            ["income_ADD", "expenses_ADD"],
            ["blood_pressure_diary_ADD", "pills_diary_ADD"],
            [
                "tasks",
                "finances",
            ],
            ["health"],
            # [
            #     "utilities",
            #     "clothes",
            #     "storage",
            # ],
            # [
            # "food",
            # "plants",
            # ],
            ["organizations", "people"],
            ["settings", "statistics"],
        ],
    )
