import asyncio
import os
import sqlite3
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, FSInputFile
from aiogram.filters import Command

# ================= CONFIG =================
TOKEN = os.getenv("8554950175:AAHt-6LoVbI4LJZhBcWaz4g8wQkKx_nCwMM")  # Render uchun environment variable
CHANNEL = "t.me/Asadbek55551"     # majburiy obuna kanal
ADMIN = 155824357           # sizning Telegram ID

bot = Bot("TOKEN")
dp = Dispatcher()

# ================= DATABASE =================
db = sqlite3.connect("db.sqlite3")
cursor = db.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users(
    user_id INTEGER PRIMARY KEY,
    downloads INTEGER DEFAULT 0
)
""")
db.commit()


def add_user(uid):
    cursor.execute("INSERT OR IGNORE INTO users VALUES(?,0)", (uid,))
    db.commit()


def add_download(uid):
    cursor.execute("UPDATE users SET downloads = downloads + 1 WHERE user_id=?", (uid,))
    db.commit()


def get_downloads(uid):
    cursor.execute("SELECT downloads FROM users WHERE user_id=?", (uid,))
    return cursor.fetchone()[0]


def reset_all():
    cursor.execute("UPDATE users SET downloads=0")
    db.commit()


# ================= CHANNEL CHECK =================
async def check_sub(uid):
    member = await bot.get_chat_member(CHANNEL, uid)
    return member.status in ["member", "administrator", "creator"]


# ================= START =================
@dp.message(Command("start"))
async def start(message: Message):
    add_user(message.from_user.id)
    await message.answer(
        "🎬 Video yuklovchi bot\n\n"
        "Link yuboring (YouTube/TikTok/Instagram)\n"
        "Kunlik limit: 5 ta"
    )


# ================= VIDEO =================
@dp.message(F.text.startswith("http"))
async def video_handler(message: Message):
    uid = message.from_user.id
    add_user(uid)

    # kanal tekshirish
    if not await check_sub(uid):
        await message.answer(
            f"❌ Avval kanalga obuna bo‘ling:\n{CHANNEL}"
        )
        return

    downloads = get_downloads(uid)

    # limit
    if downloads >= 5:
        await message.answer("❌ Kunlik limit tugadi. Ertaga urinib ko‘ring.")
        return

    url = message.text
    await message.answer("⏳ Yuklanmoqda...")

    filename = f"{uid}.mp4"

    os.system(f'yt-dlp -f mp4 -o "{filename}" "{url}"')

    if os.path.exists(filename):
        await message.answer_video(FSInputFile(filename))
        os.remove(filename)
        add_download(uid)

        # ===== REKLAMA (har 3 ta) =====
        if (downloads + 1) % 3 == 0:
            await message.answer(
                "📢 Reklama:\n"
                "Eng arzon internet paketlar 👉 @sizning_reklama"
            )

    else:
        await message.answer("❌ Yuklab bo‘lmadi")


# ================= ADMIN =================
@dp.message(Command("stats"))
async def stats(message: Message):
    if message.from_user.id != ADMIN:
        return

    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]
    await message.answer(f"👤 Foydalanuvchilar: {count}")


# har kuni limit reset qilish (oddiy usul)
async def reset_task():
    while True:
        await asyncio.sleep(86400)
        reset_all()


# ================= RUN =================
async def main():
    asyncio.create_task(reset_task())
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())