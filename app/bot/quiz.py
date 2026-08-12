from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CallbackQueryHandler, CommandHandler
from app.config import Config
from app.utils.localization import get_user_language

QUIZ_ACTIVE = 0

# UI Texts (Multilingual)
QUIZ_UI_TEXTS = {
    'intro': {
        'en': "🧠 <b>Quick English Level Test</b>\n\nLet's find out your English level! It's just 5 quick questions. Choose the correct missing word for each sentence.",
        'ru': "🧠 <b>Быстрый тест на определение уровня</b>\n\nДавайте определим ваш уровень! Это всего 5 быстрых вопросов. Выберите правильное пропущенное слово в каждом предложении.",
        'uz': "🧠 <b>Tezkor darajani aniqlash testi</b>\n\nKeling, sizning darajangizni aniqlaymiz! Bu atigi 5 ta tezkor savoldan iborat. Har bir gapda tushib qolgan to'g'ri so'zni tanlang."
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

# Questions (Strictly English)
QUIZ_QUESTIONS = [
    {
        "q": "1. How long ___ you been learning English?",
        "o": ["have", "has", "did", "are"],
        "c": "have"
    },
    {
        "q": "2. I wish I ___ more time to travel.",
        "o": ["have", "had", "will have", "would have"],
        "c": "had"
    },
    {
        "q": "3. She is the woman ___ car was stolen yesterday.",
        "o": ["who", "which", "whose", "that"],
        "c": "whose"
    },
    {
        "q": "4. By the time we arrived at the cinema, the movie ___.",
        "o": ["started", "has started", "had started", "is starting"],
        "c": "had started"
    },
    {
        "q": "5. Despite ___ very hard, he didn't pass the exam.",
        "o": ["studying", "he studied", "to study", "studied"],
        "c": "studying"
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
    
    await update.message.reply_text(get_ui_text('intro', lang), parse_mode='HTML')
    
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
    
    # Admin notification kept in English as requested
    admin_text = (
        f"🧠 <b>New Lead Took The Quiz!</b>\n\n"
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

quiz_conv_handler = ConversationHandler(
    entry_points=[CommandHandler("quiz", start_quiz)],
    states={
        QUIZ_ACTIVE: [CallbackQueryHandler(handle_quiz_answer, pattern='^quiz_')]
    },
    fallbacks=[CommandHandler("cancel", cancel_quiz)]
)