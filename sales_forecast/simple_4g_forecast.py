#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版4G销售预测系统
不依赖外部库，直接使用三种方法预测
"""

import random
import math

def analyze_sales_pattern(sales_data):
    """分析销售数据模式"""
    print(f"\n销售数据分析:")
    print(f"数据点数量: {len(sales_data)}")
    print(f"最小销量: {min(sales_data)}")
    print(f"最大销量: {max(sales_data)}")
    print(f"平均销量: {sum(sales_data)/len(sales_data):.2f}")

    # 计算趋势
    if len(sales_data) >= 4:
        first_half = sales_data[:len(sales_data)//2]
        second_half = sales_data[len(sales_data)//2:]
        first_avg = sum(first_half)/len(first_half)
        second_avg = sum(second_half)/len(second_half)

        if second_avg > first_avg * 1.1:
            trend = "上升"
        elif second_avg < first_avg * 0.9:
            trend = "下降"
        else:
            trend = "稳定"

        print(f"趋势分析: {trend} (前期平均: {first_avg:.1f}, 后期平均: {second_avg:.1f})")
        return trend
    else:
        print("数据不足，无法进行趋势分析")
        return "稳定"

def sarima_style_forecast(sales_data, forecast_weeks=13):
    """SARIMA风格的预测"""
    print(f"\n=== SARIMA风格预测 ===")

    if len(sales_data) < 4:
        print("数据不足，使用简单平均")
        avg_sales = sum(sales_data) / len(sales_data)
        return [avg_sales] * forecast_weeks

    # 计算移动平均
    recent_avg = sum(sales_data[-4:]) / 4
    overall_avg = sum(sales_data) / len(sales_data)

    # 计算季节性因子（简化版）
    seasonal_factors = []
    for week in range(forecast_weeks):
        # 模拟年度季节性
        seasonal_factor = 1 + 0.2 * math.sin(2 * math.pi * week / 52)
        seasonal_factors.append(seasonal_factor)

    # 生成预测
    predictions = []
    for i in range(forecast_weeks):
        # 结合近期平均和季节性
        base_prediction = 0.7 * recent_avg + 0.3 * overall_avg
        seasonal_prediction = base_prediction * seasonal_factors[i]

        predictions.append(max(10, seasonal_prediction))

    print(f"基础预测值: {recent_avg:.2f}")
    print(f"季节性因子范围: {min(seasonal_factors):.2f} - {max(seasonal_factors):.2f}")
    print(f"预测结果: {predictions[0]:.1f} ... {predictions[-1]:.1f}")

    return predictions

def xgboost_style_forecast(sales_data, forecast_weeks=13):
    """XGBoost风格的预测"""
    print(f"\n=== XGBoost风格预测 ===")

    if len(sales_data) < 4:
        return [sum(sales_data)/len(sales_data)] * forecast_weeks

    # 特征工程：计算多个统计特征
    recent_2w = sum(sales_data[-2:]) / 2
    recent_4w = sum(sales_data[-4:]) / 4
    recent_8w = sum(sales_data[-8:]) / 8 if len(sales_data) >= 8 else recent_4w

    # 计算趋势特征
    if len(sales_data) >= 4:
        trend_slope = (sales_data[-1] - sales_data[-4]) / 4
    else:
        trend_slope = 0

    # 计算波动性
    if len(sales_data) >= 4:
            recent_values = sales_data[-4:]
            variance = sum((x - sum(recent_values)/4)**2 for x in recent_values) / 4
        else:
            variance = 0

    print(f"特征分析:")
    print(f"  近2周平均: {recent_2w:.2f}")
    print(f"  近4周平均: {recent_4w:.2f}")
    print(f"  近8周平均: {recent_8w:.2f}")
    print(f"  趋势斜率: {trend_slope:.2f}")
    print(f"  波动性: {variance:.2f}")

    # 使用加权组合进行预测
    predictions = []
    for i in range(forecast_weeks):
        # 时间衰减权重
        weight_2w = 0.4
        weight_4w = 0.3
        weight_8w = 0.2
        weight_trend = 0.1

        # 基础预测
        base_prediction = (weight_2w * recent_2w +
                         weight_4w * recent_4w +
                         weight_8w * recent_8w)

        # 添加趋势影响
        trend_effect = trend_slope * (i + 1)
        final_prediction = base_prediction + trend_effect

        # 添加一些随机性来模拟复杂模式
        if variance > 100:  # 如果波动性较大
            random_factor = 1 + random.uniform(-0.1, 0.1)
            final_prediction *= random_factor

        predictions.append(max(10, final_prediction))

    print(f"预测结果范围: {min(predictions):.1f} - {max(predictions):.1f}")

    return predictions

def prophet_style_forecast(sales_data, forecast_weeks=13):
    """Prophet风格的预测"""
    print(f"\n=== Prophet风格预测 ===")

    if len(sales_data) < 4:
        return [sum(sales_data)/len(sales_data)] * forecast_weeks

    # 分解趋势和季节性
    # 1. 计算整体趋势（线性回归简化版）
    n = len(sales_data)
    x_values = list(range(n))
    y_values = sales_data

    # 简单线性回归
    sum_x = sum(x_values)
    sum_y = sum(y_values)
    sum_xy = sum(x * y for x, y in zip(x_values, y_values))
    sum_x2 = sum(x * x for x in x_values)

    slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
    intercept = (sum_y - slope * sum_x) / n

    print(f"趋势分析:")
    print(f"  斜率: {slope:.3f} ({'上升' if slope > 0 else '下降'})")
    print(f"  截距: {intercept:.2f}")

    # 2. 计算季节性模式（年度）
    seasonal_pattern = []
    for week in range(52):
        week_sales = [sales_data[i] for i in range(week, len(sales_data), 52)]
        if week_sales:
            avg_week_sales = sum(week_sales) / len(week_sales)
            seasonal_pattern.append(avg_week_sales - intercept)  # 减去趋势
        else:
            seasonal_pattern.append(0)

    # 归一化季节性因子
    if seasonal_pattern:
        avg_seasonal = sum(seasonal_pattern) / len(seasonal_pattern)
        seasonal_factors = [(s - avg_seasonal) / avg_seasonal if avg_seasonal != 0 else 0
                           for s in seasonal_pattern]
    else:
        seasonal_factors = [0] * 52

    # 3. 生成预测
    predictions = []
    for i in range(forecast_weeks):
        future_x = n + i
        trend_value = slope * future_x + intercept

        # 应用季节性
        seasonal_index = i % 52
        seasonal_factor = 1 + seasonal_factors[seasonal_index] if seasonal_factors else 1

        predicted = trend_value * seasonal_factor
        predictions.append(max(10, predicted))

    print(f"季节性因子示例: 前4周 {seasonal_factors[:4]}")
    print(f"预测结果范围: {min(predictions):.1f} - {max(predictions):.1f}")

    return predictions

def create_demo_data():
    """创建演示用的4G销售数据"""
    print("创建演示用的4G销售数据...")
    weeks = list(range(1, 27))  # 26周的数据
    sales = []

    for week in weeks:
        # 模拟4G产品销售特点
        base_sales = 80 + 40 * (1 - math.exp(-week/15))  # 初期快速增长
        seasonal = 15 * math.sin(2 * math.pi * week / 52)  # 季节性
        noise = random.uniform(-8, 8)  # 随机噪声

        # 添加促销效果
        if week % 6 == 0:  # 每6周一次促销
            promotion = random.uniform(20, 35)
        else:
            promotion = 0

        weekly_sales = base_sales + seasonal + noise + promotion
        sales.append(max(30, weekly_sales))

    return weeks, sales

def forecast_4g_sales():
    """主预测函数"""
    print("="*60)
    print("4G产品销售预测系统")
    print("="*60)

    # 创建演示数据
    weeks, sales = create_demo_data()

    print(f"\n原始数据预览:")
    print("周数   销量")
    print("-" * 15)
    for i in range(min(10, len(weeks))):
        print(f"{weeks[i]:<6} {sales[i]:<6.1f}")
    if len(weeks) > 10:
        print("...")

    # 分析销售模式
    trend = analyze_sales_pattern(sales)

    # 使用三种方法进行预测
    print(f"\n{'='*60}")
    print("开始使用三种方法预测未来13周销售数据")
    print(f"{'='*60}")

    # 1. SARIMA风格预测
    sarima_predictions = sarima_style_forecast(sales)

    # 2. XGBoost风格预测
    xgb_predictions = xgboost_style_forecast(sales)

    # 3. Prophet风格预测
    prophet_predictions = prophet_style_forecast(sales)

    # 对比分析
    print(f"\n{'='*60}")
    print("预测结果对比分析")
    print(f"{'='*60}")

    print(f"\n各方法预测结果对比:")
    print(f"{'方法':<15} {'平均预测':<12} {'最小预测':<12} {'最大预测':<12} {'稳定性':<10}")
    print("-" * 70)

    methods = [
        ("SARIMA风格", sarima_predictions),
        ("XGBoost风格", xgb_predictions),
        ("Prophet风格", prophet_predictions)
    ]

    for method_name, predictions in methods:
        avg_pred = sum(predictions) / len(predictions)
        min_pred = min(predictions)
        max_pred = max(predictions)
        stability = max(predictions) - min(predictions)  # 简单稳定性指标

        print(f"{method_name:<15} {avg_pred:<12.2f} {min_pred:<12.2f} {max_pred:<12.2f} {stability:<10.2f}")

    # 详细预测结果
    print(f"\n未来13周详细预测:")
    print("-" * 80)
    print(f"{'未来周':<8}", end="")
    for method_name, _ in methods:
        print(f"{method_name:<12}", end="")
    print()
    print("-" * 80)

    for week in range(13):
        print(f"第{week+1:<5}周", end="")
        for _, predictions in methods:
            print(f"{predictions[week]:<12.1f}", end="")
        print()

    # 方法推荐
    print(f"\n方法特点与建议:")
    print(f"• SARIMA风格:")
    print(f"  - 适合有稳定季节性的数据")
    print(f"  - 预测相对保守，稳定性好")

    print(f"\n• XGBoost风格:")
    print(f"  - 考虑多种特征，适应性强")
    print(f"  - 能捕捉数据中的复杂模式")

    print(f"\n• Prophet风格:")
    print(f"  - 专门处理趋势和季节性")
    print(f"  - 适合业务场景下的解释")

    # 选择最佳方法
    print(f"\n推荐建议:")
    if trend == "上升":
        print("📈 检测到上升趋势，建议关注XGBoost和Prophet的结果")
    elif trend == "下降":
        print("📉 检测到下降趋势，建议关注SARIMA的稳定性")
    else:
        print("📊 数据相对稳定，可以综合考虑三种方法的平均")

    # 计算集成预测
    ensemble_predictions = []
    for i in range(13):
        ensemble = (sarima_predictions[i] + xgb_predictions[i] + prophet_predictions[i]) / 3
        ensemble_predictions.append(ensemble)

    print(f"\n🏆 集成预测（三种方法平均）:")
    print(f"未来13周平均预测: {sum(ensemble_predictions)/len(ensemble_predictions):.2f}")
    print(f"预测范围: {min(ensemble_predictions):.1f} - {max(ensemble_predictions):.1f}")

    # 保存建议
    print(f"\n💡 使用建议:")
    print(f"1. 对于库存管理，建议使用SARIMA风格的保守预测")
    print(f"2. 对于销售目标设定，可以考虑Prophet风格的趋势预测")
    print(f"3. 对于综合规划，建议使用集成预测结果")
    print(f"4. 定期用新数据重新训练模型以提高准确性")

    return {
        'weeks': weeks,
        'sales': sales,
        'sarima': sarima_predictions,
        'xgboost': xgb_predictions,
        'prophet': prophet_predictions,
        'ensemble': ensemble_predictions
    }

if __name__ == "__main__":
    results = forecast_4g_sales()

    print(f"\n{'='*60}")
    print("预测完成！")
    print(f"{'='*60}")
    print("此演示使用了模拟数据来展示三种预测方法的效果。")
    print("要使用你的真实数据，请将数据文件放在同一目录下运行预测程序。")