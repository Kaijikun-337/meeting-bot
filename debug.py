# debug.py
import os
import sys
import logging

# ── CRITICAL: Load .env FIRST before any app imports ──
# This ensures DATABASE_URL is set before get_connection() is called
from dotenv import load_dotenv
load_dotenv()

# ── Force debug to always use the REAL database (Neon/Postgres) ──
# Never use local SQLite for debugging — your data is in Neon
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("❌ FATAL: DATABASE_URL not found in .env!")
    print("   Debug requires connection to Neon (real data).")
    print("   Make sure your .env file exists and has DATABASE_URL set.")
    sys.exit(1)

print(f"✅ Using database: {'Postgres/Neon' if DATABASE_URL else 'SQLite'}")

sys.path.insert(0, os.path.dirname(__file__))

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s | %(name)s | %(levelname)s | %(message)s'
)
logger = logging.getLogger('DEBUG')

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
        from app.config import Config

        meetings  = Config.load_meetings()
        # Get unique groups from JSON
        group_names = list(set(
            m.get('group_name') for m in meetings
            if m.get('group_name')
        ))

        empty_groups  = []
        filled_groups = []

        for group in group_names:
            students = get_students_in_group(group)
            if students:
                filled_groups.append(group)
                logger.info(f"✅ '{group}' → {len(students)} student(s):")
                for s in students:
                    logger.info(
                        f"   👤 {s.get('name')} "
                        f"(chat_id: {repr(s.get('chat_id'))}, "
                        f"active: {s.get('is_active')})"
                    )
            else:
                empty_groups.append(group)
                # ⚠️ Warning only — not an error
                logger.warning(
                    f"⚠️  '{group}' → No students yet "
                    f"(group exists in JSON but no students registered)"
                )

        logger.info(
            f"\n  Groups with students : {len(filled_groups)}"
        )
        if empty_groups:
            logger.info(
                f"  Groups awaiting students: {empty_groups}"
            )

        # ✅ Only fail if ALL groups have zero students
        # (that would mean something is seriously wrong)
        if not filled_groups:
            logger.error("❌ No students found in ANY group — DB issue!")
            return False

        logger.info("\n✅ Student lookup working correctly.")
        return True

    except Exception as e:
        logger.error(f"❌ Student lookup CRASHED: {e}", exc_info=True)
        return False


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
        
        teacher = get_teacher_for_group(group_name)
        logger.info(f"  DB teacher for group: {teacher}")
        
        if teacher and json_teacher_name and teacher.get('name') != json_teacher_name:
            logger.info(f"  🔄 MISMATCH! DB={teacher.get('name')} JSON={json_teacher_name}")
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
# PHASE 7: meetings.json Integrity
# ============================================
def test_meetings_json():
    logger.info("=" * 50)
    logger.info("PHASE 7: meetings.json Integrity")
    logger.info("=" * 50)

    from app.config import Config
    meetings = Config.load_meetings()

    if not meetings:
        logger.error("❌ FAIL: No meetings loaded!")
        return False

    ids = []
    issues = []

    for m in meetings:
        mid   = m.get('id')
        title = m.get('title')
        tname = m.get('teacher_name')
        group = m.get('group_name')

        # Check duplicate IDs
        if mid in ids:
            issues.append(f"DUPLICATE ID: '{mid}'")
            logger.error(f"❌ DUPLICATE ID: '{mid}'")
        ids.append(mid)

        # Check missing required fields
        for field in ['id', 'title', 'teacher_name', 'group_name']:
            if not m.get(field):
                issues.append(f"Missing '{field}' in: {mid}")
                logger.error(f"❌ Missing '{field}' in meeting: {mid}")

    if issues:
        logger.error(f"\n🔴 {len(issues)} issue(s) in meetings.json:")
        for i in issues:
            logger.error(f"   → {i}")
        return False
    else:
        logger.info(f"✅ All {len(meetings)} meetings clean. No duplicates.")
        return True


# ============================================
# PHASE 8: Group Name Matching
# ============================================
# In test_group_matching(), add a whitelist:

def test_group_matching():
    logger.info("=" * 50)
    logger.info("PHASE 8: Student group_name Matching")
    logger.info("=" * 50)

    from app.config import Config
    from app.database.db import get_connection

    meetings = Config.load_meetings()
    conn     = get_connection()
    cursor   = conn.cursor()
    cursor.execute(
        "SELECT name, chat_id, group_name, is_active "
        "FROM users WHERE role = 'student'"
    )
    all_students = [dict(row) for row in cursor.fetchall()]
    conn.close()

    if not all_students:
        logger.warning("⚠️ No students in DB.")
        return True

    json_groups = set(
        (m.get('group_name') or '').strip().lower()
        for m in meetings
    )

    real_errors    = []  # Wrong group name — needs fixing
    pending_groups = []  # No meetings yet — expected

    for s in all_students:
        if not s['is_active']:
            continue

        raw  = s.get('group_name') or ''
        name = s['name']

        if not raw.strip():
            logger.info(f"  ⏳ {name} → no group assigned yet")
            continue

        parsed    = [g.strip().lower() for g in raw.split(',')]
        matched   = [g for g in parsed if g in json_groups]
        unmatched = [g for g in parsed if g not in json_groups]

        if matched:
            logger.info(f"  ✅ {name} → {matched}")

        if unmatched and not matched:
            # Has a group but it's completely unknown — real error
            real_errors.append(
                f"'{name}' group(s) {unmatched} "
                f"don't exist in meetings.json"
            )
            logger.error(
                f"  ❌ {name} → {unmatched} "
                f"— no matching group in JSON!"
            )
        elif unmatched and matched:
            # Has SOME matched groups — the unmatched ones
            # are just pending meetings
            pending_groups.append(name)
            logger.warning(
                f"  ⚠️  {name} → {unmatched} "
                f"have no meetings yet (OK)"
            )
        elif unmatched and not matched:
            pending_groups.append(name)
            logger.warning(
                f"  ⚠️  {name} → awaiting meetings "
                f"for {unmatched}"
            )

    if pending_groups:
        logger.info(
            f"\n  ⏳ Students awaiting meetings "
            f"(no action needed): {pending_groups}"
        )

    if real_errors:
        logger.error(f"\n🔴 {len(real_errors)} REAL error(s):")
        for e in real_errors:
            logger.error(f"   → {e}")
        logger.info("\n  💡 FIX: Update group_name in DB to match meetings.json")
        return False

    logger.info("\n✅ All students either matched or awaiting meetings.")
    return True


# ============================================
# PHASE 9: Teacher Lookup Chain
# ============================================
def test_teacher_lookup():
    logger.info("=" * 50)
    logger.info("PHASE 9: Teacher Lookup Chain")
    logger.info("=" * 50)

    from app.config import Config
    from app.services.user_service import get_user_by_name

    meetings = Config.load_meetings()
    issues   = []

    # Only check: can every teacher_name in JSON be found in DB?
    # Mismatch on get_teacher_for_group is EXPECTED for shared groups
    teacher_names = set(
        m.get('teacher_name', '') for m in meetings
        if m.get('teacher_name')
    )

    logger.info(f"\n  Unique teacher names in JSON: {sorted(teacher_names)}")
    logger.info("\n--- Checking each teacher is registered in DB ---")

    for name in sorted(teacher_names):
        result = get_user_by_name(name)
        if result:
            logger.info(
                f"  ✅ '{name}' → id={result.get('chat_id')}"
            )
        else:
            logger.error(
                f"  ❌ '{name}' NOT FOUND in DB — "
                f"has this teacher registered with the bot?"
            )
            issues.append(f"Teacher '{name}' not in DB")

    if issues:
        logger.error(f"\n🔴 {len(issues)} unregistered teacher(s):")
        for i in issues:
            logger.error(f"   → {i}")
        return False

    logger.info("\n✅ All teachers in JSON are registered in DB.")
    return True


# ============================================
# PHASE 10: /schedule & /today Filter
# ============================================
def test_schedule_filter():
    logger.info("=" * 50)
    logger.info("PHASE 10: /schedule and /today Teacher Filter")
    logger.info("=" * 50)

    from app.config import Config
    from app.database.db import get_connection

    meetings = Config.load_meetings()
    conn     = get_connection()
    cursor   = conn.cursor()
    cursor.execute(
        "SELECT name, chat_id "
        "FROM users WHERE role = 'teacher' AND is_active = 1"
    )
    teachers = [dict(row) for row in cursor.fetchall()]
    conn.close()

    if not teachers:
        logger.warning("⚠️ No active teachers in DB.")
        return True

    issues = []

    for teacher in teachers:
        t_name = teacher['name']
        t_id   = teacher['chat_id']

        # Filter by teacher_name (the fix)
        correct = [
            m for m in meetings
            if (m.get('teacher_name') or '').strip().lower()
            == t_name.strip().lower()
        ]

        if correct:
            logger.info(
                f"\n  ✅ {t_name} (id={t_id}) "
                f"→ {len(correct)} meeting(s):"
            )
            for m in correct:
                logger.info(f"       {m['id']}")
        else:
            logger.error(
                f"\n  ❌ {t_name} → NO MEETINGS MATCHED\n"
                f"     DB name '{t_name}' doesn't match "
                f"any teacher_name in JSON!"
            )
            issues.append(f"No meetings for teacher '{t_name}'")

    if issues:
        logger.error(f"\n🔴 {len(issues)} issue(s):")
        for i in issues:
            logger.error(f"   → {i}")
        return False

    logger.info("\n✅ All teachers will see only their own meetings.")
    return True


# ============================================
# PHASE 11: Simulate get_user_meetings() Fix
# ============================================
def test_get_user_meetings():
    logger.info("=" * 50)
    logger.info("PHASE 11: Simulate get_user_meetings() After Fix")
    logger.info("=" * 50)

    from app.config import Config
    from app.database.db import get_connection

    all_meetings = Config.load_meetings()

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT name, chat_id, role, group_name "
        "FROM users WHERE is_active = 1"
    )
    users = [dict(row) for row in cursor.fetchall()]
    conn.close()

    all_ok = True

    for user in users:
        role    = user['role']
        name    = (user.get('name') or '').strip()
        raw_grp = user.get('group_name') or ''

        if role == 'teacher':
            matched = [
                m for m in all_meetings
                if (m.get('teacher_name') or '').strip().lower()
                == name.lower()
            ]
            logger.info(f"\n  👨‍🏫 {name} (teacher) → {len(matched)} meeting(s):")
            for m in matched:
                logger.info(f"     ✅ {m['id']} | {m['group_name']}")
            if not matched:
                logger.error(
                    f"     ❌ NO MEETINGS — "
                    f"DB name '{name}' doesn't match any teacher_name in JSON!"
                )
                all_ok = False

        elif role == 'student':
            user_groups = [g.strip().lower() for g in raw_grp.split(',')]
            matched = [
                m for m in all_meetings
                if (m.get('group_name') or '').strip().lower()
                in user_groups
            ]
            logger.info(f"\n  👤 {name} (student)")
            logger.info(f"     DB groups : {user_groups}")
            logger.info(f"     Meetings  : {len(matched)}")
            for m in matched:
                logger.info(f"     ✅ {m['id']} | {m['group_name']}")
            if not matched:
                logger.warning(
                    f"     ⚠️ No meetings — "
                    f"check group_name spelling in DB vs JSON"
                )

    return all_ok


# ============================================
# PHASE 12: chat_id Type Consistency
# ============================================
def test_chat_id_types():
    logger.info("=" * 50)
    logger.info("PHASE 12: chat_id Type Consistency")
    logger.info("=" * 50)

    from app.database.db import get_connection

    conn   = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name, role, chat_id FROM users")
    users  = [dict(row) for row in cursor.fetchall()]
    conn.close()

    issues = []

    for u in users:
        cid  = u['chat_id']
        name = u['name']
        role = u['role']

        logger.info(
            f"  {role:8} | {name:20} | "
            f"chat_id={repr(cid)} | type={type(cid).__name__}"
        )

        try:
            int(cid)
        except (ValueError, TypeError):
            issues.append(f"'{name}' has non-numeric chat_id: {repr(cid)}")
            logger.error(f"  ❌ Non-numeric chat_id for {name}: {repr(cid)}")

    if issues:
        logger.error(f"\n🔴 TYPE ISSUES:")
        for i in issues:
            logger.error(f"   → {i}")
        return False
    else:
        logger.info("\n✅ All chat_ids can safely cast to int.")
        return True


# ============================================
# PHASE 13: Silent Killers
# ============================================
def test_silent_killers():
    logger.info("=" * 50)
    logger.info("PHASE 13: Checking for Silent Killers")
    logger.info("=" * 50)
    
    issues = []
    
    try:
        from app.utils.localization import get_user_language, get_text
        lang = get_user_language("892571478")
        logger.info(f"  ✅ get_user_language works: {lang}")
        
        for key in ['lesson_alert_title', 'lesson_details', 'lesson_join', 'lesson_click_hint']:
            text = get_text(key, lang)
            if not text or text == key:
                issues.append(f"Missing localization key: '{key}'")
                logger.error(f"  ❌ Missing key: '{key}'")
            else:
                logger.info(f"  ✅ {key}: OK")

        details = get_text('lesson_details', lang)
        try:
            details.format(
                title="Test", time="19:00",
                group="Group M/N", desc="Test",
                subject="math", teacher="Amir"
            )
            logger.info(f"  ✅ lesson_details formats OK")
        except KeyError as e:
            issues.append(f"lesson_details missing key: {e}")
            logger.error(f"  ❌ lesson_details MISSING KEY: {e}")

        join = get_text('lesson_join', lang)
        try:
            join.format(link="https://test.com")
            logger.info(f"  ✅ lesson_join formats OK")
        except KeyError as e:
            issues.append(f"lesson_join missing key: {e}")
            logger.error(f"  ❌ lesson_join MISSING KEY: {e}")

    except Exception as e:
        logger.error(f"  ❌ Localization CRASHED: {e}", exc_info=True)
        issues.append(f"Localization crash: {e}")

    try:
        from apscheduler.schedulers.asyncio import AsyncIOScheduler
        logger.info(f"  ✅ APScheduler imports OK")
    except ImportError as e:
        issues.append(f"APScheduler missing: {e}")
        logger.error(f"  ❌ APScheduler import FAILED: {e}")

    try:
        import pytz
        from app.config import Config
        from datetime import datetime
        tz  = pytz.timezone(Config.TIMEZONE)
        now = datetime.now(tz)
        logger.info(f"  ✅ Timezone OK: {Config.TIMEZONE} → {now.strftime('%H:%M %Z')}")
    except Exception as e:
        issues.append(f"Timezone: {e}")
        logger.error(f"  ❌ Timezone FAILED: {e}")

    if issues:
        logger.error(f"\n🔴 {len(issues)} silent killer(s):")
        for i in issues:
            logger.error(f"   → {i}")
        return False
    else:
        logger.info(f"\n✅ No silent killers found.")
        return True


# ============================================
# PHASE 14: Role & Keyboard Assignments
# ============================================
def test_role_keyboards():
    logger.info("=" * 50)
    logger.info("PHASE 14: Role & Keyboard Assignments")
    logger.info("=" * 50)
    
    issues = []
    
    try:
        from app.bot.keyboards import main_menu_keyboard
        from telegram import ReplyKeyboardMarkup
        from app.utils.localization import get_text
        
        roles = [
            ('admin',   dict(is_admin=True)),
            ('teacher', dict(is_teacher=True)),
            ('support', dict(is_support=True)),
            ('student', dict()),
        ]

        for role_name, kwargs in roles:
            for lang in ['en', 'ru', 'uz']:
                kb = main_menu_keyboard(**kwargs, lang=lang)
                if not isinstance(kb, ReplyKeyboardMarkup):
                    issues.append(f"{role_name} keyboard ({lang}) wrong type")
                    logger.error(f"  ❌ {role_name} keyboard ({lang}) wrong type")
                else:
                    logger.info(f"  ✅ {role_name} keyboard ({lang}) OK")

        # Students should NOT have teacher-only buttons
        for lang in ['en', 'ru', 'uz']:
            kb = main_menu_keyboard(lang=lang)
            all_buttons = [b.text for row in kb.keyboard for b in row]

            for forbidden_key in ['btn_pay', 'btn_change_lesson']:
                forbidden_text = get_text(forbidden_key, lang)
                if forbidden_text in all_buttons:
                    issues.append(
                        f"Student keyboard ({lang}) has forbidden: {forbidden_key}"
                    )
                    logger.error(
                        f"  ❌ Student ({lang}) should NOT have '{forbidden_text}'"
                    )

    except Exception as e:
        issues.append(f"Keyboard crash: {e}")
        logger.error(f"  ❌ Keyboard test CRASHED: {e}", exc_info=True)

    if issues:
        logger.error(f"\n🔴 {len(issues)} keyboard issue(s):")
        for i in issues:
            logger.error(f"   → {i}")
        return False
    else:
        logger.info("\n✅ All keyboard tests passed.")
        return True


# ============================================
# PHASE 15: Homework Subject Resolution
# ============================================
def test_homework_subject():
    logger.info("=" * 50)
    logger.info("PHASE 15: Homework Subject Resolution")
    logger.info("=" * 50)
    
    issues = []
    
    try:
        from app.config import Config
        meetings = Config.load_meetings()

        if not meetings:
            logger.error("  ❌ No meetings found!")
            return False

        group_names = set(m.get('group_name') for m in meetings if m.get('group_name'))

        for group_name in sorted(group_names):
            meeting = next(
                (m for m in meetings if m.get('group_name') == group_name), None
            )
            if meeting:
                subject = meeting.get('subject', 'Unknown')
                logger.info(f"  ✅ {group_name} → subject: {subject}")
            else:
                issues.append(f"No meeting for group: {group_name}")
                logger.error(f"  ❌ {group_name} → no matching meeting!")

        from app.services.support_service import get_available_support_staff
        support = get_available_support_staff()
        if support:
            logger.info(
                f"  ✅ Homework forwards to: "
                f"{support['name']} ({support['chat_id']})"
            )
        else:
            logger.warning("  ⚠️ No support staff — forwarding will be skipped")

    except Exception as e:
        issues.append(f"Crash: {e}")
        logger.error(f"  ❌ CRASHED: {e}", exc_info=True)

    if issues:
        logger.error(f"\n🔴 {len(issues)} issue(s):")
        for i in issues:
            logger.error(f"   → {i}")
        return False
    else:
        logger.info("\n✅ Homework subject resolution OK.")
        return True
    
# ============================================
# MIGRATION: Fix Muhammad & Муслима group_name
# Run ONCE then remove from debug.py
# ============================================
def fix_student_groups():
    logger.info("=" * 50)
    logger.info("MIGRATION: Fix Mismatched Student Groups")
    logger.info("=" * 50)

    import os
    from app.database.db import get_connection

    # Detect which DB we're on
    is_postgres = bool(os.getenv("DATABASE_URL"))
    p = "%s" if is_postgres else "?"

    logger.info(f"  DB mode: {'PostgreSQL' if is_postgres else 'SQLite'}")

    fixes = {
        'Muhammad' : 'Group Muhammad',
        'Муслима'  : 'Group Muslima',
    }

    conn   = get_connection()

    # ── Get the right cursor ──────────────────────────
    # Postgres: conn is ConnectionWrapper → conn.cursor() works
    # SQLite:   conn is raw sqlite3 conn  → conn.cursor() works
    # Both work the same way here!
    cursor = conn.cursor()

    for student_name, new_group in fixes.items():

        # Step 1: Check current state
        try:
            cursor.execute(
                f"SELECT name, group_name FROM users "
                f"WHERE name = {p} AND role = {p}",
                (student_name, 'student')
            )
            row = cursor.fetchone()
        except Exception as e:
            logger.error(f"  ❌ SELECT failed for '{student_name}': {e}")
            continue

        if not row:
            logger.error(
                f"  ❌ Student '{student_name}' not found in DB! "
                f"Check name spelling exactly."
            )
            continue

        # Works for both sqlite3.Row and psycopg2 RealDictRow
        old_group = dict(row)['group_name']
        logger.info(f"  Found '{student_name}' — current group: '{old_group}'")

        # Step 2: Apply fix
        try:
            cursor.execute(
                f"UPDATE users SET group_name = {p} "
                f"WHERE name = {p} AND role = {p}",
                (new_group, student_name, 'student')
            )
        except Exception as e:
            logger.error(f"  ❌ UPDATE failed for '{student_name}': {e}")
            continue

        if cursor.rowcount:
            logger.info(
                f"  ✅ {student_name}: "
                f"'{old_group}' → '{new_group}'"
            )
        else:
            logger.error(
                f"  ❌ rowcount=0 for '{student_name}' — "
                f"name might not match exactly in DB"
            )

    conn.commit()
    conn.close()
    logger.info("\n✅ Migration done! Re-run debug.py to verify.")
    logger.info("   Then remove fix_student_groups() from main()")
# ============================================
# RUN ALL TESTS
# ============================================
def main():
    logger.info("🚀 DEMY BOT — FULL DEBUG SUITE")
    logger.info("Runs against NEON (Postgres). Safe — no messages sent.\n")

    tests = [
        ("db_connection",       test_db_connection),
        ("user_lookup",         test_user_lookup),
        ("group_lookup",        test_group_lookup),
        ("student_lookup",      test_student_lookup),
        ("auto_heal",           test_auto_heal),
        ("message_build",       test_message_build),
        ("meetings_json",       test_meetings_json),
        ("group_matching",      test_group_matching),
        ("teacher_lookup",      test_teacher_lookup),
        ("schedule_filter",     test_schedule_filter),
        ("get_user_meetings",   test_get_user_meetings),
        ("chat_id_types",       test_chat_id_types),
        ("silent_killers",      test_silent_killers),
        ("role_keyboards",      test_role_keyboards),
        ("homework_subject",    test_homework_subject),
    ]

    results = {}

    # ── Step 1: DB must pass first ──────────────────────
    db_ok = test_db_connection()
    results['db_connection'] = db_ok

    if not db_ok:
        logger.error("❌ DB connection failed — cannot run other tests!")
        logger.error("   Check your DATABASE_URL in .env")
        return

    # ── Step 2: Run migration if needed ─────────────────
    # Remove this block after running once successfully
    logger.info("\n" + "="*50)
    logger.info("MIGRATION: Fix Student Groups (runs once)")
    logger.info("="*50)
    fix_student_groups()
    # ────────────────────────────────────────────────────

    # ── Step 3: Run all other tests ─────────────────────
    remaining = [t for t in tests if t[0] != 'db_connection']
    for name, fn in remaining:
        try:
            results[name] = fn()
        except Exception as e:
            logger.error(
                f"❌ {name} CRASHED at top level: {e}",
                exc_info=True
            )
            results[name] = False

    # ── Summary ─────────────────────────────────────────
    logger.info("\n" + "=" * 50)
    logger.info("📋 RESULTS SUMMARY")
    logger.info("=" * 50)

    passed = [n for n, r in results.items() if r]
    failed = [n for n, r in results.items() if not r]

    for name, result in results.items():
        icon = "✅" if result else "❌"
        logger.info(f"  {icon} {name.upper()}")

    logger.info(f"\n  Passed : {len(passed)}/{len(tests)}")
    logger.info(f"  Failed : {len(failed)}/{len(tests)}")

    if not failed:
        logger.info("\n🎉 ALL TESTS PASSED — Safe to deploy!")
    else:
        logger.info("\n🔴 FIX THESE BEFORE DEPLOYING:")
        for name in failed:
            logger.info(f"   → {name}")


if __name__ == '__main__':
    main()