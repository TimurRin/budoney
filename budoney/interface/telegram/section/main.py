from interface.telegram.classes import DefaultView


def init():
    DefaultView(
        "main",
        [
            ["transfers_ADD", "tasks_current_ADD"],
            ["income_ADD", "expenses_ADD"],
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
