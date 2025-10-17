"""
Simple Telegram Bot to test MMDT API
"""
import os
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from decouple import Config, RepositoryEnv

# Configuration
API_BASE_URL = "http://127.0.0.1:8000/api"

# Load token from .env file
env_path = os.path.join(os.path.dirname(__file__), 'mmdt', '.env')
config = Config(RepositoryEnv(env_path))
TELEGRAM_BOT_TOKEN = config('TELEGRAM_BOT_TOKEN')

# Store user tokens temporarily (in production, use a database)
user_tokens = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""
    welcome_message = """
Welcome to MMDT Bot! 🤖

Available commands:
/login <username> <password> - Login to get your token
/me - Get your user information
/user <id> - Get user by ID
/list - List all users (admin only)
/help - Show this message
"""
    await update.message.reply_text(welcome_message)


async def login(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Login command to get authentication token"""
    if len(context.args) != 2:
        await update.message.reply_text(
            "Usage: /login <username> <password>\n"
            "Example: /login zno admin123"
        )
        return

    username = context.args[0]
    password = context.args[1]

    try:
        # Call API to get token
        response = requests.post(
            f"{API_BASE_URL}/auth/token/",
            json={"username": username, "password": password},
            timeout=5
        )

        if response.status_code == 200:
            data = response.json()
            token = data['token']
            user_id = data['user_id']

            # Store token for this Telegram user
            user_tokens[update.effective_user.id] = token

            await update.message.reply_text(
                f"✅ Login successful!\n\n"
                f"User ID: {user_id}\n"
                f"Username: {data['username']}\n"
                f"Email: {data['email']}\n\n"
                f"Your token has been saved. You can now use /me and /user commands."
            )
        else:
            await update.message.reply_text(
                f"❌ Login failed: {response.json().get('error', 'Invalid credentials')}"
            )

    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")


async def me(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get current user information"""
    telegram_user_id = update.effective_user.id

    # Check if user is logged in
    if telegram_user_id not in user_tokens:
        await update.message.reply_text(
            "❌ You need to login first!\n"
            "Use: /login <username> <password>"
        )
        return

    token = user_tokens[telegram_user_id]

    try:
        # Call API to get user info
        response = requests.get(
            f"{API_BASE_URL}/users/me/",
            headers={"Authorization": f"Token {token}"},
            timeout=5
        )

        if response.status_code == 200:
            data = response.json()
            profile = data.get('profile', {})

            message = f"""
👤 Your Profile:

ID: {data['id']}
Username: {data['username']}
Email: {data['email']}
First Name: {data.get('first_name', 'N/A')}
Last Name: {data.get('last_name', 'N/A')}
Active: {'✅ Yes' if data['is_active'] else '❌ No'}
Staff: {'✅ Yes' if data.get('is_staff') else '❌ No'}
Date Joined: {data['date_joined']}

Profile Status: {'❌ Expired' if profile.get('expired') else '✅ Active'}
Expiry Date: {profile.get('expiry_date', 'N/A')}
"""
            await update.message.reply_text(message)
        else:
            await update.message.reply_text(
                f"❌ Error: {response.json().get('detail', 'Unknown error')}"
            )

    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")


async def user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get user by ID"""
    telegram_user_id = update.effective_user.id

    # Check if user is logged in
    if telegram_user_id not in user_tokens:
        await update.message.reply_text(
            "❌ You need to login first!\n"
            "Use: /login <username> <password>"
        )
        return

    if len(context.args) != 1:
        await update.message.reply_text(
            "Usage: /user <user_id>\n"
            "Example: /user 1"
        )
        return

    user_id = context.args[0]
    token = user_tokens[telegram_user_id]

    try:
        # Call API to get user info by ID
        response = requests.get(
            f"{API_BASE_URL}/users/{user_id}/",
            headers={"Authorization": f"Token {token}"},
            timeout=5
        )

        if response.status_code == 200:
            data = response.json()
            profile = data.get('profile', {})

            message = f"""
👤 User Profile:

ID: {data['id']}
Username: {data['username']}
Email: {data['email']}
First Name: {data.get('first_name', 'N/A')}
Last Name: {data.get('last_name', 'N/A')}
Active: {'✅ Yes' if data['is_active'] else '❌ No'}
Date Joined: {data['date_joined']}

Profile Status: {'❌ Expired' if profile.get('expired') else '✅ Active'}
"""
            await update.message.reply_text(message)
        elif response.status_code == 403:
            await update.message.reply_text(
                "❌ You don't have permission to view this user's data."
            )
        else:
            await update.message.reply_text(
                f"❌ Error: {response.json().get('detail', 'User not found')}"
            )

    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")


async def list_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all users (admin only)"""
    telegram_user_id = update.effective_user.id

    # Check if user is logged in
    if telegram_user_id not in user_tokens:
        await update.message.reply_text(
            "❌ You need to login first!\n"
            "Use: /login <username> <password>"
        )
        return

    token = user_tokens[telegram_user_id]

    try:
        # Call API to get list of users
        response = requests.get(
            f"{API_BASE_URL}/users/",
            headers={"Authorization": f"Token {token}"},
            timeout=5
        )

        if response.status_code == 200:
            data = response.json()
            users = data.get('results', [])

            if not users:
                await update.message.reply_text("No users found.")
                return

            message = f"👥 User List (Total: {data.get('count', len(users))})\n\n"

            for user in users:
                profile = user.get('profile', {})
                status = '❌ Expired' if profile.get('expired') else '✅ Active'
                is_staff = '👑 Admin' if user.get('is_staff') else '👤 User'

                message += f"{is_staff} | ID: {user['id']} | {user['username']}\n"
                message += f"   Email: {user['email']}\n"
                message += f"   Status: {status}\n\n"

            # Telegram has a message length limit, so split if needed
            if len(message) > 4000:
                # Split into chunks
                chunks = [message[i:i+4000] for i in range(0, len(message), 4000)]
                for chunk in chunks:
                    await update.message.reply_text(chunk)
            else:
                await update.message.reply_text(message)

        elif response.status_code == 403:
            await update.message.reply_text(
                "❌ You don't have permission to list all users.\n"
                "This command is only available for admin users."
            )
        else:
            await update.message.reply_text(
                f"❌ Error: {response.json().get('detail', 'Unknown error')}"
            )

    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send help message"""
    await start(update, context)


def main():
    """Start the bot"""
    if TELEGRAM_BOT_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN_HERE":
        print("❌ Error: Please set your Telegram bot token in the script!")
        print("Get a token from @BotFather on Telegram")
        return

    print("Starting MMDT Telegram Bot...")

    # Create the Application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Register command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("login", login))
    application.add_handler(CommandHandler("me", me))
    application.add_handler(CommandHandler("user", user))
    application.add_handler(CommandHandler("list", list_users))
    application.add_handler(CommandHandler("help", help_command))

    # Start the bot
    print("✅ Bot is running! Press Ctrl+C to stop.")
    print("Go to Telegram and send /start to your bot")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
