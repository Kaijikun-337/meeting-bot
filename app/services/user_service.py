import random
import string
import json
import os
from typing import Optional
from datetime import datetime
from app.database.db import get_connection


def generate_registration_key(role: str) -> str:
    """Generate unique registration key."""
    prefix = "TCH" if role == "teacher" else "STU"
    chars = string.ascii_uppercase + string.digits
    random_part = ''.join(random.choices(chars, k=6))
    return f"{prefix}-{random_part}"


def create_pending_user(name: str, role: str, group_name: str = None) -> str:
    """Create a pending user (not yet activated)."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Generate unique key
    while True:
        key = generate_registration_key(role)
        cursor.execute('SELECT 1 FROM users WHERE registration_key = ?', (key,))
        if not cursor.fetchone():
            break
    
    try:
        cursor.execute('''
            INSERT INTO users (name, role, group_name, registration_key, is_active)
            VALUES (?, ?, ?, ?, 0)
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
    
    try:
        # 1. Check if exists
        cursor.execute('''
            SELECT 1 FROM pending_teacher_groups 
            WHERE registration_key = ? AND group_name = ?
        ''', (registration_key, group_name))
        
        if cursor.fetchone():
            # 2. Update
            cursor.execute('''
                UPDATE pending_teacher_groups 
                SET subject = ? 
                WHERE registration_key = ? AND group_name = ?
            ''', (subject, registration_key, group_name))
        else:
            # 3. Insert
            cursor.execute('''
                INSERT INTO pending_teacher_groups (registration_key, group_name, subject)
                VALUES (?, ?, ?)
            ''', (registration_key, group_name, subject))
            
        conn.commit()
        return True
    except Exception as e:
        print(f"❌ Error adding pending group: {e}")
        return False
    finally:
        conn.close()


def sync_teacher_groups_from_json(teacher_chat_id, teacher_name):
    """Reads meetings.json and links groups to teacher (Postgres Safe)."""
    from app.config import Config
    
    try:
        # Load meetings using Config helper (Robust)
        # Note: We rely on Config.load_meetings to handle the path logic
        meetings = Config.load_meetings()

        # Find unique groups/subjects for this teacher
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
        
        for group, subject in found_entries:
            # 1. Check if exists
            cursor.execute("""
                SELECT 1 FROM teacher_groups 
                WHERE teacher_chat_id = ? AND group_name = ?
            """, (str(teacher_chat_id), group))
            
            if cursor.fetchone():
                # 2. Update subject if needed
                cursor.execute("""
                    UPDATE teacher_groups SET subject = ?
                    WHERE teacher_chat_id = ? AND group_name = ?
                """, (subject, str(teacher_chat_id), group))
            else:
                # 3. Insert
                cursor.execute("""
                    INSERT INTO teacher_groups (teacher_chat_id, group_name, subject)
                    VALUES (?, ?, ?)
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
    
    # Find pending user with this key
    cursor.execute('''
        SELECT * FROM users WHERE registration_key = ? AND is_active = 0
    ''', (registration_key,))
    
    user = cursor.fetchone()
    
    if not user:
        # Check if key used
        cursor.execute('SELECT * FROM users WHERE registration_key = ?', (registration_key,))
        existing = cursor.fetchone()
        conn.close()
        
        if existing and existing['is_active'] == 1:
            return {"error": "key_already_used"}
        return {"error": "invalid_key"}
    
    # Check if chat_id already registered
    cursor.execute('SELECT 1 FROM users WHERE chat_id = ? AND is_active = 1', (str(chat_id),))
    if cursor.fetchone():
        conn.close()
        return {"error": "already_registered"}
    
    # Activate user
    try:
        cursor.execute('''
            UPDATE users 
            SET chat_id = ?, is_active = 1, activated_at = ?
            WHERE registration_key = ?
        ''', (str(chat_id), datetime.now().isoformat(), registration_key))
        
        user_role = user['role']
        user_name = user['name']

        # If teacher, move pending groups to active
        if user_role == 'teacher':
            cursor.execute('''
                SELECT group_name, subject FROM pending_teacher_groups
                WHERE registration_key = ?
            ''', (registration_key,))
            
            groups = cursor.fetchall()
            for group in groups:
                # Manual Upsert for each group
                g_name = group['group_name']
                subj = group['subject']
                
                cursor.execute("SELECT 1 FROM teacher_groups WHERE teacher_chat_id=? AND group_name=?", (str(chat_id), g_name))
                if cursor.fetchone():
                    cursor.execute("UPDATE teacher_groups SET subject=? WHERE teacher_chat_id=? AND group_name=?", (subj, str(chat_id), g_name))
                else:
                    cursor.execute("INSERT INTO teacher_groups (teacher_chat_id, group_name, subject) VALUES (?, ?, ?)", (str(chat_id), g_name, subj))
            
            # Clean up pending
            cursor.execute('DELETE FROM pending_teacher_groups WHERE registration_key = ?', (registration_key,))

        conn.commit()
        conn.close()

        # Run Sync (Safe to run outside trans)
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
    cursor.execute('SELECT * FROM users WHERE chat_id = ? AND is_active = 1', (str(chat_id),))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_user_by_key(registration_key: str) -> dict:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE registration_key = ?', (registration_key,))
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
    key = generate_registration_key(role)
    
    try:
        # Check exists
        cursor.execute("SELECT 1 FROM users WHERE chat_id = ?", (str(chat_id),))
        if cursor.fetchone():
            cursor.execute("""
                UPDATE users SET name=?, role=?, group_name=?, registration_key=?, is_active=1, activated_at=?
                WHERE chat_id=?
            """, (name, role, group_name, key, datetime.now().isoformat(), str(chat_id)))
        else:
            cursor.execute("""
                INSERT INTO users (chat_id, name, role, group_name, registration_key, is_active, activated_at)
                VALUES (?, ?, ?, ?, ?, 1, ?)
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
    
    try:
        cursor.execute("SELECT 1 FROM teacher_groups WHERE teacher_chat_id=? AND group_name=?", (str(teacher_chat_id), group_name))
        if cursor.fetchone():
            cursor.execute("UPDATE teacher_groups SET subject=? WHERE teacher_chat_id=? AND group_name=?", (subject, str(teacher_chat_id), group_name))
        else:
            cursor.execute("INSERT INTO teacher_groups (teacher_chat_id, group_name, subject) VALUES (?, ?, ?)", (str(teacher_chat_id), group_name, subject))
            
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
    cursor.execute('SELECT group_name, subject FROM teacher_groups WHERE teacher_chat_id = ?', (str(teacher_chat_id),))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_students_in_group(group_name: str) -> list:
    """Get all students in a group (Handling multi-group students)."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Fetch ALL active students first (safer than complex SQL LIKEs across DB types)
    cursor.execute("SELECT * FROM users WHERE role = 'student' AND is_active = 1")
    rows = cursor.fetchall()
    conn.close()
    
    target_group = group_name.strip().lower()
    matched_students = []
    
    for row in rows:
        student_data = dict(row)
        raw_groups = student_data.get('group_name') or ""
        
        # Split "Group A, Group B" -> ["group a", "group b"]
        student_groups = [g.strip().lower() for g in raw_groups.split(',')]
        
        if target_group in student_groups:
            matched_students.append(student_data)
            
    return matched_students


def get_teacher_for_group(group_name: str) -> dict:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT u.* FROM users u
        JOIN teacher_groups tg ON u.chat_id = tg.teacher_chat_id
        WHERE tg.group_name = ? AND u.is_active = 1
    ''', (group_name,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


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
    try:
        cursor.execute('DELETE FROM users WHERE registration_key = ?', (registration_key,))
        cursor.execute('DELETE FROM pending_teacher_groups WHERE registration_key = ?', (registration_key,))
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        conn.close()

def delete_user_by_chat_id(chat_id: str) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT registration_key, role FROM users WHERE chat_id = ?", (str(chat_id),))
        row = cursor.fetchone()
        if not row: return False
        
        reg_key = row['registration_key']
        role = row['role']
        
        cursor.execute("DELETE FROM users WHERE chat_id = ?", (str(chat_id),))
        if role == 'teacher':
            cursor.execute("DELETE FROM teacher_groups WHERE teacher_chat_id = ?", (str(chat_id),))
        cursor.execute("DELETE FROM pending_teacher_groups WHERE registration_key = ?", (reg_key,))
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
    try:
        cursor.execute("UPDATE users SET name = ? WHERE chat_id = ?", (new_name, str(chat_id)))
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        conn.close()


def update_student_group(chat_id: str, new_group: str) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE users SET group_name = ? WHERE chat_id = ? AND role = 'student'", (new_group, str(chat_id)))
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        conn.close()


def update_teacher_name(chat_id: str, new_name: str) -> bool:
    return update_user_name(chat_id, new_name)


def update_teacher_groups(chat_id: str, new_group: Optional[str] = None, new_subject: Optional[str] = None) -> bool:
    if not new_group and not new_subject:
        return True
    conn = get_connection()
    cursor = conn.cursor()
    try:
        if new_group and new_subject:
            cursor.execute("UPDATE teacher_groups SET group_name = ?, subject = ? WHERE teacher_chat_id = ?", (new_group, new_subject, str(chat_id)))
        elif new_group:
            cursor.execute("UPDATE teacher_groups SET group_name = ? WHERE teacher_chat_id = ?", (new_group, str(chat_id)))
        elif new_subject:
            cursor.execute("UPDATE teacher_groups SET subject = ? WHERE teacher_chat_id = ?", (new_subject, str(chat_id)))
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        conn.close()