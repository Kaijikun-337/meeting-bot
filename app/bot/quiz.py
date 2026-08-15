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
        'en': "🎉 <b>Quiz Complete!</b>\n\nYour score: <b>{score}/{total}</b>\nYour estimated level: <b>{level}</b>\n\n<b>Areas to improve:</b>\n{weak_topics}\n\nOur manager will contact you shortly to discuss the best group for you!",
        'ru': "🎉 <b>Тест завершен!</b>\n\nВаш результат: <b>{score}/{total}</b>\nВаш примерный уровень: <b>{level}</b>\n\n<b>Зоны для улучшения:</b>\n{weak_topics}\n\nНаш менеджер скоро свяжется с вами, чтобы обсудить подходящую группу!",
        'uz': "🎉 <b>Test yakunlandi!</b>\n\nSizning balingiz: <b>{score}/{total}</b>\nTaxminiy darajangiz: <b>{level}</b>\n\n<b>Yaxshilash kerak bo'lgan yo'nalishlar:</b>\n{weak_topics}\n\nMenejerimiz sizga mos guruhni muhokama qilish uchun tez orada bog'lanadi!"
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
    },
    'phone_request': {
        'en': "📱 We noticed you don't have a Telegram @username. To help our manager contact you quickly, please share your phone number.",
        'ru': "📱 Мы заметили, что у вас нет @username в Telegram. Чтобы наш менеджер мог быстро с вами связаться, пожалуйста, поделитесь своим номером телефона.",
        'uz': "📱 Sizda Telegram @username yo'qligini payqadik. Menejerimiz siz bilan tez bog'lanishi uchun iltimos, telefon raqamingizni ulashing."
    },
    'share_phone_btn': {
        'en': "📱 Share Phone Number",
        'ru': "📱 Отправить номер телефона",
        'uz': "📱 Telefon raqamni ulashish"
    },
    'phone_received': {
        'en': "✅ Thank you! Our manager will contact you soon.",
        'ru': "✅ Спасибо! Наш менеджер скоро свяжется с вами.",
        'uz': "✅ Rahmat! Menejerimiz tez orada siz bilan bog'lanadi."
    },
    'price_list': {
        'en': "📋 <b>Price List & Plans</b>\n\nChoose the best option for you:\n\n📚 <b>Standard</b> (groups of 8-10 students)\n💵 750,000 UZS / month\n\n⭐️ <b>Comfort</b> (mini-groups up to 4 students)\n💵 1,200,000 UZS / month\n\n💎 <b>Ultima</b> (1-on-1)\n💵 2,500,000 UZS / month\n\n👇 Please select a plan below:",
        'ru': "📋 <b>Прайс-лист и тарифы</b>\n\nВыберите лучший вариант для себя:\n\n📚 <b>Стандарт</b> (группы 8-10 человек)\n💵 750 000 сум / мес\n\n⭐️ <b>Комфорт</b> (мини-группы до 4 человек)\n💵 1 200 000 сум / мес\n\n💎 <b>Ultima</b> (индивидуально)\n💵 2 500 000 сум / мес\n\n👇 Пожалуйста, выберите тариф ниже:",
        'uz': "📋 <b>Narxlar va tariflar</b>\n\nO'zingizga mos eng yaxshi variantni tanlang:\n\n📚 <b>Standard</b> (8-10 kishilik guruhlar)\n💵 750,000 UZS / oy\n\n⭐️ <b>Comfort</b> (4 kishigacha mini-guruhlar)\n💵 1,200,000 UZS / oy\n\n💎 <b>Ultima</b> (1-dan 1-ga)\n💵 2,500,000 UZS / oy\n\n👇 Iltimos, quyidan tarifni tanlang:"
    },
    'plan_group': {
        'en': '📚 Standard',
        'ru': '📚 Стандарт',
        'uz': '📚 Standard'
    },
    'plan_mini_group': {
        'en': '⭐️ Comfort',
        'ru': '⭐️ Комфорт',
        'uz': '⭐️ Comfort'
    },
    'plan_individual': {
        'en': '💎 Ultima',
        'ru': '💎 Ultima',
        'uz': '💎 Ultima'
    },
        'already_taking': {
        'en': "You are already taking the quiz! Please answer the current question.",
        'ru': "Вы уже проходите тест! Пожалуйста, ответьте на текущий вопрос.",
        'uz': "Siz allaqachon testni topshiryapsiz! Iltimos, joriy savolga javob bering."
    },
    'use_buttons': {
        'en': "Please select an answer using the buttons below 👇",
        'ru': "Пожалуйста, выберите ответ, используя кнопки ниже 👇",
        'uz': "Iltimos, quyidagi tugmalardan foydalanib javobni tanlang 👇"
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

QUIZ_TOPICS = {
    "Countries & Nationalities": {
        "en": "Countries & Nationalities -> Example: UK, USA, Polish",
        "ru": "Страны и национальности (Countries) -> Пример: UK, USA, Polish",
        "uz": "Davlatlar va millatlar (Countries) -> Masalan: UK, USA, Polish"
    },
    "Dates & Time": {
        "en": "Dates & Time -> Example: 12th of March",
        "ru": "Даты и время (Dates & Time) -> Пример: 12th of March",
        "uz": "Sana va vaqt (Dates & Time) -> Masalan: 12th of March"
    },
    "Purpose & Prepositions": {
        "en": "Purpose & Prepositions -> Example: for work, on holiday",
        "ru": "Цель и предлоги (Purpose & Prepositions) -> Пример: for work, on holiday",
        "uz": "Maqsad va predloglar (Purpose & Prepositions) -> Masalan: for work, on holiday"
    },
    "Numbers & Ages": {
        "en": "Numbers & Ages -> Example: 25, 26",
        "ru": "Числа и возраст (Numbers & Ages) -> Пример: 25, 26",
        "uz": "Sonlar va yosh (Numbers & Ages) -> Masalan: 25, 26"
    },
    "Clothing Vocabulary": {
        "en": "Clothing Vocabulary -> Example: jacket, jumper",
        "ru": "Одежда (Clothing) -> Пример: jacket, jumper",
        "uz": "Kiyimlar (Clothing) -> Masalan: jacket, jumper"
    },
    "Subject-Verb Agreement": {
        "en": "Subject-Verb Agreement -> Example: he/she needs",
        "ru": "Согласование подлежащего и сказуемого (Subject-Verb Agreement) -> Пример: he/she needs",
        "uz": "Ega va kesim mosligi (Subject-Verb Agreement) -> Masalan: he/she needs"
    },
    "Feelings & Adjectives": {
        "en": "Feelings & Adjectives -> Example: helpful, concerned",
        "ru": "Чувства и прилагательные (Feelings & Adjectives) -> Пример: helpful, concerned",
        "uz": "His-tuyg'ular va sifatlar (Feelings & Adjectives) -> Masalan: helpful, concerned"
    },
    "Prices & Currency": {
        "en": "Prices & Currency -> Example: £95.99",
        "ru": "Цены и валюта (Prices & Currency) -> Пример: £95.99",
        "uz": "Narxlar va valyuta (Prices & Currency) -> Masalan: £95.99"
    },
    "Adjectives & Vocabulary": {
        "en": "Adjectives & Vocabulary -> Example: bad, good",
        "ru": "Прилагательные и лексика (Adjectives) -> Пример: bad, good",
        "uz": "Sifatlar va lug'at (Adjectives) -> Masalan: bad, good"
    },
    "Verb 'To Be'": {
        "en": "Verb 'To Be' -> Example: is, isn't, are",
        "ru": "Глагол 'To Be' (Verb To Be) -> Пример: is, isn't, are",
        "uz": "\"To Be\" fe'li (Verb To Be) -> Masalan: is, isn't, are"
    },
    "Cause & Effect (Listening)": {
        "en": "Cause & Effect (Listening) -> Example: because she trusted him",
        "ru": "Причина и следствие (Cause & Effect) -> Пример: because she trusted him",
        "uz": "Sabab va oqibat (Cause & Effect) -> Masalan: because she trusted him"
    },
    "Inference & Reactions": {
        "en": "Inference & Reactions -> Example: She was amazed",
        "ru": "Умозаключение и реакции (Inference) -> Пример: She was amazed",
        "uz": "Xulosa va reaktsiyalar (Inference) -> Masalan: She was amazed"
    }
}

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

async def finish_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    score = context.user_data['quiz_score']
    total = len(QUIZ_QUESTIONS)
    level = get_level(score, total)
    user = update.effective_user
    chat_id = update.effective_chat.id
    lang = get_user_language(str(chat_id))
    
    weak_topics = context.user_data.get('weak_topics', [])
    
    if weak_topics:
        translated_topics = []
        for topic in weak_topics:
            topic_str = QUIZ_TOPICS.get(topic, {}).get(lang, QUIZ_TOPICS.get(topic, {}).get('en', topic))
            translated_topics.append(f"  - {topic_str}")
        weak_str = "\n".join(translated_topics)
    else:
        weak_str = get_ui_text('no_weak_topics', lang)
    
    result_text = get_ui_text('result', lang, score=score, total=total, level=level, weak_topics=weak_str)
    
    from telegram import ReplyKeyboardRemove
    await context.bot.send_message(
        chat_id=chat_id, 
        text=result_text, 
        parse_mode='HTML',
        reply_markup=ReplyKeyboardRemove()
    )
    
    # SAVE DATA TO SEND TO ADMIN LATER
    context.user_data['quiz_score'] = score
    context.user_data['quiz_total'] = total
    context.user_data['quiz_level'] = level
    context.user_data['quiz_weak_str'] = weak_str
    context.user_data[QUIZ_ACTIVE_KEY] = False
    context.user_data['awaiting_plan'] = True
    
    # SHOW PRICE LIST & PLAN BUTTONS
    from telegram import ReplyKeyboardMarkup, KeyboardButton
    keyboard = [
        [KeyboardButton(get_ui_text('plan_group', lang))],
        [KeyboardButton(get_ui_text('plan_mini_group', lang))],
        [KeyboardButton(get_ui_text('plan_individual', lang))]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    
    await context.bot.send_message(
        chat_id=chat_id,
        text=get_ui_text('price_list', lang),
        parse_mode='HTML',
        reply_markup=reply_markup
    )

async def send_final_report_and_finish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat_id = update.effective_chat.id
    lang = get_user_language(str(chat_id))
    
    score = context.user_data.get('quiz_score', 0)
    total = context.user_data.get('quiz_total', 0)
    level = context.user_data.get('quiz_level', 'N/A')
    weak_str = context.user_data.get('quiz_weak_str', 'N/A')
    selected_plan = context.user_data.get('selected_plan', 'N/A')
    phone = context.user_data.get('phone_number', None)
    
    # Build Admin Report
    admin_text = (
        f"🧠 <b>New Lead Took The Video Quiz!</b>\n\n"
        f"Name: {user.full_name}\n"
        f"Username: @{user.username if user.username else 'N/A'}\n"
        f"Telegram ID: <code>{chat_id}</code>\n"
    )
    if phone:
        admin_text += f"Phone: <code>{phone}</code>\n"
        
    admin_text += (
        f"\nScore: {score}/{total}\n"
        f"Level: <b>{level}</b>\n"
        f"Selected Plan: <b>{selected_plan}</b>\n"
        f"Weak Topics:\n{weak_str}"
    )
    
    # Send to single admin
    try:
        await context.bot.send_message(chat_id=Config.ADMIN_CHAT_ID, text=admin_text, parse_mode='HTML')
    except Exception as e:
        print(f"Failed to send quiz result to admin: {e}")
            
    # Restore menu for user
    from app.bot.keyboards import unregistered_menu_keyboard
    await context.bot.send_message(
        chat_id=chat_id, 
        text=get_ui_text('phone_received', lang), 
        parse_mode='HTML', 
        reply_markup=unregistered_menu_keyboard(lang)
    )
    context.user_data['awaiting_phone'] = False
    context.user_data['awaiting_plan'] = False
    
async def handle_unregistered_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Unified handler for all text messages during the quiz/lead-capture flow."""
    text = update.message.text
    chat_id = update.effective_chat.id
    lang = get_user_language(str(chat_id))
    user = update.effective_user
    
    # 1. Check if taking the quiz
    if context.user_data.get(QUIZ_ACTIVE_KEY, False):
        index = context.user_data['quiz_index']
        q_data = QUIZ_QUESTIONS[index]
        
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
        
    # 2. Check if awaiting plan selection
    if context.user_data.get('awaiting_plan', False):
        text_lower = text.lower()
        selected_plan = None
        if "standard" in text_lower or "стандарт" in text_lower:
            selected_plan = 'Standard'
        elif "comfort" in text_lower or "комфорт" in text_lower:
            selected_plan = 'Comfort'
        elif "ultima" in text_lower:
            selected_plan = 'Ultima'
            
        if not selected_plan:
            await update.message.reply_text("👇 Please select a plan from the buttons below:")
            raise ApplicationHandlerStop()
            
        context.user_data['awaiting_plan'] = False
        context.user_data['selected_plan'] = selected_plan
        
        if not user.username:
            context.user_data['awaiting_phone'] = True
            keyboard = [[KeyboardButton(get_ui_text('share_phone_btn', lang), request_contact=True)]]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
            
            await update.message.reply_text(
                get_ui_text('phone_request', lang),
                parse_mode='HTML',
                reply_markup=reply_markup
            )
        else:
            await send_final_report_and_finish(update, context)
            
        raise ApplicationHandlerStop()

    # 3. Check if awaiting phone number (via manual text input)
    if context.user_data.get('awaiting_phone', False):
        context.user_data['phone_number'] = text
        context.user_data['awaiting_phone'] = False
        await send_final_report_and_finish(update, context)
        raise ApplicationHandlerStop()

async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the user clicking the 'Share Phone Number' Telegram native button."""
    if not context.user_data.get('awaiting_phone', False):
        return
        
    phone_number = update.message.contact.phone_number
    context.user_data['phone_number'] = phone_number
    context.user_data['awaiting_phone'] = False
    await send_final_report_and_finish(update, context)
    raise ApplicationHandlerStop()

async def cancel_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get(QUIZ_ACTIVE_KEY, False) or context.user_data.get('awaiting_phone', False) or context.user_data.get('awaiting_plan', False):
        lang = get_user_language(str(update.effective_chat.id))
        from app.bot.keyboards import unregistered_menu_keyboard
        context.user_data[QUIZ_ACTIVE_KEY] = False
        context.user_data['awaiting_phone'] = False
        context.user_data['awaiting_plan'] = False
        await update.message.reply_text(get_ui_text('cancelled', lang), reply_markup=unregistered_menu_keyboard(lang))
        raise ApplicationHandlerStop()