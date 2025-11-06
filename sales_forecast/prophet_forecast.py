import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

try:
    from prophet import Prophet
    from prophet.diagnostics import cross_validation, performance_metrics
    PROPHET_AVAILABLE = True
except ImportError:
    PROPHET_AVAILABLE = False
    print("Prophet库未安装，将使用简化版本")

class ProphetForecaster:
    def __init__(self):
        self.models = {}
        self.forecasts = {}
        self.evaluations = {}

    def prepare_prophet_data(self, data, product_name):
        """准备Prophet格式数据"""
        product_data = data[data['product'] == product_name].copy()

        # 按周聚合数据
        weekly_data = product_data.groupby('date')['quantity'].sum().reset_index()
        weekly_data = weekly_data.sort_values('date')

        # Prophet要求的列名
        prophet_data = weekly_data.rename(columns={
            'date': 'ds',
            'quantity': 'y'
        })

        return prophet_data

    def add_custom_features(self, prophet_data, product_name):
        """添加自定义特征"""
        df = prophet_data.copy()

        # 添加季节性特征
        df['month'] = df['ds'].dt.month
        df['quarter'] = df['ds'].dt.quarter
        df['week_of_year'] = df['ds'].dt.isocalendar().week

        # 添加节假日特征（简化版）
        df['is_holiday_season'] = ((df['month'].isin([11, 12])) | (df['month'] == 1)).astype(int)
        df['is_summer'] = df['month'].isin([6, 7, 8]).astype(int)
        df['is_year_end'] = (df['month'] == 12).astype(int)

        return df

    def train_prophet_model(self, data, product_name):
        """训练Prophet模型"""
        print(f"\n=== 开始训练 {product_name} 的Prophet模型 ===")

        if not PROPHET_AVAILABLE:
            print("Prophet库不可用，使用简化时间序列方法")
            return self.train_simple_model(data, product_name)

        # 准备数据
        prophet_data = self.prepare_prophet_data(data, product_name)

        if len(prophet_data) < 8:
            print(f"产品 {product_name} 数据量不足，跳过训练")
            return None

        print(f"训练数据点数量: {len(prophet_data)}")
        print(f"数据时间范围: {prophet_data['ds'].min()} 至 {prophet_data['ds'].max()}")
        print(f"平均销量: {prophet_data['y'].mean():.2f}")
        print(f"销量标准差: {prophet_data['y'].std():.2f}")

        # 添加额外特征
        enhanced_data = self.add_custom_features(prophet_data, product_name)

        try:
            # 创建Prophet模型，根据数据量调整参数
            if len(prophet_data) < 26:  # 少于半年数据
                # 使用更简单的参数
                model = Prophet(
                    yearly_seasonality=True,
                    weekly_seasonality=False,  # 周度数据不需要周季节性
                    daily_seasonality=False,
                    changepoint_prior_scale=0.1,  # 较小的变化点先验
                    seasonality_prior_scale=5.0,  # 较大的季节性先验
                    holidays_prior_scale=5.0,
                    mcmc_samples=0,  # 不使用MCMC以加快速度
                    interval_width=0.8,
                    uncertainty_samples=1000
                )
            else:
                # 使用默认参数
                model = Prophet(
                    yearly_seasonality=True,
                    weekly_seasonality=False,
                    daily_seasonality=False,
                    changepoint_prior_scale=0.05,
                    seasonality_prior_scale=10.0,
                    holidays_prior_scale=10.0,
                    mcmc_samples=0,
                    interval_width=0.8,
                    uncertainty_samples=1000
                )

            # 添加自定义季节性
            if len(prophet_data) >= 52:  # 有足够数据时添加季度季节性
                model.add_seasonality(
                    name='quarterly',
                    period=91.25,  # 季度天数
                    fourier_order=5
                )

            # 添加额外的回归变量
            model.add_regressor('is_holiday_season')
            model.add_regressor('is_summer')

            # 准备训练数据
            train_data = enhanced_data[['ds', 'y', 'is_holiday_season', 'is_summer']]

            # 训练模型
            print("正在训练Prophet模型...")
            model.fit(train_data)

            print("Prophet模型训练完成")

            # 保存模型
            self.models[product_name] = model

            return model

        except Exception as e:
            print(f"Prophet模型训练失败: {str(e)}")
            return self.train_simple_model(data, product_name)

    def train_simple_model(self, data, product_name):
        """简化的时间序列模型作为备选"""
        print(f"使用简化模型处理 {product_name}")

        product_data = data[data['product'] == product_name].copy()
        weekly_data = product_data.groupby('date')['quantity'].sum().reset_index()
        weekly_data = weekly_data.sort_values('date')

        # 创建简单的 Prophet 风格的模型
        class SimpleProphetModel:
            def __init__(self, data):
                self.data = data
                self.trend = self.calculate_trend(data)
                self.seasonal = self.calculate_seasonal(data)

            def calculate_trend(self, data):
                """计算趋势"""
                x = np.arange(len(data))
                y = data['y'].values
                # 简单线性回归
                coeffs = np.polyfit(x, y, 1)
                return coeffs

            def calculate_seasonal(self, data):
                """计算季节性"""
                data = data.copy()
                data['week_of_year'] = data['ds'].dt.isocalendar().week
                # 计算每周的平均季节性效应
                seasonal_pattern = data.groupby('week_of_year')['y'].mean()
                seasonal_pattern = seasonal_pattern - seasonal_pattern.mean()
                return seasonal_pattern

            def predict(self, future_data):
                """预测未来数据"""
                predictions = []

                for _, row in future_data.iterrows():
                    future_date = row['ds']

                    # 计算未来日期的索引
                    last_date = self.data['ds'].max()
                    weeks_ahead = (future_date - last_date).days // 7
                    x_future = len(self.data) + weeks_ahead

                    # 趋势预测
                    trend_value = self.trend[0] * x_future + self.trend[1]

                    # 季节性预测
                    week_of_year = future_date.isocalendar().week
                    seasonal_value = self.seasonal.get(week_of_year, 0)

                    # 组合预测
                    prediction = max(1, trend_value + seasonal_value)
                    predictions.append(prediction)

                return np.array(predictions)

        try:
            # 准备简化模型数据
            prophet_data = weekly_data.rename(columns={'date': 'ds', 'quantity': 'y'})

            simple_model = SimpleProphetModel(prophet_data)
            self.models[product_name] = simple_model

            print("简化模型训练完成")
            return simple_model

        except Exception as e:
            print(f"简化模型也失败: {str(e)}")
            return None

    def predict_future(self, data, product_name, model, forecast_weeks=13):
        """预测未来销售"""
        try:
            # 获取产品数据
            product_data = data[data['product'] == product_name].copy()
            last_date = product_data['date'].max()

            # 创建未来日期
            future_dates = pd.date_range(
                start=last_date + timedelta(weeks=1),
                periods=forecast_weeks,
                freq='W'
            )

            future_df = pd.DataFrame({'ds': future_dates})

            if PROPHET_AVAILABLE and hasattr(model, 'predict'):
                # 使用真正的Prophet模型
                # 添加回归变量
                future_df['is_holiday_season'] = ((future_df['ds'].dt.month.isin([11, 12])) |
                                                 (future_df['ds'].dt.month == 1)).astype(int)
                future_df['is_summer'] = future_df['ds'].dt.month.isin([6, 7, 8]).astype(int)

                # 预测
                forecast = model.predict(future_df)

                # 创建结果DataFrame
                result_df = pd.DataFrame({
                    'date': forecast['ds'],
                    'product': product_name,
                    'predicted_quantity': forecast['yhat'],
                    'lower_bound': forecast['yhat_lower'],
                    'upper_bound': forecast['yhat_upper']
                })

            elif hasattr(model, 'predict'):
                # 使用简化模型
                predictions = model.predict(future_df)

                result_df = pd.DataFrame({
                    'date': future_df['ds'],
                    'product': product_name,
                    'predicted_quantity': predictions,
                    'lower_bound': predictions * 0.8,
                    'upper_bound': predictions * 1.2
                })

            else:
                print(f"产品 {product_name} 模型不可用")
                return None

            # 确保预测值为正数
            result_df['predicted_quantity'] = np.maximum(1, result_df['predicted_quantity'])
            result_df['lower_bound'] = np.maximum(1, result_df['lower_bound'])
            result_df['upper_bound'] = np.maximum(1, result_df['upper_bound'])

            print(f"\n{product_name} 预测结果摘要:")
            print(f"预测平均销量: {result_df['predicted_quantity'].mean():.2f}")
            print(f"预测最大销量: {result_df['predicted_quantity'].max():.2f}")
            print(f"预测最小销量: {result_df['predicted_quantity'].min():.2f}")

            return result_df

        except Exception as e:
            print(f"预测产品 {product_name} 时出错: {str(e)}")
            return None

    def evaluate_model(self, data, product_name, model):
        """评估Prophet模型"""
        if not PROPHET_AVAILABLE or not hasattr(model, 'predict'):
            print(f"产品 {product_name} 无法进行Prophet评估")
            return None

        try:
            # 准备数据
            prophet_data = self.prepare_prophet_data(data, product_name)

            if len(prophet_data) < 16:
                print(f"产品 {product_name} 数据不足，无法评估")
                return None

            # 使用Prophet的交叉验证
            cv_results = cross_validation(
                model,
                initial=f'{len(prophet_data) // 2} W',  # 使用前一半数据作为初始训练集
                period='2 W',  # 每2周进行一次预测
                horizon='4 W'  # 预测未来4周
            )

            # 计算性能指标
            performance = performance_metrics(cv_results)

            # 获取主要指标
            mae = performance['mae'].mean()
            rmse = performance['rmse'].mean()
            mape = performance['mape'].mean()

            result = {
                'product': product_name,
                'mae': mae,
                'rmse': rmse,
                'mape': mape,
                'cv_points': len(cv_results)
            }

            print(f"\n{product_name} Prophet模型评估结果:")
            print(f"交叉验证点数量: {len(cv_results)}")
            print(f"MAE: {mae:.2f}")
            print(f"RMSE: {rmse:.2f}")
            print(f"MAPE: {mape:.2f}%")

            return result

        except Exception as e:
            print(f"评估产品 {product_name} 时出错: {str(e)}")

            # 简单评估：使用最后的8个数据点
            try:
                prophet_data = self.prepare_prophet_data(data, product_name)
                if len(prophet_data) >= 16:
                    train_data = prophet_data.iloc[:-8]
                    test_data = prophet_data.iloc[-8:]

                    if PROPHET_AVAILABLE and hasattr(model, 'predict'):
                        future_df = pd.DataFrame({'ds': test_data['ds']})
                        if 'is_holiday_season' in train_data.columns:
                            future_df['is_holiday_season'] = ((future_df['ds'].dt.month.isin([11, 12])) |
                                                            (future_df['ds'].dt.month == 1)).astype(int)
                            future_df['is_summer'] = future_df['ds'].dt.month.isin([6, 7, 8]).astype(int)

                        predictions = model.predict(future_df)['yhat'].values
                    else:
                        predictions = model.predict(future_df)

                    actuals = test_data['y'].values

                    mae = np.mean(np.abs(actuals - predictions))
                    rmse = np.sqrt(np.mean((actuals - predictions) ** 2))
                    mape = np.mean(np.abs((actuals - predictions) / actuals)) * 100

                    result = {
                        'product': product_name,
                        'mae': mae,
                        'rmse': rmse,
                        'mape': mape,
                        'note': '简单后验评估'
                    }

                    print(f"\n{product_name} 简化评估结果:")
                    print(f"MAE: {mae:.2f}")
                    print(f"RMSE: {rmse:.2f}")
                    print(f"MAPE: {mape:.2f}%")

                    return result

            except Exception as e2:
                print(f"简化评估也失败: {str(e2)}")
                return None

    def forecast_all_products(self, data, forecast_weeks=13):
        """为所有产品进行Prophet预测"""
        products = data['product'].unique()
        all_forecasts = []
        all_evaluations = []

        for product in products:
            try:
                # 训练模型
                model = self.train_prophet_model(data, product)

                if model is None:
                    continue

                # 预测未来
                forecast_df = self.predict_future(data, product, model, forecast_weeks)
                if forecast_df is not None:
                    all_forecasts.append(forecast_df)

                # 评估模型
                evaluation = self.evaluate_model(data, product, model)
                if evaluation:
                    all_evaluations.append(evaluation)

            except Exception as e:
                print(f"处理产品 {product} 时出错: {str(e)}")
                continue

        # 合并所有预测结果
        if all_forecasts:
            combined_forecast = pd.concat(all_forecasts, ignore_index=True)
            print(f"\n=== Prophet总体预测结果 ===")
            print(f"成功预测产品数量: {len(self.models)}")
            print(f"未来{forecast_weeks}周预测记录总数: {len(combined_forecast)}")

            return combined_forecast, all_evaluations
        else:
            print("没有成功完成任何Prophet预测")
            return None, None