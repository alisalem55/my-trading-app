import streamlit as st
import yfinance as yf
import pandas as pd
import os
import time

# --- إعدادات الصفحة الكلية لل السحابة ---
st.set_page_config(page_title="منصة التداول الإلكتروني الحية", layout="wide")
st.title("⚡ منصة التداول الآلي وعرض العقود الأمريكية الحلال")

PORTFOLIO_FILE = "tradier_simulator_portfolio.csv"
INITIAL_CASH = 100000.0  

WATCHLIST = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "TSLA", "AMD", "META"]

# زر جانبي لتصفير المحفظة والبدء من جديد
if st.sidebar.button("🗑️ تصفية وتصفير الحساب بالكامل"):
    if os.path.exists(PORTFOLIO_FILE):
        os.remove(PORTFOLIO_FILE)
    df = pd.DataFrame(columns=["Ticker", "Type", "Buy_Price", "Qty", "Target_Price", "Stop_Price", "Total_Cost"])
    df.to_csv(PORTFOLIO_FILE, index=False)
    st.sidebar.success("✅ تم تصفير المحفظة!")
    time.sleep(1)
    st.rerun()

def load_portfolio():
    if os.path.exists(PORTFOLIO_FILE):
        try:
            return pd.read_csv(PORTFOLIO_FILE)
        except:
            pass
    df = pd.DataFrame(columns=["Ticker", "Type", "Buy_Price", "Qty", "Target_Price", "Stop_Price", "Total_Cost"])
    df.to_csv(PORTFOLIO_FILE, index=False)
    return df

def save_portfolio(df):
    df.to_csv(PORTFOLIO_FILE, index=False)

portfolio_df = load_portfolio()

def color_passed_rows(val):
    if val == "ناجح (حلال + فني) ✅":
        return 'background-color: #d4edda; color: #155724; font-weight: bold;'
    elif "مستبعد" in val:
        return 'background-color: #f8d7da; color: #721c24;'
    return ''

# --- محرك سحب البيانات والاتجار السحابي الفوري ---
results = []
hist_data_dict = {}
current_prices_dict = {}

# صندوق استعلام آمن لمنع تعليق خوادم السحابة
with st.spinner("جاري الاتصال بالبورصة وتحديث حسابك المالي حالياً..."):
    for ticker in WATCHLIST:
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="1y")
            if len(hist) < 200: continue
            hist_data_dict[ticker] = hist
            
            info = stock.info
            market_cap = info.get("marketCap", 1)
            total_debt = info.get("totalDebt", 0)
            debt_ratio = (total_debt / market_cap) * 100
            roe = info.get("returnOnEquity", 0) * 100
            
            hist['EMA_50'] = hist['Close'].ewm(span=50, adjust=False).mean()
            hist['EMA_200'] = hist['Close'].ewm(span=200, adjust=False).mean()
            delta = hist['Close'].diff()
            gain = (delta.where(delta > 0, 0)).ewm(alpha=1/14, adjust=False).mean()
            loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/14, adjust=False).mean()
            hist['RSI_14'] = 100 - (100 / (1 + (gain / loss)))
            
            last_row = hist.iloc[-1]
            current_price = last_row['Close']
            current_prices_dict[ticker] = current_price
            
            status = "انتظار نقطة دخول فنية ⏳"
            if debt_ratio >= 30.0: status = "مستبعد (غير متوافق شرعاً) ❌"
            elif roe < 15.0: status = "مستبعد (عائد مالي ضعيف) 📉"
            elif (last_row['EMA_50'] > last_row['EMA_200']) and (35 < last_row['RSI_14'] < 60): 
                status = "ناجح (حلال + فني) ✅"
                
            results.append({
                "الرمز (Ticker)": ticker, "السعر الحالي": round(current_price, 2), "حالة الفحص": status,
                "نسبة الديون الربوية": f"{debt_ratio:.1f}%", "العائد المالي ROE": f"{roe:.1f}%", "مؤشر القوة RSI": round(last_row['RSI_14'], 1)
            })
            time.sleep(0.5) # حماية من الحظر السحابي
        except: pass

# حساب الحساب الكلي
total_investment_cost = portfolio_df["Total_Cost"].sum() if not portfolio_df.empty else 0.0
current_portfolio_value = 0.0
if not portfolio_df.empty:
    for _, row in portfolio_df.iterrows():
        t = row["Ticker"]
        if t in current_prices_dict:
            current_portfolio_value += current_prices_dict[t] * 100 * int(row["Qty"])

net_profit_loss = current_portfolio_value - total_investment_cost
current_cash = INITIAL_CASH - total_investment_cost
total_account_equity = current_cash + current_portfolio_value
pnl_percentage = (net_profit_loss / total_investment_cost * 100) if total_investment_cost > 0 else 0.0

# --- [محرك الشراء والبيع التلقائي المباشر على السحابة] ---
# 1. الشراء التلقائي
for res in results:
    t_name = res["الرمز (Ticker)"]
    if res["حالة الفحص"] == "ناجح (حلال + فني) ✅" and t_name not in portfolio_df["Ticker"].values:
        cur_m_price = current_prices_dict[t_name]
        order_cost = cur_m_price * 100 * 1
        if current_cash >= order_cost:
            new_trade = pd.DataFrame([{
                "Ticker": t_name, "Type": "عقد شراء آلي (Call 🟢)", "Buy_Price": round(cur_m_price, 2),
                "Qty": 1, "Target_Price": round(cur_m_price * 1.50, 2), "Stop_Price": round(cur_m_price * 0.90, 2), "Total_Cost": order_cost
            }])
            portfolio_df = pd.concat([portfolio_df, new_trade], ignore_index=True)
            save_portfolio(portfolio_df)
            st.toast(f"🚀 تم اقتناص فرصة وشراء عقد لـ {t_name} تلقائياً!")
            time.sleep(0.5)
            st.rerun()

# --- عرض الملخص المالي العلوي لل حساب ---
st.subheader("💰 الملخص المالي الإجمالي للحساب")
m_col1, m_col2, m_col3, m_col4 = st.columns(4)
m_col1.metric("💵 الرصيد الافتتاحي", f"${INITIAL_CASH:,.2f}")
m_col2.metric("🏦 إجمالي القيمة الحالية", f"${total_account_equity:,.2f}")
m_col3.metric("💳 السيولة النقدية المتاحة", f"${current_cash:,.2f}")
if net_profit_loss >= 0:
    m_col4.metric("📈 صافي الأرباح / الخسائر", f"+${net_profit_loss:,.2f}", f"{pnl_percentage:.2f}%")
else:
    m_col4.metric("📉 صافي الأرباح / الخسائر", f"-${abs(net_profit_loss):,.2f}", f"{pnl_percentage:.2f}%", delta_color="inverse")

st.markdown("---")

# --- جدول موجودات وممتلكات الحساب الحالية ---
st.subheader("💼 جدول موجودات الحساب (المراكز المفتوحة)")
if portfolio_df.empty:
    st.info("ℹ️ محفظتك خالية حالياً، والبوت يراقب الفرص بنشاط.")
else:
    for index, row in portfolio_df.iterrows():
        t = row["Ticker"]
        cost = float(row["Total_Cost"])
        cur_p = current_prices_dict.get(t, float(row["Buy_Price"]))
        cur_value = cur_p * 100 * int(row["Qty"])
        v_pnl = cur_value - cost
        v_pnl_pct = (v_pnl / cost) * 100 if cost > 0 else 0.0
        
        p_col1, p_col2, p_col3, p_col4, p_col5 = st.columns([1, 2, 2, 2, 1.5])
        p_col1.markdown(f"### **{t}**")
        p_col2.write(f"📦 **الكمية:** {row['Qty']} عقد | **التكلفة:** ${cost:,.2f}")
        if v_pnl >= 0:
            p_col3.markdown(f"<span style='color:green; font-weight:bold;'>📈 الربح: +${v_pnl:,.2f} ({v_pnl_pct:.1f}%)</span>", unsafe_allow_html=True)
        else:
            p_col3.markdown(f"<span style='color:red; font-weight:bold;'>📉 الخسارة: -${abs(v_pnl):,.2f} ({v_pnl_pct:.1f}%)</span>", unsafe_allow_html=True)
            
        p_col4.write(f"🎯 الهدف: {row['Target_Price']}$ | الوقف: {row['Stop_Price']}$")
        if p_col5.button("❌ بيع", key=f"sell_{t}_{index}"):
            portfolio_df = portfolio_df.drop(index).reset_index(drop=True)
            save_portfolio(portfolio_df)
            st.toast(f"📢 تم تصفية وبيع {t} بنجاح!")
            time.sleep(0.5)
            st.rerun()

st.markdown("---")

# جدول تصفية الشركات الملون
if results:
    df = pd.DataFrame(results)
    styled_df = df.style.map(color_passed_rows, subset=["حالة الفحص"])
    st.subheader("📋 جدول تصفية وفرز الشركات الفوري")
    st.dataframe(styled_df, use_container_width=True, hide_index=True)

st.markdown("---")

# المخطط البياني التفاعلي
st.subheader("📈 الرسم البياني التفاعلي وحركة السهم")
selected_ticker = st.selectbox("اختر شركة لاستعراض المخطط الفني:", WATCHLIST)
if selected_ticker in hist_data_dict:
    st.line_chart(hist_data_dict[selected_ticker][['Close']])
