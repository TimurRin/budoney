import datetime
from time import sleep
import google_sheets_handler as gsh
import utils.id_utils as id_utils


def schedule_tasks():
    data = gsh.get_cached_data(["tasks_current", "tasks_scheduled"])

    task_date = datetime.datetime.today()
    recurring_timestamp = task_date.strftime("%Y_%m_%d")

    changed = False
    cells_to_read = gsh.sheets["tasks_scheduled"].range(
        "H2:L" + str(1 + len(data["tasks_scheduled"]["list"]))
    )
    cells_to_update = []
    rows_to_append = []

    ids = dict(data["tasks_current"]["dict"])

    for scheduled_task_id in data["tasks_scheduled"]["list"]:
        scheduled_task_data = data["tasks_scheduled"]["dict"][scheduled_task_id]
        consequence = 5 * scheduled_task_data["position"]
        task_id = id_utils.generate_id(ids, scheduled_task_data["name"])
        ids[task_id] = True

        if not scheduled_task_data["scheduled"] and (
            scheduled_task_data["recurring_timestamp"] != recurring_timestamp
        ):
            changed = True
            cells_to_read[1 + consequence].value = recurring_timestamp
            cells_to_update.append(cells_to_read[1 + consequence])
            recurring_stage = scheduled_task_data["recurring_stage"] + 1
            if recurring_stage > scheduled_task_data["recurring_value"]:
                recurring_stage = 1
            cells_to_read[0 + consequence].value = recurring_stage
            cells_to_update.append(cells_to_read[0 + consequence])
            if recurring_stage == 1:
                cells_to_read[2 + consequence].value = (
                    scheduled_task_data["times_scheduled"] + 1
                )
                cells_to_update.append(cells_to_read[2 + consequence])
                cells_to_read[4 + consequence].value = True
                cells_to_update.append(cells_to_read[4 + consequence])
                rows_to_append.append(
                    [
                        task_id,
                        scheduled_task_data["name"],
                        scheduled_task_data["importance"] and True or False,
                        scheduled_task_data["urgency"] and True or False,
                        scheduled_task_data["id"],
                        (task_date - datetime.datetime(1899, 12, 30)).days,
                        "",
                        "",
                    ]
                )

    if changed:
        if len(cells_to_update) > 0:
            gsh.sheets["tasks_scheduled"].update_cells(cells_to_update)
        if len(rows_to_append) > 0:
            gsh.insert_into_sheet("tasks_current", rows_to_append)
        gsh.get_cached_data(["tasks_current", "tasks_scheduled"], update=True)


def check_tasks():
    schedule_tasks()
    while True:
        sleep(60 * 10)
        schedule_tasks()
