import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import os

TOKEN = os.environ["BOT_TOKEN"]
CHANNEL = "@Spark_news_tel"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# ذخیره موقت داده‌ها
data = {}

# ─────────────── دریافت پست فوروارد شده ───────────────
@dp.message(F.forward_from | F.forward_from_chat)
async def handle_forward(msg: types.Message):
    user_id = msg.from_user.id

    data[user_id] = {
        "msg": msg,
        "caption": None
    }

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ بله", callback_data="ask_caption_yes"),
            InlineKeyboardButton(text="❌ خیر", callback_data="ask_caption_no")
        ]
    ])

    await msg.answer("📥 میخوای کپشن بزنی؟", reply_markup=keyboard)


# ─────────────── دکمه‌ها ───────────────
@dp.callback_query()
async def callbacks(call: types.CallbackQuery):
    user_id = call.from_user.id

    # لغو
    if call.data == "ask_caption_no":
        data.pop(user_id, None)
        await call.message.edit_text("❌ لغو شد")

    # درخواست کپشن
    elif call.data == "ask_caption_yes":
        await call.message.edit_text("✏️ کپشن جدید رو بفرست")

    # انتشار
    elif call.data == "publish":
        item = data.get(user_id)

        if not item:
            await call.message.edit_text("❌ چیزی پیدا نشد")
            return

        msg = item["msg"]
        caption = item["caption"]

        final_caption = f"{caption}\n\n@Spark_news_tel"

        # ارسال واقعی به کانال (بدون forward)
        if msg.photo:
            await bot.send_photo(
                chat_id=CHANNEL,
                photo=msg.photo[-1].file_id,
                caption=final_caption
            )

        elif msg.video:
            await bot.send_video(
                chat_id=CHANNEL,
                video=msg.video.file_id,
                caption=final_caption
            )

        else:
            await call.message.edit_text("❌ فقط عکس و ویدیو پشتیبانی میشه")
            return

        await call.message.edit_text("✅ با موفقیت در کانال منتشر شد")
        data.pop(user_id, None)


# ─────────────── گرفتن کپشن ───────────────
@dp.message()
async def get_caption(msg: types.Message):
    user_id = msg.from_user.id

    if user_id in data and data[user_id]["caption"] is None:

        data[user_id]["caption"] = msg.text

        original = data[user_id]["msg"]

        preview_text = f"{msg.text}\n\n@Spark_news_tel"

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
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
                reply_markup=keyboard
            )

        # پیش‌نمایش ویدیو
        elif original.video:
            await bot.send_video(
                chat_id=user_id,
                video=original.video.file_id,
                caption=preview_text,
                reply_markup=keyboard
            )

        else:
            await msg.answer("❌ فقط عکس و ویدیو پشتیبانی میشه")


# ─────────────── اجرا ───────────────
async def main():
    print("Bot is running...")
    await dp.start_polling(bot)

asyncio.run(main())
