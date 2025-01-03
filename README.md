Here's an updated version of the README that incorporates the new process where the bot will first run a script to join the groups and retrieve their IDs:

---

# Telegram Campaign Forwarder Bot

This is a Telegram bot that automates the process of forwarding advertising campaigns or messages to multiple Telegram groups at regular intervals. The bot allows users to create, update, start, stop, and manage campaigns via simple commands.

## Features

- **Create Campaigns**: Easily set up campaigns with a unique link and a specified duration for forwarding.
- **Update Campaigns**: Modify existing campaigns to change the link or duration.
- **Start Campaigns**: Begin forwarding messages to the groups listed.
- **Stop Campaigns**: Immediately halt any ongoing campaign.
- **List Campaigns**: Display all existing campaigns along with their details.
- **Delete Campaigns**: Permanently remove a campaign.
- **Skip Specific Groups**: Configure the bot to skip forwarding messages to certain groups.

## How It Works

1. **Campaign Creation**: When a campaign is created, it is assigned a unique ID. You can specify the link to be forwarded and the duration between each forward (e.g., every 2 minutes).
2. **Forwarding Logic**: The bot reads the list of chat IDs from a JSON file (`chat_ids.json`) and sends the message to all groups except those marked to be skipped.
3. **Group ID Retrieval**: Before the bot can send messages to groups, it first needs to join the groups. You will run an initial script to join the groups and retrieve their chat IDs. These IDs will be saved to `chat_ids.json`, which the bot will use later to forward messages.
4. **Stopping Campaigns**: Campaigns can be stopped at any time by using the appropriate command. The bot ensures that no further messages are forwarded once a campaign is marked inactive.
5. **Persistence**: All campaign data is stored in a JSON file (`campaigns.json`), ensuring that campaign information is retained even after a bot restart.

## Commands

| Command                | Description                                       | Usage Example                              |
|------------------------|---------------------------------------------------|-------------------------------------------|
| `/create_campaign`     | Creates a new campaign                            | `/create_campaign www.link.com 5min`      |
| `/update_campaign`     | Updates an existing campaign                      | `/update_campaign {id} www.link.com 10min`|
| `/delete_campaign`     | Deletes a campaign                                | `/delete_campaign {id}`                   |
| `/start_campaign`      | Starts a campaign                                 | `/start_campaign {id}`                    |
| `/stop_campaign`       | Stops a running campaign                          | `/stop_campaign {id}`                     |
| `/list_campaigns`      | Lists all campaigns with their details            | `/list_campaigns`                         |

## Setup Instructions

### Prerequisites

- Python 3.8+
- Telegram bot token (obtainable from [BotFather](https://core.telegram.org/bots#botfather))
- `pip` package manager

### Installation

1. Clone the repository:
    ```bash
    git clone https://github.com/your-username/telegram-campaign-forwarder-bot.git
    cd telegram-campaign-forwarder-bot
    ```

2. Create a virtual environment and activate it:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use venv\Scripts\activate
    ```

3. Install the required dependencies:
    ```bash
    pip install -r requirements.txt
    ```

4. Create a `.env` file in the project root and add your bot token:
    ```
    BOT_TOKEN=your-telegram-bot-token
    SKIP_GROUP=[group_id1, group_id2]
    ```

5. Run the `join_groups.py` script to join groups and get the IDs:
    ```bash
    python join_groups.py
    ```

### Running the Bot

Once the bot has joined the necessary groups and the chat IDs are saved to `chat_ids.json`, run the bot:
```bash
python bot.py
```

The bot will start and begin polling for messages from Telegram.

## File Structure

```
telegram-campaign-forwarder-bot/
│
├── bot.py                 # Main bot script
├── campaigns.json         # Stores campaign data
├── chat_ids.json          # Stores chat IDs to forward messages to
├── join_groups.py         # Script to join groups and get their chat IDs
├── .env                   # Environment variables (bot token)
├── requirements.txt       # List of dependencies
├── README.md              # Project documentation
└── .gitignore             # Files to ignore in git
```

### `join_groups.py` Script

This script is designed to allow the bot to join specific groups and retrieve their chat IDs. When you run this script, it will add the bot to the specified groups and collect the chat IDs, saving them in the `chat_ids.json` file for later use by the main bot.

```bash
python join_groups.py
```

## Error Handling

- The bot includes detailed logging for easier debugging and monitoring.
- Errors while sending messages to specific groups are logged but do not halt the bot’s execution.

## Future Enhancements

- Add support for more complex scheduling (e.g., specific start and end times).
- Add a web-based dashboard for campaign management.
- Implement database support for better scalability.
- Add functionality to manage chat IDs directly through bot commands.

## Contributing

Contributions are welcome! Feel free to fork the repository and submit a pull request.

## License

This project is licensed under the MIT License. See the `LICENSE` file for more details.

---

### Key Updates:
- **`join_groups.py`**: A new script that the bot runs first to join groups and collect chat IDs.
- After running `join_groups.py`, the bot will be able to use the chat IDs saved in `chat_ids.json` for forwarding messages.