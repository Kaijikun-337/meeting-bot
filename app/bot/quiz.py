from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, filters
from app.config import Config
from app.utils.localization import get_user_language
import asyncio

QUIZ_ACTIVE = 0

# UI Texts (Multilingual)
QUIZ_UI_TEXTS = {
    'intro_video': {
        'en': "🎥 <b>Video Quiz Time!</b>\n\nWatch the video, then answer the question. If you get it wrong, we'll show you a video with the correct answer. Let's go!",
        'ru': "🎥 <b>Время видео-теста!</b>\n\nПосмотрите видео и ответьте на вопрос. Если ошибетесь, мы покажем видео с правильным ответом. Поехали!",
        'uz': "🎥 <b>Video test vaqti!</b>\n\nVideoni tomosha qiling va savolga javob bering. Xato qilsangiz, to'g'ri javobli videoni ko'rsatamiz. Boshladik!"
    },
    'correct': {
        'en': "✅ Correct! Get ready for the next one...",
        'ru': "✅ Правильно! Готовьтесь к следующему...",
        'uz': "✅ To'g'ri! Keyingisiga tayyorgarlik ko'ring..."
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

# ┌───────────────────────────────────────────────────────────┐
# │  PASTE YOUR VIDEO FILE IDs AND QUESTIONS HERE             │
# └───────────────────────────────────────────────────────────┘

QUIZ_QUESTIONS = [
    {
        "q_video": "BAACAgIAAxkBAAIBj2p--m5ZbQ8hu8vLBXmadLh6km1iAAJEowACqW74S2K4dgVQThq_PQQ",
        "q": "1. Rob is from ____",
        "o": ["the UK", "the USA", "Russia", "Poland"],
        "c": "the UK"
    },
    {
        "q_video": "BAACAgIAAxkBAAIBkGp--m53YhGX3E5vjMeiWYzxbPtNAAJFowACqW74S1FhFN92Baw4PQQ",
        "q": "2. When does Rob think Jenny arrives in London?",
        "o": ["On 20th March", "On 12th of March", "Next week", "He doesn't know"],
        "c": "On 12th of March"
    },
    {
        "q_video": "BAACAgIAAxkBAAIBkWp--m5doKst4-Chv6s0IvQzGPdyAAJGowACqW74S53VqW9xYI6mPQQ",
        "q": "3. He's in Poland _____",
        "o": ["on holiday", "for work", "on business", "for fun"],
        "c": "for work"
    },
    {
        "q_video": "BAACAgIAAxkBAAIBjWp--m6UJaaZJZOQSHvLlavHmceDAAJCowACqW74SyxvdZeVRIZKPQQ",
        "q": "4. How old is Ben?",
        "o": ["25", "23", "24", "26"],
        "c": "25"
    },
    {
        "q_video": "BAACAgIAAxkBAAIBjmp--m43UmLHh7TqXTR0H3ktwKWrAAJDowACqW74S1l2SCCmg7j-PQQ",
        "q": "5. Ben likes Izzy's _____",
        "o": ["coat", "T-shirt", "jumper", "jacket"],
        "c": "jacket"
    },
    {
        "q_video": "BAACAgIAAxkBAAIBhmp--m68vOJD6yBswUQ_AAEfIav04gACO6MAAqlu-Eudxbe3A0ya0z0E",
        "q": "6. Izzy says Ben _____ to wear a helmet.",
        "o": ["needs", "doesn't need", "need", "hasn't"],
        "c": "needs"
    },
    {
        "q_video": "BAACAgIAAxkBAAIBh2p--m5pBwkmqz7sM1v_ROhwGOeuAAI9owACqW74S9Lc3SAf2Ut5PQQ",
        "q": "7. Carla is ______ when Ben hurts his back.",
        "o": ["helpful", "concerned", "annoyed", "surprised"],
        "c": "helpful"
    },
    {
        "q_video": "BAACAgIAAxkBAAIBiGp--m5ycgRZlbPQBGaj9fbq7nGVAAI8owACqW74Sz88zZOQmc1NPQQ",
        "q": "8. How much does Ben think the shoes are?",
        "o": ["£90.95", "£95.90", "£90.50", "£19.95"],
        "c": "£90.95"
    },
    {
        "q_video": "BAACAgIAAxkBAAIBiWp--m4NSr32b9msJ2pwioJBopB1AAI-owACqW74S6aS-6YGSSeGPQQ",
        "q": "9. Ben has _____ memories of the dinner at the restaurant.",
        "o": ["bad", "good", "fond", "neutral"],
        "c": "bad"
    },
    {
        "q_video": "BAACAgIAAxkBAAIBimp--m6cVtGJQVbOGUeXEUNs1rjqAAJAowACqW74S8tZJKTuELkcPQQ",
        "q": "10. Carla _____ angry with Ben for being late.",
        "o": ["isn't", "is", "aren't", "be"],
        "c": "isn't"
    },
    {
        "q_video": "BAACAgIAAxkBAAIBi2p--m5IfL1IpzmsQAWDBm1MpxWwAAI_owACqW74SyfkLdjpBypBPQQ",
        "q": "11. Izzy is angry with herself because ...",
        "o": [
            "she trusted Max too much",
            "she gave a bad presentation",
            "she took poor photos",
            "she forgot her notes"
        ],
        "c": "she trusted Max too much"
    },
    {
        "q_video": "BAACAgIAAxkBAAIBjGp--m788hC-b91_npDg3L6yAmvUAAJBowACqW74S87eRwN0dJ0MPQQ",
        "q": "12. How did Pamela react to Ben's photos?",
        "o": [
            "She was amazed",
            "She didn't like them",
            "She was disappointed",
            "She barely noticed them"
        ],
        "c": "She was amazed"
    }
    
]

# ┌───────────────────────────────────────────────────────────┐
# │  CORE LOGIC                                               │
# └───────────────────────────────────────────────────────────┘

def get_ui_text(key, lang, **kwargs):
    text = QUIZ_UI_TEXTS.get(key, {}).get(lang, QUIZ_UI_TEXTS.get(key, {}).get('en', ''))
    return text.format(**kwargs)

def get_level(score: int, total: int) -> str:
    percentage = (score / total) * 100 if total > 0 else 0
    if percentage <= 33:
        return "A1-A2 (Beginner / Elementary)"
    elif percentage <= 66:
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
    
    # 1. Send intro text
    await update.message.reply_text(get_ui_text('intro_video', lang), parse_mode='HTML')
    
    # 2. Ask the first question
    await send_question(update, context)
    return QUIZ_ACTIVE

async def send_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    index = context.user_data['quiz_index']
    q_data = QUIZ_QUESTIONS[index]
    chat_id = update.effective_chat.id
    
    # Build ReplyKeyboard with options
    keyboard = []
    for opt in q_data['o']:
        keyboard.append([KeyboardButton(opt)])
        
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    
    # Send the Question Video with the text question as a caption
    await context.bot.send_video(
        chat_id=chat_id,
        video=q_data['q_video'],
        caption=f"<b>{q_data['q']}</b>",
        parse_mode='HTML',
        reply_markup=reply_markup
    )

async def handle_quiz_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    index = context.user_data['quiz_index']
    q_data = QUIZ_QUESTIONS[index]
    lang = get_user_language(str(update.effective_chat.id))
    
    # If user types random text instead of clicking a button
    if text not in q_data['o']:
        await update.message.reply_text(get_ui_text('use_buttons', lang))
        return QUIZ_ACTIVE
        
    is_correct = text == q_data['c']
    
    if is_correct:
        context.user_data['quiz_score'] += 1
        feedback = get_ui_text('correct', lang)
    else:
        feedback = get_ui_text('wrong', lang, ans=q_data['c'])
        
    # Send feedback as a normal text message
    await update.message.reply_text(feedback, parse_mode='HTML')
        
    context.user_data['quiz_index'] += 1
    
    # Small pause before next question for better UX
    await asyncio.sleep(1.5)
    
    if context.user_data['quiz_index'] < len(QUIZ_QUESTIONS):
        await send_question(update, context)
    else:
        await finish_quiz(update, context)
        return ConversationHandler.END
        
    return QUIZ_ACTIVE

async def finish_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    score = context.user_data['quiz_score']
    total = len(QUIZ_QUESTIONS)
    level = get_level(score, total)
    user = update.effective_user
    chat_id = update.effective_chat.id
    lang = get_user_language(str(chat_id))
    
    result_text = get_ui_text('result', lang, score=score, total=total, level=level)
    
    # Bring back the unregistered menu so they aren't stuck without a keyboard
    from app.bot.keyboards import unregistered_menu_keyboard
    await context.bot.send_message(
        chat_id=chat_id, 
        text=result_text, 
        parse_mode='HTML', 
        reply_markup=unregistered_menu_keyboard(lang)
    )
    
    admin_text = (
        f"🧠 <b>New Lead Took The Video Quiz!</b>\n\n"
        f"Name: {user.full_name}\n"
        f"Username: @{user.username if user.username else 'N/A'}\n"
        f"Telegram ID: <code>{chat_id}</code>\n\n"
        f"Score: {score}/{total}\n"
        f"Level: <b>{level}</b>"
    )
    
    try:
        await context.bot.send_message(chat_id=Config.ADMIN_CHAT_ID, text=admin_text, parse_mode='HTML')
    except Exception as e:
        print(f"Failed to send quiz result to admin: {e}")

async def cancel_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_user_language(str(update.effective_chat.id))
    from app.bot.keyboards import unregistered_menu_keyboard
    await update.message.reply_text(get_ui_text('cancelled', lang), reply_markup=unregistered_menu_keyboard(lang))
    return ConversationHandler.END

quiz_conv_handler = ConversationHandler(
    entry_points=[
        CommandHandler("quiz", start_quiz),
        MessageHandler(filters.Regex('^🧠'), start_quiz),
        MessageHandler(filters.Regex('^/start quiz$'), start_quiz)
    ],
    states={
        # Listen for text messages instead of callback queries
        QUIZ_ACTIVE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_quiz_answer)]
    },
    fallbacks=[CommandHandler("cancel", cancel_quiz)]
)