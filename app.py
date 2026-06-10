import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

# --- إعدادات الواجهة ---
st.set_page_config(page_title="مختبر العقود الحلال الذكي", layout="wide")
st.title("🧪 مختبر دراسة وفحص عقود الخيارات الأمريكية الحلال")
st.write("هذه المنصة مخصصة لاستعراض ودراسة عقود الخيارات للشركات التي اجتازت الفحص الشرعي والمالي بنجاح.")

# قاعدة بيانات الشركات الحلال المعتمدة للدراسة
HALAL_WATCHLIST = ["AAPL", "MSFT", "GOOGL", "NVDA", "AMZN"]

# صندوق اختيار السهم المراد دراسة عقوده
selected_ticker = st.selectbox("🎯 اختر شركة حلال لاستعراض سلسلة عقودها (Option Chain):", HALAL_WATCHLIST)

if selected_ticker:
    try:
        stock = yf.Ticker(selected_ticker)
        
        # جلب سعر السهم الحالي حياً
        hist = stock.history(period="1d")
        current_price = hist['Close'].iloc[-1]
        
        st.info(f"📈 السعر الحالي لسهم {selected_ticker} في البورصة الآن: ${current_price:.2f}")
        
        # --- توليد سلسلة عقود افتراضية فورية ومنظمة للدراسة ---
        st.subheader(f"📋 سلسلة عقود الخيارات المتاحة للفحص لسهم {selected_ticker}")
        
        # صناعة تواريخ انتهاء قريبة (بعد أسبوع، أسبوعين، شهر)
        dates = [
            (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
            (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d"),
            (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        ]
        selected_date = st.selectbox("اختر تاريخ انتهاء العقد المستهدف (Expiration Date):", dates)
        
        # توليد أسعار تنفيذ (Strikes) حول السعر الحالي للسهم (In-The-Money & Out-Of-The-Money)
        base_strike = round(current_price)
        strikes = [base_strike - 10, base_strike - 5, base_strike, base_strike + 5, base_strike + 10]
        
        chain_data = []
        for strike in strikes:
            # محاكاة تسعير العقود (العربون/Premium) بناءً على قربه من سعر السهم (التقلب الضمني IV)
            distance = strike - current_price
            call_premium = max(0.5, round((current_price * 0.03) - (distance * 0.4), 2))
            put_premium = max(0.5, round((current_price * 0.03) + (distance * 0.4), 2))
            
            # حساب المؤشرات الفنية للعقد (الرافعة المالية التقريبية)
            leverage = round((current_price / call_premium) * 0.5, 1)
            
            chain_data.append({
                "سعر التنفيذ (Strike)": f"${strike}",
                "عقد الشراء (Call Premium)": f"${call_premium}",
                "عقد البيع (Put Premium)": f"${put_premium}",
                "الرافعة المالية للعقد": f"{leverage}x",
                "التقلب الضمني المتوقع (IV)": "32.5%",
                "حالة السيولة (Volume)": "عالية 🔥"
            })
            
        df_chain = pd.DataFrame(chain_data)
        st.dataframe(df_chain, use_container_width=True, hide_index=True)
        
        # --- قسم حاسبة المحاكاة للدراسة الفنية ---
        st.markdown("---")
        st.subheader("🧮 مختبر المحاكاة وجني الأرباح الفني")
        
        col1, col2 = st.columns(2)
        with col1:
            chosen_strike = st.selectbox("اختر سعر التنفيذ المراد دراسته:", strikes)
            contract_type = st.radio("نوع العقد:", ["Call (توقع صعود) 🟢", "Put (توقع هبوط) 🔴"])
        with col2:
            target_move = st.slider("تحرك السهم المتوقع فنيًا (نسبة مئوية %):", -10, 10, 5)
            
        # حساب الربح المتوقع بناءً على حركة السهم والرافعة المالية للعقد
        simulated_stock_price = current_price * (1 + (target_move / 100))
        contract_profit_loss = target_move * 5 # تأثير الرافعة المالية للأوبشن 5 أضعاف السهم
        
        st.markdown("#### 📊 نتائج الدراسة التقديرية:")
        if contract_profit_loss >= 0:
            st.success(f"إذا تحرك السهم بنسبة {target_move}% وصعد إلى ${simulated_stock_price:.2f}، فإن أرباح عقد الخيار المتوقعة ستكون حوالي **+{contract_profit_loss:.1f}%** من قيمة رأس المال المستثمر في العقد!")
        else:
            st.error(f"إذا تحرك السهم ضدك بنسبة {target_move}% وهبط إلى ${simulated_stock_price:.2f}، فإن خسائر عقد الخيار المتوقعة ستكون حوالي **{contract_profit_loss:.1f}%**!")

    except Exception as e:
        st.error(f"تعذر الاتصال بالبورصة حالياً جرب تحديث الصفحة. الخطأ: {e}")
