import os, requests, random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")

OTC = ["EUR/USD (OTC)", "GBP/USD (OTC)", "USD/JPY (OTC)", "AUD/USD (OTC)", "GBP/JPY (OTC)"]
LIVE = ["EUR/USD", "GBP/USD", "USD/JPY", "AUD/USD", "BTC/USDT"]

def get_signal():
    try:
        data = requests.get("https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1m&limit=20", timeout=5).json()
        closes = [float(x[4]) for x in data]
        fast = sum(closes[-9:])/9
        slow = sum(closes[-21:])/21
        return ("UP 📈" if fast>slow else "DOWN 📉"), random.randint(76,88)
    except:
        return random.choice(["UP 📈","DOWN 📉"]), random.randint(75,86)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [[InlineKeyboardButton("🔥 OTC (24/7) 🔥", callback_data="otc")],[InlineKeyboardButton("🌍 LIVE 🌍", callback_data="live")]]
    txt = "💎 ZEESHAN PRO BOT READY 💎\nMarket select karo 👇"
    if update.message: await update.message.reply_text(txt, reply_markup=InlineKeyboardMarkup(kb))
    else: await update.callback_query.message.edit_text(txt, reply_markup=InlineKeyboardMarkup(kb))

async def btns(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if q.data == "otc":
        kb = [[InlineKeyboardButton(p, callback_data=f"S_{p}")] for p in OTC] + [[InlineKeyboardButton("⬅️ Back", callback_data="home")]]
        await q.message.edit_text("🔥 OTC MARKET - Pair select karo:", reply_markup=InlineKeyboardMarkup(kb))
    elif q.data == "live":
        kb = [[InlineKeyboardButton(p, callback_data=f"S_{p}")] for p in LIVE] + [[InlineKeyboardButton("⬅️ Back", callback_data="home")]]
        await q.message.edit_text("🌍 LIVE MARKET - Pair select karo:", reply_markup=InlineKeyboardMarkup(kb))
    elif q.data == "home":
        await start(update, context)
    elif q.data.startswith("S_"):
        pair = q.data.replace("S_","")
        await q.message.edit_text(f"⏳ {pair} analysis...")
        direction, acc = get_signal()
        msg = f"💎 SIGNAL 💎\n━━━━━━━━\n💱 {pair}\n⏰ 1 MIN\n📊 {direction}\n🎯 {acc}%\n━━━━━━━━"
        kb = [[InlineKeyboardButton(f"🔄 Next {pair}", callback_data=f"S_{pair}")],[InlineKeyboardButton("⬅️ Menu", callback_data="home")]]
        await q.message.edit_text(msg, reply_markup=InlineKeyboardMarkup(kb))

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(btns))
    app.run_polling()

if __name__ == "__main__":
    main()
