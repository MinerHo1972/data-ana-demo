#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
电商销售预测演示脚本
使用说明：
1. 确保安装了所需依赖：pip install -r requirements.txt
2. 运行此脚本：python run_forecast_demo.py
3. 查看生成的预测结果和可视化图表
"""

import sys
import os
import warnings
warnings.filterwarnings('ignore')

def check_dependencies():
    """检查依赖库是否安装"""
    required_packages = [
        'pandas', 'numpy', 'matplotlib', 'seaborn',
        'statsmodels', 'sklearn', 'xgboost'
    ]

    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)

    if missing_packages:
        print(f"缺少以下依赖包: {', '.join(missing_packages)}")
        print("请运行: pip install -r requirements.txt")
        return False

    # 检查Prophet（可选）
    try:
        import prophet
        print("✓ Prophet库已安装，将使用完整功能")
    except ImportError:
        print("⚠ Prophet库未安装，将使用简化版本")
        print("  安装方法: pip install prophet")

    return True

def run_demo():
    """运行预测演示"""
    print("="*60)
    print("电商销售预测系统演示")
    print("="*60)

    # 检查依赖
    if not check_dependencies():
        return

    try:
        # 导入并运行主程序
        from forecast_comparison import main

        print("\n开始运行预测系统...")
        print("这可能需要几分钟时间，请耐心等待...")
        print("-" * 60)

        # 运行完整的预测分析
        comparison = main()

        print("\n" + "="*60)
        print("演示完成！")
        print("="*60)
        print("\n生成的文件:")
        print("1. forecast_comparison_*.png - 各产品的预测对比图")
        print("2. method_performance_comparison.png - 方法性能对比图")
        print("3. forecast_summary_report.txt - 预测总结报告")
        print("\n建议:")
        print("• 查看生成的图表了解各方法的预测效果")
        print("• 阅读总结报告了解推荐使用的预测方法")
        print("• 可以根据自己的数据修改 sales_forecasting.py 中的 load_data 方法")

    except Exception as e:
        print(f"\n运行过程中出现错误: {str(e)}")
        print("\n可能的解决方案:")
        print("1. 检查是否安装了所有依赖包")
        print("2. 确保Python版本 >= 3.8")
        print("3. 如果是Windows系统，可能需要安装Visual C++ Redistributable")
        print("4. 如果内存不足，可以减少示例数据量")
        return

def show_usage():
    """显示使用说明"""
    print("""
电商销售预测系统使用说明
===================

功能特点：
- SARIMA时间序列预测：适合有明显季节性的数据
- XGBoost机器学习预测：适合特征丰富的复杂数据
- Prophet商业预测：适合快速部署和业务场景

快速开始：
1. python run_forecast_demo.py

使用自己的数据：
1. 准备Excel文件，包含三列：日期、商品名称、销售数量
2. 修改 sales_forecasting.py 中的 load_data 方法：
   data = pd.read_excel('你的文件.xlsx')
   data.columns = ['date', 'product', 'quantity']

高级用法：
- 修改 forecast_comparison.py 中的可视化设置
- 调整各预测器中的参数以获得更好效果
- 集成多种预测方法提高准确性

注意事项：
- 建议至少有6个月的历史数据
- 数据应按周统计或按天聚合
- 缺失值和异常值会影响预测准确性
""")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help']:
        show_usage()
    else:
        run_demo()