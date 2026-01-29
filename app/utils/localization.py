# Supported languages
LANGUAGES = {
    'en': '🇬🇧 English',
    'ru': '🇷🇺 Русский',
    'uz': '🇺🇿 O\'zbekcha'
}

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
    # LESSON CHANGES
    # ═══════════════════════════════════════════════════════════
    'cancelled_lesson': {
        'en': 'Cancelled',
        'ru': 'Отменено',
        'uz': 'Bekor qilindi'
    },
    'moved_to': {
        'en': 'Moved to',
        'ru': 'Перенесено на',
        'uz': 'Ko\'chirildi'
    },
    'rescheduled_from': {
        'en': 'Rescheduled from',
        'ru': 'Перенесено с',
        'uz': 'dan ko\'chirildi'
    },
    'select_lesson': {
        'en': '📚 Select a lesson to change:',
        'ru': '📚 Выберите урок для изменения:',
        'uz': '📚 O\'zgartirish uchun darsni tanlang:'
    },
    'what_to_do': {
        'en': 'What do you want to do?',
        'ru': 'Что вы хотите сделать?',
        'uz': 'Nima qilmoqchisiz?'
    },
    'postpone': {
        'en': '📅 Postpone',
        'ru': '📅 Перенести',
        'uz': '📅 Ko\'chirish'
    },
    'cancel_lesson': {
        'en': '❌ Cancel Lesson',
        'ru': '❌ Отменить урок',
        'uz': '❌ Darsni bekor qilish'
    },
    'select_new_time': {
        'en': '📅 Select a new time:\n\nThese are your teacher\'s available slots:',
        'ru': '📅 Выберите новое время:\n\nДоступные слоты вашего учителя:',
        'uz': '📅 Yangi vaqtni tanlang:\n\nO\'qituvchingizning bo\'sh vaqtlari:'
    },
    'no_available_slots': {
        'en': '😕 No available slots\n\nYour teacher hasn\'t set any available times.\n\nPlease contact your teacher directly.',
        'ru': '😕 Нет доступных слотов\n\nВаш учитель не установил доступное время.\n\nСвяжитесь с учителем напрямую.',
        'uz': '😕 Bo\'sh vaqt yo\'q\n\nO\'qituvchingiz bo\'sh vaqtni belgilamagan.\n\nO\'qituvchingiz bilan bog\'laning.'
    },
    'confirm_cancel_lesson': {
        'en': '⚠️ Cancel lesson?\n\n📚 {title}\n📅 {date}\n\nThis will notify all participants.',
        'ru': '⚠️ Отменить урок?\n\n📚 {title}\n📅 {date}\n\nВсе участники будут уведомлены.',
        'uz': '⚠️ Darsni bekor qilasizmi?\n\n📚 {title}\n📅 {date}\n\nBarcha ishtirokchilar xabardor qilinadi.'
    },
    'confirm_reschedule': {
        'en': '📅 Confirm Reschedule\n\n📚 {title}\n\nFrom: {old_date}\nTo: {new_date} at {new_time}\n\nConfirm this change?',
        'ru': '📅 Подтвердите перенос\n\n📚 {title}\n\nС: {old_date}\nНа: {new_date} в {new_time}\n\nПодтвердить?',
        'uz': '📅 Ko\'chirishni tasdiqlang\n\n📚 {title}\n\nDan: {old_date}\nGa: {new_date} soat {new_time}\n\nTasdiqlaysizmi?'
    },
    'lesson_rescheduled': {
        'en': '✅ Lesson Rescheduled!\n\n📚 {title}\n\nFrom: {old_date}\nTo: {new_date} at {new_time}\n\nAll participants have been notified.',
        'ru': '✅ Урок перенесен!\n\n📚 {title}\n\nС: {old_date}\nНа: {new_date} в {new_time}\n\nВсе участники уведомлены.',
        'uz': '✅ Dars ko\'chirildi!\n\n📚 {title}\n\nDan: {old_date}\nGa: {new_date} soat {new_time}\n\nBarcha ishtirokchilar xabardor qilindi.'
    },
    'cancel_request_sent': {
        'en': '✅ Cancellation request sent!\n\nRequest ID: {request_id}\nWaiting for {count} approval(s).\n\nRequest expires at 23:59 today.',
        'ru': '✅ Запрос на отмену отправлен!\n\nID запроса: {request_id}\nОжидается {count} подтверждение(й).\n\nЗапрос истекает в 23:59 сегодня.',
        'uz': '✅ Bekor qilish so\'rovi yuborildi!\n\nSo\'rov ID: {request_id}\n{count} ta tasdiqlash kutilmoqda.\n\nSo\'rov bugun 23:59 da tugaydi.'
    },
    'no_lessons_to_change': {
        'en': '📭 No upcoming lessons to change.',
        'ru': '📭 Нет предстоящих уроков для изменения.',
        'uz': '📭 O\'zgartirish uchun darslar yo\'q.'
    },
    'cannot_change_lesson': {
        'en': '❌ Cannot change: {reason}',
        'ru': '❌ Невозможно изменить: {reason}',
        'uz': '❌ O\'zgartirib bo\'lmaydi: {reason}'
    },
    'too_late_to_change': {
        'en': 'Less than 2 hours before the lesson',
        'ru': 'Менее 2 часов до урока',
        'uz': 'Darsga 2 soatdan kam qoldi'
    },
    'no_teacher_found': {
        'en': '❌ Cannot find teacher for this lesson.\nPlease contact admin.',
        'ru': '❌ Учитель не найден для этого урока.\nСвяжитесь с админом.',
        'uz': '❌ Bu dars uchun o\'qituvchi topilmadi.\nAdmin bilan bog\'laning.'
    },
    
    # ═══════════════════════════════════════════════════════════
    # AVAILABILITY
    # ═══════════════════════════════════════════════════════════
    'set_availability': {
        'en': '📅 Set Your Availability\n\nSelect a day to set when you\'re FREE for rescheduled lessons:',
        'ru': '📅 Установите доступность\n\nВыберите день, когда вы СВОБОДНЫ для переносов:',
        'uz': '📅 Bo\'sh vaqtingizni belgilang\n\nKo\'chirilgan darslar uchun bo\'sh kunni tanlang:'
    },
    'current_availability': {
        'en': 'Current availability:',
        'ru': 'Текущая доступность:',
        'uz': 'Joriy bo\'sh vaqt:'
    },
    'select_day': {
        'en': 'Select a day:',
        'ru': 'Выберите день:',
        'uz': 'Kunni tanlang:'
    },
    'select_start_time': {
        'en': '⏰ Select START time (when you become available):',
        'ru': '⏰ Выберите НАЧАЛО (когда вы становитесь доступны):',
        'uz': '⏰ BOSHLANISH vaqtini tanlang (qachon bo\'sh bo\'lasiz):'
    },
    'select_end_time': {
        'en': '⏰ Select END time (when you stop being available):',
        'ru': '⏰ Выберите КОНЕЦ (когда вы перестаёте быть доступны):',
        'uz': '⏰ TUGASH vaqtini tanlang (qachon band bo\'lasiz):'
    },
    'availability_saved': {
        'en': '✅ Availability Saved!\n\n📅 {day}\n⏰ {start}:00 - {end}:00\n📊 {count} hour slot(s) available\n\nStudents can now reschedule lessons to these times.',
        'ru': '✅ Доступность сохранена!\n\n📅 {day}\n⏰ {start}:00 - {end}:00\n📊 {count} час(ов) доступно\n\nСтуденты могут переносить уроки на это время.',
        'uz': '✅ Bo\'sh vaqt saqlandi!\n\n📅 {day}\n⏰ {start}:00 - {end}:00\n📊 {count} soat mavjud\n\nO\'quvchilar endi darslarni shu vaqtga ko\'chirishlari mumkin.'
    },
    'no_availability_set': {
        'en': 'No availability set yet.',
        'ru': 'Свободное время не указано.',
        'uz': 'Bo\'sh vaqt hali belgilanmagan.'
    },
    'your_availability': {
        'en': '📋 Your Availability',
        'ru': '📋 Ваша доступность',
        'uz': '📋 Sizning bo\'sh vaqtingiz'
    },
    'view_schedule': {
        'en': '📋 View My Schedule',
        'ru': '📋 Мое расписание',
        'uz': '📋 Mening jadvalim'
    },
    'clear_all': {
        'en': '🗑 Clear All',
        'ru': '🗑 Очистить все',
        'uz': '🗑 Hammasini tozalash'
    },
    'add_more': {
        'en': '➕ Add More',
        'ru': '➕ Добавить ещё',
        'uz': '➕ Yana qo\'shish'
    },
    'all_cleared': {
        'en': '🗑 All availability cleared.\n\nUse /availability to set new times.',
        'ru': '🗑 Вся доступность очищена.\n\nИспользуйте /availability для новых настроек.',
        'uz': '🗑 Barcha bo\'sh vaqtlar tozalandi.\n\nYangi vaqtlar uchun /availability buyrug\'ini yuboring.'
    },
    'availability_closed': {
        'en': '👍 Availability menu closed.',
        'ru': '👍 Меню доступности закрыто.',
        'uz': '👍 Bo\'sh vaqt menyusi yopildi.'
    },
    
    # ═══════════════════════════════════════════════════════════
    # PAYMENT
    # ═══════════════════════════════════════════════════════════
    'select_course': {
        'en': '💰 Select course to pay for:',
        'ru': '💰 Выберите курс для оплаты:',
        'uz': '💰 To\'lov uchun kursni tanlang:'
    },
    'enter_amount': {
        'en': '💵 Enter payment amount:',
        'ru': '💵 Введите сумму оплаты:',
        'uz': '💵 To\'lov summasini kiriting:'
    },
    'upload_receipt': {
        'en': '📸 Please upload a photo of your payment receipt:',
        'ru': '📸 Загрузите фото чека оплаты:',
        'uz': '📸 To\'lov cheki rasmini yuklang:'
    },
    'payment_submitted': {
        'en': '✅ Payment submitted!\n\nCourse: {course}\nAmount: {amount}\n\nWaiting for admin confirmation.',
        'ru': '✅ Оплата отправлена!\n\nКурс: {course}\nСумма: {amount}\n\nОжидается подтверждение админа.',
        'uz': '✅ To\'lov yuborildi!\n\nKurs: {course}\nSumma: {amount}\n\nAdmin tasdig\'i kutilmoqda.'
    },
    'payment_confirmed': {
        'en': '✅ Your payment has been confirmed!',
        'ru': '✅ Ваш платёж подтверждён!',
        'uz': '✅ To\'lovingiz tasdiqlandi!'
    },
    'payment_rejected': {
        'en': '❌ Your payment was rejected. Please contact admin.',
        'ru': '❌ Ваш платёж отклонён. Свяжитесь с админом.',
        'uz': '❌ To\'lovingiz rad etildi. Admin bilan bog\'laning.'
    },
    'invalid_amount': {
        'en': '❌ Invalid amount. Please enter a number.',
        'ru': '❌ Неверная сумма. Введите число.',
        'uz': '❌ Noto\'g\'ri summa. Raqam kiriting.'
    },
    'no_courses': {
        'en': '📭 No courses found for you.',
        'ru': '📭 Курсы не найдены.',
        'uz': '📭 Sizda kurslar topilmadi.'
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
    'help_change': {
        'en': '/change - Postpone or cancel a lesson',
        'ru': '/change - Перенести или отменить урок',
        'uz': '/change - Darsni ko\'chirish yoki bekor qilish'
    },
    'help_pay': {
        'en': '/pay - Submit a payment',
        'ru': '/pay - Отправить оплату',
        'uz': '/pay - To\'lov yuborish'
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
    'help_availability': {
        'en': '/availability - Set free time (teachers)',
        'ru': '/availability - Указать свободное время (учителя)',
        'uz': '/availability - Bo\'sh vaqtni belgilash (o\'qituvchilar)'
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
    # PAYMENT (additional)
    # ═══════════════════════════════════════════════════════════
    'payment_title': {
        'en': 'Payment Submission',
        'ru': 'Отправка платежа',
        'uz': 'To\'lov yuborish'
    },
    'your_courses': {
        'en': 'Your Courses',
        'ru': 'Ваши курсы',
        'uz': 'Sizning kurslaringiz'
    },
    'course_price': {
        'en': 'Course Price',
        'ru': 'Цена курса',
        'uz': 'Kurs narxi'
    },
    'paid': {
        'en': 'Paid',
        'ru': 'Оплачено',
        'uz': 'To\'langan'
    },
    'remaining': {
        'en': 'Remaining',
        'ru': 'Остаток',
        'uz': 'Qoldiq'
    },
    'fully_paid': {
        'en': 'Fully Paid',
        'ru': 'Полностью оплачено',
        'uz': 'To\'liq to\'langan'
    },
    'course_already_paid': {
        'en': '✅ <b>{subject}</b> is already fully paid!\n\nUse /pay to select another course.',
        'ru': '✅ <b>{subject}</b> уже полностью оплачен!\n\nИспользуйте /pay для выбора другого курса.',
        'uz': '✅ <b>{subject}</b> allaqachon to\'liq to\'langan!\n\nBoshqa kurs tanlash uchun /pay yuboring.'
    },
    'already_paid': {
        'en': 'Already Paid',
        'ru': 'Уже оплачено',
        'uz': 'Allaqachon to\'langan'
    },
    'enter_amount_hint': {
        'en': 'Enter amount (e.g., 50 or {amount}):',
        'ru': 'Введите сумму (например, 50 или {amount}):',
        'uz': 'Summani kiriting (masalan, 50 yoki {amount}):'
    },
    'amount_must_be_positive': {
        'en': '❌ Amount must be greater than 0.\n\nPlease enter a valid amount:',
        'ru': '❌ Сумма должна быть больше 0.\n\nВведите корректную сумму:',
        'uz': '❌ Summa 0 dan katta bo\'lishi kerak.\n\nTo\'g\'ri summani kiriting:'
    },
    'overpaying_warning': {
        'en': '⚠️ You\'re paying <b>${amount:.2f}</b> but only <b>${remaining:.2f}</b> is remaining.\n\nThis is fine if intentional.',
        'ru': '⚠️ Вы платите <b>${amount:.2f}</b>, но остаток только <b>${remaining:.2f}</b>.\n\nЭто нормально, если так задумано.',
        'uz': '⚠️ Siz <b>${amount:.2f}</b> to\'layapsiz, lekin faqat <b>${remaining:.2f}</b> qolgan.\n\nAgar ataylab bo\'lsa, bu normal.'
    },
    'payment_amount': {
        'en': 'Payment Amount',
        'ru': 'Сумма платежа',
        'uz': 'To\'lov summasi'
    },
    'after_payment': {
        'en': 'After this payment',
        'ru': 'После этого платежа',
        'uz': 'Ushbu to\'lovdan keyin'
    },
    'total_paid': {
        'en': 'Total Paid',
        'ru': 'Всего оплачено',
        'uz': 'Jami to\'langan'
    },
    'please_send_photo': {
        'en': '❌ Please send a <b>photo</b> of your payment receipt.',
        'ru': '❌ Пожалуйста, отправьте <b>фото</b> чека оплаты.',
        'uz': '❌ Iltimos, to\'lov cheki <b>rasmini</b> yuboring.'
    },
    'payment_summary': {
        'en': 'Payment Summary',
        'ru': 'Итоги платежа',
        'uz': 'To\'lov xulosasi'
    },
    'course': {
        'en': 'Course',
        'ru': 'Курс',
        'uz': 'Kurs'
    },
    'teacher': {
        'en': 'Teacher',
        'ru': 'Учитель',
        'uz': 'O\'qituvchi'
    },
    'this_payment': {
        'en': 'This Payment',
        'ru': 'Этот платёж',
        'uz': 'Bu to\'lov'
    },
    'total_after': {
        'en': 'Total After',
        'ru': 'Итого после',
        'uz': 'Keyin jami'
    },
    'yes': {
        'en': 'Yes',
        'ru': 'Да',
        'uz': 'Ha'
    },
    'no': {
        'en': 'No',
        'ru': 'Нет',
        'uz': 'Yo\'q'
    },
    'submit_payment_question': {
        'en': 'Submit this payment?',
        'ru': 'Отправить этот платёж?',
        'uz': 'Bu to\'lovni yuborasizmi?'
    },
    'btn_submit': {
        'en': '✅ Submit',
        'ru': '✅ Отправить',
        'uz': '✅ Yuborish'
    },
    'payment_submitted': {
        'en': '✅ <b>Payment submitted!</b>\n\nYour payment is being reviewed.\nYou\'ll receive a notification once confirmed.',
        'ru': '✅ <b>Платёж отправлен!</b>\n\nВаш платёж на рассмотрении.\nВы получите уведомление после подтверждения.',
        'uz': '✅ <b>To\'lov yuborildi!</b>\n\nTo\'lovingiz ko\'rib chiqilmoqda.\nTasdiqlangandan keyin xabar olasiz.'
    },
    'congratulations_fully_paid': {
        'en': '🎉 <b>Course fully paid!</b> Thank you!',
        'ru': '🎉 <b>Курс полностью оплачен!</b> Спасибо!',
        'uz': '🎉 <b>Kurs to\'liq to\'landi!</b> Rahmat!'
    },
    'payment_confirmed_notification': {
        'en': '✅ <b>Payment Confirmed!</b>\n\n📚 Course: {subject}\n💰 Amount: ${amount:.2f}\n✅ Total Paid: ${total_paid:.2f}\n\n{status}',
        'ru': '✅ <b>Платёж подтверждён!</b>\n\n📚 Курс: {subject}\n💰 Сумма: ${amount:.2f}\n✅ Всего оплачено: ${total_paid:.2f}\n\n{status}',
        'uz': '✅ <b>To\'lov tasdiqlandi!</b>\n\n📚 Kurs: {subject}\n💰 Summa: ${amount:.2f}\n✅ Jami to\'langan: ${total_paid:.2f}\n\n{status}'
    },
    'payment_rejected_notification': {
        'en': '❌ <b>Payment Rejected</b>\n\nYour payment for <b>{subject}</b> was not approved.\n\nPlease contact your teacher.',
        'ru': '❌ <b>Платёж отклонён</b>\n\nВаш платёж за <b>{subject}</b> не был одобрен.\n\nСвяжитесь с учителем.',
        'uz': '❌ <b>To\'lov rad etildi</b>\n\n<b>{subject}</b> uchun to\'lovingiz tasdiqlanmadi.\n\nO\'qituvchingiz bilan bog\'laning.'
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
    'btn_change_lesson': {
        'en': '✏️ Change Lesson',
        'ru': '✏️ Изменить урок',
        'uz': '✏️ Darsni o\'zgartirish'
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
    # CHANGE LESSON (additional)
    # ═══════════════════════════════════════════════════════════
    'selected': {
        'en': 'Selected',
        'ru': 'Выбрано',
        'uz': 'Tanlandi'
    },
    'save_failed': {
        'en': '❌ Failed to save. Please try again.',
        'ru': '❌ Не удалось сохранить. Попробуйте снова.',
        'uz': '❌ Saqlab bo\'lmadi. Qayta urinib ko\'ring.'
    },
    'request_failed': {
        'en': '❌ Failed to create request.',
        'ru': '❌ Не удалось создать запрос.',
        'uz': '❌ So\'rov yaratib bo\'lmadi.'
    },
    'lesson_rescheduled_notification': {
        'en': '📅 <b>Lesson Rescheduled</b>\n\n📚 {title}\n👤 By: {by}\n\n<b>From:</b> {old_date}\n<b>To:</b> {new_date} at {new_time}',
        'ru': '📅 <b>Урок перенесён</b>\n\n📚 {title}\n👤 Кем: {by}\n\n<b>С:</b> {old_date}\n<b>На:</b> {new_date} в {new_time}',
        'uz': '📅 <b>Dars ko\'chirildi</b>\n\n📚 {title}\n👤 Kim: {by}\n\n<b>Dan:</b> {old_date}\n<b>Ga:</b> {new_date} soat {new_time}'
    },
    'cancel_approval_request': {
        'en': '📨 <b>Lesson Cancellation Request</b>\n\nFrom: {name} ({role})\nLesson: {title}\nDate: {date}\n\nDo you approve?',
        'ru': '📨 <b>Запрос на отмену урока</b>\n\nОт: {name} ({role})\nУрок: {title}\nДата: {date}\n\nВы одобряете?',
        'uz': '📨 <b>Darsni bekor qilish so\'rovi</b>\n\nKimdan: {name} ({role})\nDars: {title}\nSana: {date}\n\nTasdiqlaysizmi?'
    },
    'already_responded': {
        'en': '❌ You already responded to this request.',
        'ru': '❌ Вы уже ответили на этот запрос.',
        'uz': '❌ Siz allaqachon bu so\'rovga javob bergansiz.'
    },
    'request_approved': {
        'en': '✅ Request APPROVED!\n\nLesson has been {status}.',
        'ru': '✅ Запрос ОДОБРЕН!\n\nУрок был {status}.',
        'uz': '✅ So\'rov TASDIQLANDI!\n\nDars {status}.'
    },
    'request_rejected': {
        'en': '❌ Request rejected.',
        'ru': '❌ Запрос отклонён.',
        'uz': '❌ So\'rov rad etildi.'
    },
    'your_request_approved': {
        'en': '✅ Your request (ID: {request_id}) has been approved!',
        'ru': '✅ Ваш запрос (ID: {request_id}) был одобрен!',
        'uz': '✅ Sizning so\'rovingiz (ID: {request_id}) tasdiqlandi!'
    },
    'your_request_rejected': {
        'en': '❌ Your request (ID: {request_id}) was rejected.',
        'ru': '❌ Ваш запрос (ID: {request_id}) был отклонён.',
        'uz': '❌ Sizning so\'rovingiz (ID: {request_id}) rad etildi.'
    },
    'response_recorded': {
        'en': '✅ Your response recorded!\n\nWaiting for {remaining} more approval(s).',
        'ru': '✅ Ваш ответ записан!\n\nОжидается ещё {remaining} подтверждение(й).',
        'uz': '✅ Javobingiz qayd etildi!\n\nYana {remaining} ta tasdiqlash kutilmoqda.'
    },
        'btn_availability': {
        'en': '📅 Availability',
        'ru': '📅 Доступность',
        'uz': '📅 Bo\'sh vaqt'
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
        'group_vote_request': {
        'en': '🗳 <b>Group Vote</b>\n\n{name} wants to postpone <b>{title}</b>.\n\nFrom: {old_date}\nTo: {new_date} at {new_time}\n\nDo you agree? (If anyone votes NO, request is cancelled)',
        'ru': '🗳 <b>Голосование группы</b>\n\n{name} хочет перенести <b>{title}</b>.\n\nС: {old_date}\nНа: {new_date} в {new_time}\n\nВы согласны? (Если кто-то нажмет НЕТ, запрос отменится)',
        'uz': '🗳 <b>Guruh ovozi</b>\n\n{name} <b>{title}</b> darsini ko\'chirmoqchi.\n\nDan: {old_date}\nGa: {new_date} soat {new_time}\n\nRozimisiz? (Agar kimdir YO\'Q desa, so\'rov bekor qilinadi)'
    },
    'vote_started': {
        'en': '✅ <b>Vote Started!</b>\n\nWaiting for {count} other student(s) to agree.\nIf everyone agrees, the lesson will be moved.',
        'ru': '✅ <b>Голосование начато!</b>\n\nОжидаем согласия {count} других студентов.\nЕсли все согласятся, урок будет перенесен.',
        'uz': '✅ <b>Ovoz berish boshlandi!</b>\n\n{count} ta boshqa o\'quvchi roziligi kutilmoqda.\nAgar hamma rozi bo\'lsa, dars ko\'chiriladi.'
    },
    'teacher_vote_notification': {
        'en': 'ℹ️ Group <b>{group}</b> is voting to postpone <b>{title}</b>.\nYou will be notified if they all agree.',
        'ru': 'ℹ️ Группа <b>{group}</b> голосует за перенос <b>{title}</b>.\nВы получите уведомление, если все согласятся.',
        'uz': 'ℹ️ <b>{group}</b> guruhi <b>{title}</b> darsini ko\'chirish uchun ovoz bermoqda.\nAgar hamma rozi bo\'lsa, sizga xabar beriladi.'
    },
    'vote_rejected_notification': {
        'en': '❌ Postponement rejected by a group member.',
        'ru': '❌ Перенос отклонен участником группы.',
        'uz': '❌ Ko\'chirish guruh a\'zosi tomonidan rad etildi.'
    },
    # ═══════════════════════════════════════════════════════════
    # RESCHEDULE FLOW (New)
    # ═══════════════════════════════════════════════════════════
    'select_new_date': {
        'en': '📅 Select a new date:',
        'ru': '📅 Выберите новую дату:',
        'uz': '📅 Yangi sanani tanlang:'
    },
    'select_new_time_for_date': {
        'en': '⏰ Select time for <b>{date}</b>:',
        'ru': '⏰ Выберите время для <b>{date}</b>:',
        'uz': '⏰ <b>{date}</b> uchun vaqtni tanlang:'
    },
    'back_to_dates': {
        'en': '🔙 Back to Dates',
        'ru': '🔙 Назад к датам',
        'uz': '🔙 Sanalarga qaytish'
    },
}

def get_text(key: str, lang: str = 'en') -> str:
    """Get translated text by key."""
    if key not in TRANSLATIONS:
        return key  # Return key if translation not found
    
    translation = TRANSLATIONS[key]
    
    if lang in translation:
        return translation[lang]
    
    # Fallback to English
    return translation.get('en', key)


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
    
    return 'en'  # Default


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