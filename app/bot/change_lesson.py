from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from app.services.lesson_service import (
    get_upcoming_lessons,
    check_lesson_status,
    create_lesson_override,
    delete_lesson_override,
    get_available_slots_for_rescheduling,
    is_slot_available_for_group
)
from app.services.user_service import get_teacher_for_group, get_user
# REMOVED THE BAD IMPORT HERE
from app.utils.localization import get_text, get_user_language
from app.bot.keyboards import (
    confirm_keyboard_localized,
    reschedule_dates_keyboard,
    reschedule_times_keyboard,
    lessons_keyboard
)
from app.config import Config
# Add these to existing imports
from app.services.request_service import create_change_request, cast_vote
from app.services.user_service import get_students_in_group

# States
SELECTING_LESSON, SELECTING_CHANGE_TYPE, CONFIRMING, SELECTING_NEW_DATE, SELECTING_NEW_TIME = range(5)

async def change_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start change lesson flow."""
    chat_id = str(update.effective_user.id)
    lang = get_user_language(chat_id)
    
    user = get_user(chat_id)
    if not user:
        await update.message.reply_text(get_text('not_registered', lang))
        return ConversationHandler.END
    
    # Get upcoming lessons
    from app.bot.schedule import get_user_meetings
    meetings = get_user_meetings(chat_id)
    
    if not meetings:
        await update.message.reply_text(get_text('no_lessons_to_change', lang))
        return ConversationHandler.END
    
    # Build lessons list for next 14 days
    lessons = []
    for meeting in meetings:
        # Get lessons INCLUDING cancelled/postponed ones (so we can restore them)
        upcoming = get_upcoming_lessons(meeting['id'], days_ahead=14, lang=lang)
        for lesson in upcoming:
            lesson['meeting'] = meeting  # Attach meeting info to lesson
            lessons.append(lesson)
    
    if not lessons:
        await update.message.reply_text(get_text('no_lessons_to_change', lang))
        return ConversationHandler.END
    
    context.user_data['lessons'] = lessons
    
    await update.message.reply_text(
        get_text('select_lesson', lang),
        reply_markup=lessons_keyboard(lessons, lang),
        parse_mode='HTML'
    )
    
    return SELECTING_LESSON


async def lesson_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """User selected a specific lesson/date."""
    query = update.callback_query
    await query.answer()
    
    data = query.data.split('_')
    # Format: lesson_MEETINGID_DATE
    # meeting_id might contain underscores, so we join everything between index 1 and last
    meeting_id = "_".join(data[1:-1])
    date_str = data[-1]
    
    # 1. Try to find in Memory (Fastest)
    lessons = context.user_data.get('lessons', [])
    selected_lesson = next((l for l in lessons if l['meeting']['id'] == meeting_id and l['date'] == date_str), None)
    
    meeting = None
    
    if selected_lesson:
        meeting = selected_lesson['meeting']
    else:
        # 2. Fallback: Reload from Config (Robust against Restarts)
        from app.config import Config
        all_meetings = Config.load_meetings()
        meeting = next((m for m in all_meetings if m['id'] == meeting_id), None)

    if not meeting:
        await query.edit_message_text("❌ Error: Lesson configuration not found.")
        return ConversationHandler.END

    # Save to context for the next steps
    context.user_data['meeting'] = meeting
    context.user_data['selected_date'] = date_str
    
    lang = get_user_language(str(update.effective_chat.id))
    
    # Check current status
    status_info = check_lesson_status(meeting_id, date_str)
    
    # IF NORMAL: Show Cancel / Postpone
    if status_info['status'] == 'normal':
        keyboard = [
            [InlineKeyboardButton(get_text('btn_postpone', lang), callback_data="change_postpone")],
            [InlineKeyboardButton(get_text('btn_cancel_lesson', lang), callback_data="change_cancel")],
            [InlineKeyboardButton(get_text('btn_back', lang), callback_data="cancel_action")]
        ]
        text = get_text('what_to_do', lang)

    # IF MODIFIED: Show Restore
    else:
        restore_text = "✅ Restore Original Lesson" 
        keyboard = [
            [InlineKeyboardButton(restore_text, callback_data="change_restore")],
            [InlineKeyboardButton(get_text('btn_back', lang), callback_data="cancel_action")]
        ]
        current_state = status_info['status'].upper()
        text = f"⚠️ This lesson is currently <b>{current_state}</b>.\n\nDo you want to restore it?"

    await query.edit_message_text(
        text,
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return SELECTING_CHANGE_TYPE


async def change_type_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle postpone/cancel/restore selection."""
    query = update.callback_query
    await query.answer()
    
    chat_id = str(update.effective_user.id)
    lang = get_user_language(chat_id)
    
    change_type = query.data.replace("change_", "")
    context.user_data['change_type'] = change_type
    
    meeting = context.user_data['meeting']
    selected_date = context.user_data['selected_date']
    
    # --- RESTORE LOGIC ---
    if change_type == 'restore':
        success = delete_lesson_override(meeting['id'], selected_date)
        if success:
            await query.edit_message_text("✅ Lesson restored to original schedule!")
        else:
            await query.edit_message_text("❌ Failed to restore lesson.")
        return ConversationHandler.END

    # --- CANCEL LOGIC ---
    if change_type == 'cancel':
        msg = get_text('confirm_cancel_lesson', lang).format(
            title=meeting['title'],
            date=selected_date
        )
        await query.edit_message_text(
            msg,
            reply_markup=confirm_keyboard_localized(lang),
            parse_mode='HTML'
        )
        return CONFIRMING
    
    # --- POSTPONE LOGIC ---
    else:
        group_name = meeting.get('group_name')
        teacher_chat_id = None
        
        # Determine teacher ID
        if group_name:
            teacher = get_teacher_for_group(group_name)
            if teacher:
                teacher_chat_id = teacher.get('chat_id')
        
        # Fallback to config if not in DB
        if not teacher_chat_id:
            teacher_chat_id = meeting.get('teacher_chat_id') or meeting.get('chat_id')

        if not teacher_chat_id:
            await query.edit_message_text(get_text('no_teacher_found', lang))
            return ConversationHandler.END
        
        # Get slots
        slots = get_available_slots_for_rescheduling(
            teacher_chat_id,
            exclude_date=selected_date,
            group_name=group_name
        )
        
        if not slots:
            await query.edit_message_text(get_text('no_available_slots', lang), parse_mode='HTML')
            return ConversationHandler.END
        
        context.user_data['available_slots'] = slots
        
        await query.edit_message_text(
            get_text('select_new_date', lang),
            reply_markup=reschedule_dates_keyboard(slots, lang),
            parse_mode='HTML'
        )
        return SELECTING_NEW_DATE


async def date_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """User selected a new date for postponement."""
    query = update.callback_query
    await query.answer()
    
    lang = get_user_language(str(update.effective_chat.id))
    date_str = query.data.replace("resched_date_", "")
    context.user_data['new_date'] = date_str
    
    slots = context.user_data.get('available_slots', [])
    day_slots = next((s for s in slots if s['date'] == date_str), None)
    
    if not day_slots:
        await query.edit_message_text("Error: Date not found.")
        return ConversationHandler.END
        
    await query.edit_message_text(
        get_text('select_new_time', lang),
        reply_markup=reschedule_times_keyboard(day_slots['slots'], date_str, lang),
        parse_mode='HTML'
    )
    return SELECTING_NEW_TIME


async def slot_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """User selected a specific time slot."""
    query = update.callback_query
    await query.answer()
    
    lang = get_user_language(str(update.effective_chat.id))
    data = query.data.replace("reschedule_", "").split("_")
    # Format: time_DATE
    time_str = data[0] # "10:00"
    
    context.user_data['new_time'] = time_str
    
    meeting = context.user_data['meeting']
    original_date = context.user_data['selected_date']
    new_date = context.user_data['new_date']
    
    msg = get_text('confirm_postpone_lesson', lang).format(
        title=meeting['title'],
        from_date=original_date,
        to_date=new_date,
        to_time=time_str
    )
    
    await query.edit_message_text(
        msg,
        reply_markup=confirm_keyboard_localized(lang),
        parse_mode='HTML'
    )
    return CONFIRMING


async def back_to_dates(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Go back to date selection."""
    query = update.callback_query
    await query.answer()
    
    lang = get_user_language(str(update.effective_chat.id))
    slots = context.user_data.get('available_slots', [])
    
    await query.edit_message_text(
        get_text('select_new_date', lang),
        reply_markup=reschedule_dates_keyboard(slots, lang),
        parse_mode='HTML'
    )
    return SELECTING_NEW_DATE


async def confirm_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Execute the change or start voting process."""
    query = update.callback_query
    await query.answer()
    
    chat_id = str(update.effective_user.id)
    lang = get_user_language(chat_id)
    action = query.data
    
    if action == "confirm_no":
        await query.edit_message_text(get_text('cancelled', lang))
        return ConversationHandler.END
        
    # Get Data
    meeting = context.user_data['meeting']
    original_date = context.user_data['selected_date']
    change_type = context.user_data['change_type']
    user = get_user(chat_id)
    
    new_date = None
    new_hour, new_minute = None, None
    
    if change_type != 'cancel':
        new_date = context.user_data['new_date']
        h, m = map(int, context.user_data['new_time'].split(':'))
        new_hour, new_minute = h, m

    # 1. Check Group Size
    group_name = meeting.get('group_name')
    all_students = get_students_in_group(group_name)
    
    # Identify other voters (exclude requester)
    other_students = [s for s in all_students if str(s['chat_id']) != chat_id]
    
    # 2. IF SOLO STUDENT -> INSTANT CHANGE
    if not other_students:
        success = create_lesson_override(
            meeting['id'], original_date, change_type, 
            new_date, new_hour, new_minute
        )
        
        msg_key = 'lesson_cancelled_success' if change_type == 'cancel' else 'lesson_postponed_success'
        
        if success:
            await query.edit_message_text(get_text(msg_key, lang))
        else:
            await query.edit_message_text("❌ Error saving change.")
            
        return ConversationHandler.END

    # 3. IF GROUP -> START VOTE
    else:
        req_uid = create_change_request(
            requester_id=chat_id,
            meeting_id=meeting['id'],
            original_date=original_date,
            change_type=change_type,
            new_date=new_date,
            new_hour=new_hour,
            new_minute=new_minute,
            approvals_needed=len(other_students)
        )
        
        if req_uid:
            await query.edit_message_text(f"📩 Request sent! Waiting for {len(other_students)} other student(s) to approve.")
            
            # Prepare notification for others
            # Assuming ENGLISH for system messages, or loop to localize
            vote_kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Agree", callback_data=f"approve_{req_uid}"), 
                 InlineKeyboardButton("❌ Reject", callback_data=f"reject_{req_uid}")]
            ])
            
            action_text = "CANCEL" if change_type == 'cancel' else "POSTPONE"
            vote_msg = (
                f"🗳 <b>Vote Required</b>\n\n"
                f"User <b>{user['name']}</b> wants to {action_text} the {meeting['title']} lesson on {original_date}."
            )
            
            if change_type != 'cancel':
                vote_msg += f"\n👉 New Time: {new_date} at {new_hour:02d}:{new_minute:02d}"
                
            # Send to others
            for s in other_students:
                try:
                    await context.bot.send_message(
                        chat_id=s['chat_id'], 
                        text=vote_msg, 
                        reply_markup=vote_kb, 
                        parse_mode='HTML'
                    )
                except Exception as e:
                    print(f"Failed to send vote to {s['chat_id']}: {e}")
                    
        else:
            await query.edit_message_text("❌ Error creating request.")

    return ConversationHandler.END


async def cancel_change(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel the conversation."""
    if update.callback_query:
        await update.callback_query.edit_message_text("❌ Action cancelled.")
    else:
        await update.message.reply_text("❌ Action cancelled.")
    return ConversationHandler.END

async def handle_approval(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle vote clicks (Approve/Reject)."""
    query = update.callback_query
    await query.answer()
    
    data = query.data.split('_')
    action = data[0] # approve / reject
    req_uid = data[1]
    chat_id = str(update.effective_chat.id)
    
    # 1 = Yes, 0 = No
    vote_val = 1 if action == 'approve' else 0
    
    success, is_completed, req_data = cast_vote(req_uid, chat_id, vote_val)
    
    if not success:
        await query.edit_message_text("⚠️ You already voted or error occurred.")
        return
        
    if action == 'reject':
        await query.edit_message_text("❌ You rejected the request.")
        # Logic to notify requester could go here
    else:
        await query.edit_message_text("✅ You approved.")
        
    if is_completed:
        status = req_data.get('status', 'unknown')
        
        # Simplified notification
        if status == 'approved':
            msg = f"📢 <b>Update:</b> The request was APPROVED! Schedule updated."
        else:
            msg = f"📢 <b>Update:</b> The request was REJECTED."
            
        # Send to voter (update current message)
        await query.edit_message_text(f"{query.message.text}\n\n{msg}", parse_mode='HTML')