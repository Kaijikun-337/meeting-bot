import random
import string
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
    """
    Create a pending user (not yet activated).
    Returns the registration key.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Generate unique key
    while True:
        key = generate_registration_key(role)
        cursor.execute('SELECT id FROM users WHERE registration_key = ?', (key,))
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
    """Add a group for a pending teacher."""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT OR REPLACE INTO pending_teacher_groups (registration_key, group_name, subject)
            VALUES (?, ?, ?)
        ''', (registration_key, group_name, subject))
        conn.commit()
        return True
    except Exception as e:
        print(f"❌ Error adding pending group: {e}")
        return False
    finally:
        conn.close()


def activate_user(chat_id: str, registration_key: str) -> dict:
    """
    Activate a user with their registration key.
    Returns user info or error.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Find pending user with this key
    cursor.execute('''
        SELECT * FROM users WHERE registration_key = ? AND is_active = 0
    ''', (registration_key,))
    
    user = cursor.fetchone()
    
    if not user:
        # Check if key exists but already used
        cursor.execute('SELECT * FROM users WHERE registration_key = ?', (registration_key,))
        existing = cursor.fetchone()
        
        if existing and existing['is_active'] == 1:
            conn.close()
            return {"error": "key_already_used"}
        
        conn.close()
        return {"error": "invalid_key"}
    
    # Check if chat_id already registered
    cursor.execute('SELECT * FROM users WHERE chat_id = ? AND is_active = 1', (str(chat_id),))
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
        
        # If teacher, move pending groups to active
        if user['role'] == 'teacher':
            cursor.execute('''
                SELECT group_name, subject FROM pending_teacher_groups
                WHERE registration_key = ?
            ''', (registration_key,))
            
            groups = cursor.fetchall()
            for group in groups:
                cursor.execute('''
                    INSERT OR REPLACE INTO teacher_groups (teacher_chat_id, group_name, subject)
                    VALUES (?, ?, ?)
                ''', (str(chat_id), group['group_name'], group['subject']))
            
            # Clean up pending groups
            cursor.execute('DELETE FROM pending_teacher_groups WHERE registration_key = ?', (registration_key,))
        
        conn.commit()
        
        return {
            "success": True,
            "name": user['name'],
            "role": user['role'],
            "group_name": user['group_name']
        }
        
    except Exception as e:
        print(f"❌ Activation error: {e}")
        return {"error": str(e)}
    finally:
        conn.close()


def get_user(chat_id: str) -> dict:
    """Get active user by chat_id."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM users WHERE chat_id = ? AND is_active = 1', (str(chat_id),))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return dict(row)
    return None


def get_user_by_key(registration_key: str) -> dict:
    """Get user by registration key."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM users WHERE registration_key = ?', (registration_key,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return dict(row)
    return None


def is_registered(chat_id: str) -> bool:
    """Check if user is registered and active."""
    return get_user(chat_id) is not None


def get_user_role(chat_id: str) -> str:
    """Get user role (teacher/student)."""
    user = get_user(chat_id)
    return user['role'] if user else None


def register_user(chat_id: str, name: str, role: str, group_name: str = None) -> bool:
    """Legacy function - direct registration (for admin use)."""
    conn = get_connection()
    cursor = conn.cursor()
    
    key = generate_registration_key(role)
    
    try:
        cursor.execute('''
            INSERT OR REPLACE INTO users (chat_id, name, role, group_name, registration_key, is_active, activated_at)
            VALUES (?, ?, ?, ?, ?, 1, ?)
        ''', (str(chat_id), name, role, group_name, key, datetime.now().isoformat()))
        conn.commit()
        return True
    except Exception as e:
        print(f"❌ Registration error: {e}")
        return False
    finally:
        conn.close()


def add_teacher_group(teacher_chat_id: str, group_name: str, subject: str = None):
    """Link teacher to a group."""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT OR REPLACE INTO teacher_groups (teacher_chat_id, group_name, subject)
            VALUES (?, ?, ?)
        ''', (str(teacher_chat_id), group_name, subject))
        conn.commit()
        return True
    except Exception as e:
        print(f"❌ Error adding teacher group: {e}")
        return False
    finally:
        conn.close()


def get_teacher_groups(teacher_chat_id: str) -> list:
    """Get all groups for a teacher."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT group_name, subject FROM teacher_groups 
        WHERE teacher_chat_id = ?
    ''', (str(teacher_chat_id),))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]


def get_students_in_group(group_name: str) -> list:
    """Get all students in a group."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM users 
        WHERE role = 'student' AND group_name = ? AND is_active = 1
    ''', (group_name,))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]


def get_teacher_for_group(group_name: str) -> dict:
    """Get teacher for a specific group."""
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
    """Get all pending (inactive) users."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM users WHERE is_active = 0 ORDER BY created_at DESC')
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]


def get_all_active_users() -> list:
    """Get all active users."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM users WHERE is_active = 1 ORDER BY role, name')
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]


def delete_user(registration_key: str) -> bool:
    """Delete a user by registration key."""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('DELETE FROM users WHERE registration_key = ?', (registration_key,))
        cursor.execute('DELETE FROM pending_teacher_groups WHERE registration_key = ?', (registration_key,))
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"❌ Error deleting user: {e}")
        return False
    finally:
        conn.close()

def delete_user_by_chat_id(chat_id: str) -> bool:
    """Delete a user and related teacher groups by chat_id."""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Get registration key first (for cleanup of pending_teacher_groups if needed)
        cursor.execute("SELECT registration_key, role FROM users WHERE chat_id = ?", (str(chat_id),))
        row = cursor.fetchone()
        if not row:
            return False
        
        reg_key = row['registration_key']
        role = row['role']
        
        # Delete from users
        cursor.execute("DELETE FROM users WHERE chat_id = ?", (str(chat_id),))
        
        # If teacher, delete teacher_groups mapping
        if role == 'teacher':
            cursor.execute("DELETE FROM teacher_groups WHERE teacher_chat_id = ?", (str(chat_id),))
        
        # Also cleanup pending_teacher_groups if any
        cursor.execute("DELETE FROM pending_teacher_groups WHERE registration_key = ?", (reg_key,))
        
        conn.commit()
        return True
    except Exception as e:
        print(f"❌ Error deleting user by chat_id: {e}")
        return False
    finally:
        conn.close()


def update_user_name(chat_id: str, new_name: str) -> bool:
    """Update user's name by chat_id."""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("UPDATE users SET name = ? WHERE chat_id = ?", (new_name, str(chat_id)))
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"❌ Error updating user name: {e}")
        return False
    finally:
        conn.close()


def update_student_group(chat_id: str, new_group: str) -> bool:
    """Update student's group_name by chat_id."""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            UPDATE users 
            SET group_name = ?
            WHERE chat_id = ? AND role = 'student'
        """, (new_group, str(chat_id)))
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"❌ Error updating student group: {e}")
        return False
    finally:
        conn.close()


def update_teacher_name(chat_id: str, new_name: str) -> bool:
    """Update teacher's name by chat_id."""
    return update_user_name(chat_id, new_name)


def update_teacher_groups(chat_id: str, new_group: Optional[str] = None, new_subject: Optional[str] = None) -> bool:
    """
    Update all teacher_groups rows for a teacher.
    If new_group is provided, sets group_name = new_group for all mappings.
    If new_subject is provided, sets subject = new_subject for all mappings.
    """
    if not new_group and not new_subject:
        return True  # Nothing to do
    
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        if new_group and new_subject:
            cursor.execute("""
                UPDATE teacher_groups
                SET group_name = ?, subject = ?
                WHERE teacher_chat_id = ?
            """, (new_group, new_subject, str(chat_id)))
        elif new_group:
            cursor.execute("""
                UPDATE teacher_groups
                SET group_name = ?
                WHERE teacher_chat_id = ?
            """, (new_group, str(chat_id)))
        elif new_subject:
            cursor.execute("""
                UPDATE teacher_groups
                SET subject = ?
                WHERE teacher_chat_id = ?
            """, (new_subject, str(chat_id)))
        
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"❌ Error updating teacher groups: {e}")
        return False
    finally:
        conn.close()