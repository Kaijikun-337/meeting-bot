from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from app.services.user_service import get_students_in_group, get_teacher_for_group
from app.services.attendance_service import mark_attendance, get_lesson_attendance
from app.config import Config
from app.utils.localization import get_text, get_user_language

# Callback data: attend_MEETINGID_DATE
# We also need a state to store temp selections
# Format of temp storage: context.user_data['attendance_draft'] = { student_id: 'present'/'absent' }

async def start_attendance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Teacher clicked 'Mark Attendance'."""
    query = update.callback_query
    await query.answer()
    
    data = query.data.split('_')
    # attend_meetingID_date
    # meeting_id might contain underscores, so be careful
    date_str = data[-1]
    meeting_id = "_".join(data[1:-1])
    
    # 1. Find Meeting to get Group Name
    from app.config import Config
    all_meetings = Config.load_meetings()
    meeting = next((m for m in all_meetings if m['id'] == meeting_id), None)
    
    if not meeting:
        await query.edit_message_text("❌ Error: Meeting config not found.")
        return

    group_name = meeting['group_name']
    
    # 2. Get Students
    students = get_students_in_group(group_name)
    if not students:
        await query.edit_message_text("❌ No students found in this group.")
        return

    # 3. Load existing attendance (if editing)
    existing_record = get_lesson_attendance(meeting_id, date_str)
    
    # 4. Prepare Draft State
    # Default to 'present' if no record
    draft = {}
    for s in students:
        s_id = str(s['chat_id'])
        draft[s_id] = existing_record.get(s_id, 'present')
        
    context.user_data['attendance_draft'] = draft
    context.user_data['attendance_meta'] = {
        'meeting_id': meeting_id, 
        'date': date_str,
        'group': group_name,
        'students': students
    }
    
    await render_attendance_menu(query, context)


async def render_attendance_menu(query, context):
    """Render the checklist keyboard."""
    draft = context.user_data['attendance_draft']
    meta = context.user_data['attendance_meta']
    students = meta['students']
    
    keyboard = []
    
    for s in students:
        s_id = str(s['chat_id'])
        name = s['name']
        status = draft.get(s_id, 'present')
        
        # Toggle Icon
        icon = "✅" if status == 'present' else "❌"
        btn_text = f"{icon} {name}"
        
        # Callback: toggle_STUDENTID
        keyboard.append([InlineKeyboardButton(btn_text, callback_data=f"att_toggle_{s_id}")])
        
    # Submit Button
    keyboard.append([InlineKeyboardButton("💾 Submit Attendance", callback_data="att_submit")])
    
    await query.edit_message_text(
        f"📋 <b>Attendance: {meta['group']}</b>\n📅 {meta['date']}\n\nTap to toggle Present/Absent.",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


async def toggle_student(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Toggle a student's status."""
    query = update.callback_query
    # Don't await answer() here to make it snappy, or use simple answer
    # await query.answer() 
    
    student_id = query.data.replace("att_toggle_", "")
    draft = context.user_data.get('attendance_draft', {})
    
    # Flip status
    current = draft.get(student_id, 'present')
    draft[student_id] = 'absent' if current == 'present' else 'present'
    
    context.user_data['attendance_draft'] = draft
    
    # Re-render (Update the checkmark)
    await render_attendance_menu(query, context)
    await query.answer("Updated")


async def submit_attendance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Save to DB."""
    query = update.callback_query
    await query.answer("Saving...")
    
    draft = context.user_data.get('attendance_draft')
    meta = context.user_data.get('attendance_meta')
    
    if not draft or not meta:
        await query.edit_message_text("❌ Session expired.")
        return

    # Convert draft to lists for batch saving logic?
    # Actually, our service takes IDs and ONE status. 
    # But here we have mixed statuses.
    # So we should group them.
    
    present_ids = [sid for sid, status in draft.items() if status == 'present']
    absent_ids = [sid for sid, status in draft.items() if status == 'absent']
    
    from app.services.attendance_service import mark_attendance
    teacher_id = str(update.effective_chat.id)
    
    # Save Present
    if present_ids:
        mark_attendance(meta['meeting_id'], meta['date'], present_ids, 'present', teacher_id)
        
    # Save Absent
    if absent_ids:
        mark_attendance(meta['meeting_id'], meta['date'], absent_ids, 'absent', teacher_id)
        
    # Summary String
    present_count = len(present_ids)
    absent_count = len(absent_ids)
    
    await query.edit_message_text(
        f"✅ <b>Attendance Saved!</b>\n\n"
        f"🟢 Present: {present_count}\n"
        f"🔴 Absent: {absent_count}",
        parse_mode='HTML'
    )