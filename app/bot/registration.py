from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from app.bot.keyboards import role_keyboard, groups_keyboard
from app.services.user_service import register_user, is_registered, add_teacher_group
from app.config import Config

# Conversation states
CHOOSING_ROLE, ENTERING_NAME, CHOOSING_GROUP, ADDING_GROUPS = range(4)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    chat_id = update.effective_chat.id
    
    if is_registered(str(chat_id)):
        await update.message.reply_text(
            "👋 Welcome back!\n\n"
            "Commands:\n"
            "/change - Postpone or cancel a lesson\n"
            "/status - Check your status\n"
            "/help - Get help"
        )
        return ConversationHandler.END
    
    await update.message.reply_text(
        "👋 Welcome to the Meeting Bot!\n\n"
        "First, let's register you.\n"
        "Are you a teacher or a student?",
        reply_markup=role_keyboard()
    )
    return CHOOSING_ROLE


async def role_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle role selection."""
    query = update.callback_query
    await query.answer()
    
    role = query.data.replace("role_", "")  # teacher or student
    context.user_data['role'] = role
    
    await query.edit_message_text(
        f"You selected: {'👨‍🏫 Teacher' if role == 'teacher' else '👨‍🎓 Student'}\n\n"
        "Please enter your full name:"
    )
    return ENTERING_NAME


async def name_entered(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle name input."""
    name = update.message.text.strip()
    context.user_data['name'] = name
    
    role = context.user_data['role']
    
    if role == 'student':
        # Students choose their group
        meetings = Config.load_meetings()
        groups = list(set([m.get('group_name', 'Default') for m in meetings]))
        
        if not groups:
            groups = ['Default']
        
        await update.message.reply_text(
            f"Nice to meet you, {name}! 👋\n\n"
            "Which group are you in?",
            reply_markup=groups_keyboard(groups)
        )
        return CHOOSING_GROUP
    else:
        # Teachers - register first, then add groups
        chat_id = update.effective_chat.id
        register_user(str(chat_id), name, 'teacher')
        
        meetings = Config.load_meetings()
        groups = list(set([m.get('group_name', 'Default') for m in meetings]))
        
        await update.message.reply_text(
            f"Welcome, {name}! 👨‍🏫\n\n"
            "Which groups do you teach?\n"
            "(Select all that apply, then type /done)",
            reply_markup=groups_keyboard(groups)
        )
        context.user_data['selected_groups'] = []
        return ADDING_GROUPS


async def group_chosen_student(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle student group selection."""
    query = update.callback_query
    await query.answer()
    
    group = query.data.replace("group_", "")
    chat_id = update.effective_chat.id
    name = context.user_data['name']
    
    # Register student
    register_user(str(chat_id), name, 'student', group)
    
    await query.edit_message_text(
        f"✅ Registration complete!\n\n"
        f"Name: {name}\n"
        f"Role: Student\n"
        f"Group: {group}\n\n"
        "Commands:\n"
        "/change - Request lesson postpone/cancel\n"
        "/status - Check your status"
    )
    return ConversationHandler.END


async def group_chosen_teacher(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle teacher group selection."""
    query = update.callback_query
    await query.answer()
    
    group = query.data.replace("group_", "")
    chat_id = update.effective_chat.id
    
    if group not in context.user_data.get('selected_groups', []):
        context.user_data['selected_groups'].append(group)
        add_teacher_group(str(chat_id), group)
    
    selected = context.user_data['selected_groups']
    
    await query.edit_message_text(
        f"✅ Added: {group}\n\n"
        f"Selected groups: {', '.join(selected)}\n\n"
        "Select more groups or type /done to finish."
    )
    
    # Show groups keyboard again
    meetings = Config.load_meetings()
    groups = list(set([m.get('group_name', 'Default') for m in meetings]))
    
    await update.effective_chat.send_message(
        "Select another group:",
        reply_markup=groups_keyboard(groups)
    )
    return ADDING_GROUPS


async def done_adding_groups(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Finish teacher registration."""
    selected = context.user_data.get('selected_groups', [])
    name = context.user_data.get('name', 'Teacher')
    
    await update.message.reply_text(
        f"✅ Registration complete!\n\n"
        f"Name: {name}\n"
        f"Role: Teacher\n"
        f"Groups: {', '.join(selected)}\n\n"
        "Commands:\n"
        "/change - Postpone or cancel a lesson\n"
        "/status - Check your status"
    )
    return ConversationHandler.END


async def cancel_registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel registration."""
    await update.message.reply_text("Registration cancelled. Use /start to try again.")
    return ConversationHandler.END