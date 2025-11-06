# 4G销售数据预测系统 v2.0

一个功能完整的图形化销售数据预测分析系统，集成了SARIMA和Prophet两种优秀的预测算法，提供**深度数据挖掘**和**规律性分析**功能。

## 🆕 v2.0 新功能

- ✨ **季节性规律拆分**: 自动识别月度、季度、周度季节性模式
- 📈 **趋势性规律拆分**: 多维度趋势分析，包含移动平均、增长率分析
- 🎨 **增强可视化**: 5个专业分析标签页，全面数据洞察
- 🤖 **智能分析**: 数据加载后自动展示规律性图表

## 🚀 快速开始

### 运行UI系统
```bash
# 推荐方式：使用启动脚本
python run_forecast_ui.py

# 或直接运行主程序
python forecast_ui.py
```

### 运行测试
```bash
# 测试UI系统功能
python test_ui.py

# 运行完整的预测分析
python complete_forecast_analysis.py
```

## 📁 项目文件结构

### 核心程序
- `forecast_ui.py` - 主要的UI界面程序
- `run_forecast_ui.py` - UI启动脚本
- `test_ui.py` - 功能测试脚本
- `complete_forecast_analysis.py` - 完整预测分析脚本

### 算法实现
- `sarima_forecast.py` - SARIMA算法实现
- `prophet_forecast.py` - Prophet算法实现
- `xgboost_forecast.py` - XGBoost算法实现
- `forecast_comparison.py` - 算法对比脚本

### 演示脚本
- `basic_forecast_demo.py` - 基础预测演示
- `simple_4g_forecast.py` - 简单4G预测
- `single_product_forecast.py` - 单产品预测
- `run_forecast_demo.py` - 预测演示运行器

### 数据文件
- `sales_4g_byweek.xlsx` - 销售数据
- `forecast_results.csv` - 预测结果
- `model_evaluation_results.csv` - 模型评估结果

### 文档说明
- `UI使用说明.md` - 详细使用手册
- `项目完成总结.md` - 项目总结文档
- `预测分析结果总结.md` - 分析结果总结
- `使用说明.md` - 基本使用说明

### 配置文件
- `requirements.txt` - Python依赖包列表
- `pyproject.toml` - 项目配置文件

## 🛠️ 环境要求

- Python 3.7+
- 依赖包：pandas, numpy, matplotlib, seaborn, openpyxl

安装依赖：
```bash
pip install -r requirements.txt
```

## 🎯 主要功能

### 预测分析
1. **数据导入** - 支持Excel和CSV文件，智能解析中文日期
2. **智能预测** - SARIMA和Prophet双算法，支持1-52周预测
3. **模型评估** - 完整的性能指标，自动推荐最佳算法

### 🆕 深度数据挖掘
4. **季节性分析** - 月度/季度/周度规律识别，季节性强度量化
5. **趋势性分析** - 多层次趋势分析，增长率计算，时间序列分解
6. **可视化展示** - 5个专业标签页，多维度数据洞察
7. **结果导出** - CSV和PNG格式导出，支持报告生成

### 智能特性
- 自动数据预处理和特征提取
- 数据加载后自动分析并展示规律
- 智能错误处理和用户提示
- 流畅的界面交互体验

### 🆕 预测模式选择
- **评估模式**：使用部分数据训练，部分数据测试评估
- **仅预测模式**：使用全部历史数据预测，不进行评估对比
- 智能模式切换，适应不同业务需求

## 📊 算法性能

- **Prophet算法**: 整体精度最佳
- **SARIMA算法**: 百分比精度优异
- **推荐使用**: 两种算法对比分析

## 📖 使用说明

详细使用说明请参考 `UI使用说明.md` 文件。

---

**版本**: 1.0
**更新日期**: 2025年11月6日