# app/keep_alive.py
from flask import Flask, request, jsonify
import time
import logging
from app.database.db import get_connection

app = Flask(__name__)
logger = logging.getLogger(__name__)

@app.route('/webhook/click', methods=['POST'])
def click_webhook():
    data = request.form
    action = data.get('action')
    
    if action == 'PREPARE':
        return jsonify({"error": 0, "error_note": "Success"})
    
    elif action == 'COMPLETE':
        trans_id = data.get('merchant_prepare_id')
        param_string = data.get('merchant_trans_id') # Format: chat_id_group_month
        
        try:
            parts = param_string.split('_')
            if len(parts) >= 3:
                month_year = parts[-1]
                group_name = parts[-2]
                student_chat_id = "_".join(parts[:-2])
                
                conn = get_connection()
                cur = conn.cursor()
                cur.execute("""
                    UPDATE student_payments 
                    SET is_paid = 1, click_transaction_id = ?, paid_at = CURRENT_TIMESTAMP
                    WHERE student_chat_id = ? AND group_name = ? AND month_year = ? AND is_paid = 0
                """, (trans_id, student_chat_id, group_name, month_year))
                conn.commit()
                cur.close()
                conn.close()
                return jsonify({"error": 0, "error_note": "Success"})
        except Exception as e:
            logger.error(f"Click webhook error: {e}")
            
        return jsonify({"error": -1, "error_note": "Internal error"})

@app.route('/webhook/payme', methods=['POST'])
def payme_webhook():
    data = request.get_json()
    method = data.get('method')
    params = data.get('params', {})
    
    if method == 'CheckPerformTransaction':
        return jsonify({
            "jsonrpc": "2.0",
            "id": data.get('id'),
            "result": {"allow": True}
        })
        
    elif method == 'CreateTransaction':
        return jsonify({
            "jsonrpc": "2.0",
            "id": data.get('id'),
            "result": {
                "create_time": int(time.time() * 1000),
                "transaction": params.get('id'),
                "state": 1
            }
        })
        
    elif method == 'PerformTransaction':
        trans_id = params.get('id')
        account = params.get('account', {})
        student_chat_id = str(account.get('student_id'))
        group_name = account.get('group')
        month_year = account.get('month')
        
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("""
                UPDATE student_payments 
                SET is_paid = 1, payme_transaction_id = ?, paid_at = CURRENT_TIMESTAMP
                WHERE student_chat_id = ? AND group_name = ? AND month_year = ? AND is_paid = 0
            """, (trans_id, student_chat_id, group_name, month_year))
            conn.commit()
            cur.close()
            conn.close()
            
            return jsonify({
                "jsonrpc": "2.0",
                "id": data.get('id'),
                "result": {
                    "perform_time": int(time.time() * 1000),
                    "transaction": trans_id,
                    "state": 2
                }
            })
        except Exception as e:
            logger.error(f"Payme webhook error: {e}")
            return jsonify({
                "jsonrpc": "2.0",
                "id": data.get('id'),
                "error": {"code": -31099, "message": "Internal error"}
            })
            
    return jsonify({"jsonrpc": "2.0", "id": data.get('id'), "error": {"code": -32601, "message": "Method not found"}})

def keep_alive():
    app.run(host='0.0.0.0', port=8080)

if __name__ == '__main__':
    keep_alive()