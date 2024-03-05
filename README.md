# Budoney

A Telegram bot for your household finances, tasks, health and more!

## Features

`TODO`

## Getting Started

### Prerequisites

Make sure you have Python 3.x installed on your system. You can download Python from the official website: <https://www.python.org/downloads/>

### Installation

```bash
git clone https://github.com/TimurRin/budoney.git
cd budoney
pip install -r requirements.txt
mkdir config
touch general.yaml
touch telegram.yaml
```

`config/general.yaml` configuration file example:

```yaml
localization: "en" # app localization
production_mode: false # if true, hide debug information
quiet_mode: false # if true, telegram information messages won't be send
```

`config/telegram.yaml` configuration file example:

```yaml
enabled: true # enable telegram feature
interface: true # enable telegram bot interface
bot_token: "token" # telegram bot token from BotFather
authorized: [] # array of users who have access to the telegram bot
info_chats: [] # array of channel/groups/users which receive information messages
reveal_unauthorized: false # display unauthorized
```

Launch Budoney (when in repo folder)

```bash
python budoney
```

## License

This project is licensed under the **ISC License**, see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! If you find any issues or have suggestions for improvements, feel free to open an issue or create a pull request.

## Authors

- Timur Moziev ([@TimurRin](https://github.com/TimurRin)) (idea, development)
- Maria Zhizhina (idea, testing)
