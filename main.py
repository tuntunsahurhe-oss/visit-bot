import telebot
import requests
import json
import time
import threading

# --- কনফিগারেশন ---
API_TOKEN = '8328152295:AAEl4ziJj4NAqpnqzpmEXM63F2yczxtoafs'
ADMIN_ID = 6417430059 
ALLOWED_GROUP_ID = -1003765179070  # <--- আপনার মেইন গ্রুপের আইডি এখানে দিন

# ডিফল্ট চ্যানেল লিস্ট (চ্যানেলের ইউজারনেম দিতে হবে @ সহ)
REQUIRED_CHANNELS = ["@FREXY_OFC", "@FREXY_CHATS"] 

bot = telebot.TeleBot(API_TOKEN)

# গ্লোবাল ভেরিয়েবল
is_public_enabled = True  
default_minutes = 5       
auto_visit_threads = {}   

# স্টাইলিশ স্টার্ট মেসেজ (HTML Bold Style)
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

# --- জয়েন ভেরিফিকেশন ফাংশন ---
def is_user_subscribed(user_id):
    for channel in REQUIRED_CHANNELS:
        try:
            status = bot.get_chat_member(channel, user_id).status
            if status in ['left', 'kicked']:
                return False
        except Exception:
            # যদি বট চ্যানেলে এডমিন না থাকে তবে চেক করতে পারবে না
            return False
    return True

# --- অ্যাক্সেস কন্ট্রোল ডেকোরেটর ---
def check_access(message):
    # ১. এডমিন হলে সব এলাউড
    if message.from_user.id == ADMIN_ID:
        return True
    
    # ২. প্রাইভেট চ্যাটে এডমিন ছাড়া কেউ পারবে না
    if message.chat.type == "private":
        bot.reply_to(message, "<b>❌ এই বটটি শুধুমাত্র গ্রুপে ব্যবহারের জন্য।</b>", parse_mode="HTML")
        return False

    # ৩. নির্দিষ্ট গ্রুপে ভেরিফিকেশন ছাড়া কাজ করবে
    if message.chat.id == ALLOWED_GROUP_ID:
        return True
    
    # ৪. অন্য গ্রুপে জয়েন ভেরিফিকেশন চেক
    if not is_user_subscribed(message.from_user.id):
        channels_text = "\n".join(REQUIRED_CHANNELS)
        bot.reply_to(message, f"<b>⚠️ আপনি আমাদের চ্যানেলে জয়েন নেই!\n\nবটটি ব্যবহার করতে নিচের চ্যানেলগুলোতে জয়েন করুন:\n{channels_text}\n\nজয়েন করে আবার কমান্ড দিন।</b>", parse_mode="HTML")
        return False
    
    return True

# --- অটো ভিজিট হেল্পার ---
def run_auto_visit(chat_id, region, uid, minutes):
    user_key = f"{chat_id}_{uid}"
    auto_visit_threads[user_key] = True
    
    try:
        api_url = f"https://visit-api-frexy.onrender.com/visit?uid={uid}&region={region}"
        response = requests.get(api_url)
        if response.status_code == 200:
            data = response.json()
            formatted_json = json.dumps(data, indent=2, ensure_ascii=False)
            bot.send_message(chat_id, f"<b>✅ SUCCESSFUL!</b>\n\n<code>{formatted_json}</code>\n\n<b>👨‍💻 CREDIT: @FREXY_OFC</b>", parse_mode="HTML")
        else:
            bot.send_message(chat_id, "<b>❌ API Error during first hit.</b>", parse_mode="HTML")
    except:
        bot.send_message(chat_id, "<b>⚠️ Error starting auto-visit.</b>", parse_mode="HTML")

    while auto_visit_threads.get(user_key):
        time.sleep(minutes * 60)
        if auto_visit_threads.get(user_key):
            try:
                requests.get(f"https://visit-api-frexy.onrender.com/visit?uid={uid}&region={region}")
            except:
                pass

# --- এডমিন কমান্ডস ---
@bot.message_handler(commands=['addchannel'])
def add_channel(message):
    if message.from_user.id == ADMIN_ID:
        try:
            new_ch = message.text.split()[1]
            if new_ch.startswith("@"):
                REQUIRED_CHANNELS.append(new_ch)
                bot.reply_to(message, f"<b>✅ Channel {new_ch} added.</b>", parse_mode="HTML")
            else:
                bot.reply_to(message, "<b>❌ Please provide channel username with @</b>", parse_mode="HTML")
        except:
            bot.reply_to(message, "<b>Usage: /addchannel @username</b>", parse_mode="HTML")

@bot.message_handler(commands=['remchannel'])
def rem_channel(message):
    if message.from_user.id == ADMIN_ID:
        try:
            ch = message.text.split()[1]
            if ch in REQUIRED_CHANNELS:
                REQUIRED_CHANNELS.remove(ch)
                bot.reply_to(message, f"<b>✅ Channel {ch} removed.</b>", parse_mode="HTML")
        except:
            bot.reply_to(message, "<b>Usage: /remchannel @username</b>", parse_mode="HTML")

@bot.message_handler(commands=['autovisit_on'])
def turn_on(message):
    if message.from_user.id == ADMIN_ID:
        global is_public_enabled
        is_public_enabled = True
        bot.reply_to(message, "<b>✅ Public access turned ON.</b>", parse_mode="HTML")

@bot.message_handler(commands=['autovisit_off'])
def turn_off(message):
    if message.from_user.id == ADMIN_ID:
        global is_public_enabled
        is_public_enabled = False
        bot.reply_to(message, "<b>🚫 Public access turned OFF.</b>", parse_mode="HTML")

# --- ইউজার কমান্ডস ---
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    if not check_access(message): return
    bot.reply_to(message, START_TEXT, parse_mode="HTML")

@bot.message_handler(commands=['visit'])
def fetch_api_data(message):
    if not check_access(message): return
    if not is_public_enabled and message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "<b>🚫 Admin Only Mode Active.</b>", parse_mode="HTML")
        return
    try:
        text_parts = message.text.split()
        if len(text_parts) < 3:
            bot.reply_to(message, "<b>❌ Wrong Format!\nUse: /visit bd 6461428401</b>", parse_mode="HTML")
            return

        region, uid = text_parts[1].lower(), text_parts[2]
        sent_msg = bot.reply_to(message, "<b>⏳ Processing... Please wait.</b>", parse_mode="HTML")

        api_url = f"https://visit-api-frexy.onrender.com/visit?uid={uid}&region={region}"
        response = requests.get(api_url)
        
        if response.status_code == 200:
            data = response.json()
            formatted_json = json.dumps(data, indent=2, ensure_ascii=False)
            final_text = f"<b>✅ SUCCESSFUL!</b>\n\n<code>{formatted_json}</code>\n\n<b>👨‍💻 CREDIT: @FREXY_OFC</b>"
            bot.edit_message_text(final_text, chat_id=sent_msg.chat.id, message_id=sent_msg.message_id, parse_mode="HTML")
        else:
            bot.edit_message_text(f"<b>❌ API Error! Status: {response.status_code}</b>", chat_id=sent_msg.chat.id, message_id=sent_msg.message_id, parse_mode="HTML")
    except Exception as e:
        bot.reply_to(message, f"<b>⚠️ Error: {str(e)}</b>", parse_mode="HTML")

@bot.message_handler(commands=['autovisit'])
def autovisit_cmd(message):
    if not check_access(message): return
    if not is_public_enabled and message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "<b>🚫 Admin Only Mode.</b>", parse_mode="HTML")
        return
    try:
        parts = message.text.split()
        region, uid = parts[1], parts[2]
        minutes = int(parts[3]) if len(parts) > 3 else default_minutes
        threading.Thread(target=run_auto_visit, args=(message.chat.id, region, uid, minutes)).start()
        bot.reply_to(message, f"<b>✅ Auto-visit started for {uid} every {minutes} mins.</b>", parse_mode="HTML")
    except:
        bot.reply_to(message, "<b>❌ Use: /autovisit bd 9909964014 5</b>", parse_mode="HTML")

@bot.message_handler(commands=['stopvisit'])
def stop_visit(message):
    if not check_access(message): return
    try:
        uid = message.text.split()[1]
        user_key = f"{message.chat.id}_{uid}"
        auto_visit_threads[user_key] = False
        bot.reply_to(message, f"<b>🛑 Auto-visit stopped for {uid}.</b>", parse_mode="HTML")
    except:
        bot.reply_to(message, "<b>Use: /stopvisit [UID]</b>", parse_mode="HTML")

# বট চালু করা
print("✅ FREE FIRE VISIT BOT IS NOW ACTIVE!")
bot.infinity_polling()
