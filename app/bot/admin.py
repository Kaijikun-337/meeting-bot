from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, CommandHandler, CallbackQueryHandler, filters
from app.config import Config
from app.services.user_service import (
    create_pending_user, 
    add_pending_teacher_group,
    get_all_pending_users, 
    get_all_active_users, 
    delete_user,
    get_user,
    delete_user_by_chat_id,
    update_user_name,
    update_student_group,
    update_teacher_name,
    update_teacher_groups,
)
from app.database.db import get_connection
from app.utils.localization import get_user_language, get_text
from app.services.attendance_service import get_student_attendance_stats

# States
ENTERING_NAME, ENTERING_GROUP = range(2)
# Note: We removed ENTERING_SUBJECT and ADDING_MORE_GROUPS as they are no longer used

(
    EDIT_USER_CHAT,
    EDIT_STUDENT_NAME,
    EDIT_STUDENT_GROUP,
    EDIT_TEACHER_NAME,
    EDIT_TEACHER_GROUP,
    EDIT_TEACHER_SUBJECT,
    DELETE_USER_CHAT,
    DELETE_USER_CONFIRM,
) = range(4, 12) 

def is_admin(chat_id: str) -> bool:
    """Check if user is admin."""
    return str(chat_id) == str(Config.ADMIN_CHAT_ID)


async def new_student_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /new_student command (admin only)."""
    chat_id = str(update.effective_chat.id)
    
    if not is_admin(chat_id):
        await update.message.reply_text("❌ Admin only command.")
        return ConversationHandler.END
    
    context.user_data['new_user'] = {'role': 'student'}
    
    await update.message.reply_text(
        "👨‍🎓 <b>New Student Registration</b>\n\n"
        "Enter the student's <b>full name</b>:",
        parse_mode='HTML'
    )
    
    return ENTERING_NAME


async def new_teacher_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /new_teacher command (admin only)."""
    chat_id = str(update.effective_chat.id)
    
    if not is_admin(chat_id):
        await update.message.reply_text("❌ Admin only command.")
        return ConversationHandler.END
    
    context.user_data['new_user'] = {'role': 'teacher'}
    
    await update.message.reply_text(
        "👨‍🏫 <b>New Teacher Registration</b>\n\n"
        "Enter the teacher's <b>full name</b>:\n"
        "<i>(Must match the name in the schedule file exactly)</i>",
        parse_mode='HTML'
    )
    
    return ENTERING_NAME


async def name_entered_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle name input for new user."""
    name = update.message.text.strip()
    context.user_data['new_user']['name'] = name
    role = context.user_data['new_user']['role']
    
    # === STUDENT FLOW ===
    if role == 'student':
        await update.message.reply_text(
            f"👤 Name: <b>{name}</b>\n\n"
            "Enter the student's <b>group name</b>:",
            parse_mode='HTML'
        )
        return ENTERING_GROUP

    # === TEACHER FLOW (New Automatic Logic) ===
    else:
        # Create pending teacher immediately
        key = create_pending_user(name, 'teacher')
        
        if key:
            await update.message.reply_text(
                f"✅ <b>Teacher Created!</b>\n\n"
                f"👤 Name: {name}\n"
                f"🔑 <b>Registration Key:</b>\n"
                f"<code>{key}</code>\n\n"
                f"ℹ️ <b>Note:</b> Groups will be automatically assigned from the schedule when they register.\n\n"
                f"Share this key with the teacher.\n"
                f"They use /start and enter this key to activate.",
                parse_mode='HTML'
            )
        else:
            await update.message.reply_text("❌ Error creating teacher.")
        
        # End conversation immediately for teachers
        return ConversationHandler.END


async def group_entered_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle group input (Students Only)."""
    group = update.message.text.strip()
    
    # Double check this is a student (should be, based on logic above)
    if context.user_data['new_user']['role'] == 'student':
        context.user_data['new_user']['group'] = group
        
        # Create student
        name = context.user_data['new_user']['name']
        key = create_pending_user(name, 'student', group)
        
        if key:
            await update.message.reply_text(
                f"✅ <b>Student Created!</b>\n\n"
                f"👤 Name: {name}\n"
                f"📚 Group: {group}\n\n"
                f"🔑 <b>Registration Key:</b>\n"
                f"<code>{key}</code>\n\n"
                f"Share this key with the student.\n"
                f"They use /start and enter this key to activate.",
                parse_mode='HTML'
            )
        else:
            await update.message.reply_text("❌ Error creating student.")
        
        return ConversationHandler.END
    
    return ConversationHandler.END


async def list_users_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all registered users."""
    if not is_admin(update.effective_user.id):
        return
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name, role, chat_id, group_name FROM users WHERE is_active = 1 ORDER BY role, name")
    users = cursor.fetchall()
    conn.close()
    
    if not users:
        await update.message.reply_text("No users found.")
        return
    
    text = "👥 <b>Registered Users</b>\n\n"
    
    for u in users:
        icon = "👨‍🏫" if u['role'] == 'teacher' else "👨‍🎓"
        group = f" ({u['group_name']})" if u['group_name'] else ""
        text += f"{icon} <b>{u['name']}</b>{group}\n"
        text += f"🆔 <code>{u['chat_id']}</code>\n\n"
    
    await update.message.reply_text(text, parse_mode='HTML')


async def cancel_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel admin action."""
    await update.message.reply_text("❌ Cancelled.")
    return ConversationHandler.END

async def delete_user_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start delete user flow (admin only)."""
    chat_id = update.effective_user.id
    if not is_admin(chat_id):
        lang = get_user_language(str(chat_id))
        await update.message.reply_text(get_text('admin_only', lang))
        return ConversationHandler.END
    
    await update.message.reply_text(
        "🗑 Send the <b>chat_id</b> of the user you want to delete.\n\n"
        "You can copy it from /users output.",
        parse_mode='HTML'
    )
    return DELETE_USER_CHAT


async def delete_user_chat_entered(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin sent chat_id of user to delete."""
    admin_chat_id = str(update.effective_user.id)
    lang = get_user_language(admin_chat_id)
    
    text = update.message.text.strip()
    if not text.isdigit():
        await update.message.reply_text("❌ Please send a numeric chat_id.")
        return DELETE_USER_CHAT
    
    target_chat_id = text
    user = get_user(target_chat_id)
    
    if not user:
        await update.message.reply_text("❌ No such user.")
        return ConversationHandler.END
    
    context.user_data['delete_target'] = target_chat_id
    
    role_label = get_text('role_teacher', lang) if user['role'] == 'teacher' else get_text('role_student', lang)
    
    await update.message.reply_text(
        f"⚠️ <b>Confirm delete</b>\n\n"
        f"👤 {user['name']}\n"
        f"🎭 {role_label}\n"
        f"🆔 <code>{target_chat_id}</code>\n\n"
        f"This will permanently remove them from the system.",
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ Delete", callback_data="deluser_yes"),
                InlineKeyboardButton("❌ Cancel", callback_data="deluser_no"),
            ]
        ])
    )
    return DELETE_USER_CONFIRM


async def delete_user_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Confirm or cancel actual deletion."""
    query = update.callback_query
    await query.answer()
    
    admin_chat_id = str(update.effective_user.id)
    lang = get_user_language(admin_chat_id)
    
    if query.data == "deluser_no":
        await query.edit_message_text(get_text('cancelled', lang))
        return ConversationHandler.END
    
    target_chat_id = context.user_data.get('delete_target')
    if not target_chat_id:
        await query.edit_message_text("❌ No target user stored.")
        return ConversationHandler.END
    
    success = delete_user_by_chat_id(target_chat_id)
    
    if success:
        await query.edit_message_text("✅ User deleted.")
    else:
        await query.edit_message_text("❌ Failed to delete user.")
    
    return ConversationHandler.END

async def edit_student_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start edit student flow."""
    chat_id = update.effective_user.id
    if not is_admin(chat_id):
        lang = get_user_language(str(chat_id))
        await update.message.reply_text(get_text('admin_only', lang))
        return ConversationHandler.END
    
    await update.message.reply_text(
        "✏️ Send the <b>chat_id</b> of the STUDENT you want to edit.\n\nCopy it from /users.",
        parse_mode='HTML'
    )
    return EDIT_USER_CHAT


async def edit_user_chat_entered(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin sent chat_id to edit (student or teacher)."""
    admin_chat_id = str(update.effective_user.id)
    lang = get_user_language(admin_chat_id)
    
    text = update.message.text.strip()
    if not text.isdigit():
        await update.message.reply_text("❌ Please send a numeric chat_id.")
        return EDIT_USER_CHAT
    
    target_chat_id = text
    user = get_user(target_chat_id)
    
    if not user:
        await update.message.reply_text("❌ No such user.")
        return ConversationHandler.END
    
    if user['role'] != 'student':
        await update.message.reply_text("❌ This is not a student. Use /edit_teacher for teachers.")
        return ConversationHandler.END
    
    context.user_data['edit_target'] = target_chat_id
    
    await update.message.reply_text(
        f"✏️ Editing student:\n\n"
        f"👤 {user['name']}\n"
        f"👥 Group: {user.get('group_name') or 'None'}\n\n"
        f"Send a new <b>name</b> (or send /skip to leave unchanged).",
        parse_mode='HTML'
    )
    return EDIT_STUDENT_NAME


async def edit_student_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive new name for student (or /skip)."""
    admin_chat_id = str(update.effective_user.id)
    lang = get_user_language(admin_chat_id)
    
    text = update.message.text.strip()
    target_chat_id = context.user_data.get('edit_target')
    
    if text != "/skip":
        ok = update_user_name(target_chat_id, text)
        if not ok:
            await update.message.reply_text("❌ Failed to update name.")
            return ConversationHandler.END
    
    await update.message.reply_text(
        "Now send new <b>group name</b> for the student (or send /skip):",
        parse_mode='HTML'
    )
    return EDIT_STUDENT_GROUP


async def edit_student_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive new group for student (or /skip)."""
    admin_chat_id = str(update.effective_user.id)
    lang = get_user_language(admin_chat_id)
    
    text = update.message.text.strip()
    target_chat_id = context.user_data.get('edit_target')
    
    if text != "/skip":
        ok = update_student_group(target_chat_id, text)
        if not ok:
            await update.message.reply_text("❌ Failed to update group.")
            return ConversationHandler.END
    
    await update.message.reply_text("✅ Student updated.")
    return ConversationHandler.END

async def edit_teacher_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start edit teacher flow."""
    chat_id = update.effective_user.id
    if not is_admin(chat_id):
        lang = get_user_language(str(chat_id))
        await update.message.reply_text(get_text('admin_only', lang))
        return ConversationHandler.END
    
    await update.message.reply_text(
        "✏️ Send the <b>chat_id</b> of the TEACHER you want to edit.\n\nCopy it from /users.",
        parse_mode='HTML'
    )
    return EDIT_USER_CHAT  # ← FIRST state: we want chat_id here


async def edit_teacher_chat_entered(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin sent teacher chat_id."""
    admin_chat_id = str(update.effective_user.id)
    lang = get_user_language(admin_chat_id)
    
    text = update.message.text.strip()
    if not text.isdigit():
        await update.message.reply_text("❌ Please send a numeric chat_id.")
        return EDIT_USER_CHAT  # ask again
    
    target_chat_id = text
    user = get_user(target_chat_id)
    
    if not user or user['role'] != 'teacher':
        await update.message.reply_text("❌ This is not a teacher.")
        return ConversationHandler.END
    
    context.user_data['edit_target'] = target_chat_id
    
    await update.message.reply_text(
        f"✏️ Editing teacher:\n\n"
        f"👨‍🏫 {user['name']}\n\n"
        f"Send new <b>name</b> (or /skip):",
        parse_mode='HTML'
    )
    return EDIT_TEACHER_NAME  # ← Next state: waiting for new name


async def edit_teacher_name_step(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive new teacher name."""
    admin_chat_id = str(update.effective_user.id)
    lang = get_user_language(admin_chat_id)
    
    text = update.message.text.strip()
    target_chat_id = context.user_data.get('edit_target')
    
    if text != "/skip":
        ok = update_teacher_name(target_chat_id, text)
        if not ok:
            await update.message.reply_text("❌ Failed to update name.")
            return ConversationHandler.END
    
    await update.message.reply_text(
        "Send new <b>group name</b> for this teacher (applies to all their groups) or /skip:",
        parse_mode='HTML'
    )
    return EDIT_TEACHER_GROUP


async def edit_teacher_group_step(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive new teacher group name."""
    admin_chat_id = str(update.effective_user.id)
    lang = get_user_language(admin_chat_id)
    
    text = update.message.text.strip()
    target_chat_id = context.user_data.get('edit_target')
    
    new_group = None
    if text != "/skip":
        new_group = text
    
    context.user_data['edit_teacher_group'] = new_group
    
    await update.message.reply_text(
        "Send new <b>subject</b> for this teacher (applies to all their groups) or /skip:",
        parse_mode='HTML'
    )
    return EDIT_TEACHER_SUBJECT


async def edit_teacher_subject_step(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive new teacher subject."""
    admin_chat_id = str(update.effective_user.id)
    lang = get_user_language(admin_chat_id)
    
    text = update.message.text.strip()
    target_chat_id = context.user_data.get('edit_target')
    
    new_group = context.user_data.get('edit_teacher_group')
    new_subject = None
    if text != "/skip":
        new_subject = text
    
    ok = update_teacher_groups(target_chat_id, new_group=new_group, new_subject=new_subject)
    if not ok:
        await update.message.reply_text("❌ Failed to update teacher groups/subjects.")
        return ConversationHandler.END
    
    await update.message.reply_text("✅ Teacher updated.")
    return ConversationHandler.END

async def check_attendance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin: Check attendance stats."""
    if not is_admin(update.effective_user.id):
        return

    # Check if arguments provided (/attendance 12345)
    args = context.args
    if args:
        student_id = args[0]
        await show_student_stats(update, student_id)
        return

    # Otherwise show list of students
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name, chat_id FROM users WHERE role='student' AND is_active=1 ORDER BY name")
    students = cursor.fetchall()
    conn.close()
    
    if not students:
        await update.message.reply_text("No students found.")
        return
        
    msg = "👥 <b>Select a Student to view Attendance:</b>\n\n"
    for s in students:
        msg += f"• {s['name']} (<code>{s['chat_id']}</code>)\n"
        
    msg += "\nType <code>/attendance STUDENT_ID</code> to view details."
    
    await update.message.reply_text(msg, parse_mode='HTML')

async def show_student_stats(update: Update, student_id: str):
    """Show detailed stats for one student."""
    user = get_user(student_id)
    if not user:
        await update.message.reply_text("❌ User not found.")
        return

    stats = get_student_attendance_stats(student_id)
    
    msg = (
        f"📊 <b>Attendance Report: {user['name']}</b>\n"
        f"Rate: <b>{stats['percentage']:.1f}%</b>\n"
        f"Classes: {stats['present']} / {stats['total']}\n\n"
        f"<b>Recent History:</b>\n"
    )
    
    # Show last 10 lessons
    for record in stats['history'][:10]:
        icon = "✅" if record['status'] == 'present' else "❌"
        # We could lookup meeting title from ID, but ID is usually descriptive enough
        msg += f"{icon} {record['date']} ({record['meeting_id']})\n"
        
    await update.message.reply_text(msg, parse_mode='HTML')