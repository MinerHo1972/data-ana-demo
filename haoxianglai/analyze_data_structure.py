import pandas as pd
import numpy as np

# 读取Excel文件
df = pd.read_excel('haoxianglai.xlsx')

print("详细数据分析：")
print("=" * 50)

# 分析经营组织
print("\n1. 经营组织分布：")
print(df['经营组织'].value_counts())
print(f"共有 {df['经营组织'].nunique()} 个不同的经营组织")

# 分析省份分布
print("\n2. 省份分布：")
print(df['省份'].value_counts())
print(f"共有 {df['省份'].nunique()} 个不同的省份")

# 分析仓库分布
print("\n3. 经营仓库分布（前10个）：")
print(df['经营仓库'].value_counts().head(10))
print(f"共有 {df['经营仓库'].nunique()} 个不同的仓库")

# 分析时间范围
print("\n4. 订货时间范围：")
print(f"最早日期：{df['订货日期'].min()}")
print(f"最晚日期：{df['订货日期'].max()}")
print(f"时间跨度：{(df['订货日期'].max() - df['订货日期'].min()).days} 天")

# 分析订货数量
print("\n5. 订货数量统计：")
print(f"平均订货数量：{df['订货数量（件）'].mean():.2f}")
print(f"中位数订货数量：{df['订货数量（件）'].median():.2f}")
print(f"最小订货数量：{df['订货数量（件）'].min()}")
print(f"最大订货数量：{df['订货数量（件）'].max()}")

# 按省份和仓库分析订货频率
print("\n6. 各省份订货频率：")
province_freq = df.groupby('省份').size().sort_values(ascending=False)
print(province_freq)

print("\n7. 各仓库订货频率（前10个）：")
warehouse_freq = df.groupby('经营仓库').size().sort_values(ascending=False).head(10)
print(warehouse_freq)