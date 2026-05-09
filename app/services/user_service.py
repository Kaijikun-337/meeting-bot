import random
import string
from typing import Optional
from datetime import datetime
from app.database.db import get_connection, get_p
import logging
from app.config import Config

logger = logging.getLogger(__name__)

def generate_registration_key(role: str) -> str:
    """Generate unique registration key."""
    if role == "teacher":
        prefix = "TCH"
    else:
        prefix = "STU"
    chars = string.ascii_uppercase + string.digits
    random_part = ''.join(random.choices(chars, k=6))
    return f"{prefix}-{random_part}"


def create_pending_user(name: str, role: str, group_name: str = None) -> str:
    """Create a pending user (not yet activated)."""
    conn = get_connection()
    cursor = conn.cursor()
    p = get_p()

    while True:
        key = generate_registration_key(role)
        cursor.execute(f'SELECT 1 FROM users WHERE registration_key = {p}', (key,))
        if not cursor.fetchone():
            break

    try:
        cursor.execute(f'''
            INSERT INTO users (name, role, group_name, registration_key, is_active)
            VALUES ({p}, {p}, {p}, {p}, 0)
        ''', (name, role, group_name, key))
        conn.commit()
        return key
    except Exception as e:
        print(f"❌ Error creating user: {e}")
        return None
    finally:
        conn.close()


def add_pending_teacher_group(registration_key: str, group_name: str, subject: str = None):
    """Add a group for a pending teacher (Postgres Safe)."""
    conn = get_connection()
    cursor = conn.cursor()
    p = get_p()

    try:
        cursor.execute(f'''
            SELECT 1 FROM pending_teacher_groups
            WHERE registration_key = {p} AND group_name = {p}
        ''', (registration_key, group_name))

        if cursor.fetchone():
            cursor.execute(f'''
                UPDATE pending_teacher_groups
                SET subject = {p}
                WHERE registration_key = {p} AND group_name = {p}
            ''', (subject, registration_key, group_name))
        else:
            cursor.execute(f'''
                INSERT INTO pending_teacher_groups (registration_key, group_name, subject)
                VALUES ({p}, {p}, {p})
            ''', (registration_key, group_name, subject))

        conn.commit()
        return True
    except Exception as e:
        print(f"❌ Error adding pending group: {e}")
        return False
    finally:
        conn.close()


def sync_teacher_groups_from_json(teacher_chat_id, teacher_name):
    """Reads meetings.json and links groups to teacher."""
    from app.config import Config

    try:
        meetings = Config.load_meetings()

        found_entries = set()
        target_name = teacher_name.strip().lower()

        for m in meetings:
            t_name = m.get('teacher_name', '')
            if t_name and t_name.strip().lower() == target_name:
                g_name = m.get('group_name')
                subj = m.get('subject', 'General')
                if g_name:
                    found_entries.add((g_name, subj))

        if not found_entries:
            print(f"⚠️ No groups found in JSON for teacher: {teacher_name}")
            return

        conn = get_connection()
        cursor = conn.cursor()
        p = get_p()

        for group, subject in found_entries:
            cursor.execute(f"""
                SELECT 1 FROM teacher_groups
                WHERE teacher_chat_id = {p} AND group_name = {p}
            """, (str(teacher_chat_id), group))

            if cursor.fetchone():
                cursor.execute(f"""
                    UPDATE teacher_groups SET subject = {p}
                    WHERE teacher_chat_id = {p} AND group_name = {p}
                """, (subject, str(teacher_chat_id), group))
            else:
                cursor.execute(f"""
                    INSERT INTO teacher_groups (teacher_chat_id, group_name, subject)
                    VALUES ({p}, {p}, {p})
                """, (str(teacher_chat_id), group, subject))

            print(f"✅ Auto-linked group '{group}' ({subject}) to {teacher_name}")

        conn.commit()
        conn.close()

    except Exception as e:
        print(f"❌ Error syncing teacher groups: {e}")


def activate_user(chat_id: str, registration_key: str) -> dict:
    """Activate a user with their registration key (Postgres Safe)."""
    conn = get_connection()
    cursor = conn.cursor()
    p = get_p()

    cursor.execute(f'''
        SELECT * FROM users WHERE registration_key = {p} AND is_active = 0
    ''', (registration_key,))

    user = cursor.fetchone()

    if not user:
        cursor.execute(f'SELECT * FROM users WHERE registration_key = {p}', (registration_key,))
        existing = cursor.fetchone()
        conn.close()

        if existing and existing['is_active'] == 1:
            return {"error": "key_already_used"}
        return {"error": "invalid_key"}

    cursor.execute(f'SELECT 1 FROM users WHERE chat_id = {p} AND is_active = 1', (str(chat_id),))
    if cursor.fetchone():
        conn.close()
        return {"error": "already_registered"}

    try:
        cursor.execute(f'''
            UPDATE users
            SET chat_id = {p}, is_active = 1, activated_at = {p}
            WHERE registration_key = {p}
        ''', (str(chat_id), datetime.now().isoformat(), registration_key))

        user_role = user['role']
        user_name = user['name']

        if user_role == 'teacher':
            cursor.execute(f'''
                SELECT group_name, subject FROM pending_teacher_groups
                WHERE registration_key = {p}
            ''', (registration_key,))

            groups = cursor.fetchall()
            for group in groups:
                g_name = group['group_name']
                subj = group['subject']

                cursor.execute(f"SELECT 1 FROM teacher_groups WHERE teacher_chat_id={p} AND group_name={p}", (str(chat_id), g_name))
                if cursor.fetchone():
                    cursor.execute(f"UPDATE teacher_groups SET subject={p} WHERE teacher_chat_id={p} AND group_name={p}", (subj, str(chat_id), g_name))
                else:
                    cursor.execute(f"INSERT INTO teacher_groups (teacher_chat_id, group_name, subject) VALUES ({p}, {p}, {p})", (str(chat_id), g_name, subj))

            cursor.execute(f'DELETE FROM pending_teacher_groups WHERE registration_key = {p}', (registration_key,))

        conn.commit()
        conn.close()

        if user_role == 'teacher':
            sync_teacher_groups_from_json(str(chat_id), user_name)

        return {
            "success": True,
            "name": user_name,
            "role": user_role,
            "group_name": user['group_name']
        }

    except Exception as e:
        print(f"❌ Activation error: {e}")
        return {"error": str(e)}


def get_user(chat_id: str) -> dict:
    conn = get_connection()
    cursor = conn.cursor()
    p = get_p()

    cursor.execute(f'SELECT * FROM users WHERE chat_id = {p} AND is_active = 1', (str(chat_id),))

    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_user_by_key(registration_key: str) -> dict:
    conn = get_connection()
    cursor = conn.cursor()
    p = get_p()
    cursor.execute(f'SELECT * FROM users WHERE registration_key = {p}', (registration_key,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def is_registered(chat_id: str) -> bool:
    return get_user(chat_id) is not None


def get_user_role(chat_id: str) -> str:
    user = get_user(chat_id)
    return user['role'] if user else None


def register_user(chat_id: str, name: str, role: str, group_name: str = None) -> bool:
    """Legacy admin registration (Postgres Safe)."""
    conn = get_connection()
    cursor = conn.cursor()
    p = get_p()
    key = generate_registration_key(role)

    try:
        cursor.execute(f"SELECT 1 FROM users WHERE chat_id = {p}", (str(chat_id),))
        if cursor.fetchone():
            cursor.execute(f"""
                UPDATE users SET name={p}, role={p}, group_name={p}, registration_key={p}, is_active=1, activated_at={p}
                WHERE chat_id={p}
            """, (name, role, group_name, key, datetime.now().isoformat(), str(chat_id)))
        else:
            cursor.execute(f"""
                INSERT INTO users (chat_id, name, role, group_name, registration_key, is_active, activated_at)
                VALUES ({p}, {p}, {p}, {p}, {p}, 1, {p})
            """, (str(chat_id), name, role, group_name, key, datetime.now().isoformat()))

        conn.commit()
        return True
    except Exception as e:
        print(f"❌ Registration error: {e}")
        return False
    finally:
        conn.close()


def add_teacher_group(teacher_chat_id: str, group_name: str, subject: str = None):
    """Link teacher to group (Postgres Safe)."""
    conn = get_connection()
    cursor = conn.cursor()
    p = get_p()

    try:
        cursor.execute(f"SELECT 1 FROM teacher_groups WHERE teacher_chat_id={p} AND group_name={p}", (str(teacher_chat_id), group_name))
        if cursor.fetchone():
            cursor.execute(f"UPDATE teacher_groups SET subject={p} WHERE teacher_chat_id={p} AND group_name={p}", (subject, str(teacher_chat_id), group_name))
        else:
            cursor.execute(f"INSERT INTO teacher_groups (teacher_chat_id, group_name, subject) VALUES ({p}, {p}, {p})", (str(teacher_chat_id), group_name, subject))

        conn.commit()
        return True
    except Exception as e:
        print(f"❌ Error adding teacher group: {e}")
        return False
    finally:
        conn.close()


def get_teacher_groups(teacher_chat_id: str) -> list:
    conn = get_connection()
    cursor = conn.cursor()
    p = get_p()

    cursor.execute(f'SELECT group_name, subject FROM teacher_groups WHERE teacher_chat_id = {p}', (str(teacher_chat_id),))

    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_students_in_group(group_name: str) -> list:
    """Get all students in a group (Handling multi-group students)."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE role = 'student' AND is_active = 1")
    rows = cursor.fetchall()
    conn.close()

    target_group = group_name.strip().lower()
    matched_students = []

    for row in rows:
        student_data = dict(row)
        raw_groups = student_data.get('group_name') or ""
        student_groups = [g.strip().lower() for g in raw_groups.split(',')]

        if target_group in student_groups:
            matched_students.append(student_data)

    return matched_students


def get_teacher_for_group(group_name: str) -> dict:
    conn = get_connection()
    cursor = conn.cursor()
    p = get_p()

    query = f'''
        SELECT u.* FROM users u
        JOIN teacher_groups tg ON CAST(u.chat_id AS TEXT) = CAST(tg.teacher_chat_id AS TEXT)
        WHERE LOWER(tg.group_name) = LOWER({p}) AND u.is_active = 1
    '''

    try:
        cursor.execute(query, (group_name,))
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None
    except Exception as e:
        print(f"❌ SQL JOIN Error: {e}")
        return None
    finally:
        conn.close()


def get_all_pending_users() -> list:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE is_active = 0 ORDER BY created_at DESC')
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_all_active_users() -> list:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE is_active = 1 ORDER BY role, name')
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def delete_user(registration_key: str) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    p = get_p()
    try:
        cursor.execute(f'DELETE FROM users WHERE registration_key = {p}', (registration_key,))
        cursor.execute(f'DELETE FROM pending_teacher_groups WHERE registration_key = {p}', (registration_key,))
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        conn.close()

def delete_user_by_chat_id(chat_id: str) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    p = get_p()
    try:
        cursor.execute(f"SELECT registration_key, role FROM users WHERE chat_id = {p}", (str(chat_id),))
        row = cursor.fetchone()
        if not row: return False

        reg_key = row['registration_key']
        role = row['role']

        cursor.execute(f"DELETE FROM users WHERE chat_id = {p}", (str(chat_id),))
        if role == 'teacher':
            cursor.execute(f"DELETE FROM teacher_groups WHERE teacher_chat_id = {p}", (str(chat_id),))
        cursor.execute(f"DELETE FROM pending_teacher_groups WHERE registration_key = {p}", (reg_key,))
        conn.commit()
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        conn.close()


def update_user_name(chat_id: str, new_name: str) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    p = get_p()
    try:
        cursor.execute(f"UPDATE users SET name = {p} WHERE chat_id = {p}", (new_name, str(chat_id)))
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        conn.close()


def update_student_group(chat_id: str, new_group: str) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    p = get_p()
    try:
        cursor.execute(f"UPDATE users SET group_name = {p} WHERE chat_id = {p} AND role = 'student'", (new_group, str(chat_id)))
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        conn.close()


def get_teacher_groups_effective(chat_id: str) -> list:
    """Returns teacher groups from DB, falling back to meetings.json by name.
    Auto-heals the DB when the fallback finds groups the DB is missing."""
    groups = get_teacher_groups(chat_id)
    if groups:
        return groups

    user = get_user(chat_id)
    if not user:
        return []

    teacher_name = (user.get('name') or '').strip().lower()
    if not teacher_name:
        return []

    meetings = Config.load_meetings()
    seen = set()
    fallback_groups = []
    for m in meetings:
        if (m.get('teacher_name') or '').strip().lower() == teacher_name:
            g = m.get('group_name')
            subj = m.get('subject')
            if g and g not in seen:
                seen.add(g)
                fallback_groups.append({'group_name': g, 'subject': subj})

    if fallback_groups:
        logger.info(f"Teacher {user['name']} ({chat_id}): no DB groups found, healing from meetings.json")
        sync_teacher_groups_from_json(chat_id, user['name'])

    return fallback_groups


def update_teacher_name(chat_id: str, new_name: str) -> bool:
    return update_user_name(chat_id, new_name)


def update_teacher_groups(chat_id: str, new_group: Optional[str] = None, new_subject: Optional[str] = None) -> bool:
    if not new_group:
        return True

    conn = get_connection()
    cursor = conn.cursor()
    p = get_p()

    try:
        cursor.execute(f"SELECT 1 FROM teacher_groups WHERE teacher_chat_id = {p} AND group_name = {p}",
                       (str(chat_id), new_group))

        exists = cursor.fetchone()

        if exists:
            if new_subject:
                cursor.execute(f"UPDATE teacher_groups SET subject = {p} WHERE teacher_chat_id = {p} AND group_name = {p}",
                               (new_subject, str(chat_id), new_group))
        else:
            cursor.execute(f"INSERT INTO teacher_groups (teacher_chat_id, group_name, subject) VALUES ({p}, {p}, {p})",
                           (str(chat_id), new_group, new_subject or "General"))

        conn.commit()
        return True
    except Exception as e:
        print(f"❌ SQL Error: {e}")
        return False
    finally:
        conn.close()


def get_user_by_name(name: str):
    """Look up a user by name. Tries exact match first, then fuzzy."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        clean_name = name.strip()
        if not clean_name:
            return None

        if Config.DATABASE_URL:
            cur.execute(
                """SELECT chat_id, name FROM users
                   WHERE name ILIKE %s
                   AND chat_id IS NOT NULL
                   AND chat_id != ''
                   AND is_active = 1
                   LIMIT 1""",
                (clean_name,)
            )
            row = cur.fetchone()

            if not row:
                cur.execute(
                    """SELECT chat_id, name FROM users
                       WHERE name ILIKE %s
                       AND chat_id IS NOT NULL
                       AND chat_id != ''
                       AND is_active = 1
                       LIMIT 1""",
                    (f"%{clean_name}%",)
                )
                row = cur.fetchone()
        else:
            cur.execute(
                """SELECT chat_id, name FROM users
                   WHERE name = ? COLLATE NOCASE
                   AND chat_id IS NOT NULL
                   AND chat_id != ''
                   AND is_active = 1
                   LIMIT 1""",
                (clean_name,)
            )
            row = cur.fetchone()

            if not row:
                cur.execute(
                    """SELECT chat_id, name FROM users
                       WHERE name LIKE ?
                       AND chat_id IS NOT NULL
                       AND chat_id != ''
                       AND is_active = 1
                       LIMIT 1""",
                    (f"%{clean_name}%",)
                )
                row = cur.fetchone()

        if row:
            if isinstance(row, dict):
                return {'chat_id': row['chat_id'], 'name': row['name']}
            else:
                return {'chat_id': row[0], 'name': row[1]}
        return None
    except Exception as e:
        logger.error(f"❌ get_user_by_name failed for '{name}': {e}", exc_info=True)
        return None
    finally:
        cur.close()
        conn.close()

def update_teacher_group_assignment(group_name: str, new_chat_id: str, subject: str = None):
    """Updates or INSERTS the teacher-group mapping."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        new_chat_id = str(new_chat_id)

        if Config.DATABASE_URL:
            cur.execute(
                "DELETE FROM teacher_groups WHERE group_name ILIKE %s",
                (group_name,)
            )
            cur.execute(
                """INSERT INTO teacher_groups (teacher_chat_id, group_name, subject)
                   VALUES (%s, %s, %s)""",
                (new_chat_id, group_name, subject)
            )
        else:
            cur.execute(
                "DELETE FROM teacher_groups WHERE group_name = ?",
                (group_name,)
            )
            cur.execute(
                """INSERT INTO teacher_groups (teacher_chat_id, group_name, subject)
                   VALUES (?, ?, ?)""",
                (new_chat_id, group_name, subject)
            )

        conn.commit()
        logger.info(f"✅ Group '{group_name}' now assigned to teacher {new_chat_id}")
    except Exception as e:
        logger.error(f"❌ Failed to update teacher group assignment: {e}")
    finally:
        cur.close()
        conn.close()

def cleanup_expired_keys(hours: int = 24):
    """Delete users who registered a key but never activated within X hours."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        if Config.DATABASE_URL:
            cur.execute("""
                DELETE FROM users
                WHERE is_active = 0
                AND (chat_id IS NULL OR chat_id = '')
                AND created_at < NOW() - INTERVAL '%s hours'
            """, (hours,))
        else:
            cur.execute("""
                DELETE FROM users
                WHERE is_active = 0
                AND (chat_id IS NULL OR chat_id = '')
                AND created_at < datetime('now', ? || ' hours')
            """, (f'-{hours}',))

        deleted = cur.rowcount
        conn.commit()

        if deleted > 0:
            logger.info(f"🧹 Cleaned up {deleted} expired registration(s)")

        return deleted
    except Exception as e:
        logger.error(f"❌ cleanup_expired_keys failed: {e}")
        return 0
    finally:
        cur.close()
        conn.close()
