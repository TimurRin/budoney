import datetime
import google_sheets_handler as gsh
import utils.id_utils as id_utils


def schedule_tasks():
    data = gsh.get_cached_data(["tasks_current", "tasks_scheduled"])

    for scheduled_task_id in data["tasks_scheduled"]["list"]:
        scheduled_task_data = data["tasks_scheduled"]["dict"][scheduled_task_id]
        task_id = id_utils.generate_id(
            data["tasks_current"]["dict"],
            scheduled_task_data["name"]
        )

        task_date = datetime.datetime.today()

        gsh.insert_into_sheet(
            "tasks_current",
            [
                task_id,
                scheduled_task_data["name"],
                scheduled_task_data["importance"] and True or False,
                scheduled_task_data["id"],
                (task_date - datetime.datetime(1899, 12, 30)).days,
                scheduled_task_data["urgency"] and (task_date - datetime.datetime(1899, 12, 30)).days or "",
                "",
            ],
        )

    gsh.get_cached_data(["tasks_current"], update=True)
