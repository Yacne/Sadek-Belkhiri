import requests
import re
import telebot
import json
import time
from colorama import Fore, Style, init

# التوكن مباشرة داخل السكربت
bot_token = "8181551938:AAFPAg2sehMLoQ9f34_uuL8tDCkzd4hDraU"

init(autoreset=True)

bot = telebot.TeleBot(bot_token)

BASE_URL = "https://apim.djezzy.dz/djezzy-api/api/v1/subscribers/"
HEADERS = {
    "content-type": "application/x-www-form-urlencoded",
    "User-Agent": "Djezzy/2.6.7"
}

# إرسال رمز OTP
def send_otp(num):
    data = f'msisdn=213{num}&client_id=6E6CwTkp8H1CyQxraPmcEJPQ7xka&scope=smsotp'
    try:
        response = requests.post("https://apim.djezzy.dz/oauth2/registration", data=data, headers=HEADERS)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error sending OTP: {e}")
        return None

# التحقق من رمز OTP
def verify_otp(num, otp):
    data = {
        "scope": "openid",
        "client_secret": "MVpXHW_ImuMsxKIwrJpoVVMHjRsa",
        "client_id": "6E6CwTkp8H1CyQxraPmcEJPQ7xka",
        "otp": otp,
        "mobileNumber": f"213{num}",
        "grant_type": "mobile"
    }
    try:
        response = requests.post("https://apim.djezzy.dz/oauth2/token", data=data, headers=HEADERS)
        response.raise_for_status()
        json_response = response.json()
        return json_response.get("access_token"), json_response.get("id_token")
    except requests.RequestException as e:
        print(f"Error verifying OTP: {e}")
        return None, None

# تفعيل الإنترنت باستخدام الكود
def activate_reward(num, access_token, id_token, code):
    data = {
        "data": {
            "id": "GIFTWALKWIN",
            "type": "products",
            "meta": {
                "services": {
                    "steps": 25000,
                    "code": code,
                    "id": "WALKWIN"
                }
            }
        }
    }
    headers = {
        "Authorization": f"Bearer {access_token}",
        "scope": "openid",
        "id-token": id_token,
        "User-Agent": "Djezzy/2.6.7"
    }
    try:
        response = requests.post(f"{BASE_URL}213{num}/subscription-product?include=", json=data, headers=headers)
        return response.json()
    except requests.RequestException as e:
        print(f"Error activating reward: {e}")
        return None

# بدء المحادثة
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id,  "مرحباً! 🚀\nيرجى إدخال رقم هاتفك (10 أرقام فقط) لمواصلة العملية:")

# معالجة الرسائل
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    if message.text.isdigit() and len(message.text) == 10:
        num = re.sub('^0', '', message.text)
        response = send_otp(num)
        if response:
            bot.send_message(message.chat.id, f"✅ تم إرسال رمز التحقق إلى {num}. يرجى إدخال الرمز:")
            bot.register_next_step_handler(message, verify_otp_and_activate_reward, num)
        else:
            bot.send_message(message.chat.id, "❌ حدث خطأ أثناء إرسال رمز التحقق. حاول مرة أخرى.")
    else:
        bot.send_message(message.chat.id,   "⚠️ يرجى إدخال رقم هاتف صحيح يتكون من 10 أرقام فقط.")

# التحقق من OTP وتفعيل المكافأة
def verify_otp_and_activate_reward(message, num):
    otp = message.text
    access_token, id_token = verify_otp(num, otp)
    if not access_token or not id_token:
        bot.send_message(message.chat.id, "❌ خطأ في رمز التحقق. حاول مرة أخرى.")
    else:
        bot.send_message(message.chat.id, "🔄 جاري التحقق من الأكواد...")
        codes = ["GIFTWALKWIN1GO", "GIFTWALKWIN2GO"]  # أكواد 1 جيغا و 2 جيغا
        success = False
        valid_code = None
        for code in codes:
            response = activate_reward(num, access_token, id_token, code)
            print(f"Testing code: {code}")
            print("Response:", response)

            if response and "object" not in response:
                success = True
                valid_code = code
                break
            elif response and "error" in response:
                error_message = response.get("error", {}).get("message", "❌ لم يتم التفعيل.")
                if "week" in error_message:
                    bot.send_message(message.chat.id, "❌ لا يمكن التفعيل الآن: لم يكتمل الأسبوع.")
                elif "day" in error_message:
                    bot.send_message(message.chat.id, "❌ لا يمكن التفعيل الآن: لم يكتمل اليوم.")
                else:
                    bot.send_message(message.chat.id, error_message)
            time.sleep(1)  # تأخير 1 ثانية بين المحاولات

        if success:
            # رسالة التفعيل الناجح مع تفاصيل المكافأة
            bot.send_message(message.chat.id, f"✅ تم تفعيل الإنترنت باستخدام الكود {valid_code} بنجاح! \n📅 المكافأة صالحة حتى 28/12/2024 الساعة 11:09:30 \n💻 لتحميل التطبيق: http://internet.djezzy.dz/home.php")
        else:
            bot.send_message(message.chat.id, "❌ لم يتم العثور على كود صالح. حاول مرة أخرى لاحقاً.")

if __name__ == "__main__":
    if bot.polling:
        print(Fore.GREEN + Style.BRIGHT + "تم تشغيل البوت☑️")
    else:
        print(Fore.RED + Style.BRIGHT + "لم يتم تشغيل البوت📺")
    bot.polling()