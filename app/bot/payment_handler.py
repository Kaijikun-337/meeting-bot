from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from datetime import datetime
from app.database.db import get_connection
from app.config import Config
from app.utils.localization import get_text, get_user_language

async def handle_receipt_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Intercepts photos/documents from students with unpaid bills."""
    user = update.effective_user
    chat_id = update.effective_chat.id
    current_month = datetime.now().strftime("%m-%Y")

    conn = get_connection()
    cur = conn.cursor()
    
    # Check if this user is a student with an unpaid bill that isn't already pending
    cur.execute("""
        SELECT id, amount_due, group_name FROM student_payments 
        WHERE student_chat_id = ? AND month_year = ? AND is_paid = 0 
        AND (receipt_status IS NULL OR receipt_status = 'rejected')
    """, (str(chat_id), current_month))
    
    bill = cur.fetchone()
    
    if not bill:
        # Not a student with an unpaid bill, let other handlers process this message
        cur.close()
        conn.close()
        return

    bill_id = bill['id']
    amount = bill['amount_due']
    group = bill['group_name']
    lang = get_user_language(str(chat_id))
    user_name = user.full_name

    # Forward the photo/document to Admin
    admin_chat_id = Config.ADMIN_CHAT_ID
    caption = (
        f"🧾 <b>Payment Receipt</b>\n\n"
        f"Student: {user_name} (<code>{chat_id}</code>)\n"
        f"Group: {group}\n"
        f"Amount: {amount} UZS\n"
        f"Month: {current_month}"
    )

    if update.message.photo:
        msg = await context.bot.copy_message(
            chat_id=admin_chat_id,
            from_chat_id=chat_id,
            message_id=update.message.message_id,
            caption=caption,
            parse_mode='HTML'
        )
    elif update.message.document:
        msg = await context.bot.copy_message(
            chat_id=admin_chat_id,
            from_chat_id=chat_id,
            message_id=update.message.message_id,
            caption=caption,
            parse_mode='HTML'
        )
    else:
        await update.message.reply_text("Please send the receipt as a photo or file.")
        cur.close()
        conn.close()
        return

    # Add Approve/Reject buttons to the admin's message
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Approve", callback_data=f"pay_approve_{bill_id}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"pay_reject_{bill_id}")
        ]
    ])
    await context.bot.edit_message_reply_markup(chat_id=admin_chat_id, message_id=msg.message_id, reply_markup=keyboard)

    # Mark as pending so they don't spam receipts
    cur.execute("UPDATE student_payments SET receipt_status = 'pending' WHERE id = ?", (bill_id,))
    conn.commit()

    # Reply to student
    await update.message.reply_text(get_text('receipt_received', lang), parse_mode='HTML')
    
    cur.close()
    conn.close()

async def handle_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles admin clicking Approve/Reject on the receipt."""
    query = update.callback_query
    await query.answer()
    
    data = query.data.split('_')
    action = data[1]
    bill_id = int(data[2])
    
    admin_id = str(update.effective_chat.id)
    if admin_id != Config.ADMIN_CHAT_ID:
        return
        
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT student_chat_id FROM student_payments WHERE id = ?", (bill_id,))
    bill = cur.fetchone()
    
    if not bill:
        await query.edit_message_caption(caption="Error: Bill not found.", parse_mode='HTML')
        cur.close()
        conn.close()
        return
        
    student_chat_id = str(bill['student_chat_id'])
    lang = get_user_language(student_chat_id)
    original_caption = query.message.caption if query.message.caption else "Receipt"
    
    if action == 'approve':
        cur.execute("UPDATE student_payments SET is_paid = 1, receipt_status = 'approved', paid_at = CURRENT_TIMESTAMP WHERE id = ?", (bill_id,))
        conn.commit()
        
        await query.edit_message_caption(caption=original_caption + "\n\n✅ APPROVED", parse_mode='HTML')
        await context.bot.send_message(chat_id=student_chat_id, text=get_text('payment_approved', lang), parse_mode='HTML')
    else:
        cur.execute("UPDATE student_payments SET receipt_status = 'rejected' WHERE id = ?", (bill_id,))
        conn.commit()
        
        await query.edit_message_caption(caption=original_caption + "\n\n❌ REJECTED", parse_mode='HTML')
        await context.bot.send_message(chat_id=student_chat_id, text=get_text('payment_rejected', lang), parse_mode='HTML')
        
    cur.close()
    conn.close()