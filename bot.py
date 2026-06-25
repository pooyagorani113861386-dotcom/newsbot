import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import os

TOKEN = os.environ["BOT_TOKEN"]
CHANNEL = "@Spark_news_tel"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# ذخیره موقت داده‌ها
user_data = {}

# ─────────────── دریافت فوروارد ───────────────
@dp.message(F.forward_from | F.forward_from_chat)
async def get_post(msg: types.Message):
    user_id = msg.from_user.id

    user_data[user_id] = {
        "msg": msg,
        "caption": None
    }

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ بله", callback_data="yes"),
            InlineKeyboardButton(text="❌ خیر", callback_data="no")
        ]
    ])

    await msg.answer("📥 میخوای کپشن بزنی؟", reply_markup=kb)


# ─────────────── دکمه‌ها ───────────────
@dp.callback_query()
async def callback(call: types.CallbackQuery):
    user_id = call.from_user.id

    # رد کردن
    if call.data == "no":
        await call.message.edit_text("❌ لغو شد")
        user_data.pop(user_id, None)

    # شروع کپشن
    elif call.data == "yes":
        await call.message.edit_text("✏️ کپشن جدید رو بفرست")

    # ارسال نهایی به کانال
    elif call.data == "publish":
        data = user_data[user_id]
        msg = data["msg"]
        caption = data["caption"]

        final_text = f"{caption}\n\n@Spark_news_tel"

        # عکس
        if msg.photo:
            await bot.send_photo(
                chat_id=CHANNEL,
                photo=msg.photo[-1].file_id,
                caption=final_text
            )

        # ویدیو
        elif msg.video:
            await bot.send_video(
                chat_id=CHANNEL,
                video=msg.video.file_id,
                caption=final_text
            )

        await call.message.edit_text("✅ پست شد در کانال")
        user_data.pop(user_id, None)


# ─────────────── دریافت کپشن ───────────────
@dp.message()
async def get_caption(msg: types.Message):
    user_id = msg.from_user.id

    if user_id in user_data and user_data[user_id]["caption"] is None:
        user_data[user_id]["caption"] = msg.text

        original = user_data[user_id]["msg"]

        preview_text = f"{msg.text}\n\n@Spark_news_tel"

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ تایید و پست", callback_data="publish")
            ]
        ])

        # پیش‌نمایش عکس
        if original.photo:
            await bot.send_photo(
                chat_id=user_id,
                photo=original.photo[-1].file_id,
                caption=preview_text,
                reply_markup=kb
            )

        # پیش‌نمایش ویدیو
        elif original.video:
            await bot.send_video(
                chat_id=user_id,
                video=original.video.file_id,
                caption=preview_text,
                reply_markup=kb
            )

        else:
            await msg.answer("❌ فقط عکس یا ویدیو پشتیبانی میشه")


# ─────────────── اجرا ───────────────
async def main():
    await dp.start_polling(bot)

asyncio.run(main())
