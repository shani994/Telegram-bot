import yfinance as yf
import pandas as pd
import numpy as np
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")

PAIRS = {
    "EUR/USD": "EURUSD=X",
    "GBP/USD": "GBPUSD=X",
    "USD/JPY": "JPY=X",
    "AUD/USD": "AUDUSD=X",
    "EUR/JPY": "EURJPY=X"
}

def get_indicators(df):
    close = df['Close']
    # RSI
    delta = close.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    # EMA
    df['EMA9'] = close.ewm(span=9, adjust=False).mean()
    df['EMA21'] = close.ewm(span=21, adjust=False).mean()
    # BB
    df['MA20'] = close.rolling(20).mean()
    df['STD'] = close.rolling(20).std()
    df['BB_U'] = df['MA20'] + (df['STD'] * 2)
    df['BB_L'] = df['MA20'] - (df['STD'] * 2)
    return df

def analyze(symbol):
    try:
        df = yf.download(symbol, period="1d", interval="1m", progress=False)
        if len(df) < 30:
            return None
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df = get_indicators(df)
        last = df.iloc[-1]
        
        # Strong Logic
        if last['EMA9'] > last['EMA21'] and last['RSI'] > 32 and last['RSI'] < 60 and last['Close'] > last['BB_L']:
            return "UP", int(last['RSI'])
        if last['EMA9'] < last['EMA21'] and last['RSI'] < 68 and last['RSI'] > 40 and last['Close'] < last['BB_U']:
            return "DOWN", int(last['RSI'])
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton(f"{k} LIVE", callback_data=k)] for k in PAIRS]
    keyboard.append([InlineKeyboardButton("EUR/USD (OTC)", callback_data="EUR/USD")])
    await update.message.reply_text("💎 **V2 PRO FIXED & READY**\nAb crash nahi hoga. Pair select karo:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "menu":
        await start(update, context)
        return
    
    pair_name = query.data
    symbol = PAIRS.get(pair_name, "EURUSD=X")
    await query.edit_message_text(f"🔍 {pair_name} analyze ho raha hai...")

    result = analyze(symbol)
    if result:
        direction, rsi = result
        emoji = "📈" if direction == "UP" else "📉"
        text = f"💎 **SIGNAL V2 PRO** 💎\n\n**{pair_name}**\n**{direction} {emoji}**\n**1-2 MIN**\n**RSI: {rsi}**\n\n⏰ Agle Switch Time pe entry lo."
    else:
        text = f"❌ {pair_name} me abhi strong signal nahi hai. Market side-ways hai. 2 min baad try karo."

    kb = [[InlineKeyboardButton(f"Next {pair_name}", callback_data=pair_name)], [InlineKeyboardButton("Menu", callback_data="menu")]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

if __name__ == '__main__':
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    print("Bot Running...")
    app.run_polling()
