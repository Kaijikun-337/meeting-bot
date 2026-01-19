import sqlite3
import os
from app.config import Config


def get_connection():
    """Get database connection."""
    conn = sqlite3.connect(Config.DATABASE_FILE)
    conn.row_factory = sqlite3.Row  # Access columns by name
    return conn


def init_database():
    """Create all tables."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            role TEXT NOT NULL,
            group_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Teachers table (links teacher to groups)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS teacher_groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            teacher_chat_id TEXT NOT NULL,
            group_name TEXT NOT NULL,
            subject TEXT,
            UNIQUE(teacher_chat_id, group_name)
        )
    ''')
    
    # Change requests table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS change_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            request_id TEXT UNIQUE NOT NULL,
            meeting_id TEXT NOT NULL,
            requester_chat_id TEXT NOT NULL,
            requester_role TEXT NOT NULL,
            change_type TEXT NOT NULL,
            original_date TEXT NOT NULL,
            new_date TEXT,
            new_hour INTEGER,
            new_minute INTEGER,
            status TEXT DEFAULT 'pending',
            approvals_needed INTEGER DEFAULT 1,
            approvals_received INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP NOT NULL
        )
    ''')
    
    # Approvals tracking
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS approvals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            request_id TEXT NOT NULL,
            approver_chat_id TEXT NOT NULL,
            approved INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(request_id, approver_chat_id)
        )
    ''')
    
    # Lesson overrides (active postponements/cancellations)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS lesson_overrides (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            meeting_id TEXT NOT NULL,
            original_date TEXT NOT NULL,
            override_type TEXT NOT NULL,
            new_date TEXT,
            new_hour INTEGER,
            new_minute INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(meeting_id, original_date)
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ Database initialized")


# Initialize on import
if not os.path.exists(Config.DATABASE_FILE):
    init_database()