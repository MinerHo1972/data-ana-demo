import pandas as pd
import numpy as np
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.tsa.stattools import adfuller
import warnings
warnings.filterwarnings('ignore')

class SARIMAForecaster:
    def __init__(self):
        self.models = {}
        self.forecasts = {}
        self.evaluation_results = []

    def check_stationarity(self, timeseries):
        """检查时间序列的平稳性"""
        result = adfuller(timeseries)
        print('ADF Statistic: %f' % result[0])
        print('p-value: %f' % result[1])
        print('Critical Values:')
        for key, value in result[4].items():
            print('\t%s: %.3f' % (key, value))

        if result[1] <= 0.05:
            print("时间序列是平稳的")
        else:
            print("时间序列是非平稳的")
        return result[1] <= 0.05

    def find_best_sarima_params(self, timeseries, max_p=3, max_d=2, max_q=3,
                               max_P=2, max_D=1, max_Q=2, max_s=52):
        """寻找最优的SARIMA参数"""
        print("正在寻找最优SARIMA参数...")

        best_aic = float('inf')
        best_params = None

        # 简化参数搜索以加快速度
        p_range = range(0, min(3, max_p + 1))
        d_range = range(0, min(2, max_d + 1))
        q_range = range(0, min(3, max_q + 1))
        P_range = range(0, min(2, max_P + 1))
        D_range = range(0, min(2, max_D + 1))
        Q_range = range(0, min(2, max_Q + 1))

        for p in p_range:
            for d in d_range:
                for q in q_range:
                    for P in P_range:
                        for D in D_range:
                            for Q in Q_range:
                                try:
                                    model = SARIMAX(timeseries,
                                                  order=(p, d, q),
                                                  seasonal_order=(P, D, Q, 52),
                                                  enforce_stationarity=False,
                                                  enforce_invertibility=False)
                                    results = model.fit(disp=False)

                                    if results.aic < best_aic:
                                        best_aic = results.aic
                                        best_params = (p, d, q, P, D, Q)

                                except Exception as e:
                                    continue

        print(f"最优参数: (p,d,q)=({best_params[0]},{best_params[1]},{best_params[2]}), "
              f"(P,D,Q)=({best_params[3]},{best_params[4]},{best_params[5]})")
        print(f"最优AIC: {best_aic}")

        return best_params

    def train_and_forecast(self, data, product_name, forecast_weeks=13):
        """为单个产品训练SARIMA模型并预测"""
        print(f"\n=== 开始处理 {product_name} ===")

        # 准备时间序列数据
        ts_data = data[data['product'] == product_name].copy()
        ts_data = ts_data.sort_values('date')
        ts_data = ts_data.set_index('date')

        # 按周聚合数据（如果有重复日期）
        weekly_data = ts_data['quantity'].resample('W').sum()

        print(f"数据点数量: {len(weekly_data)}")
        print(f"平均周销量: {weekly_data.mean():.2f}")
        print(f"销量标准差: {weekly_data.std():.2f}")

        # 检查平稳性
        print("\n平稳性检验:")
        is_stationary = self.check_stationarity(weekly_data)

        # 如果数据点太少，使用更简单的模型
        if len(weekly_data) < 52:  # 少于一年数据
            print("数据量较少，使用简化的SARIMA参数")
            order = (1, 1, 1)
            seasonal_order = (1, 1, 0, 52)
        else:
            # 寻找最优参数
            best_params = self.find_best_sarima_params(weekly_data)
            if best_params:
                order = (best_params[0], best_params[1], best_params[2])
                seasonal_order = (best_params[3], best_params[4], best_params[5], 52)
            else:
                order = (1, 1, 1)
                seasonal_order = (1, 1, 1, 52)

        try:
            # 训练模型
            print(f"\n训练SARIMA模型: SARIMA{order}x{seasonal_order}")
            model = SARIMAX(weekly_data,
                          order=order,
                          seasonal_order=seasonal_order,
                          enforce_stationarity=False,
                          enforce_invertibility=False)

            results = model.fit(disp=False)
            print("模型训练完成")

            # 模型诊断
            print("\n模型诊断:")
            print(f"AIC: {results.aic:.2f}")
            print(f"BIC: {results.bic:.2f}")

            # 预测未来13周
            forecast = results.get_forecast(steps=forecast_weeks)
            forecast_mean = forecast.predicted_mean
            forecast_ci = forecast.conf_int()

            # 获取最后一个日期
            last_date = weekly_data.index[-1]
            forecast_dates = pd.date_range(
                start=last_date + pd.Timedelta(days=7),
                periods=forecast_weeks,
                freq='W'
            )

            # 创建预测结果DataFrame
            forecast_df = pd.DataFrame({
                'date': forecast_dates,
                'product': product_name,
                'predicted_quantity': forecast_mean.values,
                'lower_bound': forecast_ci.iloc[:, 0].values,
                'upper_bound': forecast_ci.iloc[:, 1].values
            })

            self.models[product_name] = results
            self.forecasts[product_name] = forecast_df

            print(f"\n预测结果摘要:")
            print(f"预测平均销量: {forecast_mean.mean():.2f}")
            print(f"预测最大销量: {forecast_mean.max():.2f}")
            print(f"预测最小销量: {forecast_mean.min():.2f}")

            return forecast_df

        except Exception as e:
            print(f"SARIMA模型训练失败: {str(e)}")
            # 使用简单的移动平均作为备选
            return self.simple_fallback(weekly_data, product_name, forecast_weeks)

    def simple_fallback(self, data, product_name, forecast_weeks):
        """简单备选预测方法"""
        print("使用简单移动平均作为备选方法")

        # 计算最近4周和8周的平均值
        recent_4w = data.tail(4).mean()
        recent_8w = data.tail(8).mean()

        # 使用加权平均
        predicted_value = 0.7 * recent_4w + 0.3 * recent_8w

        last_date = data.index[-1]
        forecast_dates = pd.date_range(
            start=last_date + pd.Timedelta(days=7),
            periods=forecast_weeks,
            freq='W'
        )

        forecast_df = pd.DataFrame({
            'date': forecast_dates,
            'product': product_name,
            'predicted_quantity': predicted_value,
            'lower_bound': predicted_value * 0.8,
            'upper_bound': predicted_value * 1.2
        })

        return forecast_df

    def evaluate_model(self, data, product_name):
        """评估模型在历史数据上的表现"""
        if product_name not in self.models:
            print(f"产品 {product_name} 没有训练好的模型")
            return None

        model = self.models[product_name]
        ts_data = data[data['product'] == product_name].copy()
        ts_data = ts_data.sort_values('date')
        ts_data = ts_data.set_index('date')
        weekly_data = ts_data['quantity'].resample('W').sum()

        # 使用最后8周作为测试集
        if len(weekly_data) > 16:
            train_data = weekly_data[:-8]
            test_data = weekly_data[-8:]

            # 在训练集上重新训练
            try:
                train_model = SARIMAX(train_data,
                                    order=model.model.order,
                                    seasonal_order=model.model.seasonal_order,
                                    enforce_stationarity=False,
                                    enforce_invertibility=False)
                train_results = train_model.fit(disp=False)

                # 预测测试集
                predictions = train_results.get_forecast(steps=8)
                pred_mean = predictions.predicted_mean

                # 计算评估指标
                mae = np.mean(np.abs(test_data - pred_mean))
                rmse = np.sqrt(np.mean((test_data - pred_mean) ** 2))
                mape = np.mean(np.abs((test_data - pred_mean) / test_data)) * 100

                result = {
                    'product': product_name,
                    'mae': mae,
                    'rmse': rmse,
                    'mape': mape,
                    'test_actual_mean': test_data.mean(),
                    'test_pred_mean': pred_mean.mean()
                }

                print(f"\n{product_name} 模型评估结果:")
                print(f"测试集平均实际销量: {test_data.mean():.2f}")
                print(f"测试集平均预测销量: {pred_mean.mean():.2f}")
                print(f"MAE: {mae:.2f}")
                print(f"RMSE: {rmse:.2f}")
                print(f"MAPE: {mape:.2f}%")

                return result

            except Exception as e:
                print(f"评估失败: {str(e)}")
                return None
        else:
            print("数据不足，无法进行评估")
            return None

    def forecast_all_products(self, data, forecast_weeks=13):
        """为所有产品进行预测"""
        products = data['product'].unique()
        all_forecasts = []
        all_evaluations = []

        for product in products:
            try:
                # 预测
                forecast_df = self.train_and_forecast(data, product, forecast_weeks)
                all_forecasts.append(forecast_df)

                # 评估
                evaluation = self.evaluate_model(data, product)
                if evaluation:
                    all_evaluations.append(evaluation)

            except Exception as e:
                print(f"处理产品 {product} 时出错: {str(e)}")
                continue

        # 合并所有预测结果
        if all_forecasts:
            combined_forecast = pd.concat(all_forecasts, ignore_index=True)
            print(f"\n=== 总体预测结果 ===")
            print(f"成功预测产品数量: {len(self.forecasts)}")
            print(f"未来{forecast_weeks}周预测记录总数: {len(combined_forecast)}")

            return combined_forecast, all_evaluations
        else:
            print("没有成功完成任何预测")
            return None, None