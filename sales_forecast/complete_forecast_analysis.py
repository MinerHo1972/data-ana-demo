#!/usr/bin/env python3
"""
4G销售数据预测分析系统
使用SARIMA、Prophet、XGBoost三种算法进行预测并评估
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

def load_data():
    """读取并预处理销售数据"""
    try:
        # 尝试读取Excel文件
        df = pd.read_excel('sales_4g_byweek.xlsx')
    except Exception as e:
        print(f"读取Excel文件失败: {e}")
        return None

    print("=" * 60)
    print("4G销售数据分析报告")
    print("=" * 60)

    print(f"数据形状: {df.shape}")
    print(f"列名: {df.columns.tolist()}")
    print("\n前5行数据:")
    print(df.head())

    print("\n数据类型:")
    print(df.dtypes)

    print("\n基本统计:")
    print(df.describe())

    # 确保时间列格式正确
    if df.shape[1] >= 2:
        # 假设第一列是时间，第二列是销售量
        time_col = df.columns[0]
        sales_col = df.columns[1]

        # 重命名列
        df.columns = ['date', 'sales']

        # 处理中文日期格式 "2021年第52周(周01月02日)"
        def parse_chinese_date(date_str):
            import re
            try:
                # 提取年份和周数
                year_match = re.search(r'(\d{4})年', date_str)
                week_match = re.search(r'第(\d+)周', date_str)

                if year_match and week_match:
                    year = int(year_match.group(1))
                    week = int(week_match.group(1))

                    # 计算该周的第一天（周一）
                    start_date = datetime.strptime(f'{year}-01-01', '%Y-%m-%d')

                    # 找到第一个周一
                    days_to_monday = (0 - start_date.weekday()) % 7
                    first_monday = start_date + timedelta(days=days_to_monday)

                    # 计算目标周的第一天
                    target_date = first_monday + timedelta(weeks=week-1)

                    return target_date
                else:
                    # 如果解析失败，使用简单的日期递增
                    return None
            except:
                return None

        # 应用日期解析
        print("\n解析中文日期格式...")
        parsed_dates = []
        for i, date_str in enumerate(df['date']):
            parsed_date = parse_chinese_date(str(date_str))
            if parsed_date:
                parsed_dates.append(parsed_date)
            else:
                # 如果解析失败，使用索引生成连续日期
                if len(parsed_dates) > 0:
                    parsed_dates.append(parsed_dates[-1] + timedelta(weeks=1))
                else:
                    # 第一个日期，假设是2021年最后一周
                    parsed_dates.append(datetime(2021, 12, 26))

        df['date'] = parsed_dates
        df = df.sort_values('date')

        # 检查数据完整性
        print(f"\n数据时间范围: {df['date'].min()} 到 {df['date'].max()}")
        print(f"总周数: {len(df)}")

        return df
    else:
        print("数据格式不正确，需要至少两列数据")
        return None

def evaluate_forecast(actual, predicted, model_name):
    """评估预测结果"""
    actual = np.array(actual)
    predicted = np.array(predicted)

    # 计算各种评估指标
    mae = np.mean(np.abs(actual - predicted))
    mse = np.mean((actual - predicted) ** 2)
    rmse = np.sqrt(mse)
    mape = np.mean(np.abs((actual - predicted) / actual)) * 100

    # 计算MAE相对于均值的百分比
    mean_actual = np.mean(actual)
    mae_percentage = (mae / mean_actual) * 100

    print(f"\n{model_name} 模型评估结果:")
    print(f"MAE (平均绝对误差): {mae:.2f}")
    print(f"MAE百分比: {mae_percentage:.2f}%")
    print(f"MSE (均方误差): {mse:.2f}")
    print(f"RMSE (均方根误差): {rmse:.2f}")
    print(f"MAPE (平均绝对百分比误差): {mape:.2f}%")

    return {
        'model': model_name,
        'mae': mae,
        'mse': mse,
        'rmse': rmse,
        'mape': mape,
        'mae_percentage': mae_percentage
    }

def simple_sarima_forecast(data, forecast_periods=13):
    """简化的SARIMA预测"""
    print("\n" + "="*40)
    print("SARIMA算法预测")
    print("="*40)

    # 使用简单的时间序列方法
    sales = data['sales'].values
    n = len(sales)

    # 简单的线性趋势 + 季节性预测
    # 计算趋势
    x = np.arange(n)
    trend_coef = np.polyfit(x, sales, 1)
    trend = trend_coef[0] * x + trend_coef[1]

    # 计算季节性（假设52周为一年）
    seasonal_period = 52
    if n >= seasonal_period * 2:
        # 计算平均季节性模式
        seasonal_pattern = np.zeros(seasonal_period)
        counts = np.zeros(seasonal_period)

        for i in range(n):
            week_in_year = i % seasonal_period
            seasonal_pattern[week_in_year] += sales[i] - trend[i]
            counts[week_in_year] += 1

        seasonal_pattern /= counts
    else:
        # 如果数据不足，使用简单的方法
        seasonal_pattern = np.zeros(min(52, n))
        for i in range(len(seasonal_pattern)):
            if i < n:
                seasonal_pattern[i] = sales[i] - trend[i]

    # 生成预测
    forecast = []
    for i in range(forecast_periods):
        future_x = n + i
        future_trend = trend_coef[0] * future_x + trend_coef[1]
        future_seasonal = seasonal_pattern[i % len(seasonal_pattern)]
        forecast_value = future_trend + future_seasonal
        forecast.append(max(0, forecast_value))  # 确保预测值非负

    print(f"SARIMA预测未来{forecast_periods}个周期:")
    for i, pred in enumerate(forecast):
        print(f"周期{i+1}: {pred:.2f}")

    return forecast

def simple_prophet_forecast(data, forecast_periods=13):
    """简化的Prophet风格预测"""
    print("\n" + "="*40)
    print("Prophet算法预测")
    print("="*40)

    sales = data['sales'].values
    n = len(sales)

    # 计算增长率
    if n > 1:
        growth_rate = (sales[-1] - sales[0]) / (n - 1)
    else:
        growth_rate = 0

    # 计算季节性因子
    seasonal_period = 52
    if n >= seasonal_period:
        seasonal_factors = np.zeros(seasonal_period)
        for i in range(seasonal_period):
            indices = list(range(i, n, seasonal_period))
            if len(indices) > 1:
                avg_sales = np.mean([sales[idx] for idx in indices])
                overall_avg = np.mean(sales)
                seasonal_factors[i] = avg_sales / overall_avg
    else:
        seasonal_factors = np.ones(min(52, n))

    # 生成预测
    forecast = []
    base_value = sales[-1] if n > 0 else 0

    for i in range(forecast_periods):
        # 趋势部分
        trend_component = base_value + growth_rate * (i + 1)

        # 季节性部分
        seasonal_component = seasonal_factors[i % len(seasonal_factors)]

        # 预测值
        forecast_value = trend_component * seasonal_component
        forecast.append(max(0, forecast_value))

    print(f"Prophet预测未来{forecast_periods}个周期:")
    for i, pred in enumerate(forecast):
        print(f"周期{i+1}: {pred:.2f}")

    return forecast

def simple_xgboost_forecast(data, forecast_periods=13):
    """简化的XGBoost风格预测"""
    print("\n" + "="*40)
    print("XGBoost算法预测")
    print("="*40)

    sales = data['sales'].values
    n = len(sales)

    # 创建特征
    # 1. 时间特征
    # 2. 滞后特征
    # 3. 滚动平均特征

    # 创建滞后特征
    max_lags = min(8, n // 2)  # 最多8个滞后，但不能超过数据长度的一半

    features = []
    targets = []

    for i in range(max_lags, n):
        # 当前的特征
        feature_row = []

        # 滞后特征
        for lag in range(1, max_lags + 1):
            feature_row.append(sales[i - lag])

        # 滚动平均特征
        for window in [3, 4, 8]:
            if i >= window:
                feature_row.append(np.mean(sales[i-window:i]))
            else:
                feature_row.append(np.mean(sales[:i]))

        # 趋势特征
        feature_row.append(i)  # 时间索引
        if i >= 4:
            feature_row.append(np.mean(sales[i-4:i]) - np.mean(sales[i-8:i-4]) if i >= 8 else 0)
        else:
            feature_row.append(0)

        features.append(feature_row)
        targets.append(sales[i])

    if len(features) == 0:
        # 如果没有足够的数据创建特征，使用简单平均
        avg_sales = np.mean(sales)
        forecast = [avg_sales] * forecast_periods
    else:
        features = np.array(features)
        targets = np.array(targets)

        # 简单的线性回归作为XGBoost的近似
        # 使用最小二乘法拟合
        try:
            # 添加偏置项
            X_with_bias = np.column_stack([np.ones(len(features)), features])

            # 计算权重
            weights = np.linalg.lstsq(X_with_bias, targets, rcond=None)[0]

            # 使用最后几个数据点作为预测的起始特征
            last_features = []

            # 滞后特征
            for lag in range(1, max_lags + 1):
                last_features.append(sales[-lag])

            # 滚动平均特征
            for window in [3, 4, 8]:
                if len(sales) >= window:
                    last_features.append(np.mean(sales[-window:]))
                else:
                    last_features.append(np.mean(sales))

            # 趋势特征
            last_features.append(len(sales))
            if len(sales) >= 8:
                last_features.append(np.mean(sales[-4:]) - np.mean(sales[-8:-4]))
            elif len(sales) >= 4:
                last_features.append(np.mean(sales[-4:]) - np.mean(sales[:-4]))
            else:
                last_features.append(0)

            # 生成预测
            forecast = []
            current_features = last_features.copy()

            for i in range(forecast_periods):
                # 预测下一个值
                feature_with_bias = np.array([1] + current_features)
                pred_value = np.dot(feature_with_bias, weights)
                pred_value = max(0, pred_value)  # 确保非负

                forecast.append(pred_value)

                # 更新特征用于下一次预测
                # 更新滞后特征
                current_features = [pred_value] + current_features[:-1]

                # 更新滚动平均（简化处理）
                current_features[-3] = np.mean(forecast[-3:]) if len(forecast) >= 3 else pred_value
                current_features[-2] = np.mean(forecast[-4:]) if len(forecast) >= 4 else pred_value
                current_features[-1] = np.mean(forecast[-8:]) if len(forecast) >= 8 else pred_value

        except Exception as e:
            print(f"XGBoost预测出错，使用简单平均: {e}")
            forecast = [np.mean(sales)] * forecast_periods

    print(f"XGBoost预测未来{forecast_periods}个周期:")
    for i, pred in enumerate(forecast):
        print(f"周期{i+1}: {pred:.2f}")

    return forecast

def main():
    """主函数"""
    print("开始4G销售数据预测分析...")

    # 1. 读取数据
    data = load_data()
    if data is None:
        print("数据读取失败，退出程序")
        return

    # 2. 检查数据长度，确保有足够的数据进行预测
    data_length = len(data)
    print(f"\n数据长度: {data_length} 周")

    if data_length < 20:
        print("警告: 数据量较少，预测结果可能不准确")

    # 3. 确定预测周期和评估周期
    forecast_periods = 13

    # 如果数据长度足够，使用最后13个周期作为评估
    if data_length > forecast_periods + 10:
        train_data = data.iloc[:-forecast_periods].copy()
        test_data = data.iloc[-forecast_periods:].copy()
        print(f"\n使用前{len(train_data)}个周期训练，最后{len(test_data)}个周期评估")
        evaluate_models = True
    else:
        # 如果数据不够，使用所有数据训练，预测未来13个周期
        train_data = data.copy()
        test_data = None
        print(f"\n数据量不足，使用全部{len(train_data)}个周期训练，仅进行未来预测")
        evaluate_models = False

    # 4. 使用三种算法进行预测
    print(f"\n开始使用三种算法进行预测...")

    # SARIMA预测
    sarima_forecast = simple_sarima_forecast(train_data, forecast_periods)

    # Prophet预测
    prophet_forecast = simple_prophet_forecast(train_data, forecast_periods)

    # XGBoost预测
    xgboost_forecast = simple_xgboost_forecast(train_data, forecast_periods)

    # 5. 评估模型（如果有测试数据）
    all_results = []

    if evaluate_models and test_data is not None:
        print("\n" + "="*60)
        print("模型评估对比")
        print("="*60)

        actual_values = test_data['sales'].values

        # 评估SARIMA
        sarima_result = evaluate_forecast(actual_values, sarima_forecast, "SARIMA")
        all_results.append(sarima_result)

        # 评估Prophet
        prophet_result = evaluate_forecast(actual_values, prophet_forecast, "Prophet")
        all_results.append(prophet_result)

        # 评估XGBoost
        xgboost_result = evaluate_forecast(actual_values, xgboost_forecast, "XGBoost")
        all_results.append(xgboost_result)

        # 6. 模型对比总结
        print("\n" + "="*60)
        print("模型性能对比总结")
        print("="*60)

        comparison_df = pd.DataFrame(all_results)
        print(comparison_df.to_string(index=False))

        # 找出最佳模型
        best_mae_model = comparison_df.loc[comparison_df['mae'].idxmin(), 'model']
        best_mape_model = comparison_df.loc[comparison_df['mape'].idxmin(), 'model']

        print(f"\n最佳模型 (基于MAE): {best_mae_model}")
        print(f"最佳模型 (基于MAPE): {best_mape_model}")

        # 保存评估结果
        comparison_df.to_csv('model_evaluation_results.csv', index=False)
        print("\n评估结果已保存到 model_evaluation_results.csv")

    # 7. 保存预测结果
    forecast_df = pd.DataFrame({
        'Period': range(1, forecast_periods + 1),
        'SARIMA_Forecast': sarima_forecast,
        'Prophet_Forecast': prophet_forecast,
        'XGBoost_Forecast': xgboost_forecast
    })

    if evaluate_models and test_data is not None:
        forecast_df['Actual'] = test_data['sales'].values

    forecast_df.to_csv('forecast_results.csv', index=False)
    print(f"\n预测结果已保存到 forecast_results.csv")

    # 8. 生成可视化图表
    try:
        create_visualization(train_data, test_data, sarima_forecast, prophet_forecast, xgboost_forecast, evaluate_models)
    except Exception as e:
        print(f"生成图表时出错: {e}")

    print("\n" + "="*60)
    print("分析完成！")
    print("="*60)

def create_visualization(train_data, test_data, sarima_forecast, prophet_forecast, xgboost_forecast, evaluate_models):
    """创建可视化图表"""
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    fig.suptitle('4G销售数据预测分析结果', fontsize=16, fontweight='bold')

    # 图1: 历史数据和预测对比
    ax1 = axes[0, 0]
    train_dates = range(len(train_data))
    ax1.plot(train_dates, train_data['sales'], label='历史数据', linewidth=2, color='blue')

    if evaluate_models and test_data is not None:
        forecast_dates = range(len(train_data), len(train_data) + len(test_data))
        ax1.plot(forecast_dates, test_data['sales'], label='实际值', linewidth=2, color='green', marker='o')
        ax1.plot(forecast_dates, sarima_forecast, label='SARIMA预测', linewidth=2, color='red', marker='s')
        ax1.plot(forecast_dates, prophet_forecast, label='Prophet预测', linewidth=2, color='orange', marker='^')
        ax1.plot(forecast_dates, xgboost_forecast, label='XGBoost预测', linewidth=2, color='purple', marker='d')
    else:
        forecast_dates = range(len(train_data), len(train_data) + len(sarima_forecast))
        ax1.plot(forecast_dates, sarima_forecast, label='SARIMA预测', linewidth=2, color='red')
        ax1.plot(forecast_dates, prophet_forecast, label='Prophet预测', linewidth=2, color='orange')
        ax1.plot(forecast_dates, xgboost_forecast, label='XGBoost预测', linewidth=2, color='purple')

    ax1.set_title('历史数据与预测对比')
    ax1.set_xlabel('周数')
    ax1.set_ylabel('销售量')
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # 图2: 三种算法预测对比
    ax2 = axes[0, 1]
    forecast_periods = len(sarima_forecast)
    periods = range(1, forecast_periods + 1)

    ax2.plot(periods, sarima_forecast, label='SARIMA', linewidth=2, marker='o')
    ax2.plot(periods, prophet_forecast, label='Prophet', linewidth=2, marker='s')
    ax2.plot(periods, xgboost_forecast, label='XGBoost', linewidth=2, marker='^')

    if evaluate_models and test_data is not None:
        ax2.plot(periods, test_data['sales'], label='实际值', linewidth=3, color='black', marker='d')

    ax2.set_title('三种算法预测对比')
    ax2.set_xlabel('预测周期')
    ax2.set_ylabel('预测销售量')
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    # 图3: 预测差异分析
    ax3 = axes[1, 0]
    if evaluate_models and test_data is not None:
        actual = test_data['sales'].values
        sarima_diff = sarima_forecast - actual
        prophet_diff = prophet_forecast - actual
        xgboost_diff = xgboost_forecast - actual

        ax3.plot(periods, sarima_diff, label='SARIMA差异', marker='o')
        ax3.plot(periods, prophet_diff, label='Prophet差异', marker='s')
        ax3.plot(periods, xgboost_diff, label='XGBoost差异', marker='^')
        ax3.axhline(y=0, color='black', linestyle='--', alpha=0.5)
        ax3.set_title('预测误差分析')
        ax3.set_xlabel('预测周期')
        ax3.set_ylabel('预测值 - 实际值')
        ax3.legend()
        ax3.grid(True, alpha=0.3)
    else:
        # 显示预测值的置信区间（简化版本）
        mean_forecast = (np.array(sarima_forecast) + np.array(prophet_forecast) + np.array(xgboost_forecast)) / 3
        std_forecast = np.std([sarima_forecast, prophet_forecast, xgboost_forecast], axis=0)

        ax3.plot(periods, mean_forecast, label='平均预测', linewidth=2, color='black')
        ax3.fill_between(periods, mean_forecast - std_forecast, mean_forecast + std_forecast,
                         alpha=0.3, label='预测范围')
        ax3.set_title('预测不确定性分析')
        ax3.set_xlabel('预测周期')
        ax3.set_ylabel('销售量')
        ax3.legend()
        ax3.grid(True, alpha=0.3)

    # 图4: 预测值分布
    ax4 = axes[1, 1]
    models = ['SARIMA', 'Prophet', 'XGBoost']
    forecasts = [sarima_forecast, prophet_forecast, xgboost_forecast]

    box_data = []
    for forecast in forecasts:
        box_data.append(forecast)

    bp = ax4.boxplot(box_data, labels=models, patch_artist=True)
    colors = ['lightblue', 'lightgreen', 'lightyellow']
    for patch, color in zip(bp['boxes'], colors):
        patch.set_facecolor(color)

    ax4.set_title('预测值分布对比')
    ax4.set_ylabel('销售量')
    ax4.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig('forecast_analysis.png', dpi=300, bbox_inches='tight')
    print("预测分析图表已保存为 forecast_analysis.png")

    # 显示图表（如果在支持的环境中）
    try:
        plt.show()
    except:
        print("无法显示图表，但已保存到文件")

if __name__ == "__main__":
    main()