import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler, CommandHandler, MessageHandler, filters
from database.db import get_tutors_collection
from config import SUBJECTS_LIST, GRADE_RANGES, TEACHING_METHODS
from bson.objectid import ObjectId

logger = logging.getLogger(__name__)

# Pagination constants
TUTORS_PER_PAGE = 5

async def student_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show the student menu with available actions."""
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("🔍 Find Tutors", callback_data='search_tutors')],
        [InlineKeyboardButton("ℹ️ Help", callback_data='student_help')]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "👋 Welcome to the Student/Parent Portal!\n\n"
        "You can use the following options:\n"
        "• Use the button below to find tutors\n"
        "• Use /find to search for tutors\n"
        "• Use /help for assistance",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    return 0

async def search_tutors(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the /find command to search for tutors."""
    # Initialize or reset search context
    context.user_data['search_filters'] = {}
    context.user_data['search_page'] = 0
    
    # Show search options
    keyboard = [
        [InlineKeyboardButton("🔍 Search by Subject", callback_data='search_subject')],
        [InlineKeyboardButton("🏫 Search by Grade Level", callback_data='search_grade')],
        [InlineKeyboardButton("📍 Search by Location", callback_data='search_location')],
        [InlineKeyboardButton("👨‍🏫 Show All Tutors", callback_data='show_all')]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            "🔍 *Find Tutors*\n\n"
            "How would you like to search for tutors?",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            "🔍 *Find Tutors*\n\n"
            "How would you like to search for tutors?",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    return 'SEARCH_OPTIONS'

async def handle_search_option(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle search option selection."""
    query = update.callback_query
    await query.answer()
    
    search_type = query.data
    context.user_data['search_type'] = search_type
    
    if search_type == 'search_subject':
        # Create keyboard with subject options
        keyboard = []
        for i in range(0, len(SUBJECTS_LIST), 2):
            row = []
            if i + 1 < len(SUBJECTS_LIST):
                row.extend([
                    InlineKeyboardButton(SUBJECTS_LIST[i], callback_data=f"subject_{SUBJECTS_LIST[i]}"),
                    InlineKeyboardButton(SUBJECTS_LIST[i+1], callback_data=f"subject_{SUBJECTS_LIST[i+1]}")
                ])
            else:
                row.append(InlineKeyboardButton(SUBJECTS_LIST[i], callback_data=f"subject_{SUBJECTS_LIST[i]}"))
            keyboard.append(row)
        
        keyboard.append([InlineKeyboardButton("🔙 Back", callback_data='back_to_search')])
        
        await query.edit_message_text(
            "📚 Select a subject:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return 'HANDLE_SUBJECT_SELECTION'
    
    elif search_type == 'search_grade':
        # Create keyboard with grade options
        keyboard = [
            [InlineKeyboardButton(grade, callback_data=f"grade_{grade}") for grade in GRADE_RANGES],
            [InlineKeyboardButton("🔙 Back", callback_data='back_to_search')]
        ]
        
        await query.edit_message_text(
            "🎓 Select grade level:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return 'HANDLE_GRADE_SELECTION'
    
    elif search_type == 'search_location':
        await query.edit_message_text(
            "📍 Please enter the location (e.g., Bole, Mexico):",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back", callback_data='back_to_search')]
            ])
        )
        return 'HANDLE_LOCATION_INPUT'
    
    elif search_type == 'show_all':
        return await show_tutors(update, context, {})
    
    elif search_type == 'back_to_search':
        return await search_tutors(update, context)
    
    return await search_tutors(update, context)

async def handle_subject_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle subject selection for tutor search."""
    query = update.callback_query
    await query.answer()
    
    subject = query.data.replace('subject_', '')
    context.user_data['search_filters']['subjects'] = subject
    
    return await show_tutors(update, context, {'subjects': subject})

async def handle_grade_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle grade level selection for tutor search."""
    query = update.callback_query
    await query.answer()
    
    grade = query.data.replace('grade_', '')
    return await show_tutors(update, context, {'grades': grade})

async def handle_location_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle location input for tutor search."""
    if update.callback_query:
        return await search_tutors(update, context)
    
    location = update.message.text
    return await show_tutors(update, context, {'location': location})

async def show_tutors(update: Update, context: ContextTypes.DEFAULT_TYPE, filters: dict) -> int:
    """Show tutors based on search filters with pagination."""
    tutors = get_tutors_collection()
    
    # Build query with filters
    query = {'status': 'approved'}
    
    if 'subjects' in filters:
        query['subjects'] = filters['subjects']
    if 'grades' in filters:
        query['grades'] = filters['grades']
    if 'location' in filters:
        query['location'] = {'$regex': filters['location'], '$options': 'i'}
    
    # Get pagination info
    page = context.user_data.get('search_page', 0)
    skip = page * TUTORS_PER_PAGE
    
    # Get tutors with pagination
    total_tutors = tutors.count_documents(query)
    tutor_list = list(tutors.find(query).skip(skip).limit(TUTORS_PER_PAGE))
    
    if not tutor_list and page == 0:
        message = "🔍 No tutors found matching your criteria."
        if update.callback_query:
            await update.callback_query.edit_message_text(
                message,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Back to Search", callback_data='back_to_search')]
                ])
            )
        else:
            await update.message.reply_text(
                message,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Back to Search", callback_data='back_to_search')]
                ])
            )
        return 'SEARCH_OPTIONS'
    
    # Send each tutor as a separate message with photo if available
    for tutor in tutor_list:
        tutor_info = (
            f"👤 *{tutor.get('name', 'N/A')}*\n"
            f"🏫 {tutor.get('university', 'N/A')}\n"
            f"📚 *Subjects:* {', '.join(tutor.get('subjects', []))}\n"
            f"🎓 *Grades:* {tutor.get('grades', 'N/A')}\n"
            f"📍 *Location:* {tutor.get('location', 'N/A')}\n"
            f"📞 *Contact:* {os.getenv('ADMIN_NUMBER', 'Contact Admin')}\n"
            f"📅 *Member since:* {tutor.get('registration_date', 'N/A')}\n"
        )
        
        # Create contact button with admin's number
        keyboard = []
        admin_number = os.getenv('ADMIN_NUMBER', '').strip()
        
        if admin_number:
            # Format the number for display (remove + and any non-digit characters)
            display_number = ''.join(filter(str.isdigit, admin_number))
            # Create a WhatsApp link which is more reliable than tel: on mobile
            whatsapp_url = f"https://wa.me/{display_number}"
            
            keyboard.append([
                InlineKeyboardButton("📞 Contact Admin", url=whatsapp_url)
            ])
        else:
            keyboard.append([
                InlineKeyboardButton("ℹ️ Contact information not available", callback_data="no_contact")
            ])
            
        # Add view more tutors button
        keyboard.append([InlineKeyboardButton("🔍 View More Tutors", callback_data='show_more_tutors')])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Send tutor info with photo if available
        if tutor.get('profile_photo') and update.callback_query:
            try:
                await update.callback_query.message.reply_photo(
                    photo=tutor['profile_photo'],
                    caption=tutor_info,
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
            except Exception as e:
                logger.error(f"Error sending tutor photo: {e}")
                await update.callback_query.message.reply_text(
                    f"{tutor_info}\n\n⚠️ Could not load profile photo",
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
        elif update.callback_query:
            await update.callback_query.message.reply_text(
                tutor_info,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        else:
            if tutor.get('profile_photo'):
                try:
                    await update.message.reply_photo(
                        photo=tutor['profile_photo'],
                        caption=tutor_info,
                        reply_markup=reply_markup,
                        parse_mode='Markdown'
                    )
                except Exception as e:
                    logger.error(f"Error sending tutor photo: {e}")
                    await update.message.reply_text(
                        f"{tutor_info}\n\n⚠️ Could not load profile photo",
                        reply_markup=reply_markup,
                        parse_mode='Markdown'
                    )
            else:
                await update.message.reply_text(
                    tutor_info,
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
    
    # Add pagination controls at the end
    keyboard = []
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("⬅️ Previous", callback_data='prev_page'))
    if (page + 1) * TUTORS_PER_PAGE < total_tutors:
        nav_buttons.append(InlineKeyboardButton("Next ➡️", callback_data='next_page'))
    
    if nav_buttons:
        keyboard.append(nav_buttons)
    
    keyboard.extend([
        [InlineKeyboardButton("🔍 New Search", callback_data='back_to_search')],
        [InlineKeyboardButton("🏠 Back to Main Menu", callback_data='back_to_main')]
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.message.reply_text(
            f"Showing tutors {skip + 1} to {min(skip + len(tutor_list), total_tutors)} of {total_tutors}",
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            f"Showing tutors {skip + 1} to {min(skip + len(tutor_list), total_tutors)} of {total_tutors}",
            reply_markup=reply_markup
        )
    
    return 'HANDLE_TUTOR_LIST'

async def handle_pagination(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle pagination for tutor search results."""
    query = update.callback_query
    await query.answer()
    
    action = query.data
    
    if action == 'next_page':
        context.user_data['search_page'] += 1
    elif action == 'prev_page':
        context.user_data['search_page'] = max(0, context.user_data.get('search_page', 1) - 1)
    
    # Get current search filters
    search_filters = context.user_data.get('search_filters', {})
    return await show_tutors(update, context, search_filters)

def get_student_handlers():
    """Return a list of handlers for student-related commands."""
    return [
        CallbackQueryHandler(student_menu, pattern='^student$'),
        CallbackQueryHandler(search_tutors, pattern='^search_tutors$'),
        CallbackQueryHandler(handle_search_option, pattern='^(search_|show_)'),
        CallbackQueryHandler(handle_subject_selection, pattern='^subject_'),
        CallbackQueryHandler(handle_grade_selection, pattern='^grade_'),
        CallbackQueryHandler(handle_pagination, pattern='^(next_page|prev_page)$'),
        CallbackQueryHandler(handle_search_option, pattern='^back_to_'),
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_location_input),
        CommandHandler('find', search_tutors)
    ]
