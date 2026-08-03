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

# ডিফল্ট চ্যানেল লিস্ট
REQUIRED_CHANNELS = ["@FREXY_OFC", "@FREXY_CHATS"] 

bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)

# --- রেন্ডার পোর্ট ফিক্স (Flask Server) ---
@app.route('/')
def home():
    return "Bot is running perfectly!"

def run_web_server():
    # Render অটোমেটিক পোর্ট নম্বর দেয়, সেটি রিসিভ করা
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- গ্লোবাল ভেরিয়েবল ---
is_public_enabled = True  
default_minutes = 5       
auto_visit_threads = {}   

# স্টাইলিশ স্টার্ট মেসেজ (HTML Style)
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

# --- জয়েন ভেরিফিকেশন ---
def is_user_subscribed(user_id):
    for channel in REQUIRED_CHANNELS:
        try:
            status = bot.get_chat_member(channel, user_id).status
            if status in ['left', 'kicked']:
                return False
        except:
            return False 
    return True

# --- অ্যাক্সেস কন্ট্রোল ---
def check_access(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    if user_id == ADMIN_ID: return True
    
    if message.chat.type == "private":
        bot.reply_to(message, "<b>❌ এই বটটি শুধুমাত্র গ্রুপে ব্যবহারের জন্য।</b>", parse_mode="HTML")
        return False
    
    if chat_id == ALLOWED_GROUP_ID: return True
    
    if not is_user_subscribed(user_id):
        ch_list = "\n".join(REQUIRED_CHANNELS)
        bot.reply_to(message, f"<b>⚠️ অ্যাক্সেস ডিনাইড!\n\nবটটি ব্যবহার করতে নিচের চ্যানেলগুলোতে জয়েন করুন:</b>\n{ch_list}\n\n<b>জয়েন করে আবার কমান্ড দিন।</b>", parse_mode="HTML")
        return False
    
    return True

# --- অটো ভিজিট লজিক ---
def run_auto_visit(chat_id, region, uid, minutes):
    user_key = f"{chat_id}_{uid}"
    auto_visit_threads[user_key] = True
    
    try:
        api_url = f"https://visit-api-frexy.onrender.com/visit?uid={uid}&region={region}"
        res = requests.get(api_url).json()
        bot.send_message(chat_id, f"<b>✅ AUTO VISIT STARTED!</b>\n\n<code>{json.dumps(res, indent=2)}</code>", parse_mode="HTML")
    except: pass

    while auto_visit_threads.get(user_key):
        time.sleep(minutes * 60)
        if not auto_visit_threads.get(user_key): break
        try: requests.get(f"https://visit-api-frexy.onrender.com/visit?uid={uid}&region={region}")
        except: pass

# --- এডমিন কমান্ডস ---
@bot.message_handler(commands=['addchannel'])
def add_ch(message):
    if message.from_user.id == ADMIN_ID:
        try:
            ch = message.text.split()[1]
            REQUIRED_CHANNELS.append(ch)
            bot.reply_to(message, f"<b>✅ Added: {ch}</b>", parse_mode="HTML")
        except: bot.reply_to(message, "<b>Usage: /addchannel @user</b>", parse_mode="HTML")

@bot.message_handler(commands=['remchannel'])
def rem_ch(message):
    if message.from_user.id == ADMIN_ID:
        try:
            ch = message.text.split()[1]
            if ch in REQUIRED_CHANNELS:
                REQUIRED_CHANNELS.remove(ch)
                bot.reply_to(message, f"<b>✅ Removed: {ch}</b>", parse_mode="HTML")
        except: bot.reply_to(message, "<b>Usage: /remchannel @user</b>", parse_mode="HTML")

# --- ইউজার কমান্ডস ---
@bot.message_handler(commands=['start', 'help'])
def start(message):
    if check_access(message):
        bot.reply_to(message, START_TEXT, parse_mode="HTML")

@bot.message_handler(commands=['visit'])
def visit(message):
    if not check_access(message): return
    if not is_public_enabled and message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "<b>🚫 Admin Only Mode!</b>", parse_mode="HTML")
        return
    try:
        parts = message.text.split()
        region, uid = parts[1].lower(), parts[2]
        wait = bot.reply_to(message, "<b>⏳ Processing...</b>", parse_mode="HTML")
        
        api_url = f"https://visit-api-frexy.onrender.com/visit?uid={uid}&region={region}"
        data = requests.get(api_url).json()
        formatted = json.dumps(data, indent=2, ensure_ascii=False)
        
        bot.edit_message_text(f"<b>✅ SUCCESSFUL!</b>\n\n<code>{formatted}</code>\n\n<b>👨‍💻 @FREXY_OFC</b>", chat_id=wait.chat.id, message_id=wait.message_id, parse_mode="HTML")
    except:
        bot.reply_to(message, "<b>❌ Use: /visit bd 123456</b>", parse_mode="HTML")

@bot.message_handler(commands=['autovisit'])
def autov(message):
    if not check_access(message): return
    try:
        parts = message.text.split()
        region, uid = parts[1], parts[2]
        mins = int(parts[3]) if len(parts) > 3 else default_minutes
        threading.Thread(target=run_auto_visit, args=(message.chat.id, region, uid, mins)).start()
        bot.reply_to(message, f"<b>✅ Auto-visit set for {uid}</b>", parse_mode="HTML")
    except:
        bot.reply_to(message, "<b>❌ Use: /autovisit bd 123 5</b>", parse_mode="HTML")

@bot.message_handler(commands=['stopvisit'])
def stopv(message):
    try:
        uid = message.text.split()[1]
        auto_visit_threads[f"{message.chat.id}_{uid}"] = False
        bot.reply_to(message, f"<b>🛑 Stopped for {uid}</b>", parse_mode="HTML")
    except: pass

# --- মেইন রানার ---
if __name__ == '__main__':
    # ১. ওয়েব সার্ভার আলাদা থ্রেডে চালানো (Render Port Fix এর জন্য)
    threading.Thread(target=run_web_server, daemon=True).start()
    
    # ২. টেলিগ্রাম বট শুরু করা
    print("✅ BOT IS ACTIVE AND PORT IS BINDED!")
    bot.infinity_polling()
