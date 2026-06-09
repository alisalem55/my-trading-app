import time
import os
import yfinance as yf
import pandas as pd

PORTFOLIO_FILE = "tradier_simulator_portfolio.csv"
WATCHLIST = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "TSLA", "AMD", "META"]
INITIAL_CASH = 100000.0

def load_portfolio():
    if os.path.exists(PORTFOLIO_FILE):
        return pd.read_csv(PORTFOLIO_FILE)
    df = pd.DataFrame(columns=["Ticker", "Type", "Buy_Price", "Qty", "Target_Price", "Stop_Price", "Total_Cost"])
    df.to_csv(PORTFOLIO_FILE, index=False)
    return df

def save_portfolio(df):
    df.to_csv(PORTFOLIO_FILE, index=False)

def run_automated_trading():
    portfolio = load_portfolio()
    current_prices = {}
    results = []
    
    # حساب الكاش الحالي المتوفر
    total_cost = portfolio["Total_Cost"].sum() if not portfolio.empty else 0.0
    current_cash = INITIAL_CASH - total_cost

    # 1. سحب وتحليل بيانات السوق الحية وفلترتها شرعياً وفنياً
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
            
            # حساب المؤشرات الفنية
            hist['EMA_50'] = hist['Close'].ewm(span=50, adjust=False).mean()
            hist['EMA_200'] = hist['Close'].ewm(span=200, adjust=False).mean()
            delta = hist['Close'].diff()
            gain = (delta.where(delta > 0, 0)).ewm(alpha=1/14, adjust=False).mean()
            loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/14, adjust=False).mean()
            hist['RSI_14'] = 100 - (100 / (1 + (gain / loss)))
            
            last_row = hist.iloc[-1]
            current_prices[ticker] = last_row['Close']
            
            status = "انتظار"
            if debt_ratio >= 30.0 or roe < 15.0:
                status = "مستبعد"
            elif (last_row['EMA_50'] > last_row['EMA_200']) and (35 < last_row['RSI_14'] < 60):
                status = "ناجح"
                
            results.append({"Ticker": ticker, "Price": last_row['Close'], "Status": status, "EMA50": last_row['EMA_50'], "EMA200": last_row['EMA_200'], "RSI": last_row['RSI_14']})
        except: pass

    # 2. محرك البيع التلقائي لإدارة المخاطر وعكس الاتجاه
    if not portfolio.empty:
        for index, row in portfolio.iterrows():
            t = row["Ticker"]
            if t in current_prices:
                cur_p = current_prices[t]
                buy_p = float(row["Buy_Price"])
                curr_return = (cur_p - buy_p) / buy_p
                
                # البحث عن مؤشرات السهم الحالية لعكس الاتجاه
                for r in results:
                    if r["Ticker"] == t:
                        if cur_p >= float(row["Target_Price"]) or cur_p <= float(row["Stop_Price"]) or (curr_return > 0 and (r["EMA50"] < r["EMA200"] or r["RSI"] > 75)):
                            portfolio = portfolio.drop(index).reset_index(drop=True)
                            save_portfolio(portfolio)
                            break

    # 3. محرك الشراء الآلي بالكامل عند توفر فرصة حلال وسيولة كافية
    for r in results:
        t_name = r["Ticker"]
        if r["Status"] == "ناجح" and t_name not in portfolio["Ticker"].values:
            order_cost = current_prices[t_name] * 100 * 1
            if current_cash >= order_cost:
                new_trade = pd.DataFrame([{
                    "Ticker": t_name, "Type": "عقد شراء آلي (Call 🟢)", "Buy_Price": round(current_prices[t_name], 2),
                    "Qty": 1, "Target_Price": round(current_prices[t_name] * 1.50, 2), "Stop_Price": round(current_prices[t_name] * 0.90, 2), "Total_Cost": order_cost
                }])
                portfolio = pd.concat([portfolio, new_trade], ignore_index=True)
                save_portfolio(portfolio)
                current_cash -= order_cost

if __name__ == "__main__":
    while True:
        run_automated_trading()
        time.sleep(60) # تحديث آلي وفحص مستمر كل دقيقة خلف الكواليس
