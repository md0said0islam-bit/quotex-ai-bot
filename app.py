import streamlit as st
import pandas as pd
import numpy as np
import ta
import time

# --- ১. পেজ সেটআপ ---
st.set_page_config(page_title="AI Trading Signal Bot", page_icon="📈", layout="centered")

st.title("🤖 AI Trading Signal Engine")
st.caption("Multi-indicator Technical Analysis & Signal Generator")

# --- ২. স্টেট ম্যানেজমেন্ট (ট্রেড লক সিস্টেম) ---
if 'active_trade' not in st.session_state:
    st.session_state.active_trade = False
if 'trade_start' not in st.session_state:
    st.session_state.trade_start = None
if 'trade_duration' not in st.session_state:
    st.session_state.trade_duration = 60

# --- ৩. ইউজার ইনপুট / ফিল্টার ---
col1, col2 = st.columns(2)
with col1:
    pair = st.selectbox("Currency Pair", ["EUR/USD", "GBP/USD", "USD/JPY", "AUD/USD", "BTC/USD"])
with col2:
    tf_option = st.selectbox("Trade Duration", ["1 Minute", "2 Minutes", "5 Minutes"])
    duration_sec = int(tf_option.split()[0]) * 60

# --- ৪. লাইভ/সিমুলেটেড ক্যান্ডেল ডাটা জেনারেটর ---
def generate_market_data():
    np.random.seed(int(time.time() * 100) % 10000)
    base_price = 1.0850 if "USD" in pair else 65000.0
    returns = np.random.normal(0, 0.0008, 100)
    closes = base_price * np.exp(np.cumsum(returns))
    highs = closes + (np.random.rand(100) * 0.0005)
    lows = closes - (np.random.rand(100) * 0.0005)
    opens = closes + (np.random.randn(100) * 0.0002)
    return pd.DataFrame({'open': opens, 'high': highs, 'low': lows, 'close': closes})

# --- ৫. AI টেকনিক্যাল অ্যানালাইসিস ইঞ্জিন ---
def analyze_signals(df):
    # Indicators Calculation
    df['rsi'] = ta.momentum.rsi(df['close'], window=14)
    df['ema_fast'] = ta.trend.ema_indicator(df['close'], window=9)
    df['ema_slow'] = ta.trend.ema_indicator(df['close'], window=21)
    
    latest = df.iloc[-1]
    prev1 = df.iloc[-2]
    prev2 = df.iloc[-3]
    
    score = 0
    reasons = []

    # Trend Logic (EMA Cross)
    if latest['ema_fast'] > latest['ema_slow']:
        score += 1
        reasons.append("EMA 9 > EMA 21 (Uptrend)")
    else:
        score -= 1
        reasons.append("EMA 9 < EMA 21 (Downtrend)")

    # RSI Momentum Logic
    if latest['rsi'] < 32:
        score += 2
        reasons.append("RSI Oversold (Potential Reversal UP)")
    elif latest['rsi'] > 68:
        score -= 2
        reasons.append("RSI Overbought (Potential Reversal DOWN)")

    # FVG (Fair Value Gap) Check
    if prev2['high'] < latest['low']:
        score += 1
        reasons.append("Bullish FVG Zone Detected")
    elif prev2['low'] > latest['high']:
        score -= 1
        reasons.append("Bearish FVG Zone Detected")

    # Decision Output
    if score >= 2:
        return "CALL 🟢 (BUY / UP)", "High Probability Uptrend", reasons, score
    elif score <= -2:
        return "PUT 🔴 (SELL / DOWN)", "High Probability Downtrend", reasons, score
    else:
        return "NO SIGNAL ⚪ (WAIT)", "Market is Unclear or Ranging", reasons, score

# --- ৬. টাইমার ও অ্যাক্টিভ ট্রেড ট্র্যাকার ---
if st.session_state.active_trade:
    elapsed = int(time.time() - st.session_state.trade_start)
    remaining = st.session_state.trade_duration - elapsed
    
    if remaining > 0:
        st.warning(f"⏳ Trade in Progress... Time remaining: **{remaining} Seconds**")
        st.info("ট্রেডের সময় শেষ না হওয়া পর্যন্ত নতুন সিগন্যাল তৈরি করা যাবে না।")
        time.sleep(1)
        st.rerun()
    else:
        st.session_state.active_trade = False
        st.success("✅ Trade Expiry Complete! You can generate a new signal now.")
        st.rerun()

# --- ৭. সিগন্যাল বাটন ---
if not st.session_state.active_trade:
    if st.button("🚀 Generate AI Signal", use_container_width=True):
        with st.spinner("Analyzing Candlesticks, RSI, EMA & FVG..."):
            df = generate_market_data()
            signal, status, reasons, score = analyze_signals(df)
            
            st.markdown("---")
            st.subheader(f"Analysis Result: {pair}")
            st.markdown(f"## **Signal:** {signal}")
            st.write(f"**Market Condition:** {status}")
            st.write(f"**Confidence Score:** {score} / 4")
            
            st.markdown("**Key Factors Analyzed:**")
            for r in reasons:
                st.write(f"- {r}")

            if "NO SIGNAL" not in signal:
                st.session_state.active_trade = True
                st.session_state.trade_start = time.time()
                st.session_state.trade_duration = duration_sec
                st.success(f"Trade locked for {tf_option}. Countdown started!")
                time.sleep(2)
                st.rerun()
  
