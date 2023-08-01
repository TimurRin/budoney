from scheduler.task import check_for_tasks
import configs


print_label: str = "[budoney]"

# check_for_tasks()

if configs.telegram["enabled"]:
    print(print_label, "TELEGRAM is enabled")
    import dispatcher.telegram

    conversation = None

    if configs.telegram["interface"]:
        print(print_label, "TELEGRAM_INTERFACE is enabled")
        import interface.telegram

        conversation = interface.telegram.conversation

    dispatcher.telegram.start(conversation)
