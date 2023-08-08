from scheduler.task import check_for_tasks
import database
import configs


print_label: str = "[budoney]"

database.init()

conversation = None

if configs.telegram["enabled"]:
    print(print_label, "TELEGRAM is enabled")
    if configs.telegram["interface"]:
        print(print_label, "TELEGRAM_INTERFACE is enabled")
        import interface.telegram

        conversation = interface.telegram.conversation

check_for_tasks()

if configs.telegram["enabled"]:
    import dispatcher.telegram
    dispatcher.telegram.start(conversation)
