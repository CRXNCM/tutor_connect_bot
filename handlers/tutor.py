import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler, MessageHandler, filters, CommandHandler, ConversationHandler
from database.db import get_tutors_collection
from config import (
    REGISTER, NAME, UNIVERSITY, DEPARTMENT, YEAR, SUBJECTS, GRADES, METHOD, LOCATION, CONTACT, PROFILE_PIC,
    SUBJECTS_LIST, GRADE_RANGES, TEACHING_METHODS
)

logger = logging.getLogger(__name__)

def format_tutor_info(tutor):
    """Format tutor information for display."""
    return (
        f"👤 *{tutor.get('name', 'N/A')}*\n"
        f"🏫 {tutor.get('university', 'N/A')} - {tutor.get('department', 'N/A')}\n"
        f"📅 Year of Study: {tutor.get('year', 'N/A')}\n"
        f"📚 *Subjects:* {', '.join(tutor.get('subjects', []))}\n"
        f"🎓 *Grades:* {tutor.get('grades', 'N/A')}\n"
        f"🏠 *Teaching Method:* {tutor.get('method', 'N/A')}\n"
        f"📍 *Location:* {tutor.get('location', 'N/A')}\n"
        f"📞 *Contact:* {tutor.get('contact', 'N/A')}\n"
        f"✅ *Status:* {tutor.get('status', 'pending').capitalize()}"
    )

# These are now imported from config.py

async def start_registration(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the registration process for tutors."""
    user = update.effective_user
    tutors = get_tutors_collection()
    
    # Check if user is already registered
    existing_tutor = tutors.find_one({"telegram_id": user.id})
    
    if existing_tutor:
        await update.message.reply_text(
            "You are already registered as a tutor!\n"
            "Use /myprofile to view your profile or /update to make changes."
        )
        return ConversationHandler.END
    
    await update.message.reply_text(
        "👨‍🏫 *Tutor Registration*\n\n"
        "Let's get you registered as a tutor! This will only take a few minutes.\n\n"
        "Please enter your *full name*:",
        parse_mode='Markdown'
    )
    return NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Store the tutor's name and ask for university."""
    context.user_data['name'] = update.message.text
    await update.message.reply_text(
        "🏫 *University*\n\n"
        "Please enter the name of your university:",
        parse_mode='Markdown'
    )
    return UNIVERSITY

async def get_university(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Store the university and ask for department."""
    context.user_data['university'] = update.message.text
    await update.message.reply_text(
        "📚 *Department*\n\n"
        "What is your department/faculty?",
        parse_mode='Markdown'
    )
    return DEPARTMENT

async def get_department(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Store the department and ask for year of study."""
    context.user_data['department'] = update.message.text
    await update.message.reply_text(
        "🎓 *Year of Study*\n\n"
        "What year are you in? (e.g., 1st Year, 2nd Year, etc.)",
        parse_mode='Markdown'
    )
    return YEAR

async def get_year(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Store the year of study and ask for subjects."""
    context.user_data['year'] = update.message.text
    
    # Create inline keyboard for subject selection
    keyboard = []
    for i in range(0, len(SUBJECTS_LIST), 2):
        row = []
        for subject in SUBJECTS_LIST[i:i+2]:
            row.append(InlineKeyboardButton(subject, callback_data=f"subject_{subject}"))
        keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton("Done", callback_data="subjects_done")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "📚 *Subjects*\n\n"
        "Select the subjects you can teach (you can select multiple):\n"
        "Click 'Done' when finished.",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    
    context.user_data['selected_subjects'] = []
    return SUBJECTS

async def select_subjects(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle subject selection."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "subjects_done":
        if not context.user_data.get('selected_subjects'):
            await query.edit_message_text(
                "Please select at least one subject!",
                reply_markup=query.message.reply_markup
            )
            return SUBJECTS
            
        # Create keyboard for grade range selection
        keyboard = [
            [InlineKeyboardButton(grade, callback_data=f"grade_{grade}")] 
            for grade in GRADE_RANGES
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "👨‍🎓 *Grade Range*\n\n"
            "Select the grade range you can teach:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        return GRADES
    
    # Toggle subject selection
    subject = query.data.replace("subject_", "")
    if subject in context.user_data['selected_subjects']:
        context.user_data['selected_subjects'].remove(subject)
    else:
        context.user_data['selected_subjects'].append(subject)
    
    # Update the message to show selected subjects
    selected_text = "\n".join([f"✓ {s}" for s in context.user_data['selected_subjects']])
    await query.edit_message_text(
        f"📚 *Selected Subjects*\n\n{selected_text}\n\n"
        "Select more subjects or click 'Done' to continue:",
        reply_markup=query.message.reply_markup,
        parse_mode='Markdown'
    )
    
    return SUBJECTS

async def get_grades(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Store the grade range and ask for teaching method."""
    query = update.callback_query
    await query.answer()
    
    context.user_data['grades'] = query.data.replace("grade_", "")
    
    # Create keyboard for teaching method selection
    keyboard = [
        [InlineKeyboardButton(method, callback_data=f"method_{method}")] 
        for method in TEACHING_METHODS
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "🏠 *Teaching Method*\n\n"
        "How would you prefer to teach?",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    return METHOD

async def get_method(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Store the teaching method and ask for location."""
    query = update.callback_query
    await query.answer()
    
    context.user_data['method'] = query.data.replace("method_", "")
    
    await query.edit_message_text(
        "📍 *Location*\n\n"
        "In which area do you prefer to teach? (e.g., Bole, Mexico, etc.)",
        parse_mode='Markdown'
    )
    return LOCATION

async def get_location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Store the location and ask for contact information."""
    context.user_data['location'] = update.message.text
    
    await update.message.reply_text(
        "📞 *Contact Information*\n\n"
        "Please provide your contact information (Telegram username or phone number):",
        parse_mode='Markdown'
    )
    return CONTACT

async def get_contact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Store the contact information and ask for profile picture."""
    contact = update.message.text
    
    # Validate contact (simple check for @username or phone number)
    if not (contact.startswith('@') or contact.replace('+', '').isdigit()):
        await update.message.reply_text(
            "❌ Invalid contact information. "
            "Please provide a valid Telegram username (starting with @) or phone number."
        )
        return CONTACT
    
    context.user_data['contact'] = contact
    
    # Ask for profile picture
    await update.message.reply_text(
        "📸 *Profile Picture*\n\n"
        "Please upload a clear profile picture. This will help students recognize you.\n"
        "You can skip this step by sending /skip",
        parse_mode='Markdown'
    )
    
    return PROFILE_PIC
    return ConversationHandler.END

async def myprofile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show the tutor's profile information."""
    user = update.effective_user
    tutors = get_tutors_collection()
    
    tutor = tutors.find_one({"telegram_id": user.id})
    
    if not tutor:
        if update.callback_query:
            await update.callback_query.answer()
            await update.callback_query.edit_message_text(
                "You are not registered as a tutor yet. Use /register to create your profile."
            )
        else:
            await update.message.reply_text(
                "You are not registered as a tutor yet. Use /register to create your profile."
            )
        return
    
    # Format tutor information
    message = format_tutor_info(tutor)
    
    # Create keyboard
    keyboard = [
        [InlineKeyboardButton("✏️ Update Profile", callback_data="update_profile")],
        [InlineKeyboardButton("🔄 Refresh", callback_data="myprofile")],
        [InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_main")]
    ]
    
    # If there's a profile photo, send the photo with caption
    if tutor.get('profile_photo'):
        if update.callback_query:
            await update.callback_query.answer()
            await update.callback_query.message.reply_photo(
                photo=tutor['profile_photo'],
                caption=message,
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            # Delete the previous message if it's a callback query
            try:
                await update.callback_query.message.delete()
            except Exception as e:
                logger.warning(f"Could not delete message: {e}")
        else:
            await update.message.reply_photo(
                photo=tutor['profile_photo'],
                caption=message,
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
    else:
        if update.callback_query:
            await update.callback_query.answer()
            await update.callback_query.edit_message_text(
                message,
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            await update.message.reply_text(
                message,
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

async def start_update(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the profile update process."""
    query = update.callback_query
    if query:
        await query.answer()
        user = query.from_user
    else:
        user = update.effective_user
    
    tutors = get_tutors_collection()
    tutor = tutors.find_one({"telegram_id": user.id})
    
    if not tutor:
        message = "You haven't registered as a tutor yet. Use /register to create your profile."
        if query:
            await query.edit_message_text(message)
        else:
            await update.message.reply_text(message)
        return ConversationHandler.END
    
    # Store tutor data in context for reference
    context.user_data['tutor_data'] = tutor
    
    # Show update options
    keyboard = [
        [InlineKeyboardButton("✏️ Name", callback_data='update_name')],
        [InlineKeyboardButton("🏫 University & Department", callback_data='update_uni')],
        [InlineKeyboardButton("📅 Year of Study", callback_data='update_year')],
        [InlineKeyboardButton("📚 Subjects", callback_data='update_subjects')],
        [InlineKeyboardButton("🎓 Grade Levels", callback_data='update_grades')],
        [InlineKeyboardButton("🏠 Teaching Method", callback_data='update_method')],
        [InlineKeyboardButton("📍 Location", callback_data='update_location')],
        [InlineKeyboardButton("📞 Contact Info", callback_data='update_contact')],
        [InlineKeyboardButton("❌ Cancel", callback_data='cancel_update')]
    ]
    
    message = "🔄 *Update Profile*\n\nWhat would you like to update?"
    
    if query:
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    return 'SELECT_FIELD'

async def select_field(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle field selection for update."""
    query = update.callback_query
    await query.answer()
    
    action = query.data
    
    if action == 'cancel_update':
        await query.edit_message_text("Update cancelled. Your profile remains unchanged.")
        return ConversationHandler.END
    
    context.user_data['update_field'] = action
    
    field_display = {
        'update_name': "full name",
        'update_uni': "university and department",
        'update_year': "year of study",
        'update_subjects': "subjects",
        'update_grades': "grade levels",
        'update_method': "teaching method",
        'update_location': "location",
        'update_contact': "contact information"
    }
    
    await query.edit_message_text(
        f"✏️ Please enter your new {field_display.get(action, action.replace('update_', ''))}:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Cancel", callback_data='cancel_update')]
        ])
    )
    
    return 'GET_NEW_VALUE'

async def get_new_value(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Get and update the new field value."""
    field = context.user_data.get('update_field')
    tutors = get_tutors_collection()
    
    if not field:
        await update.message.reply_text("An error occurred. Please try again.")
        return ConversationHandler.END
    
    update_data = {}
    
    if field == 'update_name':
        update_data['name'] = update.message.text
    elif field == 'update_uni':
        parts = update.message.text.split(' - ', 1)
        if len(parts) == 2:
            update_data['university'] = parts[0].strip()
            update_data['department'] = parts[1].strip()
        else:
            update_data['university'] = update.message.text
    elif field == 'update_year':
        update_data['year'] = update.message.text
    elif field == 'update_subjects':
        # This would need a more complex UI for selection
        subjects = [s.strip() for s in update.message.text.split(',')]
        update_data['subjects'] = [s for s in subjects if s in SUBJECTS_LIST]
    elif field == 'update_grades':
        if update.message.text in GRADE_RANGES:
            update_data['grades'] = update.message.text
    elif field == 'update_method':
        if update.message.text in TEACHING_METHODS:
            update_data['method'] = update.message.text
    elif field == 'update_location':
        update_data['location'] = update.message.text
    elif field == 'update_contact':
        update_data['contact'] = update.message.text
    
    if update_data:
        tutors.update_one(
            {"telegram_id": update.effective_user.id},
            {"$set": update_data}
        )
        
        # Get updated tutor data
        tutor = tutors.find_one({"telegram_id": update.effective_user.id})
        
        await update.message.reply_text(
            "✅ Profile updated successfully!\n\n"
            f"{format_tutor_info(tutor)}\n\n"
            "What would you like to do next?\n"
            "/myprofile - View your profile\n"
            "/update - Update your profile\n"
            "/find - Search for tutors",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text("No changes were made. Please try again with valid input.")
    
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel and end the conversation."""
    if update.message:
        await update.message.reply_text(
            'Operation cancelled. You can start again with /register or /update.'
        )
    elif update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text('Operation cancelled.')
    return ConversationHandler.END

# Update the tutor registration handler to include the update commands
def get_tutor_handlers():
    """Return a list of handlers for tutor commands."""
    update_conv = ConversationHandler(
        entry_points=[
            CommandHandler('update', start_update),
            CallbackQueryHandler(start_update, pattern='^update_profile$')
        ],
        states={
            'SELECT_FIELD': [CallbackQueryHandler(select_field, pattern='^update_')],
            'GET_NEW_VALUE': [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_new_value),
                CallbackQueryHandler(cancel, pattern='^cancel_update$')
            ]
        },
        fallbacks=[
            CommandHandler('cancel', cancel),
            CallbackQueryHandler(cancel, pattern='^cancel$')
        ],
        allow_reentry=True
    )
    
    return [
        update_conv,
        CommandHandler('myprofile', myprofile)
    ]

# Create conversation handler for tutor registration
async def handle_profile_pic(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the profile picture upload and complete registration."""
    # Check if user wants to skip
    if update.message.text and update.message.text.lower() == '/skip':
        profile_photo = None
    else:
        # Get the photo with the best quality
        photo = update.message.photo[-1] if update.message.photo else None
        if not photo:
            await update.message.reply_text(
                "❌ Please send a valid photo or /skip to continue without a profile picture."
            )
            return PROFILE_PIC
        
        # Get the file ID of the photo
        profile_photo = photo.file_id
    
    # Get all user data
    user_data = context.user_data
    telegram_id = update.effective_user.id
    
    # Prepare tutor data
    tutor_data = {
        'telegram_id': telegram_id,
        'name': user_data.get('name'),
        'university': user_data.get('university'),
        'department': user_data.get('department'),
        'year': user_data.get('year'),
        'subjects': user_data.get('selected_subjects', []),
        'grades': user_data.get('grades'),
        'method': user_data.get('method'),
        'location': user_data.get('location'),
        'contact': user_data.get('contact'),
        'profile_photo': profile_photo,
        'status': 'pending',
        'username': update.effective_user.username,
        'registration_date': update.message.date
    }
    
    # Save to database
    tutors = get_tutors_collection()
    tutors.insert_one(tutor_data)
    
    # Send confirmation message
    if profile_photo:
        await update.message.reply_photo(
            photo=profile_photo,
            caption="✅ *Registration Complete!*\n\n"
                  "Thank you for registering as a tutor! Your application is under review. "
                  "You will be notified once your profile is approved.\n\n"
                  "You can use /myprofile to view your profile or /update to make changes.",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            "✅ *Registration Complete!*\n\n"
            "Thank you for registering as a tutor! Your application is under review. "
            "You will be notified once your profile is approved.\n\n"
            "You can use /myprofile to view your profile or /update to make changes.",
            parse_mode='Markdown'
        )
    
    # Clear user data
    context.user_data.clear()
    return ConversationHandler.END

def get_tutor_registration_handler():
    return ConversationHandler(
        entry_points=[CommandHandler('register', start_registration)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            UNIVERSITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_university)],
            DEPARTMENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_department)],
            YEAR: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_year)],
            SUBJECTS: [CallbackQueryHandler(select_subjects, pattern='^subject_|subjects_done$')],
            GRADES: [CallbackQueryHandler(get_grades, pattern='^grade_')],
            METHOD: [CallbackQueryHandler(get_method, pattern='^method_')],
            LOCATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_location)],
            CONTACT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_contact)],
            PROFILE_PIC: [
                MessageHandler(filters.PHOTO | filters.COMMAND, handle_profile_pic),
                MessageHandler(~filters.PHOTO & ~filters.COMMAND, 
                             lambda u, c: u.message.reply_text("Please send a photo or /skip"))
            ]
        },
        fallbacks=[
            CommandHandler('cancel', cancel),
            CallbackQueryHandler(cancel, pattern='^cancel$'),
            CommandHandler('skip', handle_profile_pic)
        ],
        allow_reentry=True
    )
