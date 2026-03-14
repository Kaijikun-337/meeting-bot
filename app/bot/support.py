# app/bot/support.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from app.services.support_service import get_weekly_booking_count, create_booking, get_available_support_staff
from app.services.lesson_service import get_available_slots_for_rescheduling
from app.utils.localization import get_text, get_user_language
from app.jitsi_meet import create_jitsi_meeting
from app.services.support_service import can_book_support
from app.utils.localization import t

SELECT_DATE, SELECT_TIME = range(2)

# --- CUSTOM KEYBOARDS (Prevents clashing with Change Lesson) ---
def support_dates_keyboard(slots, lang='en'):
    keyboard = []
    seen = set()
    for slot in slots:
        if slot['date'] not in seen:
            seen.add(slot['date'])
            # Extract just the date part (e.g. "Wed 25 Oct")
            display = slot['display'].split(' at ')[0] if ' at ' in slot['display'] else slot['display']
            keyboard.append([InlineKeyboardButton(f"📅 {display}", callback_data=f"sup_date_{slot['date']}")])
            
    keyboard.append([InlineKeyboardButton(get_text('btn_cancel', lang), callback_data="sup_cancel")])
    return InlineKeyboardMarkup(keyboard)

def support_times_keyboard(slots, selected_date, lang='en'):
    keyboard = []
    row = []
    # Filter the flat list for only the selected date
    day_slots = [s for s in slots if s['date'] == selected_date]
    
    for slot in day_slots:
        time_str = f"{slot['hour']:02d}:{slot['minute']:02d}"
        row.append(InlineKeyboardButton(time_str, callback_data=f"sup_time_{time_str}"))
        if len(row) == 3:
            keyboard.append(row)
            row = []
            
    if row:
        keyboard.append(row)
        
    keyboard.append([InlineKeyboardButton(get_text('btn_back', lang), callback_data="sup_back")])
    return InlineKeyboardMarkup(keyboard)

# --- HANDLERS ---
async def start_support_booking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Triggered when student clicks 'Book lesson with support'"""
    chat_id = str(update.effective_chat.id)
    lang = get_user_language(chat_id)

    # 1. Check weekly limit (now uses the REAL counter)
    if not can_book_support(chat_id):
        await update.message.reply_text(
            get_text('support_limit_reached', lang)
        )
        return ConversationHandler.END

    # 2. Find Support Staff
    support = get_available_support_staff()
    if not support:
        await update.message.reply_text(
            get_text('support_no_staff', lang)
        )
        return ConversationHandler.END

    context.user_data['support_id'] = support['chat_id']
    context.user_data['support_name'] = support['name']

    # 3. Get Slots FROM THE NEW SYSTEM (not rescheduling!)
    from app.services.support_service import get_available_slots
    slots = get_available_slots(support['chat_id'])

    if not slots:
        await update.message.reply_text(
            get_text('support_no_slots', lang)
        )
        return ConversationHandler.END

    context.user_data['support_slots'] = slots

    await update.message.reply_text(
        f"👨‍🏫 <b>Academic Support</b> with {support['name']}\n"
        f"📏 Session: 30 minutes\n"
        f"📊 Bookings this week: "
        f"{get_weekly_booking_count(chat_id)}/2\n\n"
        f"Select a date:",
        reply_markup=support_dates_keyboard(slots, lang),
        parse_mode='HTML'
    )
    return SELECT_DATE

async def support_date_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    chat_id = str(update.effective_chat.id)
    lang = get_user_language(chat_id)
    
    if query.data == "sup_cancel":
        await query.edit_message_text(get_text('cancelled', lang))
        return ConversationHandler.END
        
    date = query.data.replace("sup_date_", "")
    context.user_data['support_date'] = date
    slots = context.user_data.get('support_slots', [])
    
    await query.edit_message_text(
        f"Select time for <b>{date}</b>:",
        reply_markup=support_times_keyboard(slots, date, lang),
        parse_mode='HTML'
    )
    return SELECT_TIME

async def support_time_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    chat_id = str(update.effective_chat.id)
    lang = get_user_language(chat_id)
    
    if query.data == "sup_back":
        # Go back to date selection
        slots = context.user_data.get('support_slots', [])
        support_name = context.user_data.get('support_name', 'Support')
        await query.edit_message_text(
            f"👨‍🏫 <b>Academic Support</b> with {support_name}\nSelect a date:",
            reply_markup=support_dates_keyboard(slots, lang),
            parse_mode='HTML'
        )
        return SELECT_DATE
        
    time_str = query.data.replace("sup_time_", "")
    date_str = context.user_data.get('support_date')
    support_id = context.user_data.get('support_id')
    student_id = str(update.effective_chat.id)
    
    # Generate Link
    meeting = create_jitsi_meeting("Academic Support")
    link = meeting['meet_link']
    
    msg = f"✅ <b>Booked!</b>\n📅 {date_str} at {time_str}\n🔗 Link: {link}\n\n<i>(Save this link! It has also been sent to the support staff)</i>"
    
    # Save to DB
    success = create_booking(student_id, support_id, date_str, time_str, link)
    
    if success:
        await query.edit_message_text(msg, parse_mode='HTML')
        
        # Notify the Support Staff
        student_name = update.effective_user.first_name
        await context.bot.send_message(
            chat_id=support_id,
            text=f"🆕 <b>New Support Booking</b>\n👤 Student: {student_name}\n📅 {date_str} at {time_str}\n🔗 {link}",
            parse_mode='HTML'
        )
    else:
        await query.edit_message_text("❌ Error saving booking to database.")
        
    return ConversationHandler.END

async def cancel_support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Fallback if the user types /cancel during support booking."""
    chat_id = str(update.effective_chat.id)
    lang = get_user_language(chat_id)
    
    # We use update.message because /cancel is a text command, not a button click
    if update.message:
        await update.message.reply_text(get_text('cancelled', lang))
        
    return ConversationHandler.END

async def handle_book_support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for when a student clicks 'Book lesson with support'."""
    chat_id = str(update.effective_chat.id)
    
    # 1. Check the rule: Max 2 per week
    if not can_book_support(chat_id):
        # ❌ They reached the limit
        await update.message.reply_text(
            t(chat_id, 'support_limit_reached') 
        )
        return
    
    # 2. Record the booking
    success = start_support_booking(chat_id)
    
    if success:
        # ✅ Success!
        # TODO: Send a message to the Support Staff/Admin group here if needed.
        await update.message.reply_text(
            t(chat_id, 'support_booking_success')
        )
    else:
        # DB Error
        await update.message.reply_text(
            t(chat_id, 'error_occurred')
        )