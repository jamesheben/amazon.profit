import streamlit as st
from utils import generate_profit_report
st.title("利润报表生成器")
# 上传文件
order_file = st.file_uploader("上传订单报表 (CSV 文件)", type=["csv"])
ad_file = st.file_uploader("上传广告报表 (CSV 文件)", type=["csv"])
ad_sum_file = st.file_uploader("上传广告总报表 (CSV 文件)", type=["csv"])
if order_file and ad_file and ad_sum_file:
    if st.button("生成利润报表"):
        try:
            # 调用生成利润报表的函数，传入临时文件路径
            profit_df = generate_profit_report(order_file, ad_file, ad_sum_file)

            # 显示利润报表
            st.write("利润报表:")
            st.dataframe(profit_df)
            # 提供下载链接
            # csv = profit_df.to_csv(sep="\t", na_rep="nan",encoding='utf-8')
            # st.download_button(
            #     label="下载利润报表 (CSV 文件)",
            #     data=csv,
            #     file_name="profit_report.csv",
            #     mime="text/csv"
            # )
        except Exception as e:
            st.error(f"生成报表时出现错误: {e}")