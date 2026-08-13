from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CallbackQueryHandler, CommandHandler, MessageHandler, filters
from app.config import Config
from app.utils.localization import get_user_language

QUIZ_ACTIVE = 0

VIDEO_URL = "https://www.w3schools.com/html/mov_bbb.mp4"

# UI Texts (Multilingual)
QUIZ_UI_TEXTS = {
    'intro_video': {
        'en': "🎥 <b>Please watch this short video.</b>\nOnce you've watched it, answer the 5 questions below to test your listening skills!",
        'ru': "🎥 <b>Пожалуйста, посмотрите это короткое видео.</b>\nПосле просмотра ответьте на 5 вопросов ниже, чтобы проверить свои навыки аудирования!",
        'uz': "🎥 <b>Iltimos, bu qisqani videoni tomosha qiling.</b>\nKo'rgach, tinglash qobiliyatingizni tekshirish uchun quyidagi 5 ta savolga javob bering!"
    },
    'correct': {
        'en': "✅ Correct!",
        'ru': "✅ Правильно!",
        'uz': "✅ To'g'ri!"
    },
    'wrong': {
        'en': "❌ Wrong. The correct answer was: <b>{ans}</b>",
        'ru': "❌ Неверно. Правильный ответ: <b>{ans}</b>",
        'uz': "❌ Noto'g'ri. To'g'ri javob: <b>{ans}</b>"
    },
    'result': {
        'en': "🎉 <b>Quiz Complete!</b>\n\nYour score: <b>{score}/{total}</b>\nYour estimated level: <b>{level}</b>\n\nOur manager will contact you shortly to discuss the best group for you!",
        'ru': "🎉 <b>Тест завершен!</b>\n\nВаш результат: <b>{score}/{total}</b>\nВаш примерный уровень: <b>{level}</b>\n\nНаш менеджер скоро свяжется с вами, чтобы обсудить подходящую группу!",
        'uz': "🎉 <b>Test yakunlandi!</b>\n\nSizning balingiz: <b>{score}/{total}</b>\nTaxminiy darajangiz: <b>{level}</b>\n\nMenejerimiz sizga mos guruhni muhokama qilish uchun tez orada bog'lanadi!"
    },
    'cancelled': {
        'en': "Quiz cancelled. You can start it again anytime with /quiz",
        'ru': "Тест отменен. Вы можете начать его снова в любое время с помощью /quiz",
        'uz': "Test bekor qilindi. Uni istalgan vaqtda /quiz bilan qayta boshlashingiz mumkin."
    },
    'admin_cant': {
        'en': "Admins can't take the quiz 😊",
        'ru': "Админы не могут проходить тест 😊",
        'uz': "Adminlar testni topshira olmaydi 😊"
    }
}

# Questions based on the video (English only)
QUIZ_QUESTIONS = [
    {
        "q": "1. What animal is the main character of the video?",
        "o": ["A cat", "A rabbit", "A dog", "A bear"],
        "c": "A rabbit"
    },
    {
        "q": "2. What is the rabbit looking at at the beginning of the video?",
        "o": ["A clock", "A mirror", "A window", "A book"],
        "c": "A clock"
    },
    {
        "q": "3. What happens after the rabbit looks at the clock?",
        "o": ["He goes to sleep", "He starts running", "He eats a carrot", "He opens a door"],
        "c": "He starts running"
    },
    {
        "q": "4. Who does the rabbit meet in the hallway?",
        "o": ["A mouse", "A cat", "Another rabbit", "A bird"],
        "c": "A cat"
    },
    {
        "q": "5. How does the video end?",
        "o": ["They fight", "They run through a door", "They eat dinner", "They go outside"],
        "c": "They run through a door"
    }
]

def get_ui_text(key, lang, **kwargs):
    text = QUIZ_UI_TEXTS.get(key, {}).get(lang, QUIZ_UI_TEXTS.get(key, {}).get('en', ''))
    return text.format(**kwargs)

def get_level(score: int) -> str:
    if score <= 1:
        return "A1-A2 (Beginner / Elementary)"
    elif score <= 3:
        return "B1 (Intermediate)"
    else:
        return "B2-C1 (Upper-Intermediate / Advanced)"

async def start_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat_id = update.effective_chat.id
    lang = get_user_language(str(chat_id))
    
    if str(chat_id) == str(Config.ADMIN_CHAT_ID):
        await update.message.reply_text(get_ui_text('admin_cant', lang))
        return ConversationHandler.END

    context.user_data['quiz_score'] = 0
    context.user_data['quiz_index'] = 0
    
    # 1. Send the video first
    try:
        await context.bot.send_video(
            chat_id=chat_id,
            video=VIDEO_URL,
            caption=get_ui_text('intro_video', lang),
            parse_mode='HTML'
        )
    except Exception as e:
        # Fallback if video fails to send
        print(f"Failed to send quiz video: {e}")
        await update.message.reply_text(get_ui_text('intro_video', lang), parse_mode='HTML')
    
    # 2. Ask the first question
    await send_question(update, context)
    return QUIZ_ACTIVE

async def send_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    index = context.user_data['quiz_index']
    q_data = QUIZ_QUESTIONS[index]
    
    keyboard = []
    for opt in q_data['o']:
        keyboard.append([InlineKeyboardButton(opt, callback_data=f"quiz_{opt}")])
        
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"<b>{q_data['q']}</b>",
        parse_mode='HTML',
        reply_markup=reply_markup
    )

async def handle_quiz_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    lang = get_user_language(str(update.effective_chat.id))
    selected_opt = query.data.replace("quiz_", "")
    index = context.user_data['quiz_index']
    q_data = QUIZ_QUESTIONS[index]
    
    if selected_opt == q_data['c']:
        context.user_data['quiz_score'] += 1
        feedback = get_ui_text('correct', lang)
    else:
        feedback = get_ui_text('wrong', lang, ans=q_data['c'])
        
    await query.edit_message_text(
        text=f"{q_data['q']}\n\n{feedback}",
        parse_mode='HTML'
    )
    
    context.user_data['quiz_index'] += 1
    
    if context.user_data['quiz_index'] < len(QUIZ_QUESTIONS):
        await send_question(update, context)
    else:
        await finish_quiz(update, context)
        return ConversationHandler.END
        
    return QUIZ_ACTIVE

async def finish_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    score = context.user_data['quiz_score']
    level = get_level(score)
    user = update.effective_user
    chat_id = update.effective_chat.id
    lang = get_user_language(str(chat_id))
    
    result_text = get_ui_text('result', lang, score=score, total=len(QUIZ_QUESTIONS), level=level)
    await context.bot.send_message(chat_id=chat_id, text=result_text, parse_mode='HTML')
    
    admin_text = (
        f"🧠 <b>New Lead Took The Video Quiz!</b>\n\n"
        f"Name: {user.full_name}\n"
        f"Username: @{user.username if user.username else 'N/A'}\n"
        f"Telegram ID: <code>{chat_id}</code>\n\n"
        f"Score: {score}/{len(QUIZ_QUESTIONS)}\n"
        f"Level: <b>{level}</b>"
    )
    
    try:
        await context.bot.send_message(chat_id=Config.ADMIN_CHAT_ID, text=admin_text, parse_mode='HTML')
    except Exception as e:
        print(f"Failed to send quiz result to admin: {e}")

async def cancel_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_user_language(str(update.effective_chat.id))
    await update.message.reply_text(get_ui_text('cancelled', lang))
    return ConversationHandler.END

# Updated ConversationHandler with Deep Link support
quiz_conv_handler = ConversationHandler(
    entry_points=[
        CommandHandler("quiz", start_quiz),
        MessageHandler(filters.Regex('^🧠'), start_quiz),
        MessageHandler(filters.Regex('^/start quiz$'), start_quiz) # Deep Link!
    ],
    states={
        QUIZ_ACTIVE: [CallbackQueryHandler(handle_quiz_answer, pattern='^quiz_')]
    },
    fallbacks=[CommandHandler("cancel", cancel_quiz)]
)