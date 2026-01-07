import streamlit as st
import pandas as pd
import plotly.express as px
import yfinance as yf
from datetime import datetime

st.set_page_config(page_title="金银比价监测", layout="wide", page_icon="👑")
st.title("👑 宏观对冲监测：伦敦金(XAU) / 伦敦银(XAG)")

@st.cache_data(ttl=60)
def get_data():
    # 获取数据，yahoo finance代码: GC=F(黄金期货) SI=F(白银期货) 
    # 或者用现货 XAUUSD=X, XAGUSD=X，这里用现货更准
    data = yf.download("XAUUSD=X XAGUSD=X", period="2y", interval="1d", progress=False)
    
    # 数据清洗标准流程
    if isinstance(data.columns, pd.MultiIndex):
        df = data['Close'].reset_index()
    else:
        df = data.reset_index()

    # 简单粗暴的重命名，防止列名变动
    df.columns = [str(col).replace('=X', '') for col in df.columns]
    
    # 自动找哪列是金，哪列是银
    date_col = [c for c in df.columns if 'Date' in c][0]
    gold_col = [c for c in df.columns if 'XAU' in c][0]
    silver_col = [c for c in df.columns if 'XAG' in c][0]

    df = df.rename(columns={date_col: 'date', gold_col: 'gold', silver_col: 'silver'}).dropna()
    df['date'] = pd.to_datetime(df['date']).dt.date
    df['ratio'] = df['gold'] / df['silver']
    return df.sort_values('date')

try:
    with st.spinner('连接国际市场中...'):
        df = get_data()
    
    last = df.iloc[-1]
    
    # 指标栏
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("日期", f"{last['date']}")
    c2.metric("金银比", f"{last['ratio']:.2f}")
    c3.metric("伦敦金", f"${last['gold']:,.2f}")
    c4.metric("伦敦银", f"${last['silver']:.3f}")

    # 图表
    fig = px.line(df, x='date', y='ratio', title='金银比价走势 (Gold/Silver Ratio)')
    fig.update_traces(line_color='#FFD700', line_width=2)
    st.plotly_chart(fig, use_container_width=True)

except Exception as e:
    st.error(f"连接超时，请刷新重试: {e}")
