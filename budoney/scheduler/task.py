import threading
import configs


def check_for_tasks():
    print("Checking for events...")

    if configs.telegram["enabled"]:
        import dispatcher.telegram
        dispatcher.telegram.send_info_message("hehe")

    event_timer = threading.Timer(10.0, check_for_tasks)
    event_timer.daemon = True
    event_timer.start()
