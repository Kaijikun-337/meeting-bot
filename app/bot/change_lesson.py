from telegram import Update
from telegram.ext import (
    ContextTypes,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
)
from app.services.user_service import get_user, get_teacher_for_group, get_students_in_group
from app.services.lesson_service import (
    get_upcoming_lessons,
    can_change_lesson,
    create_lesson_override,
)
from app.services.request_service import create_change_request, add_approval, get_request
from app.services.availability_service import get_available_slots_for_rescheduling
from app.bot.keyboards import (
    lessons_keyboard,
    confirm_keyboard,
    approval_keyboard,
    reschedule_slots_keyboard,
)
from app.utils.localization import get_text, get_user_language

# States
SELECTING_LESSON, SELECTING_CHANGE_TYPE, SELECTING_SLOT, CONFIRMING = range(4)


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
        upcoming = get_upcoming_lessons(meeting['id'], days_ahead=14, lang=lang)
        for lesson in upcoming:
            lesson['meeting'] = meeting
            lessons.append(lesson)
    
    if not lessons:
        await update.message.reply_text(get_text('no_lessons_to_change', lang))
        return ConversationHandler.END
    
    context.user_data['lessons'] = lessons
    
    await update.message.reply_text(
        get_text('select_lesson', lang),
        reply_markup=lessons_keyboard(lessons, lang),  # ← Pass lang
        parse_mode='HTML'
    )
    
    return SELECTING_LESSON


async def lesson_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle lesson date selection."""
    query = update.callback_query
    await query.answer()
    
    chat_id = str(update.effective_user.id)
    lang = get_user_language(chat_id)
    
    if query.data == "cancel_action":
        await query.edit_message_text(get_text('cancelled', lang))
        return ConversationHandler.END
    
    date = query.data.replace("lesson_", "")
    context.user_data['selected_date'] = date
    
    # Find the meeting for this date
    lessons = context.user_data.get('lessons', [])
    meeting = None
    for lesson in lessons:
        if lesson['date'] == date:
            meeting = lesson['meeting']
            break
    
    if not meeting:
        await query.edit_message_text(get_text('cancelled', lang))
        return ConversationHandler.END
    
    context.user_data['meeting'] = meeting
    
    # Check if change is allowed (2+ hours before)
    can_change, reason = can_change_lesson(meeting, date)
    
    if not can_change:
        msg = get_text('cannot_change_lesson', lang).format(reason=get_text('too_late_to_change', lang))
        await query.edit_message_text(msg)
        return ConversationHandler.END
    
    await query.edit_message_text(
        f"{get_text('selected', lang)}: {date}\n\n{get_text('what_to_do', lang)}",
        reply_markup=change_type_keyboard_localized(lang)
    )
    return SELECTING_CHANGE_TYPE


async def change_type_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle postpone/cancel selection."""
    query = update.callback_query
    await query.answer()
    
    chat_id = str(update.effective_user.id)
    lang = get_user_language(chat_id)
    
    change_type = query.data.replace("change_", "")
    context.user_data['change_type'] = change_type
    
    meeting = context.user_data['meeting']
    selected_date = context.user_data['selected_date']
    
    if change_type == 'cancel':
        msg = get_text('confirm_cancel_lesson', lang).format(
            title=meeting['title'],
            date=selected_date
        )
        await query.edit_message_text(
            msg,
            reply_markup=confirm_keyboard_localized(lang),  # Already correct
            parse_mode='HTML'
        )
        return CONFIRMING
    
    else:
        # Postpone - show teacher's available slots
        group_name = meeting.get('group_name')
        teacher_chat_id = None
        
        if group_name:
            teacher = get_teacher_for_group(group_name)
            if teacher:
                teacher_chat_id = teacher.get('chat_id')
        
        if not teacher_chat_id:
            await query.edit_message_text(get_text('no_teacher_found', lang))
            return ConversationHandler.END
        
        slots = get_available_slots_for_rescheduling(
            teacher_chat_id,
            exclude_date=selected_date,
            group_name=group_name
        )
        
        if not slots:
            await query.edit_message_text(
                get_text('no_available_slots', lang),
                parse_mode='HTML'
            )
            return ConversationHandler.END
        
        await query.edit_message_text(
            get_text('select_new_time', lang),
            reply_markup=reschedule_slots_keyboard(slots, lang),  # ← Pass lang
            parse_mode='HTML'
        )
        return SELECTING_SLOT


async def slot_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle slot selection for rescheduling."""
    query = update.callback_query
    await query.answer()
    
    chat_id = str(update.effective_user.id)
    lang = get_user_language(chat_id)
    
    if query.data == "cancel_action":
        await query.edit_message_text(get_text('cancelled', lang))
        return ConversationHandler.END
    
    if query.data == "no_slots":
        await query.edit_message_text(get_text('no_available_slots', lang))
        return ConversationHandler.END
    
    # Parse new time
    parts = query.data.replace("reschedule_", "").rsplit("_", 2)  # Split from right, max 2 split
    new_date = parts[0]       # "29-01-2026"
    new_hour = int(parts[1])  # 13
    new_minute = int(parts[2]) # 30
    
    meeting = context.user_data['meeting']
    original_date = context.user_data['selected_date']
    group_name = meeting.get('group_name')
    
    # Check number of students in group
    students = get_students_in_group(group_name)
    student_count = len(students)
    
    # CASE 1: Individual lesson (1 student) -> INSTANT CHANGE
    if student_count <= 1:
        success = create_lesson_override(
            meeting_id=meeting['id'],
            original_date=original_date,
            override_type='postponed',
            new_date=new_date,
            new_hour=new_hour,
            new_minute=new_minute
        )
        
        if not success:
            await query.edit_message_text(get_text('save_failed', lang))
            return ConversationHandler.END
        
        # Notify teacher
        teacher = get_teacher_for_group(group_name)
        if teacher:
            try:
                t_lang = get_user_language(teacher['chat_id'])
                msg = get_text('lesson_rescheduled_notification', t_lang).format(
                    title=meeting['title'],
                    by=get_user(chat_id)['name'],
                    old_date=original_date,
                    new_date=new_date,
                    new_time=f"{new_hour:02d}:00"
                )
                await context.bot.send_message(teacher['chat_id'], msg, parse_mode='HTML')
            except:
                pass
        
        # Confirm to user
        await query.edit_message_text(
            get_text('lesson_rescheduled', lang).format(
                title=meeting['title'],
                old_date=original_date,
                new_date=new_date,
                new_time=f"{new_hour:02d}:00"
            ),
            parse_mode='HTML'
        )
        
        return ConversationHandler.END
    
    # CASE 2: Group lesson (>1 student) -> START VOTING
    else:
        # Create request requiring (student_count - 1) approvals
        # The requester automatically approves
        approvals_needed = student_count - 1
        
        request_id = create_change_request(
            meeting_id=meeting['id'],
            requester_chat_id=chat_id,
            requester_role='student',
            change_type='postponed',
            original_date=original_date,
            new_date=new_date,
            new_hour=new_hour,
            new_minute=new_minute,
            approvals_needed=approvals_needed
        )
        
        if not request_id:
            await query.edit_message_text(get_text('request_failed', lang))
            return ConversationHandler.END
        
        # Auto-approve for the requester
        add_approval(request_id, chat_id, True)
        
        # Notify other students to vote
        sent_count = 0
        user = get_user(chat_id)
        
        for student in students:
            if str(student['chat_id']) == chat_id:
                continue  # Skip requester
            
            try:
                s_lang = get_user_language(student['chat_id'])
                message = get_text('group_vote_request', s_lang).format(
                    name=user['name'],
                    title=meeting['title'],
                    old_date=original_date,
                    new_date=new_date,
                    new_time=f"{new_hour:02d}:00"
                )
                
                await context.bot.send_message(
                    chat_id=student['chat_id'],
                    text=message,
                    parse_mode='HTML',
                    reply_markup=approval_keyboard(request_id, s_lang)
                )
                sent_count += 1
            except Exception as e:
                print(f"Failed to notify {student['chat_id']}: {e}")
        
        # Notify teacher (FYI only)
        teacher = get_teacher_for_group(group_name)
        if teacher:
            try:
                t_lang = get_user_language(teacher['chat_id'])
                await context.bot.send_message(
                    teacher['chat_id'],
                    get_text('teacher_vote_notification', t_lang).format(
                        group=group_name,
                        title=meeting['title']
                    ),
                    parse_mode='HTML'
                )
            except:
                pass
        
        # Confirm to requester
        await query.edit_message_text(
            get_text('vote_started', lang).format(
                count=approvals_needed,
                total=student_count
            ),
            parse_mode='HTML'
        )
        
        return ConversationHandler.END


async def confirm_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle confirmation - only for CANCELLATIONS (still needs approval)."""
    query = update.callback_query
    await query.answer()
    
    chat_id = str(update.effective_chat.id)
    lang = get_user_language(chat_id)
    
    if query.data == "confirm_no":
        await query.edit_message_text(get_text('cancelled', lang))
        return ConversationHandler.END
    
    user = get_user(chat_id)
    meeting = context.user_data['meeting']
    change_type = context.user_data['change_type']
    original_date = context.user_data['selected_date']
    
    group_name = meeting.get('group_name')
    
    if user['role'] == 'student':
        teacher = get_teacher_for_group(group_name)
        if not teacher:
            await query.edit_message_text(get_text('no_teacher_found', lang))
            return ConversationHandler.END
        
        approvals_needed = 1
        notify_chat_ids = [teacher['chat_id']]
    else:
        students = get_students_in_group(group_name)
        approvals_needed = max(1, len(students))
        notify_chat_ids = [s['chat_id'] for s in students]
    
    # Normalize override type
    override_type = 'cancelled' if change_type == 'cancel' else 'postponed'
    
    request_id = create_change_request(
        meeting_id=meeting['id'],
        requester_chat_id=chat_id,
        requester_role=user['role'],
        change_type=override_type,
        original_date=original_date,
        new_date=None,
        new_hour=None,
        new_minute=None,
        approvals_needed=approvals_needed
    )
    
    if not request_id:
        await query.edit_message_text(get_text('request_failed', lang))
        return ConversationHandler.END
    
    # Send approval request to each recipient in their language
    sent_count = 0
    for target_chat_id in notify_chat_ids:
        try:
            target_lang = get_user_language(target_chat_id)
            message = get_text('cancel_approval_request', target_lang).format(
                name=user['name'],
                role=get_text('role_' + user['role'], target_lang),
                title=meeting['title'],
                date=original_date
            )
            await context.bot.send_message(
                chat_id=target_chat_id,
                text=message,
                parse_mode='HTML',
                reply_markup=approval_keyboard(request_id, target_lang)
            )
            sent_count += 1
        except Exception as e:
            print(f"❌ Failed to notify {target_chat_id}: {e}")
    
    msg = get_text('cancel_request_sent', lang).format(
        request_id=request_id,
        count=approvals_needed
    )
    
    await query.edit_message_text(msg)
    
    return ConversationHandler.END


async def handle_approval(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle approval/rejection button clicks."""
    query = update.callback_query
    await query.answer()
    
    from app.services.lesson_service import add_lesson_override
    from app.config import Config
    
    data = query.data
    chat_id = str(update.effective_chat.id)
    lang = get_user_language(chat_id)
    
    if data.startswith("approve_"):
        request_id = data.replace("approve_", "")
        approved = True
    elif data.startswith("reject_"):
        request_id = data.replace("reject_", "")
        approved = False
    else:
        return
    
    result = add_approval(request_id, chat_id, approved)
    
    if result.get("error") == "already_voted":
        await query.edit_message_text(get_text('already_responded', lang))
        return
    
    request = get_request(request_id)
    
    # ══════════════════════════════════════════════════════
    # CASE 1: APPROVED (All votes collected)
    # ══════════════════════════════════════════════════════
    if result.get("status") == "approved":
        change_type = request['change_type']
        
        # Normalize type
        if change_type == 'cancel':
            override_type = 'cancelled'
        elif change_type == 'postpone':
            override_type = 'postponed'
        else:
            override_type = change_type
        
        # Apply override
        add_lesson_override(
            meeting_id=request['meeting_id'],
            original_date=request['original_date'],
            override_type=override_type,
            new_date=request.get('new_date'),
            new_hour=request.get('new_hour'),
            new_minute=request.get('new_minute')
        )
        
        status_text = get_text('cancelled_lesson', lang) if override_type == 'cancelled' else 'postponed'
        
        # Update the message button to show result
        await query.edit_message_text(
            get_text('request_approved', lang).format(status=status_text)
        )
        
        # 🔔 NOTIFY EVERYONE (Teacher + All Students)
        # 1. Get meeting details
        meetings = Config.load_meetings()
        meeting = next((m for m in meetings if m['id'] == request['meeting_id']), None)
        
        if meeting:
            group_name = meeting.get('group_name')
            
            # Get requester name for the message
            requester = get_user(request['requester_chat_id'])
            requester_name = requester['name'] if requester else "Group Vote"
            
            # Prepare list of people to notify
            notify_targets = []
            
            # Add Teacher
            teacher = get_teacher_for_group(group_name)
            if teacher:
                notify_targets.append(teacher['chat_id'])
            
            # Add All Students (except the one who just clicked button, as they see the edit)
            students = get_students_in_group(group_name)
            for student in students:
                if str(student['chat_id']) != chat_id:
                    notify_targets.append(student['chat_id'])
            
            # Send notifications
            for target_id in notify_targets:
                try:
                    t_lang = get_user_language(target_id)
                    
                    if override_type == 'postponed':
                        msg = get_text('lesson_rescheduled_notification', t_lang).format(
                            title=meeting['title'],
                            by=f"{requester_name} (Group Vote)",
                            old_date=request['original_date'],
                            new_date=request['new_date'],
                            new_time=f"{request['new_hour']:02d}:{request['new_minute']:02d}"
                        )
                    else:
                        # Simple cancellation message
                        msg = f"❌ <b>{meeting['title']}</b>\n📅 {request['original_date']}\n\nCancelled by Group Vote."
                    
                    await context.bot.send_message(
                        chat_id=target_id,
                        text=msg,
                        parse_mode='HTML'
                    )
                except Exception as e:
                    print(f"Failed to notify {target_id}: {e}")

    # ══════════════════════════════════════════════════════
    # CASE 2: REJECTED (Someone voted NO)
    # ══════════════════════════════════════════════════════
    elif result.get("status") == "rejected":
        await query.edit_message_text(get_text('request_rejected', lang))
        
        # Notify requester that it failed
        try:
            requester_lang = get_user_language(request['requester_chat_id'])
            await context.bot.send_message(
                chat_id=request['requester_chat_id'],
                text=get_text('your_request_rejected', requester_lang).format(request_id=request_id)
            )
        except:
            pass
    
    # ══════════════════════════════════════════════════════
    # CASE 3: PENDING (Still waiting for others)
    # ══════════════════════════════════════════════════════
    else:
        remaining = result.get("remaining", "?")
        await query.edit_message_text(
            get_text('response_recorded', lang).format(remaining=remaining)
        )


async def cancel_change(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel change action."""
    lang = get_user_language(str(update.effective_user.id))
    await update.message.reply_text(get_text('cancelled', lang))
    return ConversationHandler.END


# ═══════════════════════════════════════════════════════════
# LOCALIZED KEYBOARDS (helper functions)
# ═══════════════════════════════════════════════════════════

def change_type_keyboard_localized(lang: str):
    """Localized postpone/cancel keyboard."""
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    
    keyboard = [
        [InlineKeyboardButton(get_text('postpone', lang), callback_data="change_postpone")],
        [InlineKeyboardButton(get_text('cancel_lesson', lang), callback_data="change_cancel")]
    ]
    return InlineKeyboardMarkup(keyboard)


def confirm_keyboard_localized(lang: str):
    """Localized confirm keyboard."""
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    
    keyboard = [
        [
            InlineKeyboardButton(get_text('btn_yes', lang), callback_data="confirm_yes"),
            InlineKeyboardButton(get_text('btn_no', lang), callback_data="confirm_no")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


# ═══════════════════════════════════════════════════════════
# CONVERSATION HANDLER
# ═══════════════════════════════════════════════════════════

def get_change_lesson_handler():
    return ConversationHandler(
        entry_points=[
            CommandHandler('change', change_command),
        ],
        states={
            SELECTING_LESSON: [CallbackQueryHandler(lesson_selected)],
            SELECTING_CHANGE_TYPE: [CallbackQueryHandler(change_type_selected)],
            SELECTING_SLOT: [CallbackQueryHandler(slot_selected)],
            CONFIRMING: [CallbackQueryHandler(confirm_action)]
        },
        fallbacks=[CommandHandler('cancel', cancel_change)],
        name="change_lesson",
        persistent=False,
    )