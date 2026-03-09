import gspread
from oauth2client.service_account import ServiceAccountCredentials
from app.config import Config
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

SCOPE = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive"
]

def get_client():
    """Authenticate and return the gspread client."""
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name(Config.SHEETS_CREDENTIALS_FILE, SCOPE)
        client = gspread.authorize(creds)
        return client
    except Exception as e:
        logger.error(f"❌ Google Sheets Auth Failed: {e}")
        return None

def export_attendance_to_sheet(teacher_name, attendance_data):
    """
    Writes attendance list to a specific Monthly Tab for the teacher.
    Tab Name: "Teacher Name - MMM YYYY" (e.g. "Sardor - Feb 2026")
    """
    client = get_client()
    if not client: return False

    try:
        sheet = client.open_by_key(Config.GOOGLE_SHEETS_ID)
        
        # Determine Tab Name based on the date of the first record
        # (Assuming batch is same month, or we default to Today)
        if attendance_data:
            first_date = attendance_data[0]['date']
            try:
                dt = datetime.strptime(first_date, "%d-%m-%Y")
                month_str = dt.strftime("%b %Y")
            except:
                month_str = datetime.now().strftime("%b %Y")
        else:
            return False

        tab_name = f"{teacher_name} - {month_str}"
        
        # Get/Create Worksheet
        try:
            worksheet = sheet.worksheet(tab_name)
        except gspread.exceptions.WorksheetNotFound:
            worksheet = sheet.add_worksheet(title=tab_name, rows=100, cols=5)
            worksheet.append_row(["Date", "Group", "Student Name", "Status"])
            worksheet.format('A1:D1', {'textFormat': {'bold': True}})

        # Prepare Rows
        rows_to_add = []
        for record in attendance_data:
            rows_to_add.append([
                record['date'],
                record.get('group', ''),
                record['student_name'],
                record['status']
            ])

        if rows_to_add:
            worksheet.append_rows(rows_to_add)
            return True
            
    except Exception as e:
        logger.error(f"❌ Failed to write to Sheet: {e}")
        return False
    return False

def sync_all_attendance_to_sheets():
    """
    One-time script to push ALL DB attendance to Sheets.
    Groups by Teacher and Month automatically.
    """
    from app.database.db import get_connection
    from app.services.user_service import get_user, get_teacher_for_group
    from app.config import Config
    
    print("⏳ Syncing All Attendance...")
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. Fetch All Logs with Student Info
    cursor.execute("""
        SELECT a.date, a.status, a.student_chat_id, u.name as student_name, u.group_name 
        FROM attendance_log a
        JOIN users u ON a.student_chat_id = u.chat_id
    """)
    logs = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    if not logs:
        print("   No attendance logs found.")
        return

    # 2. Group by Teacher (We need to find who taught this group)
    # Map: Teacher -> List of Records
    teacher_batches = {}
    
    # Cache teacher lookups to speed up
    # GroupName -> TeacherName
    teacher_cache = {}
    
    # Pre-load all meetings to map Group -> Teacher? 
    # Or rely on DB `teacher_groups`?
    # Let's rely on DB helper `get_teacher_for_group`
    
    for log in logs:
        group = log['group_name']
        if not group: continue # Skip ungrouped students
        
        # Find Teacher
        if group in teacher_cache:
            t_name = teacher_cache[group]
        else:
            t_obj = get_teacher_for_group(group)
            t_name = t_obj['name'] if t_obj else "Unknown Teacher"
            teacher_cache[group] = t_name
            
        if t_name not in teacher_batches:
            teacher_batches[t_name] = []
            
        teacher_batches[t_name].append({
            'date': log['date'],
            'group': group,
            'student_name': log['student_name'],
            'status': log['status']
        })
        
    # 3. Export
    for teacher, records in teacher_batches.items():
        print(f"   Exporting {len(records)} rows for {teacher}...")
        # Note: This simple export might mix months if we have history.
        # But `export_attendance_to_sheet` creates tab based on FIRST record's date.
        # Ideally we split by month here too.
        
        # Split by month
        by_month = {}
        for r in records:
            m_key = r['date'][3:] # "02-2026"
            if m_key not in by_month: by_month[m_key] = []
            by_month[m_key].append(r)
            
        for month_records in by_month.values():
            export_attendance_to_sheet(teacher, month_records)
            
    print("✅ Sync Complete!")