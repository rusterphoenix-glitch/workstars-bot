# ================= НАСТРОЙКИ =================

BOT_TOKEN = "8542979384:AAHmPf_QarngEfxFoyCKWf_KD9n-yfeIRPA"
ADMIN_ID = 123456789

STAR_PRICE = 0.00756
MIN_STARS = 100
REF_BONUS = 10

CRYPTOPAY_API_KEY = "PASTE_CRYPTOPAY_KEY"
MONO_TOKEN = "PASTE_MONOBANK_TOKEN"

TON_DISCOUNT = 0.97  # покупка TON на 3% ниже рынка

# =============================================

logging.basicConfig(level=logging.INFO)
db = sqlite3.connect("db.sqlite", check_same_thread=False)
sql = db.cursor()

sql.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    balance REAL DEFAULT 0,
    ref INTEGER,
    bonus INTEGER DEFAULT 0
)
""")

sql.execute("""
CREATE TABLE IF NOT EXISTS history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user INTEGER,
    type TEXT,
    amount REAL,
    date TEXT
)
""")

db.commit()

# =============================================

def menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⭐ Купить Stars", callback_data="buy_stars")],
        [InlineKeyboardButton("💎 Продать TON", callback_data="sell_ton")],
        [InlineKeyboardButton("➕ Пополнить", callback_data="topup")],
        [InlineKeyboardButton("🎁 Рефералка", callback_data="ref")],
        [InlineKeyboardButton("🆘 Поддержка", callback_data="support")]
    ])

# =============================================

def ton_price():
    r = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=the-open-network&vs_currencies=usd")
    market = r.json()["the-open-network"]["usd"]
    return round(market * TON_DISCOUNT, 4)

# =============================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    ref = context.args[0] if context.args else None

    sql.execute("INSERT OR IGNORE INTO users (id, ref) VALUES (?,?)", (uid, ref))
    if ref:
        sql.execute("UPDATE users SET bonus = bonus + ? WHERE id=?", (REF_BONUS, ref))

    db.commit()

    await update.message.reply_text(
        "🚀 *WorkStars Buy*\n\n"
        "⭐ Stars • 💎 TON\n"
        "Crypto • Monobank",
        reply_markup=menu(),
        parse_mode="Markdown"
    )

# =============================================

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    if q.data == "buy_stars":
        await q.message.reply_text(
            f"⭐ Цена: `{STAR_PRICE} USDT`\n"
            f"Минимум: `{MIN_STARS}`\n\n"
            "Введи количество:",
            parse_mode="Markdown"
        )
        context.user_data["state"] = "stars"

    elif q.data == "sell_ton":
        price = ton_price()
        await q.message.reply_text(
            f"💎 Покупаем TON\n"
            f"Цена: `{price} USDT`\n\n"
            "Введи количество TON:",
            parse_mode="Markdown"
        )
        context.user_data["state"] = "ton"

    elif q.data == "support":
        context.user_data["support"] = True
        await q.message.reply_text("✍️ Напиши сообщение для поддержки")

    elif q.data == "ref":
        await q.message.reply_text(
            f"🎁 +{REF_BONUS}% к пополнению\n\n"
            f"https://t.me/YOUR_BOT?start={q.from_user.id}"
        )

# =============================================

async def text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = update.message.text

    if context.user_data.get("support"):
        await context.bot.send_message(ADMIN_ID, f"🆘 {uid}:\n{text}")
        context.user_data.clear()
        return

    if context.user_data.get("state") == "stars":
        qty = int(text)
        if qty < MIN_STARS:
            await update.message.reply_text("❌ Минимум 100 Stars")
            return

        cost = round(qty * STAR_PRICE, 4)
        await update.message.reply_text(
            f"💰 К оплате: `{cost} USDT`\n\n"
            "Оплата:\n• CryptoBot\n• Monobank",
            parse_mode="Markdown"
        )

    elif context.user_data.get("state") == "ton":
        ton = float(text)
        payout = round(ton * ton_price(), 4)
        await update.message.reply_text(
            f"💎 Выплата: `{payout} USDT`\n"
            "Отправь TON → напиши реквизиты",
            parse_mode="Markdown"
        )

# =============================================

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(buttons))
app.add_handler(MessageHandler(filters.TEXT, text))
app.run_polling()
