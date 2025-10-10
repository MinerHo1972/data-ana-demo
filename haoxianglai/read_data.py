import pandas as pd
import numpy as np

# 读取Excel文件
try:
    df = pd.read_excel('haoxianglai.xlsx')
    print("数据基本信息：")
    print(f"数据形状：{df.shape}")
    print(f"列名：{df.columns.tolist()}")
    print("\n前5行数据：")
    print(df.head())
    print("\n数据类型：")
    print(df.dtypes)
    print("\n数据统计信息：")
    print(df.describe(include='all'))
    print("\n缺失值情况：")
    print(df.isnull().sum())
except Exception as e:
    print(f"读取文件时出错：{e}")