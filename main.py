import os
import asyncio
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

BOT_TOKEN = os.environ.get("BOT_TOKEN")
is_on = False
chat_id_global = None

# RSI nikalne ka function
def get_rsi(symbol="BTCUSDT", interval="1m"):
    try:
        url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit=20"
        data = requests.get(url).json()
        closes = [float(x[4]) for x in data]
        gains = []
        losses = []
        for i in range(1, len(closes)):
            diff = closes[i] - closes[i-1]
            if diff > 0:
                gains.append(diff)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(diff))
        avg_gain = sum(gains[-14:]) / 14
        avg_loss = sum(losses[-14:]) / 14
        if avg_loss == 0:
            return 70
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return round(rsi, 2)
    except:
        return 50

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot Ready! ✅\n/on likho to start hoga\n/off likho to band")

async def on_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global is_on, chat_id_global
    is_on = True
    chat_id_global = update.effective_chat.id
    await update.message.reply_text("✅ Bot ON! Ab RSI scan hoga har 1 min me...")

async def off_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global is_on
    is_on = False
    await update.message.reply_text("❌ Bot OFF!")

async def auto_loop(context: ContextTypes.DEFAULT_TYPE):
    global is_on, chat_id_global
    if not is_on or not chat_id_global:
        return
    rsi_1m = get_rsi("BTCUSDT", "1m")
    rsi_5m = get_rsi("BTCUSDT", "5m")
    rsi_15m = get_rsi("BTCUSDT", "15m")

    msg = f"📊 BTC SCAN\n1m RSI: {rsi_1m}\n5m RSI: {rsi_5m}\n15m RSI: {rsi_15m}"

    # Strong signal logic
    if rsi_1m < 30 and rsi_5m < 35 and rsi_15m < 40:
        msg += "\n\n🟢 STRONG BUY SIGNAL - Oversold!"
    elif rsi_1m > 70 and rsi_5m > 65 and rsi_15m > 60:
        msg += "\n\n🔴 STRONG SELL SIGNAL - Overbought!"

    await context.bot.send_message(chat_id=chat_id_global, text=msg)

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("on", on_cmd))
    app.add_handler(CommandHandler("off", off_cmd))
    app.job_queue.run_repeating(auto_loop, interval=60, first=5)
    app.run_polling()

if __name__ == "__main__":
    main()
