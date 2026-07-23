import streamlit as st
import pandas as pd
import numpy as np
import ta
import time

# --- ১. পেজ সেটআপ ---
st.set_page_config(page_title="Floating AI Signal Bot", page_icon="📈", layout="centered")

st.title("🤖 Quick Expiry AI Signal Bot")

# --- ২. স্টেট ম্যানেজমেন্ট ---
if 'active_trade' not in st.session_state:
    st.session_state.active_trade = False
if 'trade_start' not in st.session_state:
    st.session_state.trade_start = None
if 'trade_duration' not in st.session_state:
    st.session_state.trade_duration = 5

# --- ৩. কাস্টম টাইমফ্রেম ফিল্টার ---
col1, col2 = st.columns(2)
with col1:
    pair = st.selectbox("Asset Pair", ["EUR/USD", "GBP/USD", "USD/JPY", "AUD/USD", "BTC/USD"])
with col2:
    # কাস্টম শর্ট টাইমফ্রেম যোগ করা হয়েছে
    tf_option = st.selectbox("Expiry Time", ["5 Seconds", "10 Seconds", "15 Seconds", "30 Seconds", "1 Minute"])
    
    # সময় সেকেন্ডে কনভার্ট করার নিয়ম
    if "Seconds" in tf_option:
        duration_sec = int(tf_option.split()[0])
    else:
        duration_sec = int(tf_option.split()[0]) * 60

# --- ৪. ডাটা জেনারেটর ---
def generate_market_data():
    np.random.seed(int(time.time() * 100) % 10000)
    base_price = 1.0850 if "USD" in pair else 65000.0
    returns = np.random.normal(0, 0.0008, 100)
    closes = base_price * np.exp(np.cumsum(returns))
    highs = closes + (np.random.rand(100) * 0.0005)
    lows = closes - (np.random.rand(100) * 0.0005)
    opens = closes + (np.random.randn(100) * 0.0002)
    return pd.DataFrame({'open': opens, 'high': highs, 'low': lows, 'close': closes})

# --- ৫. AI সিগন্যাল লজিক ---
def analyze_signals(df):
    df['rsi'] = ta.momentum.rsi(df['close'], window=14)
    df['ema_fast'] = ta.trend.ema_indicator(df['close'], window=9)
    df['ema_slow'] = ta.trend.ema_indicator(df['close'], window=21)
    
    latest = df.iloc[-1]
    prev2 = df.iloc[-3]
    score = 0
    reasons = []

    if latest['ema_fast'] > latest['ema_slow']:
        score += 1
        reasons.append("EMA 9 > EMA 21 (Up Trend)")
    else:
        score -= 1
        reasons.append("EMA 9 < EMA 21 (Down Trend)")

    if latest['rsi'] < 35:
        score += 2
        reasons.append("RSI Oversold (UP Signal)")
    elif latest['rsi'] > 65:
        score -= 2
        reasons.append("RSI Overbought (DOWN Signal)")

    if prev2['high'] < latest['low']:
        score += 1
        reasons.append("Bullish FVG Zone")
    elif prev2['low'] > latest['high']:
        score -= 1
        reasons.append("Bearish FVG Zone")

    if score >= 2:
        return "CALL 🟢 (BUY)", reasons, score
    elif score <= -2:
        return "PUT 🔴 (SELL)", reasons, score
    else:
        return "WAIT ⚪ (NO SIGNAL)", reasons, score

# --- ৬. কাউন্টডাউন টাইমার ---
if st.session_state.active_trade:
    elapsed = int(time.time() - st.session_state.trade_start)
    remaining = st.session_state.trade_duration - elapsed
    
    if remaining > 0:
        st.warning(f"⏳ Trade Active: **{remaining}s** remaining")
        time.sleep(1)
        st.rerun()
    else:
        st.session_state.active_trade = False
        st.success("✅ Trade Finished! Ready for next trade.")
        st.rerun()

# --- ৭. সিগন্যাল বাটন ---
if not st.session_state.active_trade:
    if st.button("🚀 Get Signal", use_container_width=True):
        df = generate_market_data()
        signal, reasons, score = analyze_signals(df)
        
        st.markdown(f"### **Signal:** {signal}")
        st.write(f"Confidence: {score} / 4")
        
        for r in reasons:
            st.caption(f"- {r}")

        if "WAIT" not in signal:
            st.session_state.active_trade = True
            st.session_state.trade_start = time.time()
            st.session_state.trade_duration = duration_sec
            time.sleep(1)
            st.rerun()
    
