print_label: str = "[budoney]"

TELEGRAM = True
TELEGRAM_INTERFACE = True

if TELEGRAM:
    print(print_label, "TELEGRAM is enabled")
    import telegram_connector

    conversation = None

    if TELEGRAM_INTERFACE:
        print(print_label, "TELEGRAM_INTERFACE is enabled")
        import interface.telegram as telegram_interface
        conversation = telegram_interface.conversation

    telegram_connector.start(conversation)
