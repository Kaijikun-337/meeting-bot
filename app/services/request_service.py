import uuid
from datetime import datetime, timedelta
from app.database.db import get_connection
from app.config import Config
import pytz


def create_change_request(
    meeting_id: str,
    requester_chat_id: str,
    requester_role: str,
    change_type: str,
    original_date: str,
    new_date: str = None,
    new_hour: int = None,
    new_minute: int = None,
    approvals_needed: int = 1
) -> str:
    """Create a new change request. Returns request_id."""
    conn = get_connection()
    cursor = conn.cursor()
    
    request_id = str(uuid.uuid4())[:8]
    
    # Expires at end of day
    tz = pytz.timezone(Config.TIMEZONE)
    now = datetime.now(tz)
    expires_at = now.replace(hour=23, minute=59, second=59)
    
    try:
        cursor.execute('''
            INSERT INTO change_requests 
            (request_id, meeting_id, requester_chat_id, requester_role, 
             change_type, original_date, new_date, new_hour, new_minute,
             approvals_needed, expires_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (request_id, meeting_id, str(requester_chat_id), requester_role,
              change_type, original_date, new_date, new_hour, new_minute,
              approvals_needed, expires_at.isoformat()))
        conn.commit()
        return request_id
    except Exception as e:
        print(f"❌ Error creating request: {e}")
        return None
    finally:
        conn.close()


def get_request(request_id: str) -> dict:
    """Get request by ID."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM change_requests WHERE request_id = ?', (request_id,))
    row = cursor.fetchone()
    conn.close()
    
    return dict(row) if row else None


def add_approval(request_id: str, approver_chat_id: str, approved: bool) -> dict:
    """Add an approval/rejection to a request. Returns updated request status."""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Check if already voted
        cursor.execute('''
            SELECT * FROM approvals 
            WHERE request_id = ? AND approver_chat_id = ?
        ''', (request_id, str(approver_chat_id)))
        
        if cursor.fetchone():
            return {"error": "already_voted"}
        
        # Add vote
        cursor.execute('''
            INSERT INTO approvals (request_id, approver_chat_id, approved)
            VALUES (?, ?, ?)
        ''', (request_id, str(approver_chat_id), 1 if approved else 0))
        
        if approved:
            # Increment approval count
            cursor.execute('''
                UPDATE change_requests 
                SET approvals_received = approvals_received + 1
                WHERE request_id = ?
            ''', (request_id,))
        else:
            # Rejected - mark request as rejected
            cursor.execute('''
                UPDATE change_requests SET status = 'rejected'
                WHERE request_id = ?
            ''', (request_id,))
            conn.commit()
            return {"status": "rejected"}
        
        # Check if all approvals received
        cursor.execute('''
            SELECT approvals_needed, approvals_received 
            FROM change_requests WHERE request_id = ?
        ''', (request_id,))
        
        row = cursor.fetchone()
        if row['approvals_received'] >= row['approvals_needed']:
            cursor.execute('''
                UPDATE change_requests SET status = 'approved'
                WHERE request_id = ?
            ''', (request_id,))
            conn.commit()
            return {"status": "approved"}
        
        conn.commit()
        return {"status": "pending", "remaining": row['approvals_needed'] - row['approvals_received']}
        
    except Exception as e:
        print(f"❌ Approval error: {e}")
        return {"error": str(e)}
    finally:
        conn.close()


def get_pending_requests_for_user(chat_id: str) -> list:
    """Get pending requests where user needs to vote."""
    # This is complex - we need to find requests where this user hasn't voted
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT cr.* FROM change_requests cr
        WHERE cr.status = 'pending'
        AND cr.request_id NOT IN (
            SELECT request_id FROM approvals WHERE approver_chat_id = ?
        )
        AND cr.expires_at > datetime('now')
    ''', (str(chat_id),))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]


def cleanup_expired_requests():
    """Delete expired requests."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE change_requests 
        SET status = 'expired'
        WHERE status = 'pending' AND expires_at < datetime('now')
    ''')
    
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    
    if affected > 0:
        print(f"🧹 Cleaned up {affected} expired requests")
    
    return affected