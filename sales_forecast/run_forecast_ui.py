#!/usr/bin/env python3
"""
4G销售数据预测系统启动脚本
"""

print("启动4G销售数据预测系统...")

try:
    from forecast_ui import main
    main()
except Exception as e:
    print(f"启动失败: {e}")
    input("按回车键退出...")