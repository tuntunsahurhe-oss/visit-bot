import telebot
import requests
import json
import time
import threading

# --- কনফিগারেশন ---
API_TOKEN = '8328152295:AAEl4ziJj4NAqpnqzpmEXM63F2yczxtoafs'
ADMIN_ID = 6417430059  # <--- এখানে আপনার টেলিগ্রাম আইডি দিন

bot = telebot.TeleBot(API_TOKEN)

# গ্লোবাল ভেরিয়েবল
is_public_enabled = True  
default_minutes = 5       
auto_visit_threads = {}   

# স্টাইলিশ স্টার্ট মেসেজ (আপনার দেওয়াটাই হুবহু রাখা হয়েছে)
START_TEXT = """
╭━━━━━━━━━━━━━━━━✪
│🎮 ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ ꜰʀᴇᴇꜰɪʀᴇ ʙᴏᴛ!
╰━━━━━━━━━━━━━━━━✪

╭━⟮ ✦ ✨ ꜰᴇᴀᴛᴜʀᴇs ✦ ⟯
│❤️ ᴘʀᴏꜰɪʟᴇ ᴠɪsɪᴛ / ᴠɪsɪᴛ
│⏳ ᴀᴜᴛᴏ ᴠɪsɪᴛ ꜱʏꜱᴛᴇᴍ
╰━━━━━━━━━━━━━━━✪

╭━⟮ 📋 ᴀᴠᴀɪʟᴀʙʟᴇ ᴄᴏᴍᴍᴀɴᴅs !
│• ꜱᴇɴᴅ ᴘʀᴏꜰɪʟᴇ ᴠɪsɪᴛꜱ
│• ╰ᐅ `/visit <ʀᴇɢɪᴏɴ> <ᴜɪᴅ>`
│•  `POWAEED BY FREXY`
╰━━━━━━━━━━━━━━━✪
 👨‍💻 CREDIT `@FREXY_OFC`
"""

# --- অটো ভিজিট হেল্পার ---
def run_auto_visit(chat_id, region, uid, minutes):
    user_key = f"{chat_id}_{uid}"
    auto_visit_threads[user_key] = True
    
    # প্রথম হিটের ডাটা JSON ফরম্যাটে দেখাবে
    try:
        api_url = f"https://visit-api-frexy.onrender.com/visit?uid={uid}&region={region}"
        response = requests.get(api_url)
        if response.status_code == 200:
            data = response.json()
            formatted_json = json.dumps(data, indent=2, ensure_ascii=False)
            bot.send_message(chat_id, f"✅ **SUCCESSFUL!**\n\n```json\n{formatted_json}\n```\n\n👨‍💻 CREDIT: `@FREXY_OFC`", parse_mode="Markdown")
        else:
            bot.send_message(chat_id, "❌ API Error during first hit.")
    except:
        bot.send_message(chat_id, "⚠️ Error starting auto-visit.")

    while auto_visit_threads.get(user_key):
        time.sleep(minutes * 60)
        
        if auto_visit_threads.get(user_key):
            try:
                requests.get(f"https://visit-api-frexy.onrender.com/visit?uid={uid}&region={region}")
            except:
                pass

# --- এডমিন কমান্ডস ---
@bot.message_handler(commands=['autovisit_on'])
def turn_on(message):
    if message.from_user.id == ADMIN_ID:
        global is_public_enabled
        is_public_enabled = True
        bot.reply_to(message, "✅ Public access turned ON.")

@bot.message_handler(commands=['autovisit_off'])
def turn_off(message):
    if message.from_user.id == ADMIN_ID:
        global is_public_enabled
        is_public_enabled = False
        bot.reply_to(message, "🚫 Public access turned OFF.")

@bot.message_handler(commands=['setminute'])
def set_min(message):
    if message.from_user.id == ADMIN_ID:
        try:
            global default_minutes
            m = int(message.text.split()[1])
            default_minutes = m
            # এখানেও সেই JSON ফরম্যাট
            res = {"status": "success", "new_interval": f"{m} minutes", "admin": "confirmed"}
            bot.reply_to(message, f"✅ **SUCCESSFUL!**\n\n```json\n{json.dumps(res, indent=2)}\n```", parse_mode="Markdown")
        except:
            bot.reply_to(message, "Use: `/setminute 5`")

# --- ইউজার কমান্ডস ---
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, START_TEXT, parse_mode="Markdown")

@bot.message_handler(commands=['visit'])
def fetch_api_data(message):
    if not is_public_enabled and message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "🚫 Admin Only Mode Active.")
        return
    try:
        text_parts = message.text.split()
        if len(text_parts) < 3:
            bot.reply_to(message, "❌ **Wrong Format!**\nUse: `/visit bd 6461428401`", parse_mode="Markdown")
            return

        region, uid = text_parts[1].lower(), text_parts[2]
        sent_msg = bot.reply_to(message, "⏳ Processing your request... Please wait.")

        api_url = f"https://visit-api-frexy.onrender.com/visit?uid={uid}&region={region}"
        response = requests.get(api_url)
        
        if response.status_code == 200:
            data = response.json()
            formatted_json = json.dumps(data, indent=2, ensure_ascii=False)
            final_text = f"✅ **SUCCESSFUL!**\n\n```json\n{formatted_json}\n```\n\n👨‍💻 CREDIT: `@FREXY_OFC`"
            bot.edit_message_text(final_text, chat_id=sent_msg.chat.id, message_id=sent_msg.message_id, parse_mode="Markdown")
        else:
            bot.edit_message_text(f"❌ **API Error!** Status: {response.status_code}", chat_id=sent_msg.chat.id, message_id=sent_msg.message_id)
    except Exception as e:
        bot.reply_to(message, f"⚠️ **Error:** {str(e)}")

@bot.message_handler(commands=['autovisit'])
def autovisit_cmd(message):
    if not is_public_enabled and message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "🚫 Admin Only Mode.")
        return
    try:
        parts = message.text.split()
        region, uid = parts[1], parts[2]
        minutes = int(parts[3]) if len(parts) > 3 else default_minutes
        threading.Thread(target=run_auto_visit, args=(message.chat.id, region, uid, minutes)).start()
    except:
        bot.reply_to(message, "❌ Use: `/autovisit bd 9909964014 5`")

@bot.message_handler(commands=['stopvisit'])
def stop_visit(message):
    try:
        uid = message.text.split()[1]
        user_key = f"{message.chat.id}_{uid}"
        auto_visit_threads[user_key] = False
        bot.reply_to(message, f"🛑 Auto-visit stopped for {uid}.")
    except:
        bot.reply_to(message, "Use: `/stopvisit <uid>`")

# বট চালু করা
print("✅ FREE FIRE VISIT BOT IS NOW ACTIVE!")
bot.infinity_polling()
