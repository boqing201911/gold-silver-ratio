
import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import json
import re

# ==========================================
# 页面配置
# ==========================================
st.set_page_config(
    page_title="金银比价监测 (Sina源)",
    layout="wide",
    page_icon="🐉"
)

st.title("🐉 宏观对冲监测：伦敦金 / 伦敦银 (新浪直连)")

# ==========================================
# 核心函数：手写新浪接口抓取器
# ==========================================
@st.cache_data(ttl=60)
def get_sina_data(symbol, name_code):
    """
    直接请求新浪财经的期货/外汇K线接口
    symbol: 新浪的代码，例如 'XAU' 或 'XAG'
    """
    # 新浪的日线历史数据接口 (这是个隐藏接口，非常快)
    url = f"https://stock2.finance.sina.com.cn/futures/api/jsonp.php/var%20_/GlobalFuturesService.getGlobalFuturesDailyKLine?symbol={symbol}&_={pd.Timestamp.now().timestamp()}"
    
    try:
        response = requests.get(url, timeout=5)
        # 新浪返回的是类似JS变量的字符串，需要清洗一下
        # 格式如: /* var _ = */ [...]
        content = response.text
        
        # 使用正则提取方括号 [] 里的 JSON 内容
        match = re.search(r'\[.*\]', content)
        if not match:
            return pd.DataFrame()
            
        json_str = match.group(0)
        data = json.loads(json_str)
        
        # 转成 DataFrame
        df = pd.DataFrame(data)
        
        # 新浪返回的列名通常是: date, open, high, low, close, volume
        # 我们只需要 date 和 close
        df = df[['date', 'close']]
        df = df.rename(columns={'close': name_code})
        df['date'] = pd.to_datetime(df['date']).dt.date
        
        # 确保价格是数字类型
        df[name_code] = df[name_code].astype(float)
        
        return df
    except Exception as e:
        st.error(f"获取 {symbol} 失败: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=60)
def get_combined_data():
    # 1. 获取黄金 (新浪代码 XAU)
    gold = get_sina_data('XAU', 'gold_price')
    
    # 2. 获取白银 (新浪代码 XAG)
    silver = get_sina_data('XAG', 'silver_price')
    
    # 3. 合并数据
    if gold.empty or silver.empty:
        return pd.DataFrame()
        
    df = pd.merge(gold, silver, on='date', how='inner')
    
    # 4. 计算比价
    df['ratio'] = df['gold_price'] / df['silver_price']
    
    return df.sort_values('date')

# ==========================================
# 展示层
# ==========================================
try:
    with st.spinner('正如猛龙过江，正在直连新浪财经...'):
        df = get_combined_data()

    if df.empty:
        st.error("数据接口暂时无响应，请稍后刷新。")
    else:
        last = df.iloc[-1]
        
        # 样式优化：使用卡片展示
        st.markdown("### 📊 实时市场快照")
        c1, c2, c3, c4 = st.columns(4)
        
        # 涨跌幅计算 (和昨天比)
        prev = df.iloc[-2]
        ratio_chg = last['ratio'] - prev['ratio']
        gold_chg = last['gold_price'] - prev['gold_price']
        silver_chg = last['silver_price'] - prev['silver_price']

        c1.metric("数据日期", f"{last['date']}")
        c2.metric("金银比 (Ratio)", f"{last['ratio']:.2f}", f"{ratio_chg:.2f}")
        c3.metric("伦敦金 (XAU)", f"${last['gold_price']:,.2f}", f"{gold_chg:.2f}")
        c4.metric("伦敦银 (XAG)", f"${last['silver_price']:.3f}", f"{silver_chg:.3f}")

        # 图表
        st.markdown("---")
        fig = px.line(df, x='date', y='ratio', 
                      title='金银比价历史走势 (Source: Sina Finance)',
                      height=500)
        
        # 金融图表配色
        fig.update_traces(line_color='#d4af37', line_width=2.5) # 香槟金
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis_title="",
            yaxis_title="XAU / XAG",
            hovermode="x unified"
        )
        st.plotly_chart(fig, use_container_width=True)

except Exception as e:
    st.error(f"程序运行出错: {e}")
