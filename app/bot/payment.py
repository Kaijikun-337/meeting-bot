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
from app.utils.localization import get_user_language, get_text

# States
SELECTING_COURSE, ENTERING_AMOUNT, UPLOADING_PHOTO, CONFIRMING = range(4)

# Store pending payments
pending_payments = {}


def get_student_courses(chat_id: str) -> list:
    """Get list of courses available for this student based on their group."""
    user = get_user(chat_id)
    if not user or not user.get('group_name'):
        return []
    
    group_name = user['group_name']
    student_name = user.get('name', '')
    
    # Load prices
    price_list = Config.load_price_list()
    
    courses = []
    
    # Iterate through courses
    for course in price_list.get('courses', []):
        # 1. Safe Group Check
        c_group = course.get('group') or ""
        
        # 2. Compare (Case-Insensitive)
        if c_group.strip().lower() == group_name.strip().lower():
            
            subject = course.get('subject', 'Course')
            teacher = course.get('teacher', 'Teacher')
            price = course.get('price', 100)
            currency = course.get('currency', 'USD')
            
            # Calculate totals
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


def courses_keyboard(courses: list, lang: str):
    """Create keyboard with course options."""
    keyboard = []
    
    for i, course in enumerate(courses):
        if course['completed']:
            status = get_text('fully_paid', lang)
        else:
            status = f"${course['remaining']:.0f} {get_text('remaining', lang)}"
        
        text = f"📚 {course['subject']} - {course['teacher']} ({status})"
        keyboard.append([InlineKeyboardButton(text, callback_data=f"course_{i}")])
    
    keyboard.append([InlineKeyboardButton(get_text('btn_cancel', lang), callback_data="payment_cancel")])
    
    return InlineKeyboardMarkup(keyboard)


async def pay_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /pay command."""
    chat_id = str(update.effective_chat.id)
    lang = get_user_language(chat_id)
    user = get_user(chat_id)
    
    if not user:
        await update.message.reply_text(get_text('not_registered', lang))
        return ConversationHandler.END
    
    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
    
    courses = get_student_courses(chat_id)
    
    if not courses:
        await update.message.reply_text(get_text('no_courses', lang))
        return ConversationHandler.END
    
    context.user_data['payment'] = {
        'student_name': user['name'],
        'student_chat_id': chat_id,
        'courses': courses
    }
    
    message = f"💰 <b>{get_text('payment_title', lang)}</b>\n\n"
    message += f"👤 {get_text('status_name', lang)}: <b>{user['name']}</b>\n"
    message += f"📖 {get_text('status_group', lang)}: <b>{user.get('group_name', 'N/A')}</b>\n\n"
    message += f"<b>{get_text('your_courses', lang)}:</b>\n\n"
    
    for course in courses:
        if course['completed']:
            status_icon = "✅"
            status_text = get_text('fully_paid', lang)
        else:
            status_icon = "📊"
            status_text = f"{get_text('remaining', lang)}: ${course['remaining']:.2f}"
        
        message += (
            f"📚 <b>{course['subject']}</b> - {course['teacher']}\n"
            f"   💵 {get_text('course_price', lang)}: ${course['course_price']:.2f}\n"
            f"   💰 {get_text('paid', lang)}: ${course['total_paid']:.2f}\n"
            f"   {status_icon} {status_text}\n\n"
        )
    
    message += f"<b>{get_text('select_course', lang)}</b>"
    
    await update.message.reply_text(
        message,
        parse_mode='HTML',
        reply_markup=courses_keyboard(courses, lang)  # ← Pass lang
    )
    
    return SELECTING_COURSE


async def course_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle course selection."""
    query = update.callback_query
    await query.answer()
    
    chat_id = str(update.effective_user.id)
    lang = get_user_language(chat_id)
    
    if query.data == "payment_cancel":
        await query.edit_message_text(get_text('cancelled', lang))
        return ConversationHandler.END
    
    course_idx = int(query.data.replace("course_", ""))
    courses = context.user_data['payment']['courses']
    
    if course_idx >= len(courses):
        await query.edit_message_text(get_text('cancelled', lang))
        return ConversationHandler.END
    
    course = courses[course_idx]
    context.user_data['payment']['selected_course'] = course
    
    if course['completed']:
        await query.edit_message_text(
            get_text('course_already_paid', lang).format(subject=course['subject']),
            parse_mode='HTML'
        )
        return ConversationHandler.END
    
    await query.edit_message_text(
        f"📚 <b>{course['subject']}</b> - {course['teacher']}\n\n"
        f"💵 {get_text('course_price', lang)}: <b>${course['course_price']:.2f}</b>\n"
        f"✅ {get_text('already_paid', lang)}: <b>${course['total_paid']:.2f}</b>\n"
        f"📊 {get_text('remaining', lang)}: <b>${course['remaining']:.2f}</b>\n\n"
        f"💰 <b>{get_text('enter_amount', lang)}</b>\n\n"
        f"<i>{get_text('enter_amount_hint', lang).format(amount=int(course['remaining']))}</i>",
        parse_mode='HTML'
    )
    
    return ENTERING_AMOUNT


async def amount_entered(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle amount input."""
    chat_id = str(update.effective_user.id)
    lang = get_user_language(chat_id)
    text = update.message.text.strip()
    
    if text.startswith('/'):
        await update.message.reply_text(get_text('cancelled', lang))
        return ConversationHandler.END
    
    amount_text = text.replace('$', '').replace(',', '')
    
    try:
        amount = float(amount_text)
    except ValueError:
        await update.message.reply_text(
            get_text('invalid_amount', lang),
            parse_mode='HTML'
        )
        return ENTERING_AMOUNT
    
    if amount <= 0:
        await update.message.reply_text(
            get_text('amount_must_be_positive', lang),
            parse_mode='HTML'
        )
        return ENTERING_AMOUNT
    
    course = context.user_data['payment']['selected_course']
    
    new_total = course['total_paid'] + amount
    new_remaining = max(0, course['course_price'] - new_total)
    
    if amount > course['remaining']:
        await update.message.reply_text(
            get_text('overpaying_warning', lang).format(
                amount=amount,
                remaining=course['remaining']
            ) + f"\n\n📸 <b>{get_text('upload_receipt', lang)}</b>",
            parse_mode='HTML'
        )
    else:
        await update.message.reply_text(
            f"💰 {get_text('payment_amount', lang)}: <b>${amount:.2f}</b>\n\n"
            f"{get_text('after_payment', lang)}:\n"
            f"   ✅ {get_text('total_paid', lang)}: ${new_total:.2f}\n"
            f"   📊 {get_text('remaining', lang)}: ${new_remaining:.2f}\n\n"
            f"📸 <b>{get_text('upload_receipt', lang)}</b>",
            parse_mode='HTML'
        )
    
    context.user_data['payment']['amount'] = amount
    
    return UPLOADING_PHOTO


async def photo_uploaded(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle photo upload."""
    chat_id = str(update.effective_user.id)
    lang = get_user_language(chat_id)
    
    if not update.message.photo:
        await update.message.reply_text(
            get_text('please_send_photo', lang),
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
    fully_paid = get_text('yes', lang) if new_total >= course['course_price'] else f"{get_text('no', lang)} (${new_remaining:.2f} {get_text('remaining', lang).lower()})"
    
    await update.message.reply_text(
        f"📋 <b>{get_text('payment_summary', lang)}</b>\n\n"
        f"👤 {get_text('status_name', lang)}: {payment['student_name']}\n"
        f"📚 {get_text('course', lang)}: {course['subject']}\n"
        f"👨‍🏫 {get_text('teacher', lang)}: {course['teacher']}\n"
        f"📖 {get_text('status_group', lang)}: {course['group']}\n\n"
        f"💵 {get_text('course_price', lang)}: ${course['course_price']:.2f}\n"
        f"💰 {get_text('this_payment', lang)}: ${amount:.2f}\n"
        f"✅ {get_text('total_after', lang)}: ${new_total:.2f}\n"
        f"🎯 {get_text('fully_paid', lang)}: {fully_paid}\n\n"
        f"<b>{get_text('submit_payment_question', lang)}</b>",
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(get_text('btn_submit', lang), callback_data="payment_submit"),
                InlineKeyboardButton(get_text('btn_cancel', lang), callback_data="payment_cancel")
            ]
        ])
    )
    
    return CONFIRMING


async def payment_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle payment confirmation."""
    query = update.callback_query
    await query.answer()
    
    chat_id = str(update.effective_user.id)
    lang = get_user_language(chat_id)
    
    if query.data == "payment_cancel":
        await query.edit_message_text(get_text('cancelled', lang))
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
            get_text('payment_submitted', lang),
            parse_mode='HTML'
        )
        
    except Exception as e:
        print(f"❌ Error: {e}")
        await query.edit_message_text(get_text('error_occurred', lang))
    
    return ConversationHandler.END


async def admin_payment_decision(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle admin's confirm/reject decision."""
    query = update.callback_query
    await query.answer()
    
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
    
    student_lang = get_user_language(payment['student_chat_id'])
    
    if approved:
        try:
            add_payment_to_cache(
                student_name=payment['student_name'],
                subject=payment['subject'],
                teacher=payment['teacher'],
                group_name=payment['group'],
                amount=payment['amount']
            )
            
            add_payment(
                student_name=payment['student_name'],
                subject=payment['subject'],
                teacher_name=payment['teacher'],
                group=payment['group'],
                payment_amount=payment['amount'],
                status="✅ Confirmed"
            )
            
            summary = get_student_payment_summary_cached(
                payment['student_name'],
                payment['subject'],
                payment['teacher'],
                payment['course_price']
            )
            
            if summary['completed']:
                status_msg = get_text('congratulations_fully_paid', student_lang)
            else:
                status_msg = f"📊 {get_text('remaining', student_lang)}: ${summary['remaining']:.2f}"
            
            await context.bot.send_message(
                chat_id=payment['student_chat_id'],
                text=get_text('payment_confirmed_notification', student_lang).format(
                    subject=payment['subject'],
                    amount=payment['amount'],
                    total_paid=summary['total_paid'],
                    status=status_msg
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
            text=get_text('payment_rejected_notification', student_lang).format(
                subject=payment['subject']
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
    lang = get_user_language(str(update.effective_user.id))
    await update.message.reply_text(get_text('cancelled', lang))
    return ConversationHandler.END