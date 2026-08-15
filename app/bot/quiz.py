from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters, ApplicationHandlerStop
from app.config import Config
from app.utils.localization import get_user_language
import asyncio

QUIZ_ACTIVE_KEY = 1

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
        'en': "🎉 <b>Quiz Complete!</b>\n\nYour score: <b>{score}/{total}</b>\nYour estimated level: <b>{level}</b>\n\nAreas to improve: <i>{weak_topics}</i>\n\nOur manager will contact you shortly to discuss the best group for you!",
        'ru': "🎉 <b>Тест завершен!</b>\n\nВаш результат: <b>{score}/{total}</b>\nВаш примерный уровень: <b>{level}</b>\n\nЗоны для улучшения: <i>{weak_topics}</i>\n\nНаш менеджер скоро свяжется с вами, чтобы обсудить подходящую группу!",
        'uz': "🎉 <b>Test yakunlandi!</b>\n\nSizning balingiz: <b>{score}/{total}</b>\nTaxminiy darajangiz: <b>{level}</b>\n\nYaxshilash kerak bo'lgan yo'nalishlar: <i>{weak_topics}</i>\n\nMenejerimiz sizga mos guruhni muhokama qilish uchun tez orada bog'lanadi!"
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
    },
    'no_weak_topics': {
        'en': "None - Perfect score! 🎯",
        'ru': "Нет - Идеальный результат! 🎯",
        'uz': "Yo'q - Mukammal natija! 🎯"
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
        "c": "the UK",
        "topic": "Countries & Nationalities"
    },
    {
        "q_video": "BAACAgIAAxkBAAIBkGp--m53YhGX3E5vjMeiWYzxbPtNAAJFowACqW74S1FhFN92Baw4PQQ",
        "q": "2. When does Rob think Jenny arrives in London?",
        "o": ["On 20th March", "On 12th of March", "Next week", "He doesn't know"],
        "c": "On 12th of March",
        "topic": "Dates & Time"
    },
    {
        "q_video": "BAACAgIAAxkBAAIBkWp--m5doKst4-Chv6s0IvQzGPdyAAJGowACqW74S53VqW9xYI6mPQQ",
        "q": "3. He's in Poland _____",
        "o": ["on holiday", "for work", "on business", "for fun"],
        "c": "for work",
        "topic": "Purpose & Prepositions"
    },
    {
        "q_video": "BAACAgIAAxkBAAIBjWp--m6UJaaZJZOQSHvLlavHmceDAAJCowACqW74SyxvdZeVRIZKPQQ",
        "q": "4. How old is Ben?",
        "o": ["25", "23", "24", "26"],
        "c": "25",
        "topic": "Numbers & Ages"
    },
    {
        "q_video": "BAACAgIAAxkBAAIBjmp--m43UmLHh7TqXTR0H3ktwKWrAAJDowACqW74S1l2SCCmg7j-PQQ",
        "q": "5. Ben likes Izzy's _____",
        "o": ["coat", "T-shirt", "jumper", "jacket"],
        "c": "jacket",
        "topic": "Clothing Vocabulary"
    },
    {
        "q_video": "BAACAgIAAxkBAAIBhmp--m68vOJD6yBswUQ_AAEfIav04gACO6MAAqlu-Eudxbe3A0ya0z0E",
        "q": "6. Izzy says Ben _____ to wear a helmet.",
        "o": ["needs", "doesn't need", "need", "hasn't"],
        "c": "needs",
        "topic": "Subject-Verb Agreement"
    },
    {
        "q_video": "BAACAgIAAxkBAAIBh2p--m5pBwkmqz7sM1v_ROhwGOeuAAI9owACqW74S9Lc3SAf2Ut5PQQ",
        "q": "7. Carla is ______ when Ben hurts his back.",
        "o": ["helpful", "concerned", "annoyed", "surprised"],
        "c": "helpful",
        "topic": "Feelings & Adjectives"
    },
    {
        "q_video": "BAACAgIAAxkBAAIBiGp--m5ycgRZlbPQBGaj9fbq7nGVAAI8owACqW74Sz88zZOQmc1NPQQ",
        "q": "8. How much does Ben think the shoes are?",
        "o": ["£90.95", "£95.99", "£90.50", "£19.95"],
        "c": "£95.99",
        "topic": "Prices & Currency"
    },
    {
        "q_video": "BAACAgIAAxkBAAIBiWp--m4NSr32b9msJ2pwioJBopB1AAI-owACqW74S6aS-6YGSSeGPQQ",
        "q": "9. Ben has _____ memories of the dinner at the restaurant.",
        "o": ["bad", "good", "fond", "neutral"],
        "c": "bad",
        "topic": "Adjectives & Vocabulary"
    },
    {
        "q_video": "BAACAgIAAxkBAAIBimp--m6cVtGJQVbOGUeXEUNs1rjqAAJAowACqW74S8tZJKTuELkcPQQ",
        "q": "10. Carla _____ angry with Ben for being late.",
        "o": ["isn't", "is", "aren't", "be"],
        "c": "isn't",
        "topic": "Verb 'To Be'"
    },
    {
        "q_video": "BAACAgIAAxkBAAIBi2p--m5IfL1IpzmsQAWDBm1MpxWwAAI_owACqW74SyfkLdjpBypBPQQ",
        "q": "11. Izzy is angry with herself because ...",
        "o": ["she trusted Max too much", "she gave a bad presentation", "she took poor photos", "she forgot her notes"],
        "c": "she trusted Max too much",
        "topic": "Cause & Effect (Listening)"
    },
    {
        "q_video": "BAACAgIAAxkBAAIBjGp--m788hC-b91_npDg3L6yAmvUAAJBowACqW74S87eRwN0dJ0MPQQ",
        "q": "12. How did Pamela react to Ben's photos?",
        "o": ["She was amazed", "She didn't like them", "She was disappointed", "She barely noticed them"],
        "c": "She was amazed",
        "topic": "Inference & Reactions"
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
        return

    if context.user_data.get(QUIZ_ACTIVE_KEY, False):
        await update.message.reply_text(get_ui_text('already_taking', lang))
        return

    context.user_data['quiz_score'] = 0
    context.user_data['quiz_index'] = 0
    context.user_data['weak_topics'] = []
    context.user_data[QUIZ_ACTIVE_KEY] = True
    
    await update.message.reply_text(get_ui_text('intro_video', lang), parse_mode='HTML')
    await send_question(update, context)

async def send_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    index = context.user_data['quiz_index']
    q_data = QUIZ_QUESTIONS[index]
    chat_id = update.effective_chat.id
    
    keyboard = []
    for opt in q_data['o']:
        keyboard.append([KeyboardButton(opt)])
        
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    
    await context.bot.send_video(
        chat_id=chat_id,
        video=q_data['q_video'],
        caption=f"<b>{q_data['q']}</b>",
        parse_mode='HTML',
        reply_markup=reply_markup
    )

async def handle_quiz_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # If user is not in quiz, let other handlers process this message
    if not context.user_data.get(QUIZ_ACTIVE_KEY, False):
        return
    
    text = update.message.text
    index = context.user_data['quiz_index']
    q_data = QUIZ_QUESTIONS[index]
    lang = get_user_language(str(update.effective_chat.id))
    
    if text not in q_data['o']:
        await update.message.reply_text(get_ui_text('use_buttons', lang))
        raise ApplicationHandlerStop()
        
    is_correct = text == q_data['c']
    
    if is_correct:
        context.user_data['quiz_score'] += 1
        feedback = get_ui_text('correct', lang)
    else:
        feedback = get_ui_text('wrong', lang, ans=q_data['c'])
        
        topic = q_data.get('topic', 'General')
        if topic not in context.user_data['weak_topics']:
            context.user_data['weak_topics'].append(topic)
        
    await update.message.reply_text(feedback, parse_mode='HTML')
        
    context.user_data['quiz_index'] += 1
    
    await asyncio.sleep(1.5)
    
    if context.user_data['quiz_index'] < len(QUIZ_QUESTIONS):
        await send_question(update, context)
    else:
        await finish_quiz(update, context)
        
    raise ApplicationHandlerStop()

async def finish_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    score = context.user_data['quiz_score']
    total = len(QUIZ_QUESTIONS)
    level = get_level(score, total)
    user = update.effective_user
    chat_id = update.effective_chat.id
    lang = get_user_language(str(chat_id))
    
    weak_topics = context.user_data.get('weak_topics', [])
    
    # Format the weak topics string for the user
    if weak_topics:
        weak_str = ", ".join(weak_topics)
    else:
        weak_str = get_ui_text('no_weak_topics', lang)
    
    # Pass weak_str into the result message
    result_text = get_ui_text('result', lang, score=score, total=total, level=level, weak_topics=weak_str)
    
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
        f"Level: <b>{level}</b>\n"
        f"Weak Topics: <i>{weak_str}</i>"
    )
    
    try:
        await context.bot.send_message(chat_id=Config.ADMIN_CHAT_ID, text=admin_text, parse_mode='HTML')
    except Exception as e:
        print(f"Failed to send quiz result to admin: {e}")
        
    context.user_data[QUIZ_ACTIVE_KEY] = False

async def cancel_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get(QUIZ_ACTIVE_KEY, False):
        lang = get_user_language(str(update.effective_chat.id))
        from app.bot.keyboards import unregistered_menu_keyboard
        context.user_data[QUIZ_ACTIVE_KEY] = False
        await update.message.reply_text(get_ui_text('cancelled', lang), reply_markup=unregistered_menu_keyboard(lang))
        raise ApplicationHandlerStop()