import logging
import os
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, MessageHandler,
    filters, ContextTypes, ConversationHandler
)
from database.db import db_manager
from config import REGISTER, NAME, UNIVERSITY, DEPARTMENT, YEAR, SUBJECTS, GRADES, METHOD, LOCATION, CONTACT
from handlers.tutor import get_tutor_registration_handler, get_tutor_handlers, select_subjects, get_grades, get_method
from handlers.student import student_menu, search_tutors, get_student_handlers
from handlers.admin import admin_panel, get_admin_handlers, pending_approvals, handle_approval

# Load environment variables
load_dotenv()

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Conversation states are now imported from config.py

# Admin IDs
ADMIN_IDS = [int(id_str.strip()) for id_str in os.getenv('ADMIN_IDS', '').split(',') if id_str.strip()]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Send a welcome message and ask for the user's role."""
    user = update.effective_user
    keyboard = [
        [InlineKeyboardButton("👨‍🎓 I'm a Tutor", callback_data='tutor')],
        [InlineKeyboardButton("👨‍👩‍👧 I'm a Parent", callback_data='student')]
    ]
    if user.id in ADMIN_IDS:
        keyboard.append([InlineKeyboardButton("👨‍💼 Admin Panel", callback_data='admin')])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"👋 Welcome to *Tutor Connect Bot*, {user.first_name}!\n\n"
        "This bot connects university student tutors with students who need help with their studies.\n\n"
        "Please select your role:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    return 0

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle button callbacks from the main menu."""
    query = update.callback_query
    await query.answer()
    
    if query.data == 'tutor':
        await query.edit_message_text(
            "👨‍🏫 *Tutor Menu*\n\n"
            "What would you like to do?\n"
            "• /register - Register as a tutor\n"
            "• /myprofile - View your profile\n"
            "• /update - Update your profile\n"
            "• /help - Show help",
            parse_mode='Markdown'
        )
    
    return 0

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    help_text = """
🤖 *Tutor Connect Bot Help* 🤖

*Available Commands:*
/start - Start the bot and select your role
/help - Show this help message
/register - Register as a tutor
/myprofile - View your tutor profile
/update - Update your tutor profile
/find - Search for tutors

*Support:*
For any issues, please contact @your_support_handle
"""
    await update.message.reply_text(help_text, parse_mode='Markdown')

def main() -> None:
    """Start the bot."""
    # Create the Application
    application = Application.builder().token(os.getenv('BOT_TOKEN')).build()

    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))

    # Add tutor handlers
    for handler in get_tutor_handlers():
        application.add_handler(handler)
    
    # Add tutor registration handler
    application.add_handler(get_tutor_registration_handler())
    
    # Add student handlers
    for handler in get_student_handlers():
        application.add_handler(handler)
    
    # Add admin handlers
    for handler in get_admin_handlers():
        application.add_handler(handler)
    
    # Add main menu button handlers
    application.add_handler(CallbackQueryHandler(button_handler, pattern='^tutor$'))
    application.add_handler(CallbackQueryHandler(student_menu, pattern='^student$'))
    application.add_handler(CallbackQueryHandler(admin_panel, pattern='^admin$'))
    
    # Add conversation handlers
    application.add_handler(CallbackQueryHandler(select_subjects, pattern='^subject_|subjects_done$'))
    application.add_handler(CallbackQueryHandler(get_grades, pattern='^grade_'))
    application.add_handler(CallbackQueryHandler(get_method, pattern='^method_'))
    application.add_handler(CallbackQueryHandler(pending_approvals, pattern='^pending_approvals$'))
    application.add_handler(CallbackQueryHandler(handle_approval, pattern='^(approve|reject)_'))

    # Start the Bot
    application.run_polling()

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        logger.error(f"Error in main: {e}")
    finally:
        # Close the database connection when the bot stops
        db_manager.close_connection()
