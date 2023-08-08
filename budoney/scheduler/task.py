from typing import Any
import threading
from datetime import datetime
from database import DATABASE_DRIVER
import configs
from dispatcher.telegram import send_info_message
from interface.telegram.classes import database_views


def check_for_tasks():
    try:
        recurring = DATABASE_DRIVER.get_data(
            "SELECT r.id AS recurring, r.name, r.important, CAST(strftime('%s', 'now') AS INTEGER) AS date_created, (CAST(strftime('%s', 'now') AS INTEGER) + r.urgent * 86400) AS date_due FROM tasks_recurring r LEFT JOIN (SELECT COALESCE(date_completed, CAST(strftime('%s', 'now') AS INTEGER)) AS date_completed, recurring FROM tasks_current) c ON r.id = c.recurring WHERE r.paused = 0 GROUP BY c.recurring HAVING c.date_completed IS NULL OR CAST(strftime('%s', 'now') AS INTEGER) > (MAX(c.date_completed) + (r.rest_days + 1) * 86400)",
            [],
        )
        for record in recurring:
            DATABASE_DRIVER.append_data(
                "tasks_current",
                record,
            )
            send_info_message(database_views["tasks_current"].display_full_func(record))

    except Exception as e:
        print(e)
    finally:
        event_timer = threading.Timer(60.0, check_for_tasks)
        event_timer.daemon = True
        event_timer.start()
