from app.database.db import get_connection


def get_cached_total_paid(student_name: str, subject: str, teacher: str) -> float:
    """Get total paid from local cache (fast!)."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT COALESCE(SUM(amount), 0) as total
        FROM payments_cache
        WHERE LOWER(student_name) = LOWER(?)
        AND LOWER(subject) = LOWER(?)
        AND LOWER(teacher) = LOWER(?)
        AND status = 'confirmed'
    ''', (student_name, subject, teacher))
    
    row = cursor.fetchone()
    conn.close()
    
    return float(row['total']) if row else 0.0


def add_payment_to_cache(
    student_name: str,
    subject: str,
    teacher: str,
    group_name: str,
    amount: float
) -> bool:
    """Add payment to local cache."""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO payments_cache (student_name, subject, teacher, group_name, amount)
            VALUES (?, ?, ?, ?, ?)
        ''', (student_name, subject, teacher, group_name, amount))
        conn.commit()
        return True
    except Exception as e:
        print(f"❌ Cache error: {e}")
        return False
    finally:
        conn.close()


def get_student_payment_summary_cached(student_name: str, subject: str, teacher: str, course_price: float) -> dict:
    """Get payment summary from cache."""
    total_paid = get_cached_total_paid(student_name, subject, teacher)
    remaining = max(0, course_price - total_paid)
    completed = total_paid >= course_price
    
    return {
        "course_price": course_price,
        "total_paid": total_paid,
        "remaining": remaining,
        "completed": completed
    }