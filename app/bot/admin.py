from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from app.config import Config
from app.services.user_service import (
    create_pending_user, add_pending_teacher_group,
    get_all_pending_users, get_all_active_users, delete_user
)

# States
ENTERING_NAME, ENTERING_GROUP, ADDING_MORE_GROUPS, ENTERING_SUBJECT = range(4)

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
    
    context.user_data['new_user'] = {'role': 'teacher', 'groups': []}
    
    await update.message.reply_text(
        "👨‍🏫 <b>New Teacher Registration</b>\n\n"
        "Enter the teacher's <b>full name</b>:",
        parse_mode='HTML'
    )
    
    return ENTERING_NAME


async def name_entered_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle name input for new user."""
    name = update.message.text.strip()
    context.user_data['new_user']['name'] = name
    
    role = context.user_data['new_user']['role']
    
    if role == 'student':
        await update.message.reply_text(
            f"👤 Name: <b>{name}</b>\n\n"
            "Enter the student's <b>group name</b>:",
            parse_mode='HTML'
        )
        return ENTERING_GROUP
    else:
        await update.message.reply_text(
            f"👤 Name: <b>{name}</b>\n\n"
            "Enter a <b>group name</b> this teacher will teach:",
            parse_mode='HTML'
        )
        return ENTERING_GROUP


async def group_entered_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle group input."""
    group = update.message.text.strip()
    role = context.user_data['new_user']['role']
    
    if role == 'student':
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
    
    else:
        # Teacher - ask for subject for this group
        context.user_data['new_user']['current_group'] = group
        
        await update.message.reply_text(
            f"📚 Group: <b>{group}</b>\n\n"
            "Enter the <b>subject</b> for this group:\n\n"
            "<i>Example: Math, English, Physics</i>",
            parse_mode='HTML'
        )
        return ENTERING_SUBJECT


async def subject_entered_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle subject input for teacher."""
    subject = update.message.text.strip()
    group = context.user_data['new_user']['current_group']
    
    context.user_data['new_user']['groups'].append({
        'group': group,
        'subject': subject
    })
    
    groups_list = context.user_data['new_user']['groups']
    groups_text = "\n".join([f"  • {g['group']} ({g['subject']})" for g in groups_list])
    
    await update.message.reply_text(
        f"✅ Added: <b>{group}</b> - {subject}\n\n"
        f"<b>Groups so far:</b>\n{groups_text}\n\n"
        "Add another group or finish?",
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("➕ Add Another Group", callback_data="admin_add_group"),
                InlineKeyboardButton("✅ Finish", callback_data="admin_finish_teacher")
            ]
        ])
    )
    
    return ADDING_MORE_GROUPS


async def admin_group_decision(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle add more groups or finish."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "admin_add_group":
        await query.edit_message_text(
            "Enter another <b>group name</b>:",
            parse_mode='HTML'
        )
        return ENTERING_GROUP
    
    elif query.data == "admin_finish_teacher":
        # Create teacher
        user_data = context.user_data['new_user']
        name = user_data['name']
        groups = user_data['groups']
        
        # Create pending user
        key = create_pending_user(name, 'teacher')
        
        if key:
            # Add pending groups
            for g in groups:
                add_pending_teacher_group(key, g['group'], g['subject'])
            
            groups_text = "\n".join([f"  • {g['group']} ({g['subject']})" for g in groups])
            
            await query.edit_message_text(
                f"✅ <b>Teacher Created!</b>\n\n"
                f"👤 Name: {name}\n"
                f"📚 Groups:\n{groups_text}\n\n"
                f"🔑 <b>Registration Key:</b>\n"
                f"<code>{key}</code>\n\n"
                f"Share this key with the teacher.\n"
                f"They use /start and enter this key to activate.",
                parse_mode='HTML'
            )
        else:
            await query.edit_message_text("❌ Error creating teacher.")
        
        return ConversationHandler.END


async def list_users_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /users command - list all users."""
    chat_id = str(update.effective_chat.id)
    
    if not is_admin(chat_id):
        await update.message.reply_text("❌ Admin only command.")
        return
    
    active = get_all_active_users()
    pending = get_all_pending_users()
    
    message = "👥 <b>All Users</b>\n\n"
    
    if active:
        message += "<b>✅ Active Users:</b>\n"
        for user in active:
            role_icon = "👨‍🏫" if user['role'] == 'teacher' else "👨‍🎓"
            group = user.get('group_name', 'N/A')
            message += f"{role_icon} {user['name']} ({group})\n"
        message += "\n"
    
    if pending:
        message += "<b>⏳ Pending Users:</b>\n"
        for user in pending:
            role_icon = "👨‍🏫" if user['role'] == 'teacher' else "👨‍🎓"
            group = user.get('group_name', 'N/A')
            message += f"{role_icon} {user['name']} ({group})\n"
            message += f"   Key: <code>{user['registration_key']}</code>\n"
    
    if not active and not pending:
        message += "<i>No users found.</i>"
    
    await update.message.reply_text(message, parse_mode='HTML')


async def cancel_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel admin action."""
    await update.message.reply_text("❌ Cancelled.")
    return ConversationHandler.END