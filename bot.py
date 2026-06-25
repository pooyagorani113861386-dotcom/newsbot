from aiogram import Bot, Dispatcher, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import asyncio
import os

TOKEN = os.environ["BOT_TOKEN"]

bot = Bot(token=TOKEN)
dp = Dispatcher()

# ذخیره موقت
data = {}

# ─────────────── 1. دریافت فوروارد ───────────────
@dp.message(F.forward_from | F.forward_from_chat)
async def get_post(msg: types.Message):
    user_id = msg.from_user.id

    data[user_id] = {
        "message": msg,
        "caption": None
    }

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ بله", callback_data="yes"),
            InlineKeyboardButton(text="❌ خیر", callback_data="no")
        ]
    ])

    await msg.answer("📥 میخوای کپشن بزنی؟", reply_markup=kb)


# ─────────────── 2. دکمه‌ها ───────────────
@dp.callback_query()
async def callback(call: types.CallbackQuery):
    user_id = call.from_user.id

    if call.data == "no":
        await call.message.edit_text("❌ لغو شد")
        data.pop(user_id, None)

    elif call.data == "yes":
        await call.message.edit_text("✏️ کپشن جدید رو بفرست")

    elif call.data == "publish":
        post = data[user_id]
        msg = post["message"]
        caption = post["caption"]

        text = f"{caption}\n\n@Spark_rap"

        if msg.photo:
            await bot.send_photo(user_id, msg.photo[-1].file_id, caption=text)
        elif msg.video:
            await bot.send_video(user_id, msg.video.file_id, caption=text)

        await call.message.edit_text("✅ منتشر شد")
        data.pop(user_id, None)


# ─────────────── 3. گرفتن کپشن ───────────────
@dp.message()
async def get_caption(msg: types.Message):
    user_id = msg.from_user.id

    if user_id in data and data[user_id]["caption"] is None:
        data[user_id]["caption"] = msg.text

        post = data[user_id]["message"]

        text = f"{msg.text}\n\n@Spark_rap"

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ تایید و پست", callback_data="publish")]
        ])

        if post.photo:
            await bot.send_photo(user_id, post.photo[-1].file_id, caption=text, reply_markup=kb)
        elif post.video:
            await bot.send_video(user_id, post.video.file_id, caption=text, reply_markup=kb)


async def main():
    await dp.start_polling(bot)

asyncio.run(main())