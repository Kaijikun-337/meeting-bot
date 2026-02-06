import uuid
from datetime import datetime, timedelta
from app.database.db import get_connection
from app.config import Config
import pytz

# NOTE: We do NOT import create_lesson_override at the top to avoid Circular Import errors.
# We import it inside the function where it is used.

def create_change_request(requester_id, meeting_id, original_date, change_type, new_date=None, new_hour=None, new_minute=None, approvals_needed=1):
    """Create a new change request in the DB."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Create unique request ID
    req_uid = str(uuid.uuid4())[:8]
    
    # Calculate expiry (24 hours from now)
    # Convert to ISO string for DB compatibility
    expires_at = (datetime.now() + timedelta(hours=24)).strftime("%Y-%m-%d %H:%M:%S")
    
    try:
        cursor.execute("""
            INSERT INTO change_requests 
            (request_id, meeting_id, requester_chat_id, change_type, original_date, new_date, new_hour, new_minute, approvals_needed, approvals_received, status, expires_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 0, 'pending', %s)
        """, (req_uid, meeting_id, str(requester_id), change_type, original_date, new_date, new_hour, new_minute, approvals_needed, expires_at))
        
        conn.commit()
        return req_uid
    except Exception as e:
        print(f"❌ Error creating request: {e}")
        return None
    finally:
        conn.close()
        
def get_request_by_uid(request_uid):
    """Get request details."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM change_requests WHERE request_id = %s", (request_uid,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def cast_vote(request_uid, voter_id, vote_val):
    conn = get_connection()
    cursor = conn.cursor()
    
    # Import here to avoid circular dependency
    from app.services.lesson_service import create_lesson_override
    
    try:
        # 1. Check if already voted
        cursor.execute("SELECT 1 FROM approvals WHERE request_id = %s AND approver_chat_id = %s", (request_uid, str(voter_id)))
        if cursor.fetchone():
            return False, False, None
            
        # 2. Record vote
        cursor.execute("""
            INSERT INTO approvals (request_id, approver_chat_id, approved)
            VALUES (%s, %s, %s)
        """, (request_uid, str(voter_id), vote_val))
        
        # 3. IF REJECTED
        if vote_val == 0:
            cursor.execute("UPDATE change_requests SET status = 'rejected' WHERE request_id = %s", (request_uid,))
            conn.commit()
            return True, True, get_request_by_uid(request_uid)
            
        # 4. IF APPROVED -> Increment & Check
        cursor.execute("""
            UPDATE change_requests 
            SET approvals_received = approvals_received + 1 
            WHERE request_id = %s
        """, (request_uid,))
        
        # --- FIX IS HERE: Get the FRESH count ---
        cursor.execute("SELECT * FROM change_requests WHERE request_id = %s", (request_uid,))
        req = dict(cursor.fetchone())
        
        needed = req['approvals_needed']
        received = req['approvals_received']
        
        if received >= needed:
            cursor.execute("UPDATE change_requests SET status = 'approved' WHERE request_id = %s", (request_uid,))
            
            create_lesson_override(
                req['meeting_id'], req['original_date'], req['change_type'],
                req['new_date'], req['new_hour'], req['new_minute']
            )
            conn.commit()
            
            # Fetch final state to return 'approved' status
            req['status'] = 'approved' 
            return True, True, req
            
        conn.commit()
        return True, False, req
            
    except Exception as e:
        print(f"Error casting vote: {e}")
        return False, False, None
    finally:
        conn.close()

def cleanup_expired_requests():
    """Delete expired requests."""
    conn = get_connection()
    cursor = conn.cursor()
    
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    try:
        cursor.execute('''
            UPDATE change_requests 
            SET status = 'expired'
            WHERE status = 'pending' AND expires_at < %s
        ''', (now_str,))
        
        affected = cursor.rowcount
        conn.commit()
        
        if affected > 0:
            print(f"🧹 Cleaned up {affected} expired requests")
        
        return affected
    except Exception as e:
        print(f"Cleanup error: {e}")
        return 0
    finally:
        conn.close()