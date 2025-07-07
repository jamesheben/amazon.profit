import pandas as pd
def generate_profit_report(order_file, ad_file,ad_sum_file):
    order_df=pd.read_csv(order_file,header=7)#表头是第7行
    #order_df
    ad_df=pd.read_csv(ad_file,index_col=0)#设置第0列为索引
    ad_df.index = ad_df.index.str.split('-', n=1).str.get(1)# 使用字符串分割方法处理 索引列"-"后一列
    ad_df = ad_df[ad_df.iloc[:,9] > 0]# 排除 Spend(USD) 列中小于等于 0 的行
    #ad_df
    ad_sum_df=pd.read_csv(ad_sum_file,index_col=0)
    ad_bd=ad_sum_df.iloc[:,15].sum()-ad_df.iloc[:,9].sum()   #相减得到品牌广告费
    ad_bd=round(ad_bd,2)
    #ad_sum_df
    profit_df=pd.read_csv("./利润报表.csv",index_col=0)#设置第0列为索引
    #profit_df
    cost_df=pd.read_csv("./成本报表.csv",index_col=0)#设置第0列为索引
    #cost_df

    #order_df1 = order_df[~order_df['type'].isin(['Liquidations', 'Liquidations Adjustments'])]
    order_df1 = order_df[order_df['type'].isin(['Order', 'Refund'])]
    unique_skus = order_df1['sku'].unique()
    unique_skus = [sku for sku in unique_skus if not pd.isna(sku)]# 过滤掉空值（NaN）
    unique_skus = [str(sku) for sku in unique_skus]
    unique_skus = sorted(unique_skus)
    #unique_skus

    # 自定义 profit_df 的列数
    new_column_count = len(unique_skus)
    # 如果 profit_df 列数不足，添加空列
    while len(profit_df.columns) < new_column_count:
        profit_df[f'new_col_{len(profit_df.columns)}'] = None
    # 如果 profit_df 列数过多，删除多余列
    if len(profit_df.columns) > new_column_count:
        profit_df = profit_df.iloc[:, :new_column_count]
    profit_df.columns = unique_skus
    #profit_df

    for SKU in unique_skus:
        filtered_order = order_df[(order_df['sku'] == SKU) & (order_df['type'] == 'Order')]
        quantity_sum = filtered_order['quantity'].sum()
        quantity_sum = int(quantity_sum)
        profit_df.loc['销量', SKU] = quantity_sum

        product_sales_sum = filtered_order['product sales'].sum()
        profit_df.at['总结算额', SKU] = round(product_sales_sum, 2)

        platform_cost_sum = filtered_order[['selling fees', 'fba fees']].sum().sum()
        profit_df.at['平台成本', SKU] = round(platform_cost_sum, 2)

        coupon_sum = filtered_order.iloc[:, 15:25].sum().sum()
        profit_df.at['折扣和税', SKU] = round(coupon_sum, 2)

        filtered_refund = order_df[(order_df['sku'] == SKU) & (order_df['type'] == "Refund")]
        refund_total_sum = filtered_refund['total'].sum()
        profit_df.at['退款', SKU] = round(refund_total_sum, 2)

        if not pd.isna(product_sales_sum) and product_sales_sum != 0:
            platform_cost_ratio = (platform_cost_sum / product_sales_sum) * 100
            platform_cost_ratio = round(platform_cost_ratio, 2)
            profit_df.at['平台成本占比%', SKU] = platform_cost_ratio

            refund_ratio = (refund_total_sum / product_sales_sum) * 100
            refund_ratio = round(refund_ratio, 2)
            profit_df.at['退款占比%', SKU] = refund_ratio
        else:
            profit_df.at['平台成本占比%', SKU] = pd.NA
            profit_df.at['退款占比%', SKU] = pd.NA
    #profit_df

    # 遍历插入广告费
    unique_ad_skus = ad_df.index.unique()
    for ad_sku in unique_ad_skus:
        filtered_ad_df = ad_df.loc[ad_sku]  # 筛选索引为 "ad_sku" 的行
        ad_spend = filtered_ad_df.iloc[9].sum() # 对 "Spend(USD)" 列求和,只有一行，不能用[:,9],series不是Dataframe
        # 检查 ad_sku 是否存在于 profit_df 的列中
        if ad_sku not in profit_df.columns:
            # 如果不存在，新增一列并初始化为 0.00
            profit_df[ad_sku] = 0.00
        # 将广告求和结果赋值给 profit_df 中索引为 "广告费"，列名为 ad_sku 的位置
        profit_df.at['广告费', ad_sku] = -abs(ad_spend) # 将广告求和结果赋值给 profit_df 中索引为 "广告费"，列名为 "ad_sku" 的位置

    # 计算其他费用
    filtered_adjust_liquid = order_df[order_df['type'].isin(["Adjustment", "Liquidations", "Liquidations Adjustments"])]
    adjust_liquid_sum=filtered_adjust_liquid["total"].sum()
    profit_df.at['Liquidations和Adjustments', "汇总"]=round(adjust_liquid_sum,2)
    fba_inventory_fee_df=order_df[order_df['type']=="FBA Inventory Fee"]
    profit_df.at['FBA Inventory Fee仓储费', "汇总"]=fba_inventory_fee_df["total"].sum()
    fba_transaction_fees_df=order_df[order_df['type']=="FBA Transaction fees"]
    profit_df.at['FBA Transaction fees退货处理费，AWD转运费', "汇总"]=fba_transaction_fees_df["total"].sum()
    service_fee_df=order_df[(order_df['type']=="Service Fee") & (order_df['description']!="Cost of Advertising")]
    profit_df.at['Service Fee（广告除外）如入库配置费', "汇总"]=service_fee_df["total"].sum()

    except_df=order_df['type'].isin(["Adjustment","Liquidations","Liquidations Adjustments",
                                 "FBA Inventory Fee","FBA Transaction fees","Service Fee","Order","Refund","Transfer"])
    profit_df.at['其他', "汇总"]=order_df[~except_df]["total"].sum()
    #profit_df

    # 处理广告费和其他指标
    ad_sum = profit_df.loc['广告费'].sum()
    unique_profit_sku = profit_df.columns[:-1]
    for profit_sku in unique_profit_sku: 
        product_cost = cost_df[profit_sku].sum()/7.2*profit_df.at['销量', profit_sku]      #插入产品成本
        product_cost = round(product_cost, 2)
        profit_df.at['产品成本', profit_sku] = -abs(product_cost)
        
        if pd.isna(profit_df.at['广告费', profit_sku]):
            profit_df.at['广告费', profit_sku] = 0         # 遍历广告费空则为0
        if not pd.isna(profit_df.at['总结算额', profit_sku]):  # 不是空值才计算，空值不计算跳过
            profit_df.at['广告费', profit_sku] = profit_df.at['广告费', profit_sku] - (
                        profit_df.at['广告费', profit_sku] / ad_sum) * ad_bd
            profit_df.at['广告费', profit_sku] = round(profit_df.at['广告费', profit_sku], 2)

            # 检查总结算额是否为零
            summary_settlement = profit_df.at['总结算额', profit_sku]
            if summary_settlement != 0:

                ad_ratio = ((profit_df.at['广告费', profit_sku])/ (profit_df.at['总结算额', profit_sku])) * 100
                ad_ratio = round(ad_ratio, 2)
                profit_df.at['广告占比%', profit_sku] = ad_ratio

                product_ratio = ((profit_df.at['产品成本', profit_sku])/ (profit_df.at['总结算额', profit_sku])) * 100
                product_ratio = round(product_ratio, 2)
                profit_df.at['产品成本占比%', profit_sku] = product_ratio
            else:
                # 如果总结算额为零，将广告占比设为 0
                profit_df.at['广告占比%', profit_sku] = 0

            # 获取各项占比的值，并处理 NaN
            platform_cost_ratio = profit_df.at['平台成本占比%', profit_sku]
            refund_ratio = profit_df.at['退款占比%', profit_sku]
            ad_ratio = profit_df.at['广告占比%', profit_sku]
            product_ratio = profit_df.at['产品成本占比%', profit_sku]
           
            
            platform_cost_ratio = 0 if pd.isna(platform_cost_ratio) else platform_cost_ratio
            refund_ratio = 0 if pd.isna(refund_ratio) else refund_ratio
            ad_ratio = 0 if pd.isna(ad_ratio) else ad_ratio
            product_ratio = 0 if pd.isna(product_ratio) else product_ratio
            
            profit_df.at['剩下%', profit_sku]=100+ platform_cost_ratio + refund_ratio + ad_ratio + product_ratio
            profit_df.at['剩下%', profit_sku] = round(profit_df.at['剩下%', profit_sku], 2)

            profit_df.at['利润', profit_sku] = profit_df.at['总结算额', profit_sku] + profit_df.at['平台成本', profit_sku] + \
                                               profit_df.at['退款', profit_sku] + profit_df.at['广告费', profit_sku] + \
                                               profit_df.at['产品成本', profit_sku]
            profit_df.at['利润', profit_sku] = round(profit_df.at['利润', profit_sku], 2)
            profit_df.at['最终利润', profit_sku] = profit_df.at['利润', profit_sku] + profit_df.at['折扣和税', profit_sku]
            profit_df.at['最终利润', profit_sku] = round(profit_df.at['最终利润', profit_sku], 2)
    if abs(ad_sum_df.iloc[:, 15].sum() + profit_df.loc['广告费'].sum()) > 1:
        profit_df.loc["请注意"] = "产品广告第二页没下载完整，请选择单页50条重新下载"

    filtered_order = order_df[order_df['type'].isin(["Order"])]

    quantity_sum = filtered_order['quantity'].sum()
    profit_df.loc['销量', "汇总"] = int(quantity_sum)
    
    product_sales_sum = filtered_order['product sales'].sum()
    profit_df.at['总结算额', "汇总"] = round(product_sales_sum,2)
    
    platform_cost_sum = filtered_order[['selling fees', 'fba fees']].sum().sum()
    profit_df.at['平台成本', "汇总"] = round(platform_cost_sum,2)
    
    filtered_refund = order_df[order_df['type'].isin(["Refund"])]
    refund_total_sum = filtered_refund['total'].sum()
    profit_df.at['退款', "汇总"] = round(refund_total_sum,2)
    
    profit_df.at["广告费","汇总"]=-ad_sum_df.iloc[:,15].sum().round(2)

    
    lens=len(profit_df.columns)-1
    profit_df.at["产品成本","汇总"]=profit_df.loc["产品成本"].iloc[0:lens].sum()
    # profit_df.at["利润","汇总"]=profit_df.loc["利润"].iloc[0:lens].sum()
    profit_df.at["折扣和税","汇总"]=round(profit_df.loc["折扣和税"].iloc[0:lens].sum(),2)
    # profit_df.at["最终利润","汇总"]=profit_df.loc["最终利润"].iloc[0:lens].sum()
    profit_df.at["平台成本占比%","汇总"]=round((profit_df.at["平台成本","汇总"]/profit_df.at["总结算额","汇总"])*100,2)
    profit_df.at["退款占比%","汇总"]=round((profit_df.at["退款","汇总"]/profit_df.at["总结算额","汇总"])*100,2)
    profit_df.at["广告占比%","汇总"]=round((profit_df.at["广告费","汇总"]/profit_df.at["总结算额","汇总"])*100,2)
    profit_df.at["产品成本占比%", "汇总"] = round((profit_df.at["产品成本", "汇总"] / profit_df.at["总结算额", "汇总"]) * 100,2)
    profit_df.at["剩下%", "汇总"] = 100 + profit_df.at["平台成本占比%", "汇总"] + profit_df.at["退款占比%", "汇总"] + \
                                    profit_df.at["广告占比%", "汇总"] + profit_df.at["产品成本占比%", "汇总"]
    profit_df.at["利润","汇总"]=round(profit_df.at["剩下%", "汇总"]/100*profit_df.at['总结算额', "汇总"])
    profit_df.at["最终利润","汇总"]=profit_df.at["利润","汇总"]+profit_df.at["折扣和税","汇总"]
    
    profit_df.at["盈利","汇总"] =profit_df["汇总"].iloc[13] + profit_df["汇总"].iloc[15:20].sum()
    profit_df.at["盈利","汇总"] = round(profit_df.at["盈利","汇总"],2)
    #profit_df
    
    lens = len(profit_df.columns)
    start_row = profit_df.index.tolist().index('总结算额')
    end_row = profit_df.index.tolist().index('其他') + 1
    # 使用 loc 进行赋值，避免链式索引
    profit_df.loc[profit_df.index[start_row:end_row], profit_df.columns[:lens]] = profit_df.loc[
        profit_df.index[start_row:end_row], profit_df.columns[:lens]].round(2)

    profit_df=profit_df.astype(object)          #格式化表格内容为object
    rows = ["平台成本占比%", "退款占比%", "广告占比%","产品成本占比%","剩下%"]
    for row in rows:
        for sku in profit_df.columns:
            if pd.notna(profit_df.at[row, sku]):
            # 将数值转换为字符串并添加 % 符号
                profit_df.at[row, sku] = f"{profit_df.at[row, sku]}%"
            else:
            # 处理缺失值
                profit_df.at[row, sku] = pd.NA

    return profit_df
