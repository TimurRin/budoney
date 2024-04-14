from typing import Any
import threading
from datetime import datetime
from database import DATABASE_DRIVER
import configs
from dispatcher.telegram import send_info_message
from interface.telegram.classes import database_views
import utils.date_utils as date_utils

print_label: str = "[budoney :: Scheduler :: Task]"

def check_for_tasks():
    try:
        # plant_lots_query = "SELECT pl.id AS id, pl.name AS name, COUNT(pr_latest.plant) AS alive_plants_count, pl.task, REPLACE(GROUP_CONCAT(DISTINCT ps.emoji), ',', ' ') AS emoji_pack FROM plant_lots pl LEFT JOIN ( SELECT pr.plant, pr.lot, MAX(pr.date_replanted) AS latest_replant FROM plant_replants pr JOIN plant_registry pr2 ON pr2.id = pr.plant AND pr2.date_died IS NULL GROUP BY pr.plant ) latest_replants ON pl.id = latest_replants.lot LEFT JOIN plant_replants pr_latest ON latest_replants.plant = pr_latest.plant AND latest_replants.latest_replant = pr_latest.date_replanted LEFT JOIN plant_registry pr3 ON latest_replants.plant = pr3.id LEFT JOIN plant_species ps ON pr3.species = ps.id WHERE pl.task IS NULL GROUP BY pl.id, pl.name HAVING alive_plants_count > 0 ORDER BY pl.id"
        # plant_lots = DATABASE_DRIVER.get_data(plant_lots_query, [])
        plant_lots = []

        for plant_lot in plant_lots:
            if not plant_lot["task"]:
                record = {
                    "name": f"💧 Полить {plant_lot['emoji_pack']} {plant_lot['name']}",
                    "important": 1,
                    "category": "Огород",
                    "urgent": 0,
                    "work_days": 1,
                    "rest_days": 2,
                    "paused": 0,
                }
                last_id = DATABASE_DRIVER.append_data(
                    "tasks_recurring",
                    record,
                )
                print(print_label, "check_for_tasks", "last_id", last_id)
                if last_id:
                    print(print_label, "check_for_tasks", "plant_lot", plant_lot)
                    DATABASE_DRIVER.replace_data(
                        "plant_lots", plant_lot["id"], {"task": last_id}
                    )

        midnight = date_utils.get_today_midnight_timestamp()
        recurring = DATABASE_DRIVER.get_data(
            f"SELECT r.id AS recurring, r.name, r.category, r.important, {midnight} AS date_created, ({midnight} + r.urgent * 86400) AS date_due FROM tasks_recurring r LEFT JOIN (SELECT COALESCE(date_completed, {midnight}) AS date_completed, recurring FROM tasks_current) c ON r.id = c.recurring WHERE r.paused = 0 GROUP BY r.id HAVING c.date_completed IS NULL OR {midnight} >= (MAX(c.date_completed) + (r.rest_days + 1) * 86400) ORDER BY r.category, r.urgent DESC, r.important DESC, r.name",
            [],
        )
        new_tasks_start = f"<b>NEW TASKS</b> ({len(recurring)}):"
        new_messages = []
        message_threshold = len(new_tasks_start)
        category = ""
        for record in recurring:
            DATABASE_DRIVER.append_data(
                "tasks_current",
                record,
            )
            text = database_views["tasks_current"].inline_display(record, None)[:4096]
            text_len = len(text)
            text_len_added = message_threshold + text_len
            if not new_messages:
                new_messages.append([new_tasks_start])
            if "category" not in record or (category != record["category"]):
                category = record["category"]
                new_messages[-1].append("")
                new_messages[-1].append(f"<b>{category}</b>")
            if text_len_added <= 4096:
                message_threshold += text_len
                new_messages[-1].append(text)
            else:
                message_threshold = text_len
                new_messages.append([text])
        if len(new_messages):
            for new_message in new_messages:
                send_info_message("\n".join(new_message))
    except Exception as e:
        print(e)
    finally:
        event_timer = threading.Timer(60.0, check_for_tasks)
        event_timer.daemon = True
        event_timer.start()
