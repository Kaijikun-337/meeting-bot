from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from datetime import datetime, timedelta
import pytz

from app.bot.keyboards import (
    change_type_keyboard, lessons_keyboard, days_keyboard,
    hours_keyboard, minutes_keyboard, confirm_keyboard, approval_keyboard
)
from app.services.user_service import (
    get_user, get_user_role, get_students_in_group, 
    get_teacher_for_group, get_teacher_groups
)
from app.services.lesson_service import (
    get_upcoming_lessons, can_change_lesson, add_lesson_override
)
from app.services.request_service import (
    create_change_request, get_request, add_approval
)
from app.config import Config

# States
SELECTING_LESSON, SELECTING_CHANGE_TYPE, SELECTING_DAY, SELECTING_HOUR, SELECTING_MINUTE, CONFIRMING = range(6)


async def change_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /change command."""
    chat_id = str(update.effective_chat.id)
    user = get_user(chat_id)
    
    if not user:
        await update.message.reply_text(
            "❌ You're not registered!\n"
            "Use /start to register first."
        )
        return ConversationHandler.END
    
    # Get meetings for this user
    meetings = Config.load_meetings()
    
    if user['role'] == 'student':
        # Filter meetings for student's group
        user_meetings = [m for m in meetings if m.get('group_name') == user.get('group_name')]
    else:
        # Teacher - get meetings for their groups
        teacher_groups = get_teacher_groups(chat_id)
        group_names = [g['group_name'] for g in teacher_groups]
        user_meetings = [m for m in meetings if m.get('group_name') in group_names]
    
    if not user_meetings:
        await update.message.reply_text("❌ No lessons found for you.")
        return ConversationHandler.END
    
    # For simplicity, use first meeting (you can expand to show meeting selection)
    meeting = user_meetings[0]
    context.user_data['meeting'] = meeting
    
    # Get upcoming lessons
    upcoming = get_upcoming_lessons(meeting['id'], days_ahead=14)
    
    if not upcoming:
        await update.message.reply_text("❌ No upcoming lessons found.")
        return ConversationHandler.END
    
    await update.message.reply_text(
        f"📚 {meeting['title']}\n\n"
        "Select a lesson to change:",
        reply_markup=lessons_keyboard(upcoming)
    )
    return SELECTING_LESSON


async def lesson_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle lesson date selection."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "cancel_action":
        await query.edit_message_text("❌ Action cancelled.")
        return ConversationHandler.END
    
    date = query.data.replace("lesson_", "")
    context.user_data['selected_date'] = date
    
    # Check if change is allowed (2+ hours before)
    meeting = context.user_data['meeting']
    can_change, reason = can_change_lesson(meeting, date)
    
    if not can_change:
        await query.edit_message_text(f"❌ Cannot change: {reason}")
        return ConversationHandler.END
    
    await query.edit_message_text(
        f"Selected: {date}\n\n"
        "What do you want to do?",
        reply_markup=change_type_keyboard()
    )
    return SELECTING_CHANGE_TYPE


async def change_type_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle postpone/cancel selection."""
    query = update.callback_query
    await query.answer()
    
    change_type = query.data.replace("change_", "")  # postpone or cancel
    context.user_data['change_type'] = change_type
    
    if change_type == 'cancel':
        # Go straight to confirmation
        date = context.user_data['selected_date']
        meeting = context.user_data['meeting']
        
        await query.edit_message_text(
            f"⚠️ Cancel lesson?\n\n"
            f"📚 {meeting['title']}\n"
            f"📅 {date}\n\n"
            "This will notify all participants.",
            reply_markup=confirm_keyboard()
        )
        return CONFIRMING
    else:
        # Postpone - ask for new day
        await query.edit_message_text(
            "📅 Select new day:",
            reply_markup=days_keyboard()
        )
        return SELECTING_DAY


async def day_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle new day selection."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "cancel_action":
        await query.edit_message_text("❌ Action cancelled.")
        return ConversationHandler.END
    
    day = query.data.replace("newday_", "")
    context.user_data['new_day'] = day
    
    await query.edit_message_text(
        f"Selected: {day.capitalize()}\n\n"
        "⏰ Select hour:",
        reply_markup=hours_keyboard()
    )
    return SELECTING_HOUR


async def hour_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle hour selection."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "cancel_action":
        await query.edit_message_text("❌ Action cancelled.")
        return ConversationHandler.END
    
    hour = int(query.data.replace("hour_", ""))
    context.user_data['new_hour'] = hour
    
    await query.edit_message_text(
        f"⏰ {hour:02d}:??\n\n"
        "Select minutes:",
        reply_markup=minutes_keyboard()
    )
    return SELECTING_MINUTE


async def minute_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle minute selection."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "cancel_action":
        await query.edit_message_text("❌ Action cancelled.")
        return ConversationHandler.END
    
    minute = int(query.data.replace("minute_", ""))
    context.user_data['new_minute'] = minute
    
    # Calculate new date
    day_name = context.user_data['new_day']
    hour = context.user_data['new_hour']
    
    # Find next occurrence of that day
    tz = pytz.timezone(Config.TIMEZONE)
    now = datetime.now(tz)
    
    day_map = {
        'monday': 0, 'tuesday': 1, 'wednesday': 2,
        'thursday': 3, 'friday': 4, 'saturday': 5, 'sunday': 6
    }
    
    target_day = day_map[day_name]
    days_ahead = target_day - now.weekday()
    if days_ahead <= 0:
        days_ahead += 7
    
    new_date = now + timedelta(days=days_ahead)
    context.user_data['new_date'] = new_date.strftime("%Y-%m-%d")
    
    meeting = context.user_data['meeting']
    original_date = context.user_data['selected_date']
    
    await query.edit_message_text(
        f"⚠️ Confirm postponement?\n\n"
        f"📚 {meeting['title']}\n"
        f"📅 From: {original_date}\n"
        f"📅 To: {context.user_data['new_date']} at {hour:02d}:{minute:02d}\n\n"
        "This will send request for approval.",
        reply_markup=confirm_keyboard()
    )
    return CONFIRMING


async def confirm_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle confirmation."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "confirm_no":
        await query.edit_message_text("❌ Action cancelled.")
        return ConversationHandler.END
    
    # Get all data
    chat_id = str(update.effective_chat.id)
    user = get_user(chat_id)
    meeting = context.user_data['meeting']
    change_type = context.user_data['change_type']
    original_date = context.user_data['selected_date']
    
    new_date = context.user_data.get('new_date')
    new_hour = context.user_data.get('new_hour')
    new_minute = context.user_data.get('new_minute')
    
    # Determine who needs to approve
    group_name = meeting.get('group_name')
    
    if user['role'] == 'student':
        # Student request - teacher needs to approve
        teacher = get_teacher_for_group(group_name)
        if not teacher:
            await query.edit_message_text("❌ No teacher found for your group.")
            return ConversationHandler.END
        
        approvals_needed = 1
        notify_chat_ids = [teacher['chat_id']]
    else:
        # Teacher request - all students need to approve
        students = get_students_in_group(group_name)
        approvals_needed = max(1, len(students))
        notify_chat_ids = [s['chat_id'] for s in students]
    
    # Create request
    request_id = create_change_request(
        meeting_id=meeting['id'],
        requester_chat_id=chat_id,
        requester_role=user['role'],
        change_type=change_type,
        original_date=original_date,
        new_date=new_date,
        new_hour=new_hour,
        new_minute=new_minute,
        approvals_needed=approvals_needed
    )
    
    if not request_id:
        await query.edit_message_text("❌ Failed to create request.")
        return ConversationHandler.END
    
    # Send approval requests
    bot = context.bot
    
    if change_type == 'cancel':
        message = (
            f"📨 <b>Lesson Cancellation Request</b>\n\n"
            f"From: {user['name']} ({user['role']})\n"
            f"Lesson: {meeting['title']}\n"
            f"Date: {original_date}\n\n"
            f"Do you approve?"
        )
    else:
        message = (
            f"📨 <b>Lesson Postponement Request</b>\n\n"
            f"From: {user['name']} ({user['role']})\n"
            f"Lesson: {meeting['title']}\n"
            f"From: {original_date}\n"
            f"To: {new_date} at {new_hour:02d}:{new_minute:02d}\n\n"
            f"Do you approve?"
        )
    
    sent_count = 0
    for target_chat_id in notify_chat_ids:
        try:
            await bot.send_message(
                chat_id=target_chat_id,
                text=message,
                parse_mode='HTML',
                reply_markup=approval_keyboard(request_id)
            )
            sent_count += 1
        except Exception as e:
            print(f"❌ Failed to notify {target_chat_id}: {e}")
    
    await query.edit_message_text(
        f"✅ Request sent!\n\n"
        f"Request ID: {request_id}\n"
        f"Waiting for {approvals_needed} approval(s).\n"
        f"Notifications sent: {sent_count}\n\n"
        f"Request expires at 23:59 today."
    )
    
    return ConversationHandler.END


async def handle_approval(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle approval/rejection button clicks."""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    chat_id = str(update.effective_chat.id)
    
    if data.startswith("approve_"):
        request_id = data.replace("approve_", "")
        approved = True
    elif data.startswith("reject_"):
        request_id = data.replace("reject_", "")
        approved = False
    else:
        return
    
    # Add approval
    result = add_approval(request_id, chat_id, approved)
    
    if result.get("error") == "already_voted":
        await query.edit_message_text("❌ You already responded to this request.")
        return
    
    request = get_request(request_id)
    
    if result.get("status") == "approved":
        # All approvals received - create override
        add_lesson_override(
            meeting_id=request['meeting_id'],
            original_date=request['original_date'],
            override_type=request['change_type'],
            new_date=request.get('new_date'),
            new_hour=request.get('new_hour'),
            new_minute=request.get('new_minute')
        )
        
        await query.edit_message_text(
            f"✅ Request APPROVED!\n\n"
            f"Lesson has been {'cancelled' if request['change_type'] == 'cancel' else 'postponed'}."
        )
        
        # Notify requester
        try:
            await context.bot.send_message(
                chat_id=request['requester_chat_id'],
                text=f"✅ Your request (ID: {request_id}) has been approved!"
            )
        except:
            pass
    
    elif result.get("status") == "rejected":
        await query.edit_message_text("❌ Request rejected.")
        
        # Notify requester
        try:
            await context.bot.send_message(
                chat_id=request['requester_chat_id'],
                text=f"❌ Your request (ID: {request_id}) was rejected."
            )
        except:
            pass
    
    else:
        remaining = result.get("remaining", "?")
        await query.edit_message_text(
            f"✅ Your response recorded!\n\n"
            f"Waiting for {remaining} more approval(s)."
        )


async def cancel_change(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel change action."""
    await update.message.reply_text("❌ Action cancelled.")
    return ConversationHandler.END