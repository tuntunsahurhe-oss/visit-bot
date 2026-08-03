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
ALLOWED_GROUP_ID = -1003765179070 # আপনার নির্দিষ্ট গ্রুপ আইডি

# ডিফল্ট ২টা চ্যানেল লিঙ্ক
REQUIRED_CHANNELS = ["@FREXY_OFC", "@YourChannel2"] 

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
is_public_enabled = True  
default_minutes = 5       
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
<b>│• POWERED BY FREXY</b>
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
    cid = message.chat.id
    
    # এডমিন সব জায়গায় পারবে
    if uid == ADMIN_ID: return True
    
    # প্রাইভেট চ্যাটে এডমিন ছাড়া কেউ পারবে না
    if message.chat.type == "private":
        bot.reply_to(message, "<b>❌ এই বটটি শুধুমাত্র গ্রুপে ব্যবহারের জন্য।</b>", parse_mode="HTML")
        return False
    
    # নির্দিষ্ট গ্রুপে ভেরিফিকেশন লাগবে না
    if cid == ALLOWED_GROUP_ID: return True
    
    # অন্য গ্রুপে ২টা চ্যানেল জয়েন চেক
    if not is_subscribed(uid):
        links = "\n".join(REQUIRED_CHANNELS)
        bot.reply_to(message, f"<b>⚠️ অ্যাক্সেস ডিনাইড!\n\nবটটি ব্যবহার করতে নিচের চ্যানেলগুলোতে জয়েন করুন:</b>\n{links}", parse_mode="HTML")
        return False
    return True

# --- অটো ভিজিট প্রসেস ---
def auto_visit_task(chat_id, region, uid, minutes):
    key = f"{chat_id}_{uid}"
    auto_visit_threads[key] = True
    try:
        api_url = f"https://visit-api-frexy.onrender.com/visit?uid={uid}&region={region}"
        data = requests.get(api_url).json()
        # JSON ফরম্যাটে ডাটা তৈরি
        json_output = json.dumps(data, indent=2, ensure_ascii=False)
        bot.send_message(chat_id, f"<b>✅ AUTO VISIT ACTIVE!</b>\n\n<code>{json_output}</code>\n\n<b>👨‍💻 @FREXY_OFC</b>", parse_mode="HTML")
    except: pass

    while auto_visit_threads.get(key):
        time.sleep(minutes * 60)
        if not auto_visit_threads.get(key): break
        try: requests.get(f"https://visit-api-frexy.onrender.com/visit?uid={uid}&region={region}")
        except: pass

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
            bot.reply_to(message, "<b>❌ Use: /visit bd 123456</b>", parse_mode="HTML")
            return
            
        region, uid = parts[1].lower(), parts[2]
        msg = bot.reply_to(message, "<b>⏳ Processing...</b>", parse_mode="HTML")
        
        response = requests.get(f"https://visit-api-frexy.onrender.com/visit?uid={uid}&region={region}")
        if response.status_code == 200:
            # JSON ডাটা সুন্দর করে ফরম্যাট করা
            json_data = json.dumps(response.json(), indent=2, ensure_ascii=False)
            bot.edit_message_text(f"<b>✅ SUCCESSFUL!</b>\n\n<code>{json_data}</code>\n\n<b>👨‍💻 @FREXY_OFC</b>", chat_id=msg.chat.id, message_id=msg.message_id, parse_mode="HTML")
        else:
            bot.edit_message_text("<b>❌ API Error!</b>", chat_id=msg.chat.id, message_id=msg.message_id, parse_mode="HTML")
    except Exception as e:
        bot.reply_to(message, f"<b>⚠️ Error: {str(e)}</b>", parse_mode="HTML")

@bot.message_handler(commands=['autovisit'])
def autovisit_cmd(message):
    if not has_access(message): return
    try:
        p = message.text.split()
        region, uid = p[1], p[2]
        mins = int(p[3]) if len(p) > 3 else default_minutes
        threading.Thread(target=auto_visit_task, args=(message.chat.id, region, uid, mins)).start()
        bot.reply_to(message, f"<b>✅ Auto-visit started for {uid} every {mins} mins.</b>", parse_mode="HTML")
    except:
        bot.reply_to(message, "<b>❌ Format: /autovisit bd 123 5</b>", parse_mode="HTML")

@bot.message_handler(commands=['stopvisit'])
def stop_cmd(message):
    try:
        uid = message.text.split()[1]
        auto_visit_threads[f"{message.chat.id}_{uid}"] = False
        bot.reply_to(message, f"<b>🛑 Stopped auto-visit for: {uid}</b>", parse_mode="HTML")
    except: pass

# --- এডমিন কমান্ড (চ্যানেল ম্যানেজমেন্ট) ---
@bot.message_handler(commands=['addchannel'])
def add_ch(message):
    if message.from_user.id == ADMIN_ID:
        try:
            ch = message.text.split()[1]
            REQUIRED_CHANNELS.append(ch)
            bot.reply_to(message, f"<b>✅ Channel Added: {ch}</b>", parse_mode="HTML")
        except: pass

# --- রানার ---
if __name__ == '__main__':
    # ১. টেলিগ্রাম বট ব্যাকগ্রাউন্ড থ্রেডে
    threading.Thread(target=lambda: bot.infinity_polling(timeout=20, long_polling_timeout=5)).start()
    
    # ২. ফ্লাস্ক সার্ভার মেইন থ্রেডে (Render Port Fix)
    print("✅ BOT STARTED WITH JSON OUTPUT & PORT BINDING!")
    run_flask()
