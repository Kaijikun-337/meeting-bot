from app.database.db import get_connection

def mark_attendance(meeting_id, date_str, student_ids, status='present', teacher_id=None):
    """
    Mark a list of students as present/absent for a specific lesson.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        for student_id in student_ids:
            # Upsert logic (Update if exists, else Insert)
            cursor.execute("""
                SELECT 1 FROM attendance_log 
                WHERE meeting_id=%s AND date=%s AND student_chat_id=%s
            """, (meeting_id, date_str, str(student_id)))
            
            if cursor.fetchone():
                cursor.execute("""
                    UPDATE attendance_log 
                    SET status=%s, marked_by=%s
                    WHERE meeting_id=%s AND date=%s AND student_chat_id=%s
                """, (status, str(teacher_id), meeting_id, date_str, str(student_id)))
            else:
                cursor.execute("""
                    INSERT INTO attendance_log (meeting_id, date, student_chat_id, status, marked_by)
                    VALUES (%s, %s, %s, %s, %s)
                """, (meeting_id, date_str, str(student_id), status, str(teacher_id)))
                
        conn.commit()
        return True
    except Exception as e:
        print(f"❌ Attendance Error: {e}")
        return False
    finally:
        conn.close()

def get_lesson_attendance(meeting_id, date_str):
    """Get attendance status for a specific lesson."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT student_chat_id, status 
        FROM attendance_log 
        WHERE meeting_id=%s AND date=%s
    """, (meeting_id, date_str))
    
    rows = cursor.fetchall()
    conn.close()
    
    # Convert to dict: {'123': 'present', '456': 'absent'}
    return {row['student_chat_id']: row['status'] for row in rows}

def get_student_attendance_stats(student_id: str):
    """Get total stats and history for a student."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Get all records
    cursor.execute("""
        SELECT meeting_id, date, status 
        FROM attendance_log 
        WHERE student_chat_id = %s
        ORDER BY date DESC
    """, (str(student_id),))
    
    rows = cursor.fetchall()
    conn.close()
    
    history = [dict(row) for row in rows]
    total = len(history)
    present = sum(1 for r in history if r['status'] == 'present')
    
    return {
        "total": total,
        "present": present,
        "percentage": (present / total * 100) if total > 0 else 0,
        "history": history
    }