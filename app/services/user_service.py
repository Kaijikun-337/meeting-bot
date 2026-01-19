from app.database.db import get_connection


def register_user(chat_id: str, name: str, role: str, group_name: str = None) -> bool:
    """Register a new user."""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT OR REPLACE INTO users (chat_id, name, role, group_name)
            VALUES (?, ?, ?, ?)
        ''', (str(chat_id), name, role, group_name))
        conn.commit()
        return True
    except Exception as e:
        print(f"❌ Registration error: {e}")
        return False
    finally:
        conn.close()


def get_user(chat_id: str) -> dict:
    """Get user by chat_id."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM users WHERE chat_id = ?', (str(chat_id),))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return dict(row)
    return None


def is_registered(chat_id: str) -> bool:
    """Check if user is registered."""
    return get_user(chat_id) is not None


def get_user_role(chat_id: str) -> str:
    """Get user role (teacher/student)."""
    user = get_user(chat_id)
    return user['role'] if user else None


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
        WHERE role = 'student' AND group_name = ?
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
        WHERE tg.group_name = ?
    ''', (group_name,))
    
    row = cursor.fetchone()
    conn.close()
    
    return dict(row) if row else None