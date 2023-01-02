import datetime
from time import sleep
import google_sheets_handler as gsh
import utils.id_utils as id_utils


def schedule_tasks():
    data = gsh.get_cached_data(["tasks_current", "tasks_scheduled"])

    task_date = datetime.datetime.today()
    recurring_timestamp = task_date.strftime("%Y_%m_%d")

    changed = False

    for line, scheduled_task_id in enumerate(data["tasks_scheduled"]["list"], 2):
        scheduled_task_data = data["tasks_scheduled"]["dict"][scheduled_task_id]
        task_id = id_utils.generate_id(
            data["tasks_current"]["dict"], scheduled_task_data["name"]
        )

        if scheduled_task_data["recurring_timestamp"] != recurring_timestamp:
            changed = True
            gsh.sheets["tasks_scheduled"].update_cell(line, 9, recurring_timestamp)
            recurring_stage = scheduled_task_data["recurring_stage"] + 1
            if recurring_stage > scheduled_task_data["recurring_value"]:
                recurring_stage = 1
            gsh.sheets["tasks_scheduled"].update_cell(line, 8, recurring_stage)
            if recurring_stage == 1:
                gsh.sheets["tasks_scheduled"].update_cell(
                    line, 10, scheduled_task_data["times_scheduled"] + 1
                )
                gsh.insert_into_sheet(
                    "tasks_current",
                    [
                        task_id,
                        scheduled_task_data["name"],
                        scheduled_task_data["importance"] and True or False,
                        scheduled_task_data["urgency"] and True or False,
                        scheduled_task_data["id"],
                        (task_date - datetime.datetime(1899, 12, 30)).days,
                        "",
                        "",
                    ],
                )

    if changed:
        gsh.get_cached_data(["tasks_current", "tasks_scheduled"], update=True)


def check_tasks():
    schedule_tasks()
    while True:
        sleep(60 * 15)
        schedule_tasks()
