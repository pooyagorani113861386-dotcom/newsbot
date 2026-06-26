import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto, InputMediaVideo
import os

TOKEN = os.environ["BOT_TOKEN"]

CHANNEL = "@Spark_news_tel"

# 🔐 فقط تو
ALLOWED_USERS = [8293164271]

bot = Bot(token=TOKEN)
dp = Dispatcher()

# ذخیره وضعیت موقت و حافظه آلبوم‌ها
state = {}
media_groups_cache = {}


# ─────────────── چک دسترسی ───────────────
def allowed(user_id: int):
    return user_id in ALLOWED_USERS

# ─────────────── ارسال پرسش کپشن ───────────────
async def prompt_caption(user_id: int):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ بله", callback_data="yes"),
            InlineKeyboardButton(text="❌ خیر", callback_data="no")
        ]
    ])
    await bot.send_message(user_id, "📥 میخوای کپشن بزنی؟", reply_markup=kb)

# ─────────────── پردازش تاخیری آلبوم ───────────────
async def process_media_group(mg_id: str, user_id: int):
    # ۲ ثانیه صبر می‌کنیم تا همه پیام‌های آلبوم به سرور برسند
    await asyncio.sleep(2)
    
    if mg_id not in media_groups_cache:
        return
    
    msgs = media_groups_cache.pop(mg_id)
    
    state[user_id] = {
        "msgs": msgs,  # حالا یک لیست از پیام‌ها داریم
        "caption": None,
        "is_album": True
    }
    await prompt_caption(user_id)


# ─────────────── دریافت فوروارد ───────────────
@dp.message(F.forward_from | F.forward_from_chat)
async def forward_handler(msg: types.Message):

    if not allowed(msg.from_user.id):
        return

    user_id = msg.from_user.id

    # اگر پیام بخشی از یک آلبوم باشد
    if msg.media_group_id:
        if msg.media_group_id not in media_groups_cache:
            media_groups_cache[msg.media_group_id] = []
            # یک تسک ایجاد می‌کنیم که بعد از ۲ ثانیه آلبوم را پردازش کند
            asyncio.create_task(process_media_group(msg.media_group_id, user_id))
        
        media_groups_cache[msg.media_group_id].append(msg)
    
    # اگر پیام تکی باشد (یک عکس یا ویدیو)
    else:
        state[user_id] = {
            "msgs": [msg],
            "caption": None,
            "is_album": False
        }
        await prompt_caption(user_id)


# ─────────────── گرفتن کپشن ───────────────
@dp.message()
async def caption_handler(msg: types.Message):

    if not allowed(msg.from_user.id):
        return

    user_id = msg.from_user.id

    if user_id in state and state[user_id]["caption"] is None:
        state[user_id]["caption"] = msg.text

        data = state[user_id]
        msgs = data["msgs"]
        is_album = data["is_album"]
        
        final_text = f"{msg.text}\n\n@Spark_news_tel"

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ تایید و پست", callback_data="publish")]
        ])

        try:
            if is_album:
                media_group = []
                for i, m in enumerate(msgs):
                    # کپشن فقط روی فایل اول تنظیم می‌شود
                    cap = final_text if i == 0 else None
                    if m.photo:
                        media_group.append(InputMediaPhoto(media=m.photo[-1].file_id, caption=cap))
                    elif m.video:
                        media_group.append(InputMediaVideo(media=m.video.file_id, caption=cap))
                
                if media_group:
                    await bot.send_media_group(chat_id=user_id, media=media_group)
                    # در حالت آلبوم، دکمه باید در پیام جداگانه ارسال شود
                    await bot.send_message(chat_id=user_id, text="👆 این پیش‌نمایش آلبوم شماست. تایید می‌کنید؟", reply_markup=kb)
            
            else:
                original = msgs[0]
                if original.photo:
                    await bot.send_photo(chat_id=user_id, photo=original.photo[-1].file_id, caption=final_text, reply_markup=kb)
                elif original.video:
                    await bot.send_video(chat_id=user_id, video=original.video.file_id, caption=final_text, reply_markup=kb)
                else:
                    await msg.answer("❌ فقط عکس یا ویدیو پشتیبانی میشه")
        
        except Exception as e:
            await msg.answer(f"❌ خطا در پیش‌نمایش:\n{e}")


# ─────────────── دکمه‌ها ───────────────
@dp.callback_query()
async def callback_handler(call: types.CallbackQuery):

    if not allowed(call.from_user.id):
        await call.answer("⛔ دسترسی نداری", show_alert=True)
        return

    await call.answer()

    user_id = call.from_user.id

    if user_id not in state:
        await call.message.edit_text("⛔ داده‌ای پیدا نشد")
        return

    data = state[user_id]

    # ❌ لغو
    if call.data == "no":
        await call.message.edit_text("❌ لغو شد")
        state.pop(user_id, None)
        return

    # ✏️ درخواست کپشن
    if call.data == "yes":
        await call.message.edit_text("✏️ کپشن جدید رو بفرست")
        return

    # 📢 انتشار
    if call.data == "publish":
        msgs = data["msgs"]
        caption = data["caption"]
        is_album = data["is_album"]

        # اگر کاربر "خیر" را زده باشد، فقط آیدی کانال را میگذاریم
        final_text = f"{caption}\n\n@Spark_news_tel" if caption else "@Spark_news_tel"

        try:
            if is_album:
                media_group = []
                for i, m in enumerate(msgs):
                    cap = final_text if i == 0 else None
                    if m.photo:
                        media_group.append(InputMediaPhoto(media=m.photo[-1].file_id, caption=cap))
                    elif m.video:
                        media_group.append(InputMediaVideo(media=m.video.file_id, caption=cap))
                
                if media_group:
                    await bot.send_media_group(chat_id=CHANNEL, media=media_group)
            
            else:
                msg = msgs[0]
                if msg.photo:
                    await bot.send_photo(chat_id=CHANNEL, photo=msg.photo[-1].file_id, caption=final_text)
                elif msg.video:
                    await bot.send_video(chat_id=CHANNEL, video=msg.video.file_id, caption=final_text)

            # پیام موفقیت و پاک کردن دکمه تایید
            await bot.send_message(chat_id=user_id, text="✅ پست با موفقیت در کانال منتشر شد")
            try:
                await call.message.delete()
            except:
                pass
            
            state.pop(user_id, None)
            
        except Exception as e:
            await bot.send_message(chat_id=user_id, text=f"❌ خطا در ارسال به کانال:\n{e}")


# ─────────────── اجرا ───────────────
async def main():
    print("🤖 Bot is running...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
