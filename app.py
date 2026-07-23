import numpy as np
import pandas as pd

# =========================================================
# 1. CONFIGURATION: TIMEFRAMES & MARKETS
# =========================================================

QUOTEX_TIMEFRAMES = {
    "5s": 5, "10s": 10, "15s": 15, "30s": 30,
    "1m": 60, "2m": 120, "5m": 300, "10m": 600, "15m": 900, "30m": 1800,
    "1h": 3600, "4h": 14400, "1d": 86400
}

MARKETS = {
    "OTC_FOREX": [
        "EURUSD_otc", "GBPUSD_otc", "USDJPY_otc", "AUDUSD_otc", "USDCAD_otc",
        "USDCHF_otc", "NZDUSD_otc", "EURGBP_otc", "EURJPY_otc", "GBPJPY_otc",
        "USDBRL_otc", "USDINR_otc", "USDBDT_otc"
    ],
    "STANDARD_FOREX": [
        "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "USDCHF", "NZDUSD"
    ],
    "CRYPTO_COMMODITIES": [
        "BTCUSD", "ETHUSD", "XAUUSD", "UKBrent", "BTCUSD_otc", "XAUUSD_otc"
    ]
}

ALL_MARKETS = sum(MARKETS.values(), [])

BOT_SETTINGS = {
    "TIMEFRAME": "1m",
    "MIN_PAYOUT": 80,
    "MAX_DAILY_LOSS": 5,        # ৫% লস হলে বট অফ হবে
    "RISK_PER_TRADE_PERCENT": 2, # প্রতি ট্রেডে ২% ঝুঁকি
    "EMA_PERIOD": 50            # ট্রেন্ড ফিল্টার
}

# =========================================================
# 2. ANALYSIS ENGINE (TECHNICAL INDICATORS & PATTERNS)
# =========================================================

class SignalEngine:
    def __init__(self, df):
        """
        df: Pandas DataFrame with columns ['open', 'high', 'low', 'close', 'volume']
        """
        self.df = df

    def calculate_ema(self, period=50):
        """EMA গণনা করে ট্রেন্ড ফিল্টার করে"""
        self.df['ema'] = self.df['close'].ewm(span=period, adjust=False).mean()
        latest_close = self.df['close'].iloc[-1]
        latest_ema = self.df['ema'].iloc[-1]
        
        if latest_close > latest_ema:
            return "UPTREND"
        elif latest_close < latest_ema:
            return "DOWNTREND"
        return "SIDEWAYS"

    def check_support_resistance(self, lookback=30):
        """বিগত ক্যান্ডেলগুলোর থেকে Key Support & Resistance বের করে"""
        recent_df = self.df.tail(lookback)
        resistance = recent_df['high'].max()
        support = recent_df['low'].min()
        latest_close = self.df['close'].iloc[-1]
        
        # লেভেলের কাছাকাছি (0.05% Range) আছে কি না
        near_support = abs(latest_close - support) / support < 0.0005
        near_resistance = abs(latest_close - resistance) / resistance < 0.0005
        
        return near_support, near_resistance

    def detect_fvg(self):
        """Fair Value Gap (FVG) নির্ণয় করে"""
        if len(self.df) < 3:
            return None
        
        # ৩টি ক্যান্ডেলের বিশ্লেষণ
        c1_high = self.df['high'].iloc[-3]
        c1_low = self.df['low'].iloc[-3]
        c3_high = self.df['high'].iloc[-1]
        c3_low = self.df['low'].iloc[-1]
        
        if c3_low > c1_high:
            return "BULLISH_FVG"
        elif c3_high < c1_low:
            return "BEARISH_FVG"
        return None

    def detect_ppr(self):
        """Pivot Point Reversal (PPR) প্যাটার্ন পরীক্ষা করে"""
        if len(self.df) < 2:
            return None

        prev = self.df.iloc[-2]
        curr = self.df.iloc[-1]

        # Bullish PPR: আগেরটা রেড ক্যান্ডেল, বর্তমানটা স্ট্রং গ্রিন
        is_prev_red = prev['close'] < prev['open']
        is_curr_green = curr['close'] > curr['open']
        if is_prev_red and is_curr_green and curr['close'] > prev['high']:
            return "BULLISH_PPR"

        # Bearish PPR: আগেরটা গ্রিন ক্যান্ডেল, বর্তমানটা স্ট্রং রেড
        is_prev_green = prev['close'] > prev['open']
        is_curr_red = curr['close'] < curr['open']
        if is_prev_green and is_curr_red and curr['close'] < prev['low']:
            return "BEARISH_PPR"

        return None

# =========================================================
# 3. MASTER SIGNAL GENERATOR (MAIN LOGIC)
# =========================================================

def generate_signal(market, candles_df, payout):
    # ১. পে-আউট ফিল্টার
    if payout < BOT_SETTINGS["MIN_PAYOUT"]:
        return {"status": "REJECTED", "reason": "Low Payout"}

    engine = SignalEngine(candles_df)
    
    # ২. উপাদানসমূহ বিশ্লেষণ
    trend = engine.calculate_ema(period=BOT_SETTINGS["EMA_PERIOD"])
    at_support, at_resistance = engine.check_support_resistance()
    fvg = engine.detect_fvg()
    ppr = engine.detect_ppr()

    # ৩. সিগন্যাল লজিক কম্বিনেশন (CALL / BUY)
    if trend == "UPTREND":
        if (at_support or fvg == "BULLISH_FVG") and ppr == "BULLISH_PPR":
            return {
                "status": "SIGNAL",
                "action": "CALL (UP)",
                "market": market,
                "confidence": "HIGH",
                "reason": "Uptrend + Support/FVG + Bullish PPR"
            }

    # ৪. সিগন্যাল লজিক কম্বিনেশন (PUT / SELL)
    if trend == "DOWNTREND":
        if (at_resistance or fvg == "BEARISH_FVG") and ppr == "BEARISH_PPR":
            return {
                "status": "SIGNAL",
                "action": "PUT (DOWN)",
                "market": market,
                "confidence": "HIGH",
                "reason": "Downtrend + Resistance/FVG + Bearish PPR"
            }

    return {"status": "NO_SIGNAL", "reason": "Conditions not met"}

# =========================================================
# 4. EXECUTION DEMO (টেস্ট রান)
# =========================================================

if __name__ == "__main__":
    # ডেমো ক্যান্ডেলস্টিক ডেটা
    sample_data = {
        'open':  [1.0810, 1.0805, 1.0800, 1.0795, 1.0812],
        'high':  [1.0815, 1.0810, 1.0802, 1.0798, 1.0820],
        'low':   [1.0802, 1.0798, 1.0790, 1.0792, 1.0800],
        'close': [1.0805, 1.0800, 1.0792, 1.0810, 1.0818],
        'volume': [120, 140, 110, 200, 250]
    }
    df = pd.DataFrame(sample_data)

    # টেস্ট সিগন্যাল চেক
    result = generate_signal(market="EURUSD_otc", candles_df=df, payout=85)
    
    print("-----------------------------------------")
    print("🤖 BOTS ANALYSIS RESULT")
    print("-----------------------------------------")
    for key, value in result.items():
        print(f"{key.capitalize()}: {value}")
    print("-----------------------------------------")
