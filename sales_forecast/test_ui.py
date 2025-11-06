#!/usr/bin/env python3
"""
测试UI程序的主要功能
"""

import sys
import os

def test_imports():
    """测试必要的导入"""
    try:
        import tkinter as tk
        from tkinter import ttk, filedialog, messagebox
        print("[OK] tkinter 导入成功")
    except ImportError as e:
        print(f"[ERROR] tkinter 导入失败: {e}")
        return False

    try:
        import pandas as pd
        import numpy as np
        print("[OK] pandas 和 numpy 导入成功")
    except ImportError as e:
        print(f"[ERROR] pandas/numpy 导入失败: {e}")
        return False

    try:
        import matplotlib.pyplot as plt
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        print("[OK] matplotlib 导入成功")
    except ImportError as e:
        print(f"[ERROR] matplotlib 导入失败: {e}")
        return False

    try:
        import seaborn as sns
        print("[OK] seaborn 导入成功")
    except ImportError as e:
        print(f"[ERROR] seaborn 导入失败: {e}")
        return False

    return True

def test_data_loading():
    """测试数据加载功能"""
    try:
        # 检查测试数据文件
        test_file = 'sales_4g_byweek.xlsx'
        if not os.path.exists(test_file):
            print(f"[ERROR] 测试数据文件不存在: {test_file}")
            return False

        # 测试数据读取
        import pandas as pd
        df = pd.read_excel(test_file)
        print(f"[OK] 测试数据加载成功: {df.shape[0]} 行, {df.shape[1]} 列")
        return True

    except Exception as e:
        print(f"[ERROR] 数据加载测试失败: {e}")
        return False

def test_algorithms():
    """测试预测算法"""
    try:
        # 导入UI模块中的算法
        sys.path.append('.')
        from forecast_ui import ForecastApp

        # 创建临时应用实例来测试算法
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()  # 隐藏窗口

        app = ForecastApp(root)

        # 创建测试数据
        import pandas as pd
        import numpy as np
        from datetime import datetime, timedelta

        # 生成测试数据
        dates = [datetime(2022, 1, 1) + timedelta(weeks=i) for i in range(100)]
        sales = np.random.normal(500000, 100000, 100).astype(int)
        test_data = pd.DataFrame({'date': dates, 'sales': sales})

        app.processed_data = test_data

        # 测试SARIMA算法
        sarima_forecast = app.simple_sarima_forecast(test_data, 5)
        print(f"[OK] SARIMA算法测试成功: {len(sarima_forecast)} 个预测值")

        # 测试Prophet算法
        prophet_forecast = app.simple_prophet_forecast(test_data, 5)
        print(f"[OK] Prophet算法测试成功: {len(prophet_forecast)} 个预测值")

        root.destroy()
        return True

    except Exception as e:
        print(f"[ERROR] 算法测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("=" * 50)
    print("UI程序功能测试")
    print("=" * 50)

    # 测试导入
    print("\n1. 测试模块导入...")
    if not test_imports():
        print("导入测试失败，无法继续")
        return False

    # 测试数据加载
    print("\n2. 测试数据加载...")
    if not test_data_loading():
        print("数据加载测试失败，但可以继续")

    # 测试算法
    print("\n3. 测试预测算法...")
    if not test_algorithms():
        print("算法测试失败")
        return False

    print("\n" + "=" * 50)
    print("[OK] 所有测试通过！UI程序应该可以正常运行")
    print("=" * 50)

    print("\n启动UI程序...")
    print("注意：UI程序将在新窗口中打开")

    return True

if __name__ == "__main__":
    if main():
        try:
            # 尝试启动UI程序
            from forecast_ui import main as ui_main
            ui_main()
        except KeyboardInterrupt:
            print("\n程序被用户中断")
        except Exception as e:
            print(f"\nUI程序启动失败: {e}")
    else:
        print("\n测试失败，请检查错误信息")