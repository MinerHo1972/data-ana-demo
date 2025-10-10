import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor, ExtraTreesRegressor
from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.svm import SVR
from sklearn.tree import DecisionTreeRegressor
from sklearn.neighbors import KNeighborsRegressor
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

print("开始多种预测模型对比分析...")

# 读取数据
df = pd.read_excel('haoxianglai.xlsx')
cols = df.columns.tolist()
df['订货日期'] = pd.to_datetime(df[cols[4]])

print(f"数据加载完成：{len(df)}条记录")

# 1. 数据预处理和特征工程
print("\n1. 数据预处理和特征工程...")

# 基础聚合统计
province_warehouse_stats = df.groupby([cols[1], cols[2]]).agg({
    cols[3]: ['count', 'sum', 'mean', 'std', 'min', 'max']
}).round(2)
province_warehouse_stats.columns = ['订货次数', '总订货量', '平均订货量', '标准差', '最小订货量', '最大订货量']
province_warehouse_stats = province_warehouse_stats.reset_index()

# 时间特征
df['月份'] = df['订货日期'].dt.month
df['星期几'] = df['订货日期'].dt.dayofweek
df['一年中的第几周'] = df['订货日期'].dt.isocalendar().week

# 计算时间趋势
monthly_trend = df.groupby([cols[1], '月份'])[cols[3]].sum().reset_index()
monthly_trend.columns = ['省份', '月份', '月订货量']

# 省份级别趋势特征
province_features = monthly_trend.groupby('省份').apply(
    lambda x: pd.Series({
        '月度趋势': np.polyfit(x['月份'], x['月订货量'], 1)[0] if len(x) > 1 else 0,
        '平均月订货量': x['月订货量'].mean(),
        '月订货量波动': x['月订货量'].std(),
        '最大月订货量': x['月订货量'].max(),
        '活跃月份数': len(x)
    })
).round(2).reset_index()

# 2. 构建特征矩阵
print("2. 构建特征矩阵...")

features_list = []

for (province, warehouse), group in df.groupby([cols[1], cols[2]]):
    # 基础统计特征
    features = {
        '省份': province,
        '仓库': warehouse,
        '历史订货次数': len(group),
        '历史总订货量': group[cols[3]].sum(),
        '历史平均订货量': group[cols[3]].mean(),
        '历史订货量标准差': group[cols[3]].std() if len(group) > 1 else 0,
        '历史最小订货量': group[cols[3]].min(),
        '历史最大订货量': group[cols[3]].max(),
        '最近订货日期': group['订货日期'].max(),
        '首次订货日期': group['订货日期'].min(),
        '活跃天数': (group['订货日期'].max() - group['订货日期'].min()).days + 1,
        '订货频率': len(group) / max((group['订货日期'].max() - group['订货日期'].min()).days + 1, 1)
    }

    # 时间特征
    features['距今天数'] = (datetime.now() - features['最近订货日期']).days
    features['活跃度'] = features['活跃天数'] / 88  # 相对于总时间跨度的活跃度

    # 订货间隔特征
    if len(group) > 1:
        date_diffs = sorted(group['订货日期'].unique())
        intervals = [(date_diffs[i+1] - date_diffs[i]).days for i in range(len(date_diffs)-1)]
        features['平均订货间隔'] = np.mean(intervals)
        features['订货间隔标准差'] = np.std(intervals)
    else:
        features['平均订货间隔'] = 88
        features['订货间隔标准差'] = 0

    # 省份级别特征
    prov_data = province_features[province_features['省份'] == province]
    if not prov_data.empty:
        features.update({
            '省份月度趋势': prov_data['月度趋势'].iloc[0],
            '省份平均月订货量': prov_data['平均月订货量'].iloc[0],
            '省份月订货量波动': prov_data['月订货量波动'].iloc[0],
            '省份最大月订货量': prov_data['最大月订货量'].iloc[0],
            '省份活跃月份数': prov_data['活跃月份数'].iloc[0]
        })
    else:
        features.update({
            '省份月度趋势': 0,
            '省份平均月订货量': features['历史总订货量'] / 3,
            '省份月订货量波动': 0,
            '省份最大月订货量': features['历史总订货量'],
            '省份活跃月份数': 1
        })

    # 最近30天表现
    recent_cutoff = df['订货日期'].max() - timedelta(days=30)
    recent_data = group[group['订货日期'] > recent_cutoff]

    if len(recent_data) > 0:
        features['最近30天订货次数'] = len(recent_data)
        features['最近30天订货量'] = recent_data[cols[3]].sum()
        features['最近30天平均订货量'] = recent_data[cols[3]].mean()
        features['最近30天订货频率'] = len(recent_data) / 30
    else:
        features['最近30天订货次数'] = 0
        features['最近30天订货量'] = 0
        features['最近30天平均订货量'] = 0
        features['最近30天订货频率'] = 0

    features_list.append(features)

features_df = pd.DataFrame(features_list)

# 3. 目标变量构建
print("3. 构建目标变量...")

# 计算日均订货量
features_df['日均订货量'] = features_df['历史总订货量'] / features_df['活跃天数']
features_df['30天基准预测'] = features_df['日均订货量'] * 30

# 考虑最近的趋势
features_df['趋势调整因子'] = np.where(
    features_df['最近30天订货量'] > 0,
    (features_df['最近30天订货量'] / 30) / features_df['日均订货量'],
    1.0
)

# 考虑省份趋势
features_df['省份趋势调整'] = 1 + (features_df['省份月度趋势'] /
                                   np.maximum(features_df['省份平均月订货量'], 1)) * 0.1

# 综合目标值
features_df['目标30天订货量'] = (features_df['30天基准预测'] *
                                 features_df['趋势调整因子'] *
                                 features_df['省份趋势调整']).clip(lower=0)

# 4. 特征选择和预处理
print("4. 特征选择和预处理...")

# 选择特征列
feature_columns = [
    '历史订货次数', '历史总订货量', '历史平均订货量', '历史订货量标准差',
    '历史最小订货量', '历史最大订货量', '活跃天数', '订货频率',
    '距今天数', '活跃度', '平均订货间隔', '订货间隔标准差',
    '省份月度趋势', '省份平均月订货量', '省份月订货量波动',
    '省份最大月订货量', '省份活跃月份数', '最近30天订货次数',
    '最近30天订货量', '最近30天平均订货量', '最近30天订货频率',
    '日均订货量', '趋势调整因子', '省份趋势调整'
]

# 处理缺失值
for col in feature_columns:
    features_df[col] = features_df[col].fillna(features_df[col].median())

X = features_df[feature_columns]
y = features_df['目标30天订货量']

# 标准化特征
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# 5. 定义预测模型
print("5. 定义和训练多种预测模型...")

models = {
    '线性回归': LinearRegression(),
    '岭回归': Ridge(alpha=1.0),
    'Lasso回归': Lasso(alpha=1.0),
    '随机森林': RandomForestRegressor(n_estimators=100, random_state=42),
    '梯度提升': GradientBoostingRegressor(n_estimators=100, random_state=42),
    '极端随机树': ExtraTreesRegressor(n_estimators=100, random_state=42),
    '决策树': DecisionTreeRegressor(random_state=42),
    'K近邻': KNeighborsRegressor(n_neighbors=5),
    '支持向量回归': SVR(kernel='rbf', C=1.0, gamma='scale')
}

# 分割数据
X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)

# 训练和评估模型
model_results = {}
predictions = {}

print("\n模型训练和评估结果：")
print("-" * 60)

for name, model in models.items():
    try:
        # 训练模型
        model.fit(X_train, y_train)

        # 预测
        y_pred = model.predict(X_test)

        # 评估指标
        mae = mean_absolute_error(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        r2 = r2_score(y_test, y_pred)

        # 交叉验证
        cv_scores = cross_val_score(model, X_scaled, y, cv=5, scoring='neg_mean_absolute_error')
        cv_mae = -cv_scores.mean()

        model_results[name] = {
            'MAE': mae,
            'RMSE': rmse,
            'R2': r2,
            'CV_MAE': cv_mae
        }

        # 对全部数据进行预测
        full_predictions = model.predict(X_scaled)
        predictions[name] = full_predictions

        print(f"{name:12} | MAE: {mae:8.2f} | RMSE: {rmse:8.2f} | R2: {r2:6.3f} | CV_MAE: {cv_mae:8.2f}")

    except Exception as e:
        print(f"{name:12} | 训练失败: {str(e)}")

# 6. 集成预测
print("\n6. 集成预测...")

# 选择表现最好的几个模型进行集成
top_models = sorted(model_results.items(), key=lambda x: x[1]['MAE'])[:5]
print(f"选择表现最好的{len(top_models)}个模型进行集成:")
for name, metrics in top_models:
    print(f"  - {name}: MAE = {metrics['MAE']:.2f}")

# 加权平均集成（根据MAE倒数进行加权）
weights = []
model_names = []
for name, metrics in top_models:
    weight = 1.0 / metrics['MAE']
    weights.append(weight)
    model_names.append(name)

weights = np.array(weights) / np.sum(weights)

print(f"\n模型权重:")
for name, weight in zip(model_names, weights):
    print(f"  - {name}: {weight:.3f}")

# 集成预测
ensemble_predictions = np.zeros(len(X_scaled))
for name, weight in zip(model_names, weights):
    ensemble_predictions += weight * predictions[name]

# 添加到特征数据框
features_df['集成预测30天订货量'] = np.maximum(ensemble_predictions, 0)

# 7. 预测结果分析和保存
print("\n7. 预测结果分析和保存...")

# 计算各种预测的统计信息
prediction_stats = []
for name in model_names + ['集成']:
    if name == '集成':
        pred_col = '集成预测30天订货量'
    else:
        pred_col = f'{name}预测30天订货量'
        features_df[pred_col] = np.maximum(predictions[name], 0)

    stats = {
        '模型': name,
        '预测总订货量': features_df[pred_col].sum(),
        '预测平均订货量': features_df[pred_col].mean(),
        '预测最大订货量': features_df[pred_col].max(),
        '预测最小订货量': features_df[pred_col].min(),
        '预测标准差': features_df[pred_col].std()
    }
    prediction_stats.append(stats)

prediction_stats_df = pd.DataFrame(prediction_stats)

# 省份级别预测汇总
province_predictions = features_df.groupby('省份')['集成预测30天订货量'].agg([
    'sum', 'mean', 'count', 'std'
]).round(2)
province_predictions.columns = ['预测总订货量', '预测平均订货量', '仓库数量', '预测标准差']
province_predictions = province_predictions.sort_values('预测总订货量', ascending=False)

# 保存结果
with pd.ExcelWriter('多模型预测结果.xlsx', engine='openpyxl') as writer:
    # 模型性能对比
    model_performance_data = []
    for name, metrics in model_results.items():
        row = {'模型': name}
        row.update(metrics)
        model_performance_data.append(row)
    model_performance_df = pd.DataFrame(model_performance_data)
    model_performance_df = model_performance_df.sort_values('MAE')
    model_performance_df.to_excel(writer, sheet_name='模型性能对比', index=False)

    # 预测统计对比
    prediction_stats_df.to_excel(writer, sheet_name='预测统计对比', index=False)

    # 各仓库详细预测
    output_columns = ['省份', '仓库', '历史订货次数', '历史总订货量', '目标30天订货量'] + \
                    [f'{name}预测30天订货量' for name in model_names] + \
                    ['集成预测30天订货量']

    features_df[output_columns].to_excel(writer, sheet_name='各仓库预测详情', index=False)

    # 省份汇总预测
    province_predictions.to_excel(writer, sheet_name='省份汇总预测')

# 8. 生成可视化对比
print("8. 生成可视化对比...")

import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

fig, axes = plt.subplots(2, 2, figsize=(16, 12))

# 1. 模型性能对比
model_names_plot = list(model_performance_df['模型'])
mae_values = list(model_performance_df['MAE'])
colors = plt.cm.Set3(np.linspace(0, 1, len(model_names_plot)))

bars = axes[0,0].barh(model_names_plot, mae_values, color=colors)
axes[0,0].set_title('各模型平均绝对误差对比', fontsize=14, fontweight='bold')
axes[0,0].set_xlabel('平均绝对误差 (MAE)', fontsize=12)
axes[0,0].grid(True, alpha=0.3)

# 添加数值标签
for i, (bar, value) in enumerate(zip(bars, mae_values)):
    axes[0,0].text(value + max(mae_values)*0.01, bar.get_y() + bar.get_height()/2,
                   f'{value:.2f}', va='center', fontsize=10)

# 2. 预测总订货量对比
ax = axes[0,1]
prediction_totals = prediction_stats_df[prediction_stats_df['模型'] != '集成']['预测总订货量']
model_names_for_plot = prediction_stats_df[prediction_stats_df['模型'] != '集成']['模型']

bars = ax.bar(model_names_for_plot, prediction_totals, color='lightblue', alpha=0.7)
ax.set_title('各模型预测总订货量对比', fontsize=14, fontweight='bold')
ax.set_xlabel('预测模型', fontsize=12)
ax.set_ylabel('预测总订货量（件）', fontsize=12)
ax.tick_params(axis='x', rotation=45)
ax.grid(True, alpha=0.3)

# 添加数值标签
for bar, value in zip(bars, prediction_totals):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(prediction_totals)*0.01,
            f'{value:.0f}', ha='center', va='bottom', fontsize=10)

# 3. 前10个省份的集成预测结果
top_provinces = province_predictions.head(10)
axes[1,0].barh(range(len(top_provinces)), top_provinces['预测总订货量'],
               color='lightgreen', alpha=0.8)
axes[1,0].set_title('前10个省份集成预测订货量', fontsize=14, fontweight='bold')
axes[1,0].set_xlabel('预测订货量（件）', fontsize=12)
axes[1,0].set_ylabel('省份', fontsize=12)
axes[1,0].set_yticks(range(len(top_provinces)))
axes[1,0].set_yticklabels(top_provinces.index)
axes[1,0].grid(True, alpha=0.3)

# 4. 不同模型预测的分布对比
sample_predictions = prediction_stats_df[prediction_stats_df['模型'] != '集成'][['模型', '预测平均订货量', '预测标准差']]
x_pos = np.arange(len(sample_predictions))

axes[1,1].errorbar(x_pos, sample_predictions['预测平均订货量'],
                   yerr=sample_predictions['预测标准差'],
                   fmt='o', capsize=5, capthick=2, markersize=8)
axes[1,1].set_title('各模型预测平均值±标准差', fontsize=14, fontweight='bold')
axes[1,1].set_xlabel('预测模型', fontsize=12)
axes[1,1].set_ylabel('预测订货量（件）', fontsize=12)
axes[1,1].set_xticks(x_pos)
axes[1,1].set_xticklabels(sample_predictions['模型'], rotation=45, ha='right')
axes[1,1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('多模型预测对比分析.png', dpi=300, bbox_inches='tight')
plt.close()

print("\n多模型预测分析完成！")
print("=" * 60)
print("主要输出文件：")
print("1. 多模型预测结果.xlsx - 详细的预测结果和模型性能对比")
print("2. 多模型预测对比分析.png - 可视化对比图表")
print("\n最佳集成预测总结：")
print(f"- 预测仓库总数: {len(features_df)}个")
print(f"- 集成预测30天总订货量: {features_df['集成预测30天订货量'].sum():.0f}件")
print(f"- 集成预测平均每仓订货量: {features_df['集成预测30天订货量'].mean():.0f}件")
print(f"- 集成预测最大订货量: {features_df['集成预测30天订货量'].max():.0f}件")
print(f"- 集成预测最小订货量: {features_df['集成预测30天订货量'].min():.0f}件")