import pytz
from datetime import datetime
from app.config import Config

# Supported languages
LANGUAGES = {
    'en': '🇬🇧 English',
    'ru': '🇷🇺 Русский',
    'uz': '🇺🇿 O\'zbekcha'
}

TRANSLATIONS = {
    # ═══════════════════════════════════════════════════════════
    # COMMON
    # ═══════════════════════════════════════════════════════════
    'welcome': {
        'en': 'Welcome to the Meeting Bot!',
        'ru': 'Добро пожаловать в бот!',
        'uz': 'Botga xush kelibsiz!'
    },
    'language_changed': {
        'en': '✅ Language changed to English',
        'ru': '✅ Язык изменен на Русский',
        'uz': '✅ Til O\'zbekchaga o\'zgartirildi'
    },
    'choose_language': {
        'en': '🌐 Choose your language:',
        'ru': '🌐 Выберите язык:',
        'uz': '🌐 Tilni tanlang:'
    },
    'cancelled': {
        'en': '❌ Action cancelled.',
        'ru': '❌ Действие отменено.',
        'uz': '❌ Amal bekor qilindi.'
    },
    'error_occurred': {
        'en': '😕 Oops! Something went wrong.',
        'ru': '😕 Упс! Что-то пошло не так.',
        'uz': '😕 Xatolik yuz berdi.'
    },
    'not_registered': {
        'en': "❌ You're not registered!\nUse /start to register first.",
        'ru': '❌ Вы не зарегистрированы!\nИспользуйте /start для регистрации.',
        'uz': '❌ Siz ro\'yxatdan o\'tmagansiz!\nRo\'yxatdan o\'tish uchun /start buyrug\'ini yuboring.'
    },
    'teachers_only': {
        'en': '⛔ This command is for teachers only.',
        'ru': '⛔ Эта команда только для учителей.',
        'uz': '⛔ Bu buyruq faqat o\'qituvchilar uchun.'
    },
    'students_only': {
        'en': '⛔ This command is for students only.',
        'ru': '⛔ Эта команда только для студентов.',
        'uz': '⛔ Bu buyruq faqat o\'quvchilar uchun.'
    },
    'admin_only': {
        'en': '⛔ This command is for admin only.',
        'ru': '⛔ Эта команда только для админа.',
        'uz': '⛔ Bu buyruq faqat admin uchun.'
    },
    
    # ═══════════════════════════════════════════════════════════
    # START / REGISTRATION
    # ═══════════════════════════════════════════════════════════
    'start_welcome': {
        'en': '👋 Welcome to the Meeting Bot!\n\nPlease enter your registration key:',
        'ru': '👋 Добро пожаловать!\n\nВведите ваш регистрационный ключ:',
        'uz': '👋 Xush kelibsiz!\n\nRo\'yxatdan o\'tish kalitini kiriting:'
    },
    'already_registered': {
        'en': '✅ You are already registered!',
        'ru': '✅ Вы уже зарегистрированы!',
        'uz': '✅ Siz allaqachon ro\'yxatdan o\'tgansiz!'
    },
    'registration_success': {
        'en': '✅ Registration successful!\n\nWelcome, {name}!\nRole: {role}',
        'ru': '✅ Регистрация успешна!\n\nДобро пожаловать, {name}!\nРоль: {role}',
        'uz': '✅ Ro\'yxatdan o\'tish muvaffaqiyatli!\n\nXush kelibsiz, {name}!\nRol: {role}'
    },
    'invalid_key': {
        'en': '❌ Invalid registration key. Please try again.',
        'ru': '❌ Неверный ключ регистрации. Попробуйте снова.',
        'uz': '❌ Noto\'g\'ri kalit. Qaytadan urinib ko\'ring.'
    },
    'key_already_used': {
        'en': '❌ This key has already been used.',
        'ru': '❌ Этот ключ уже использован.',
        'uz': '❌ Bu kalit allaqachon ishlatilgan.'
    },
    'role_teacher': {
        'en': 'Teacher',
        'ru': 'Учитель',
        'uz': 'O\'qituvchi'
    },
    'role_student': {
        'en': 'Student',
        'ru': 'Студент',
        'uz': 'O\'quvchi'
    },
    
    # ═══════════════════════════════════════════════════════════
    # SCHEDULE
    # ═══════════════════════════════════════════════════════════
    'your_schedule': {
        'en': 'Your Schedule',
        'ru': 'Ваше расписание',
        'uz': 'Sizning jadvalingiz'
    },
    'today_schedule': {
        'en': "Today's Schedule",
        'ru': 'Расписание на сегодня',
        'uz': 'Bugungi jadval'
    },
    'no_lessons': {
        'en': 'No lessons',
        'ru': 'Нет уроков',
        'uz': 'Darslar yo\'q'
    },
    'no_lessons_today': {
        'en': 'No lessons today!',
        'ru': 'Сегодня нет уроков!',
        'uz': 'Bugun darslar yo\'q!'
    },
    'week_of': {
        'en': 'Week of',
        'ru': 'Неделя',
        'uz': 'Hafta'
    },
    'today': {
        'en': 'TODAY',
        'ru': 'СЕГОДНЯ',
        'uz': 'BUGUN'
    },
    
    # ═══════════════════════════════════════════════════════════
    # STATUS
    # ═══════════════════════════════════════════════════════════
    'your_status': {
        'en': '📋 Your Status',
        'ru': '📋 Ваш статус',
        'uz': '📋 Sizning holatngiz'
    },
    'status_name': {
        'en': 'Name',
        'ru': 'Имя',
        'uz': 'Ism'
    },
    'status_role': {
        'en': 'Role',
        'ru': 'Роль',
        'uz': 'Rol'
    },
    'status_group': {
        'en': 'Group',
        'ru': 'Группа',
        'uz': 'Guruh'
    },
    'status_registered': {
        'en': 'Registered',
        'ru': 'Зарегистрирован',
        'uz': 'Ro\'yxatdan o\'tgan'
    },
    
    # ═══════════════════════════════════════════════════════════
    # HELP
    # ═══════════════════════════════════════════════════════════
    'help_title': {
        'en': '❓ Help - Available Commands',
        'ru': '❓ Помощь - Доступные команды',
        'uz': '❓ Yordam - Mavjud buyruqlar'
    },
    'help_schedule': {
        'en': '/schedule - View weekly schedule',
        'ru': '/schedule - Расписание на неделю',
        'uz': '/schedule - Haftalik jadval'
    },
    'help_today': {
        'en': '/today - View today\'s lessons',
        'ru': '/today - Сегодняшние уроки',
        'uz': '/today - Bugungi darslar'
    },
    'help_status': {
        'en': '/status - View your profile',
        'ru': '/status - Ваш профиль',
        'uz': '/status - Sizning profilingiz'
    },
    'help_language': {
        'en': '/language - Change language',
        'ru': '/language - Сменить язык',
        'uz': '/language - Tilni o\'zgartirish'
    },
    
    # ═══════════════════════════════════════════════════════════
    # DAY NAMES
    # ═══════════════════════════════════════════════════════════
    'monday': {'en': 'Monday', 'ru': 'Понедельник', 'uz': 'Dushanba'},
    'tuesday': {'en': 'Tuesday', 'ru': 'Вторник', 'uz': 'Seshanba'},
    'wednesday': {'en': 'Wednesday', 'ru': 'Среда', 'uz': 'Chorshanba'},
    'thursday': {'en': 'Thursday', 'ru': 'Четверг', 'uz': 'Payshanba'},
    'friday': {'en': 'Friday', 'ru': 'Пятница', 'uz': 'Juma'},
    'saturday': {'en': 'Saturday', 'ru': 'Суббота', 'uz': 'Shanba'},
    'sunday': {'en': 'Sunday', 'ru': 'Воскресенье', 'uz': 'Yakshanba'},
    
    # ═══════════════════════════════════════════════════════════
    # MONTH NAMES
    # ═══════════════════════════════════════════════════════════
    'january': {'en': 'January', 'ru': 'Январь', 'uz': 'Yanvar'},
    'february': {'en': 'February', 'ru': 'Февраль', 'uz': 'Fevral'},
    'march': {'en': 'March', 'ru': 'Март', 'uz': 'Mart'},
    'april': {'en': 'April', 'ru': 'Апрель', 'uz': 'Aprel'},
    'may': {'en': 'May', 'ru': 'Май', 'uz': 'May'},
    'june': {'en': 'June', 'ru': 'Июнь', 'uz': 'Iyun'},
    'july': {'en': 'July', 'ru': 'Июль', 'uz': 'Iyul'},
    'august': {'en': 'August', 'ru': 'Август', 'uz': 'Avgust'},
    'september': {'en': 'September', 'ru': 'Сентябрь', 'uz': 'Sentyabr'},
    'october': {'en': 'October', 'ru': 'Октябрь', 'uz': 'Oktyabr'},
    'november': {'en': 'November', 'ru': 'Ноябрь', 'uz': 'Noyabr'},
    'december': {'en': 'December', 'ru': 'Декабрь', 'uz': 'Dekabr'},
    
    # ═══════════════════════════════════════════════════════════
    # BUTTONS / NAVIGATION
    # ═══════════════════════════════════════════════════════════
    'prev_week': {'en': '⬅️ Previous Week', 'ru': '⬅️ Прошлая неделя', 'uz': '⬅️ Oldingi hafta'},
    'next_week': {'en': 'Next Week ➡️', 'ru': 'Следующая неделя ➡️', 'uz': 'Keyingi hafta ➡️'},
    'this_week': {'en': '📍 This Week', 'ru': '📍 Эта неделя', 'uz': '📍 Shu hafta'},
    'today_only': {'en': '📅 Today Only', 'ru': '📅 Только сегодня', 'uz': '📅 Faqat bugun'},
    'btn_back': {'en': '◀️ Back', 'ru': '◀️ Назад', 'uz': '◀️ Orqaga'},
    'btn_cancel': {'en': '🔙 Cancel', 'ru': '🔙 Отмена', 'uz': '🔙 Bekor qilish'},
    'btn_confirm': {'en': '✅ Confirm', 'ru': '✅ Подтвердить', 'uz': '✅ Tasdiqlash'},
    'btn_close': {'en': '❌ Close', 'ru': '❌ Закрыть', 'uz': '❌ Yopish'},
    'btn_yes': {'en': '✅ Yes', 'ru': '✅ Да', 'uz': '✅ Ha'},
    'btn_no': {'en': '❌ No', 'ru': '❌ Нет', 'uz': '❌ Yo\'q'},
    
        # ═══════════════════════════════════════════════════════════
    # REGISTRATION (additional)
    # ═══════════════════════════════════════════════════════════
    'admin_welcome': {
        'en': '👋 <b>Welcome, Admin!</b>\n\nUse the menu below to navigate.',
        'ru': '👋 <b>Добро пожаловать, Админ!</b>\n\nИспользуйте меню ниже.',
        'uz': '👋 <b>Xush kelibsiz, Admin!</b>\n\nQuyidagi menyudan foydalaning.'
    },
    'start_welcome': {
        'en': '👋 <b>Welcome to Meeting Bot!</b>\n\nPlease enter your <b>registration key</b>:\n\n<i>Format: STU-XXXXXX or TCH-XXXXXX</i>\n\nDon\'t have a key? Contact your administrator.',
        'ru': '👋 <b>Добро пожаловать в Meeting Bot!</b>\n\nВведите ваш <b>регистрационный ключ</b>:\n\n<i>Формат: STU-XXXXXX или TCH-XXXXXX</i>\n\nНет ключа? Свяжитесь с администратором.',
        'uz': '👋 <b>Meeting Bot ga xush kelibsiz!</b>\n\n<b>Ro\'yxatdan o\'tish kalitini</b> kiriting:\n\n<i>Format: STU-XXXXXX yoki TCH-XXXXXX</i>\n\nKalit yo\'qmi? Administrator bilan bog\'laning.'
    },
    'registration_cancelled': {
        'en': '❌ Registration cancelled.\n\nUse /start to try again.',
        'ru': '❌ Регистрация отменена.\n\nИспользуйте /start для повтора.',
        'uz': '❌ Ro\'yxatdan o\'tish bekor qilindi.\n\nQayta urinish uchun /start yuboring.'
    },
    'invalid_key_format': {
        'en': '❌ Invalid key format.\n\nKeys look like: <code>STU-ABC123</code> or <code>TCH-XYZ789</code>\n\nPlease try again or /cancel:',
        'ru': '❌ Неверный формат ключа.\n\nКлючи выглядят так: <code>STU-ABC123</code> или <code>TCH-XYZ789</code>\n\nПопробуйте снова или /cancel:',
        'uz': '❌ Kalit formati noto\'g\'ri.\n\nKalitlar shunday ko\'rinadi: <code>STU-ABC123</code> yoki <code>TCH-XYZ789</code>\n\nQayta urinib ko\'ring yoki /cancel:'
    },
    'registration_success': {
        'en': '✅ <b>Registration Successful!</b>\n\n{icon} Welcome, <b>{name}</b>!\nRole: {role}{group}\n\nUse the menu below to navigate.',
        'ru': '✅ <b>Регистрация успешна!</b>\n\n{icon} Добро пожаловать, <b>{name}</b>!\nРоль: {role}{group}\n\nИспользуйте меню ниже.',
        'uz': '✅ <b>Ro\'yxatdan o\'tish muvaffaqiyatli!</b>\n\n{icon} Xush kelibsiz, <b>{name}</b>!\nRol: {role}{group}\n\nQuyidagi menyudan foydalaning.'
    },
    
    # ═══════════════════════════════════════════════════════════
    # MENU BUTTONS
    # ═══════════════════════════════════════════════════════════
    'btn_schedule': {
        'en': '📅 Schedule',
        'ru': '📅 Расписание',
        'uz': '📅 Jadval'
    },
    'btn_today': {
        'en': '📅 Today',
        'ru': '📅 Сегодня',
        'uz': '📅 Bugun'
    },
    'btn_pay': {
        'en': '💰 Pay',
        'ru': '💰 Оплата',
        'uz': '💰 To\'lov'
    },
    'btn_status': {
        'en': '📋 Status',
        'ru': '📋 Статус',
        'uz': '📋 Holat'
    },
    'btn_help': {
        'en': '❓ Help',
        'ru': '❓ Помощь',
        'uz': '❓ Yordam'
    },
    'btn_new_student': {
        'en': '👤 New Student',
        'ru': '👤 Новый ученик',
        'uz': '👤 Yangi o\'quvchi'
    },
    'btn_new_teacher': {
        'en': '👤 New Teacher',
        'ru': '👤 Новый учитель',
        'uz': '👤 Yangi o\'qituvchi'
    },
    'btn_users': {
        'en': '👥 Users',
        'ru': '👥 Пользователи',
        'uz': '👥 Foydalanuvchilar'
    },
    'btn_language': {
        'en': '🌐 Language',
        'ru': '🌐 Язык',
        'uz': '🌐 Til'
    },
    'btn_approve': {
        'en': '✅ Approve',
        'ru': '✅ Одобрить',
        'uz': '✅ Tasdiqlash'
    },
    'btn_reject': {
        'en': '❌ Reject',
        'ru': '❌ Отклонить',
        'uz': '❌ Rad etish'
    },
    'btn_submit': {
        'en': '✅ Submit',
        'ru': '✅ Отправить',
        'uz': '✅ Yuborish'
    },
    'remove': {
        'en': 'Remove',
        'ru': 'Удалить',
        'uz': 'O\'chirish'
    },
    # ═══════════════════════════════════════════════════════════
    # HOMEWORK
    # ═══════════════════════════════════════════════════════════
    'btn_homework': {
        'en': '📚 Homework',
        'ru': '📚 Домашнее задание',
        'uz': '📚 Uy vazifasi'
    },
    'homework_start': {
        'en': '📚 <b>Homework Distribution</b>\n\nSend me the homework files (documents, photos, videos, etc.).\n\nYou can send multiple files.\n\nWhen done, tap the button below:',
        'ru': '📚 <b>Отправка домашнего задания</b>\n\nОтправьте мне файлы домашнего задания (документы, фото, видео и т.д.).\n\nМожно отправить несколько файлов.\n\nКогда закончите, нажмите кнопку ниже:',
        'uz': '📚 <b>Uy vazifasini yuborish</b>\n\nMenga uy vazifasi fayllarini yuboring (hujjatlar, rasmlar, videolar va h.k.).\n\nBir nechta fayl yuborishingiz mumkin.\n\nTugagach, quyidagi tugmani bosing:'
    },
    'done_uploading': {
        'en': '✅ Done uploading',
        'ru': '✅ Загрузка завершена',
        'uz': '✅ Yuklash tugadi'
    },
    'file_received': {
        'en': '✅ File received! ({count} total)\n\nSend more or tap "Done uploading".',
        'ru': '✅ Файл получен! (всего {count})\n\nОтправьте ещё или нажмите "Загрузка завершена".',
        'uz': '✅ Fayl qabul qilindi! (jami {count})\n\nYana yuboring yoki "Yuklash tugadi" tugmasini bosing.'
    },
    'no_files_uploaded': {
        'en': '⚠️ No files received. Please send at least one file.',
        'ru': '⚠️ Файлы не получены. Отправьте хотя бы один файл.',
        'uz': '⚠️ Fayllar olinmadi. Kamida bitta fayl yuboring.'
    },
    'session_expired': {
        'en': '⏰ Session expired. Please start again with /homework',
        'ru': '⏰ Сессия истекла. Начните заново с /homework',
        'uz': '⏰ Sessiya tugadi. /homework bilan qaytadan boshlang'
    },
    'no_groups_assigned': {
        'en': '⚠️ You have no groups assigned. Please contact admin.',
        'ru': '⚠️ У вас нет назначенных групп. Свяжитесь с админом.',
        'uz': '⚠️ Sizga guruhlar biriktirilmagan. Admin bilan bog\'laning.'
    },
    'select_group_for_homework': {
        'en': '📁 <b>{count} file(s) ready</b>\n\nSelect which group should receive this homework:',
        'ru': '📁 <b>{count} файл(ов) готово</b>\n\nВыберите группу для отправки:',
        'uz': '📁 <b>{count} ta fayl tayyor</b>\n\nQaysi guruhga yuborishni tanlang:'
    },
    'no_students_in_group': {
        'en': '⚠️ No students found in group "{group}".',
        'ru': '⚠️ В группе "{group}" нет студентов.',
        'uz': '⚠️ "{group}" guruhida o\'quvchilar topilmadi.'
    },
    'confirm_homework_send': {
        'en': '📤 <b>Ready to send homework</b>\n\n📁 Files: {file_count}\n👥 Recipients: {student_count} students\n📚 Group: {group}\n\nProceed?',
        'ru': '📤 <b>Готово к отправке</b>\n\n📁 Файлов: {file_count}\n👥 Получателей: {student_count} студентов\n📚 Группа: {group}\n\nПродолжить?',
        'uz': '📤 <b>Yuborishga tayyor</b>\n\n📁 Fayllar: {file_count}\n👥 Qabul qiluvchilar: {student_count} o\'quvchi\n📚 Guruh: {group}\n\nDavom etasizmi?'
    },
    'btn_send_now': {
        'en': '📤 Send Now',
        'ru': '📤 Отправить',
        'uz': '📤 Yuborish'
    },
    'sending': {
        'en': 'Sending...',
        'ru': 'Отправляется...',
        'uz': 'Yuborilmoqda...'
    },
    'homework_received': {
        'en': '📚 <b>New Homework</b>\n\nYou have received new homework materials:',
        'ru': '📚 <b>Новое домашнее задание</b>\n\nВы получили новые материалы:',
        'uz': '📚 <b>Yangi uy vazifasi</b>\n\nSiz yangi uy vazifasi materiallarini oldingiz:'
    },
    'homework_sent_success': {
        'en': '✅ <b>Homework Sent!</b>\n\n📤 Successfully sent to {sent} students.',
        'ru': '✅ <b>Домашнее задание отправлено!</b>\n\n📤 Успешно отправлено {sent} студентам.',
        'uz': '✅ <b>Uy vazifasi yuborildi!</b>\n\n📤 {sent} ta o\'quvchiga muvaffaqiyatli yuborildi.'
    },
    'homework_sent_partial': {
        'en': '✅ <b>Homework Sent!</b>\n\n📤 Sent to: {sent} students\n⚠️ Failed: {failed} students',
        'ru': '✅ <b>Домашнее задание отправлено!</b>\n\n📤 Отправлено: {sent} студентам\n⚠️ Ошибка: {failed} студентов',
        'uz': '✅ <b>Uy vazifasi yuborildi!</b>\n\n📤 Yuborildi: {sent} o\'quvchiga\n⚠️ Xato: {failed} o\'quvchi'
    },

    'welcome_message':{
        'en': "👋 Welcome to Demy Academy bot!\n\n"
              "Who are you?\n"
              "• 👨‍🎓 Student\n"
              "• 👨‍🏫 Teacher\n\n"
              "To start using the bot, please enter your registration key.\n"
              "Format: STU-XXXXXX or TCH-XXXXXX\n\n"
              "If you don't have a key yet, ask your teacher or administrator.",
        'ru': "👋 Добро пожаловать в бот Demy Academy!\n\n"
              "Кто вы?\n"
              "• 👨‍🎓 Студент\n"
              "• 👨‍🏫 Учитель\n\n"
              "Чтобы начать, введите ваш ключ регистрации.\n"
              "Формат: STU-XXXXXX или TCH-XXXXXX\n\n"
              "Если у вас нет ключа, обратитесь к администратору.",
        'uz': "👋 Demy Academy botiga xush kelibsiz!\n\n"
              "Siz kimsiz?\n"
              "• 👨‍🎓 Talaba\n"
              "• 👨‍🏫 O'qituvchi\n\n"
              "Boshlash uchun ro'yxatdan o'tish kalitini kiriting.\n"
              "Format: STU-XXXXXX yoki TCH-XXXXXX\n\n"
              "Agar kalitingiz bo'lmasa, administratorga murojaat qiling."
    },
    
    'menu_open': {
        'en': "⬇️ Menu",
        'ru': "⬇️ Меню",
        'uz': "⬇️ Menyu"
    },
    
    'status_teaching_groups':{
        'en': "Teaching Groups",
        'ru': "Преподаваемые группы",
        'uz': "O'qitiladigan guruhlar"
    },
    
    'lesson_alert_title':{
        'en': "🎥 <b>Lesson Time!</b>",
        'ru': "🎥 <b>Время Урока!</b>",
        'uz': "🎥 <b>Dars Vaqti!</b>"
    },
    
    'lesson_details':{
        'en': "📌 <b>Title:</b> {title}\n"
              "⏰ <b>Time:</b> {time}\n"
              "👥 <b>Group:</b> {group}\n"
              "📝 <b>Description:</b> {desc}\n"
              "📚 <b>Subject:</b> {subject}\n"
              "👨‍🏫 <b>Teacher:</b> {teacher}",
        'ru': "📌 <b>Название:</b> {title}\n"
              "⏰ <b>Время:</b> {time}\n"
              "👥 <b>Группа:</b> {group}\n"
              "📝 <b>Описание:</b> {desc}\n"
              "📚 <b>Предмет:</b> {subject}\n"
              "👨‍🏫 <b>Учитель:</b> {teacher}",
        'uz': "📌 <b>Mavzu:</b> {title}\n"
            "⏰ <b>Vaqt:</b> {time}\n"
            "👥 <b>Guruh:</b> {group}\n"
            "📝 <b>Tavsif:</b> {desc}\n"
            "📚 <b>Fan:</b> {subject}\n"
            "👨‍🏫 <b>O‘qituvchi:</b> {teacher}"
    },
    
    'lesson_join':{
        'en': "🔗 <b>Join here:</b>\n{link}",
        'ru': "🔗 <b>Ссылка для входа:</b>\n{link}",
        'uz': "🔗 <b>Kirish uchun havola:</b>\n{link}"
    },
    
    'lesson_click_hint':{
        'en': "👆 <i>Click the link to join!</i>",
        'ru': "👆 <i>Нажмите на ссылку, чтобы войти!</i>",
        'uz': "👆 <i>Kirish uchun havolani bosing!</i>"
    },
}

def get_text(key: str, lang: str = 'en') -> str:
    """Get translated text by key."""
    # SAFETY FIX: If lang is None, force 'en'
    if lang is None:
        lang = 'en'
        
    if key not in TRANSLATIONS:
        return key
    
    translation = TRANSLATIONS[key]
    
    if lang in translation:
        return translation[lang]
    
    return translation.get('en', key)

def get_now():
    """Get current time in the configured Timezone."""
    tz = pytz.timezone(Config.TIMEZONE)
    return datetime.now(tz)

def get_user_language(chat_id: str) -> str:
    """Get user's language preference from database."""
    from app.database.db import get_connection
    
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT language FROM users WHERE chat_id = ? AND is_active = 1", (str(chat_id),))
    row = cursor.fetchone()
    conn.close()
    
    if row and row['language']:
        return row['language']
    
    return 'en'


def set_user_language(chat_id: str, language: str) -> bool:
    """Set user's language preference."""
    from app.database.db import get_connection
    
    if language not in LANGUAGES:
        return False
    
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("UPDATE users SET language = ? WHERE chat_id = ?", (language, str(chat_id)))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error setting language: {e}")
        return False
    finally:
        conn.close()
        
def t(chat_id: str, key: str) -> str:
    """Shortcut: get translated text for a user."""
    lang = get_user_language(chat_id)
    return get_text(key, lang)

def get_day_name(day_name_en: str, lang: str) -> str:
    """Translate English day name to user's language."""
    key = day_name_en.lower()
    return get_text(key, lang)


def get_month_name(month_name_en: str, lang: str) -> str:
    """Translate English month name to user's language."""
    key = month_name_en.lower()
    return get_text(key, lang)


def format_date_localized(date_obj, lang: str, format_type: str = 'short') -> str:
    """
    Format date with translated month/day names.
    
    format_type:
        'short': "Jan 26"
        'full': "Monday, Jan 26"
        'month_day': "January 26"
    """
    day_name_en = date_obj.strftime("%A")  # Monday
    month_name_en = date_obj.strftime("%B")  # January
    day_num = date_obj.strftime("%d").lstrip('0')  # 26
    
    day_name = get_day_name(day_name_en, lang)
    month_name = get_month_name(month_name_en, lang)
    month_short = month_name[:3]  # Янв, Jan, Yan
    
    if format_type == 'short':
        return f"{month_short} {day_num}"
    elif format_type == 'full':
        return f"{day_name}, {month_short} {day_num}"
    elif format_type == 'month_day':
        return f"{month_name} {day_num}"
    
    return f"{month_short} {day_num}"