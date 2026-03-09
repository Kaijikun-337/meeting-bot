from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from app.services.support_service import get_weekly_booking_count, create_booking, get_available_support_staff
from app.services.availability_service import get_teacher_availability # Reuse this!
from app.bot.keyboards import reschedule_dates_keyboard, reschedule_times_keyboard
from app.utils.localization import get_text, get_user_language
from app.jitsi_meet import create_jitsi_meeting

SELECT_DATE, SELECT_TIME = range(2)

async def support_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    lang = get_user_language(chat_id)
    
    # 1. Check Limit
    count = get_weekly_booking_count(chat_id)
    if count >= 2:
        await update.message.reply_text("❌ You have reached the limit of 2 support sessions this week.")
        return ConversationHandler.END
        
    # 2. Find Support Staff
    support = get_available_support_staff()
    if not support:
        await update.message.reply_text("❌ No academic support staff available right now.")
        return ConversationHandler.END
        
    context.user_data['support_id'] = support['chat_id']
    context.user_data['support_name'] = support['name']
    
    # 3. Get Slots (Reuse logic from lesson_service)
    from app.services.lesson_service import get_available_slots_for_rescheduling
    # We trick the function by passing support_id as "teacher_id"
    slots = get_available_slots_for_rescheduling(support['chat_id'], "", "Support")
    
    if not slots:
        await update.message.reply_text("❌ No available slots found.")
        return ConversationHandler.END
        
    context.user_data['support_slots'] = slots
    
    await update.message.reply_text(
        f"👨‍🏫 <b>Academic Support</b> with {support['name']}\nSelect a date:",
        reply_markup=reschedule_dates_keyboard(slots, lang),
        parse_mode='HTML'
    )
    return SELECT_DATE

async def support_date_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    date = query.data.replace("resched_date_", "")
    context.user_data['support_date'] = date
    
    slots = context.user_data['support_slots']
    day_slots = next((s for s in slots if s['date'] == date), None)
    
    await query.edit_message_text(
        "Select time:",
        reply_markup=reschedule_times_keyboard(day_slots['slots'], date, "en") # Reuse keyboard
    )
    return SELECT_TIME

async def support_time_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data.replace("reschedule_", "").split("_")
    time = data[0]
    meeting = create_jitsi_meeting("Academic Support")
    link = meeting['meet_link']
    
    student_id = str(update.effective_chat.id)
    support_id = context.user_data['support_id']
    date = context.user_data['support_date']
    
    msg = f"✅ <b>Booked!</b>\n📅 {date} at {time}\n🔗 Link: {link}\n(Save this link!)"
    
    # Save to DB
    success = create_booking(student_id, support_id, date, time)
    
    if success:
        await query.edit_message_text(msg, parse_mode='HTML')
        
        # Schedule the Jitsi Link
        # (We need to add a dynamic job to scheduler here)
        await context.bot.send_message(
            chat_id=support_id,
            text=f"🆕 New Support Booking\n📅 {date} at {time}\n🔗 {link}"
        )
        
    else:
        await query.edit_message_text("❌ Error booking.")
        
    return ConversationHandler.END