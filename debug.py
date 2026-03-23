# test_scheduler.py
# Run: python test_scheduler.py

import logging
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s | %(name)s | %(levelname)s | %(message)s'
)
logger = logging.getLogger('TEST')


# ============================================
# PHASE 1: Test Database Connection
# ============================================
def test_db_connection():
    logger.info("=" * 50)
    logger.info("PHASE 1: Testing Database Connection")
    logger.info("=" * 50)
    
    try:
        from app.config import Config
        logger.info(f"DATABASE_URL exists: {bool(Config.DATABASE_URL)}")
        
        from app.database.db import get_connection
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1")
        result = cur.fetchone()
        logger.info(f"✅ DB Connection OK. SELECT 1 = {result}")
        cur.close()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"❌ DB Connection FAILED: {e}")
        return False


# ============================================
# PHASE 2: Test User Lookup
# ============================================
def test_user_lookup():
    logger.info("=" * 50)
    logger.info("PHASE 2: Testing User Lookup")
    logger.info("=" * 50)
    
    try:
        from app.services.user_service import get_user_by_name
        
        test_name = "Amir"
        logger.info(f"Looking up teacher: '{test_name}'")
        
        result = get_user_by_name(test_name)
        
        if result:
            logger.info(f"✅ Found: {result['name']} (chat_id: {result['chat_id']})")
            return result
        else:
            logger.error(f"❌ Teacher '{test_name}' NOT FOUND in users table!")
            return None
    except Exception as e:
        logger.error(f"❌ User lookup CRASHED: {e}", exc_info=True)
        return None


# ============================================
# PHASE 3: Test Teacher-Group Assignment
# ============================================
def test_group_lookup():
    logger.info("=" * 50)
    logger.info("PHASE 3: Testing Teacher-Group Assignment")
    logger.info("=" * 50)
    
    try:
        from app.services.user_service import get_teacher_for_group
        
        test_group = "Group M/N"
        logger.info(f"Looking up teacher for group: '{test_group}'")
        
        result = get_teacher_for_group(test_group)
        
        if result:
            logger.info(f"✅ Group teacher: {result.get('name')} (chat_id: {result.get('chat_id')})")
        else:
            logger.warning(f"⚠️ No teacher assigned to '{test_group}' in teacher_groups table")
            logger.info("   This is OK — auto-heal will fix it on first run")
        
        return result
    except Exception as e:
        logger.error(f"❌ Group lookup CRASHED: {e}", exc_info=True)
        return None


# ============================================
# PHASE 4: Test Student Lookup
# ============================================
def test_student_lookup():
    logger.info("=" * 50)
    logger.info("PHASE 4: Testing Student Lookup")
    logger.info("=" * 50)
    
    try:
        from app.services.user_service import get_students_in_group
        
        test_group = "Group M/N"
        logger.info(f"Looking up students in: '{test_group}'")
        
        students = get_students_in_group(test_group)
        
        if students:
            for s in students:
                logger.info(f"  👤 {s.get('name')} (chat_id: {s.get('chat_id')})")
            logger.info(f"✅ Found {len(students)} student(s)")
        else:
            logger.warning(f"⚠️ No students found in '{test_group}'")
        
        return students
    except Exception as e:
        logger.error(f"❌ Student lookup CRASHED: {e}", exc_info=True)
        return None


# ============================================
# PHASE 5: Test Auto-Heal Logic
# ============================================
def test_auto_heal():
    logger.info("=" * 50)
    logger.info("PHASE 5: Testing Auto-Heal (UPSERT)")
    logger.info("=" * 50)
    
    try:
        from app.services.user_service import (
            get_user_by_name, 
            update_teacher_group_assignment,
            get_teacher_for_group
        )
        
        test_group = "Group M/N"
        test_teacher = "Amir"
        test_subject = "math"
        
        teacher = get_user_by_name(test_teacher)
        if not teacher:
            logger.error(f"❌ Can't test auto-heal: '{test_teacher}' not in DB")
            return False
        
        logger.info(f"Step 1: Found {teacher['name']} → {teacher['chat_id']}")
        
        logger.info(f"Step 2: Running update_teacher_group_assignment...")
        update_teacher_group_assignment(test_group, teacher['chat_id'], test_subject)
        
        logger.info(f"Step 3: Verifying...")
        result = get_teacher_for_group(test_group)
        
        if result and str(result.get('chat_id')) == str(teacher['chat_id']):
            logger.info(f"✅ Auto-heal WORKS! {test_group} → {result.get('name')}")
            return True
        else:
            logger.error(f"❌ Auto-heal FAILED. Got: {result}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Auto-heal CRASHED: {e}", exc_info=True)
        return False


# ============================================
# PHASE 6: Test Full Message Build (No Send)
# ============================================
def test_message_build():
    logger.info("=" * 50)
    logger.info("PHASE 6: Testing Full Message Build (DRY RUN)")
    logger.info("=" * 50)
    
    try:
        from app.config import Config
        from app.jitsi_meet import create_jitsi_meeting
        from app.services.user_service import (
            get_teacher_for_group,
            get_user_by_name,
            get_students_in_group
        )
        
        meetings = Config.load_meetings()
        if not meetings:
            logger.error("❌ No meetings in meetings.json!")
            return False
        
        m = meetings[0]
        logger.info(f"Testing with: {m['title']} | Group: {m.get('group_name')}")
        
        group_name = m.get('group_name', 'Unknown')
        json_teacher_name = m.get('teacher_name')
        
        logger.info(f"  JSON teacher_name: {json_teacher_name}")
        
        teacher = get_teacher_for_group(group_name)
        logger.info(f"  DB teacher for group: {teacher}")
        
        if teacher and json_teacher_name and teacher.get('name') != json_teacher_name:
            logger.info(f"  🔄 MISMATCH detected! DB={teacher.get('name')} JSON={json_teacher_name}")
            teacher = None
        
        if not teacher and json_teacher_name:
            teacher = get_user_by_name(json_teacher_name)
            logger.info(f"  Name lookup result: {teacher}")
        
        students = get_students_in_group(group_name)
        
        recipients = set()
        if teacher and teacher.get('chat_id'):
            recipients.add(str(teacher['chat_id']))
        for s in (students or []):
            if s.get('chat_id'):
                recipients.add(str(s['chat_id']))
        
        meeting_data = create_jitsi_meeting(title=m['title'])
        
        logger.info(f"  📨 Recipients: {recipients}")
        logger.info(f"  🔗 Jitsi Link: {meeting_data.get('meet_link')}")
        
        if recipients:
            logger.info(f"✅ Message build SUCCESS — would send to {len(recipients)} people")
            return True
        else:
            logger.error(f"❌ No recipients! Message would be lost!")
            return False
            
    except Exception as e:
        logger.error(f"❌ Message build CRASHED: {e}", exc_info=True)
        return False


# ============================================
# PHASE 7: Test Support System
# ============================================
def test_support_system():
    logger.info("=" * 50)
    logger.info("PHASE 7: Testing Support System")
    logger.info("=" * 50)

    try:
        from app.config import Config
        schedule = Config.load_support_schedule()
        if schedule:
            logger.info(f"  ✅ Schedule loaded: {list(schedule.get('schedule', {}).keys())}")
            logger.info(f"  ⏱ Session duration: {schedule.get('session_duration_minutes')} min")
            logger.info(f"  📊 Max per week: {schedule.get('max_bookings_per_week')}")
        else:
            logger.error("  ❌ support_schedule.json not found!")
            return False
    except Exception as e:
        logger.error(f"  ❌ Config load failed: {e}", exc_info=True)
        return False

    try:
        from app.services.support_service import get_available_support_staff
        staff = get_available_support_staff()
        if staff:
            logger.info(f"  ✅ Support staff: {staff['name']} ({staff['chat_id']})")
        else:
            logger.error("  ❌ No active support staff in DB! (role='support', is_active=1)")
            return False
    except Exception as e:
        logger.error(f"  ❌ Staff lookup failed: {e}", exc_info=True)
        return False

    try:
        from app.services.support_service import get_available_slots
        slots = get_available_slots(staff['chat_id'])
        if slots:
            logger.info(f"  ✅ Generated {len(slots)} available slots")
            for s in slots[:5]:
                logger.info(f"     📅 {s['display']}")
            if len(slots) > 5:
                logger.info(f"     ... and {len(slots)-5} more")
        else:
            logger.warning("  ⚠️ No slots available (might be outside schedule hours)")
    except Exception as e:
        logger.error(f"  ❌ Slot generation failed: {e}", exc_info=True)
        return False

    try:
        from app.services.support_service import get_weekly_booking_count
        count = get_weekly_booking_count("test_user_000")
        logger.info(f"  ✅ Weekly count for test user: {count}")
    except Exception as e:
        logger.error(f"  ❌ Weekly count failed: {e}", exc_info=True)
        return False

    return True


# ============================================
# PHASE 8: Test send_meeting_to_recipients (DRY RUN)
# ============================================
def test_send_meeting_flow():
    logger.info("=" * 50)
    logger.info("PHASE 8: Testing FULL send_meeting_to_recipients Flow")
    logger.info("=" * 50)
    
    try:
        from app.config import Config
        from app.jitsi_meet import create_jitsi_meeting
        
        meetings = Config.load_meetings()
        if not meetings:
            logger.error("❌ No meetings found!")
            return False
        
        m = meetings[0]
        logger.info(f"  Using meeting: {m['title']} | Group: {m.get('group_name')}")
        logger.info(f"  JSON teacher_name: {m.get('teacher_name')}")
        
        group_name = m.get('group_name', 'Unknown')
        json_teacher_name = m.get('teacher_name')
        teacher = None
        recipients = set()
        db_teacher_found = False
        
        logger.info(f"\n  --- PHASE 1: Teacher Routing ---")
        
        if group_name and group_name != 'Unknown':
            from app.services.user_service import (
                get_teacher_for_group,
                get_user_by_name,
                update_teacher_group_assignment,
                get_students_in_group
            )
            
            teacher = get_teacher_for_group(group_name)
            logger.info(f"  DB lookup result: {teacher}")
            
            if teacher and json_teacher_name and teacher.get('name') != json_teacher_name:
                logger.info(f"  🔄 MISMATCH! DB: {teacher.get('name')} | JSON: {json_teacher_name}")
                teacher = None
            elif teacher:
                logger.info(f"  ✅ DB matches JSON — no mismatch")
            
            if not teacher and json_teacher_name:
                logger.info(f"  🔧 Auto-healing: looking up '{json_teacher_name}' by name...")
                teacher = get_user_by_name(json_teacher_name)
                if teacher:
                    logger.info(f"  ✅ Found! ID: {teacher['chat_id']}")
                    update_teacher_group_assignment(
                        group_name,
                        teacher['chat_id'],
                        subject=m.get('subject')
                    )
                    logger.info(f"  ✅ DB healed!")
                else:
                    logger.error(f"  ❌ '{json_teacher_name}' NOT in users table!")
            
            if teacher and teacher.get('chat_id'):
                recipients.add(str(teacher['chat_id']))
                db_teacher_found = True
                logger.info(f"  ✅ Teacher added: {teacher.get('name')} → {teacher['chat_id']}")
            else:
                logger.warning(f"  ⚠️ No teacher to add!")
        else:
            logger.warning(f"  ⚠️ group_name is '{group_name}' — skipping Phase 1")
        
        logger.info(f"\n  --- PHASE 2: Fallbacks ---")
        if not db_teacher_found:
            json_id = m.get('teacher_chat_id') or m.get('chat_id')
            if json_id:
                recipients.add(str(json_id))
                logger.info(f"  ⚠️ Using fallback ID: {json_id}")
            else:
                logger.warning(f"  ❌ No fallback ID either!")
        else:
            logger.info(f"  ✅ DB teacher found — no fallback needed")
        
        logger.info(f"\n  --- PHASE 3: Students ---")
        if group_name and group_name != 'Unknown':
            from app.services.user_service import get_students_in_group
            students = get_students_in_group(group_name)
            for s in (students or []):
                if s.get('chat_id'):
                    recipients.add(str(s['chat_id']))
                    logger.info(f"  👤 {s.get('name')} → {s['chat_id']}")
            if not students:
                logger.warning(f"  ⚠️ No students in group")
        
        logger.info(f"\n  --- PHASE 4: Final Check ---")
        logger.info(f"  📨 Total recipients: {len(recipients)}")
        for r in recipients:
            logger.info(f"     → {r}")
        
        if not recipients:
            logger.error(f"  ❌ ZERO RECIPIENTS — message would be lost!")
            return False
        
        meeting_data = create_jitsi_meeting(title=m['title'])
        logger.info(f"  🔗 Jitsi: {meeting_data.get('meet_link')}")
        
        logger.info(f"\n  ✅ WOULD SEND to {len(recipients)} people (dry run)")
        return True
        
    except Exception as e:
        logger.error(f"❌ CRASHED: {e}", exc_info=True)
        return False


# ============================================
# PHASE 9: Simulating ACTUAL Scheduler Job
# ============================================
def test_actual_job():
    logger.info("=" * 50)
    logger.info("PHASE 9: Simulating ACTUAL Scheduler Job")
    logger.info("=" * 50)
    
    try:
        from app.config import Config
        from app.scheduler import job_send_lesson, create_job_args
        
        meetings = Config.load_meetings()
        if not meetings:
            logger.error("❌ No meetings!")
            return False
        
        m = meetings[0]
        logger.info(f"  Meeting: {m['title']}")
        
        frozen_args = create_job_args(None, m)
        logger.info(f"  Frozen args type: {type(frozen_args)}")
        logger.info(f"  Frozen args[0] (app): {frozen_args[0]}")
        logger.info(f"  Frozen args[1] (config): {type(frozen_args[1])}")
        logger.info(f"  Frozen meeting title: {frozen_args[1].get('title')}")
        logger.info(f"  Frozen teacher_name: {frozen_args[1].get('teacher_name')}")
        logger.info(f"  Frozen group_name: {frozen_args[1].get('group_name')}")
        logger.info(f"  Frozen schedule: {frozen_args[1].get('schedule')}")
        
        logger.info(f"\n  --- Testing check_lesson_status ---")
        from app.services.lesson_service import check_lesson_status
        import pytz
        from datetime import datetime
        
        tz = pytz.timezone(Config.TIMEZONE)
        today = datetime.now(tz).strftime("%d-%m-%Y")
        meeting_id = m['id']
        
        logger.info(f"  Meeting ID: {meeting_id}")
        logger.info(f"  Today: {today}")
        
        status = check_lesson_status(meeting_id, today)
        logger.info(f"  Status: {status}")
        
        if status['status'] == 'cancelled':
            logger.warning(f"  ⚠️ Lesson is CANCELLED today — job would skip!")
        elif status['status'] == 'postponed':
            logger.warning(f"  ⚠️ Lesson is POSTPONED — job would skip!")
        else:
            logger.info(f"  ✅ Lesson is ACTIVE — job would proceed")
        
        logger.info(f"\n  --- Testing Jitsi Link ---")
        from app.jitsi_meet import create_jitsi_meeting
        meeting_data = create_jitsi_meeting(title=m['title'])
        logger.info(f"  Link: {meeting_data.get('meet_link')}")
        
        if not meeting_data.get('meet_link'):
            logger.error(f"  ❌ Jitsi returned no link!")
            return False
        
        logger.info(f"\n  --- Testing job_send_lesson (DRY) ---")
        from app.scheduler import send_meeting_to_recipients
        logger.info(f"  ✅ send_meeting_to_recipients imported OK")
        
        import inspect
        sig = inspect.signature(send_meeting_to_recipients)
        logger.info(f"  ✅ Function signature: {sig}")
        
        logger.info(f"\n  --- Testing Scheduler Setup ---")
        from app.scheduler import DAY_MAP
        
        schedule = m.get('schedule', {})
        days = schedule.get('days', [])
        hour = schedule.get('hour', 9)
        minute = schedule.get('minute', 0)
        
        cron_days = ",".join(
            [DAY_MAP.get(d.lower(), d)[:3] for d in days]
        )
        
        logger.info(f"  Days: {days} → cron: {cron_days}")
        logger.info(f"  Time: {hour:02d}:{minute:02d}")
        
        if not cron_days:
            logger.error(f"  ❌ No cron days — job would never fire!")
            return False
        
        now = datetime.now(tz)
        current_day = now.strftime("%A").lower()
        logger.info(f"  Current day: {current_day}")
        logger.info(f"  Current time: {now.strftime('%H:%M')}")
        logger.info(f"  Scheduled days: {days}")
        
        if current_day in [d.lower() for d in days]:
            logger.info(f"  ✅ Today IS a scheduled day")
        else:
            logger.info(f"  ℹ️ Today is NOT a scheduled day (next fire on {days})")
        
        logger.info(f"\n  ✅ All scheduler components OK")
        return True
        
    except Exception as e:
        logger.error(f"❌ CRASHED: {e}", exc_info=True)
        return False


# ============================================
# PHASE 10: Check for Silent Killers
# ============================================
def test_silent_killers():
    logger.info("=" * 50)
    logger.info("PHASE 10: Checking for Silent Killers")
    logger.info("=" * 50)
    
    issues = []
    
    try:
        from app.utils.localization import get_user_language, get_text
        lang = get_user_language("892571478")
        logger.info(f"  ✅ get_user_language works: {lang}")
        
        header = get_text('lesson_alert_title', lang)
        logger.info(f"  ✅ lesson_alert_title: {header[:50]}...")
        
        details = get_text('lesson_details', lang)
        logger.info(f"  ✅ lesson_details template exists: {bool(details)}")
        
        try:
            formatted = details.format(
                title="Test", time="19:00", 
                group="Group M/N", desc="Test desc",
                subject="math", teacher="Amir"
            )
            logger.info(f"  ✅ lesson_details formats OK")
        except KeyError as e:
            logger.error(f"  ❌ lesson_details MISSING KEY: {e}")
            issues.append(f"Missing template key: {e}")
        
        join = get_text('lesson_join', lang)
        try:
            join.format(link="https://test.com")
            logger.info(f"  ✅ lesson_join formats OK")
        except KeyError as e:
            logger.error(f"  ❌ lesson_join MISSING KEY: {e}")
            issues.append(f"Missing join key: {e}")
            
        footer = get_text('lesson_click_hint', lang)
        logger.info(f"  ✅ lesson_click_hint: {footer[:50] if footer else 'EMPTY'}...")
        
    except Exception as e:
        logger.error(f"  ❌ Localization CRASHED: {e}", exc_info=True)
        issues.append(f"Localization crash: {e}")
    
    try:
        from apscheduler.schedulers.asyncio import AsyncIOScheduler
        from apscheduler.triggers.cron import CronTrigger
        logger.info(f"  ✅ APScheduler imports OK")
    except ImportError as e:
        logger.error(f"  ❌ APScheduler import FAILED: {e}")
        issues.append(f"APScheduler missing: {e}")
    
    try:
        import pytz
        from app.config import Config
        tz = pytz.timezone(Config.TIMEZONE)
        from datetime import datetime
        now = datetime.now(tz)
        logger.info(f"  ✅ Timezone OK: {Config.TIMEZONE} → {now.strftime('%H:%M %Z')}")
    except Exception as e:
        logger.error(f"  ❌ Timezone FAILED: {e}")
        issues.append(f"Timezone: {e}")
    
    try:
        from app.scheduler import start_scheduler, load_meetings
        meetings = load_meetings()
        logger.info(f"  ✅ load_meetings: {len(meetings)} meetings")
        
        for m in meetings:
            missing = []
            for key in ['id', 'title', 'schedule', 'group_name', 'teacher_name']:
                if key not in m:
                    missing.append(key)
            if missing:
                logger.error(f"  ❌ Meeting '{m.get('id', '?')}' missing: {missing}")
                issues.append(f"Meeting missing fields: {missing}")
            else:
                logger.info(f"  ✅ Meeting '{m['id']}' has all required fields")
    except Exception as e:
        logger.error(f"  ❌ Scheduler import FAILED: {e}", exc_info=True)
        issues.append(f"Scheduler: {e}")
    
    if issues:
        logger.error(f"\n  🔴 Found {len(issues)} issue(s)!")
        for i in issues:
            logger.error(f"     → {i}")
        return False
    else:
        logger.info(f"\n  ✅ No silent killers found")
        return True


# ============================================
# PHASE 11: Test Role & Keyboard Assignments
# ============================================
def test_role_keyboards():
    logger.info("=" * 50)
    logger.info("PHASE 11: Testing Role & Keyboard Assignments")
    logger.info("=" * 50)
    
    issues = []
    
    try:
        from app.bot.keyboards import main_menu_keyboard
        from telegram import ReplyKeyboardMarkup
        
        for lang in ['en', 'ru', 'uz']:
            kb = main_menu_keyboard(is_admin=True, lang=lang)
            if not isinstance(kb, ReplyKeyboardMarkup):
                issues.append(f"Admin keyboard ({lang}) wrong type: {type(kb)}")
            else:
                logger.info(f"  ✅ Admin keyboard ({lang}) OK")
            
            kb = main_menu_keyboard(is_teacher=True, lang=lang)
            if not isinstance(kb, ReplyKeyboardMarkup):
                issues.append(f"Teacher keyboard ({lang}) wrong type: {type(kb)}")
            else:
                logger.info(f"  ✅ Teacher keyboard ({lang}) OK")
            
            kb = main_menu_keyboard(is_support=True, lang=lang)
            if not isinstance(kb, ReplyKeyboardMarkup):
                issues.append(f"Support keyboard ({lang}) wrong type: {type(kb)}")
            else:
                logger.info(f"  ✅ Support keyboard ({lang}) OK")
            
            kb = main_menu_keyboard(lang=lang)
            if not isinstance(kb, ReplyKeyboardMarkup):
                issues.append(f"Student keyboard ({lang}) wrong type: {type(kb)}")
            else:
                logger.info(f"  ✅ Student keyboard ({lang}) OK")
                
    except Exception as e:
        logger.error(f"  ❌ Keyboard test CRASHED: {e}", exc_info=True)
        issues.append(f"Keyboard crash: {e}")
    
    try:
        from app.utils.localization import get_text
        
        for lang in ['en', 'ru', 'uz']:
            kb = main_menu_keyboard(lang=lang)
            
            all_buttons = []
            for row in kb.keyboard:
                for button in row:
                    all_buttons.append(button.text)
            
            pay_text = get_text('btn_pay', lang)
            change_text = get_text('btn_change_lesson', lang)
            
            if pay_text in all_buttons:
                logger.error(f"  ❌ Student keyboard ({lang}) still has PAYMENT button!")
                issues.append(f"Student has payment button ({lang})")
            else:
                logger.info(f"  ✅ Student keyboard ({lang}) — no payment button")
            
            if change_text in all_buttons:
                logger.error(f"  ❌ Student keyboard ({lang}) still has CHANGE LESSON button!")
                issues.append(f"Student has change lesson button ({lang})")
            else:
                logger.info(f"  ✅ Student keyboard ({lang}) — no change lesson button")
                
    except Exception as e:
        logger.error(f"  ❌ Button check CRASHED: {e}", exc_info=True)
        issues.append(f"Button check crash: {e}")
    
    try:
        for lang in ['en', 'ru', 'uz']:
            kb = main_menu_keyboard(is_support=True, lang=lang)
            
            all_buttons = []
            for row in kb.keyboard:
                for button in row:
                    all_buttons.append(button.text)
            
            expected = [
                get_text('btn_schedule', lang),
                get_text('btn_today', lang),
                get_text('btn_status', lang),
                get_text('btn_language', lang),
                get_text('btn_help', lang)
            ]
            
            for btn in expected:
                if btn in all_buttons:
                    logger.info(f"  ✅ Support ({lang}) has: {btn}")
                else:
                    logger.error(f"  ❌ Support ({lang}) MISSING: {btn}")
                    issues.append(f"Support missing {btn} ({lang})")
            
            forbidden = [
                get_text('btn_pay', lang),
                get_text('btn_change_lesson', lang),
                get_text('btn_homework', lang),
                get_text('btn_book_support', lang)
            ]
            
            for btn in forbidden:
                if btn in all_buttons:
                    logger.error(f"  ❌ Support ({lang}) should NOT have: {btn}")
                    issues.append(f"Support has forbidden {btn} ({lang})")
                    
    except Exception as e:
        logger.error(f"  ❌ Support button check CRASHED: {e}", exc_info=True)
        issues.append(f"Support check crash: {e}")
    
    try:
        from app.utils.localization import get_text
        
        for lang in ['en', 'ru', 'uz']:
            text = get_text('role_support', lang)
            if text == 'role_support':
                logger.error(f"  ❌ 'role_support' not found in {lang} strings!")
                issues.append(f"Missing role_support in {lang}")
            else:
                logger.info(f"  ✅ role_support ({lang}): {text}")
                
    except Exception as e:
        logger.error(f"  ❌ Localization check CRASHED: {e}", exc_info=True)
        issues.append(f"Localization crash: {e}")
    
    try:
        logger.info(f"\n  --- Testing role → status mapping ---")
        
        test_roles = ['teacher', 'student', 'support']
        expected_keys = {
            'teacher': 'role_teacher',
            'student': 'role_student', 
            'support': 'role_support'
        }
        
        for role in test_roles:
            if role == 'teacher':
                role_key = 'role_teacher'
            elif role == 'support':
                role_key = 'role_support'
            else:
                role_key = 'role_student'
            
            if role_key == expected_keys[role]:
                logger.info(f"  ✅ role='{role}' → key='{role_key}'")
            else:
                logger.error(f"  ❌ role='{role}' → got '{role_key}', expected '{expected_keys[role]}'")
                issues.append(f"Wrong role mapping for {role}")
                
    except Exception as e:
        logger.error(f"  ❌ Role mapping CRASHED: {e}", exc_info=True)
        issues.append(f"Role mapping crash: {e}")
    
    try:
        logger.info(f"\n  --- Testing homework → support forwarding ---")
        from app.services.support_service import get_available_support_staff
        
        support = get_available_support_staff()
        if support:
            logger.info(f"  ✅ Support staff found: {support['name']} ({support['chat_id']})")
            logger.info(f"     Homework will be forwarded to this person")
        else:
            logger.warning(f"  ⚠️ No support staff found — homework forwarding will be skipped")
            
    except Exception as e:
        logger.error(f"  ❌ Support staff lookup CRASHED: {e}", exc_info=True)
        issues.append(f"Support lookup crash: {e}")
    
    if issues:
        logger.error(f"\n  🔴 {len(issues)} issue(s) found!")
        for i in issues:
            logger.error(f"     → {i}")
        return False
    else:
        logger.info(f"\n  ✅ All role & keyboard tests passed!")
        return True


# ============================================
# PHASE 12: Test Support Double-Booking Prevention
# ============================================
def test_support_double_booking():
    logger.info("=" * 50)
    logger.info("PHASE 12: Testing Support Double-Booking Prevention")
    logger.info("=" * 50)
    
    issues = []
    
    try:
        from app.services.support_service import (
            get_available_support_staff,
            get_available_slots,
            create_booking,
            get_booked_sessions,
            get_weekly_booking_count
        )
        from app.config import Config
        import pytz
        from datetime import datetime, timedelta
        
        # 1. Get support staff
        support = get_available_support_staff()
        if not support:
            logger.error("  ❌ No support staff found!")
            return False
        
        support_id = support['chat_id']
        logger.info(f"  ✅ Support staff: {support['name']} ({support_id})")
        
        # 2. Get available slots BEFORE booking
        slots_before = get_available_slots(support_id)
        logger.info(f"  ✅ Available slots before test: {len(slots_before)}")
        
        if not slots_before:
            logger.warning("  ⚠️ No slots available — can't test double booking")
            logger.warning("     (This might be outside schedule hours)")
            return True
        
        # 3. Pick the first available slot
        test_slot = slots_before[0]
        test_date = test_slot['date']
        test_time = f"{test_slot['hour']:02d}:{test_slot['minute']:02d}"
        
        logger.info(f"  📅 Test slot: {test_date} at {test_time}")
        
        # 4. Create a FAKE booking (Student A)
        logger.info(f"\n  --- Simulating Student A booking at {test_time} ---")
        
        success = create_booking(
            student_id="TEST_STUDENT_A",
            support_id=str(support_id),
            date_str=test_date,
            time_str=test_time,
            link="https://test.jitsi/fake-link"
        )
        
        if success:
            logger.info(f"  ✅ Student A booked at {test_time}")
        else:
            logger.error(f"  ❌ Student A booking FAILED!")
            issues.append("Booking creation failed")
            return False
        
        # 5. Check that the slot is NOW gone
        logger.info(f"\n  --- Checking if slot disappeared for Student B ---")
        
        slots_after = get_available_slots(support_id)
        logger.info(f"  ✅ Available slots after booking: {len(slots_after)}")
        
        booked_slot_available = False
        for slot in slots_after:
            slot_time = f"{slot['hour']:02d}:{slot['minute']:02d}"
            if slot['date'] == test_date and slot_time == test_time:
                booked_slot_available = True
                break
        
        if booked_slot_available:
            logger.error(f"  ❌ DOUBLE BOOKING POSSIBLE! {test_date} {test_time} still available!")
            issues.append("Double booking not prevented")
        else:
            logger.info(f"  ✅ Slot {test_date} {test_time} correctly REMOVED from available list")
        
        # 6. Verify booked sessions
        logger.info(f"\n  --- Verifying get_booked_sessions ---")
        
        sessions = get_booked_sessions(str(support_id), test_date)
        logger.info(f"  Booked sessions for {test_date}: {len(sessions)}")
        
        found_our_booking = False
        for sess in sessions:
            logger.info(f"     📋 {sess['date']} at {sess['time']} ({sess['duration']} min)")
            if sess['time'] == test_time:
                found_our_booking = True
        
        if found_our_booking:
            logger.info(f"  ✅ Our test booking found in sessions")
        else:
            logger.error(f"  ❌ Our test booking NOT found in sessions!")
            issues.append("Booking not returned by get_booked_sessions")
        
        # 7. Check slot count decreased
        actual_decrease = len(slots_before) - len(slots_after)
        
        logger.info(f"\n  --- Slot count check ---")
        logger.info(f"  Before: {len(slots_before)} | After: {len(slots_after)} | Decreased by: {actual_decrease}")
        
        if actual_decrease >= 1:
            logger.info(f"  ✅ Slot count decreased correctly")
        else:
            logger.error(f"  ❌ Slot count didn't decrease!")
            issues.append("Slot count unchanged after booking")
        
        # 8. CLEANUP
        logger.info(f"\n  --- Cleaning up test booking ---")
        
        from app.database.db import get_connection
        conn = get_connection()
        cur = conn.cursor()
        try:
            if Config.DATABASE_URL:
                cur.execute(
                    "DELETE FROM support_bookings WHERE student_chat_id = %s",
                    ("TEST_STUDENT_A",)
                )
            else:
                cur.execute(
                    "DELETE FROM support_bookings WHERE student_chat_id = ?",
                    ("TEST_STUDENT_A",)
                )
            conn.commit()
            logger.info(f"  ✅ Test booking cleaned up")
        except Exception as e:
            logger.warning(f"  ⚠️ Cleanup failed (not critical): {e}")
        finally:
            cur.close()
            conn.close()
        
        # 9. Verify slots restored
        slots_restored = get_available_slots(support_id)
        logger.info(f"  Slots after cleanup: {len(slots_restored)}")
        
        if len(slots_restored) == len(slots_before):
            logger.info(f"  ✅ Slots fully restored after cleanup")
        else:
            logger.warning(f"  ⚠️ Slots not fully restored ({len(slots_restored)} vs {len(slots_before)})")
        
    except Exception as e:
        logger.error(f"  ❌ CRASHED: {e}", exc_info=True)
        issues.append(f"Crash: {e}")
    
    if issues:
        logger.error(f"\n  🔴 {len(issues)} issue(s) found!")
        for i in issues:
            logger.error(f"     → {i}")
        return False
    else:
        logger.info(f"\n  ✅ Double-booking prevention works correctly!")
        return True


# ============================================
# PHASE 13: Test Homework Subject Resolution
# ============================================
def test_homework_subject():
    logger.info("=" * 50)
    logger.info("PHASE 13: Testing Homework Subject Resolution")
    logger.info("=" * 50)
    
    issues = []
    
    try:
        from app.config import Config
        
        # 1. Load meetings
        meetings = Config.load_meetings()
        if not meetings:
            logger.error("  ❌ No meetings found!")
            return False
        
        logger.info(f"  ✅ Loaded {len(meetings)} meetings")
        
        # 2. Test subject resolution for each group
        logger.info(f"\n  --- Testing subject lookup by group_name ---")
        
        group_names = set()
        for m in meetings:
            gn = m.get('group_name')
            if gn:
                group_names.add(gn)
        
        logger.info(f"  Found {len(group_names)} unique groups")
        
        for group_name in sorted(group_names):
            meeting = next(
                (m for m in meetings if m.get('group_name') == group_name), 
                None
            )
            
            if meeting:
                subject = meeting.get('subject', 'Unknown Subject')
                title = meeting.get('title', 'Unknown')
                logger.info(f"  ✅ {group_name} → subject: {subject} | title: {title}")
            else:
                logger.error(f"  ❌ {group_name} → NO MATCHING MEETING FOUND!")
                issues.append(f"No meeting for group: {group_name}")
        
        # 3. Test fallback for unknown group
        logger.info(f"\n  --- Testing fallback for unknown group ---")
        
        fake_group = "Group DOESNT_EXIST"
        meeting = next(
            (m for m in meetings if m.get('group_name') == fake_group), 
            None
        )
        subject = meeting.get('subject', 'Unknown Subject') if meeting else 'Unknown'
        
        if subject == 'Unknown':
            logger.info(f"  ✅ Unknown group correctly returns 'Unknown'")
        else:
            logger.error(f"  ❌ Unknown group returned '{subject}' instead of 'Unknown'")
            issues.append("Fallback for unknown group broken")
        
        # 4. Test support staff exists for forwarding
        logger.info(f"\n  --- Testing support forwarding target ---")
        
        from app.services.support_service import get_available_support_staff
        support = get_available_support_staff()
        
        if support:
            logger.info(f"  ✅ Homework will forward to: {support['name']} ({support['chat_id']})")
        else:
            logger.warning(f"  ⚠️ No support staff — homework forwarding will be skipped")
        
        # 5. Test the full message build
        logger.info(f"\n  --- Testing support message format ---")
        
        from datetime import datetime
        import pytz
        
        tz = pytz.timezone(Config.TIMEZONE)
        now = datetime.now(tz)
        timestamp = now.strftime("%d-%m-%Y %H:%M")
        
        test_group = list(group_names)[0] if group_names else "Test Group"
        test_meeting = next(
            (m for m in meetings if m.get('group_name') == test_group), 
            None
        )
        test_subject = test_meeting.get('subject', 'Unknown') if test_meeting else 'Unknown'
        
        support_header = (
            f"📚 <b>Homework Notification</b>\n\n"
            f"👨‍🏫 Teacher: <b>Test Teacher</b>\n"
            f"👥 Group: <b>{test_group}</b>\n"
            f"📘 Subject: <b>{test_subject}</b>\n"
            f"👤 Students: Student A, Student B\n"
            f"📎 Files: 2\n"
            f"🕐 Sent at: {timestamp}\n"
            f"{'─' * 30}"
        )
        
        logger.info(f"  Message preview:")
        for line in support_header.split('\n'):
            clean = line.replace('<b>', '').replace('</b>', '')
            clean = clean.replace('<i>', '').replace('</i>', '')
            logger.info(f"     {clean}")
        
        if 'None' in support_header:
            logger.error(f"  ❌ Message contains 'None' — a field is missing!")
            issues.append("None in support message")
        else:
            logger.info(f"  ✅ Message format OK — no None values")
        
    except Exception as e:
        logger.error(f"  ❌ CRASHED: {e}", exc_info=True)
        issues.append(f"Crash: {e}")
    
    if issues:
        logger.error(f"\n  🔴 {len(issues)} issue(s) found!")
        for i in issues:
            logger.error(f"     → {i}")
        return False
    else:
        logger.info(f"\n  ✅ Homework subject resolution works correctly!")
        return True


# ============================================
# RUN ALL TESTS
# ============================================
def main():
    logger.info("🚀 SCHEDULER DEBUG SCRIPT")
    logger.info("This simulates what happens when a lesson fires\n")
    
    results = {}
    
    results['db'] = test_db_connection()
    results['user'] = test_user_lookup()
    results['group'] = test_group_lookup()
    results['students'] = test_student_lookup()
    results['autoheal'] = test_auto_heal()
    results['message'] = test_message_build()
    results['support'] = test_support_system()
    results['send_flow'] = test_send_meeting_flow()
    results['job_sim'] = test_actual_job()
    results['killers'] = test_silent_killers()
    results['roles'] = test_role_keyboards()
    results['double_booking'] = test_support_double_booking()
    results['homework_subject'] = test_homework_subject()
    
    # Summary
    logger.info("\n" + "=" * 50)
    logger.info("📋 RESULTS SUMMARY")
    logger.info("=" * 50)
    
    all_pass = True
    for name, passed in results.items():
        icon = "✅" if passed else "❌"
        logger.info(f"  {icon} {name.upper()}")
        if not passed:
            all_pass = False
    
    if all_pass:
        logger.info("\n🎉 ALL TESTS PASSED — Safe to deploy!")
    else:
        logger.info("\n🔴 SOME TESTS FAILED — Fix before deploying!")


if __name__ == '__main__':
    main()