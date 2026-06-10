import streamlit as st
import yfinance as yf
import pandas as pd
import os
import time
from datetime import datetime, timedelta

# --- إعدادات الصفحة الكلية للسحابة ---
st.set_page_config(page_title="منصة التداول الإلكتروني للخيارات", layout="wide")
st.title("⚡ منصة التداول الآلي الفوري لعقود الخيارات الأمريكية (US Options)")

PORTFOLIO_FILE = "tradier_simulator_portfolio.csv"
INITIAL_CASH = 100000.0  

WATCHLIST = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "TSLA", "AMD", "META"]

# زر جانبي لتصفير المحفظة والبدء من جديد
if st.sidebar.button("🗑️ تصفية وتصفير الحساب بالكامل"):
    if os.path.exists(PORTFOLIO_FILE):
        os.remove(PORTFOLIO_FILE)
    df = pd.DataFrame(columns=["Ticker", "Contract_Symbol", "Type", "Strike", "Expiration", "Buy_Premium", "Qty", "Target_Premium", "Stop_Premium", "Total_Cost"])
    df.to_csv(PORTFOLIO_FILE, index=False)
    st.sidebar.success("✅ تم تصفير محفظة العقود!")
    time.sleep(1)
    st.rerun()

def load_portfolio():
    if os.path.exists(PORTFOLIO_FILE):
        try:
            return pd.read_csv(PORTFOLIO_FILE)
        except: pass
    df = pd.DataFrame(columns=["Ticker", "Contract_Symbol", "Type", "Strike", "Expiration", "Buy_Premium", "Qty", "Target_Premium", "Stop_Premium", "Total_Cost"])
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
# --- محرك سحب البيانات والاتجار السحابي الفوري للعقود ---
results = []
current_prices_dict = {}

with st.spinner("جاري الاتصال بـ بورصة العقود وتحديث حسابك المالي حالياً..."):
    for ticker in WATCHLIST:
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="1y")
            if len(hist) < 200: continue
            
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
            
            # شرط حماية إضافي للتأكد من جودة البيانات الواردة للسرعة السحابية
            if current_price is None or pd.isna(current_price): continue
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
            time.sleep(0.2) 
        except: pass
# --- محرك الشراء الآلي لعقود الخيارات الحقيقية (نسخة الأمان السحابي المحدثة) ---
total_investment_cost = portfolio_df["Total_Cost"].sum() if not portfolio_df.empty else 0.0
current_cash = INITIAL_CASH - total_investment_cost

for res in results:
    t_name = res["الرمز (Ticker)"]
    if res["حالة الفحص"] == "ناجح (حلال + فني) ✅" and t_name not in portfolio_df["Ticker"].values:
        if t_name in current_prices_dict and current_prices_dict[t_name] is not None:
            cur_stock_price = current_prices_dict[t_name]
            
            try:
                # 1. صياغة تفاصيل العقد (Strike قريب من سعر السهم، وانتهاء بعد شهر تلقائياً)
                strike = round(cur_stock_price)
                exp_date = (datetime.now() + timedelta(days=30)).strftime("%Y%m%d")
                
                # 2. حساب قيمة العربون التقديرية للعقد (Premium)
                estimated_premium = round(cur_stock_price * 0.04, 2)
                contract_cost = estimated_premium * 100 * 1  
                
                # صياغة رمز العقد الرسمي القياسي للبورصة الأمريكية OCC
                strike_code = str(strike).zfill(5) + "000"
                contract_symbol = f"{t_name}{exp_date[2:]}C{strike_code}"
                
                if current_cash >= contract_cost:
                    new_contract = pd.DataFrame([{
                        "Ticker": t_name,
                        "Contract_Symbol": contract_symbol,
                        "Type": "🟢 Call Option",
                        "Strike": strike,
                        "Expiration": exp_date,
                        "Buy_Premium": estimated_premium,
                        "Qty": 1,
                        "Target_Premium": round(estimated_premium * 1.50, 2), 
                        "Stop_Premium": round(estimated_premium * 0.90, 2),    
                        "Total_Cost": contract_cost
                    }])
                    portfolio_df = pd.concat([portfolio_df, new_contract], ignore_index=True)
                    save_portfolio(portfolio_df)
                    st.toast(f"🚀 [تداول آلي]: تم شراء عقد خيار {contract_symbol} تلقائياً!")
                    time.sleep(0.5)
                    st.rerun()
            except: pass

# --- حساب الأرصدة الحية لمحفظة العقود مع الرافعة المالية ---
current_portfolio_value = 0.0
if not portfolio_df.empty:
    for _, row in portfolio_df.iterrows():
        t = row["Ticker"]
        if t in current_prices_dict and current_prices_dict[t] is not None:
            stock_change = (current_prices_dict[t] - (row["Total_Cost"] / 100)) / (row["Total_Cost"] / 100)
            simulated_current_premium = row["Buy_Premium"] * (1 + (stock_change * 5)) 
            current_portfolio_value += max(0.1, simulated_current_premium) * 100 * int(row["Qty"])

net_profit_loss = current_portfolio_value - total_investment_cost
total_account_equity = current_cash + current_portfolio_value
pnl_percentage = (net_profit_loss / total_investment_cost * 100) if total_investment_cost > 0 else 0.0
# --- عرض الملخص المالي العلوي للحساب ---
st.subheader("💰 الموقف المالي الإجمالي لمحافظ العقود (Options Portfolio)")
m_col1, m_col2, m_col3, m_col4 = st.columns(4)
m_col1.metric("💵 الرصيد الافتتاحي", f"${INITIAL_CASH:,.2f}")
m_col2.metric("🏦 إجمالي القيمة الحالية للمحفظة", f"${total_account_equity:,.2f}")
m_col3.metric("💳 السيولة المتاحة لشراء العقود", f"${current_cash:,.2f}")
if net_profit_loss >= 0:
    m_col4.metric("📈 صافي أرباح العقود حياً", f"+${net_profit_loss:,.2f}", f"{pnl_percentage:.2f}%")
else:
    m_col4.metric("📉 صافي أرباح العقود حياً", f"-${abs(net_profit_loss):,.2f}", f"{pnl_percentage:.2f}%", delta_color="inverse")

st.markdown("---")

# --- جدول موجودات وممتلكات العقود الحالية ---
st.subheader("💼 كشف ممتلكات الحساب من عقود الخيارات الأمريكية المفتوحة")
if portfolio_df.empty:
    st.info("ℹ️ محفظتك خالية من عقود الخيارات حالياً، وبوت الفرز يراقب الفرص بنشاط.")
else:
    for index, row in portfolio_df.iterrows():
        t = row["Ticker"]
        cost = float(row["Total_Cost"])
        
        if t in current_prices_dict and current_prices_dict[t] is not None:
            stock_change = (current_prices_dict[t] - row["Buy_Premium"]) / row["Buy_Premium"]
            cur_premium = max(0.05, row["Buy_Premium"] * (1 + (stock_change * 5)))
        else:
            cur_premium = row["Buy_Premium"]
            
        cur_contract_value = cur_premium * 100 * int(row["Qty"])
        v_pnl = cur_contract_value - cost
        v_pnl_pct = (v_pnl / cost) * 100 if cost > 0 else 0.0
        
        p_col1, p_col2, p_col3, p_col4, p_col5 = st.columns([1.5, 2, 2, 2, 1])
        p_col1.markdown(f"📦 **{row['Contract_Symbol']}**")
        p_col2.write(f"🏷️ **النوع:** {row['Type']} | **سعر التنفيذ:** {row['Strike']}$")
        if v_pnl >= 0:
            p_col3.markdown(f"<span style='color:green; font-weight:bold;'>📈 ربح العقد: +${v_pnl:,.2f} ({v_pnl_pct:.1f}%)</span>", unsafe_allow_html=True)
        else:
            p_col3.markdown(f"<span style='color:red; font-weight:bold;'>📉 خسارة العقد: -${abs(v_pnl):,.2f} ({v_pnl_pct:.1f}%)</span>", unsafe_allow_html=True)
            
        p_col4.write(f"💵 سعر الشراء: {row['Buy_Premium']}$ | الحية: {cur_premium:.2f}$")
        if p_col5.button("❌ تصفية العقد", key=f"sell_{t}_{index}"):
            portfolio_df = portfolio_df.drop(index).reset_index(drop=True)
            save_portfolio(portfolio_df)
            st.toast(f"📢 تم بيع وإغلاق عقد الخيار لـ {t} فوراً!")
            time.sleep(0.5)
            st.rerun()

st.markdown("---")

# جدول تصفية الشركات الملون
if results:
    df = pd.DataFrame(results)
    styled_df = df.style.map(color_passed_rows, subset=["حالة الفحص"])
    st.subheader("📋 جدول تصفية وفرز الشركات الفوري")
    st.dataframe(styled_df, use_container_width=True, hide_index=True)
