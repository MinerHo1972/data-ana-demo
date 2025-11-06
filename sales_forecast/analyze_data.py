import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

def load_and_analyze_data():
    """读取并分析销售数据"""
    try:
        # 尝试使用openpyxl读取Excel文件
        df = pd.read_excel('sales_4g_byweek.xlsx', engine='openpyxl')
    except:
        try:
            # 尝试使用xlrd读取
            df = pd.read_excel('sales_4g_byweek.xlsx', engine='xlrd')
        except:
            # 如果都失败，尝试直接读取
            df = pd.read_excel('sales_4g_byweek.xlsx')

    print("=" * 50)
    print("销售数据分析报告")
    print("=" * 50)

    # 显示数据基本信息
    print(f"数据形状: {df.shape}")
    print(f"列名: {df.columns.tolist()}")
    print("\n前5行数据:")
    print(df.head())

    print("\n后5行数据:")
    print(df.tail())

    # 检查数据类型和缺失值
    print("\n数据信息:")
    df.info()

    print("\n缺失值统计:")
    print(df.isnull().sum())

    # 分析数据结构
    print("\n数据统计分析:")
    print(df.describe())

    return df

if __name__ == "__main__":
    df = load_and_analyze_data()

    # 保存数据以供后续使用
    df.to_csv('sales_data.csv', index=False)
    print(f"\n数据已保存到 sales_data.csv")
    print("数据分析完成！")