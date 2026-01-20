from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from telegram.constants import ChatAction
from app.services.user_service import get_user
from app.services.sheets_service import add_payment, get_student_payment_summary
from app.services.payment_cache import (
    get_cached_total_paid, 
    add_payment_to_cache,
    get_student_payment_summary_cached
)
from app.config import Config

# States
SELECTING_COURSE, ENTERING_AMOUNT, UPLOADING_PHOTO, CONFIRMING = range(4)

# Store pending payments
pending_payments = {}


def get_student_courses(chat_id: str) -> list:
    """Get all courses for a student (uses local cache - FAST!)."""
    user = get_user(chat_id)
    if not user:
        return []
    
    group_name = user.get('group_name', '')
    student_name = user.get('name', '')
    
    # Load from price_list.json (local file - fast!)
    price_list = Config.load_price_list()
    
    courses = []
    
    for course in price_list.get('courses', []):
        if course.get('group', '').lower() == group_name.lower():
            subject = course.get('subject', 'Course')
            teacher = course.get('teacher', 'Teacher')
            price = course.get('price', price_list.get('default_price', 100))
            currency = course.get('currency', price_list.get('currency', 'USD'))
            
            # Get payment info from LOCAL CACHE (fast!)
            total_paid = get_cached_total_paid(student_name, subject, teacher)
            remaining = max(0, price - total_paid)
            completed = total_paid >= price
            
            courses.append({
                'subject': subject,
                'teacher': teacher,
                'group': group_name,
                'course_price': price,
                'currency': currency,
                'total_paid': total_paid,
                'remaining': remaining,
                'completed': completed
            })
    
    return courses


def courses_keyboard(courses: list):
    """Create keyboard with course options."""
    keyboard = []
    
    for i, course in enumerate(courses):
        if course['completed']:
            status = "✅ Fully Paid"
        else:
            status = f"${course['remaining']:.0f} left"
        
        text = f"📚 {course['subject']} - {course['teacher']} ({status})"
        keyboard.append([InlineKeyboardButton(text, callback_data=f"course_{i}")])
    
    keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="payment_cancel")])
    
    return InlineKeyboardMarkup(keyboard)


async def pay_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /pay command."""
    chat_id = str(update.effective_chat.id)
    user = get_user(chat_id)
    
    if not user:
        await update.message.reply_text(
            "❌ You're not registered!\n"
            "Use /start to register first."
        )
        return ConversationHandler.END
    
    # Show typing indicator
    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
    
    # Get student's courses (now uses cache - fast!)
    courses = get_student_courses(chat_id)
    
    if not courses:
        await update.message.reply_text(
            "❌ No courses found for your group.\n\n"
            "Please contact your administrator."
        )
        return ConversationHandler.END
    
    context.user_data['payment'] = {
        'student_name': user['name'],
        'student_chat_id': chat_id,
        'courses': courses
    }
    
    message = f"💰 <b>Payment Submission</b>\n\n"
    message += f"👤 Student: <b>{user['name']}</b>\n"
    message += f"📖 Group: <b>{user.get('group_name', 'N/A')}</b>\n\n"
    message += "<b>Your Courses:</b>\n\n"
    
    for course in courses:
        if course['completed']:
            status_icon = "✅"
            status_text = "Fully Paid!"
        else:
            status_icon = "📊"
            status_text = f"Remaining: ${course['remaining']:.2f}"
        
        message += (
            f"📚 <b>{course['subject']}</b> - {course['teacher']}\n"
            f"   💵 Course: ${course['course_price']:.2f}\n"
            f"   💰 Paid: ${course['total_paid']:.2f}\n"
            f"   {status_icon} {status_text}\n\n"
        )
    
    message += "<b>Select a course to pay:</b>"
    
    await update.message.reply_text(
        message,
        parse_mode='HTML',
        reply_markup=courses_keyboard(courses)
    )
    
    return SELECTING_COURSE


async def course_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle course selection."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "payment_cancel":
        await query.edit_message_text("❌ Payment cancelled.")
        return ConversationHandler.END
    
    course_idx = int(query.data.replace("course_", ""))
    courses = context.user_data['payment']['courses']
    
    if course_idx >= len(courses):
        await query.edit_message_text("❌ Invalid selection.")
        return ConversationHandler.END
    
    course = courses[course_idx]
    context.user_data['payment']['selected_course'] = course
    
    if course['completed']:
        await query.edit_message_text(
            f"✅ <b>{course['subject']}</b> is already fully paid!\n\n"
            f"Use /pay to select another course.",
            parse_mode='HTML'
        )
        return ConversationHandler.END
    
    await query.edit_message_text(
        f"📚 <b>{course['subject']}</b> - {course['teacher']}\n\n"
        f"💵 Course Price: <b>${course['course_price']:.2f}</b>\n"
        f"✅ Already Paid: <b>${course['total_paid']:.2f}</b>\n"
        f"📊 Remaining: <b>${course['remaining']:.2f}</b>\n\n"
        f"💰 <b>How much are you paying now?</b>\n\n"
        f"<i>Enter amount (e.g., 50 or {course['remaining']:.0f}):</i>",
        parse_mode='HTML'
    )
    
    return ENTERING_AMOUNT


async def amount_entered(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle amount input."""
    text = update.message.text.strip()
    
    if text.startswith('/'):
        await update.message.reply_text("❌ Payment cancelled.")
        return ConversationHandler.END
    
    amount_text = text.replace('$', '').replace(',', '')
    
    try:
        amount = float(amount_text)
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid amount. Please enter a number:\n\n"
            "<i>Example: 50 or 100.50</i>",
            parse_mode='HTML'
        )
        return ENTERING_AMOUNT
    
    if amount <= 0:
        await update.message.reply_text(
            "❌ Amount must be greater than 0.\n\n"
            "Please enter a valid amount:",
            parse_mode='HTML'
        )
        return ENTERING_AMOUNT
    
    course = context.user_data['payment']['selected_course']
    
    if amount > course['remaining']:
        await update.message.reply_text(
            f"⚠️ You're paying <b>${amount:.2f}</b> but only <b>${course['remaining']:.2f}</b> is remaining.\n\n"
            f"This is fine if intentional.\n\n"
            f"📸 <b>Send a photo of your payment receipt:</b>",
            parse_mode='HTML'
        )
    else:
        new_total = course['total_paid'] + amount
        new_remaining = max(0, course['course_price'] - new_total)
        
        await update.message.reply_text(
            f"💰 Payment: <b>${amount:.2f}</b>\n\n"
            f"After this payment:\n"
            f"   ✅ Total Paid: ${new_total:.2f}\n"
            f"   📊 Remaining: ${new_remaining:.2f}\n\n"
            f"📸 <b>Send a photo of your payment receipt:</b>",
            parse_mode='HTML'
        )
    
    context.user_data['payment']['amount'] = amount
    
    return UPLOADING_PHOTO


async def photo_uploaded(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle photo upload."""
    if not update.message.photo:
        await update.message.reply_text(
            "❌ Please send a <b>photo</b> of your payment receipt.",
            parse_mode='HTML'
        )
        return UPLOADING_PHOTO
    
    photo = update.message.photo[-1]
    context.user_data['payment']['photo_file_id'] = photo.file_id
    
    payment = context.user_data['payment']
    course = payment['selected_course']
    amount = payment['amount']
    
    new_total = course['total_paid'] + amount
    new_remaining = max(0, course['course_price'] - new_total)
    fully_paid = "✅ Yes!" if new_total >= course['course_price'] else f"❌ No (${new_remaining:.2f} left)"
    
    await update.message.reply_text(
        f"📋 <b>Payment Summary</b>\n\n"
        f"👤 Student: {payment['student_name']}\n"
        f"📚 Course: {course['subject']}\n"
        f"👨‍🏫 Teacher: {course['teacher']}\n"
        f"📖 Group: {course['group']}\n\n"
        f"💵 Course Price: ${course['course_price']:.2f}\n"
        f"💰 This Payment: ${amount:.2f}\n"
        f"✅ Total After: ${new_total:.2f}\n"
        f"🎯 Fully Paid: {fully_paid}\n\n"
        f"<b>Submit this payment?</b>",
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ Submit", callback_data="payment_submit"),
                InlineKeyboardButton("❌ Cancel", callback_data="payment_cancel")
            ]
        ])
    )
    
    return CONFIRMING


async def payment_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle payment confirmation."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "payment_cancel":
        await query.edit_message_text("❌ Payment cancelled.")
        return ConversationHandler.END
    
    payment = context.user_data['payment']
    course = payment['selected_course']
    
    import uuid
    payment_id = str(uuid.uuid4())[:8]
    
    pending_payments[payment_id] = {
        'student_name': payment['student_name'],
        'student_chat_id': payment['student_chat_id'],
        'subject': course['subject'],
        'teacher': course['teacher'],
        'group': course['group'],
        'amount': payment['amount'],
        'photo_file_id': payment['photo_file_id'],
        'course_price': course['course_price'],
        'previous_paid': course['total_paid']
    }
    
    admin_chat_id = Config.ADMIN_CHAT_ID
    
    new_total = course['total_paid'] + payment['amount']
    new_remaining = max(0, course['course_price'] - new_total)
    completed = "✅ YES" if new_total >= course['course_price'] else "❌ NO"
    
    admin_message = (
        f"💰 <b>NEW PAYMENT</b>\n\n"
        f"🆔 ID: <code>{payment_id}</code>\n\n"
        f"👤 Student: {payment['student_name']}\n"
        f"📚 Course: {course['subject']}\n"
        f"👨‍🏫 Teacher: {course['teacher']}\n"
        f"📖 Group: {course['group']}\n\n"
        f"💵 Course Price: ${course['course_price']:.2f}\n"
        f"💳 Previously Paid: ${course['total_paid']:.2f}\n"
        f"💰 <b>This Payment: ${payment['amount']:.2f}</b>\n"
        f"📊 New Total: ${new_total:.2f}\n"
        f"📉 Remaining: ${new_remaining:.2f}\n"
        f"✅ Fully Paid: {completed}"
    )
    
    try:
        await context.bot.send_message(
            chat_id=admin_chat_id,
            text=admin_message,
            parse_mode='HTML'
        )
        
        await context.bot.send_photo(
            chat_id=admin_chat_id,
            photo=payment['photo_file_id'],
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("✅ Confirm", callback_data=f"admin_confirm_{payment_id}"),
                    InlineKeyboardButton("❌ Reject", callback_data=f"admin_reject_{payment_id}")
                ]
            ])
        )
        
        await query.edit_message_text(
            "✅ <b>Payment submitted!</b>\n\n"
            "Your payment is being reviewed.\n"
            "You'll receive a notification once confirmed.",
            parse_mode='HTML'
        )
        
    except Exception as e:
        print(f"❌ Error: {e}")
        await query.edit_message_text("❌ Error submitting. Please try again.")
    
    return ConversationHandler.END


async def admin_payment_decision(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle admin's confirm/reject decision."""
    query = update.callback_query
    await query.answer()
    
    # Show typing
    await context.bot.send_chat_action(
        chat_id=query.message.chat_id, 
        action=ChatAction.TYPING
    )
    
    data = query.data
    
    if data.startswith("admin_confirm_"):
        payment_id = data.replace("admin_confirm_", "")
        approved = True
    elif data.startswith("admin_reject_"):
        payment_id = data.replace("admin_reject_", "")
        approved = False
    else:
        return
    
    payment = pending_payments.get(payment_id)
    
    if not payment:
        await query.edit_message_caption("❌ Payment not found or already processed.")
        return
    
    if approved:
        try:
            # 1. Add to LOCAL cache (instant!)
            add_payment_to_cache(
                student_name=payment['student_name'],
                subject=payment['subject'],
                teacher=payment['teacher'],
                group_name=payment['group'],
                amount=payment['amount']
            )
            
            # 2. Add to Google Sheets (background, can be slow)
            add_payment(
                student_name=payment['student_name'],
                subject=payment['subject'],
                teacher_name=payment['teacher'],
                group=payment['group'],
                payment_amount=payment['amount'],
                status="✅ Confirmed"
            )
            
            # 3. Get updated summary from cache
            summary = get_student_payment_summary_cached(
                payment['student_name'],
                payment['subject'],
                payment['teacher'],
                payment['course_price']
            )
            
            if summary['completed']:
                status_msg = "🎉 <b>Course fully paid!</b> Thank you!"
            else:
                status_msg = f"📊 Remaining: ${summary['remaining']:.2f}"
            
            await context.bot.send_message(
                chat_id=payment['student_chat_id'],
                text=(
                    f"✅ <b>Payment Confirmed!</b>\n\n"
                    f"📚 Course: {payment['subject']}\n"
                    f"💰 Amount: ${payment['amount']:.2f}\n"
                    f"✅ Total Paid: ${summary['total_paid']:.2f}\n\n"
                    f"{status_msg}"
                ),
                parse_mode='HTML'
            )
            
            await query.edit_message_caption(
                f"✅ CONFIRMED\n\n"
                f"Student: {payment['student_name']}\n"
                f"Course: {payment['subject']}\n"
                f"Amount: ${payment['amount']:.2f}\n"
                f"Total: ${summary['total_paid']:.2f}"
            )
            
        except Exception as e:
            print(f"❌ Error: {e}")
            await query.edit_message_caption(f"❌ Error: {e}")
    
    else:
        await context.bot.send_message(
            chat_id=payment['student_chat_id'],
            text=(
                f"❌ <b>Payment Rejected</b>\n\n"
                f"Your payment for <b>{payment['subject']}</b> was not approved.\n\n"
                f"Please contact your teacher."
            ),
            parse_mode='HTML'
        )
        
        await query.edit_message_caption(
            f"❌ REJECTED\n\n"
            f"Student: {payment['student_name']}\n"
            f"Amount: ${payment['amount']:.2f}"
        )
    
    del pending_payments[payment_id]


async def cancel_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel payment."""
    await update.message.reply_text("❌ Payment cancelled.")
    return ConversationHandler.END