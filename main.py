import telebot
import requests
import json
import time
import threading
import os
import io
from flask import Flask

# --- কনফিগারেশন ---
API_TOKEN = '8328152295:AAEl4ziJj4NAqpnqzpmEXM63F2yczxtoafs'
ADMIN_ID = 6417430059 
ALLOWED_GROUP_ID = -1003765179070 # আপনার নির্দিষ্ট গ্রুপ আইডি

# ডিফল্ট ২টা চ্যানেল লিঙ্ক
REQUIRED_CHANNELS = ["@FREXY_OFC", "@FREXY_CHATS"] 

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

<b>╭━⟮ 📋 ᴀᴠᴀɪʟᴀʙʟᴇ ᴄᴏᴍᴀɴᴅs !</b>
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
    
    if uid == ADMIN_ID: return True
    
    if message.chat.type == "private":
        bot.reply_to(message, "<b>❌ এই বটটি শুধুমাত্র গ্রুপে ব্যবহারের জন্য।</b>", parse_mode="HTML")
        return False
    
    if cid == ALLOWED_GROUP_ID: return True
    
    if not is_subscribed(uid):
        links = "\n".join(REQUIRED_CHANNELS)
        bot.reply_to(message, f"<b>⚠️ অ্যাক্সেস ডিনাইড!\n\nবটটি ব্যবহার করতে নিচের চ্যানেলগুলোতে জয়েন করুন:</b>\n{links}", parse_mode="HTML")
        return False
    return True

# --- ফরম্যাট ফাংশন (JSON সাজানোর জন্য) ---
def format_visit_response(data):
    output = {
        "level": data.get("level") or data.get("Level"),
        "likes_before": data.get("likes_before") or data.get("Likes Before"),
        "nickname": data.get("nickname") or data.get("Nickname"),
        "sent_success": data.get("sent_success") or data.get("Visits Sent"),
        "status": "Success",
        "total_tried": data.get("total_tried") or data.get("Visits Sent"),
        "uid": data.get("uid") or data.get("UID")
    }
    return json.dumps(output, indent=2, ensure_ascii=False)

# --- JSON ফাইল পাঠানোর হেল্পার ---
def send_json_file(chat_id, json_text, caption, reply_to=None):
    json_file = io.BytesIO(json_text.encode('utf-8'))
    json_file.name = "result.json"
    return bot.send_document(
        chat_id, 
        json_file, 
        caption=caption, 
        parse_mode="HTML", 
        reply_to_message_id=reply_to
    )

# --- অটো ভিজিট প্রসেস ---
def auto_visit_task(chat_id, region, uid, minutes):
    key = f"{chat_id}_{uid}"
    auto_visit_threads[key] = True
    
    try:
        api_url = f"https://visit-api-frexy.onrender.com/visit?uid={uid}&region={region}"
        res = requests.get(api_url).json()
        json_text = format_visit_response(res)
        send_json_file(
            chat_id, 
            json_text, 
            f"<b>✅ AUTO VISIT ACTIVE!</b>\n\n<b>👨‍💻 @FREXY_OFC</b>"
        )
    except: pass

    while auto_visit_threads.get(key):
        time.sleep(minutes * 60)
        if not auto_visit_threads.get(key): break
        try: 
            requests.get(f"https://visit-api-frexy.onrender.com/visit?uid={uid}&region={region}")
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
            json_text = format_visit_response(response.json())
            # Processing মেসেজ ডিলিট করে JSON ফাইল পাঠাও
            bot.delete_message(msg.chat.id, msg.message_id)
            send_json_file(
                msg.chat.id, 
                json_text, 
                f"<b>✅ SUCCESSFUL!</b>\n\n<b>👨‍💻 @FREXY_OFC</b>", 
                reply_to=message.message_id
            )
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
    threading.Thread(target=lambda: bot.infinity_polling(timeout=20, long_polling_timeout=5)).start()
    print("✅ BOT STARTED WITH JSON FILE OUTPUT!")
    run_flask()
