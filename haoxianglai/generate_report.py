import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
import seaborn as sns
from datetime import datetime
import os

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

# 读取数据和结果
df = pd.read_excel('haoxianglai.xlsx')
predictions = pd.read_excel('订货预测结果.xlsx', sheet_name='各仓库预测详情')
province_summary = pd.read_excel('订货预测结果.xlsx', sheet_name='省份汇总预测')
cols = df.columns.tolist()

print("生成数据分析报告...")

# 创建报告图表
fig, axes = plt.subplots(3, 2, figsize=(20, 18))

# 1. 订货数量分布分析
axes[0,0].hist(df[cols[3]], bins=15, alpha=0.7, color='skyblue', edgecolor='black')
axes[0,0].set_title('图1: 订货数量分布', fontsize=14, fontweight='bold')
axes[0,0].set_xlabel('订货数量（件）', fontsize=12)
axes[0,0].set_ylabel('频次', fontsize=12)
axes[0,0].grid(True, alpha=0.3)

# 2. 各省份订货频次分布（前10个）
province_freq = df[cols[1]].value_counts().head(10)
axes[0,1].barh(range(len(province_freq)), province_freq.values, color='lightcoral')
axes[0,1].set_title('图2: 前10个省份订货频次', fontsize=14, fontweight='bold')
axes[0,1].set_xlabel('订货频次', fontsize=12)
axes[0,1].set_ylabel('省份', fontsize=12)
axes[0,1].set_yticks(range(len(province_freq)))
axes[0,1].set_yticklabels(province_freq.index)
axes[0,1].grid(True, alpha=0.3)

# 3. 时间序列趋势分析
df['订货日期'] = pd.to_datetime(df[cols[4]])
daily_trend = df.groupby(df['订货日期'].dt.date)[cols[3]].sum()
axes[1,0].plot(daily_trend.index, daily_trend.values, marker='o', linestyle='-', color='green', linewidth=2)
axes[1,0].set_title('图3: 每日总订货量时间序列', fontsize=14, fontweight='bold')
axes[1,0].set_xlabel('日期', fontsize=12)
axes[1,0].set_ylabel('总订货量（件）', fontsize=12)
axes[1,0].tick_params(axis='x', rotation=45)
axes[1,0].grid(True, alpha=0.3)

# 4. 前10个仓库的总订货量
top_warehouses = df.groupby(cols[2])[cols[3]].sum().sort_values(ascending=False).head(10)
axes[1,1].barh(range(len(top_warehouses)), top_warehouses.values, color='gold')
axes[1,1].set_title('图4: 前10个仓库历史总订货量', fontsize=14, fontweight='bold')
axes[1,1].set_xlabel('总订货量（件）', fontsize=12)
axes[1,1].set_ylabel('仓库', fontsize=12)
axes[1,1].set_yticks(range(len(top_warehouses)))
axes[1,1].set_yticklabels([warehouse[:15] for warehouse in top_warehouses.index])
axes[1,1].grid(True, alpha=0.3)

# 5. 预测结果：前10个省份
top_provinces_pred = province_summary.head(10)
axes[2,0].barh(range(len(top_provinces_pred)), top_provinces_pred['预测总订货量'],
               color='lightblue', alpha=0.8)
axes[2,0].set_title('图5: 前10个省份未来30天预测订货量', fontsize=14, fontweight='bold')
axes[2,0].set_xlabel('预测订货量（件）', fontsize=12)
axes[2,0].set_ylabel('省份', fontsize=12)
axes[2,0].set_yticks(range(len(top_provinces_pred)))
axes[2,0].set_yticklabels(top_provinces_pred.index)
axes[2,0].grid(True, alpha=0.3)

# 6. 历史vs预测对比（前15个仓库）
comparison = pd.merge(
    df.groupby(cols[2])[cols[3]].sum().sort_values(ascending=False).head(15).reset_index(),
    predictions[['仓库', '最终预测30天订货量']],
    left_on=cols[2], right_on='仓库', how='left'
).fillna(0)

x_pos = np.arange(len(comparison))
width = 0.35

bars1 = axes[2,1].bar(x_pos - width/2, comparison[cols[3]], width,
                      label='历史总订货量', color='orange', alpha=0.7)
bars2 = axes[2,1].bar(x_pos + width/2, comparison['最终预测30天订货量'], width,
                      label='预测30天订货量', color='green', alpha=0.7)

axes[2,1].set_title('图6: 历史订货量 vs 预测订货量对比', fontsize=14, fontweight='bold')
axes[2,1].set_xlabel('仓库', fontsize=12)
axes[2,1].set_ylabel('订货量（件）', fontsize=12)
axes[2,1].set_xticks(x_pos)
axes[2,1].set_xticklabels([warehouse[:8] for warehouse in comparison[cols[2]]],
                          rotation=45, ha='right')
axes[2,1].legend()
axes[2,1].grid(True, alpha=0.3)

# 添加数值标签
for i, (bar1, bar2) in enumerate(zip(bars1, bars2)):
    height1 = bar1.get_height()
    height2 = bar2.get_height()
    axes[2,1].annotate(f'{height1:.0f}',
                      xy=(bar1.get_x() + bar1.get_width() / 2, height1),
                      xytext=(0, 3), textcoords="offset points",
                      ha='center', va='bottom', fontsize=8)
    axes[2,1].annotate(f'{height2:.0f}',
                      xy=(bar2.get_x() + bar2.get_width() / 2, height2),
                      xytext=(0, 3), textcoords="offset points",
                      ha='center', va='bottom', fontsize=8)

plt.tight_layout()
plt.savefig('数据分析报告图表.png', dpi=300, bbox_inches='tight')
plt.close()

# 生成统计表格
print("生成关键统计信息...")

# 关键统计指标
stats_summary = {
    '指标': [
        '数据记录总数', '数据时间跨度', '经营组织数量', '省份数量', '仓库数量',
        '平均订货量', '订货量中位数', '最大单次订货量', '最小单次订货量',
        '预测仓库总数', '预测30天总订货量', '预测平均每仓订货量'
    ],
    '数值': [
        len(df),
        f"{(df['订货日期'].max() - df['订货日期'].min()).days}天",
        df[cols[0]].nunique(),
        df[cols[1]].nunique(),
        df[cols[2]].nunique(),
        f"{df[cols[3]].mean():.2f}件",
        f"{df[cols[3]].median():.2f}件",
        f"{df[cols[3]].max()}件",
        f"{df[cols[3]].min()}件",
        len(predictions),
        f"{predictions['最终预测30天订货量'].sum():.0f}件",
        f"{predictions['最终预测30天订货量'].mean():.0f}件"
    ]
}

stats_df = pd.DataFrame(stats_summary)
stats_df.to_excel('关键统计指标.xlsx', index=False)

print("数据分析报告图表和统计信息已生成")
print("图表文件：数据分析报告图表.png")
print("统计文件：关键统计指标.xlsx")