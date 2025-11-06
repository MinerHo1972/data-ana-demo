#!/usr/bin/env python3
"""
4G销售数据预测系统 - UI版本
使用tkinter创建用户界面，支持SARIMA和Prophet两种算法
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import seaborn as sns
from datetime import datetime, timedelta
import warnings
import threading
import os
import re

warnings.filterwarnings('ignore')

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

class ForecastApp:
    def __init__(self, root):
        self.root = root
        self.root.title("4G销售数据预测系统")
        self.root.geometry("1200x800")

        # 数据存储
        self.data = None
        self.processed_data = None
        self.forecast_results = None

        # 设置样式
        self.setup_styles()

        # 创建界面
        self.create_widgets()

    def setup_styles(self):
        """设置界面样式"""
        style = ttk.Style()
        style.theme_use('clam')

        # 配置样式
        style.configure('Title.TLabel', font=('Arial', 16, 'bold'))
        style.configure('Header.TLabel', font=('Arial', 12, 'bold'))
        style.configure('Success.TLabel', foreground='green')
        style.configure('Error.TLabel', foreground='red')

    def create_widgets(self):
        """创建主界面组件"""
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 配置行列权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)

        # 标题
        title_label = ttk.Label(main_frame, text="4G销售数据预测系统", style='Title.TLabel')
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))

        # 左侧控制面板
        control_frame = ttk.LabelFrame(main_frame, text="控制面板", padding="10")
        control_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))

        # 右侧结果面板
        result_frame = ttk.LabelFrame(main_frame, text="分析结果", padding="10")
        result_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 创建控制面板组件
        self.create_control_panel(control_frame)

        # 创建结果面板组件（包含多个标签页）
        self.create_result_panel(result_frame)

        # 状态栏
        self.status_var = tk.StringVar()
        self.status_var.set("就绪")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))

    def create_control_panel(self, parent):
        """创建控制面板"""
        # 文件导入部分
        file_frame = ttk.LabelFrame(parent, text="数据导入", padding="5")
        file_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(file_frame, text="选择数据文件:").pack(anchor=tk.W)

        file_button_frame = ttk.Frame(file_frame)
        file_button_frame.pack(fill=tk.X, pady=5)

        self.file_path_var = tk.StringVar()
        file_entry = ttk.Entry(file_button_frame, textvariable=self.file_path_var, width=30)
        file_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        browse_button = ttk.Button(file_button_frame, text="浏览", command=self.browse_file)
        browse_button.pack(side=tk.RIGHT, padx=(5, 0))

        load_button = ttk.Button(file_frame, text="加载数据", command=self.load_data)
        load_button.pack(fill=tk.X, pady=5)

        # 数据信息显示
        info_frame = ttk.LabelFrame(parent, text="数据信息", padding="5")
        info_frame.pack(fill=tk.X, pady=(0, 10))

        self.data_info_text = tk.Text(info_frame, height=6, width=40, wrap=tk.WORD)
        self.data_info_text.pack(fill=tk.BOTH, expand=True)

        # 预测设置部分
        forecast_frame = ttk.LabelFrame(parent, text="预测设置", padding="5")
        forecast_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(forecast_frame, text="预测周期数:").pack(anchor=tk.W)
        self.forecast_periods_var = tk.StringVar(value="13")
        periods_spinbox = ttk.Spinbox(forecast_frame, from_=1, to=52, textvariable=self.forecast_periods_var, width=10)
        periods_spinbox.pack(anchor=tk.W, pady=5)

        # 预测模式选择
        ttk.Label(forecast_frame, text="预测模式:").pack(anchor=tk.W, pady=(10, 5))

        self.forecast_only_var = tk.BooleanVar(value=False)
        forecast_only_check = ttk.Checkbutton(forecast_frame, text="仅预测模式（不进行模型评估）",
                                            variable=self.forecast_only_var)
        forecast_only_check.pack(anchor=tk.W, pady=5)

        # 算法选择
        ttk.Label(forecast_frame, text="选择预测算法:").pack(anchor=tk.W)

        self.algorithm_var = tk.StringVar()
        self.algorithm_var.set("both")

        ttk.Radiobutton(forecast_frame, text="SARIMA算法", variable=self.algorithm_var, value="sarima").pack(anchor=tk.W)
        ttk.Radiobutton(forecast_frame, text="Prophet算法", variable=self.algorithm_var, value="prophet").pack(anchor=tk.W)
        ttk.Radiobutton(forecast_frame, text="两种算法都使用", variable=self.algorithm_var, value="both").pack(anchor=tk.W)

        # 预测按钮
        predict_button = ttk.Button(forecast_frame, text="开始预测", command=self.start_prediction)
        predict_button.pack(fill=tk.X, pady=10)

        # 导出功能
        export_frame = ttk.LabelFrame(parent, text="数据导出", padding="5")
        export_frame.pack(fill=tk.X)

        export_csv_button = ttk.Button(export_frame, text="导出预测结果(CSV)", command=self.export_csv)
        export_csv_button.pack(fill=tk.X, pady=2)

        export_image_button = ttk.Button(export_frame, text="导出图表(PNG)", command=self.export_chart)
        export_image_button.pack(fill=tk.X, pady=2)

    def create_result_panel(self, parent):
        """创建结果显示面板"""
        # 创建Notebook用于多标签页
        self.notebook = ttk.Notebook(parent)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # 预测结果标签页
        self.create_forecast_tab()

        # 模型评估标签页
        self.create_evaluation_tab()

        # 数据可视化标签页
        self.create_visualization_tab()

        # 季节性分析标签页
        self.create_seasonality_tab()

        # 趋势性分析标签页
        self.create_trend_tab()

    def create_forecast_tab(self):
        """创建预测结果标签页"""
        self.result_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.result_frame, text="预测结果")

        # 创建表格
        columns = ('周期', 'SARIMA预测', 'Prophet预测', '实际值', '差异分析')
        self.result_tree = ttk.Treeview(self.result_frame, columns=columns, show='headings', height=15)

        # 设置列标题
        for col in columns:
            self.result_tree.heading(col, text=col)
            self.result_tree.column(col, width=120)

        # 添加滚动条
        result_scrollbar = ttk.Scrollbar(self.result_frame, orient=tk.VERTICAL, command=self.result_tree.yview)
        self.result_tree.configure(yscrollcommand=result_scrollbar.set)

        self.result_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        result_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def create_evaluation_tab(self):
        """创建模型评估标签页"""
        self.evaluation_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.evaluation_frame, text="模型评估")

        # 评估结果显示
        self.evaluation_text = tk.Text(self.evaluation_frame, height=15, width=60, wrap=tk.WORD)
        eval_scrollbar = ttk.Scrollbar(self.evaluation_frame, orient=tk.VERTICAL, command=self.evaluation_text.yview)
        self.evaluation_text.configure(yscrollcommand=eval_scrollbar.set)

        self.evaluation_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        eval_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def create_visualization_tab(self):
        """创建数据可视化标签页"""
        self.visualization_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.visualization_frame, text="数据可视化")

        # 创建matplotlib图形
        self.figure = Figure(figsize=(12, 8), dpi=80)
        self.canvas = FigureCanvasTkAgg(self.figure, self.visualization_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # 创建工具栏
        toolbar_frame = ttk.Frame(self.visualization_frame)
        toolbar_frame.pack(fill=tk.X)

        refresh_button = ttk.Button(toolbar_frame, text="刷新图表", command=self.update_charts)
        refresh_button.pack(side=tk.LEFT, padx=5)

    def create_seasonality_tab(self):
        """创建季节性分析标签页"""
        self.seasonality_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.seasonality_frame, text="季节性分析")

        # 创建季节性分析的图形
        self.seasonality_figure = Figure(figsize=(12, 8), dpi=80)
        self.seasonality_canvas = FigureCanvasTkAgg(self.seasonality_figure, self.seasonality_frame)
        self.seasonality_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # 工具栏
        seasonality_toolbar = ttk.Frame(self.seasonality_frame)
        seasonality_toolbar.pack(fill=tk.X)

        refresh_seasonality_button = ttk.Button(seasonality_toolbar, text="刷新季节性分析", command=self.update_seasonality_analysis)
        refresh_seasonality_button.pack(side=tk.LEFT, padx=5)

    def create_trend_tab(self):
        """创建趋势性分析标签页"""
        self.trend_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.trend_frame, text="趋势性分析")

        # 创建趋势性分析的图形
        self.trend_figure = Figure(figsize=(12, 8), dpi=80)
        self.trend_canvas = FigureCanvasTkAgg(self.trend_figure, self.trend_frame)
        self.trend_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # 工具栏
        trend_toolbar = ttk.Frame(self.trend_frame)
        trend_toolbar.pack(fill=tk.X)

        refresh_trend_button = ttk.Button(trend_toolbar, text="刷新趋势性分析", command=self.update_trend_analysis)
        refresh_trend_button.pack(side=tk.LEFT, padx=5)

    
    def browse_file(self):
        """浏览文件对话框"""
        filename = filedialog.askopenfilename(
            title="选择销售数据文件",
            filetypes=[
                ("Excel文件", "*.xlsx *.xls"),
                ("CSV文件", "*.csv"),
                ("所有文件", "*.*")
            ]
        )
        if filename:
            self.file_path_var.set(filename)

    def load_data(self):
        """加载并处理数据"""
        file_path = self.file_path_var.get()
        if not file_path:
            messagebox.showerror("错误", "请先选择数据文件")
            return

        try:
            self.status_var.set("正在加载数据...")
            self.root.update()

            # 读取数据
            if file_path.endswith('.csv'):
                self.data = pd.read_csv(file_path)
            else:
                self.data = pd.read_excel(file_path)

            # 处理数据
            self.process_data()

            # 更新数据信息显示
            self.update_data_info()

            self.status_var.set(f"数据加载成功 - {len(self.data)} 条记录")
            messagebox.showinfo("成功", f"数据加载成功！\n共 {len(self.data)} 条记录")

        except Exception as e:
            self.status_var.set("数据加载失败")
            messagebox.showerror("错误", f"数据加载失败:\n{str(e)}")

    def process_data(self):
        """处理数据格式"""
        if self.data is None:
            return

        df = self.data.copy()

        # 重命名列
        if df.shape[1] >= 2:
            df.columns = ['date', 'sales']

            # 处理日期格式
            def parse_date(date_str):
                if pd.isna(date_str):
                    return None

                try:
                    # 尝试直接解析
                    if isinstance(date_str, (datetime, pd.Timestamp)):
                        return date_str

                    date_str = str(date_str)

                    # 处理中文日期格式 "2021年第52周(周01月02日)"
                    year_match = re.search(r'(\d{4})年', date_str)
                    week_match = re.search(r'第(\d+)周', date_str)

                    if year_match and week_match:
                        year = int(year_match.group(1))
                        week = int(week_match.group(1))

                        start_date = datetime.strptime(f'{year}-01-01', '%Y-%m-%d')
                        days_to_monday = (0 - start_date.weekday()) % 7
                        first_monday = start_date + timedelta(days=days_to_monday)
                        target_date = first_monday + timedelta(weeks=week-1)
                        return target_date
                    else:
                        # 尝试其他日期格式
                        return pd.to_datetime(date_str)

                except:
                    return None

            # 应用日期解析
            parsed_dates = []
            for i, date_str in enumerate(df['date']):
                parsed_date = parse_date(date_str)
                if parsed_date:
                    parsed_dates.append(parsed_date)
                else:
                    if len(parsed_dates) > 0:
                        parsed_dates.append(parsed_dates[-1] + timedelta(weeks=1))
                    else:
                        parsed_dates.append(datetime(2021, 12, 26))

            df['date'] = parsed_dates
            df = df.sort_values('date').reset_index(drop=True)

        self.processed_data = df

    def update_data_info(self):
        """更新数据信息显示"""
        self.data_info_text.delete(1.0, tk.END)

        if self.processed_data is not None:
            info = f"""数据概览:
总记录数: {len(self.processed_data)}
时间范围: {self.processed_data['date'].min().strftime('%Y-%m-%d')} 至 {self.processed_data['date'].max().strftime('%Y-%m-%d')}
销售量范围: {self.processed_data['sales'].min():,} 至 {self.processed_data['sales'].max():,}
平均销售量: {self.processed_data['sales'].mean():,.0f}
标准差: {self.processed_data['sales'].std():,.0f}

数据列: {', '.join(self.processed_data.columns.tolist())}
"""
            self.data_info_text.insert(1.0, info)

            # 数据加载后自动更新季节性和趋势性分析
            try:
                self.update_seasonality_analysis()
                self.update_trend_analysis()
            except Exception as e:
                print(f"更新分析图表时出错: {e}")

    def start_prediction(self):
        """开始预测（在后台线程中运行）"""
        if self.processed_data is None:
            messagebox.showerror("错误", "请先加载数据")
            return

        # 在新线程中运行预测
        thread = threading.Thread(target=self.run_prediction)
        thread.daemon = True
        thread.start()

    def run_prediction(self):
        """运行预测算法"""
        try:
            self.status_var.set("正在运行预测...")
            self.root.update()

            forecast_periods = int(self.forecast_periods_var.get())
            algorithm = self.algorithm_var.get()
            forecast_only = self.forecast_only_var.get()

            # 准备数据
            data_length = len(self.processed_data)

            # 根据预测模式确定数据使用方式
            if forecast_only:
                # 仅预测模式：使用全部数据进行预测
                train_data = self.processed_data.copy()
                test_data = None
                evaluate_models = False
                self.status_var.set("仅预测模式：使用全部数据进行预测...")
            else:
                # 评估模式：分割数据进行训练和测试
                if data_length > forecast_periods + 10:
                    train_data = self.processed_data.iloc[:-forecast_periods].copy()
                    test_data = self.processed_data.iloc[-forecast_periods:].copy()
                    evaluate_models = True
                    self.status_var.set("评估模式：分割数据进行预测和评估...")
                else:
                    train_data = self.processed_data.copy()
                    test_data = None
                    evaluate_models = False
                    self.status_var.set("数据不足，使用全部数据预测...")

            self.root.update()

            results = {}
            evaluation_results = []

            # 运行选定的算法
            if algorithm in ['sarima', 'both']:
                self.status_var.set("运行SARIMA算法...")
                self.root.update()
                sarima_forecast = self.simple_sarima_forecast(train_data, forecast_periods)
                results['SARIMA'] = sarima_forecast

                if evaluate_models:
                    eval_result = self.evaluate_forecast(test_data['sales'].values, sarima_forecast, "SARIMA")
                    evaluation_results.append(eval_result)

            if algorithm in ['prophet', 'both']:
                self.status_var.set("运行Prophet算法...")
                self.root.update()
                prophet_forecast = self.simple_prophet_forecast(train_data, forecast_periods)
                results['Prophet'] = prophet_forecast

                if evaluate_models:
                    eval_result = self.evaluate_forecast(test_data['sales'].values, prophet_forecast, "Prophet")
                    evaluation_results.append(eval_result)

            # 存储结果
            self.forecast_results = {
                'periods': range(1, forecast_periods + 1),
                'forecasts': results,
                'actual': test_data['sales'].values if evaluate_models else None,
                'evaluation': evaluation_results
            }

            # 更新UI（在主线程中）
            self.root.after(0, self.update_results, evaluate_models)

        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("错误", f"预测失败:\n{str(e)}"))
            self.root.after(0, lambda: self.status_var.set("预测失败"))

    def simple_sarima_forecast(self, data, forecast_periods=13):
        """简化的SARIMA预测"""
        sales = data['sales'].values
        n = len(sales)

        # 计算趋势
        x = np.arange(n)
        trend_coef = np.polyfit(x, sales, 1)
        trend = trend_coef[0] * x + trend_coef[1]

        # 计算季节性
        seasonal_period = 52
        if n >= seasonal_period * 2:
            seasonal_pattern = np.zeros(seasonal_period)
            counts = np.zeros(seasonal_period)

            for i in range(n):
                week_in_year = i % seasonal_period
                seasonal_pattern[week_in_year] += sales[i] - trend[i]
                counts[week_in_year] += 1

            seasonal_pattern /= counts
        else:
            seasonal_pattern = np.zeros(min(52, n))
            for i in range(len(seasonal_pattern)):
                if i < n:
                    seasonal_pattern[i] = sales[i] - trend[i]

        # 生成预测
        forecast = []
        for i in range(forecast_periods):
            future_x = n + i
            future_trend = trend_coef[0] * future_x + trend_coef[1]
            future_seasonal = seasonal_pattern[i % len(seasonal_pattern)]
            forecast_value = future_trend + future_seasonal
            forecast.append(max(0, forecast_value))

        return forecast

    def simple_prophet_forecast(self, data, forecast_periods=13):
        """简化的Prophet预测"""
        sales = data['sales'].values
        n = len(sales)

        # 计算增长率
        if n > 1:
            growth_rate = (sales[-1] - sales[0]) / (n - 1)
        else:
            growth_rate = 0

        # 计算季节性因子
        seasonal_period = 52
        if n >= seasonal_period:
            seasonal_factors = np.zeros(seasonal_period)
            for i in range(seasonal_period):
                indices = list(range(i, n, seasonal_period))
                if len(indices) > 1:
                    avg_sales = np.mean([sales[idx] for idx in indices])
                    overall_avg = np.mean(sales)
                    seasonal_factors[i] = avg_sales / overall_avg
        else:
            seasonal_factors = np.ones(min(52, n))

        # 生成预测
        forecast = []
        base_value = sales[-1] if n > 0 else 0

        for i in range(forecast_periods):
            trend_component = base_value + growth_rate * (i + 1)
            seasonal_component = seasonal_factors[i % len(seasonal_factors)]
            forecast_value = trend_component * seasonal_component
            forecast.append(max(0, forecast_value))

        return forecast

    def evaluate_forecast(self, actual, predicted, model_name):
        """评估预测结果"""
        actual = np.array(actual)
        predicted = np.array(predicted)

        mae = np.mean(np.abs(actual - predicted))
        mse = np.mean((actual - predicted) ** 2)
        rmse = np.sqrt(mse)
        mape = np.mean(np.abs((actual - predicted) / actual)) * 100

        mean_actual = np.mean(actual)
        mae_percentage = (mae / mean_actual) * 100

        return {
            'model': model_name,
            'mae': mae,
            'mse': mse,
            'rmse': rmse,
            'mape': mape,
            'mae_percentage': mae_percentage
        }

    def update_results(self, evaluate_models=True):
        """更新结果显示"""
        if self.forecast_results is None:
            return

        forecast_only = self.forecast_only_var.get()

        # 清空结果表格
        for item in self.result_tree.get_children():
            self.result_tree.delete(item)

        # 添加预测结果
        periods = self.forecast_results['periods']
        forecasts = self.forecast_results['forecasts']
        actual = self.forecast_results['actual']

        for i, period in enumerate(periods):
            values = [period]

            if 'SARIMA' in forecasts:
                values.append(f"{forecasts['SARIMA'][i]:,.0f}")
            else:
                values.append("N/A")

            if 'Prophet' in forecasts:
                values.append(f"{forecasts['Prophet'][i]:,.0f}")
            else:
                values.append("N/A")

            if actual is not None and not forecast_only:
                values.append(f"{actual[i]:,.0f}")

                # 计算差异
                if 'SARIMA' in forecasts and 'Prophet' in forecasts:
                    sarima_diff = forecasts['SARIMA'][i] - actual[i]
                    prophet_diff = forecasts['Prophet'][i] - actual[i]
                    values.append(f"SARIMA:{sarima_diff:+,.0f}, Prophet:{prophet_diff:+,.0f}")
                elif 'SARIMA' in forecasts:
                    sarima_diff = forecasts['SARIMA'][i] - actual[i]
                    values.append(f"SARIMA:{sarima_diff:+,.0f}")
                elif 'Prophet' in forecasts:
                    prophet_diff = forecasts['Prophet'][i] - actual[i]
                    values.append(f"Prophet:{prophet_diff:+,.0f}")
            else:
                if forecast_only:
                    values.append("无对比数据")
                    values.append("仅预测模式")
                else:
                    values.append("N/A")
                    values.append("N/A")

            self.result_tree.insert('', tk.END, values=values)

        # 更新评估结果
        self.update_evaluation_results()

        # 更新所有图表
        try:
            self.update_charts()
            self.update_seasonality_analysis()
            self.update_trend_analysis()
        except Exception as e:
            print(f"更新图表时出错: {e}")

        self.status_var.set("预测完成")

    def update_evaluation_results(self):
        """更新评估结果显示"""
        self.evaluation_text.delete(1.0, tk.END)

        forecast_only = self.forecast_only_var.get()

        if forecast_only:
            # 仅预测模式
            text = "仅预测模式\n" + "="*50 + "\n\n"
            text += "当前运行模式：仅预测\n\n"
            text += "功能说明：\n"
            text += "• 使用全部历史数据进行预测\n"
            text += "• 不进行模型精度评估\n"
            text += "• 不与实际值进行对比\n\n"
            text += "适用场景：\n"
            text += "• 需要基于全部历史数据进行预测\n"
            text += "• 缺少足够的测试数据\n"
            text += "• 只关注预测结果，不需要模型评估\n\n"
            text += "如需模型评估，请取消勾选'仅预测模式'选项"

            self.evaluation_text.insert(1.0, text)
        elif self.forecast_results and self.forecast_results['evaluation']:
            # 评估模式且有评估结果
            results = self.forecast_results['evaluation']

            text = "模型评估结果\n" + "="*50 + "\n\n"

            for result in results:
                text += f"{result['model']} 模型:\n"
                text += f"  MAE (平均绝对误差): {result['mae']:,.2f}\n"
                text += f"  MAE百分比: {result['mae_percentage']:.2f}%\n"
                text += f"  MSE (均方误差): {result['mse']:,.2f}\n"
                text += f"  RMSE (均方根误差): {result['rmse']:,.2f}\n"
                text += f"  MAPE (平均绝对百分比误差): {result['mape']:.2f}%\n\n"

            # 如果有多个模型，添加对比
            if len(results) > 1:
                text += "模型对比:\n" + "-"*30 + "\n"

                best_mae_model = min(results, key=lambda x: x['mae'])
                best_mape_model = min(results, key=lambda x: x['mape'])

                text += f"最佳模型 (基于MAE): {best_mae_model['model']}\n"
                text += f"最佳模型 (基于MAPE): {best_mape_model['model']}\n"

            self.evaluation_text.insert(1.0, text)
        else:
            # 评估模式但没有足够数据
            text = "模型评估信息\n" + "="*50 + "\n\n"
            text += "当前运行模式：评估模式\n\n"
            text += "暂无评估结果\n\n"
            text += "可能原因：\n"
            text += "• 历史数据不足\n"
            text += "• 预测周期设置过大\n\n"
            text += "建议：\n"
            text += "• 减少预测周期数\n"
            text += "• 或选择'仅预测模式'\n"
            text += "• 或提供更多历史数据"

            self.evaluation_text.insert(1.0, text)

    def update_charts(self):
        """更新图表显示"""
        if self.forecast_results is None or self.processed_data is None:
            return

        self.figure.clear()

        # 创建子图
        ax1 = self.figure.add_subplot(121)
        ax2 = self.figure.add_subplot(122)

        forecast_only = self.forecast_only_var.get()
        periods = self.forecast_results['periods']
        forecasts = self.forecast_results['forecasts']
        actual = self.forecast_results['actual']

        # 图1: 预测对比
        if not forecast_only and actual is not None:
            # 评估模式：显示历史数据 + 预测 + 实际
            train_length = len(self.processed_data) - len(periods)
            train_dates = range(train_length)
            forecast_dates = range(train_length, train_length + len(periods))

            ax1.plot(train_dates, self.processed_data['sales'][:train_length],
                    label='历史数据', linewidth=2, color='blue')
            ax1.plot(forecast_dates, actual,
                    label='实际值', linewidth=2, color='green', marker='o')

            if 'SARIMA' in forecasts:
                ax1.plot(forecast_dates, forecasts['SARIMA'],
                        label='SARIMA预测', linewidth=2, color='red', marker='s')

            if 'Prophet' in forecasts:
                ax1.plot(forecast_dates, forecasts['Prophet'],
                        label='Prophet预测', linewidth=2, color='orange', marker='^')

            ax1.set_title('预测结果对比（评估模式）')
        else:
            # 仅预测模式或无实际数据：显示历史数据 + 预测
            historical_dates = range(len(self.processed_data))
            forecast_dates = range(len(self.processed_data), len(self.processed_data) + len(periods))

            ax1.plot(historical_dates, self.processed_data['sales'],
                    label='历史数据', linewidth=2, color='blue')

            if 'SARIMA' in forecasts:
                ax1.plot(forecast_dates, forecasts['SARIMA'],
                        label='SARIMA预测', linewidth=2, color='red', marker='s')

            if 'Prophet' in forecasts:
                ax1.plot(forecast_dates, forecasts['Prophet'],
                        label='Prophet预测', linewidth=2, color='orange', marker='^')

            ax1.set_title('预测结果展示（仅预测模式）')

        ax1.set_xlabel('周期')
        ax1.set_ylabel('销售量')
        ax1.legend()
        ax1.grid(True, alpha=0.3)

        # 图2: 算法对比
        if 'SARIMA' in forecasts and 'Prophet' in forecasts:
            ax2.plot(periods, forecasts['SARIMA'],
                    label='SARIMA', linewidth=2, marker='o')
            ax2.plot(periods, forecasts['Prophet'],
                    label='Prophet', linewidth=2, marker='s')

            if actual is not None:
                ax2.plot(periods, actual,
                        label='实际值', linewidth=3, color='black', marker='d')
        elif 'SARIMA' in forecasts:
            ax2.plot(periods, forecasts['SARIMA'],
                    label='SARIMA预测', linewidth=2, marker='o')
        elif 'Prophet' in forecasts:
            ax2.plot(periods, forecasts['Prophet'],
                    label='Prophet预测', linewidth=2, marker='o')

        ax2.set_title('算法预测对比')
        ax2.set_xlabel('预测周期')
        ax2.set_ylabel('预测销售量')
        ax2.legend()
        ax2.grid(True, alpha=0.3)

        self.figure.tight_layout()
        self.canvas.draw()

    def update_seasonality_analysis(self):
        """更新季节性分析图表"""
        if self.processed_data is None:
            messagebox.showwarning("提示", "请先加载数据")
            return

        self.seasonality_figure.clear()

        # 创建子图
        fig = self.seasonality_figure
        ax1 = fig.add_subplot(221)  # 月度模式
        ax2 = fig.add_subplot(222)  # 季度模式
        ax3 = fig.add_subplot(223)  # 周度模式
        ax4 = fig.add_subplot(224)  # 季节性强度

        data = self.processed_data.copy()
        sales = data['sales'].values
        dates = data['date']

        # 提取时间特征
        data['month'] = dates.dt.month
        data['quarter'] = dates.dt.quarter
        data['week_of_year'] = dates.dt.isocalendar().week
        data['day_of_week'] = dates.dt.dayofweek

        # 1. 月度季节性分析
        monthly_avg = data.groupby('month')['sales'].mean()
        monthly_std = data.groupby('month')['sales'].std()

        months = range(1, 13)
        month_names = ['1月', '2月', '3月', '4月', '5月', '6月',
                      '7月', '8月', '9月', '10月', '11月', '12月']

        ax1.bar(months, monthly_avg.reindex(months, fill_value=0),
                yerr=monthly_std.reindex(months, fill_value=0),
                capsize=5, alpha=0.7, color='skyblue')
        ax1.set_xlabel('月份')
        ax1.set_ylabel('平均销售量')
        ax1.set_title('月度季节性模式')
        ax1.set_xticks(months)
        ax1.set_xticklabels(month_names, rotation=45)
        ax1.grid(True, alpha=0.3)

        # 2. 季度季节性分析
        quarterly_avg = data.groupby('quarter')['sales'].mean()
        quarterly_std = data.groupby('quarter')['sales'].std()

        quarters = ['Q1', 'Q2', 'Q3', 'Q4']
        colors = ['lightcoral', 'lightgreen', 'lightsalmon', 'lightblue']

        bars = ax2.bar(quarters, quarterly_avg.reindex([1,2,3,4], fill_value=0),
                      yerr=quarterly_std.reindex([1,2,3,4], fill_value=0),
                      capsize=5, alpha=0.7, color=colors)
        ax2.set_xlabel('季度')
        ax2.set_ylabel('平均销售量')
        ax2.set_title('季度季节性模式')
        ax2.grid(True, alpha=0.3)

        # 添加数值标签
        for bar, avg in zip(bars, quarterly_avg):
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                    f'{avg:,.0f}', ha='center', va='bottom')

        # 3. 周度季节性分析（如果有足够数据）
        if len(data) > 52:
            weekly_avg = data.groupby('week_of_year')['sales'].mean()
            weeks = range(1, min(53, len(weekly_avg) + 1))

            ax3.plot(weeks, weekly_avg.reindex(weeks, fill_value=0),
                    marker='o', linewidth=2, markersize=4, color='orange')
            ax3.set_xlabel('周数')
            ax3.set_ylabel('平均销售量')
            ax3.set_title('周度季节性模式')
            ax3.grid(True, alpha=0.3)
            ax3.set_xlim(1, 52)
        else:
            # 如果数据不足，显示星期几的模式
            if data['day_of_week'].nunique() > 1:
                dow_avg = data.groupby('day_of_week')['sales'].mean()
                dow_names = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']

                ax3.bar(range(7), dow_avg.reindex(range(7), fill_value=0),
                        alpha=0.7, color='lightgreen')
                ax3.set_xlabel('星期')
                ax3.set_ylabel('平均销售量')
                ax3.set_title('星期几销售模式')
                ax3.set_xticks(range(7))
                ax3.set_xticklabels(dow_names)
                ax3.grid(True, alpha=0.3)

        # 4. 季节性强度分析
        # 计算季节性强度指标
        overall_mean = data['sales'].mean()
        overall_std = data['sales'].std()

        # 月度变异系数
        monthly_cv = monthly_avg.std() / monthly_avg.mean() if monthly_avg.mean() > 0 else 0

        # 季度变异系数
        quarterly_cv = quarterly_avg.std() / quarterly_avg.mean() if quarterly_avg.mean() > 0 else 0

        # 绘制季节性强度对比
        categories = ['整体变异', '月度变异', '季度变异']
        values = [overall_std/overall_mean if overall_mean > 0 else 0,
                 monthly_cv, quarterly_cv]
        colors = ['red', 'blue', 'green']

        bars = ax4.bar(categories, values, color=colors, alpha=0.7)
        ax4.set_ylabel('变异系数')
        ax4.set_title('季节性强度分析')
        ax4.set_ylim(0, max(values) * 1.2 if max(values) > 0 else 1)
        ax4.grid(True, alpha=0.3)

        # 添加数值标签
        for bar, value in zip(bars, values):
            height = bar.get_height()
            ax4.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                    f'{value:.3f}', ha='center', va='bottom')

        fig.tight_layout()
        self.seasonality_canvas.draw()

    def update_trend_analysis(self):
        """更新趋势性分析图表"""
        if self.processed_data is None:
            messagebox.showwarning("提示", "请先加载数据")
            return

        self.trend_figure.clear()

        # 创建子图
        fig = self.trend_figure
        ax1 = fig.add_subplot(221)  # 原始数据+趋势线
        ax2 = fig.add_subplot(222)  # 移动平均
        ax3 = fig.add_subplot(223)  # 增长率分析
        ax4 = fig.add_subplot(224)  # 趋势分解

        data = self.processed_data.copy()
        sales = data['sales'].values
        x = np.arange(len(sales))

        # 1. 原始数据和趋势线
        ax1.plot(x, sales, label='原始数据', alpha=0.7, color='blue', linewidth=1)

        # 线性趋势
        z = np.polyfit(x, sales, 1)
        p = np.poly1d(z)
        ax1.plot(x, p(x), "r--", label=f'线性趋势 (斜率: {z[0]:,.0f}/周)', linewidth=2)

        # 多项式趋势（3阶）
        z3 = np.polyfit(x, sales, 3)
        p3 = np.poly1d(z3)
        ax1.plot(x, p3(x), "g:", label='3阶多项式趋势', linewidth=2, alpha=0.8)

        ax1.set_xlabel('时间 (周)')
        ax1.set_ylabel('销售量')
        ax1.set_title('销售数据趋势分析')
        ax1.legend()
        ax1.grid(True, alpha=0.3)

        # 2. 移动平均分析
        window_sizes = [4, 8, 12]  # 4周、8周、12周移动平均

        for window in window_sizes:
            if len(sales) >= window:
                ma = np.convolve(sales, np.ones(window)/window, mode='valid')
                ma_x = np.arange(window-1, len(sales))
                ax2.plot(ma_x, ma, label=f'{window}周移动平均', linewidth=2, alpha=0.8)

        ax2.plot(x, sales, label='原始数据', alpha=0.3, color='gray', linewidth=1)
        ax2.set_xlabel('时间 (周)')
        ax2.set_ylabel('销售量')
        ax2.set_title('移动平均趋势分析')
        ax2.legend()
        ax2.grid(True, alpha=0.3)

        # 3. 增长率分析
        if len(sales) > 1:
            # 计算周增长率
            growth_rates = np.diff(sales) / sales[:-1] * 100

            # 绘制增长率
            ax3.plot(x[1:], growth_rates, label='周增长率', alpha=0.7, color='purple')
            ax3.axhline(y=0, color='black', linestyle='-', alpha=0.3)

            # 添加平均增长率线
            avg_growth = np.mean(growth_rates)
            ax3.axhline(y=avg_growth, color='red', linestyle='--',
                       label=f'平均增长率: {avg_growth:.2f}%', linewidth=2)

            ax3.set_xlabel('时间 (周)')
            ax3.set_ylabel('增长率 (%)')
            ax3.set_title('周增长率分析')
            ax3.legend()
            ax3.grid(True, alpha=0.3)

        # 4. 趋势分解 (简化版)
        # 计算趋势、季节性和残差
        if len(sales) >= 12:  # 至少需要12个数据点
            # 趋势（使用移动平均）
            trend_window = min(12, len(sales) // 4)
            trend = np.convolve(sales, np.ones(trend_window)/trend_window, mode='same')

            # 季节性（简化：减去趋势）
            seasonal = sales - trend
            if len(seasonal) >= 52:
                seasonal_pattern = np.zeros(52)
                for i in range(52):
                    indices = list(range(i, len(seasonal), 52))
                    if indices:
                        seasonal_pattern[i] = np.mean([seasonal[idx] for idx in indices])

                # 扩展季节性模式到整个数据长度
                extended_seasonal = np.tile(seasonal_pattern, len(seasonal) // 52 + 1)[:len(seasonal)]
            else:
                extended_seasonal = seasonal

            # 残差
            residual = sales - trend - extended_seasonal

            # 绘制分解结果
            ax4.plot(x, trend, label='趋势', linewidth=2, color='red')
            ax4.plot(x, extended_seasonal, label='季节性', linewidth=1, color='blue', alpha=0.7)
            ax4.plot(x, residual, label='残差', linewidth=1, color='green', alpha=0.7)
            ax4.plot(x, sales, label='原始数据', linewidth=1, color='black', alpha=0.5)

            ax4.set_xlabel('时间 (周)')
            ax4.set_ylabel('销售量')
            ax4.set_title('时间序列分解')
            ax4.legend()
            ax4.grid(True, alpha=0.3)

        fig.tight_layout()
        self.trend_canvas.draw()

    def export_csv(self):
        """导出预测结果为CSV"""
        if self.forecast_results is None:
            messagebox.showerror("错误", "没有预测结果可导出")
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV文件", "*.csv"), ("所有文件", "*.*")]
        )

        if filename:
            try:
                # 创建导出数据
                export_data = {
                    'Period': self.forecast_results['periods']
                }

                for algorithm, forecast in self.forecast_results['forecasts'].items():
                    export_data[f'{algorithm}_Forecast'] = forecast

                if self.forecast_results['actual'] is not None:
                    export_data['Actual'] = self.forecast_results['actual']

                df = pd.DataFrame(export_data)
                df.to_csv(filename, index=False)

                messagebox.showinfo("成功", f"预测结果已导出到:\n{filename}")

            except Exception as e:
                messagebox.showerror("错误", f"导出失败:\n{str(e)}")

    def export_chart(self):
        """导出图表为PNG"""
        if self.forecast_results is None:
            messagebox.showerror("错误", "没有图表可导出")
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG文件", "*.png"), ("所有文件", "*.*")]
        )

        if filename:
            try:
                self.figure.savefig(filename, dpi=300, bbox_inches='tight')
                messagebox.showinfo("成功", f"图表已导出到:\n{filename}")

            except Exception as e:
                messagebox.showerror("错误", f"导出失败:\n{str(e)}")

def main():
    """主函数"""
    root = tk.Tk()
    app = ForecastApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()