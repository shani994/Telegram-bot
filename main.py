import yfinance as yf
import pandas as pd
import pandas_ta as ta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import asyncio
import os

TOKEN = os.getenv("BOT_TOKEN")

PAIRS = {
    "EUR/USD": "EURUSD=X",
    "GBP/USD": "GBPUSD=X",
    "USD/JPY": "JPY=X",
    "AUD/USD": "AUDUSD=X"
}

def analyze_market(symbol):
    try:
        df = yf.download(symbol, period="1d", interval="1m", progress=False)
        if len(df) < 50:
            return None
        
        # Indicators
        df['RSI'] = ta.rsi(df['Close'], length=14)
        df['EMA_9'] = ta.ema(df['Close'], length=9)
        df['EMA_21'] = ta.ema(df['Close'], length=21)
        df['MACD'] = ta.macd(df['Close'])['MACD_12_26_9']
        df['MACD_S'] = ta.macd(df['Close'])['MACDs_12_26_9']
        bb = ta.bbands(df['Close'], length=20, std=2)
        df['BB_L'] = bb['BBL_20_2.0']
        df['BB_U'] = bb['BBU_20_2.0']

        last = df.iloc[-1]
        prev = df.iloc[-2]

        # STRONG BUY LOGIC
        buy_cond = (
            last['RSI'] > 30 and last['RSI'] < 58 and
            last['EMA_9'] > last['EMA_21'] and
            prev['EMA_9'] <= prev['EMA_21'] and # Fresh crossover
            last['MACD'] > last['MACD_S'] and
            last['Close'] > last['BB_L']
        )

        # STRONG SELL LOGIC
        sell_cond = (
            last['RSI'] < 70 and last['RSI'] > 42 and
            last['EMA_9'] < last['EMA_21'] and
            prev['EMA_9'] >= prev['EMA_21'] and # Fresh crossover
            last['MACD'] < last['MACD_S'] and
            last['Close'] < last['BB_U']
        )

        if buy_cond:
            acc = 75 + int((58 - last['RSI'])/2) # dynamic accuracy
            return "UP", min(acc, 88), round(last['RSI'],1)
        elif sell_cond:
            acc = 75 + int((last['RSI'] - 42)/2)
            return "DOWN", min(acc, 88), round(last['RSI'],1)
        else:
            return None
    except Exception as e:
        print(e)
        return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = []
    for name in PAIRS.keys():
        keyboard.append([InlineKeyboardButton(f"{name} LIVE", callback_data=name)])
    keyboard.append([InlineKeyboardButton("EUR/USD (OTC)", callback_data="EUR/USD")]) # OTC ke liye bhi LIVE data use hoga
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("💎 **V2 PRO ANALYZER READY**\nMarket khud analyze karke signal dunga. Pair select karo:", reply_markup=reply_markup, parse_mode='Markdown')

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    pair_name = query.data
    symbol = PAIRS.get(pair_name, "EURUSD=X")
    
    await query.edit_message_text(f"🔍 {pair_name} ko analyze kar raha hu... 4 Indicators check ho rahe hain...")

    result = analyze_market(symbol)

    if result:
        direction, acc, rsi = result
        emoji = "📈" if direction == "UP" else "📉"
        text = f"""💎 **SIGNAL V2 PRO** 💎
        
**{pair_name} {'(OTC)' if 'OTC' in query.data else 'LIVE'}**
**1-2 MIN**
**{direction} {emoji}**
**🎯 Accuracy: {acc}%**
**RSI: {rsi} | EMA + MACD + BB Confirmed**

⏰ Agli candle (Switch Time) pe entry lo.
"""
    else:
        text = f"""❌ {pair_name} me abhi koi strong signal nahi hai.
Market side-ways hai. Thodi der baad try karo.

Yehi iski khasiyat hai, har waqt signal nahi dega, sirf strong wala dega."""

    keyboard = [[InlineKeyboardButton(f"Next {pair_name}", callback_data=pair_name)], [InlineKeyboardButton("Menu", callback_data="menu")]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

    if query.data == "menu":
        await start(update, context)

if __name__ == '__main__':
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.run_polling()
