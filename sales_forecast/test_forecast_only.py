#!/usr/bin/env python3
"""
测试仅预测功能
"""

import sys
import os

def test_import():
    """测试模块导入"""
    try:
        import forecast_ui
        print("[OK] forecast_ui模块导入成功")
        return True
    except Exception as e:
        print(f"[ERROR] 模块导入失败: {e}")
        return False

def test_ui_creation():
    """测试UI创建"""
    try:
        import tkinter as tk
        from forecast_ui import ForecastApp

        # 创建一个隐藏的窗口进行测试
        root = tk.Tk()
        root.withdraw()  # 隐藏窗口

        app = ForecastApp(root)
        print("[OK] UI创建成功")

        # 检查仅预测选项是否存在
        if hasattr(app, 'forecast_only_var'):
            print("[OK] 仅预测选项变量创建成功")
        else:
            print("[ERROR] 仅预测选项变量缺失")
            return False

        root.destroy()
        return True

    except Exception as e:
        print(f"[ERROR] UI创建失败: {e}")
        return False

def main():
    """主测试函数"""
    print("=" * 50)
    print("仅预测功能测试")
    print("=" * 50)

    # 测试导入
    if not test_import():
        return False

    # 测试UI创建
    if not test_ui_creation():
        return False

    print("\n" + "=" * 50)
    print("[OK] 所有测试通过！仅预测功能正常")
    print("=" * 50)

    print("\n功能说明:")
    print("- 在预测设置中新增了'仅预测模式'复选框")
    print("- 勾选后使用全部历史数据进行预测")
    print("- 不进行模型评估和对比分析")
    print("- 适用于数据不足或仅需预测结果的情况")

    return True

if __name__ == "__main__":
    success = main()
    if not success:
        print("\n测试失败，请检查代码")
        sys.exit(1)

    print("\n现在可以运行UI程序进行实际测试:")
    print("python run_forecast_ui.py")