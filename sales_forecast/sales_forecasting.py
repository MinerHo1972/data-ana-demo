import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

class SalesForecaster:
    def __init__(self):
        self.data = None
        self.processed_data = None

    def load_data(self, file_path=None):
        """加载数据或创建示例数据"""
        if file_path:
            # 从文件加载真实数据
            self.data = pd.read_excel(file_path)
            self.data.columns = ['date', 'product', 'quantity']
        else:
            # 创建示例数据
            self.create_sample_data()

        self.data['date'] = pd.to_datetime(self.data['date'])
        return self.data

    def create_sample_data(self):
        """创建示例电商销售数据"""
        np.random.seed(42)

        # 创建时间序列（104周 = 2年）
        start_date = datetime(2022, 1, 1)
        dates = []
        products = []
        quantities = []

        product_list = ['商品A', '商品B', '商品C', '商品D', '商品E']

        for week in range(104):
            current_date = start_date + timedelta(weeks=week)

            for product in product_list:
                dates.append(current_date)
                products.append(product)

                # 模拟不同的销售模式
                base_quantity = {
                    '商品A': 100 + 10 * np.sin(week * 2 * np.pi / 52),  # 季节性
                    '商品B': 80 + week * 0.5 + np.random.normal(0, 10),  # 趋势性
                    '商品C': 60 + 20 * np.random.random(),  # 随机性
                    '商品D': 120 + 15 * np.cos(week * 2 * np.pi / 26),  # 半年周期
                    '商品E': 90 + 5 * np.sin(week * 2 * np.pi / 13)    # 季度周期
                }[product]

                # 添加噪声和异常值
                noise = np.random.normal(0, base_quantity * 0.1)
                quantity = max(1, int(base_quantity + noise))

                # 偶尔添加促销效果
                if np.random.random() < 0.05:
                    quantity = int(quantity * (1.5 + np.random.random()))

                quantities.append(quantity)

        self.data = pd.DataFrame({
            'date': dates,
            'product': products,
            'quantity': quantities
        })

        print("示例数据已创建：")
        print(f"数据时间范围: {self.data['date'].min()} 至 {self.data['date'].max()}")
        print(f"商品数量: {self.data['product'].nunique()}")
        print(f"数据记录数: {len(self.data)}")

    def preprocess_data(self):
        """数据预处理"""
        # 按产品和周聚合数据
        self.processed_data = self.data.copy()
        self.processed_data['year_week'] = self.processed_data['date'].dt.isocalendar().week
        self.processed_data['year'] = self.processed_data['date'].dt.year

        # 创建时间特征
        self.processed_data['month'] = self.processed_data['date'].dt.month
        self.processed_data['quarter'] = self.processed_data['date'].dt.quarter
        self.processed_data['week_of_year'] = self.processed_data['date'].dt.isocalendar().week

        # 为每个产品创建滞后特征
        self.processed_data = self.processed_data.sort_values(['product', 'date'])

        for lag in [1, 2, 4, 8]:  # 1周、2周、1个月、2个月前的销售
            self.processed_data[f'lag_{lag}'] = self.processed_data.groupby('product')['quantity'].shift(lag)

        # 创建滚动平均特征
        for window in [2, 4, 8]:
            self.processed_data[f'rolling_mean_{window}'] = self.processed_data.groupby('product')['quantity'].transform(
                lambda x: x.rolling(window=window, min_periods=1).mean()
            )

        # 删除包含NaN的行（由于滞后特征导致）
        self.processed_data = self.processed_data.dropna()

        print("数据预处理完成")
        return self.processed_data

    def evaluate_predictions(self, y_true, y_pred, model_name):
        """评估预测结果"""
        from sklearn.metrics import mean_absolute_error, mean_squared_error

        mae = mean_absolute_error(y_true, y_pred)
        rmse = np.sqrt(mean_squared_error(y_true, y_pred))
        mape = np.mean(np.abs((y_true - y_pred) / y_true)) * 100
        wape = np.sum(np.abs(y_true - y_pred)) / np.sum(np.abs(y_true)) * 100

        print(f"\n{model_name} 模型评估结果:")
        print(f"MAE (平均绝对误差): {mae:.2f}")
        print(f"RMSE (均方根误差): {rmse:.2f}")
        print(f"MAPE (平均绝对百分比误差): {mape:.2f}%")
        print(f"WAPE (加权平均绝对百分比误差): {wape:.2f}%")

        return {
            'model': model_name,
            'mae': mae,
            'rmse': rmse,
            'mape': mape,
            'wape': wape
        }