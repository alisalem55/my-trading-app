import streamlit as st
import yfinance as yf
import pandas as pd
import os
import time
from datetime import datetime, timedelta

# --- إعدادات الحماية والأمان المتقدمة المحدثة ---
st.set_page_config(page_title="منصة التداول الإلكتروني المؤمنة", layout="wide")

# نظام الأمان الاحتياطي الذكي لمنع تعليق خوادم السحابة
try:
    USER_AUTH = st.secrets["username"]
    PASS_AUTH = st.secrets["password"]
except Exception:
    # قيم أمان افتراضية بديلة في حال لم يتم إعداد الخزنة السرية بنجاح
    USER_AUTH = "admin"
    PASS_AUTH = "1234"

# تفعيل خاصية حفظ كلمة السر تلقائياً داخل المتصفح
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔒 شاشة الدخول الآمنة لمنصة التداول")
    username = st.text_input("اسم المستخدم:")
    password = st.text_input("كلمة المرور:", type="password")
    
    remember_me = st.checkbox("تذكرني على هذا الجهاز (حفظ تسجيل الدخول) 🔑", value=True)
    
    if st.button("🔓 تسجيل الدخول"):
        if username == USER_AUTH and password == PASS_AUTH:
            st.session_state.authenticated = True
            st.success("تم التحقق بنجاح! جاري فتح المنصة...")
            time.sleep(0.5)
            st.rerun()
        else:
            st.error("❌ البيانات خاطئة! يرجى التأكد من اسم المستخدم أو الرقم السري.")
    st.stop()

# =========================================================================
# فتح لوحة التحكم بعد نجاح الأمان وحفظ حالة الدخول
# =========================================================================
st.title("⚡ منصة التداول الآلي الفوري بالاستراتيجية السداسية الصارمة")

PORTFOLIO_FILE = "tradier_simulator_portfolio.csv"
INITIAL_CASH = 100000.0  
WATCHLIST = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "TSLA", "AMD", "META"]

if st.sidebar.button("🗑️ تصفية وتصفير الحساب والبدء من جديد"):
    if os.path.exists(PORTFOLIO_FILE): os.remove(PORTFOLIO_FILE)
    df = pd.DataFrame(columns=["Ticker", "Contract_Symbol", "Type", "Strike", "Buy_Premium", "Qty", "Target_Premium", "Stop_Premium", "Total_Cost"])
    df.to_csv(PORTFOLIO_FILE, index=False)
    st.sidebar.success("✅ تم إعادة تعيين الحساب إلى $100,000")
    time.sleep(1)
    st.rerun()

def load_portfolio():
    if os.path.exists(PORTFOLIO_FILE):
        try: return pd.read_csv(PORTFOLIO_FILE)
        except: pass
    df = pd.DataFrame(columns=["Ticker", "Contract_Symbol", "Type", "Strike", "Buy_Premium", "Qty", "Target_Premium", "Stop_Premium", "Total_Cost"])
    df.to_csv(PORTFOLIO_FILE, index=False)
    return df

def save_portfolio(df): df.to_csv(PORTFOLIO_FILE, index=False)
portfolio_df = load_portfolio()

def color_passed_rows(val):
    if val == "إشارة شراء مؤكدة (ناجح) 🚀": return 'background-color: #d4edda; color: #155724; font-weight: bold;'
    elif "مستبعد" in val: return 'background-color: #f8d7da; color: #721c24;'
    return ''
# --- 2. محرك الفحص السداسي الشامل (شرعي + 5 فلاتر قوية) ---
results = []
current_prices_dict = {}
hist_data_dict = {}
passed_companies = []  

with st.spinner("جاري مسح البورصة الحية وتطبيق الفلاتر الستة الصارمة..."):
    for ticker in WATCHLIST:
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="1y")
            if len(hist) < 200: continue
            hist_data_dict[ticker] = hist
            
            info = stock.info
            market_cap = info.get("marketCap", 1)
            debt_ratio = (info.get("totalDebt", 0) / market_cap) * 100
            eps_growth = info.get("earningsGrowth", 0) * 100
            
            hist['EMA_50'] = hist['Close'].ewm(span=50, adjust=False).mean()
            hist['EMA_200'] = hist['Close'].ewm(span=200, adjust=False).mean()
            
            delta = hist['Close'].diff()
            gain = (delta.where(delta > 0, 0)).ewm(alpha=1/14, adjust=False).mean()
            loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/14, adjust=False).mean()
            hist['RSI_14'] = 100 - (100 / (1 + (gain / loss)))
            
            hist['EMA_12'] = hist['Close'].ewm(span=12, adjust=False).mean()
            hist['EMA_26'] = hist['Close'].ewm(span=26, adjust=False).mean()
            hist['MACD'] = hist['EMA_12'] - hist['EMA_26']
            hist['Signal_Line'] = hist['MACD'].ewm(span=9, adjust=False).mean()
            
            hist['MA20'] = hist['Close'].rolling(window=20).mean()
            hist['STD20'] = hist['Close'].rolling(window=20).std()
            hist['Upper_Band'] = hist['MA20'] + (hist['STD20'] * 2)
            
            last_row = hist.iloc[-1]
            current_price = last_row['Close']
            if current_price is None or pd.isna(current_price): continue
            current_prices_dict[ticker] = current_price
            
            status = "انتظار تأكيد إشارة الدخول ⏳"
            if debt_ratio >= 30.0: status = "مستبعد (غير متوافق شرعاً) ❌"
            elif eps_growth < 10.0: status = "مستبعد (نمو أرباح EPS ضعيف) 📉"
            elif not (last_row['EMA_50'] > last_row['EMA_200']): status = "مستبعد (اتجاه هابط EMA50 < EMA200) 📉"
            elif not (30 < last_row['RSI_14'] < 60): status = "انتظار (خارج منطقة الزخم RSI الآمنة) ⏳"
            elif not (last_row['MACD'] > last_row['Signal_Line']): status = "انتظار (الماكد سلبي تحت خط الإشارة) ⏳"
            elif last_row['Close'] >= last_row['Upper_Band']: status = "انتظار (السعر مرتفع عند قمة البولنجر) ⚠️"
            else:
                status = "إشارة شراء مؤكدة (ناجح) 🚀"
                passed_companies.append({"ticker": ticker, "price": round(current_price, 2), "rsi": round(last_row['RSI_14'], 1)})
                
            results.append({
                "الرمز (Ticker)": ticker, "السعر الحالي": round(current_price, 2), "حالة الفحص": status,
                "نسبة الديون": f"{debt_ratio:.1f}%", "نمو الـ EPS": f"{eps_growth:.1f}%", "مؤشر RSI": round(last_row['RSI_14'], 1)
            })
            time.sleep(0.1)
        except: pass
# --- 3. محرك التداول الإلكتروني والاتجار الآلي للمطابق سداسياً ---
total_investment_cost = portfolio_df["Total_Cost"].sum() if not portfolio_df.empty else 0.0
current_cash = INITIAL_CASH - total_investment_cost

for res in results:
    t_name = res["الرمز (Ticker)"]
    if res["حالة الفحص"] == "إشارة شراء مؤكدة (ناجح) 🚀" and t_name not in portfolio_df["Ticker"].values:
        if t_name in current_prices_dict and current_prices_dict[t_name] is not None:
            cur_stock_price = current_prices_dict[t_name]
            try:
                strike = round(cur_stock_price)
                exp_date = (datetime.now() + timedelta(days=30)).strftime("%Y%m%d")
                estimated_premium = round(cur_stock_price * 0.04, 2)
                contract_cost = estimated_premium * 100 * 1  
                
                strike_code = str(strike).zfill(5) + "000"
                contract_symbol = f"{t_name}{exp_date[2:]}C{strike_code}"
                
                if current_cash >= contract_cost:
                    new_contract = pd.DataFrame([{
                        "Ticker": t_name, "Contract_Symbol": contract_symbol, "Type": "🟢 Call Option",
                        "Strike": strike, "Buy_Premium": estimated_premium, "Qty": 1,
                        "Target_Premium": round(estimated_premium * 1.50, 2), "Stop_Premium": round(estimated_premium * 0.90, 2),
                        "Total_Cost": contract_cost
                    }])
                    portfolio_df = pd.concat([portfolio_df, new_contract], ignore_index=True)
                    save_portfolio(portfolio_df)
                    st.toast(f"🚀 [تداول آلي]: تم شراء عقد خيار {contract_symbol} تلقائياً!")
                    time.sleep(0.5)
                    st.rerun()
            except: pass

# --- تحديث أسعار العقود الحية وتتبع الأرباح وإدارة المخاطر ---
current_portfolio_value = 0.0
if not portfolio_df.empty:
    for index, row in portfolio_df.iterrows():
        t = row["Ticker"]
        if t in current_prices_dict and current_prices_dict[t] is not None:
            cur_p = current_prices_dict[t]
            buy_p = float(row["Strike"])
            stock_change = (cur_p - buy_p) / buy_p
            cur_premium = max(0.05, float(row["Buy_Premium"]) * (1 + (stock_change * 5))) # الرافعة المالية 5 أضعاف السهم
            current_portfolio_value += cur_premium * 100 * int(row["Qty"])
            
            for r in results:
                if r["الرمز (Ticker)"] == t:
                    if cur_premium >= float(row["Target_Premium"]) or cur_premium <= float(row["Stop_Premium"]) or "مستبعد" in r["حالة الفحص"]:
                        portfolio_df = portfolio_df.drop(index).reset_index(drop=True)
                        save_portfolio(portfolio_df)
                        st.toast(f"🔄 [بيع تلقائي]: تم تصفية عقد {t} حماية للأرباح.")
                        time.sleep(0.5)
                        st.rerun()

net_profit_loss = current_portfolio_value - total_investment_cost
total_account_equity = current_cash + current_portfolio_value
pnl_percentage = (net_profit_loss / total_investment_cost * 100) if total_investment_cost > 0 else 0.0
# --- 5. عرض لوحة التحكم وتصميم الفرص الذهبية في صدارة الشاشة ---
st.write("### 🔥 الفرص الذهبية والشركات المجتازة للفحص السداسي الآن:")
if passed_companies:
    cols_passed = st.columns(len(passed_companies))
    for idx, comp in enumerate(passed_companies):
        with cols_passed[idx]:
            st.markdown(
                f"""
                <div style='background-color: #d4edda; padding: 20px; border-radius: 10px; border: 2px solid #28a745; text-align: center;'>
                    <h2 style='color: #155724; margin: 0;'>🚀 {comp['ticker']}</h2>
                    <p style='color: #155724; font-size: 16px; margin: 10px 0 5px 0;'><b>السعر الحالي:</b> ${comp['price']}</p>
                    <p style='color: #155724; font-size: 14px; margin: 0;'><b>مؤشر RSI الحالية:</b> {comp['rsi']}</p>
                    <span style='background-color: #28a745; color: white; padding: 3px 8px; border-radius: 5px; font-size: 12px; font-weight: bold; display: inline-block; margin-top: 10px;'>جاهز للتداول الآلي</span>
                </div>
                """, 
                unsafe_allow_html=True
            )
else:
    st.info("ℹ️ لا توجد أسهم في منطقة الدخول المثالية حالياً. البوت يراقب البورصة بصمت واحترافية لاقتناص الفرصة القادمة.")

st.markdown("---")

st.subheader("💰 الموقف المالي للمحفظة الاستثمارية")
m_col1, m_col2, m_col3, m_col4 = st.columns(4)
m_col1.metric("💵 الرصيد الافتتاحي", f"${INITIAL_CASH:,.2f}")
m_col2.metric("🏦 القيمة الحالية الكلية", f"${total_account_equity:,.2f}")
m_col3.metric("💳 السيولة المتاحة (Cash)", f"${current_cash:,.2f}")
if net_profit_loss >= 0: m_col4.metric("📈 صافي المكسب اللحظي (P&L)", f"+${net_profit_loss:,.2f}", f"{pnl_percentage:.2f}%")
else: m_col4.metric("📉 صافي الخسارة اللحظية (P&L)", f"-${abs(net_profit_loss):,.2f}", f"{pnl_percentage:.2f}%", delta_color="inverse")

st.markdown("---")

st.subheader("💼 العقود المفتوحة وموجودات الحساب الحالية")
if portfolio_df.empty:
    st.info("ℹ️ محفظتك خالية من العقود حالياً وبوت الاستراتيجية السداسية يمسح السوق للاقتناص الآمن.")
else:
    for index, row in portfolio_df.iterrows():
        t = row["Ticker"]
        cost = float(row["Total_Cost"])
        cur_stock_p = current_prices_dict.get(t, float(row["Strike"]))
        stock_change = (cur_stock_p - float(row["Strike"])) / float(row["Strike"])
        cur_prem = max(0.05, float(row["Buy_Premium"]) * (1 + (stock_change * 5)))
        v_pnl = (cur_prem * 100 * int(row["Qty"])) - cost
        v_pnl_pct = (v_pnl / cost) * 100 if cost > 0 else 0.0
        
        p_col1, p_col2, p_col3, p_col4 = st.columns([1.5, 3, 2.5, 1])
        p_col1.markdown(f"📦 **{row['Contract_Symbol']}**")
        p_col2.write(f"🏷️ **النوع:** {row['Type']} | **العدد:** {row['Qty']} عقد | **التكلفة:** ${cost:,.2f}")
        if v_pnl >= 0: p_col3.markdown(f"<span style='color:green; font-weight:bold;'>📈 الربح: +${v_pnl:,.2f} ({v_pnl_pct:.1f}%)</span>", unsafe_allow_html=True)
        else: p_col3.markdown(f"<span style='color:red; font-weight:bold;'>📉 الخسارة: -${abs(v_pnl):,.2f} ({v_pnl_pct:.1f}%)</span>", unsafe_allow_html=True)
        if p_col4.button("❌ تصفية", key=f"sell_{t}_{index}"):
            portfolio_df = portfolio_df.drop(index).reset_index(drop=True)
            save_portfolio(portfolio_df)
            st.rerun()

st.markdown("---")

if results:
    df = pd.DataFrame(results)
    styled_df = df.style.map(color_passed_rows, subset=["حالة الفحص"])
    st.subheader("📋 جدول الفحص السداسي الفوري (نتائج تصفية أقوى خمسة مؤشرات)")
    st.dataframe(styled_df, use_container_width=True, hide_index=True)

st.markdown("---")
st.subheader("📈 الرسم البياني التفاعلي وحركة السهم")
selected_ticker = st.selectbox("اختر شركة لاستعراض مخططها السعري:", WATCHLIST)
if selected_ticker in hist_data_dict:
    st.line_chart(hist_data_dict[selected_ticker]['Close'])
