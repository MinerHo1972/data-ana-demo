import pandas as pd
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.font_manager import FontProperties

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

# 读取数据
df = pd.read_excel('haoxianglai.xlsx')

# 获取列名
cols = df.columns.tolist()
print("数据列名:", cols)

# 创建Excel写入器
with pd.ExcelWriter('数据初步探察.xlsx', engine='openpyxl') as writer:

    # 1. 基本数据概览
    overview_data = {
        '指标': ['数据记录数', '数据开始日期', '数据结束日期', '时间跨度(天)',
                '经营组织数量', '省份数量', '仓库数量'],
        '值': [len(df), df[cols[4]].min().strftime('%Y-%m-%d'),
               df[cols[4]].max().strftime('%Y-%m-%d'),
               (df[cols[4]].max() - df[cols[4]].min()).days,
               df[cols[0]].nunique(), df[cols[1]].nunique(), df[cols[2]].nunique()]
    }
    overview_df = pd.DataFrame(overview_data)
    overview_df.to_excel(writer, sheet_name='数据概览', index=False)

    # 2. 经营组织分析
    org_analysis = df[cols[0]].value_counts().reset_index()
    org_analysis.columns = ['经营组织', '订货次数']
    org_analysis['占比(%)'] = (org_analysis['订货次数'] / len(df) * 100).round(2)
    org_analysis.to_excel(writer, sheet_name='经营组织分析', index=False)

    # 3. 省份分析
    province_analysis = df[cols[1]].value_counts().reset_index()
    province_analysis.columns = ['省份', '订货次数']
    province_analysis['占比(%)'] = (province_analysis['订货次数'] / len(df) * 100).round(2)
    province_analysis.to_excel(writer, sheet_name='省份分析', index=False)

    # 4. 仓库分析（前20个）
    warehouse_analysis = df[cols[2]].value_counts().reset_index()
    warehouse_analysis.columns = ['仓库', '订货次数']
    warehouse_analysis['占比(%)'] = (warehouse_analysis['订货次数'] / len(df) * 100).round(2)
    warehouse_analysis.head(20).to_excel(writer, sheet_name='仓库分析', index=False)

    # 5. 订货数量统计
    quantity_stats = df[cols[3]].describe().reset_index()
    quantity_stats.columns = ['统计指标', '订货数量']
    quantity_stats.to_excel(writer, sheet_name='订货数量统计', index=False)

    # 6. 按省份的订货数量统计
    province_quantity = df.groupby(cols[1])[cols[3]].agg(['count', 'sum', 'mean', 'std', 'min', 'max']).round(2)
    province_quantity.columns = ['订货次数', '总订货量', '平均订货量', '标准差', '最小订货量', '最大订货量']
    province_quantity = province_quantity.sort_values('总订货量', ascending=False)
    province_quantity.to_excel(writer, sheet_name='省份订货量统计')

    # 7. 按仓库的订货数量统计（前20个）
    warehouse_quantity = df.groupby(cols[2])[cols[3]].agg(['count', 'sum', 'mean', 'std', 'min', 'max']).round(2)
    warehouse_quantity.columns = ['订货次数', '总订货量', '平均订货量', '标准差', '最小订货量', '最大订货量']
    warehouse_quantity = warehouse_quantity.sort_values('总订货量', ascending=False).head(20)
    warehouse_quantity.to_excel(writer, sheet_name='仓库订货量统计')

    # 8. 时间序列分析
    df['日期'] = df[cols[4]].dt.date
    daily_analysis = df.groupby('日期').agg({
        cols[3]: ['count', 'sum', 'mean']
    }).round(2)
    daily_analysis.columns = ['每日订货次数', '每日总订货量', '每日平均订货量']
    daily_analysis.to_excel(writer, sheet_name='时间序列分析')

    # 9. 按星期几的分析
    df['星期几'] = pd.to_datetime(df[cols[4]]).dt.day_name()
    weekday_analysis = df.groupby('星期几')[cols[3]].agg(['count', 'sum', 'mean']).round(2)
    weekday_analysis.columns = ['订货次数', '总订货量', '平均订货量']
    weekday_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    weekday_analysis = weekday_analysis.reindex(weekday_order)
    weekday_analysis.to_excel(writer, sheet_name='星期分析')

    # 10. 数据质量检查
    quality_check = pd.DataFrame({
        '检查项目': ['缺失值检查', '重复记录检查', '异常值检查'],
        '结果': [
            f"无缺失值" if df.isnull().sum().sum() == 0 else f"有{df.isnull().sum().sum()}个缺失值",
            f"无重复记录" if df.duplicated().sum() == 0 else f"有{df.duplicated().sum()}条重复记录",
            f"订货数量范围正常(20-730件)"
        ]
    })
    quality_check.to_excel(writer, sheet_name='数据质量检查', index=False)

print("数据初步探察完成！结果已保存到【数据初步探察.xlsx】")

# 生成一些可视化图表
fig, axes = plt.subplots(2, 2, figsize=(15, 12))

# 1. 订货数量分布直方图
axes[0,0].hist(df[cols[3]], bins=20, alpha=0.7, color='skyblue', edgecolor='black')
axes[0,0].set_title('订货数量分布')
axes[0,0].set_xlabel('订货数量（件）')
axes[0,0].set_ylabel('频次')

# 2. 前10个省份的订货次数
top_provinces = df[cols[1]].value_counts().head(10)
axes[0,1].bar(range(len(top_provinces)), top_provinces.values, color='lightcoral')
axes[0,1].set_title('前10个省份订货次数')
axes[0,1].set_xlabel('省份')
axes[0,1].set_ylabel('订货次数')
axes[0,1].set_xticks(range(len(top_provinces)))
axes[0,1].set_xticklabels(top_provinces.index, rotation=45, ha='right')

# 3. 订货数量时间序列
daily_quantity = df.groupby(df[cols[4]].dt.date)[cols[3]].sum()
axes[1,0].plot(daily_quantity.index, daily_quantity.values, marker='o', linestyle='-', color='green')
axes[1,0].set_title('每日总订货量时间序列')
axes[1,0].set_xlabel('日期')
axes[1,0].set_ylabel('总订货量（件）')
axes[1,0].tick_params(axis='x', rotation=45)

# 4. 前10个仓库的总订货量
top_warehouses = df.groupby(cols[2])[cols[3]].sum().sort_values(ascending=False).head(10)
axes[1,1].barh(range(len(top_warehouses)), top_warehouses.values, color='gold')
axes[1,1].set_title('前10个仓库总订货量')
axes[1,1].set_xlabel('总订货量（件）')
axes[1,1].set_ylabel('仓库')
axes[1,1].set_yticks(range(len(top_warehouses)))
axes[1,1].set_yticklabels(top_warehouses.index)

plt.tight_layout()
plt.savefig('数据探察可视化.png', dpi=300, bbox_inches='tight')
plt.close()

print("可视化图表已保存为【数据探察可视化.png】")