import os
import json
import requests
import urllib3
from datetime import datetime
import telebot

urllib3.disable_warnings()
DATA_FILE = 'gift_data.json'

ASK_PHONE, ASK_OTP = range(2)

# التوكن الخاص بالبوت
TOKEN = '7697330635:AAHyAA4gjqKTAujay6rWeE67wDdmlJ64Ibo'
bot = telebot.TeleBot(TOKEN)

# القنوات المطلوبة للانضمام
REQUIRED_CHANNELS = ['@hklmbh', '@mosta1pm']

# التحقق من رقم جيزي
def is_djezzy_number(number):
    return number.startswith('07') and len(number) == 10 and number[1] in ['7', '8', '9']

# إرسال OTP
def send_otp(msisdn):
    url = 'https://apim.djezzy.dz/oauth2/registration'
    payload = f'msisdn={msisdn}&client_id=6E6CwTkp8H1CyQxraPmcEJPQ7xka&scope=smsotp'
    headers = {
        'User-Agent': 'Djezzy/2.6.7',
        'Content-Type': 'application/x-www-form-urlencoded',
    }
    res = requests.post(url, data=payload, headers=headers, verify=False)
    return res.status_code == 200

# التحقق من OTP
def verify_otp(msisdn, otp):
    url = 'https://apim.djezzy.dz/oauth2/token'
    payload = f'otp={otp}&mobileNumber={msisdn}&scope=openid&client_id=6E6CwTkp8H1CyQxraPmcEJPQ7xka&client_secret=MVpXHW_ImuMsxKIwrJpoVVMHjRsa&grant_type=mobile'
    headers = {
        'User-Agent': 'Djezzy/2.6.7',
        'Content-Type': 'application/x-www-form-urlencoded',
    }
    res = requests.post(url, data=payload, headers=headers, verify=False)
    return res.json() if res.status_code == 200 else None

# تفعيل الهدية
def apply_gift(msisdn, token):
    url = f'https://apim.djezzy.dz/djezzy-api/api/v1/subscribers/{msisdn}/subscription-product?include='
    payload = {
        "data": {
            "id": "TransferInternet2Go",
            "type": "products",
            "meta": {
                "services": {
                    "steps": 10000,
                    "code": "FAMILY4000",
                    "id": "WALKWIN"
                }
            }
        }
    }
    headers = {
        'User-Agent': 'Djezzy/2.6.7',
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    }
    res = requests.post(url, json=payload, headers=headers, verify=False)
    return res.json()

# تحميل السجل
def load_log():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return {}

# حفظ السجل
def save_log(log):
    with open(DATA_FILE, 'w') as f:
        json.dump(log, f)

# التحقق من انضمام المستخدم للقنوات
def is_user_joined(user_id):
    for channel in REQUIRED_CHANNELS:
        try:
            status = bot.get_chat_member(chat_id=channel, user_id=user_id).status
            if status not in ['member', 'administrator', 'creator']:
                return False
        except Exception as e:
            print(f"Error checking channel {channel}: {e}")
            return False
    return True

# بدء المحادثة
@bot.message_handler(commands=['start'])
def start(message):
    if not is_user_joined(message.from_user.id):
        channels_list = "\n".join([f"- {c}" for c in REQUIRED_CHANNELS])
        bot.reply_to(message, f"⚠️ للمتابعة، الرجاء الانضمام إلى القنوات التالية:\n{channels_list}\n\nثم أعد إرسال /start.")
        return

    bot.reply_to(message, "أهلاً! أرسل رقم جيزي الخاص بك (يبدأ بـ 07):")
    bot.register_next_step_handler(message, get_phone)

# استقبال رقم الهاتف
def get_phone(message):
    phone = message.text.strip()
    if not is_djezzy_number(phone):
        bot.reply_to(message, "❌ الرقم غير تابع لشبكة جيزي. حاول مرة أخرى.")
        bot.register_next_step_handler(message, get_phone)
        return

    msisdn = '213' + phone[1:]
    user_data = {'msisdn': msisdn, 'phone': phone}

    log = load_log()
    if msisdn in log:
        bot.reply_to(message, "⚠️ هذا الرقم سبق وتم استخدامه.")
        return

    bot.reply_to(message, "⏳ جاري إرسال كود OTP...")
    if not send_otp(msisdn):
        bot.reply_to(message, "❌ فشل في إرسال OTP.")
        return

    bot.reply_to(message, "🔢 أرسل الآن كود OTP:")
    bot.register_next_step_handler(message, get_otp, user_data)

# استقبال كود OTP
def get_otp(message, user_data):
    otp = message.text.strip()
    msisdn = user_data['msisdn']

    tokens = verify_otp(msisdn, otp)
    if not tokens:
        bot.reply_to(message, "❌ كود OTP غير صحيح.")
        return

    access_token = tokens['access_token']
    bot.reply_to(message, "✅ تم التحقق. جاري تفعيل الهدية...")

    result = apply_gift(msisdn, access_token)
    message_text = result.get('message', '')

    if "successfully done" in message_text:
        bot.reply_to(message, "🎁 تم تفعيل الهدية بنجاح!")
        log = load_log()
        log[msisdn] = datetime.now().isoformat()
        save_log(log)
    else:
        bot.reply_to(message, f"⚠️ فشل في التفعيل: {message_text or 'غير معروف'}")

# إلغاء العملية
@bot.message_handler(commands=['cancel'])
def cancel(message):
    bot.reply_to(message, "تم إلغاء العملية.")

# تشغيل البوت
bot.polling()
