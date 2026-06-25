import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import os

TOKEN = os.environ["BOT_TOKEN"]

CHANNEL = "@Spark_news_tel"

# 🔐 فقط ادمین مجاز
ALLOWED_USERS = [8293164271]

bot = Bot(token=TOKEN)
dp = Dispatcher()

# ذخیره وضعیت کاربران
state = {}

# ─────────────── چک دسترسی ───────────────
def is_allowed(user_id: int):
    return user_id in ALLOWED_USERS


# ─────────────── دریافت فوروارد ───────────────
@dp.message(F.forward_from | F.forward_from_chat)
async def on_forward(msg: types.Message):

    if not is_allowed(msg.from_user.id):
        return

    user_id = msg.from_user.id

    state[user_id] = {
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
async def callbacks(call: types.CallbackQuery):

    if not is_allowed(call.from_user.id):
        await call.answer("⛔ دسترسی نداری", show_alert=True)
        return

    user_id = call.from_user.id

    if user_id not in state:
        await call.answer("⛔ چیزی پیدا نشد")
        return

    # ❌ لغو
    if call.data == "no":
        await call.message.edit_text("❌ لغو شد")
        state.pop(user_id, None)

    # ✏️ درخواست کپشن
    elif call.data == "yes":
        await call.message.edit_text("✏️ کپشن جدید رو بفرست")

    # 📢 انتشار نهایی
    elif call.data == "publish":

        item = state[user_id]
        msg = item["msg"]
        caption = item["caption"]

        final_text = f"{caption}\n\n@Spark_news_tel"

        # 📤 ارسال به کانال (عکس)
        if msg.photo:
            await bot.send_photo(
                chat_id=CHANNEL,
                photo=msg.photo[-1].file_id,
                caption=final_text
            )

        # 📤 ارسال به کانال (ویدیو)
        elif msg.video:
            await bot.send_video(
                chat_id=CHANNEL,
                video=msg.video.file_id,
                caption=final_text
            )

        await call.message.edit_text("✅ پست شد در کانال")

        state.pop(user_id, None)


# ─────────────── دریافت کپشن ───────────────
@dp.message()
async def get_caption(msg: types.Message):

    if not is_allowed(msg.from_user.id):
        return

    user_id = msg.from_user.id

    if user_id in state and state[user_id]["caption"] is None:
        state[user_id]["caption"] = msg.text

        original = state[user_id]["msg"]
        text = f"{msg.text}\n\n@Spark_news_tel"

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ تایید و پست", callback_data="publish")
            ]
        ])

        # 👀 پیش‌نمایش عکس
        if original.photo:
            await bot.send_photo(
                chat_id=user_id,
                photo=original.photo[-1].file_id,
                caption=text,
                reply_markup=kb
            )

        # 👀 پیش‌نمایش ویدیو
        elif original.video:
            await bot.send_video(
                chat_id=user_id,
                video=original.video.file_id,
                caption=text,
                reply_markup=kb
            )

        else:
            await msg.answer("❌ فقط عکس یا ویدیو پشتیبانی میشه")


# ─────────────── اجرا ───────────────
async def main():
    print("🤖 Bot is running...")
    await dp.start_polling(bot)

asyncio.run(main())
