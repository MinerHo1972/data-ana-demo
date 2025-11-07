# 折线面积堆积图生成器

这是一个专业的Python脚本，用于生成美观的折线面积堆积图。

## 功能特点

- 🎨 专业的图表样式和配色
- 📊 同时显示数值堆积图和百分比堆积图
- 📈 支持折线叠加显示
- 🏷️ 自动添加数据标签
- 📋 包含详细统计信息
- 💾 支持多种格式导出（PNG、PDF）
- 🎯 支持自定义数据导入

## 安装和使用

### 方法一：一键运行（推荐）

1. 双击运行 `run_chart.bat`
2. 脚本会自动检查并安装依赖
3. 生成示例图表

### 方法二：手动安装

1. 安装依赖：
   ```batch
   install_requirements.bat
   ```

2. 运行脚本：
   ```python
   python stacked_area_line_chart.py
   ```

## 脚本说明

### 主要文件

- `stacked_area_line_chart.py` - 主脚本文件
- `install_requirements.bat` - 依赖安装脚本
- `run_chart.bat` - 一键运行脚本
- `sample_data.csv` - 示例数据文件
- `README_chart.md` - 使用说明

### 主函数

```python
def main():
    """主函数 - 生成示例数据的堆积图"""
```

### 自定义数据

```python
def create_custom_chart(data_file=None, categories=None, title=None):
    """
    使用自定义数据创建图表

    参数:
    - data_file: CSV数据文件路径
    - categories: 要显示的类别列表
    - title: 图表标题
    """
```

## 数据格式要求

CSV文件应包含以下列：
- `日期`: 时间序列数据
- `类别`: 数据分类
- `数值`: 数值数据

示例：
```csv
日期,类别,数值
2024-01-01,产品A,150
2024-01-01,产品B,200
2024-01-01,产品C,100
```

## 自定义使用示例

```python
# 使用自定义数据
create_custom_chart(
    data_file='your_data.csv',
    categories=['产品A', '产品B', '产品C'],
    title='自定义产品销售分析'
)

# 使用示例数据
create_custom_chart(
    data_file='sample_data.csv',
    title='示例数据分析'
)
```

## 输出文件

脚本会在当前目录生成：
- `stacked_area_line_chart.png` - PNG格式图表
- `stacked_area_line_chart.pdf` - PDF格式图表

## 依赖包

- numpy - 数值计算
- pandas - 数据处理
- matplotlib - 图表绘制
- seaborn - 图表样式

## 注意事项

1. 确保系统已安装Python 3.6+
2. 首次运行会自动安装依赖包
3. 支持中文显示（自动检测系统字体）
4. 数据值必须为非负数

## 故障排除

如果遇到中文字体显示问题：
1. 确保系统安装了中文字体
2. 可以修改代码中的字体设置
3. 在代码中添加其他可用的中文字体

## 技术支持

如需帮助或报告问题，请检查：
1. Python版本是否兼容
2. 依赖包是否正确安装
3. 数据格式是否符合要求