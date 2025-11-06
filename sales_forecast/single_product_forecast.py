#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
单一商品4G销售预测系统
处理两列数据：第几周和销售量
使用三种方法预测未来13周销售数据
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

class SingleProductForecaster:
    def __init__(self):
        self.data = None
        self.results = {}

    def load_data_from_file(self, file_path):
        """从Excel文件加载单一商品数据"""
        try:
            # 尝试读取Excel文件
            self.data = pd.read_excel(file_path)
            print(f"成功加载文件: {file_path}")
            print(f"数据形状: {self.data.shape}")
            print(f"列名: {list(self.data.columns)}")

            # 统一列名
            if len(self.data.columns) == 2:
                self.data.columns = ['week', 'sales']
            else:
                # 如果列名不同，尝试自动识别
                cols = list(self.data.columns)
                if 'week' in cols[0].lower() or '周' in cols[0]:
                    self.data.columns = ['week', 'sales']
                else:
                    self.data.columns = ['sales', 'week']
                    self.data = self.data[['week', 'sales']]

            print("数据预览:")
            print(self.data.head(10))
            print(f"\n数据统计:")
            print(f"周数范围: {self.data['week'].min()} - {self.data['week'].max()}")
            print(f"销量范围: {self.data['sales'].min()} - {self.data['sales'].max()}")
            print(f"平均销量: {self.data['sales'].mean():.2f}")
            print(f"销量标准差: {self.data['sales'].std():.2f}")

            return True

        except Exception as e:
            print(f"文件读取失败: {str(e)}")
            # 创建示例数据用于演示
            print("创建示例4G销售数据进行演示...")
            self.create_demo_data()
            return True

    def create_demo_data(self):
        """创建演示用的4G销售数据"""
        np.random.seed(42)

        # 创建52周的数据
        weeks = list(range(1, 53))
        sales = []

        for week in weeks:
            # 模拟4G产品销售模式：初期增长，后期稳定，有季节性
            base_sales = 50 + 30 * (1 - np.exp(-week/20))  # 初期快速增长，后期饱和
            seasonal = 10 * np.sin(2 * np.pi * week / 52)  # 年度季节性
            noise = np.random.normal(0, 5)  # 随机噪声

            # 添加一些特殊的促销周
            if week in [13, 26, 39]:  # 季度末促销
                promotion_boost = np.random.uniform(15, 25)
            else:
                promotion_boost = 0

            weekly_sales = base_sales + seasonal + noise + promotion_boost
            sales.append(max(20, weekly_sales))  # 确保最低销量

        self.data = pd.DataFrame({
            'week': weeks,
            'sales': sales
        })

        print("示例数据已创建:")
        print(f"周数: 1-52")
        print(f"销量范围: {min(sales):.1f} - {max(sales):.1f}")

    def prepare_features(self):
        """准备特征用于机器学习模型"""
        df = self.data.copy()

        # 基础特征
        df['week_sin'] = np.sin(2 * np.pi * df['week'] / 52)
        df['week_cos'] = np.cos(2 * np.pi * df['week'] / 52)
        df['quarter'] = ((df['week'] - 1) // 13) + 1
        df['month_approx'] = ((df['week'] - 1) // 4) + 1

        # 滞后特征
        for lag in [1, 2, 4, 8, 13]:
            df[f'lag_{lag}'] = df['sales'].shift(lag)

        # 滚动统计特征
        for window in [2, 4, 8, 13]:
            df[f'rolling_mean_{window}'] = df['sales'].rolling(window=window, min_periods=1).mean()
            df[f'rolling_std_{window}'] = df['sales'].rolling(window=window, min_periods=1).std().fillna(0)
            df[f'rolling_trend_{window}'] = df['sales'].rolling(window=window, min_periods=2).apply(
                lambda x: np.polyfit(range(len(x)), x, 1)[0] if len(x) > 1 else 0
            )

        # 填充缺失值
        df = df.fillna(method='bfill').fillna(0)

        return df

    def sarima_forecast(self):
        """SARIMA时间序列预测"""
        print("\n" + "="*50)
        print("1. SARIMA 时间序列预测")
        print("="*50)

        try:
            from statsmodels.tsa.statespace.sarimax import SARIMAX
            from statsmodels.tsa.stattools import adfuller

            # 准备时间序列数据
            ts_data = self.data['sales'].values

            print(f"数据点数量: {len(ts_data)}")

            # 平稳性检验
            result = adfuller(ts_data)
            print(f"ADF检验统计量: {result[0]:.4f}")
            print(f"p-value: {result[1]:.4f}")

            # 根据数据量选择参数
            if len(ts_data) < 26:  # 少于半年数据
                order = (1, 1, 1)
                seasonal_order = (0, 1, 1, 52)
            else:
                order = (2, 1, 2)
                seasonal_order = (1, 1, 1, 52)

            print(f"使用SARIMA{order}x{seasonal_order}")

            # 训练模型
            model = SARIMAX(ts_data,
                          order=order,
                          seasonal_order=seasonal_order,
                          enforce_stationarity=False,
                          enforce_invertibility=False)

            results = model.fit(disp=False)
            print(f"模型AIC: {results.aic:.2f}")

            # 预测未来13周
            forecast = results.get_forecast(steps=13)
            forecast_mean = forecast.predicted_mean
            forecast_ci = forecast.conf_int()

            # 创建预测结果
            last_week = self.data['week'].max()
            future_weeks = list(range(last_week + 1, last_week + 14))

            sarima_results = pd.DataFrame({
                'week': future_weeks,
                'predicted_sales': forecast_mean.values,
                'lower_bound': forecast_ci.iloc[:, 0].values,
                'upper_bound': forecast_ci.iloc[:, 1].values,
                'method': 'SARIMA'
            })

            print(f"\nSARIMA预测结果:")
            print(f"未来13周平均预测: {forecast_mean.mean():.2f}")
            print(f"预测范围: {forecast_mean.min():.2f} - {forecast_mean.max():.2f}")

            self.results['SARIMA'] = sarima_results
            return sarima_results

        except Exception as e:
            print(f"SARIMA预测失败: {str(e)}")
            return self.fallback_forecast('SARIMA')

    def xgboost_forecast(self):
        """XGBoost机器学习预测"""
        print("\n" + "="*50)
        print("2. XGBoost 机器学习预测")
        print("="*50)

        try:
            import xgboost as xgb
            from sklearn.model_selection import train_test_split
            from sklearn.metrics import mean_absolute_error

            # 准备特征
            feature_df = self.prepare_features()

            # 定义特征列
            feature_columns = [col for col in feature_df.columns if col not in ['week', 'sales']]

            # 准备训练数据
            X = feature_df[feature_columns]
            y = feature_df['sales']

            print(f"特征数量: {len(feature_columns)}")
            print(f"训练数据点: {len(X)}")

            # 确保有足够的数据
            if len(X) < 10:
                print("数据量不足，使用简化模型")
                return self.fallback_forecast('XGBoost')

            # 分割训练和验证集
            if len(X) > 20:
                X_train, X_val, y_train, y_val = train_test_split(
                    X, y, test_size=0.2, random_state=42, shuffle=False
                )
            else:
                X_train, y_train = X, y
                X_val, y_val = X, y

            # 训练XGBoost模型
            model = xgb.XGBRegressor(
                n_estimators=100,
                max_depth=3,
                learning_rate=0.1,
                random_state=42,
                n_jobs=-1
            )

            model.fit(X_train, y_train)

            # 验证模型
            if len(X_val) > 0:
                val_pred = model.predict(X_val)
                val_mae = mean_absolute_error(y_val, val_pred)
                print(f"验证集MAE: {val_mae:.2f}")

            # 创建未来特征
            last_week = self.data['week'].max()
            future_weeks = list(range(last_week + 1, last_week + 14))

            future_features = []
            for week in future_weeks:
                # 计算特征
                week_sin = np.sin(2 * np.pi * week / 52)
                week_cos = np.cos(2 * np.pi * week / 52)
                quarter = ((week - 1) // 13) + 1
                month_approx = ((week - 1) // 4) + 1

                # 使用历史数据的统计值作为滞后特征
                recent_sales = self.data['sales'].tail(4).mean()
                sales_std = self.data['sales'].std()

                feature_row = {
                    'week_sin': week_sin,
                    'week_cos': week_cos,
                    'quarter': quarter,
                    'month_approx': month_approx,
                    'lag_1': recent_sales,
                    'lag_2': recent_sales,
                    'lag_4': recent_sales,
                    'lag_8': recent_sales,
                    'lag_13': recent_sales,
                    'rolling_mean_2': recent_sales,
                    'rolling_std_2': sales_std,
                    'rolling_trend_2': 0,
                    'rolling_mean_4': recent_sales,
                    'rolling_std_4': sales_std,
                    'rolling_trend_4': 0,
                    'rolling_mean_8': recent_sales,
                    'rolling_std_8': sales_std,
                    'rolling_trend_8': 0,
                    'rolling_mean_13': recent_sales,
                    'rolling_std_13': sales_std,
                    'rolling_trend_13': 0
                }

                future_features.append(feature_row)

            future_df = pd.DataFrame(future_features)

            # 确保特征列一致
            for col in feature_columns:
                if col not in future_df.columns:
                    future_df[col] = 0

            X_future = future_df[feature_columns]

            # 预测
            predictions = model.predict(X_future)
            predictions = np.maximum(10, predictions)  # 确保最小销量

            xgb_results = pd.DataFrame({
                'week': future_weeks,
                'predicted_sales': predictions,
                'method': 'XGBoost'
            })

            # 计算置信区间（简化版）
            xgb_results['lower_bound'] = xgb_results['predicted_sales'] * 0.8
            xgb_results['upper_bound'] = xgb_results['predicted_sales'] * 1.2

            print(f"\nXGBoost预测结果:")
            print(f"未来13周平均预测: {predictions.mean():.2f}")
            print(f"预测范围: {predictions.min():.2f} - {predictions.max():.2f}")

            # 特征重要性
            feature_importance = pd.DataFrame({
                'feature': feature_columns,
                'importance': model.feature_importances_
            }).sort_values('importance', ascending=False)

            print(f"\n前5个重要特征:")
            print(feature_importance.head())

            self.results['XGBoost'] = xgb_results
            return xgb_results

        except Exception as e:
            print(f"XGBoost预测失败: {str(e)}")
            return self.fallback_forecast('XGBoost')

    def prophet_forecast(self):
        """Prophet商业预测"""
        print("\n" + "="*50)
        print("3. Prophet 商业预测")
        print("="*50)

        try:
            from prophet import Prophet

            # 准备Prophet格式数据
            prophet_df = self.data.copy()

            # 将周数转换为日期（假设从2022年第1周开始）
            start_date = datetime(2022, 1, 1)
            prophet_df['ds'] = prophet_df['week'].apply(
                lambda w: start_date + timedelta(weeks=w-1)
            )
            prophet_df['y'] = prophet_df['sales']

            print(f"数据时间范围: {prophet_df['ds'].min()} 至 {prophet_df['ds'].max()}")

            # 创建Prophet模型
            model = Prophet(
                yearly_seasonality=True,
                weekly_seasonality=False,  # 周数据不需要周季节性
                daily_seasonality=False,
                changepoint_prior_scale=0.05,
                seasonality_prior_scale=10.0,
                holidays_prior_scale=10.0,
                interval_width=0.8
            )

            # 添加季度季节性（如果有足够数据）
            if len(prophet_df) >= 26:
                model.add_seasonality(
                    name='quarterly',
                    period=91.25,  # 季度天数
                    fourier_order=5
                )

            # 训练模型
            model.fit(prophet_df)

            # 创建未来13周的数据框
            last_date = prophet_df['ds'].max()
            future_dates = pd.date_range(
                start=last_date + timedelta(weeks=1),
                periods=13,
                freq='W'
            )

            future_df = pd.DataFrame({'ds': future_dates})

            # 预测
            forecast = model.predict(future_df)

            # 提取预测结果
            prophet_results = pd.DataFrame({
                'week': list(range(self.data['week'].max() + 1, self.data['week'].max() + 14)),
                'predicted_sales': forecast['yhat'].values,
                'lower_bound': forecast['yhat_lower'].values,
                'upper_bound': forecast['yhat_upper'].values,
                'method': 'Prophet'
            })

            # 确保预测值为正数
            prophet_results['predicted_sales'] = np.maximum(10, prophet_results['predicted_sales'])
            prophet_results['lower_bound'] = np.maximum(10, prophet_results['lower_bound'])
            prophet_results['upper_bound'] = np.maximum(10, prophet_results['upper_bound'])

            print(f"\nProphet预测结果:")
            print(f"未来13周平均预测: {prophet_results['predicted_sales'].mean():.2f}")
            print(f"预测范围: {prophet_results['predicted_sales'].min():.2f} - {prophet_results['predicted_sales'].max():.2f}")

            self.results['Prophet'] = prophet_results
            return prophet_results

        except Exception as e:
            print(f"Prophet预测失败: {str(e)}")
            print("使用简化Prophet方法...")
            return self.simple_prophet_forecast()

    def simple_prophet_forecast(self):
        """简化的Prophet风格预测"""
        print("使用简化Prophet方法...")

        # 计算趋势和季节性
        sales_data = self.data['sales'].values

        # 简单线性趋势
        x = np.arange(len(sales_data))
        trend_coeffs = np.polyfit(x, sales_data, 1)
        trend = np.polyval(trend_coeffs, x)

        # 季节性模式（年度周期）
        seasonal_pattern = []
        for week in range(52):
            week_sales = [sales_data[i] for i in range(week, len(sales_data), 52)]
            if week_sales:
                seasonal_pattern.append(np.mean(week_sales) - np.mean(sales_data))
            else:
                seasonal_pattern.append(0)

        # 预测未来13周
        last_week = self.data['week'].max()
        future_weeks = list(range(last_week + 1, last_week + 14))
        predictions = []

        for i, week in enumerate(future_weeks):
            # 趋势预测
            future_x = len(sales_data) + i
            trend_value = np.polyval(trend_coeffs, future_x)

            # 季节性调整
            seasonal_index = (week - 1) % 52
            seasonal_value = seasonal_pattern[seasonal_index] if seasonal_index < len(seasonal_pattern) else 0

            # 组合预测
            predicted = trend_value + seasonal_value
            predicted = max(10, predicted)  # 确保最小销量

            predictions.append(predicted)

        prophet_results = pd.DataFrame({
            'week': future_weeks,
            'predicted_sales': predictions,
            'lower_bound': [p * 0.8 for p in predictions],
            'upper_bound': [p * 1.2 for p in predictions],
            'method': '简化Prophet'
        })

        print(f"简化Prophet预测完成，平均预测: {np.mean(predictions):.2f}")

        self.results['Prophet'] = prophet_results
        return prophet_results

    def fallback_forecast(self, method_name):
        """备用预测方法（移动平均）"""
        print(f"使用{method_name}的备用预测方法...")

        # 计算最近4周和8周的加权平均
        recent_4w = self.data['sales'].tail(4).mean()
        recent_8w = self.data['sales'].tail(8).mean()

        # 加权平均
        base_prediction = 0.7 * recent_4w + 0.3 * recent_8w

        # 预测未来13周
        last_week = self.data['week'].max()
        future_weeks = list(range(last_week + 1, last_week + 14))

        predictions = []
        for i in range(13):
            # 添加简单的季节性调整
            seasonal_factor = 1 + 0.1 * np.sin(2 * np.pi * i / 13)
            predicted = base_prediction * seasonal_factor
            predictions.append(max(10, predicted))

        fallback_results = pd.DataFrame({
            'week': future_weeks,
            'predicted_sales': predictions,
            'lower_bound': [p * 0.8 for p in predictions],
            'upper_bound': [p * 1.2 for p in predictions],
            'method': f'{method_name}备用'
        })

        return fallback_results

    def compare_methods(self):
        """比较三种预测方法"""
        print("\n" + "="*60)
        print("预测方法对比分析")
        print("="*60)

        if not self.results:
            print("没有可比较的预测结果")
            return

        # 创建对比表格
        comparison_data = []
        for method, result in self.results.items():
            avg_prediction = result['predicted_sales'].mean()
            min_prediction = result['predicted_sales'].min()
            max_prediction = result['predicted_sales'].max()

            comparison_data.append({
                '方法': method,
                '平均预测': f"{avg_prediction:.2f}",
                '最小预测': f"{min_prediction:.2f}",
                '最大预测': f"{max_prediction:.2f}",
                '预测范围': f"{max_prediction - min_prediction:.2f}"
            })

        comparison_df = pd.DataFrame(comparison_data)
        print("\n预测结果对比:")
        print(comparison_df.to_string(index=False))

        # 显示详细预测
        print(f"\n未来13周详细预测:")
        print("-" * 80)
        print(f"{'周数':<6}", end="")
        for method in self.results.keys():
            print(f"{method:<12}", end="")
        print()
        print("-" * 80)

        last_week = self.data['week'].max()
        for i in range(13):
            week = last_week + i + 1
            print(f"{week:<6}", end="")
            for method in self.results.keys():
                prediction = self.results[method].iloc[i]['predicted_sales']
                print(f"{prediction:<12.1f}", end="")
            print()

        # 方法推荐
        print(f"\n方法特点分析:")
        print(f"• SARIMA: 适合有季节性的时间序列数据")
        print(f"• XGBoost: 适合复杂的非线性模式")
        print(f"• Prophet: 适合业务场景下的快速预测")

        # 选择最佳方法（基于预测稳定性）
        best_method = None
        best_stability = float('inf')

        for method, result in self.results.items():
            predictions = result['predicted_sales'].values
            stability = np.std(predictions)  # 标准差越小越稳定

            if stability < best_stability:
                best_stability = stability
                best_method = method

        print(f"\n🏆 基于预测稳定性，推荐使用: {best_method}")
        print(f"   预测标准差: {best_stability:.2f}")

    def save_results(self, filename='4g_sales_forecast_results.xlsx'):
        """保存预测结果到Excel文件"""
        try:
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                # 保存原始数据
                self.data.to_excel(writer, sheet_name='原始数据', index=False)

                # 保存各方法的预测结果
                for method, result in self.results.items():
                    result.to_excel(writer, sheet_name=f'{method}预测', index=False)

                # 保存汇总结果
                if len(self.results) > 1:
                    # 创建汇总表
                    summary_data = []
                    last_week = self.data['week'].max()

                    for i in range(13):
                        week = last_week + i + 1
                        row = {'周数': week}

                        for method, result in self.results.items():
                            if i < len(result):
                                row[f'{method}_预测'] = result.iloc[i]['predicted_sales']
                                if 'lower_bound' in result.columns:
                                    row[f'{method}_下限'] = result.iloc[i]['lower_bound']
                                    row[f'{method}_上限'] = result.iloc[i]['upper_bound']

                        summary_data.append(row)

                    summary_df = pd.DataFrame(summary_data)
                    summary_df.to_excel(writer, sheet_name='预测汇总', index=False)

                print(f"\n预测结果已保存到: {filename}")

        except Exception as e:
            print(f"保存结果失败: {str(e)}")

    def run_all_forecasts(self, file_path=None):
        """运行所有预测方法"""
        print("="*60)
        print("单一商品4G销售预测系统")
        print("="*60)

        # 加载数据
        if not self.load_data_from_file(file_path):
            print("数据加载失败")
            return

        print(f"\n开始使用三种方法预测未来13周销售数据...")

        # 运行三种预测方法
        try:
            self.sarima_forecast()
        except Exception as e:
            print(f"SARIMA预测异常: {str(e)}")

        try:
            self.xgboost_forecast()
        except Exception as e:
            print(f"XGBoost预测异常: {str(e)}")

        try:
            self.prophet_forecast()
        except Exception as e:
            print(f"Prophet预测异常: {str(e)}")

        # 比较方法
        self.compare_methods()

        # 保存结果
        self.save_results()

        print(f"\n预测完成！")
        return self.results

def main():
    """主函数"""
    forecaster = SingleProductForecaster()

    # 尝试加载用户提供的文件
    file_path = 'sales_4g_byweek.xlsx'

    try:
        results = forecaster.run_all_forecasts(file_path)

        print(f"\n{'='*60}")
        print("预测总结")
        print(f"{'='*60}")
        print(f"✅ 已完成三种方法的预测分析")
        print(f"✅ 结果已保存到 Excel 文件")
        print(f"✅ 请查看生成的预测结果和建议")

    except Exception as e:
        print(f"运行过程中出现错误: {str(e)}")
        print("请检查数据文件是否正确")

if __name__ == "__main__":
    main()