import pandas as pd
import numpy as np

# 读取Excel文件
df = pd.read_excel('haoxianglai.xlsx')

print("详细数据分析：")
print("=" * 50)

# 获取列名
print("数据列名：")
print(df.columns.tolist())
print()

# 分析经营组织
print("\n1. 经营组织分布：")
print(df[df.columns[0]].value_counts())
print(f"共有 {df[df.columns[0]].nunique()} 个不同的经营组织")

# 分析省份分布
print("\n2. 省份分布：")
print(df[df.columns[1]].value_counts())
print(f"共有 {df[df.columns[1]].nunique()} 个不同的省份")

# 分析仓库分布
print("\n3. 经营仓库分布（前10个）：")
print(df[df.columns[2]].value_counts().head(10))
print(f"共有 {df[df.columns[2]].nunique()} 个不同的仓库")

# 分析时间范围
print("\n4. 订货时间范围：")
print(f"最早日期：{df[df.columns[4]].min()}")
print(f"最晚日期：{df[df.columns[4]].max()}")
print(f"时间跨度：{(df[df.columns[4]].max() - df[df.columns[4]].min()).days} 天")

# 分析订货数量
print("\n5. 订货数量统计：")
print(f"平均订货数量：{df[df.columns[3]].mean():.2f}")
print(f"中位数订货数量：{df[df.columns[3]].median():.2f}")
print(f"最小订货数量：{df[df.columns[3]].min()}")
print(f"最大订货数量：{df[df.columns[3]].max()}")

# 按省份和仓库分析订货频率
print("\n6. 各省份订货频率：")
province_freq = df.groupby(df.columns[1]).size().sort_values(ascending=False)
print(province_freq)

print("\n7. 各仓库订货频率（前10个）：")
warehouse_freq = df.groupby(df.columns[2]).size().sort_values(ascending=False).head(10)
print(warehouse_freq)