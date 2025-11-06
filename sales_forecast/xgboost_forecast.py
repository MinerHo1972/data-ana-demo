import pandas as pd
import numpy as np
from sklearn.model_selection import TimeSeriesSplit, GridSearchCV
from sklearn.metrics import mean_absolute_error, mean_squared_error
import xgboost as xgb
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

class XGBoostForecaster:
    def __init__(self):
        self.models = {}
        self.feature_importance = {}
        self.predictions = {}

    def create_features(self, data, is_training=True):
        """创建特征工程"""
        df = data.copy()

        # 基础时间特征
        df['year'] = df['date'].dt.year
        df['month'] = df['date'].dt.month
        df['quarter'] = df['date'].dt.quarter
        df['week_of_year'] = df['date'].dt.isocalendar().week
        df['day_of_year'] = df['date'].dt.dayofyear

        # 周期性特征
        df['month_sin'] = np.sin(2 * np.pi * df['month'] / 12)
        df['month_cos'] = np.cos(2 * np.pi * df['month'] / 12)
        df['week_sin'] = np.sin(2 * np.pi * df['week_of_year'] / 52)
        df['week_cos'] = np.cos(2 * np.pi * df['week_of_year'] / 52)

        # 产品特征
        product_stats = df.groupby('product')['quantity'].agg(['mean', 'std', 'median']).reset_index()
        product_stats.columns = ['product', 'product_mean', 'product_std', 'product_median']
        df = df.merge(product_stats, on='product', how='left')

        # 产品归一化特征
        df['quantity_vs_mean'] = df['quantity'] / df['product_mean']
        df['quantity_vs_median'] = df['quantity'] / df['product_median']

        # 滞后特征
        df = df.sort_values(['product', 'date'])
        for lag in [1, 2, 4, 8, 13]:  # 1周、2周、1个月、2个月、季度
            df[f'lag_{lag}'] = df.groupby('product')['quantity'].shift(lag)

        # 滚动统计特征
        for window in [2, 4, 8, 13]:
            df[f'rolling_mean_{window}'] = df.groupby('product')['quantity'].transform(
                lambda x: x.rolling(window=window, min_periods=1).mean()
            )
            df[f'rolling_std_{window}'] = df.groupby('product')['quantity'].transform(
                lambda x: x.rolling(window=window, min_periods=1).std().fillna(0)
            )
            df[f'rolling_max_{window}'] = df.groupby('product')['quantity'].transform(
                lambda x: x.rolling(window=window, min_periods=1).max()
            )
            df[f'rolling_min_{window}'] = df.groupby('product')['quantity'].transform(
                lambda x: x.rolling(window=window, min_periods=1).min()
            )

        # 滚动窗口的趋势特征
        for window in [4, 8, 13]:
            df[f'rolling_trend_{window}'] = df.groupby('product')['quantity'].transform(
                lambda x: x.rolling(window=window, min_periods=2).apply(
                    lambda y: np.polyfit(range(len(y)), y, 1)[0] if len(y) > 1 else 0
                )
            )

        # 季节性特征
        df['is_holiday_season'] = ((df['month'].isin([11, 12])) | (df['month'] == 1)).astype(int)
        df['is_summer'] = df['month'].isin([6, 7, 8]).astype(int)
        df['is_year_end'] = (df['month'] == 12).astype(int)
        df['is_year_start'] = (df['month'] == 1).astype(int)

        # 周数特征
        df['week_number'] = df.groupby(['product', 'year']).cumcount() + 1

        # 填充缺失值
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        for col in numeric_columns:
            if df[col].isnull().any():
                df[col] = df[col].fillna(df[col].median())

        return df

    def prepare_training_data(self, data, product_name):
        """为单个产品准备训练数据"""
        product_data = data[data['product'] == product_name].copy()

        # 创建特征
        product_data = self.create_features(product_data)

        # 定义特征列
        feature_columns = [col for col in product_data.columns
                          if col not in ['date', 'product', 'quantity']]

        # 准备特征和目标变量
        X = product_data[feature_columns]
        y = product_data['quantity']

        # 删除包含NaN的行（由于滞后特征）
        mask = ~(X.isnull().any(axis=1) | y.isnull())
        X = X[mask]
        y = y[mask]

        return X, y, feature_columns

    def train_product_model(self, data, product_name):
        """为单个产品训练XGBoost模型"""
        print(f"\n=== 开始训练 {product_name} 的XGBoost模型 ===")

        # 准备数据
        X, y, feature_columns = self.prepare_training_data(data, product_name)

        if len(X) < 10:
            print(f"产品 {product_name} 数据量不足，跳过训练")
            return None

        print(f"训练数据点数量: {len(X)}")
        print(f"特征数量: {len(feature_columns)}")
        print(f"平均销量: {y.mean():.2f}")
        print(f"销量标准差: {y.std():.2f}")

        # 时间序列分割
        tscv = TimeSeriesSplit(n_splits=min(5, len(X) // 4))

        # XGBoost参数调优
        param_grid = {
            'n_estimators': [100, 200],
            'max_depth': [3, 5, 7],
            'learning_rate': [0.01, 0.1],
            'subsample': [0.8, 0.9],
            'colsample_bytree': [0.8, 0.9]
        }

        # 使用较小的参数空间以加快训练
        param_grid = {
            'n_estimators': [100, 200],
            'max_depth': [3, 5],
            'learning_rate': [0.1],
            'subsample': [0.8],
            'colsample_bytree': [0.8]
        }

        model = xgb.XGBRegressor(
            objective='reg:squarederror',
            random_state=42,
            n_jobs=-1
        )

        try:
            # 网格搜索最优参数
            grid_search = GridSearchCV(
                estimator=model,
                param_grid=param_grid,
                cv=tscv,
                scoring='neg_mean_absolute_error',
                verbose=0,
                n_jobs=-1
            )

            grid_search.fit(X, y)

            best_model = grid_search.best_estimator_
            best_params = grid_search.best_params_

            print(f"最优参数: {best_params}")
            print(f"最佳CV得分: {-grid_search.best_score_:.2f}")

            # 保存模型
            self.models[product_name] = best_model

            # 计算特征重要性
            feature_importance = pd.DataFrame({
                'feature': feature_columns,
                'importance': best_model.feature_importances_
            }).sort_values('importance', ascending=False)

            self.feature_importance[product_name] = feature_importance

            print(f"\n前10个重要特征:")
            print(feature_importance.head(10))

            return best_model, feature_columns

        except Exception as e:
            print(f"训练产品 {product_name} 的模型时出错: {str(e)}")
            # 使用简单的默认参数
            try:
                simple_model = xgb.XGBRegressor(
                    n_estimators=100,
                    max_depth=3,
                    learning_rate=0.1,
                    random_state=42
                )
                simple_model.fit(X, y)
                self.models[product_name] = simple_model
                print("使用默认参数成功训练模型")
                return simple_model, feature_columns
            except Exception as e2:
                print(f"使用默认参数也失败: {str(e2)}")
                return None

    def create_future_features(self, last_date, product_name, product_stats, forecast_weeks=13):
        """为未来预测创建特征"""
        future_dates = pd.date_range(
            start=last_date + timedelta(weeks=1),
            periods=forecast_weeks,
            freq='W'
        )

        future_data = pd.DataFrame({
            'date': future_dates,
            'product': product_name
        })

        # 基础时间特征
        future_data['year'] = future_data['date'].dt.year
        future_data['month'] = future_data['date'].dt.month
        future_data['quarter'] = future_data['date'].dt.quarter
        future_data['week_of_year'] = future_data['date'].dt.isocalendar().week
        future_data['day_of_year'] = future_data['date'].dt.dayofyear

        # 周期性特征
        future_data['month_sin'] = np.sin(2 * np.pi * future_data['month'] / 12)
        future_data['month_cos'] = np.cos(2 * np.pi * future_data['month'] / 12)
        future_data['week_sin'] = np.sin(2 * np.pi * future_data['week_of_year'] / 52)
        future_data['week_cos'] = np.cos(2 * np.pi * future_data['week_of_year'] / 52)

        # 产品统计特征
        future_data['product_mean'] = product_stats['mean']
        future_data['product_std'] = product_stats['std']
        future_data['product_median'] = product_stats['median']

        # 产品归一化特征（初始化为1，表示与平均值相同）
        future_data['quantity_vs_mean'] = 1.0
        future_data['quantity_vs_median'] = 1.0

        # 季节性特征
        future_data['is_holiday_season'] = ((future_data['month'].isin([11, 12])) | (future_data['month'] == 1)).astype(int)
        future_data['is_summer'] = future_data['month'].isin([6, 7, 8]).astype(int)
        future_data['is_year_end'] = (future_data['month'] == 12).astype(int)
        future_data['is_year_start'] = (future_data['month'] == 1).astype(int)

        # 周数特征
        future_data['week_number'] = range(1, forecast_weeks + 1)

        # 其他特征设置为默认值
        numeric_features = [f'lag_{i}' for i in [1, 2, 4, 8, 13]] + \
                          [f'rolling_mean_{i}' for i in [2, 4, 8, 13]] + \
                          [f'rolling_std_{i}' for i in [2, 4, 8, 13]] + \
                          [f'rolling_max_{i}' for i in [2, 4, 8, 13]] + \
                          [f'rolling_min_{i}' for i in [2, 4, 8, 13]] + \
                          [f'rolling_trend_{i}' for i in [4, 8, 13]]

        for feature in numeric_features:
            if feature.startswith('lag_') or 'mean' in feature:
                future_data[feature] = product_stats['mean']
            elif 'std' in feature:
                future_data[feature] = product_stats['std']
            elif 'max' in feature:
                future_data[feature] = product_stats['mean'] + product_stats['std']
            elif 'min' in feature:
                future_data[feature] = max(1, product_stats['mean'] - product_stats['std'])
            elif 'trend' in feature:
                future_data[feature] = 0

        return future_data

    def predict_future(self, data, product_name, model, feature_columns, forecast_weeks=13):
        """预测未来销售"""
        # 获取产品统计信息
        product_data = data[data['product'] == product_name]
        product_stats = {
            'mean': product_data['quantity'].mean(),
            'std': product_data['quantity'].std(),
            'median': product_data['quantity'].median()
        }

        # 获取最后日期
        last_date = product_data['date'].max()

        # 创建未来特征
        future_data = self.create_future_features(last_date, product_name, product_stats, forecast_weeks)

        # 确保特征列与训练时一致
        for col in feature_columns:
            if col not in future_data.columns:
                future_data[col] = 0

        X_future = future_data[feature_columns]

        # 预测
        predictions = model.predict(X_future)

        # 确保预测值为正数
        predictions = np.maximum(1, predictions)

        # 创建预测结果
        forecast_df = pd.DataFrame({
            'date': future_data['date'],
            'product': product_name,
            'predicted_quantity': predictions
        })

        return forecast_df

    def evaluate_model(self, data, product_name, model, feature_columns):
        """评估模型在历史数据上的表现"""
        product_data = data[data['product'] == product_name].copy()
        product_data = product_data.sort_values('date')

        if len(product_data) < 20:
            print(f"产品 {product_name} 数据不足，跳过评估")
            return None

        # 使用最后8周作为测试集
        train_size = len(product_data) - 8
        train_data = product_data.iloc[:train_size]
        test_data = product_data.iloc[train_size:]

        # 准备训练和测试数据
        X_train, y_train, _ = self.prepare_training_data(train_data, product_name)
        X_test, y_test, _ = self.prepare_training_data(test_data, product_name)

        if len(X_test) == 0:
            print(f"产品 {product_name} 测试数据不足")
            return None

        # 在训练集上重新训练模型
        try:
            eval_model = xgb.XGBRegressor(**model.get_params())
            eval_model.fit(X_train, y_train)

            # 预测测试集
            y_pred = eval_model.predict(X_test)
            y_pred = np.maximum(1, y_pred)

            # 计算评估指标
            mae = mean_absolute_error(y_test, y_pred)
            rmse = np.sqrt(mean_squared_error(y_test, y_pred))
            mape = np.mean(np.abs((y_test - y_pred) / y_test)) * 100

            result = {
                'product': product_name,
                'mae': mae,
                'rmse': rmse,
                'mape': mape,
                'test_actual_mean': y_test.mean(),
                'test_pred_mean': y_pred.mean(),
                'test_size': len(y_test)
            }

            print(f"\n{product_name} XGBoost模型评估结果:")
            print(f"测试集大小: {len(y_test)}")
            print(f"测试集平均实际销量: {y_test.mean():.2f}")
            print(f"测试集平均预测销量: {y_pred.mean():.2f}")
            print(f"MAE: {mae:.2f}")
            print(f"RMSE: {rmse:.2f}")
            print(f"MAPE: {mape:.2f}%")

            return result

        except Exception as e:
            print(f"评估产品 {product_name} 时出错: {str(e)}")
            return None

    def forecast_all_products(self, data, forecast_weeks=13):
        """为所有产品进行预测"""
        products = data['product'].unique()
        all_forecasts = []
        all_evaluations = []

        for product in products:
            try:
                # 训练模型
                model, feature_columns = self.train_product_model(data, product)

                if model is None:
                    continue

                # 预测未来
                forecast_df = self.predict_future(data, product, model, feature_columns, forecast_weeks)
                all_forecasts.append(forecast_df)

                # 评估模型
                evaluation = self.evaluate_model(data, product, model, feature_columns)
                if evaluation:
                    all_evaluations.append(evaluation)

            except Exception as e:
                print(f"处理产品 {product} 时出错: {str(e)}")
                continue

        # 合并所有预测结果
        if all_forecasts:
            combined_forecast = pd.concat(all_forecasts, ignore_index=True)
            print(f"\n=== XGBoost总体预测结果 ===")
            print(f"成功预测产品数量: {len(self.models)}")
            print(f"未来{forecast_weeks}周预测记录总数: {len(combined_forecast)}")

            return combined_forecast, all_evaluations
        else:
            print("没有成功完成任何XGBoost预测")
            return None, None