import streamlit as st
import yfinance as yf
import pandas as pd
import os
import time

st.set_page_config(page_title="منصة التداول الإلكتروني الآلية", layout="wide")
st.title("⚡ منصة التداول الآلي وعرض العقود الأمريكية الحلال")

PORTFOLIO_FILE = "tradier_simulator_portfolio.csv"
INITIAL_CASH = 100000.0
WATCHLIST = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "TSLA", "AMD", "META"]

# زر جانبي لتصفير وتطهير الحساب للبدء من جديد
if st.sidebar.button("🗑️ تصفية وتصفير الحساب بالكامل"):
    if os.path.exists(PORTFOLIO_FILE): os.remove(PORTFOLIO_FILE)
    df = pd.DataFrame(columns=["Ticker", "Type", "Buy_Price", "Qty", "Target_Price", "Stop_Price", "Total_Cost"])
    df.to_csv(PORTFOLIO_FILE, index=False)
    st.sidebar.success("✅ تم تصفير المحفظة بنجاح!")
    time.sleep(1)
    st.rerun()

# قراءة البيانات الحية لعرض الحساب
portfolio = pd.read_csv(PORTFOLIO_FILE) if os.path.exists(PORTFOLIO_FILE) else pd.DataFrame()
current_prices = {}
results = []

for ticker in WATCHLIST:
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1y")
        last_row = hist.iloc[-1]
        current_prices[ticker] = last_row['Close']
        
        info = stock.info
        debt = (info.get("totalDebt", 0) / info.get("marketCap", 1)) * 100
        roe = info.get("returnOnEquity", 0) * 100
        
        status = "انتظار نقطة دخول فنية ⏳"
        if debt >= 30.0: status = "مستبعد (غير متوافق شرعاً) ❌"
        elif roe < 15.0: status = "مستبعد (عائد مالي ضعيف) 📉"
        
        results.append({"الرمز (Ticker)": ticker, "السعر الحالي": round(last_row['Close'], 2), "حالة الفحص": status, "نسبة الديون الربوية": f"{debt:.1f}%", "العائد المالي ROE": f"{roe:.1f}%"})
    except: pass

# حساب الحساب المالي للعرض
total_cost = portfolio["Total_Cost"].sum() if not portfolio.empty else 0.0
current_cash = INITIAL_CASH - total_cost
current_val = sum(current_prices.get(r["Ticker"], r["Buy_Price"]) * 100 * r["Qty"] for _, r in portfolio.iterrows()) if not portfolio.empty else 0.0
net_pnl = current_val - total_cost

# --- عرض الملخص المالي العلوي ---
st.subheader("💰 الملخص المالي الإجمالي للحساب")
m1, m2, m3, m4 = st.columns(4)
m1.metric("💵 الرصيد الافتتاحي", f"${INITIAL_CASH:,.2f}")
m2.metric("🏦 إجمالي قيمة الحساب", f"${current_cash + current_val:,.2f}")
m3.metric("💳 السيولة المتاحة (Cash)", f"${current_cash:,.2f}")
m4.metric("📈 صافي الأرباح / الخسائر", f"${net_pnl:,.2f}", f"{((net_pnl/total_cost*100) if total_cost>0 else 0):.2f}%")

st.markdown("---")

# --- عرض جدول الممتلكات الحية ---
st.subheader("💼 جدول موجودات الحساب (المراكز المفتوحة)")
if portfolio.empty:
    st.info("ℹ️ محفظتك خالية حالياً وبوت التداول يبحث عن فرص حلال بالخلفية.")
else:
    for idx, row in portfolio.iterrows():
        t = row["Ticker"]
        cur_p = current_prices.get(t, row["Buy_Price"])
        v_pnl = (cur_p * 100 * row["Qty"]) - row["Total_Cost"]
        
        p1, p2, p3, p4 = st.columns([1, 2, 2, 1])
        p1.markdown(f"### **{t}**")
        p2.write(f"🤖 **الكمية:** {row['Qty']} عقد | **التكلفة:** ${row['Total_Cost']:,.2f}")
        p3.write(f"📊 **الربح اللحظي:** ${v_pnl:,.2f}")
        if p4.button("❌ تصفية", key=f"sel_{t}_{idx}"):
            portfolio.drop(idx).to_csv(PORTFOLIO_FILE, index=False)
            st.rerun()

st.markdown("---")
st.subheader("📋 جدول تصفية وفرز الشركات الفوري")
st.dataframe(pd.DataFrame(results), use_container_width=True, hide_index=True)
