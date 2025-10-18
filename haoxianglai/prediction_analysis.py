import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.font_manager import FontProperties
import warnings
warnings.filterwarnings('ignore')

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

# 读取数据
df = pd.read_excel('haoxianglai.xlsx')
cols = df.columns.tolist()
df['订货日期'] = pd.to_datetime(df[cols[4]])

print("开始深入分析...")

# 1. 按省份和仓库聚合数据，预测各省份各仓库的总订货量
print("1. 数据聚合和特征工程...")

# 计算每个省份-仓库组合的历史表现
province_warehouse_stats = df.groupby([cols[1], cols[2]]).agg({
    cols[3]: ['count', 'sum', 'mean', 'std']
}).round(2)
province_warehouse_stats.columns = ['订货次数', '总订货量', '平均订货量', '标准差']
province_warehouse_stats = province_warehouse_stats.reset_index()

# 计算每个省份的历史表现
province_stats = df.groupby(cols[1]).agg({
    cols[3]: ['count', 'sum', 'mean', 'std']
}).round(2)
province_stats.columns = ['订货次数', '总订货量', '平均订货量', '标准差']
province_stats = province_stats.reset_index()

# 按月份计算趋势
df['月份'] = df['订货日期'].dt.month
monthly_trend = df.groupby([cols[1], '月份'])[cols[3]].sum().reset_index()
monthly_trend.columns = ['省份', '月份', '月订货量']

# 计算每个省份的月度增长率
province_growth = monthly_trend.groupby('省份').apply(
    lambda x: pd.Series({
        '订货量趋势': np.polyfit(x['月份'], x['月订货量'], 1)[0] if len(x) > 1 else 0,
        '平均月订货量': x['月订货量'].mean(),
        '月订货量标准差': x['月订货量'].std()
    })
).round(2).reset_index()

# 2. 特征工程
print("2. 构建预测特征...")

# 为每个省份-仓库组合构建特征
features_list = []

for (province, warehouse), group in df.groupby([cols[1], cols[2]]):
    # 基础统计特征
    features = {
        '省份': province,
        '仓库': warehouse,
        '历史订货次数': len(group),
        '历史总订货量': group[cols[3]].sum(),
        '历史平均订货量': group[cols[3]].mean(),
        '历史订货量标准差': group[cols[3]].std(),
        '最近订货日期': group['订货日期'].max(),
        '首次订货日期': group['订货日期'].min(),
        '活跃天数': (group['订货日期'].max() - group['订货日期'].min()).days
    }

    # 时间特征
    features['订货频率'] = features['历史订货次数'] / max(features['活跃天数'], 1)
    features['距今天数'] = (datetime.now() - features['最近订货日期']).days

    # 从省份级别特征中获取
    province_data = province_growth[province_growth['省份'] == province]
    if not province_data.empty:
        features['省份订货趋势'] = province_data['订货量趋势'].iloc[0]
        features['省份平均月订货量'] = province_data['平均月订货量'].iloc[0]
    else:
        features['省份订货趋势'] = 0
        features['省份平均月订货量'] = province_stats[province_stats[cols[1]] == province]['总订货量'].sum() / 3  # 假设3个月

    features_list.append(features)

features_df = pd.DataFrame(features_list)

# 3. 目标变量构建 - 基于历史模式计算期望的30天订货量
print("3. 构建预测目标...")

# 计算每个组合的历史日均订货量
target_list = []

for idx, row in features_df.iterrows():
    # 基于历史数据的日均订货量
    daily_avg = row['历史总订货量'] / max(row['活跃天数'], 1)

    # 考虑季节性因素（最近30天的表现）
    recent_data = df[
        (df[cols[1]] == row['省份']) &
        (df[cols[2]] == row['仓库']) &
        (df['订货日期'] > (df['订货日期'].max() - timedelta(days=30)))
    ]

    if len(recent_data) > 0:
        recent_daily_avg = recent_data[cols[3]].sum() / 30
        # 结合历史平均和最近表现
        predicted_30_days = (daily_avg * 0.3 + recent_daily_avg * 0.7) * 30
    else:
        # 只使用历史数据
        predicted_30_days = daily_avg * 30

    # 考虑趋势因素
    trend_adjustment = 1 + (row['省份订货趋势'] / row['省份平均月订货量']) * 0.1
    predicted_30_days *= max(trend_adjustment, 0.5)  # 限制调整幅度

    target_list.append(predicted_30_days)

features_df['预测30天订货量'] = target_list

# 4. 机器学习预测模型
print("4. 构建预测模型...")

# 选择用于建模的特征
feature_columns = [
    '历史订货次数', '历史总订货量', '历史平均订货量',
    '历史订货量标准差', '活跃天数', '订货频率', '距今天数',
    '省份订货趋势', '省份平均月订货量'
]

# 处理缺失值
features_df[feature_columns] = features_df[feature_columns].fillna(0)

# 使用历史数据作为训练目标（使用历史总订货量作为代理目标）
X = features_df[feature_columns]
y = features_df['历史总订货量']

# 分割数据
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 训练随机森林模型
rf_model = RandomForestRegressor(n_estimators=100, random_state=42)
rf_model.fit(X_train, y_train)

# 评估模型
y_pred = rf_model.predict(X_test)
mae = mean_absolute_error(y_test, y_pred)
rmse = np.sqrt(mean_squared_error(y_test, y_pred))

print(f"模型评估 - MAE: {mae:.2f}, RMSE: {rmse:.2f}")

# 5. 生成最终预测结果
print("5. 生成未来30天预测...")

# 使用模型预测30天订货量
features_df['模型预测30天订货量'] = rf_model.predict(X)

# 结合统计方法和机器学习的预测结果
features_df['最终预测30天订货量'] = (
    features_df['预测30天订货量'] * 0.6 +
    features_df['模型预测30天订货量'] * 0.4
).round(0)

# 确保预测值不为负数
features_df['最终预测30天订货量'] = features_df['最终预测30天订货量'].clip(lower=0)

# 6. 按省份汇总预测结果
province_predictions = features_df.groupby('省份')['最终预测30天订货量'].agg([
    'sum', 'mean', 'count'
]).round(2)
province_predictions.columns = ['预测总订货量', '预测平均订货量', '仓库数量']
province_predictions = province_predictions.sort_values('预测总订货量', ascending=False)

# 7. 保存预测结果
print("6. 保存预测结果...")

with pd.ExcelWriter('订货预测结果.xlsx', engine='openpyxl') as writer:
    # 各省份各仓库详细预测
    features_df[['省份', '仓库', '历史订货次数', '历史总订货量',
                '最终预测30天订货量']].to_excel(
        writer, sheet_name='各仓库预测详情', index=False
    )

    # 省份汇总预测
    province_predictions.to_excel(writer, sheet_name='省份汇总预测')

    # 预测统计摘要
    summary_stats = pd.DataFrame({
        '统计指标': ['预测仓库总数', '预测总订货量', '预测平均每仓订货量',
                    '预测最大订货量', '预测最小订货量'],
        '数值': [
            len(features_df),
            features_df['最终预测30天订货量'].sum(),
            features_df['最终预测30天订货量'].mean(),
            features_df['最终预测30天订货量'].max(),
            features_df['最终预测30天订货量'].min()
        ]
    }).round(2)
    summary_stats.to_excel(writer, sheet_name='预测统计摘要', index=False)

print("预测分析完成！结果已保存到【订货预测结果.xlsx】")

# 8. 生成预测可视化
print("7. 生成预测可视化图表...")

fig, axes = plt.subplots(2, 2, figsize=(16, 12))

# 前10个省份的预测订货量
top_provinces_pred = province_predictions.head(10)
axes[0,0].barh(range(len(top_provinces_pred)), top_provinces_pred['预测总订货量'],
               color='lightblue')
axes[0,0].set_title('前10个省份未来30天预测订货量')
axes[0,0].set_xlabel('预测订货量（件）')
axes[0,0].set_ylabel('省份')
axes[0,0].set_yticks(range(len(top_provinces_pred)))
axes[0,0].set_yticklabels(top_provinces_pred.index)

# 历史总订货量 vs 预测订货量对比
comparison_df = features_df.sort_values('历史总订货量', ascending=False).head(15)
x_pos = np.arange(len(comparison_df))
width = 0.35

axes[0,1].bar(x_pos - width/2, comparison_df['历史总订货量'], width,
              label='历史总订货量', color='orange', alpha=0.7)
axes[0,1].bar(x_pos + width/2, comparison_df['最终预测30天订货量'], width,
              label='预测30天订货量', color='green', alpha=0.7)
axes[0,1].set_title('历史订货量 vs 预测订货量对比（前15个仓库）')
axes[0,1].set_xlabel('仓库')
axes[0,1].set_ylabel('订货量（件）')
axes[0,1].set_xticks(x_pos)
axes[0,1].set_xticklabels([f"{row['省份'][:2]}-{row['仓库'][:6]}"
                           for _, row in comparison_df.iterrows()],
                          rotation=45, ha='right')
axes[0,1].legend()

# 预测订货量分布
axes[1,0].hist(features_df['最终预测30天订货量'], bins=20,
               color='lightgreen', alpha=0.7, edgecolor='black')
axes[1,0].set_title('预测30天订货量分布')
axes[1,0].set_xlabel('预测订货量（件）')
axes[1,0].set_ylabel('仓库数量')

# 各省份仓库数量与预测订货量的关系
axes[1,1].scatter(province_predictions['仓库数量'], province_predictions['预测总订货量'],
                 alpha=0.6, s=60, color='red')
axes[1,1].set_title('各省份仓库数量 vs 预测总订货量')
axes[1,1].set_xlabel('仓库数量')
axes[1,1].set_ylabel('预测总订货量（件）')

# 添加标签
for i, (province, row) in enumerate(province_predictions.iterrows()):
    if i < 5:  # 只标注前5个省份
        axes[1,1].annotate(province[:2],
                          (row['仓库数量'], row['预测总订货量']),
                          xytext=(5, 5), textcoords='offset points', fontsize=8)

plt.tight_layout()
plt.savefig('预测分析可视化.png', dpi=300, bbox_inches='tight')
plt.close()

print("预测可视化图表已保存为【预测分析可视化.png】")
print("\n分析完成！")