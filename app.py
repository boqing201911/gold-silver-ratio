
import streamlit as st
import pandas as pd
import plotly.express as px
import yfinance as yf

# ==========================================
# 页面配置
# ==========================================
st.set_page_config(
    page_title="金银比价监测",
    layout="wide",
    page_icon="👑"
)

st.title("👑 宏观对冲监测：伦敦金(XAU) / 伦敦银(XAG)")

# ==========================================
# 数据获取函数 (稳健版：分开抓取)
# ==========================================
@st.cache_data(ttl=60)
def get_gold_silver_data():
    # 1. 单独获取黄金数据
    # 这里的 history 方法比 download 更稳定，不容易出格式问题
    gold = yf.Ticker("XAUUSD=X").history(period="2y")
    gold = gold[['Close']].rename(columns={'Close': 'gold_price'})
    gold.index = pd.to_datetime(gold.index).date # 只保留日期部分
    
    # 2. 单独获取白银数据
    silver = yf.Ticker("XAGUSD=X").history(period="2y")
    silver = silver[['Close']].rename(columns={'Close': 'silver_price'})
    silver.index = pd.to_datetime(silver.index).date
    
    # 3. 合并两张表 (按日期对齐)
    # left_index=True 表示用左边的日期做基准
    df = pd.merge(gold, silver, left_index=True, right_index=True, how='inner')
    
    # 4. 把日期从索引变成一列，方便画图
    df = df.reset_index()
    df = df.rename(columns={'index': 'date'})
    
    # 5. 计算比价
    df['ratio'] = df['gold_price'] / df['silver_price']
    
    return df

# ==========================================
# 执行与展示
# ==========================================
try:
    with st.spinner('正在分别连接黄金和白银市场...'):
        df = get_gold_silver_data()

    # 检查数据是否为空（防止网络完全断开的情况）
    if df.empty:
        st.error("获取到的数据为空，请稍后刷新重试。")
    else:
        latest_record = df.iloc[-1]
        latest_date = latest_record['date']
        latest_ratio = round(latest_record['ratio'], 2)
        latest_gold = round(latest_record['gold_price'], 2)
        latest_silver = round(latest_record['silver_price'], 3)

        # 1. 核心指标卡
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("日期", f"{latest_date}")
        col2.metric("当前金银比", f"{latest_ratio}")
        col3.metric("伦敦金 ($)", f"{latest_gold:,}")
        col4.metric("伦敦银 ($)", f"{latest_silver}")

        # 2. 交互走势图
        st.subheader("金银比价历史走势 (Gold/Silver Ratio)")
        fig = px.line(df, x='date', y='ratio', 
                      title='XAU/XAG Ratio Trend',
                      labels={'date': '日期', 'ratio': '比值'})
        fig.update_traces(line_color='#FFD700', line_width=2) 
        fig.update_layout(hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)

        # 3. 原始数据
        with st.expander("查看原始数据"):
            st.dataframe(df.sort_values(by='date', ascending=False), use_container_width=True)

except Exception as e:
    st.error(f"发生错误: {e}")
    st.info("提示：如果是 Connection Error，通常是 Streamlit 服务器访问 Yahoo 偶尔超时，刷新页面即可。")
