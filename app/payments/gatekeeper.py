from app.database.db import get_connection
from app.utils.localization import TRANSLATIONS
from datetime import datetime

def get_text(key, lang, **kwargs):
    text = TRANSLATIONS.get(key, {}).get(lang, TRANSLATIONS.get(key, {}).get('en', ''))
    return text.format(**kwargs)

async def check_and_send_lesson_link(bot, student_chat_id, group_name, jitsi_link, lang='en'):
    current_month = datetime.now().strftime("%m-%Y")
    
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT amount_due, receipt_status FROM student_payments 
        WHERE student_chat_id = ? AND group_name = ? AND month_year = ? AND is_paid = 0
    """, (str(student_chat_id), group_name, current_month))
    
    unpaid_bill = cur.fetchone()
    cur.close()
    conn.close()
    
    if unpaid_bill:
        amount = unpaid_bill['amount_due']
        receipt_status = unpaid_bill['receipt_status'] if 'receipt_status' in unpaid_bill.keys() else None
        
        if receipt_status == 'pending':
            text = get_text('payment_pending', lang)
        else:
            text = get_text('payment_restricted', lang, amount=amount)
            
        await bot.send_message(chat_id=student_chat_id, text=text, parse_mode='HTML')
        return False
        
    else:
        text = get_text('lesson_starting', lang, link=jitsi_link)
        await bot.send_message(chat_id=student_chat_id, text=text, parse_mode='HTML')
        return True