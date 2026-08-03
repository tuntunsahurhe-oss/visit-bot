import telebot
import requests
import json
import time
import threading
import os
from flask import Flask

# --- কনফিগারেশন ---
API_TOKEN = '8328152295:AAEl4ziJj4NAqpnqzpmEXM63F2yczxtoafs'
ADMIN_ID = 6417430059 
ALLOWED_GROUP_ID = -1003765179070 

# ডিফল্ট চ্যানেল লিঙ্ক
REQUIRED_CHANNELS = ["@FREXY_OFC"] 

bot = telebot.TeleBot(API_TOKEN)
server = Flask(__name__)

# --- Render Port Fix (Flask) ---
@server.route('/')
def home():
    return "Bot is running online!", 200

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    server.run(host='0.0.0.0', port=port)

# --- গ্লোবাল ভেরিয়েবল ---
auto_visit_threads = {}   

# স্টাইলিশ স্টার্ট মেসেজ
START_TEXT = """
<b>╭━━━━━━━━━━━━━━━━✪</b>
<b>│🎮 ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ ꜰʀᴇᴇꜰɪʀᴇ ʙᴏᴛ!</b>
<b>╰━━━━━━━━━━━━━━━━✪</b>

<b>╭━⟮ ✦ ✨ ꜰᴇᴀᴛᴜʀᴇs ✦ ⟯</b>
<b>│❤️ ᴘʀᴏꜰɪʟᴇ ᴠɪsɪᴛ / ᴠɪsɪᴛ</b>
<b>│⏳ ᴀᴜᴛᴏ ᴠɪsɪᴛ ꜱʏꜱᴛᴇᴍ</b>
<b>╰━━━━━━━━━━━━━━━✪</b>

<b>╭━⟮ 📋 ᴀᴠᴀɪʟᴀʙʟᴇ ᴄᴏᴍᴍᴀɴᴅs !</b>
<b>│• ꜱᴇɴᴅ ᴘʀᴏꜰɪʟᴇ ᴠɪsɪᴛꜱ</b>
<b>│• ╰ᐅ /visit [REGION] [UID]</b>
<b>│• ╰ᐅ /autovisit [REGION] [UID] [MINS]</b>
<b>╰━━━━━━━━━━━━━━━✪</b>
<b>👨‍💻 CREDIT @FREXY_OFC</b>
"""

# --- জয়েন চেক ফাংশন ---
def is_subscribed(user_id):
    for ch in REQUIRED_CHANNELS:
        try:
            status = bot.get_chat_member(ch, user_id).status
            if status in ['left', 'kicked']: return False
        except: return False
    return True

# --- অ্যাক্সেস কন্ট্রোল ---
def has_access(message):
    uid = message.from_user.id
    if uid == ADMIN_ID: return True
    
    if message.chat.type == "private":
        bot.reply_to(message, "<b>❌ এই বটটি শুধুমাত্র গ্রুপে ব্যবহারের জন্য।</b>", parse_mode="HTML")
        return False
    
    if message.chat.id != ALLOWED_GROUP_ID:
        bot.reply_to(message, "<b>❌ এই গ্রুপে বটটি ব্যবহারের অনুমতি নেই।</b>", parse_mode="HTML")
        return False

    if not is_subscribed(uid):
        links = "\n".join(REQUIRED_CHANNELS)
        bot.reply_to(message, f"<b>⚠️ অ্যাক্সেস ডিনাইড!\n\nবটটি ব্যবহার করতে নিচের চ্যানেলগুলোতে জয়েন করুন:</b>\n{links}", parse_mode="HTML")
        return False
    return True

# --- নরমাল টেক্সট ফরম্যাট ফাংশন (Bold Font) ---
def format_to_normal_text(data):
    """
    API ডাটাকে নরমাল বোল্ড টেক্সট হিসেবে সাজায়
    """
    uid = data.get("uid") or data.get("UID") or "N/A"
    nickname = data.get("nickname") or data.get("Nickname") or "Unknown"
    level = data.get("level") or data.get("Level") or "0"
    likes_before = data.get("likes_before") or data.get("Likes Before") or "0"
    visits_sent = data.get("sent_success") or data.get("Visits Sent") or "0"

    text = (
        f"<b>👤 PLAYER NAME: {nickname}</b>\n"
        f"<b>🆔 PLAYER UID: {uid}</b>\n"
        f"<b>📈 PLAYER LEVEL: {level}</b>\n"
        f"<b>❤️ LIKES BEFORE: {likes_before}</b>\n"
        f"<b>✅ VISITS SENT: {visits_sent}</b>\n"
        f"<b>🕒 TIME: {time.strftime('%I:%M %p')}</b>\n"
        f"<b>👨‍💻 BY: @FREXY_OFC</b>"
    )
    return text

# --- অটো ভিজিট প্রসেস ---
def auto_visit_task(chat_id, region, uid, minutes):
    key = f"{chat_id}_{uid}"
    auto_visit_threads[key] = True
    
    while auto_visit_threads.get(key):
        try:
            api_url = f"https://visit-api-frexy.onrender.com/visit?uid={uid}&region={region}"
            res = requests.get(api_url).json()
            formatted_msg = format_to_normal_text(res)
            
            bot.send_message(
                chat_id, 
                f"<b>🚀 AUTO VISIT UPDATE</b>\n\n{formatted_msg}", 
                parse_mode="HTML"
            )
        except:
            pass
        
        time.sleep(minutes * 60)

# --- কমান্ড হ্যান্ডলার ---
@bot.message_handler(commands=['start', 'help'])
def start_cmd(message):
    if has_access(message):
        bot.reply_to(message, START_TEXT, parse_mode="HTML")

@bot.message_handler(commands=['visit'])
def visit_cmd(message):
    if not has_access(message): return
    try:
        parts = message.text.split()
        if len(parts) < 3:
            bot.reply_to(message, "<b>❌ সঠিক নিয়ম: /visit bd 123456</b>", parse_mode="HTML")
            return
            
        region, uid = parts[1].lower(), parts[2]
        msg = bot.reply_to(message, "<b>⏳ দয়া করে অপেক্ষা করুন...</b>", parse_mode="HTML")
        
        response = requests.get(f"https://visit-api-frexy.onrender.com/visit?uid={uid}&region={region}")
        
        if response.status_code == 200:
            formatted_msg = format_to_normal_text(response.json())
            bot.edit_message_text(
                f"<b>🚀 VISIT SUCCESSFUL!</b>\n\n{formatted_msg}", 
                chat_id=msg.chat.id, 
                message_id=msg.message_id, 
                parse_mode="HTML"
            )
        else:
            bot.edit_message_text("<b>❌ এপিআই সার্ভার ত্রুটি! আবার চেষ্টা করুন।</b>", chat_id=msg.chat.id, message_id=msg.message_id, parse_mode="HTML")
            
    except Exception as e:
        bot.reply_to(message, f"<b>⚠️ সমস্যা হয়েছে: {str(e)}</b>", parse_mode="HTML")

@bot.message_handler(commands=['autovisit'])
def autovisit_cmd(message):
    if not has_access(message): return
    try:
        p = message.text.split()
        if len(p) < 3:
            bot.reply_to(message, "<b>❌ ব্যবহার বিধি: /autovisit bd 123 5</b>", parse_mode="HTML")
            return
            
        region, uid = p[1], p[2]
        mins = int(p[3]) if len(p) > 3 else 5
        
        threading.Thread(target=auto_visit_task, args=(message.chat.id, region, uid, mins), daemon=True).start()
        bot.reply_to(message, f"<b>✅ অটো-ভিজিট শুরু হয়েছে!\n🆔 UID: {uid}\n⏱ প্রতি {mins} মিনিট পর পর।</b>", parse_mode="HTML")
    except:
        bot.reply_to(message, "<b>❌ ভুল ইনপুট!</b>", parse_mode="HTML")

@bot.message_handler(commands=['stopvisit'])
def stop_cmd(message):
    try:
        uid = message.text.split()[1]
        key = f"{message.chat.id}_{uid}"
        if key in auto_visit_threads:
            auto_visit_threads[key] = False
            bot.reply_to(message, f"<b>🛑 অটো-ভিজিট বন্ধ করা হয়েছে: {uid}</b>", parse_mode="HTML")
        else:
            bot.reply_to(message, "<b>❌ এই আইডিতে কোনো অটো-ভিজিট চালু নেই।</b>", parse_mode="HTML")
    except:
        bot.reply_to(message, "<b>❌ ব্যবহার বিধি: /stopvisit 123456</b>", parse_mode="HTML")

# --- রানার ---
if __name__ == '__main__':
    threading.Thread(target=run_flask).start()
    print("✅ BOT STARTED WITH NORMAL BOLD TEXT FORMAT!")
    bot.infinity_polling()
