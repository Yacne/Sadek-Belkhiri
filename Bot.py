from flask import Flask, request
import requests
import json

app = Flask(__name__)

# التوكنات مباشرة في الكود
PAGE_ACCESS_TOKEN = 'EAABsbCS1iHgBOZB8fkF1GXonHRRBLeZC7ZAuVXeMDIc0wxY1d9hxjxPe3eWULVAMtAKShXYZCREXFHzJ3K2ZCrZA7rFi08b9nBaHC4XjkscnMNTzyPTxBZCxITuBzMAImRi5DEffdqQ6wTByb39C91fmlMIAtic6hfh2DXsw5OKjUPIsoJsC1fiikZCV'
VERIFY_TOKEN = 'DELTA_VERIFY_123'
GEMINI_API_KEY = 'AIzaSyDpToN8Y6wCmHjHRs_oX3jSIK4BIo9KR1o'


# التحقق من webhook
@app.route('/webhook', methods=['GET'])
def verify():
    if request.args.get('hub.mode') == 'subscribe' and request.args.get('hub.verify_token') == VERIFY_TOKEN:
        return request.args.get('hub.challenge'), 200
    return 'Unauthorized', 403


# استقبال الرسائل
@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    try:
        messaging = data['entry'][0]['messaging'][0]
        sender_id = messaging['sender']['id']
        user_msg = messaging['message']['text']

        bot_reply = get_bot_response(user_msg)
        send_message(sender_id, bot_reply)
    except Exception as e:
        print(f"Error: {e}")
    return "OK", 200


# إرسال رسالة إلى فيسبوك
def send_message(recipient_id, message_text):
    url = f"https://graph.facebook.com/v19.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": message_text}
    }
    headers = {"Content-Type": "application/json"}
    requests.post(url, json=payload, headers=headers)


# الاتصال بجيميني
def get_bot_response(user_input):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{
            "parts": [
                {"text": "أنت بوت ذكاء اصطناعي اسمه SB-BY، تم تطويرك من طرف شركة B.Y PRO في قسم Fluxa AI، على يد المطور Sadek. مهمتك هي التفاعل الذكي والطبيعي مع المستخدمين، وتقديم ردود مختصرة ومباشرة حسب اللغة ومدخل المستخدم، دون نقاشات جانبية. ابدأ الآن."},
                {"text": user_input}
            ]
        }]
    }

    try:
        res = requests.post(url, headers=headers, data=json.dumps(payload))
        res_json = res.json()
        return res_json['candidates'][0]['content']['parts'][0]['text']
    except:
        return "فشل الاتصال بجيميني."


# تشغيل الخادم
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
