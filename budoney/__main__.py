print_label: str = "[budoney]"

TELEGRAM = True
TELEGRAM_INTERFACE = True

if TELEGRAM:
    print(print_label, "TELEGRAM is enabled")
    import dispatcher.telegram

    conversation = None

    if TELEGRAM_INTERFACE:
        print(print_label, "TELEGRAM_INTERFACE is enabled")
        import interface.telegram

        conversation = interface.telegram.conversation

    dispatcher.telegram.start(conversation)
