import telebot
from telebot.types import BotCommand, Message, ChatPermissions
from datetime import datetime, timedelta, UTC
import re

API_TOKEN = 'YOUR_BOT_TOKEN_HERE'  # ← замени на свой токен
bot = telebot.TeleBot(API_TOKEN)

blacklist = set()  # Чёрный список пользователей

# ========== Команды ==========
mute_commands = [
    ("mut_30s", "Мут на 30 секунд"),
    ("mut_1m", "Мут на 1 минуту"),
    ("mut_2m", "Мут на 2 минуты"),
    ("mut_5m", "Мут на 5 минут"),
    ("mut_10m", "Мут на 10 минут"),
    ("mut_15m", "Мут на 15 минут"),
    ("mut_30m", "Мут на 30 минут"),
    ("mut_45m", "Мут на 45 минут"),
    ("mut_1h", "Мут на 1 час"),
    ("mut_2h", "Мут на 2 часа"),
    ("mut_3h", "Мут на 3 часа"),
    ("mut_6h", "Мут на 6 часов"),
    ("mut_12h", "Мут на 12 часов"),
    ("mut_1d", "Мут на 1 день"),
    ("mut_2d", "Мут на 2 дня"),
    ("mut_3d", "Мут на 3 дня"),
    ("mut_7d", "Мут на 7 дней"),
    ("mut_30d", "Мут на 30 дней"),
    ("mut_perm", "Бессрочный мут"),
    ("unmute", "Снять мут")
]


block_commands = [
    ("block_media", "Запретить стикеры и гифки"),
    ("unblock_media", "Разрешить стикеры и гифки")
]

ban_commands = [
    ("ban", "Забанить"),
    ("unban", "Разбанить"),
    ("add_admin", "Выдать админку"),
    ("remove_admin", "Снять админку")
]

all_commands = mute_commands + block_commands + ban_commands
bot.set_my_commands([BotCommand(cmd, desc) for cmd, desc in all_commands])

# ========== Вспомогательные функции ==========
def is_admin(chat_id, user_id):
    try:
        member = bot.get_chat_member(chat_id, user_id)
        return member.status in ['administrator', 'creator']
    except Exception:
        return False

def parse_duration(duration: str) -> int:
    match = re.match(r'(\d+)([smhd])', duration)
    if not match:
        return 0
    num, unit = match.groups()
    seconds = int(num)
    if unit == 'm':
        seconds *= 60
    elif unit == 'h':
        seconds *= 3600
    elif unit == 'd':
        seconds *= 86400
    return seconds

# ========== Обработчики команд ==========
@bot.message_handler(func=lambda m: m.from_user.id in blacklist)
def blocked_user(message: Message):
    bot.reply_to(message, "⛔ Вы в чёрном списке и не можете использовать этого бота.")

@bot.message_handler(commands=['ban'])
def ban_user(message: Message):
    if not is_admin(message.chat.id, message.from_user.id):
        return
    if message.reply_to_message:
        bot.ban_chat_member(message.chat.id, message.reply_to_message.from_user.id)
        bot.reply_to(message, "✅ Пользователь забанен.")

@bot.message_handler(commands=['unban'])
def unban_user(message: Message):
    if not is_admin(message.chat.id, message.from_user.id):
        return
    if message.reply_to_message:
        bot.unban_chat_member(message.chat.id, message.reply_to_message.from_user.id)
        bot.reply_to(message, "✅ Пользователь разбанен.")

@bot.message_handler(commands=['unmute'])
def unmute_user(message: Message):
    if not is_admin(message.chat.id, message.from_user.id):
        return
    if message.reply_to_message:
        perms = ChatPermissions(
            can_send_messages=True,
            can_send_media_messages=True,
            can_send_other_messages=True,
            can_add_web_page_previews=True,
            can_send_polls=True,
            can_change_info=False,
            can_invite_users=True,
            can_pin_messages=False
        )
        bot.restrict_chat_member(
            chat_id=message.chat.id,
            user_id=message.reply_to_message.from_user.id,
            permissions=perms,
            until_date=0
        )
        bot.reply_to(message, "✅ Мут снят.")

@bot.message_handler(commands=[cmd[0] for cmd in mute_commands if 'mut_' in cmd[0]])
def handle_mute(message: Message):
    if not is_admin(message.chat.id, message.from_user.id):
        bot.reply_to(message, "⛔ Только админ может выдавать мут.")
        return
    if not message.reply_to_message:
        bot.reply_to(message, "🔄 Ответь на сообщение пользователя, которому нужно выдать мут.")
        return

    try:
        cmd = message.text.split()[0]
        duration_code = cmd.split('_')[1]

        if duration_code == "perm":
            until = datetime.now(UTC) + timedelta(days=365 * 100)
        else:
            seconds = parse_duration(duration_code)
            until = datetime.now(UTC) + timedelta(seconds=seconds)

        perms = ChatPermissions(
            can_send_messages=False,
            can_send_media_messages=False,
            can_send_other_messages=False,
            can_add_web_page_previews=False,
            can_send_polls=False
        )

        bot.restrict_chat_member(
            chat_id=message.chat.id,
            user_id=message.reply_to_message.from_user.id,
            permissions=perms,
            until_date=until
        )
        bot.reply_to(message, f"🔇 Мут на {duration_code}")
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")

@bot.message_handler(commands=['block_media'])
def block_media(message: Message):
    if is_admin(message.chat.id, message.from_user.id) and message.reply_to_message:
        perms = ChatPermissions(
            can_send_messages=True,
            can_send_media_messages=False,
            can_send_other_messages=False,
            can_add_web_page_previews=False,
            can_send_polls=True
        )
        bot.restrict_chat_member(message.chat.id, message.reply_to_message.from_user.id, permissions=perms)
        bot.reply_to(message, "🚫 Стикеры и гифки запрещены.")

@bot.message_handler(commands=['unblock_media'])
def unblock_media(message: Message):
    if is_admin(message.chat.id, message.from_user.id) and message.reply_to_message:
        perms = ChatPermissions(
            can_send_messages=True,
            can_send_media_messages=True,
            can_send_other_messages=True,
            can_add_web_page_previews=True,
            can_send_polls=True
        )
        bot.restrict_chat_member(message.chat.id, message.reply_to_message.from_user.id, permissions=perms)
        bot.reply_to(message, "✅ Стикеры и гифки разрешены.")

@bot.message_handler(commands=['add_admin'])
def add_admin(message: Message):
    if is_admin(message.chat.id, message.from_user.id) and message.reply_to_message:
        try:
            bot.promote_chat_member(
                chat_id=message.chat.id,
                user_id=message.reply_to_message.from_user.id,
                can_change_info=True,
                can_delete_messages=True,
                can_invite_users=True,
                can_restrict_members=True,
                can_pin_messages=True,
                can_promote_members=False,
                can_manage_chat=True
            )
            bot.reply_to(message, "👑 Админка выдана.")
        except Exception as e:
            bot.reply_to(message, f"Ошибка: {e}")

@bot.message_handler(commands=['remove_admin'])
def remove_admin(message: Message):
    if is_admin(message.chat.id, message.from_user.id) and message.reply_to_message:
        try:
            bot.promote_chat_member(
                chat_id=message.chat.id,
                user_id=message.reply_to_message.from_user.id,
                can_change_info=False,
                can_delete_messages=False,
                can_invite_users=False,
                can_restrict_members=False,
                can_pin_messages=False,
                can_promote_members=False,
                can_manage_chat=False
            )
            bot.reply_to(message, "🗑 Админка снята.")
        except Exception as e:
            bot.reply_to(message, f"Ошибка: {e}")

# ========== Запуск ==========
print("✅ Бот запущен...")
bot.infinity_polling()
