import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
from app.config import Config

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]


def get_sheets_client():
    """Get authenticated Google Sheets client."""
    creds = Credentials.from_service_account_file(
        Config.SHEETS_CREDENTIALS_FILE,
        scopes=SCOPES
    )
    return gspread.authorize(creds)


def get_spreadsheet():
    """Get the payments spreadsheet."""
    client = get_sheets_client()
    return client.open_by_key(Config.GOOGLE_SHEETS_ID)


def setup_payments_sheet():
    """Create and format the payments sheet."""
    spreadsheet = get_spreadsheet()
    
    try:
        sheet = spreadsheet.worksheet("Payments")
        # Clear existing data
        sheet.clear()
    except gspread.exceptions.WorksheetNotFound:
        sheet = spreadsheet.add_worksheet(title="Payments", rows=1000, cols=12)
    
    # New headers
    headers = [
        "Date", 
        "Student", 
        "Subject", 
        "Teacher", 
        "Group", 
        "Course Price",  # Total price for course
        "This Payment",  # Current payment
        "Total Paid",    # Running sum
        "Remaining",     # Course Price - Total Paid
        "Status", 
        "Completed"      # Yes/No if fully paid
    ]
    sheet.update('A1:K1', [headers])
    
    # Format headers
    sheet.format('A1:K1', {
        "backgroundColor": {"red": 0.2, "green": 0.4, "blue": 0.6},
        "textFormat": {
            "bold": True,
            "fontSize": 11,
            "foregroundColor": {"red": 1, "green": 1, "blue": 1}
        },
        "horizontalAlignment": "CENTER",
        "verticalAlignment": "MIDDLE"
    })
    
    # Set column widths
    set_column_widths(spreadsheet, sheet)
    
    # Freeze header row
    sheet.freeze(rows=1)
    
    print("✅ Payments sheet set up!")
    return sheet


def set_column_widths(spreadsheet, sheet):
    """Set proper column widths."""
    requests = [
        {"updateDimensionProperties": {
            "range": {"sheetId": sheet.id, "dimension": "COLUMNS", "startIndex": 0, "endIndex": 1},
            "properties": {"pixelSize": 100}, "fields": "pixelSize"
        }},  # Date
        {"updateDimensionProperties": {
            "range": {"sheetId": sheet.id, "dimension": "COLUMNS", "startIndex": 1, "endIndex": 2},
            "properties": {"pixelSize": 140}, "fields": "pixelSize"
        }},  # Student
        {"updateDimensionProperties": {
            "range": {"sheetId": sheet.id, "dimension": "COLUMNS", "startIndex": 2, "endIndex": 3},
            "properties": {"pixelSize": 100}, "fields": "pixelSize"
        }},  # Subject
        {"updateDimensionProperties": {
            "range": {"sheetId": sheet.id, "dimension": "COLUMNS", "startIndex": 3, "endIndex": 4},
            "properties": {"pixelSize": 120}, "fields": "pixelSize"
        }},  # Teacher
        {"updateDimensionProperties": {
            "range": {"sheetId": sheet.id, "dimension": "COLUMNS", "startIndex": 4, "endIndex": 5},
            "properties": {"pixelSize": 90}, "fields": "pixelSize"
        }},  # Group
        {"updateDimensionProperties": {
            "range": {"sheetId": sheet.id, "dimension": "COLUMNS", "startIndex": 5, "endIndex": 6},
            "properties": {"pixelSize": 100}, "fields": "pixelSize"
        }},  # Course Price
        {"updateDimensionProperties": {
            "range": {"sheetId": sheet.id, "dimension": "COLUMNS", "startIndex": 6, "endIndex": 7},
            "properties": {"pixelSize": 100}, "fields": "pixelSize"
        }},  # This Payment
        {"updateDimensionProperties": {
            "range": {"sheetId": sheet.id, "dimension": "COLUMNS", "startIndex": 7, "endIndex": 8},
            "properties": {"pixelSize": 90}, "fields": "pixelSize"
        }},  # Total Paid
        {"updateDimensionProperties": {
            "range": {"sheetId": sheet.id, "dimension": "COLUMNS", "startIndex": 8, "endIndex": 9},
            "properties": {"pixelSize": 90}, "fields": "pixelSize"
        }},  # Remaining
        {"updateDimensionProperties": {
            "range": {"sheetId": sheet.id, "dimension": "COLUMNS", "startIndex": 9, "endIndex": 10},
            "properties": {"pixelSize": 100}, "fields": "pixelSize"
        }},  # Status
        {"updateDimensionProperties": {
            "range": {"sheetId": sheet.id, "dimension": "COLUMNS", "startIndex": 10, "endIndex": 11},
            "properties": {"pixelSize": 90}, "fields": "pixelSize"
        }},  # Completed
    ]
    
    spreadsheet.batch_update({"requests": requests})


def get_teacher_color(teacher_name: str) -> dict:
    """Get color for teacher."""
    return Config.TEACHER_COLORS.get(teacher_name, Config.TEACHER_COLORS["Default"])


def get_total_paid(student_name: str, subject: str, teacher_name: str) -> float:
    """Get total amount already paid by student for specific course."""
    spreadsheet = get_spreadsheet()
    
    try:
        sheet = spreadsheet.worksheet("Payments")
    except gspread.exceptions.WorksheetNotFound:
        return 0.0
    
    records = sheet.get_all_records()
    
    total = 0.0
    for record in records:
        if (record.get('Student', '').lower() == student_name.lower() and
            record.get('Subject', '').lower() == subject.lower() and
            record.get('Teacher', '').lower() == teacher_name.lower() and
            record.get('Status') == '✅ Confirmed'):
            try:
                payment = str(record.get('This Payment', 0)).replace('$', '').replace(',', '')
                total += float(payment)
            except ValueError:
                pass
    
    return total


def add_payment(
    student_name: str,
    subject: str,
    teacher_name: str,
    group: str,
    payment_amount: float,
    status: str = "✅ Confirmed"
) -> bool:
    """Add a payment record to the sheet."""
    spreadsheet = get_spreadsheet()
    
    try:
        sheet = spreadsheet.worksheet("Payments")
    except gspread.exceptions.WorksheetNotFound:
        sheet = setup_payments_sheet()
    
    # Get course price from price list
    course_price = Config.get_course_price(subject, teacher_name, group)
    
    # Get current total paid
    current_paid = get_total_paid(student_name, subject, teacher_name)
    new_total = current_paid + payment_amount
    
    # Calculate remaining
    remaining = max(0, course_price - new_total)
    
    # Check if completed
    completed = "✅ Yes" if new_total >= course_price else "❌ No"
    
    # Prepare row data
    date_str = datetime.now().strftime("%d-%m-%Y")
    row = [
        date_str,
        student_name,
        subject,
        teacher_name,
        group,
        f"${course_price:.2f}",
        f"${payment_amount:.2f}",
        f"${new_total:.2f}",
        f"${remaining:.2f}",
        status,
        completed
    ]
    
    # Add row
    sheet.append_row(row, value_input_option='USER_ENTERED')
    
    # Get row number (last row)
    row_num = len(sheet.get_all_values())
    
    # Format the new row
    format_payment_row(spreadsheet, sheet, row_num, teacher_name, status, completed)
    
    return True


def format_payment_row(spreadsheet, sheet, row_num: int, teacher_name: str, status: str, completed: str):
    """Format a payment row with colors."""
    
    # Teacher color for student name cell
    teacher_color = get_teacher_color(teacher_name)
    
    # Status color
    if status == "✅ Confirmed":
        status_color = {"red": 0.85, "green": 0.95, "blue": 0.85}
    elif status == "❌ Rejected":
        status_color = {"red": 0.95, "green": 0.85, "blue": 0.85}
    else:
        status_color = {"red": 0.98, "green": 0.95, "blue": 0.85}
    
    # Completed color
    if "Yes" in completed:
        completed_color = {"red": 0.7, "green": 0.95, "blue": 0.7}  # Green
    else:
        completed_color = {"red": 0.98, "green": 0.9, "blue": 0.8}  # Light orange
    
    requests = [
        # Student name cell - teacher color
        {
            "repeatCell": {
                "range": {
                    "sheetId": sheet.id,
                    "startRowIndex": row_num - 1,
                    "endRowIndex": row_num,
                    "startColumnIndex": 1,
                    "endColumnIndex": 2
                },
                "cell": {
                    "userEnteredFormat": {
                        "backgroundColor": teacher_color,
                        "textFormat": {"bold": True}
                    }
                },
                "fields": "userEnteredFormat(backgroundColor,textFormat)"
            }
        },
        # Status cell
        {
            "repeatCell": {
                "range": {
                    "sheetId": sheet.id,
                    "startRowIndex": row_num - 1,
                    "endRowIndex": row_num,
                    "startColumnIndex": 9,
                    "endColumnIndex": 10
                },
                "cell": {
                    "userEnteredFormat": {
                        "backgroundColor": status_color,
                        "horizontalAlignment": "CENTER"
                    }
                },
                "fields": "userEnteredFormat(backgroundColor,horizontalAlignment)"
            }
        },
        # Completed cell
        {
            "repeatCell": {
                "range": {
                    "sheetId": sheet.id,
                    "startRowIndex": row_num - 1,
                    "endRowIndex": row_num,
                    "startColumnIndex": 10,
                    "endColumnIndex": 11
                },
                "cell": {
                    "userEnteredFormat": {
                        "backgroundColor": completed_color,
                        "horizontalAlignment": "CENTER",
                        "textFormat": {"bold": True}
                    }
                },
                "fields": "userEnteredFormat(backgroundColor,horizontalAlignment,textFormat)"
            }
        },
        # All cells - border and alignment
        {
            "repeatCell": {
                "range": {
                    "sheetId": sheet.id,
                    "startRowIndex": row_num - 1,
                    "endRowIndex": row_num,
                    "startColumnIndex": 0,
                    "endColumnIndex": 11
                },
                "cell": {
                    "userEnteredFormat": {
                        "verticalAlignment": "MIDDLE",
                        "borders": {
                            "top": {"style": "SOLID", "color": {"red": 0.8, "green": 0.8, "blue": 0.8}},
                            "bottom": {"style": "SOLID", "color": {"red": 0.8, "green": 0.8, "blue": 0.8}},
                            "left": {"style": "SOLID", "color": {"red": 0.8, "green": 0.8, "blue": 0.8}},
                            "right": {"style": "SOLID", "color": {"red": 0.8, "green": 0.8, "blue": 0.8}}
                        }
                    }
                },
                "fields": "userEnteredFormat(verticalAlignment,borders)"
            }
        }
    ]
    
    spreadsheet.batch_update({"requests": requests})


def get_student_payment_summary(student_name: str, subject: str, teacher_name: str) -> dict:
    """Get payment summary for a student's course."""
    course_price = Config.get_course_price(subject, teacher_name, "")
    total_paid = get_total_paid(student_name, subject, teacher_name)
    remaining = max(0, course_price - total_paid)
    completed = total_paid >= course_price
    
    return {
        "course_price": course_price,
        "total_paid": total_paid,
        "remaining": remaining,
        "completed": completed
    }


def get_student_payments(student_name: str) -> list:
    """Get all payments for a student."""
    spreadsheet = get_spreadsheet()
    
    try:
        sheet = spreadsheet.worksheet("Payments")
    except gspread.exceptions.WorksheetNotFound:
        return []
    
    records = sheet.get_all_records()
    
    payments = []
    for record in records:
        if record.get('Student', '').lower() == student_name.lower():
            payments.append(record)
    
    return payments