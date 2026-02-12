import asyncio
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage

# ========== ТВОИ ДАННЫЕ ==========
TOKEN = "8015794685:AAF8Qoi-kEhnNfDIAumXwBzjJrb5Ij6xgfQ"
ADMIN_ID = 8593277423  # Твой Telegram ID
BOT_NAME = "TestGossipBot"  # Юзернейм бота (без @)

# ========== ПАМЯТЬ ВМЕСТО БАЗЫ ==========
gossip_db = {}  # {post_id: author}
user_balance = {}  # {user_id: stars}

# ========== БОТ ==========
bot = Bot(token=TOKEN, parse_mode="HTML")
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# ========== СТАРТ ==========
@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    if user_id not in user_balance:
        user_balance[user_id] = 1000  # Всем новым — 1000 тестовых звёзд
    
    args = message.get_args()
    if args.startswith("gossip_"):
        post_id = args.replace("gossip_", "")
        await cmd_gossip(message, post_id)
    else:
        await message.reply(
            "👋 Тестовый бот сплетен.\n"
            "У тебя 1000 ⭐ для тестов.\n"
            "Баланс: /balance\n"
            "Узнать автора: /gossip_123"
        )

# ========== БАЛАНС ==========
@dp.message_handler(commands=['balance'])
async def cmd_balance(message: types.Message):
    balance = user_balance.get(message.from_user.id, 1000)
    await message.reply(f"💰 Твой баланс: {balance} ⭐")

# ========== АДМИН: ДОБАВИТЬ СПЛЕТНЮ ==========
@dp.message_handler(commands=['addgossip'])
async def cmd_addgossip(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    
    args = message.get_args().split()
    if len(args) != 2:
        await message.reply("❌ Формат: /addgossip 123 @username")
        return
    
    post_id, author = args[0], args[1]
    gossip_db[post_id] = author
    
    keyboard = types.InlineKeyboardMarkup()
    btn = types.InlineKeyboardButton(
        "🔗 Скопировать ссылку",
        url=f"https://t.me/{BOT_NAME}?start=gossip_{post_id}"
    )
    keyboard.add(btn)
    
    await message.reply(
        f"✅ Сплетня #{post_id}\nАвтор: {author}",
        reply_markup=keyboard
    )

# ========== УЗНАТЬ АВТОРА ==========
@dp.message_handler(lambda msg: msg.text and msg.text.startswith('/gossip_'))
async def cmd_gossip(message: types.Message, post_id=None):
    if not post_id:
        post_id = message.text.replace('/gossip_', '').strip()
    
    author = gossip_db.get(post_id)
    if not author:
        await message.reply("❌ Сплетня не найдена")
        return
    
    keyboard = types.InlineKeyboardMarkup()
    btn = types.InlineKeyboardButton(
        "🕵️ Узнать автора (300 ⭐)",
        callback_data=f"buy_{post_id}"
    )
    keyboard.add(btn)
    
    await message.reply(
        f"📌 Сплетня #{post_id}\n"
        f"Стоимость: 300 ⭐",
        reply_markup=keyboard
    )

# ========== ПОКУПКА ==========
@dp.callback_query_handler(lambda c: c.data and c.data.startswith('buy_'))
async def process_buy(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    post_id = callback.data.replace('buy_', '')
    author = gossip_db.get(post_id)
    
    if not author:
        await callback.answer("❌ Сплетня удалена", show_alert=True)
        return
    
    # Баланс юзера
    if user_id not in user_balance:
        user_balance[user_id] = 1000
    balance = user_balance[user_id]
    
    if balance < 300:
        await callback.answer(f"❌ Не хватает! У тебя {balance} ⭐", show_alert=True)
        return
    
    # Списываем 300
    user_balance[user_id] -= 300
    
    # Админу +150
    if ADMIN_ID not in user_balance:
        user_balance[ADMIN_ID] = 0
    user_balance[ADMIN_ID] += 150
    
    # Уведомление админу
    try:
        username = callback.from_user.username or "no username"
        await bot.send_message(
            ADMIN_ID,
            f"💰 Тест-оплата!\n"
            f"👤 @{username}\n"
            f"💎 Сплетня #{post_id}\n"
            f"⭐ Твоя доля: +150"
        )
    except:
        pass
    
    await callback.message.delete()
    
    # Кнопка для связи
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(
        "👤 Написать автору",
        url=f"https://t.me/{author.replace('@', '')}"
    ))
    
    await callback.message.answer(
        f"✅ Оплата прошла!\n\n"
        f"🕵️ Автор сплетни #{post_id}:\n{author}\n\n"
        f"💰 Твой баланс: {user_balance[user_id]} ⭐",
        reply_markup=keyboard
    )
    await callback.answer()

# ========== ЗАПУСК ==========
if __name__ == "__main__":
    print("🤖 ТЕСТОВЫЙ БОТ ЗАПУЩЕН")
    print("✅ База данных — не нужна")
    print("💰 Всё хранится в оперативной памяти")
    print("👤 У новых юзеров: 1000 ⭐")
    print("🛠️ Версия Python: 3.10+")
    executor.start_polling(dp, skip_updates=True)