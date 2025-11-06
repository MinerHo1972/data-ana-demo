#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基础电商销售预测演示 - 不依赖外部库
演示三种预测方法的核心逻辑
"""

import random
from datetime import datetime, timedelta

def create_sample_data():
    """创建示例销售数据"""
    print("创建示例电商销售数据...")

    # 产品列表
    products = ['商品A', '商品B', '商品C', '商品D', '商品E']

    # 生成104周（2年）的数据
    data = []
    start_date = datetime(2022, 1, 1)

    for week in range(104):
        current_date = start_date + timedelta(weeks=week)

        for product in products:
            # 模拟不同的销售模式
            if product == '商品A':
                # 季节性模式
                base_quantity = 100 + 20 * (week % 52) / 52
            elif product == '商品B':
                # 上升趋势
                base_quantity = 50 + week * 0.5
            elif product == '商品C':
                # 稳定销售
                base_quantity = 80
            elif product == '商品D':
                # 周期性波动
                base_quantity = 90 + 30 * (week % 13) / 13
            else:  # 商品E
                # 随机波动
                base_quantity = 70 + random.uniform(-10, 10)

            # 添加随机噪声
            noise = random.uniform(-10, 10)
            quantity = max(10, int(base_quantity + noise))

            data.append({
                'date': current_date.strftime('%Y-%m-%d'),
                'product': product,
                'quantity': quantity
            })

    print(f"生成 {len(data)} 条记录")
    print(f"时间范围: {data[0]['date']} 至 {data[-1]['date']}")
    print(f"产品数量: {len(products)}")

    return data

def simple_moving_average_forecast(data, product_name, window=4):
    """简单移动平均预测"""
    print(f"\n=== 简单移动平均预测 - {product_name} ===")

    # 获取特定产品的数据
    product_data = [item for item in data if item['product'] == product_name]
    product_data.sort(key=lambda x: x['date'])

    # 提取销量数据
    quantities = [item['quantity'] for item in product_data]

    if len(quantities) < window:
        print(f"数据不足（{len(quantities)} < {window}），使用全部数据平均")
        avg_quantity = sum(quantities) / len(quantities)
    else:
        # 计算最近window周的平均值
        recent_quantities = quantities[-window:]
        avg_quantity = sum(recent_quantities) / len(recent_quantities)
        print(f"最近{window}周销量: {recent_quantities}")

    print(f"平均销量: {avg_quantity:.2f}")

    # 预测未来13周
    forecast = []
    last_date = datetime.strptime(product_data[-1]['date'], '%Y-%m-%d')

    for week in range(1, 14):
        future_date = last_date + timedelta(weeks=week)

        # 添加简单的季节性调整
        seasonal_factor = 1 + 0.1 * (week % 13) / 13
        predicted_quantity = avg_quantity * seasonal_factor

        forecast.append({
            'date': future_date.strftime('%Y-%m-%d'),
            'product': product_name,
            'method': '移动平均',
            'predicted_quantity': round(predicted_quantity, 1)
        })

    print(f"预测未来13周平均销量: {sum([f['predicted_quantity'] for f in forecast]) / len(forecast):.2f}")

    return forecast

def weighted_average_forecast(data, product_name):
    """加权平均预测（给近期数据更高权重）"""
    print(f"\n=== 加权平均预测 - {product_name} ===")

    # 获取特定产品的数据
    product_data = [item for item in data if item['product'] == product_name]
    product_data.sort(key=lambda x: x['date'])

    # 提取销量数据
    quantities = [item['quantity'] for item in product_data]

    if len(quantities) < 4:
        return simple_moving_average_forecast(data, product_name)

    # 计算加权平均（最近的数据权重更高）
    weights = list(range(1, len(quantities) + 1))  # 权重递增
    weighted_sum = sum(q * w for q, w in zip(quantities, weights))
    total_weight = sum(weights)
    weighted_avg = weighted_sum / total_weight

    print(f"最近销量: {quantities[-4:]}")
    print(f"加权平均销量: {weighted_avg:.2f}")

    # 预测未来13周
    forecast = []
    last_date = datetime.strptime(product_data[-1]['date'], '%Y-%m-%d')

    for week in range(1, 14):
        future_date = last_date + timedelta(weeks=week)

        # 添加趋势调整
        trend_factor = 1 + (week - 1) * 0.02  # 每周增长2%
        predicted_quantity = weighted_avg * trend_factor

        forecast.append({
            'date': future_date.strftime('%Y-%m-%d'),
            'product': product_name,
            'method': '加权平均',
            'predicted_quantity': round(predicted_quantity, 1)
        })

    print(f"预测未来13周平均销量: {sum([f['predicted_quantity'] for f in forecast]) / len(forecast):.2f}")

    return forecast

def seasonal_trend_forecast(data, product_name):
    """季节趋势预测"""
    print(f"\n=== 季节趋势预测 - {product_name} ===")

    # 获取特定产品的数据
    product_data = [item for item in data if item['product'] == product_name]
    product_data.sort(key=lambda x: x['date'])

    # 提取销量数据
    quantities = [item['quantity'] for item in product_data]

    if len(quantities) < 8:
        return weighted_average_forecast(data, product_name)

    # 计算趋势（简单线性趋势）
    n = len(quantities)
    x_sum = sum(range(n))
    y_sum = sum(quantities)
    xy_sum = sum(i * q for i, q in enumerate(quantities))
    x2_sum = sum(i * i for i in range(n))

    # 计算线性回归参数 y = ax + b
    a = (n * xy_sum - x_sum * y_sum) / (n * x2_sum - x_sum * x_sum)
    b = (y_sum - a * x_sum) / n

    print(f"趋势参数: 斜率={a:.3f}, 截距={b:.2f}")
    print(f"趋势解读: {'上升' if a > 0 else '下降'}趋势")

    # 计算季节性模式（简化版，假设13周一个周期）
    seasonal_pattern = []
    for week in range(13):
        week_quantities = [quantities[i] for i in range(week, len(quantities), 13)]
        if week_quantities:
            seasonal_pattern.append(sum(week_quantities) / len(week_quantities))
        else:
            seasonal_pattern.append(0)

    # 归一化季节性因子
    avg_seasonal = sum(seasonal_pattern) / len(seasonal_pattern) if seasonal_pattern else 1
    seasonal_factors = [s / avg_seasonal if avg_seasonal > 0 else 1 for s in seasonal_pattern]

    print(f"季节性因子范围: {min(seasonal_factors):.2f} - {max(seasonal_factors):.2f}")

    # 预测未来13周
    forecast = []
    last_date = datetime.strptime(product_data[-1]['date'], '%Y-%m-%d')

    for week in range(1, 14):
        future_date = last_date + timedelta(weeks=week)

        # 趋势预测
        trend_value = a * (n + week - 1) + b

        # 应用季节性调整
        seasonal_index = (week - 1) % 13
        seasonal_factor = seasonal_factors[seasonal_index] if seasonal_factors else 1

        predicted_quantity = trend_value * seasonal_factor
        predicted_quantity = max(10, predicted_quantity)  # 确保最小销量

        forecast.append({
            'date': future_date.strftime('%Y-%m-%d'),
            'product': product_name,
            'method': '季节趋势',
            'predicted_quantity': round(predicted_quantity, 1)
        })

    print(f"预测未来13周平均销量: {sum([f['predicted_quantity'] for f in forecast]) / len(forecast):.2f}")

    return forecast

def compare_methods(data, product_name):
    """比较三种预测方法"""
    print(f"\n{'='*60}")
    print(f"预测方法对比分析 - {product_name}")
    print(f"{'='*60}")

    # 运行三种预测方法
    forecasts = {}

    # 1. 移动平均预测
    forecasts['移动平均'] = simple_moving_average_forecast(data, product_name)

    # 2. 加权平均预测
    forecasts['加权平均'] = weighted_average_forecast(data, product_name)

    # 3. 季节趋势预测
    forecasts['季节趋势'] = seasonal_trend_forecast(data, product_name)

    # 比较结果
    print(f"\n预测结果对比:")
    print(f"{'方法':<10} {'第1周':<8} {'第4周':<8} {'第8周':<8} {'第13周':<8} {'平均':<8}")
    print(f"{'-'*60}")

    for method, forecast in forecasts.items():
        week1 = forecast[0]['predicted_quantity']
        week4 = forecast[3]['predicted_quantity']
        week8 = forecast[7]['predicted_quantity']
        week13 = forecast[12]['predicted_quantity']
        avg = sum([f['predicted_quantity'] for f in forecast]) / len(forecast)

        print(f"{method:<10} {week1:<8.1f} {week4:<8.1f} {week8:<8.1f} {week13:<8.1f} {avg:<8.1f}")

    # 方法推荐
    print(f"\n方法特点:")
    print(f"• 移动平均: 简单稳定，适合销售波动小的商品")
    print(f"• 加权平均: 考虑趋势变化，适合有增长趋势的商品")
    print(f"• 季节趋势: 考虑季节性，适合有明显周期性的商品")

    return forecasts

def generate_summary_report(data, all_forecasts):
    """生成总结报告"""
    print(f"\n{'='*60}")
    print("预测总结报告")
    print(f"{'='*60}")

    print(f"\n数据概况:")
    print(f"• 总记录数: {len(data)}")
    print(f"• 产品数量: {len(set(item['product'] for item in data))}")
    print(f"• 时间跨度: {data[0]['date']} 至 {data[-1]['date']}")

    print(f"\n预测方法说明:")
    print(f"1. 移动平均预测 (类似于简化的SARIMA):")
    print(f"   - 基于历史数据的平均值进行预测")
    print(f"   - 适合数据稳定的商品")
    print(f"   - 优点: 简单稳定，不易受异常值影响")

    print(f"\n2. 加权平均预测 (类似于简化的XGBoost):")
    print(f"   - 给近期数据更高的权重")
    print(f"   - 考虑数据的趋势变化")
    print(f"   - 优点: 能捕捉趋势变化")

    print(f"\n3. 季节趋势预测 (类似于简化的Prophet):")
    print(f"   - 结合趋势分析和季节性调整")
    print(f"   - 适合有明显季节性的商品")
    print(f"   - 优点: 能处理周期性变化")

    print(f"\n使用建议:")
    print(f"• 对于销量稳定的商品，推荐使用移动平均方法")
    print(f"• 对于有增长趋势的商品，推荐使用加权平均方法")
    print(f"• 对于有季节性的商品，推荐使用季节趋势方法")
    print(f"• 可以结合多种方法的结果，进行集成预测")

    # 实际应用建议
    print(f"\n实际应用建议:")
    print(f"1. 数据准备:")
    print(f"   - 确保数据质量，处理异常值")
    print(f"   - 建议至少有6个月的历史数据")
    print(f"   - 数据应包含日期、商品、销售数量")

    print(f"\n2. 模型选择:")
    print(f"   - 根据商品特点选择合适的预测方法")
    print(f"   - 可以使用多种方法进行交叉验证")
    print(f"   - 定期重新训练模型以适应变化")

    print(f"\n3. 结果应用:")
    print(f"   - 结合业务知识解释预测结果")
    print(f"   - 考虑促销、节假日等特殊因素")
    print(f"   - 建立预测准确率监控机制")

def main():
    """主演示函数"""
    print("电商销售预测系统演示")
    print("=" * 50)

    # 1. 创建示例数据
    data = create_sample_data()

    # 2. 选择一个产品进行详细预测
    product_name = '商品A'

    # 3. 比较三种预测方法
    forecasts = compare_methods(data, product_name)

    # 4. 快速展示其他产品的预测
    print(f"\n{'='*60}")
    print("其他产品快速预测")
    print(f"{'='*60}")

    other_products = ['商品B', '商品C', '商品D', '商品E']
    for product in other_products:
        print(f"\n{product} - 使用移动平均方法:")
        forecast = simple_moving_average_forecast(data, product)
        avg_prediction = sum([f['predicted_quantity'] for f in forecast]) / len(forecast)
        print(f"未来13周平均预测: {avg_prediction:.1f}")

    # 5. 生成总结报告
    generate_summary_report(data, forecasts)

    print(f"\n{'='*60}")
    print("演示完成！")
    print(f"{'='*60}")

    print(f"\n完整系统功能:")
    print(f"• SARIMA: 统计时间序列预测模型")
    print(f"• XGBoost: 机器学习预测模型")
    print(f"• Prophet: 商业预测模型")
    print(f"• 可视化和对比分析")
    print(f"• 性能评估和报告生成")

    print(f"\n如需使用完整功能，请:")
    print(f"1. 安装依赖: pip install pandas numpy matplotlib scikit-learn xgboost")
    print(f"2. 运行完整演示: python run_forecast_demo.py")

if __name__ == "__main__":
    main()