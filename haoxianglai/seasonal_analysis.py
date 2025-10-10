import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from datetime import datetime, timedelta
from scipy import stats
from scipy.signal import find_peaks
import warnings
warnings.filterwarnings('ignore')

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

print("开始分析订货数据的周期性规律...")

# 读取数据
df = pd.read_excel('haoxianglai.xlsx')
cols = df.columns.tolist()
df['订货日期'] = pd.to_datetime(df[cols[4]])

print(f"数据时间范围: {df['订货日期'].min()} 至 {df['订货日期'].max()}")
print(f"总记录数: {len(df)}条")

# 1. 按日期聚合订货数据
print("\n1. 按日期聚合数据...")
daily_data = df.groupby('订货日期').agg({
    cols[3]: ['sum', 'count', 'mean']
}).round(2)
daily_data.columns = ['每日总订货量', '每日订货次数', '平均每次订货量']
daily_data = daily_data.reset_index()

# 填充缺失日期（没有订货的日期）
date_range = pd.date_range(start=df['订货日期'].min(), end=df['订货日期'].max(), freq='D')
daily_data = daily_data.set_index('订货日期').reindex(date_range).fillna(0)
daily_data.index.name = '订货日期'

# 2. 基础周期性分析
print("2. 基础周期性分析...")

# 添加时间特征
daily_data['星期几'] = daily_data.index.dayofweek
daily_data['一年中的第几周'] = daily_data.index.isocalendar().week
daily_data['月份'] = daily_data.index.month
daily_data['日期'] = daily_data.index.day

# 按星期几分析
weekday_analysis = daily_data.groupby('星期几')['每日总订货量'].agg(['mean', 'std', 'count']).round(2)
weekday_names = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
weekday_analysis.index = weekday_names

# 按月份分析
month_analysis = daily_data.groupby('月份')['每日总订货量'].agg(['mean', 'std', 'count']).round(2)

# 按一月中的日期分析
day_of_month_analysis = daily_data.groupby('日期')['每日总订货量'].agg(['mean', 'std', 'count']).round(2)

# 3. 寻找峰值和低谷
print("3. 识别订货峰值和低谷...")

# 使用移动平均平滑数据
daily_data['7天移动平均'] = daily_data['每日总订货量'].rolling(window=7, center=True).mean()
daily_data['14天移动平均'] = daily_data['每日总订货量'].rolling(window=14, center=True).mean()

# 寻找峰值（使用平滑后的数据）
smoothed_data = daily_data['14天移动平均'].fillna(method='bfill').fillna(method='ffill')
peaks, _ = find_peaks(smoothed_data, height=smoothed_data.mean(), distance=7)
valleys, _ = find_peaks(-smoothed_data, height=-smoothed_data.mean(), distance=7)

print(f"识别到 {len(peaks)} 个峰值和 {len(valleys)} 个低谷")

# 4. 周期性统计检验
print("4. 周期性统计检验...")

# 按星期的方差分析
weekday_groups = [group['每日总订货量'].values for name, group in daily_data.groupby('星期几')]
f_stat_weekday, p_value_weekday = stats.f_oneway(*weekday_groups)

# 按月份的方差分析
month_groups = [group['每日总订货量'].values for name, group in daily_data.groupby('月份')]
f_stat_month, p_value_month = stats.f_oneway(*month_groups)

print(f"星期效应方差分析: F={f_stat_weekday:.3f}, p={p_value_weekday:.4f}")
print(f"月份效应方差分析: F={f_stat_month:.3f}, p={p_value_month:.4f}")

# 5. 自相关分析
print("5. 自相关分析...")

# 计算不同滞后期的自相关
def autocorrelation_analysis(series, max_lag=30):
    autocorr_values = []
    for lag in range(1, max_lag + 1):
        autocorr = series.autocorr(lag=lag)
        if not np.isnan(autocorr):
            autocorr_values.append(autocorr)
        else:
            autocorr_values.append(0)
    return autocorr_values

autocorr_7days = autocorrelation_analysis(daily_data['每日总订货量'], 35)
autocorr_14days = autocorrelation_analysis(daily_data['每日总订货量'], 60)

# 寻找主要周期
significant_peaks_autocorr, _ = find_peaks(autocorr_7days, height=0.1, distance=5)

# 6. 预测下一次峰值
print("6. 预测下一次订货峰值...")

# 分析最近的历史周期
recent_data = daily_data.tail(60)  # 最近60天

# 计算不同周期的强度
def calculate_periodicity_strength(data, period):
    """计算特定周期的强度"""
    pattern = np.zeros(period)
    counts = np.zeros(period)

    for i in range(len(data)):
        pattern[i % period] += data.iloc[i]
        counts[i % period] += 1

    pattern = pattern / counts
    strength = np.std(pattern) / np.mean(pattern) if np.mean(pattern) > 0 else 0
    return strength, pattern

# 计算不同周期的强度
periods_to_test = [7, 14, 21, 30]  # 周、双周、三周、月
period_strengths = {}
period_patterns = {}

for period in periods_to_test:
    strength, pattern = calculate_periodicity_strength(recent_data['每日总订货量'], period)
    period_strengths[period] = strength
    period_patterns[period] = pattern
    print(f"{period}天周期强度: {strength:.4f}")

# 选择最强周期
strongest_period = max(period_strengths, key=period_strengths.get)
print(f"\n最强周期: {strongest_period}天")

# 预测下一次峰值
def predict_next_peak(data, period, last_date):
    """预测下一次峰值时间"""
    # 分析历史峰值在周期中的位置
    smoothed_data = data['14天移动平均'].fillna(method='bfill').fillna(method='ffill')
    peaks, _ = find_peaks(smoothed_data, distance=period//2)

    if len(peaks) == 0:
        return None, "未找到明显峰值模式"

    # 计算峰值在周期中的位置分布
    peak_positions = [p % period for p in peaks]
    peak_position_freq = np.bincount(peak_positions, minlength=period)
    most_common_position = np.argmax(peak_position_freq)

    # 预测下一个峰值
    days_since_last_peak = (len(data) - peaks[-1]) % period
    days_to_next_peak = (most_common_position - days_since_last_peak) % period

    if days_to_next_peak == 0:
        days_to_next_peak = period

    next_peak_date = last_date + timedelta(days=int(days_to_next_peak))
    confidence = peak_position_freq[most_common_position] / len(peaks)

    return next_peak_date, confidence

# 预测下次峰值
last_date = daily_data.index[-1]
next_peak_date, peak_confidence = predict_next_peak(daily_data, strongest_period, last_date)

if next_peak_date:
    print(f"\n预测下一次峰值: {next_peak_date.strftime('%Y年%m月%d日')}")
    print(f"预测置信度: {peak_confidence:.2%}")
else:
    print("\n无法预测下一次峰值时间")

# 7. 生成可视化
print("7. 生成周期性分析可视化...")

fig, axes = plt.subplots(3, 2, figsize=(18, 16))

# 1. 时间序列和峰值识别
ax1 = axes[0,0]
ax1.plot(daily_data.index, daily_data['每日总订货量'], alpha=0.6, color='lightblue', label='每日订货量')
ax1.plot(daily_data.index, daily_data['14天移动平均'], color='red', linewidth=2, label='14天移动平均')

# 标记峰值和低谷
if len(peaks) > 0:
    peak_dates = daily_data.index[peaks]
    peak_values = daily_data['14天移动平均'].iloc[peaks]
    ax1.scatter(peak_dates, peak_values, color='red', s=100, zorder=5, label='峰值')

if len(valleys) > 0:
    valley_dates = daily_data.index[valleys]
    valley_values = daily_data['14天移动平均'].iloc[valleys]
    ax1.scatter(valley_dates, valley_values, color='green', s=100, zorder=5, label='低谷')

# 预测下次峰值
if next_peak_date:
    ax1.axvline(x=next_peak_date, color='orange', linestyle='--', linewidth=2, label=f'预测下次峰值: {next_peak_date.strftime("%m-%d")}')

ax1.set_title('每日订货量时间序列及峰值识别', fontsize=14, fontweight='bold')
ax1.set_xlabel('日期')
ax1.set_ylabel('订货量（件）')
ax1.legend()
ax1.grid(True, alpha=0.3)

# 2. 星期几模式
ax2 = axes[0,1]
bars = ax2.bar(weekday_analysis.index, weekday_analysis['mean'], color='lightcoral', alpha=0.7)
ax2.set_title('按星期几的订货量分布', fontsize=14, fontweight='bold')
ax2.set_xlabel('星期几')
ax2.set_ylabel('平均订货量（件）')
ax2.tick_params(axis='x', rotation=45)

# 添加数值标签
for bar, value in zip(bars, weekday_analysis['mean']):
    ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(weekday_analysis['mean'])*0.01,
             f'{value:.0f}', ha='center', va='bottom', fontsize=10)

# 3. 月份模式
ax3 = axes[1,0]
bars = ax3.bar(month_analysis.index, month_analysis['mean'], color='lightgreen', alpha=0.7)
ax3.set_title('按月份的订货量分布', fontsize=14, fontweight='bold')
ax3.set_xlabel('月份')
ax3.set_ylabel('平均订货量（件）')
ax3.set_xticks(range(7, 11))  # 7月到10月

# 添加数值标签
for bar, value in zip(bars, month_analysis['mean']):
    ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(month_analysis['mean'])*0.01,
             f'{value:.0f}', ha='center', va='bottom', fontsize=10)

# 4. 一个月中日期的模式
ax4 = axes[1,1]
ax4.plot(day_of_month_analysis.index, day_of_month_analysis['mean'], marker='o', color='purple', linewidth=2)
ax4.set_title('一个月中各日期的订货量模式', fontsize=14, fontweight='bold')
ax4.set_xlabel('日期')
ax4.set_ylabel('平均订货量（件）')
ax4.grid(True, alpha=0.3)

# 5. 自相关分析
ax5 = axes[2,0]
lags = range(1, len(autocorr_7days) + 1)
ax5.bar(lags, autocorr_7days, color='orange', alpha=0.7)
ax5.set_title('订货量自相关分析（35天）', fontsize=14, fontweight='bold')
ax5.set_xlabel('滞后天数')
ax5.set_ylabel('自相关系数')
ax5.axhline(y=0, color='black', linestyle='-', alpha=0.3)
ax5.grid(True, alpha=0.3)

# 标记显著的自相关峰值
if len(significant_peaks_autocorr) > 0:
    for peak in significant_peaks_autocorr:
        ax5.scatter(peak + 1, autocorr_7days[peak], color='red', s=100, zorder=5)
        ax5.annotate(f'{peak+1}天', (peak + 1, autocorr_7days[peak]),
                    xytext=(5, 5), textcoords='offset points', fontsize=9)

# 6. 周期强度分析
ax6 = axes[2,1]
periods = list(period_strengths.keys())
strengths = list(period_strengths.values())

bars = ax6.bar([f'{p}天' for p in periods], strengths, color='gold', alpha=0.7)
ax6.set_title('不同周期的强度分析', fontsize=14, fontweight='bold')
ax6.set_xlabel('周期长度')
ax6.set_ylabel('周期强度')
ax6.grid(True, alpha=0.3)

# 标记最强周期
max_strength_idx = strengths.index(max(strengths))
bars[max_strength_idx].set_color('red')

# 添加数值标签
for bar, strength in zip(bars, strengths):
    ax6.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(strengths)*0.01,
             f'{strength:.3f}', ha='center', va='bottom', fontsize=10)

plt.tight_layout()
plt.savefig('订货周期性分析.png', dpi=300, bbox_inches='tight')
plt.close()

# 8. 保存分析结果
print("8. 保存周期性分析结果...")

# 创建详细的周期性分析报告
with pd.ExcelWriter('订货周期性分析结果.xlsx', engine='openpyxl') as writer:
    # 基础统计
    basic_stats = pd.DataFrame({
        '统计指标': ['分析天数', '总订货量', '平均每日订货量', '标准差', '最大值', '最小值', '峰值数量', '低谷数量'],
        '数值': [len(daily_data), daily_data['每日总订货量'].sum(), daily_data['每日总订货量'].mean(),
                daily_data['每日总订货量'].std(), daily_data['每日总订货量'].max(), daily_data['每日总订货量'].min(),
                len(peaks), len(valleys)]
    })
    basic_stats.to_excel(writer, sheet_name='基础统计', index=False)

    # 星期几分析
    weekday_analysis.to_excel(writer, sheet_name='星期几分析')

    # 月份分析
    month_analysis.to_excel(writer, sheet_name='月份分析')

    # 日期分析
    day_of_month_analysis.to_excel(writer, sheet_name='日期分析')

    # 周期强度分析
    period_analysis_df = pd.DataFrame({
        '周期长度(天)': periods,
        '周期强度': strengths,
        '周期类型': ['周', '双周', '三周', '月']
    })
    period_analysis_df.to_excel(writer, sheet_name='周期强度分析', index=False)

    # 峰值和低谷详情
    if len(peaks) > 0:
        peaks_df = pd.DataFrame({
            '峰值日期': daily_data.index[peaks],
            '订货量': daily_data['每日总订货量'].iloc[peaks],
            '14天移动平均': daily_data['14天移动平均'].iloc[peaks]
        })
        peaks_df.to_excel(writer, sheet_name='峰值详情', index=False)

    if len(valleys) > 0:
        valleys_df = pd.DataFrame({
            '低谷日期': daily_data.index[valleys],
            '订货量': daily_data['每日总订货量'].iloc[valleys],
            '14天移动平均': daily_data['14天移动平均'].iloc[valleys]
        })
        valleys_df.to_excel(writer, sheet_name='低谷详情', index=False)

    # 预测结果
    prediction_results = pd.DataFrame({
        '预测项目': ['最强周期', '下次预测峰值日期', '预测置信度', '星期效应显著性', '月份效应显著性'],
        '结果': [f'{strongest_period}天',
                next_peak_date.strftime('%Y-%m-%d') if next_peak_date else '无法预测',
                f'{peak_confidence:.2%}' if peak_confidence else '无法计算',
                '显著' if p_value_weekday < 0.05 else '不显著',
                '显著' if p_value_month < 0.05 else '不显著']
    })
    prediction_results.to_excel(writer, sheet_name='预测结果', index=False)

print("\n周期性分析完成！")
print("=" * 60)
print("主要发现：")
print(f"1. 星期效应: {'显著' if p_value_weekday < 0.05 else '不显著'} (p={p_value_weekday:.4f})")
print(f"2. 月份效应: {'显著' if p_value_month < 0.05 else '不显著'} (p={p_value_month:.4f})")
print(f"3. 最强周期: {strongest_period}天")
print(f"4. 识别到 {len(peaks)} 个历史峰值和 {len(valleys)} 个低谷")
if next_peak_date:
    print(f"5. 预测下次峰值: {next_peak_date.strftime('%Y年%m月%d日')} (置信度: {peak_confidence:.1%})")
else:
    print("5. 无法预测下次峰值时间")

print("\n输出文件：")
print("1. 订货周期性分析.png - 可视化分析图表")
print("2. 订货周期性分析结果.xlsx - 详细分析数据")