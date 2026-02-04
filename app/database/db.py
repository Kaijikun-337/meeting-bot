import os
import sqlite3
import logging
from contextlib import contextmanager

# Check if we are on Render (Postgres) or Local (SQLite)
DATABASE_URL = os.getenv("DATABASE_URL")

# Try importing psycopg2 (Postgres driver)
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    HAS_POSTGRES = True
except ImportError:
    HAS_POSTGRES = False

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════
# POSTGRES COMPATIBILITY LAYERS
# ═══════════════════════════════════════════════════════════

class SQLiteToPostgresCursor:
    """
    Wrapper to make Postgres behave like SQLite (converts ? to %s).
    """
    def __init__(self, cursor):
        self.cursor = cursor
        self.row_factory = None

    def execute(self, sql, params=None):
        # Convert SQLite syntax (?) to Postgres syntax (%s)
        clean_sql = sql.replace('?', '%s')
        try:
            if params:
                return self.cursor.execute(clean_sql, params)
            return self.cursor.execute(clean_sql)
        except Exception as e:
            logger.error(f"SQL Error: {e} | Query: {clean_sql}")
            raise e

    def fetchone(self):
        return self.cursor.fetchone()

    def fetchall(self):
        return self.cursor.fetchall()
    
    @property
    def rowcount(self):
        return self.cursor.rowcount

    def close(self):
        self.cursor.close()

class ConnectionWrapper:
    """Wraps Postgres connection to look like SQLite connection."""
    def __init__(self, conn):
        self.conn = conn
    
    def cursor(self):
        real_cursor = self.conn.cursor()
        return SQLiteToPostgresCursor(real_cursor)
    
    def commit(self):
        self.conn.commit()
    
    def close(self):
        self.conn.close()

# ═══════════════════════════════════════════════════════════
# CONNECTION FACTORY
# ═══════════════════════════════════════════════════════════

def get_connection():
    """
    Hybrid connection factory:
    - If DATABASE_URL is set -> Returns Postgres connection (Wrapped).
    - If NOT set -> Returns SQLite connection (Standard).
    """
    if DATABASE_URL and HAS_POSTGRES:
        # --- POSTGRES (Cloud) ---
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        return ConnectionWrapper(conn)
    else:
        # --- SQLITE (Local) ---
        # Calculate path relative to this file
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        db_path = os.path.join(base_dir, 'data.db')
        
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn

# ═══════════════════════════════════════════════════════════
# INITIALIZATION
# ═══════════════════════════════════════════════════════════

def init_database():
    """Initialize tables (Handles both SQLite and Postgres syntax)."""
    
    conn = get_connection()
    
    # Determine mode for Primary Keys
    if DATABASE_URL and HAS_POSTGRES:
        # Unwrap for init to avoid '?' issues in CREATE statements
        cursor = conn.conn.cursor() 
        pk_type = "SERIAL PRIMARY KEY"
        print("🚀 Initializing Database: POSTGRES Mode")
    else:
        cursor = conn.cursor()
        pk_type = "INTEGER PRIMARY KEY AUTOINCREMENT"
        print("💻 Initializing Database: SQLITE Mode (Local)")

    # 1. Users
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS users (
            id {pk_type},
            chat_id TEXT UNIQUE,
            name TEXT NOT NULL,
            role TEXT NOT NULL,
            group_name TEXT,
            registration_key TEXT UNIQUE NOT NULL,
            is_active INTEGER DEFAULT 0,
            language TEXT DEFAULT 'en',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            activated_at TIMESTAMP
        )
    """)
    
    # 2. Teacher Groups
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS teacher_groups (
            id {pk_type},
            teacher_chat_id TEXT NOT NULL,
            group_name TEXT NOT NULL,
            subject TEXT,
            UNIQUE(teacher_chat_id, group_name)
        )
    """)
    
    # 3. Pending Teacher Groups
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS pending_teacher_groups (
            id {pk_type},
            registration_key TEXT NOT NULL,
            group_name TEXT NOT NULL,
            subject TEXT,
            UNIQUE(registration_key, group_name)
        )
    """)
    
    # 4. Change Requests
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS change_requests (
            id {pk_type},
            request_id TEXT UNIQUE, 
            meeting_id TEXT NOT NULL,
            requester_chat_id TEXT NOT NULL,
            requester_role TEXT,
            change_type TEXT NOT NULL,
            original_date TEXT NOT NULL,
            new_date TEXT,
            new_hour INTEGER,
            new_minute INTEGER,
            status TEXT DEFAULT 'pending',
            approvals_needed INTEGER DEFAULT 1,
            approvals_received INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP
        )
    """)
    
    # 5. Approvals
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS approvals (
            id {pk_type},
            request_id TEXT NOT NULL,
            approver_chat_id TEXT NOT NULL,
            approved INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(request_id, approver_chat_id)
        )
    """)
    
    # 6. Lesson Overrides (Restored your specific columns)
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS lesson_overrides (
            id {pk_type},
            meeting_id TEXT NOT NULL,
            original_date TEXT NOT NULL,
            override_type TEXT,
            new_date TEXT,
            new_hour INTEGER,
            new_minute INTEGER,
            status TEXT, 
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(meeting_id, original_date)
        )
    """)
    
    # 7. Payments Cache
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS payments_cache (
            id {pk_type},
            student_name TEXT NOT NULL,
            subject TEXT NOT NULL,
            teacher TEXT NOT NULL,
            group_name TEXT,
            amount REAL NOT NULL,
            status TEXT DEFAULT 'confirmed',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 8. Teacher Availability
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS teacher_availability (
            id {pk_type},
            teacher_chat_id TEXT NOT NULL,
            available_date TEXT NOT NULL,
            start_hour INTEGER NOT NULL,
            end_hour INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(teacher_chat_id, available_date)
        )
    """)

    # --- AUTO-FIX FOR LOCAL SQLITE ---
    # Attempt to add columns that might be missing in your local file
    if not (DATABASE_URL and HAS_POSTGRES):
        try:
            cursor.execute("ALTER TABLE lesson_overrides ADD COLUMN override_type TEXT")
            print("🔧 Fixed: Added 'override_type' to lesson_overrides")
        except:
            pass
        
        try:
            cursor.execute("ALTER TABLE lesson_overrides ADD COLUMN status TEXT")
        except:
            pass

    conn.commit()
    conn.close()
    print("✅ Database initialized successfully.")