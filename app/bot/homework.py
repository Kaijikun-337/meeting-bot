from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    filters
)
from app.services.user_service import (
    get_user,
    get_user_role,
    get_teacher_groups,
    get_students_in_group
)
from app.utils.localization import get_text, get_user_language

# Conversation states
WAITING_FOR_FILES = 1
WAITING_FOR_GROUP = 2
CONFIRM_SEND = 3

# Temporary storage for homework sessions
homework_sessions = {}


# ═══════════════════════════════════════════════════════════
# KEYBOARDS
# ═══════════════════════════════════════════════════════════

def done_uploading_keyboard(lang: str = 'en'):
    """Done uploading files button."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(get_text('done_uploading', lang), callback_data="hw_done_upload")]
    ])


def groups_for_homework_keyboard(groups: list, lang: str = 'en'):
    """Select group to send homework to."""
    buttons = []
    for group in groups:
        group_name = group['group_name']
        buttons.append([
            InlineKeyboardButton(
                f"👥 {group_name}",
                callback_data=f"hw_group_{group_name}"
            )
        ])
    
    buttons.append([InlineKeyboardButton(get_text('btn_cancel', lang), callback_data="hw_cancel")])
    return InlineKeyboardMarkup(buttons)


def confirm_send_keyboard(lang: str = 'en'):
    """Confirm sending homework."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(get_text('btn_send_now', lang), callback_data="hw_confirm_send")],
        [InlineKeyboardButton(get_text('btn_cancel', lang), callback_data="hw_cancel")]
    ])


# ═══════════════════════════════════════════════════════════
# COMMAND: /homework
# ═══════════════════════════════════════════════════════════

async def homework_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start homework distribution flow."""
    chat_id = str(update.effective_user.id)
    lang = get_user_language(chat_id)
    
    # Verify teacher
    user = get_user(chat_id)
    role = get_user_role(chat_id)
    
    if not user or role != "teacher":
        await update.message.reply_text(get_text('teachers_only', lang))
        return ConversationHandler.END
    
    # Check if teacher has groups
    groups = get_teacher_groups(chat_id)
    if not groups:
        await update.message.reply_text(get_text('no_groups_assigned', lang))
        return ConversationHandler.END
    
    # Initialize session
    homework_sessions[chat_id] = {
        'teacher_name': user.get('name', 'Teacher'),
        'files': [],
        'selected_group': None
    }
    
    await update.message.reply_text(
        get_text('homework_start', lang),
        reply_markup=done_uploading_keyboard(lang),
        parse_mode="HTML"
    )
    
    return WAITING_FOR_FILES


# ═══════════════════════════════════════════════════════════
# FILE COLLECTION
# ═══════════════════════════════════════════════════════════

async def receive_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive homework files from teacher."""
    chat_id = str(update.effective_user.id)
    lang = get_user_language(chat_id)
    
    if chat_id not in homework_sessions:
        return ConversationHandler.END
    
    message = update.message
    file_info = None
    
    # Determine file type
    if message.document:
        file_info = {
            'type': 'document',
            'file_id': message.document.file_id,
            'file_name': message.document.file_name or 'document'
        }
    elif message.photo:
        # Get highest resolution photo
        file_info = {
            'type': 'photo',
            'file_id': message.photo[-1].file_id,
            'file_name': 'photo.jpg'
        }
    elif message.video:
        file_info = {
            'type': 'video',
            'file_id': message.video.file_id,
            'file_name': message.video.file_name or 'video.mp4'
        }
    elif message.audio:
        file_info = {
            'type': 'audio',
            'file_id': message.audio.file_id,
            'file_name': message.audio.file_name or 'audio.mp3'
        }
    elif message.voice:
        file_info = {
            'type': 'voice',
            'file_id': message.voice.file_id,
            'file_name': 'voice_message.ogg'
        }
    
    if file_info:
        homework_sessions[chat_id]['files'].append(file_info)
        file_count = len(homework_sessions[chat_id]['files'])
        
        await message.reply_text(
            get_text('file_received', lang).format(count=file_count),
            reply_markup=done_uploading_keyboard(lang)
        )
    
    return WAITING_FOR_FILES


async def done_uploading(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Teacher finished uploading files, show group selection."""
    query = update.callback_query
    await query.answer()
    
    chat_id = str(update.effective_user.id)
    lang = get_user_language(chat_id)
    
    if chat_id not in homework_sessions:
        await query.edit_message_text(get_text('session_expired', lang))
        return ConversationHandler.END
    
    session = homework_sessions[chat_id]
    
    if not session['files']:
        await query.edit_message_text(
            get_text('no_files_uploaded', lang),
            reply_markup=done_uploading_keyboard(lang)
        )
        return WAITING_FOR_FILES
    
    # Get teacher's groups
    groups = get_teacher_groups(chat_id)
    
    if not groups:
        await query.edit_message_text(get_text('no_groups_assigned', lang))
        del homework_sessions[chat_id]
        return ConversationHandler.END
    
    file_count = len(session['files'])
    
    await query.edit_message_text(
        get_text('select_group_for_homework', lang).format(count=file_count),
        reply_markup=groups_for_homework_keyboard(groups, lang),
        parse_mode="HTML"
    )
    
    return WAITING_FOR_GROUP


# ═══════════════════════════════════════════════════════════
# GROUP SELECTION & CONFIRMATION
# ═══════════════════════════════════════════════════════════

async def select_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Teacher selected a group, show confirmation."""
    query = update.callback_query
    await query.answer()
    
    chat_id = str(update.effective_user.id)
    lang = get_user_language(chat_id)
    
    if chat_id not in homework_sessions:
        await query.edit_message_text(get_text('session_expired', lang))
        return ConversationHandler.END
    
    # Parse group name
    group_name = query.data.replace("hw_group_", "")
    session = homework_sessions[chat_id]
    session['selected_group'] = group_name
    
    # Get students in group
    students = get_students_in_group(group_name)
    student_count = len(students)
    file_count = len(session['files'])
    
    if student_count == 0:
        await query.edit_message_text(
            get_text('no_students_in_group', lang).format(group=group_name)
        )
        del homework_sessions[chat_id]
        return ConversationHandler.END
    
    # Show confirmation
    await query.edit_message_text(
        get_text('confirm_homework_send', lang).format(
            file_count=file_count,
            student_count=student_count,
            group=group_name
        ),
        reply_markup=confirm_send_keyboard(lang),
        parse_mode="HTML"
    )
    
    return CONFIRM_SEND


async def confirm_send(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send homework to all students in the group anonymously."""
    query = update.callback_query
    await query.answer(get_text('sending', lang='en'))
    
    chat_id = str(update.effective_user.id)
    lang = get_user_language(chat_id)
    
    if chat_id not in homework_sessions:
        await query.edit_message_text(get_text('session_expired', lang))
        return ConversationHandler.END
    
    session = homework_sessions[chat_id]
    group_name = session['selected_group']
    files = session['files']
    
    # Get students
    students = get_students_in_group(group_name)
    
    sent_count = 0
    failed_count = 0
    
    for student in students:
        student_chat_id = student.get('chat_id')
        if not student_chat_id:
            failed_count += 1
            continue
        
        try:
            student_lang = get_user_language(student_chat_id)
            
            # Send anonymous header message
            await context.bot.send_message(
                chat_id=student_chat_id,
                text=get_text('homework_received', student_lang),
                parse_mode="HTML"
            )
            
            # Send each file
            for file_info in files:
                if file_info['type'] == 'document':
                    await context.bot.send_document(
                        chat_id=student_chat_id,
                        document=file_info['file_id']
                    )
                elif file_info['type'] == 'photo':
                    await context.bot.send_photo(
                        chat_id=student_chat_id,
                        photo=file_info['file_id']
                    )
                elif file_info['type'] == 'video':
                    await context.bot.send_video(
                        chat_id=student_chat_id,
                        video=file_info['file_id']
                    )
                elif file_info['type'] == 'audio':
                    await context.bot.send_audio(
                        chat_id=student_chat_id,
                        audio=file_info['file_id']
                    )
                elif file_info['type'] == 'voice':
                    await context.bot.send_voice(
                        chat_id=student_chat_id,
                        voice=file_info['file_id']
                    )
            
            sent_count += 1
            
        except Exception as e:
            print(f"Failed to send homework to {student_chat_id}: {e}")
            failed_count += 1
    
    # Clean up session
    del homework_sessions[chat_id]
    
    # Report results
    if failed_count > 0:
        result_text = get_text('homework_sent_partial', lang).format(
            sent=sent_count,
            failed=failed_count
        )
    else:
        result_text = get_text('homework_sent_success', lang).format(sent=sent_count)
    
    await query.edit_message_text(result_text, parse_mode="HTML")
    
    return ConversationHandler.END


async def cancel_homework(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel homework distribution."""
    query = update.callback_query
    await query.answer()
    
    chat_id = str(update.effective_user.id)
    lang = get_user_language(chat_id)
    
    if chat_id in homework_sessions:
        del homework_sessions[chat_id]
    
    await query.edit_message_text(get_text('cancelled', lang))
    return ConversationHandler.END


async def cancel_homework_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel via /cancel command."""
    chat_id = str(update.effective_user.id)
    lang = get_user_language(chat_id)
    
    if chat_id in homework_sessions:
        del homework_sessions[chat_id]
    
    await update.message.reply_text(get_text('cancelled', lang))
    return ConversationHandler.END


# ═══════════════════════════════════════════════════════════
# CONVERSATION HANDLER
# ═══════════════════════════════════════════════════════════

def get_homework_conversation_handler():
    """Create and return the homework conversation handler."""
    from app.bot.menu_handler import is_button
    
    class HomeworkButtonFilter(filters.MessageFilter):
        """Matches Homework button in any language."""
        def filter(self, message):
            if message.text:
                return is_button(message.text, 'btn_homework')
            return False
    
    homework_button = HomeworkButtonFilter()
    
    return ConversationHandler(
        entry_points=[
            CommandHandler("homework", homework_command),
            MessageHandler(homework_button, homework_command)
        ],
        states={
            WAITING_FOR_FILES: [
                MessageHandler(
                    filters.Document.ALL | filters.PHOTO | filters.VIDEO | 
                    filters.AUDIO | filters.VOICE,
                    receive_file
                ),
                CallbackQueryHandler(done_uploading, pattern=r"^hw_done_upload$"),
                CallbackQueryHandler(cancel_homework, pattern=r"^hw_cancel$"),
            ],
            WAITING_FOR_GROUP: [
                CallbackQueryHandler(select_group, pattern=r"^hw_group_"),
                CallbackQueryHandler(cancel_homework, pattern=r"^hw_cancel$"),
            ],
            CONFIRM_SEND: [
                CallbackQueryHandler(confirm_send, pattern=r"^hw_confirm_send$"),
                CallbackQueryHandler(cancel_homework, pattern=r"^hw_cancel$"),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel_homework_command),
            CallbackQueryHandler(cancel_homework, pattern=r"^hw_cancel$"),
        ],
        name="homework_conversation",
        persistent=False,
    )