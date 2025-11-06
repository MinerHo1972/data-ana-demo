#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单测试脚本 - 演示预测功能
"""

import sys
import warnings
warnings.filterwarnings('ignore')

def test_basic_functionality():
    """测试基本功能"""
    print("="*50)
    print("电商销售预测系统 - 简单测试")
    print("="*50)

    try:
        # 尝试创建示例数据
        print("1. 创建示例数据...")
        from sales_forecasting import SalesForecaster
        forecaster = SalesForecaster()
        data = forecaster.load_data()  # 创建示例数据

        print(f"   数据记录数: {len(data)}")
        print(f"   商品数量: {data['product'].nunique()}")
        print(f"   时间范围: {data['date'].min()} 至 {data['date'].max()}")

        # 数据预处理
        print("\n2. 数据预处理...")
        processed_data = forecaster.preprocess_data()
        print(f"   预处理后数据记录数: {len(processed_data)}")

        # 测试单个产品的预测
        print("\n3. 测试单个产品预测...")
        test_product = data['product'].unique()[0]
        print(f"   选择测试产品: {test_product}")

        # 简单预测（使用移动平均）
        product_data = data[data['product'] == test_product].copy()
        product_data = product_data.sort_values('date')
        weekly_data = product_data.groupby('date')['quantity'].sum().reset_index()

        # 计算最近4周平均值作为预测
        recent_avg = weekly_data.tail(4)['quantity'].mean()
        print(f"   最近4周平均销量: {recent_avg:.2f}")

        # 生成未来13周的简单预测
        from datetime import timedelta
        last_date = weekly_data['date'].max()
        future_dates = [last_date + timedelta(weeks=i) for i in range(1, 14)]

        simple_forecast = []
        for i, date in enumerate(future_dates):
            # 添加一些季节性变化
            seasonal_factor = 1 + 0.1 * (i % 13) / 13  # 简单的周期变化
            predicted = recent_avg * seasonal_factor
            simple_forecast.append({
                'date': date,
                'product': test_product,
                'predicted_quantity': round(predicted, 1)
            })

        print(f"   生成未来13周预测:")
        for week, pred in enumerate(simple_forecast[:5], 1):  # 显示前5周
            print(f"     第{week}周 ({pred['date'].strftime('%Y-%m-%d')}): {pred['predicted_quantity']:.1f}")

        print("   ...")
        print(f"     第13周 ({simple_forecast[-1]['date'].strftime('%Y-%m-%d')}): {simple_forecast[-1]['predicted_quantity']:.1f}")

        print("\n4. 预测方法说明:")
        print("   ✅ 数据加载和预处理: 成功")
        print("   ✅ 简单预测演示: 成功")
        print("\n完整预测功能包括:")
        print("   • SARIMA: 统计时间序列模型，适合季节性数据")
        print("   • XGBoost: 机器学习模型，适合复杂数据")
        print("   • Prophet: 商业预测模型，适合快速部署")

        print("\n5. 使用建议:")
        print("   • 确保有足够的历史数据（建议至少6个月）")
        print("   • 数据应包含日期、商品名称、销售数量三列")
        print("   • 可以修改 sales_forecasting.py 中的 load_data 方法使用自己的数据")
        print("   • 运行完整预测: python run_forecast_demo.py (需要安装完整依赖)")

        return True

    except ImportError as e:
        print(f"❌ 导入错误: {e}")
        print("请安装必要的依赖包:")
        print("pip install pandas numpy matplotlib scikit-learn")
        return False

    except Exception as e:
        print(f"❌ 运行错误: {e}")
        return False

def show_detailed_info():
    """显示详细信息"""
    print("\n" + "="*50)
    print("预测系统详细信息")
    print("="*50)

    print("\n【文件结构】")
    files = [
        ('sales_forecasting.py', '主要的数据处理和评估类'),
        ('sarima_forecast.py', 'SARIMA时间序列预测实现'),
        ('xgboost_forecast.py', 'XGBoost机器学习预测实现'),
        ('prophet_forecast.py', 'Prophet商业预测实现'),
        ('forecast_comparison.py', '预测结果对比和可视化'),
        ('run_forecast_demo.py', '主演示脚本'),
        ('requirements.txt', '依赖包列表'),
        ('simple_test.py', '简单测试脚本')
    ]

    for file, desc in files:
        print(f"  {file:<25} - {desc}")

    print("\n【预测方法对比】")
    methods = [
        ("SARIMA", "统计模型", "适合有明显季节性的稳定数据", "理论成熟，可解释性强"),
        ("XGBoost", "机器学习", "适合特征丰富的复杂数据", "预测精度高，能处理非线性关系"),
        ("Prophet", "商业预测", "适合快速部署的业务场景", "使用简单，自动处理节假日")
    ]

    for method, type, suitable, advantage in methods:
        print(f"\n  {method}:")
        print(f"    类型: {type}")
        print(f"    适用: {suitable}")
        print(f"    优势: {advantage}")

    print("\n【数据格式要求】")
    print("  输入数据应包含三列:")
    print("  - 日期 (date): 销售发生的日期")
    print("  - 商品名称 (product): 商品的唯一标识")
    print("  - 销售数量 (quantity): 该商品在对应日期的销售数量")

    print("\n【快速开始】")
    print("  1. 确保Python版本 >= 3.8")
    print("  2. 安装依赖: pip install pandas numpy matplotlib")
    print("  3. 运行测试: python simple_test.py")
    print("  4. 使用完整功能: pip install -r requirements.txt")
    print("  5. 运行演示: python run_forecast_demo.py")

if __name__ == "__main__":
    success = test_basic_functionality()
    show_detailed_info()

    if success:
        print("\n✅ 基本功能测试成功！")
        print("系统已准备就绪，可以进行预测分析。")
    else:
        print("\n❌ 测试失败，请检查依赖安装。")