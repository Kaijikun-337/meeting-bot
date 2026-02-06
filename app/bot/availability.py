from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
)
from datetime import datetime, timedelta
from app.services.user_service import get_user_role
from app.services.availability_service import (
    set_availability,
    get_teacher_availability,
    remove_availability,
    get_teacher_availability_summary
)
from app.bot.keyboards import (
    availability_days_keyboard,
    availability_start_hour_keyboard,
    availability_end_hour_keyboard,
    availability_view_keyboard
)
from app.utils.localization import get_text, get_user_language, format_date_localized

# States
SELECT_DAY = 1
SELECT_START_HOUR = 2
SELECT_END_HOUR = 3

# Temp storage
availability_sessions = {}


def build_days_list(lang: str) -> list:
    """Build list of next 7 days for selection."""
    days = []
    today = datetime.now()
    
    for i in range(7):
        day = today + timedelta(days=i)
        date_str = day.strftime("%d-%m-%Y")
        display = format_date_localized(day, lang, 'full')
        
        if i == 0:
            display = f"{get_text('today', lang)} ({display})"
        
        days.append({
            "date_str": date_str,
            "display": display
        })
    
    return days


def build_availability_list(chat_id: str, lang: str) -> list:
    """Build formatted availability list for display."""
    availability = get_teacher_availability(chat_id)
    
    result = []
    for entry in availability:
        try:
            date_obj = datetime.strptime(entry["date"], "%d-%m-%Y")
            result.append({
                "date": entry["date"],
                "display": format_date_localized(date_obj, lang, 'short'),
                "start_hour": entry["start_hour"],
                "end_hour": entry["end_hour"]
            })
        except ValueError:
            continue
    
    return result


async def availability_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Entry point - teacher sets their availability."""
    chat_id = str(update.effective_user.id)
    lang = get_user_language(chat_id)
    
    role = get_user_role(chat_id)
    if role != "teacher":
        await update.message.reply_text(get_text('teachers_only', lang))
        return ConversationHandler.END
    
    current = get_teacher_availability_summary(chat_id)
    if current == "No availability set yet.":
        current = get_text('no_availability_set', lang)
    
    days = build_days_list(lang)
    
    text = (
        f"📅 <b>{get_text('set_availability', lang)}</b>\n\n"
        f"<b>{get_text('current_availability', lang)}</b>\n{current}"
    )
    
    await update.message.reply_text(
        text,
        reply_markup=availability_days_keyboard(days, lang),  # ← Pass lang
        parse_mode="HTML"
    )
    
    return SELECT_DAY


async def day_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Teacher selected a day."""
    query = update.callback_query
    await query.answer()
    
    chat_id = str(update.effective_user.id)
    lang = get_user_language(chat_id)
    date_str = query.data.replace("avail_day_", "")
    
    availability_sessions[chat_id] = {"date": date_str}
    
    date_obj = datetime.strptime(date_str, "%d-%m-%Y")
    day_display = format_date_localized(date_obj, lang, 'full')
    
    # Get keyboard
    base_kb = availability_start_hour_keyboard(lang=lang)
    
    # 2. Extract buttons as a LIST (convert from Tuple)
    buttons = list(base_kb.inline_keyboard)
    
    # 3. Add your new button
    buttons.append([
        InlineKeyboardButton("🗑 Clear This Day", callback_data="avail_clear_this_day")
    ])
    
    # 4. Create NEW markup
    kb = InlineKeyboardMarkup(buttons)
    
    await query.edit_message_text(
        f"📅 <b>{day_display}</b>\n\n"
        f"{get_text('select_start_time', lang)}",
        reply_markup=kb,
        parse_mode="HTML"
    )
    return SELECT_START_HOUR


async def start_hour_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Teacher selected start hour."""
    query = update.callback_query
    await query.answer()
    
    chat_id = str(update.effective_user.id)
    lang = get_user_language(chat_id)
    start_hour = int(query.data.replace("avail_start_", ""))
    
    if chat_id not in availability_sessions:
        await query.edit_message_text("Session expired. Use /availability again.")
        return ConversationHandler.END
    
    availability_sessions[chat_id]["start_hour"] = start_hour
    
    date_str = availability_sessions[chat_id]["date"]
    date_obj = datetime.strptime(date_str, "%d-%m-%Y")
    day_display = format_date_localized(date_obj, lang, 'full')
    
    await query.edit_message_text(
        f"📅 <b>{day_display}</b>\n"
        f"⏰ Start: <b>{start_hour:02d}:00</b>\n\n"
        f"{get_text('select_end_time', lang)}",
        reply_markup=availability_end_hour_keyboard(start_hour, lang=lang),  # ← Pass lang
        parse_mode="HTML"
    )
    
    return SELECT_END_HOUR


async def end_hour_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Teacher selected end hour, save availability."""
    query = update.callback_query
    await query.answer()
    
    chat_id = str(update.effective_user.id)
    lang = get_user_language(chat_id)
    end_hour = int(query.data.replace("avail_end_", ""))
    
    if chat_id not in availability_sessions:
        await query.edit_message_text("Session expired. Use /availability again.")
        return ConversationHandler.END
    
    session = availability_sessions[chat_id]
    date_str = session["date"]
    start_hour = session["start_hour"]
    
    success = set_availability(chat_id, date_str, start_hour, end_hour)
    
    del availability_sessions[chat_id]
    
    if success:
        date_obj = datetime.strptime(date_str, "%d-%m-%Y")
        day_display = format_date_localized(date_obj, lang, 'full')
        num_slots = end_hour - start_hour
        
        msg = get_text('availability_saved', lang).format(
            day=day_display,
            start=start_hour,
            end=end_hour,
            count=num_slots
        )
        
        await query.edit_message_text(msg, parse_mode="HTML")
    else:
        await query.edit_message_text("❌ Failed to save. Try /availability again.")
    
    return ConversationHandler.END


async def view_availability(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show current availability."""
    query = update.callback_query
    await query.answer()
    
    chat_id = str(update.effective_user.id)
    lang = get_user_language(chat_id)
    availability = build_availability_list(chat_id, lang)
    
    if not availability:
        await query.edit_message_text(
            f"📋 <b>{get_text('your_availability', lang)}</b>\n\n"
            f"{get_text('no_availability_set', lang)}",
            parse_mode="HTML"
        )
        return ConversationHandler.END
    
    text = f"📋 <b>{get_text('your_availability', lang)}</b>\n\n"
    for entry in availability:
        start = f"{entry['start_hour']:02d}:00"
        end = f"{entry['end_hour']:02d}:00"
        text += f"• {entry['display']}: {start} - {end}\n"
    
    await query.edit_message_text(
        text,
        reply_markup=availability_view_keyboard(availability, lang),  # ← Pass lang
        parse_mode="HTML"
    )
    
    return SELECT_DAY


async def remove_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Remove availability for a specific day."""
    query = update.callback_query
    
    chat_id = str(update.effective_user.id)
    date_str = query.data.replace("avail_remove_", "")
    
    remove_availability(chat_id, date_str)
    await query.answer(f"Removed {date_str}", show_alert=True)
    
    await view_availability(update, context)
    return SELECT_DAY


async def clear_all_availability(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Clear all availability."""
    query = update.callback_query
    await query.answer()
    
    chat_id = str(update.effective_user.id)
    lang = get_user_language(chat_id)
    availability = get_teacher_availability(chat_id)
    
    for entry in availability:
        remove_availability(chat_id, entry["date"])
    
    await query.edit_message_text(get_text('all_cleared', lang), parse_mode="HTML")
    
    return ConversationHandler.END


async def back_to_days(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Go back to day selection."""
    query = update.callback_query
    await query.answer()
    
    chat_id = str(update.effective_user.id)
    lang = get_user_language(chat_id)
    
    if chat_id in availability_sessions:
        del availability_sessions[chat_id]
    
    current = get_teacher_availability_summary(chat_id)
    if current == "No availability set yet.":
        current = get_text('no_availability_set', lang)
    
    days = build_days_list(lang)
    
    await query.edit_message_text(
        f"📅 <b>{get_text('set_availability', lang)}</b>\n\n"
        f"<b>{get_text('current_availability', lang)}</b>\n{current}",
        reply_markup=availability_days_keyboard(days, lang),  # ← Pass lang
        parse_mode="HTML"
    )
    
    return SELECT_DAY


async def add_more(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await back_to_days(update, context)


async def close_availability(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Close the availability menu."""
    query = update.callback_query
    await query.answer()
    
    chat_id = str(update.effective_user.id)
    lang = get_user_language(chat_id)
    
    if chat_id in availability_sessions:
        del availability_sessions[chat_id]
    
    await query.edit_message_text(get_text('availability_closed', lang))
    return ConversationHandler.END


async def cancel_availability(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel command."""
    chat_id = str(update.effective_user.id)
    lang = get_user_language(chat_id)
    
    if chat_id in availability_sessions:
        del availability_sessions[chat_id]
    
    await update.message.reply_text(get_text('cancelled', lang))
    return ConversationHandler.END


def get_availability_conversation_handler():
    from telegram.ext import MessageHandler, filters
    from app.bot.menu_handler import is_button
    
    class AvailabilityButtonFilter(filters.MessageFilter):
        """Matches Availability button in any language."""
        def filter(self, message):
            if message.text:
                return is_button(message.text, 'btn_availability')
            return False
    
    availability_button = AvailabilityButtonFilter()
    
    return ConversationHandler(
        entry_points=[
            CommandHandler("availability", availability_command),
            MessageHandler(availability_button, availability_command)
        ],
        states={
            SELECT_DAY: [
                CallbackQueryHandler(day_selected, pattern=r"^avail_day_"),
                CallbackQueryHandler(view_availability, pattern=r"^avail_view$"),
                CallbackQueryHandler(clear_all_availability, pattern=r"^avail_clear_all$"),
                CallbackQueryHandler(remove_day, pattern=r"^avail_remove_"),
                CallbackQueryHandler(add_more, pattern=r"^avail_add_more$"),
                CallbackQueryHandler(close_availability, pattern=r"^avail_close$"),
            ],
            SELECT_START_HOUR: [
                CallbackQueryHandler(start_hour_selected, pattern=r"^avail_start_"),
                CallbackQueryHandler(back_to_days, pattern=r"^avail_back$"),
                CallbackQueryHandler(clear_current_day, pattern=r"^avail_clear_this_day$")
            ],
            SELECT_END_HOUR: [
                CallbackQueryHandler(end_hour_selected, pattern=r"^avail_end_"),
                CallbackQueryHandler(back_to_days, pattern=r"^avail_back$"),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel_availability),
            CallbackQueryHandler(close_availability, pattern=r"^avail_close$"),
        ],
        name="availability_conversation",
        persistent=False,
    )
    
async def clear_current_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Clear availability for the currently selected day."""
    query = update.callback_query
    await query.answer()
    
    chat_id = str(update.effective_user.id)
    
    if chat_id not in availability_sessions:
        await query.edit_message_text("Session expired.")
        return ConversationHandler.END
        
    date_str = availability_sessions[chat_id]["date"]
    
    # Call service to remove
    from app.services.availability_service import remove_availability
    remove_availability(chat_id, date_str)
    
    del availability_sessions[chat_id]
    
    await query.edit_message_text(f"🗑 Availability removed for {date_str}.")
    return ConversationHandler.END