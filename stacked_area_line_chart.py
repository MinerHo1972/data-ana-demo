#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
折线面积堆积图生成器
使用matplotlib和seaborn创建专业的折线面积堆积图
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import seaborn as sns
from datetime import datetime, timedelta
import random

# 设置中文字体支持
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

def set_style():
    """设置图表样式"""
    plt.style.use('seaborn-v0_8')
    sns.set_palette("husl")

def generate_sample_data():
    """生成示例数据"""
    # 创建时间序列
    dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='M')

    # 生成多个类别的数据
    categories = ['产品A', '产品B', '产品C', '产品D', '产品E']

    data = []
    for category in categories:
        # 为每个类别生成趋势数据
        base_value = random.randint(100, 500)
        trend = np.linspace(0, random.randint(-50, 100), len(dates))
        seasonal = 50 * np.sin(np.linspace(0, 2*np.pi, len(dates)))
        noise = np.random.normal(0, 20, len(dates))

        values = base_value + trend + seasonal + noise
        values = np.maximum(values, 0)  # 确保非负值

        for date, value in zip(dates, values):
            data.append({
                '日期': date,
                '类别': category,
                '数值': round(value, 2)
            })

    return pd.DataFrame(data)

def create_stacked_area_chart(df, title='折线面积堆积图', figsize=(12, 8)):
    """创建折线面积堆积图"""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=figsize, gridspec_kw={'height_ratios': [3, 1]})

    # 准备数据
    pivot_df = df.pivot(index='日期', columns='类别', values='数值').fillna(0)

    # 绘制堆积面积图
    pivot_df.plot(kind='area', stacked=True, alpha=0.7, ax=ax1)

    # 绘制折线图
    for column in pivot_df.columns:
        cumulative_values = pivot_df[column].values
        # 计算累积值用于绘制折线
        prev_columns = [col for col in pivot_df.columns if pivot_df.columns.get_loc(col) < pivot_df.columns.get_loc(column)]
        if prev_columns:
            cumulative_values += pivot_df[prev_columns].sum(axis=1).values

        ax1.plot(pivot_df.index, cumulative_values,
                marker='o', linewidth=2, markersize=4,
                label=f'{column} (累计)')

    # 设置第一个子图
    ax1.set_title(title, fontsize=16, fontweight='bold', pad=20)
    ax1.set_ylabel('数值', fontsize=12)
    ax1.grid(True, alpha=0.3)
    ax1.legend(loc='upper left', bbox_to_anchor=(1, 1))

    # 添加数据标签
    total_values = pivot_df.sum(axis=1)
    for i, (date, total) in enumerate(zip(pivot_df.index, total_values)):
        if i % max(1, len(pivot_df) // 10) == 0:  # 每10个点显示一个标签
            ax1.annotate(f'{total:.0f}',
                        (date, total),
                        textcoords="offset points",
                        xytext=(0,10),
                        ha='center',
                        fontsize=8)

    # 绘制百分比堆积图
    percentage_df = pivot_df.div(pivot_df.sum(axis=1), axis=0) * 100
    percentage_df.plot(kind='area', stacked=True, alpha=0.8, ax=ax2)

    ax2.set_title('百分比堆积图', fontsize=14)
    ax2.set_ylabel('百分比 (%)', fontsize=12)
    ax2.set_xlabel('日期', fontsize=12)
    ax2.grid(True, alpha=0.3)
    ax2.legend(loc='upper left', bbox_to_anchor=(1, 1))

    # 添加百分比标签
    for i, date in enumerate(percentage_df.index):
        if i % max(1, len(percentage_df) // 10) == 0:
            y_pos = 0
            for category in percentage_df.columns:
                percentage = percentage_df.loc[date, category]
                y_pos += percentage / 2  # 在每个区域的中间位置显示标签
                if percentage > 5:  # 只显示大于5%的标签
                    ax2.annotate(f'{percentage:.1f}%',
                               (date, y_pos),
                               textcoords="offset points",
                               xytext=(0,0),
                               ha='center',
                               fontsize=7,
                               color='white',
                               fontweight='bold')
                y_pos += percentage / 2

    plt.tight_layout()
    return fig

def add_statistics_info(fig, df):
    """添加统计信息"""
    # 计算统计信息
    total_by_category = df.groupby('类别')['数值'].sum()
    avg_by_category = df.groupby('类别')['数值'].mean()
    max_by_category = df.groupby('类别')['数值'].max()

    # 在图表底部添加统计信息
    stats_text = "统计信息:\n"
    for category in total_by_category.index:
        stats_text += f"{category}: 总计={total_by_category[category]:.0f}, "
        stats_text += f"平均={avg_by_category[category]:.0f}, "
        stats_text += f"最大={max_by_category[category]:.0f}\n"

    fig.text(0.02, 0.02, stats_text, fontsize=8,
            verticalalignment='bottom',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

def save_chart(fig, filename='stacked_area_line_chart', formats=['png', 'pdf']):
    """保存图表"""
    for fmt in formats:
        output_path = f'{filename}.{fmt}'
        fig.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f'图表已保存为: {output_path}')

def main():
    """主函数"""
    print("开始生成折线面积堆积图...")

    # 设置样式
    set_style()

    # 生成数据
    print("正在生成示例数据...")
    df = generate_sample_data()
    print(f"数据维度: {df.shape}")
    print("数据预览:")
    print(df.head())

    # 创建图表
    print("正在创建折线面积堆积图...")
    fig = create_stacked_area_chart(df, title='2024年产品销售数据堆积图')

    # 添加统计信息
    add_statistics_info(fig, df)

    # 保存图表
    save_chart(fig)

    # 显示图表
    plt.show()

    print("折线面积堆积图生成完成！")

def create_custom_chart(data_file=None, categories=None, title=None):
    """
    使用自定义数据创建图表

    Parameters:
    - data_file: 数据文件路径 (CSV格式)
    - categories: 要显示的类别列表
    - title: 图表标题
    """
    if data_file:
        try:
            df = pd.read_csv(data_file)
            if '日期' in df.columns:
                df['日期'] = pd.to_datetime(df['日期'])
        except Exception as e:
            print(f"读取数据文件失败: {e}")
            return None

    if categories:
        df = df[df['类别'].isin(categories)]

    if not title:
        title = f"折线面积堆积图 - {', '.join(categories) if categories else '所有类别'}"

    fig = create_stacked_area_chart(df, title=title)
    add_statistics_info(fig, df)
    save_chart(fig, filename='custom_stacked_chart')
    plt.show()

    return fig

if __name__ == "__main__":
    main()

    # 示例: 使用自定义数据
    # create_custom_chart(
    #     data_file='your_data.csv',
    #     categories=['产品A', '产品B', '产品C'],
    #     title='自定义产品销售分析'
    # )