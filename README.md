# 📚 Tutor Connect Bot

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Telegram](https://img.shields.io/badge/Telegram-Bot-blue.svg)](https://core.telegram.org/bots)
[![MongoDB](https://img.shields.io/badge/MongoDB-4.4+-green.svg)](https://www.mongodb.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A comprehensive Telegram bot that connects students with tutors, featuring an admin panel, session management, and real-time communication.

## ✨ Features

### For Students
- 🔍 Find tutors by subject, level, and availability
- 📅 Book and manage tutoring sessions
- ⭐ Rate and review tutors
- 💬 In-app messaging with tutors
- 🔔 Session reminders and notifications

### For Tutors
- 📝 Create detailed profiles with subjects and availability
- 🗓️ Manage session schedule
- 💰 Set hourly rates and payment preferences
- 📊 View performance metrics and reviews
- 📱 Mobile-friendly interface

### For Admins
- 👥 User and tutor management
- ✅ Approve/Reject tutor applications
- 📊 Dashboard with system analytics
- 📢 Broadcast messages to all users
- ⚙️ System configuration

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- MongoDB 4.4+
- Telegram Bot Token from [@BotFather](https://t.me/botfather)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/tutor-connect-bot.git
   cd tutor-connect-bot
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure environment variables:
   Create a `.env` file in the project root:
   ```env
   TELEGRAM_TOKEN=your_telegram_bot_token
   MONGODB_URI=mongodb://localhost:27017/
   DATABASE_NAME=tutor_connect
   ADMIN_IDS=123456789,987654321  # Comma-separated list of admin Telegram IDs
   ```

5. Run the bot:
   ```bash
   python -m tutor_connect_bot.main
   ```

## 🛠️ Project Structure

```
tutor-connect-bot/
├── tutor_connect_bot/
│   ├── handlers/           # Bot command and callback handlers
│   │   ├── admin.py        # Admin panel functionality
│   │   ├── student.py      # Student commands
│   │   └── tutor.py        # Tutor commands
│   ├── database/           # Database models and connections
│   ├── utils/              # Utility functions
│   ├── config.py           # Configuration settings
│   └── main.py             # Bot initialization and main entry point
├── .env.example           # Example environment variables
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## 🤖 Available Commands

### Student Commands
- `/start` - Start the bot and show main menu
- `/find_tutor` - Search for available tutors
- `/my_sessions` - View upcoming and past sessions
- `/help` - Show help information

### Tutor Commands
- `/profile` - View and edit your profile
- `/availability` - Set your available hours
- `/sessions` - Manage your tutoring sessions
- `/earnings` - View your earnings and payment history

### Admin Commands
- `/admin` - Access the admin panel
- `/stats` - View system statistics
- `/broadcast` - Send a message to all users
- `/export` - Export user data (CSV/Excel)

## 🔧 Configuration

Edit the `.env` file to configure the bot:

```env
# Required
TELEGRAM_TOKEN=your_telegram_bot_token
MONGODB_URI=mongodb://localhost:27017/
DATABASE_NAME=tutor_connect

# Optional
ADMIN_IDS=123456789,987654321  # Comma-separated list of admin IDs
LOG_LEVEL=INFO                 # DEBUG, INFO, WARNING, ERROR, CRITICAL
SESSION_TIMEOUT=3600           # Session timeout in seconds
```

## 📦 Dependencies

- `python-telegram-bot` - Telegram Bot API wrapper
- `pymongo` - MongoDB driver
- `python-dotenv` - Environment variable management
- `pytz` - Timezone support
- `python-dateutil` - Date/time utilities

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [python-telegram-bot](https://python-telegram-bot.org/) for the excellent Telegram Bot API wrapper
- [MongoDB](https://www.mongodb.com/) for the flexible NoSQL database
- All contributors who helped improve this project

---

<div align="center">
  Made with ❤️ by Your Name
</div>
