import datetime
import logging
import os
import csv
from io import StringIO
from typing import List

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes, 
    CallbackQueryHandler, 
    CommandHandler, 
    MessageHandler, 
    filters,
    ConversationHandler
)
from telegram.constants import ParseMode
from bson.objectid import ObjectId

from database.db import get_tutors_collection, get_users_collection

logger = logging.getLogger(__name__)

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show the admin panel with available actions."""
    query = update.callback_query
    
    # Check if user is admin
    if str(update.effective_user.id) not in os.getenv('ADMIN_IDS', '').split(','):
        if query:
            await query.answer("❌ You don't have permission to access this.", show_alert=True)
        else:
            await update.message.reply_text("❌ You don't have permission to access this.")
        return
    
    if query:
        await query.answer()
    
    # Get pending tutor applications count
    tutors = get_tutors_collection()
    pending_count = tutors.count_documents({"status": "pending"})
    total_tutors = tutors.count_documents({})
    
    keyboard = [
        [InlineKeyboardButton(f"👥 Pending Approvals ({pending_count})", callback_data='pending_approvals')],
        [InlineKeyboardButton("📋 All Tutors", callback_data='all_tutors')],
        [InlineKeyboardButton("📤 Export Data", callback_data='export_data')],
        [InlineKeyboardButton("📢 Broadcast", callback_data='broadcast')]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = (
        f"👨‍💼 *Admin Panel*\n\n"
        f"• Pending Approvals: `{pending_count}`\n"
        f"• Total Tutors: `{total_tutors}`\n\n"
        "Select an option below:"
    )
    
    try:
        if query:
            if query.message.text:  # Only try to edit if the message has text
                await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
            else:
                # If the message doesn't have text (e.g., it's a photo), send a new message
                await query.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
        else:
            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Error in admin_panel: {e}")
        # Fallback: Try to send a new message if editing fails
        if query:
            await query.message.reply_text("Admin Panel\n\n" + text, reply_markup=reply_markup, parse_mode='Markdown')
        else:
            await update.message.reply_text("Admin Panel\n\n" + text, reply_markup=reply_markup, parse_mode='Markdown')

async def pending_approvals(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show pending tutor applications."""
    try:
        if update.callback_query:
            query = update.callback_query
            await query.answer()
        
        tutors = get_tutors_collection()
        pending_tutors = list(tutors.find({"status": "pending"}).sort("_id", -1).limit(10))
        
        if not pending_tutors:
            message = "✅ No pending tutor applications at the moment."
            reply_markup = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back to Admin Panel", callback_data='admin')]
            ])
            
            if update.callback_query:
                await query.edit_message_text(message, reply_markup=reply_markup)
            else:
                await update.message.reply_text(message, reply_markup=reply_markup)
            return
        
        tutor = pending_tutors[0]
        tutor_id = str(tutor['_id'])
        
        # Ensure we have a valid ObjectId
        from bson import ObjectId
        if not ObjectId.is_valid(tutor_id):
            raise ValueError("Invalid tutor ID format")
    
        # Prepare tutor info
        tutor_info = (
            f"👤 *{tutor.get('name', 'N/A')}*\n"
            f"🏫 {tutor.get('university', 'N/A')} - {tutor.get('department', 'N/A')}\n"
            f"📚 *Subjects:* {', '.join(tutor.get('subjects', []))}\n"
            f"🎓 *Grades:* {tutor.get('grades', 'N/A')}\n"
            f"📍 *Location:* {tutor.get('location', 'N/A')}\n"
            f"📞 *Contact:* {tutor.get('contact', 'N/A')}\n"
            f"📅 *Registered:* {tutor.get('registration_date', 'N/A')}"
        )
        
        # Get profile photo if available
        profile_photo = tutor.get('profile_photo')
        
        # Create approve/reject buttons
        keyboard = [
            [
                InlineKeyboardButton("✅ Approve", callback_data=f"approve_{tutor_id}"),
                InlineKeyboardButton("❌ Reject", callback_data=f"reject_{tutor_id}")
            ],
            [InlineKeyboardButton("🔙 Back to Admin Panel", callback_data='admin')]
        ]
        
        message_text = f"📝 *Tutor Application*\n\n{tutor_info}"
        
        if update.callback_query:
            if profile_photo:
                try:
                    await query.message.reply_photo(
                        photo=profile_photo,
                        caption=message_text,
                        reply_markup=InlineKeyboardMarkup(keyboard),
                        parse_mode='Markdown'
                    )
                    await query.message.delete()
                except Exception as e:
                    logger.error(f"Error sending photo: {e}")
                    await query.edit_message_text(
                        f"{message_text}\n\n⚠️ Could not load profile photo",
                        reply_markup=InlineKeyboardMarkup(keyboard),
                        parse_mode='Markdown'
                    )
            else:
                await query.edit_message_text(
                    message_text,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode='Markdown'
                )
        else:
            if profile_photo:
                try:
                    await update.message.reply_photo(
                        photo=profile_photo,
                        caption=message_text,
                        reply_markup=InlineKeyboardMarkup(keyboard),
                        parse_mode='Markdown'
                    )
                except Exception as e:
                    logger.error(f"Error sending photo: {e}")
                    await update.message.reply_text(
                        f"{message_text}\n\n⚠️ Could not load profile photo",
                        reply_markup=InlineKeyboardMarkup(keyboard),
                        parse_mode='Markdown'
                    )
            else:
                await update.message.reply_text(
                    message_text,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode='Markdown'
                )
    except Exception as e:
        logger.error(f"Error in pending_approvals: {e}")
        error_message = "❌ An error occurred while loading tutor applications. Please try again."
        if update.callback_query:
            await query.edit_message_text(error_message)
        else:
            await update.message.reply_text(error_message)

async def handle_approval(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle tutor approval or rejection."""
    query = update.callback_query
    await query.answer()
    
    # Get the action and tutor ID from the callback data
    action, tutor_id = query.data.split('_', 1)
    tutors = get_tutors_collection()
    
    # Update tutor status
    status = "approved" if action == "approve" else "rejected"
    
    # Convert string ID to ObjectId for MongoDB
    try:
        # Update the tutor status
        result = tutors.update_one(
            {"_id": ObjectId(tutor_id)}, 
            {"$set": {"status": status}}
        )
        
        if result.modified_count == 0:
            await query.edit_message_text("❌ Failed to update tutor status. Please try again.")
            return
        
        # Get the updated tutor document
        tutor = tutors.find_one({"_id": ObjectId(tutor_id)})
        
        # Notify the tutor
        if tutor and 'telegram_id' in tutor:
            try:
                if status == "approved":
                    await context.bot.send_message(
                        chat_id=tutor['telegram_id'],
                        text="🎉 *Your tutor application has been approved!*\n\n"
                             "You can now be found by students searching for tutors. "
                             "Use /myprofile to view your profile or /update to make changes.",
                        parse_mode='Markdown'
                    )
                else:
                    await context.bot.send_message(
                        chat_id=tutor['telegram_id'],
                        text="❌ Your tutor application has been rejected.\n\n"
                             "If you believe this was a mistake, please contact support.",
                        parse_mode='Markdown'
                    )
            except Exception as e:
                logger.error(f"Error notifying tutor: {e}")
                await query.edit_message_text("✅ Tutor status updated, but failed to send notification.")
        
        # Show success message
        await query.edit_message_text(
            f"✅ Tutor has been {status} successfully!"
        )
        
        # Show next pending approval
        await pending_approvals(update, context)
        
    except Exception as e:
        logger.error(f"Error in handle_approval: {e}")
        await query.edit_message_text("❌ An error occurred. Please try again.")

async def all_tutors(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show all approved tutors with pagination."""
    query = update.callback_query
    if query:
        await query.answer()
    
    tutors = get_tutors_collection()
    page = int(context.user_data.get('tutors_page', 0))
    per_page = 5
    skip = page * per_page
    
    # Get total count and paginated tutors with more fields
    total_tutors = tutors.count_documents({"status": "approved"})
    tutor_list = list(tutors.find({"status": "approved"})
                     .skip(skip)
                     .limit(per_page)
                     .sort("name", 1))
    
    if not tutor_list and page == 0:
        message = "No tutors found in the system."
        keyboard = [[InlineKeyboardButton("🔙 Back to Admin Panel", callback_data='admin')]]
    else:
        message = f"📋 *All Tutors* (Page {page + 1}/{(total_tutors + per_page - 1) // per_page or 1})\n\n"
        
        for i, tutor in enumerate(tutor_list, 1):
            # Format tutor details
            tutor_details = (
                f"👤 *{tutor.get('name', 'N/A')}* "
                f"({'✅ Active' if tutor.get('is_active', True) else '❌ Inactive'})\n"
                f"🏫 *University:* {tutor.get('university', 'N/A')} - {tutor.get('department', 'N/A')}\n"
                f"📚 *Subjects:* {', '.join(tutor.get('subjects', ['N/A']))}\n"
                f"🎓 *Levels:* {tutor.get('grades', 'N/A')}\n"
                f"📍 *Location:* {tutor.get('location', 'N/A')}\n"
                f"📞 *Contact:* {tutor.get('contact', 'N/A')}\n"
                f"📅 *Member since:* {tutor.get('registration_date', 'N/A')}\n"
                f"⭐ *Rating:* {tutor.get('rating', 'N/A')} ({tutor.get('reviews_count', 0)} reviews)\n"
                f"💬 *Bio:* {tutor.get('bio', 'No bio provided')[:100]}{'...' if len(tutor.get('bio', '')) > 100 else ''}\n"
                f"🔗 *Profile ID:* `{str(tutor.get('_id', 'N/A'))}`\n"
                "─────────────────────\n\n"
            )
            message += tutor_details
        
        # Create action buttons for each tutor
        keyboard = []
        for tutor in tutor_list:
            tutor_id = str(tutor.get('_id'))
            keyboard.append([
                InlineKeyboardButton(
                    f"👤 {tutor.get('name', 'Tutor')}", 
                    callback_data=f'view_tutor_{tutor_id}'
                )
            ])
        
        # Add pagination controls
        pagination_row = []
        if page > 0:
            pagination_row.append(InlineKeyboardButton("⬅️ Previous", callback_data=f'tutors_page_{page-1}'))
        if (page + 1) * per_page < total_tutors:
            pagination_row.append(InlineKeyboardButton("Next ➡️", callback_data=f'tutors_page_{page+1}'))
        
        if pagination_row:
            keyboard.append(pagination_row)
            
        # Add admin actions and navigation
        keyboard.extend([
            [
                InlineKeyboardButton("📤 Export All Data", callback_data='export_data'),
                InlineKeyboardButton("📢 Broadcast", callback_data='broadcast')
            ],
            [InlineKeyboardButton("🔙 Back to Admin Panel", callback_data='admin')]
        ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    try:
        if query:
            if query.message.text:  # Only try to edit if the message has text
                await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')
            else:
                # If the message doesn't have text (e.g., it's a photo), send a new message
                await query.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')
        else:
            await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Error in all_tutors: {e}")
        # Fallback: Try to send a new message if editing fails
        if query:
            await query.message.reply_text("Showing tutors:" + message, reply_markup=reply_markup, parse_mode='Markdown')
        else:
            await update.message.reply_text("An error occurred. Here are the tutors:" + message, reply_markup=reply_markup, parse_mode='Markdown')

async def export_data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Export tutor data to a CSV file."""
    query = update.callback_query
    if query:
        await query.answer("Preparing data export...")
    
    tutors = get_tutors_collection()
    tutor_list = list(tutors.find({}, {'_id': 0, 'profile_photo': 0, 'telegram_id': 0}))
    
    if not tutor_list:
        message = "No tutor data available to export."
        reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Admin Panel", callback_data='admin')]])
        if query:
            await query.edit_message_text(message, reply_markup=reply_markup)
        else:
            await update.message.reply_text(message, reply_markup=reply_markup)
        return
    
    # Create CSV content
    import csv
    from io import StringIO
    
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=tutor_list[0].keys())
    writer.writeheader()
    writer.writerows(tutor_list)
    
    # Send the file
    output.seek(0)
    filename = f"tutors_export_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    if query:
        await query.message.reply_document(
            document=output.getvalue().encode('utf-8'),
            filename=filename,
            caption="📊 Here's the exported tutor data.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Admin Panel", callback_data='admin')]])
        )
    else:
        await update.message.reply_document(
            document=output.getvalue().encode('utf-8'),
            filename=filename,
            caption="📊 Here's the exported tutor data.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Admin Panel", callback_data='admin')]])
        )

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the broadcast message process."""
    query = update.callback_query
    
    # Check if user is admin
    if str(update.effective_user.id) not in os.getenv('ADMIN_IDS', '').split(','):
        if query:
            await query.answer("❌ You don't have permission to use this feature.", show_alert=True)
        return -1
    
    if query:
        await query.answer()
        await query.message.reply_text(
            "📢 *Broadcast Message*\n\n"
            "Please enter the message you want to broadcast to all users.\n"
            "You can use markdown formatting: *bold*, _italic_, `code`.",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Cancel", callback_data='admin')]
            ])
        )
    else:
        await update.message.reply_text(
            "📢 *Broadcast Message*\n\n"
            "Please enter the message you want to broadcast to all users.\n"
            "You can use markdown formatting: *bold*, _italic_, `code`.",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Cancel", callback_data='admin')]
            ])
        )
    
    # Store the original message ID for cleanup
    if query and query.message:
        context.user_data['broadcast_message_id'] = query.message.message_id
    
    return 'AWAITING_BROADCAST_MESSAGE'

async def handle_broadcast_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the broadcast message and send to all users."""
    try:
        message_text = update.message.text
        
        # Get all users collection (both tutors and students)
        users_collection = get_users_collection()
        tutors_collection = get_tutors_collection()
        
        # Get all users with chat_id (telegram_id)
        all_users = list(users_collection.find({"chat_id": {"$exists": True, "$ne": None}}))
        
        # If no users found in users collection, try to get from tutors collection
        if not all_users:
            all_users = list(tutors_collection.find({"chat_id": {"$exists": True, "$ne": None}}))
        
        # If still no users, try to find any ID field that might be a Telegram ID
        if not all_users:
            all_users = list(users_collection.find({}) + tutors_collection.find({}))
            
            # Try to find any numeric ID field
            user_ids = set()
            for user in all_users:
                for key, value in user.items():
                    if isinstance(value, (int, str)) and str(value).isdigit() and int(value) > 10000:
                        user_ids.add(int(value))
            
            if user_ids:
                all_users = [{"chat_id": uid} for uid in user_ids]
        
        # Get unique chat IDs
        chat_ids = set()
        for user in all_users:
            if 'chat_id' in user and user['chat_id']:
                try:
                    chat_ids.add(int(user['chat_id']))
                except (ValueError, TypeError):
                    continue
        
        chat_ids = list(chat_ids)
        
        if not chat_ids:
            await update.message.reply_text(
                "❌ No active users found to send the broadcast message to.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Back to Admin Panel", callback_data='admin')]
                ])
            )
            return -1
        
        sent_count = 0
        failed_count = 0
        failed_users = []
        
        # Send initial message
        progress_message = await update.message.reply_text(
            f"📤 Preparing to send broadcast to {len(user_ids)} users..."
        )
        
        # Send the message to each user
        sent_count = 0
        failed_count = 0
        failed_users = []
        
        # Format the broadcast message with a nice header and footer
        broadcast_msg = (
            f"📢 *Announcement from Admin*\n\n"
            f"{message_text}\n\n"
            f"_This is a broadcast message. Please do not reply to this message._"
        )
        
        # Send initial status message
        status_message = await update.message.reply_text(
            f"📤 Sending broadcast to {len(chat_ids)} users...\n"
            "🔄 0% complete (0/0 sent, 0 failed)"
        )
        
        # Send messages to all chat IDs
        for i, chat_id in enumerate(chat_ids, 1):
            try:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=broadcast_msg,
                    parse_mode=ParseMode.MARKDOWN
                )
                sent_count += 1
            except Exception as e:
                logger.error(f"Failed to send message to chat {chat_id}: {e}")
                failed_count += 1
                failed_users.append(str(chat_id))
            
            # Update status every 5 messages or if it's the last message
            if i % 5 == 0 or i == len(chat_ids):
                progress = int((i / len(chat_ids)) * 100)
                status_text = (
                    f"📤 Sending broadcast to {len(chat_ids)} users...\n"
                    f"🔄 {progress}% complete ({i}/{len(chat_ids)} sent, {failed_count} failed)"
                )
                
                # Add failed users if any (show only last 5 to avoid message being too long)
                if failed_users:
                    status_text += f"\n\n❌ Failed to send to: {', '.join(failed_users[-5:])}"
                    if len(failed_users) > 5:
                        status_text += f" and {len(failed_users) - 5} more..."
                
                try:
                    await status_message.edit_text(status_text)
                except Exception as e:
                    logger.error(f"Failed to update status message: {e}")
        
        # Send final result
        result_message = (
            f"✅ *Broadcast Completed*\n\n"
            f"📤 *Sent to:* {sent_count} users\n"
            f"❌ *Failed:* {failed_count} users"
        )
        
        # Add failed users to the result message (limited to first 10)
        if failed_users:
            result_message += "\n\n*Failed to send to:*"
            for i in range(0, min(10, len(failed_users)), 5):
                result_message += f"\n• {', '.join(failed_users[i:i+5])}"
            
            if len(failed_users) > 10:
                result_message += f"\n... and {len(failed_users) - 10} more"
        
        # Send the final result
        await update.message.reply_text(
            result_message,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back to Admin Panel", callback_data='admin')]
            ])
        )
        
        # Clean up the broadcast message if it exists
        if 'broadcast_message_id' in context.user_data:
            try:
                await context.bot.delete_message(
                    chat_id=update.effective_chat.id,
                    message_id=context.user_data['broadcast_message_id']
                )
            except Exception as e:
                logger.error(f"Error cleaning up message: {e}")
            
            del context.user_data['broadcast_message_id']
        
        return -1  # End conversation
        
    except Exception as e:
        logger.error(f"Error in broadcast: {e}", exc_info=True)
        await update.message.reply_text(
            "❌ An error occurred while sending the broadcast. Please try again.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back to Admin Panel", callback_data='admin')]
            ])
        )
        return -1
    
    return await admin_panel(update, context)

async def view_tutor_details(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show detailed information about a specific tutor."""
    query = update.callback_query
    await query.answer()
    
    try:
        tutor_id = query.data.replace('view_tutor_', '')
        tutors = get_tutors_collection()
        tutor = tutors.find_one({"_id": ObjectId(tutor_id)})
        
        if not tutor:
            await query.edit_message_text("❌ Tutor not found.")
            return
            
        # Format registration date if it exists
        reg_date = tutor.get('registration_date')
        if isinstance(reg_date, datetime.datetime):
            reg_date = reg_date.strftime("%Y-%m-%d %H:%M")
        
        # Get profile photo if exists
        profile_photo = tutor.get('profile_photo')
        
        # Format tutor details with markdown
        tutor_info = (
            f"👤 *{tutor.get('name', 'N/A')}* "
            f"({'✅ Active' if tutor.get('is_active', True) else '❌ Inactive'})\n\n"
            f"📧 *Email:* `{tutor.get('email', 'N/A')}`\n"
            f"📞 *Phone:* `{tutor.get('contact', 'N/A')}`\n"
            f"🏫 *University:* {tutor.get('university', 'N/A')}\n"
            f"🎓 *Department:* {tutor.get('department', 'N/A')}\n"
            f"📚 *Subjects:* {', '.join(tutor.get('subjects', ['N/A']))}\n"
            f"🎯 *Levels:* {tutor.get('grades', 'N/A')}\n"
            f"📍 *Location:* {tutor.get('location', 'N/A')}\n"
            f"⭐ *Rating:* {tutor.get('rating', 'N/A')} ({tutor.get('reviews_count', 0)} reviews)\n"
            f"📅 *Member since:* {reg_date or 'N/A'}\n"
            f"🔗 *Profile ID:* `{str(tutor.get('_id', 'N/A'))}`\n\n"
            f"📝 *Bio:*\n{tutor.get('bio', 'No bio provided')}\n"
        )
        
        # Create keyboard with all buttons
        keyboard = [
            [
                InlineKeyboardButton("✏️ Edit Tutor", callback_data=f'edit_tutor_{tutor_id}'),
                InlineKeyboardButton("🔒 Toggle Status", callback_data=f'toggle_status_{tutor_id}')
            ],
            [
                InlineKeyboardButton("📨 Contact", 
                    url=f"https://t.me/{tutor.get('username', '').lstrip('@')}" if tutor.get('username') else None, 
                    callback_data='no_username' if not tutor.get('username') else None
                ),
                InlineKeyboardButton("📞 Show Phone", 
                    callback_data=f'show_phone_{tutor_id}'
                ) if tutor.get('contact') else InlineKeyboardButton("📞 No Phone", callback_data='no_phone')
            ],
            [
                InlineKeyboardButton("📊 View Reviews", callback_data=f'reviews_{tutor_id}'),
                InlineKeyboardButton("📋 View Sessions", callback_data=f'sessions_{tutor_id}')
            ],
            [
                InlineKeyboardButton("⬅️ Back to List", callback_data='all_tutors'),
                InlineKeyboardButton("🏠 Admin Panel", callback_data='admin')
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        try:
            # If there's a photo in the current message, delete it first
            if query.message.photo:
                await query.message.delete()
            
            # If tutor has a profile photo, send it with caption
            if profile_photo:
                await context.bot.send_photo(
                    chat_id=query.message.chat_id,
                    photo=profile_photo,
                    caption=tutor_info,
                    reply_markup=reply_markup,
                    parse_mode='Markdown',
                    reply_to_message_id=query.message.message_id
                )
            else:
                # If no photo, just send the text with buttons
                await context.bot.send_message(
                    chat_id=query.message.chat_id,
                    text=tutor_info,
                    reply_markup=reply_markup,
                    parse_mode='Markdown',
                    reply_to_message_id=query.message.message_id
                )
        except Exception as e:
            logger.error(f"Error sending tutor details: {e}")
            await query.edit_message_text(
                "❌ Error loading tutor details. Please try again.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("⬅️ Back to List", callback_data='all_tutors')],
                    [InlineKeyboardButton("🏠 Admin Panel", callback_data='admin')]
                ])
            )
            
    except Exception as e:
        logger.error(f"Error in view_tutor_details: {e}")
        await query.edit_message_text("❌ An error occurred while loading tutor details.")

async def handle_show_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show tutor's phone number when requested."""
    query = update.callback_query
    await query.answer()
    
    try:
        tutor_id = query.data.replace('show_phone_', '')
        tutors = get_tutors_collection()
        tutor = tutors.find_one({"_id": ObjectId(tutor_id)})
        
        if not tutor or not tutor.get('contact'):
            await query.answer("❌ Phone number not available.", show_alert=True)
            return
            
        # Show phone number in an alert
        await query.answer(
            f"📞 Tutor's phone number: {tutor['contact']}", 
            show_alert=True
        )
    except Exception as e:
        logger.error(f"Error showing phone number: {e}")
        await query.answer("❌ Error retrieving phone number.", show_alert=True)

async def handle_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel and end the conversation."""
    query = update.callback_query
    if query:
        await query.answer()
        await query.edit_message_text("Operation cancelled.")
    else:
        await update.message.reply_text("Operation cancelled.")
    
    return await admin_panel(update, context)

def get_admin_handlers():
    """Return a list of handlers for admin commands."""
    # Create a conversation handler for the broadcast feature
    broadcast_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(broadcast, pattern='^broadcast$')
        ],
        states={
            'AWAITING_BROADCAST_MESSAGE': [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    handle_broadcast_message
                ),
                CallbackQueryHandler(admin_panel, pattern='^admin$')
            ]
        },
        fallbacks=[
            CommandHandler('cancel', handle_cancel),
            CallbackQueryHandler(admin_panel, pattern='^admin$')
        ],
        map_to_parent={
            -1: 'ADMIN_PANEL'  # Return to admin panel when done
        }
    )
    
    return [
        # Conversation handler for the admin panel
        ConversationHandler(
            entry_points=[
                CommandHandler('admin', admin_panel),
                CallbackQueryHandler(admin_panel, pattern='^admin$')
            ],
            states={
                'ADMIN_PANEL': [
                    CallbackQueryHandler(handle_approval, pattern='^(approve|reject)_'),
                    CallbackQueryHandler(handle_show_phone, pattern='^show_phone_'),
                    CallbackQueryHandler(all_tutors, pattern='^all_tutors$'),
                    CallbackQueryHandler(export_data, pattern='^export_data$'),
                    CallbackQueryHandler(broadcast, pattern='^broadcast$'),
                    CallbackQueryHandler(view_tutor_details, pattern='^view_tutor_'),
                    CallbackQueryHandler(pending_approvals, pattern='^pending_approvals$'),
                    CallbackQueryHandler(handle_cancel, pattern='^cancel$')
                ]
            },
            fallbacks=[
                CommandHandler('cancel', handle_cancel),
                CallbackQueryHandler(handle_cancel, pattern='^cancel$')
            ]
        ),
        # Add the broadcast handler separately
        broadcast_handler
    ]
