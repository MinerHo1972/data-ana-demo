#!/usr/bin/env python3
"""
4G销售数据预测系统启动脚本
简化启动方式，包含依赖检查
"""

import sys
import os

def check_dependencies():
    """检查必要的依赖库"""
    required_packages = [
        ('tkinter', 'tkinter'),
        ('pandas', 'pandas'),
        ('numpy', 'numpy'),
        ('matplotlib', 'matplotlib'),
        ('seaborn', 'seaborn'),
        ('openpyxl', 'openpyxl')
    ]

    missing_packages = []

    for package_name, import_name in required_packages:
        try:
            if import_name == 'tkinter':
                import tkinter
            else:
                __import__(import_name)
            print(f"✓ {package_name} 已安装")
        except ImportError:
            print(f"✗ {package_name} 未安装")
            missing_packages.append(package_name)

    if missing_packages:
        print(f"\n缺少以下依赖包: {', '.join(missing_packages)}")
        print("请使用以下命令安装:")
        print(f"pip install {' '.join(missing_packages)}")
        return False

    return True

def main():
    """主函数"""
    print("=" * 60)
    print("4G销售数据预测系统")
    print("=" * 60)

    # 检查依赖
    print("检查依赖包...")
    if not check_dependencies():
        input("\n按回车键退出...")
        return

    print("\n依赖检查完成！")
    print("正在启动预测系统...")

    try:
        # 导入并启动UI应用
        from forecast_ui import main as ui_main
        ui_main()

    except KeyboardInterrupt:
        print("\n程序被用户中断")
    except ImportError as e:
        print(f"\n导入错误: {e}")
        print("请确保 forecast_ui.py 文件在当前目录")
    except Exception as e:
        print(f"\n启动失败: {e}")

    input("\n按回车键退出...")

if __name__ == "__main__":
    main()