import telebot
import requests
import json
import time
import threading
import os
from http.server import HTTPServer, BaseHTTPRequestHandler

# --- কনফিগারেশন (এখানে আপনার তথ্য দিন) ---
API_TOKEN = '8328152295:AAEl4ziJj4NAqpnqzpmEXM63F2yczxtoafs'
ADMIN_ID = 6417430059 
ALLOWED_GROUP_ID = -1003765179070 # <--- আপনার মেইন গ্রুপ আইডি দিন যেখানে ভেরিফিকেশন লাগবে না

# ডিফল্ট চ্যানেল লিস্ট (এডমিন এগুলো পরে পরিবর্তন করতে পারবে)
REQUIRED_CHANNELS = ["@FREXY_OFC", "@FREXY_CHATS"] 

bot = telebot.TeleBot(API_TOKEN)

# --- রেন্ডার পোর্ট ফিক্স (Dummy Server) ---
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running perfectly!")

def run_health_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    server.serve_forever()

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

# --- অ্যাক্সেস ও ভেরিফিকেশন লজিক ---
def is_user_subscribed(user_id):
    for channel in REQUIRED_CHANNELS:
        try:
            status = bot.get_chat_member(channel, user_id).status
            if status in ['left', 'kicked']:
                return False
        except:
            return False # বট চ্যানেলে এডমিন না থাকলে এটি ফলস দিবে
    return True

def check_access(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    # ১. এডমিন হলে সবসময় অ্যাক্সেস পাবে
    if user_id == ADMIN_ID:
        return True
    
    # ২. প্রাইভেট চ্যাটে এডমিন ছাড়া অন্য কেউ এলাউড না
    if message.chat.type == "private":
        bot.reply_to(message, "<b>❌ এই বটটি শুধুমাত্র গ্রুপে ব্যবহারের জন্য। এডমিন ছাড়া প্রাইভেট চ্যাটে এটি কাজ করবে না।</b>", parse_mode="HTML")
        return False
    
    # ৩. নির্দিষ্ট গ্রুপে জয়েন ভেরিফিকেশন লাগবে না
    if chat_id == ALLOWED_GROUP_ID:
        return True
    
    # ৪. অন্য যেকোনো গ্রুপে ২টা চ্যানেলে জয়েন চেক করবে
    if not is_user_subscribed(user_id):
        ch_links = "\n".join(REQUIRED_CHANNELS)
        bot.reply_to(message, f"<b>⚠️ অ্যাক্সেস ডিনাইড!</b>\n\n<b>বটটি ব্যবহার করতে নিচের চ্যানেলগুলোতে জয়েন করুন:</b>\n{ch_links}\n\n<b>জয়েন করার পর আবার ট্রাই করুন।</b>", parse_mode="HTML")
        return False
    
    return True

# --- অটো ভিজিট থ্রেড ---
def run_auto_visit(chat_id, region, uid, minutes):
    user_key = f"{chat_id}_{uid}"
    auto_visit_threads[user_key] = True
    
    # প্রথম হিট
    try:
        api_url = f"https://visit-api-frexy.onrender.com/visit?uid={uid}&region={region}"
        res = requests.get(api_url).json()
        formatted_json = json.dumps(res, indent=2, ensure_ascii=False)
        bot.send_message(chat_id, f"<b>✅ AUTO VISIT STARTED!</b>\n\n<code>{formatted_json}</code>\n\n<b>👨‍💻 CREDIT: @FREXY_OFC</b>", parse_mode="HTML")
    except:
        pass

    while auto_visit_threads.get(user_key):
        time.sleep(minutes * 60)
        if not auto_visit_threads.get(user_key): break
        try:
            requests.get(f"https://visit-api-frexy.onrender.com/visit?uid={uid}&region={region}")
        except:
            pass

# --- এডমিন কমান্ডস ---
@bot.message_handler(commands=['addchannel'])
def add_ch(message):
    if message.from_user.id == ADMIN_ID:
        try:
            new_ch = message.text.split()[1]
            REQUIRED_CHANNELS.append(new_ch)
            bot.reply_to(message, f"<b>✅ Channel {new_ch} Added.</b>", parse_mode="HTML")
        except:
            bot.reply_to(message, "<b>Use: /addchannel @username</b>", parse_mode="HTML")

@bot.message_handler(commands=['remchannel'])
def rem_ch(message):
    if message.from_user.id == ADMIN_ID:
        try:
            ch = message.text.split()[1]
            if ch in REQUIRED_CHANNELS:
                REQUIRED_CHANNELS.remove(ch)
                bot.reply_to(message, f"<b>✅ Channel {ch} Removed.</b>", parse_mode="HTML")
        except:
            bot.reply_to(message, "<b>Use: /remchannel @username</b>", parse_mode="HTML")

@bot.message_handler(commands=['autovisit_on'])
def turn_on(message):
    if message.from_user.id == ADMIN_ID:
        global is_public_enabled
        is_public_enabled = True
        bot.reply_to(message, "<b>✅ Public Access: ON</b>", parse_mode="HTML")

@bot.message_handler(commands=['autovisit_off'])
def turn_off(message):
    if message.from_user.id == ADMIN_ID:
        global is_public_enabled
        is_public_enabled = False
        bot.reply_to(message, "<b>🚫 Public Access: OFF (Admin Only)</b>", parse_mode="HTML")

# --- ইউজার কমান্ডস ---
@bot.message_handler(commands=['start', 'help'])
def welcome(message):
    if check_access(message):
        bot.reply_to(message, START_TEXT, parse_mode="HTML")

@bot.message_handler(commands=['visit'])
def visit_player(message):
    if not check_access(message): return
    if not is_public_enabled and message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "<b>🚫 বর্তমানে শুধুমাত্র এডমিন এই কমান্ড ব্যবহার করতে পারবে।</b>", parse_mode="HTML")
        return
    
    try:
        parts = message.text.split()
        if len(parts) < 3:
            bot.reply_to(message, "<b>❌ ফরম্যাট ভুল!\nসঠিক নিয়ম: /visit bd 6461428401</b>", parse_mode="HTML")
            return
        
        region, uid = parts[1].lower(), parts[2]
        wait_msg = bot.reply_to(message, "<b>⏳ প্রসেসিং হচ্ছে... দয়া করে অপেক্ষা করুন।</b>", parse_mode="HTML")
        
        api_url = f"https://visit-api-frexy.onrender.com/visit?uid={uid}&region={region}"
        response = requests.get(api_url)
        
        if response.status_code == 200:
            formatted_json = json.dumps(response.json(), indent=2, ensure_ascii=False)
            bot.edit_message_text(f"<b>✅ SUCCESSFUL!</b>\n\n<code>{formatted_json}</code>\n\n<b>👨‍💻 CREDIT: @FREXY_OFC</b>", chat_id=wait_msg.chat.id, message_id=wait_msg.message_id, parse_mode="HTML")
        else:
            bot.edit_message_text("<b>❌ API রেসপন্স দিতে পারছে না। পরে চেষ্টা করুন।</b>", chat_id=wait_msg.chat.id, message_id=wait_msg.message_id, parse_mode="HTML")
    except Exception as e:
        bot.reply_to(message, f"<b>⚠️ এরর: {str(e)}</b>", parse_mode="HTML")

@bot.message_handler(commands=['autovisit'])
def auto_visit_cmd(message):
    if not check_access(message): return
    try:
        parts = message.text.split()
        region, uid = parts[1].lower(), parts[2]
        mins = int(parts[3]) if len(parts) > 3 else default_minutes
        
        threading.Thread(target=run_auto_visit, args=(message.chat.id, region, uid, mins)).start()
    except:
        bot.reply_to(message, "<b>❌ সঠিক নিয়ম: /autovisit bd 1234567 5</b>", parse_mode="HTML")

@bot.message_handler(commands=['stopvisit'])
def stop_v(message):
    if not check_access(message): return
    try:
        uid = message.text.split()[1]
        auto_visit_threads[f"{message.chat.id}_{uid}"] = False
        bot.reply_to(message, f"<b>🛑 {uid} এর জন্য অটো-ভিজিট বন্ধ করা হয়েছে।</b>", parse_mode="HTML")
    except:
        bot.reply_to(message, "<b>Use: /stopvisit [UID]</b>", parse_mode="HTML")

# --- রানার ---
if __name__ == '__main__':
    # রেন্ডার পোর্টের জন্য আলাদা থ্রেডে সার্ভার চালানো
    threading.Thread(target=run_health_server, daemon=True).start()
    
    print("✅ FREE FIRE VISIT BOT IS ONLINE!")
    bot.infinity_polling()
