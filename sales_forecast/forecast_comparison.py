import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

class ForecastComparison:
    def __init__(self):
        self.all_results = {}
        self.comparison_metrics = {}

    def run_all_forecasts(self, data, forecast_weeks=13):
        """运行所有三种预测方法"""
        print("=" * 60)
        print("开始电商销售预测对比分析")
        print("=" * 60)

        # 导入各个预测器
        from sales_forecasting import SalesForecaster
        from sarima_forecast import SARIMAForecaster
        from xgboost_forecast import XGBoostForecaster
        from prophet_forecast import ProphetForecaster

        # 初始化预测器
        forecaster = SalesForecaster()
        sarima_forecaster = SARIMAForecaster()
        xgboost_forecaster = XGBoostForecaster()
        prophet_forecaster = ProphetForecaster()

        # 加载和预处理数据
        print("正在加载数据...")
        data = forecaster.load_data()
        data = forecaster.preprocess_data()

        # 运行SARIMA预测
        print("\n" + "="*40)
        print("1. SARIMA 时间序列预测")
        print("="*40)
        sarima_forecast, sarima_eval = sarima_forecaster.forecast_all_products(data, forecast_weeks)
        self.all_results['SARIMA'] = {
            'forecast': sarima_forecast,
            'evaluation': sarima_eval
        }

        # 运行XGBoost预测
        print("\n" + "="*40)
        print("2. XGBoost 机器学习预测")
        print("="*40)
        xgb_forecast, xgb_eval = xgboost_forecaster.forecast_all_products(data, forecast_weeks)
        self.all_results['XGBoost'] = {
            'forecast': xgb_forecast,
            'evaluation': xgb_eval
        }

        # 运行Prophet预测
        print("\n" + "="*40)
        print("3. Prophet 商业预测")
        print("="*40)
        prophet_forecast, prophet_eval = prophet_forecaster.forecast_all_products(data, forecast_weeks)
        self.all_results['Prophet'] = {
            'forecast': prophet_forecast,
            'evaluation': prophet_eval
        }

        return self.all_results

    def compare_methods(self):
        """比较不同预测方法的性能"""
        print("\n" + "="*60)
        print("预测方法对比分析")
        print("="*60)

        comparison_data = []

        for method, results in self.all_results.items():
            if results['evaluation']:
                eval_df = pd.DataFrame(results['evaluation'])
                if not eval_df.empty:
                    avg_metrics = {
                        'method': method,
                        'avg_mae': eval_df['mae'].mean(),
                        'avg_rmse': eval_df['rmse'].mean(),
                        'avg_mape': eval_df['mape'].mean() if 'mape' in eval_df.columns else None,
                        'products_count': len(eval_df)
                    }
                    comparison_data.append(avg_metrics)

        if comparison_data:
            comparison_df = pd.DataFrame(comparison_data)
            self.comparison_metrics = comparison_df

            print("\n各方法平均性能指标:")
            print(comparison_df.to_string(index=False, float_format='%.2f'))

            # 找出最佳方法
            if not comparison_df.empty and 'avg_mae' in comparison_df.columns:
                best_mae = comparison_df.loc[comparison_df['avg_mae'].idxmin()]
                print(f"\n🏆 最佳预测方法 (MAE最低): {best_mae['method']}")
                print(f"   MAE: {best_mae['avg_mae']:.2f}")

            return comparison_df
        else:
            print("无法生成对比分析")
            return None

    def visualize_forecasts(self, data, product_name=None, save_plots=True):
        """可视化预测结果"""
        print("\n生成预测结果可视化...")

        # 选择要显示的产品
        if product_name is None:
            products = data['product'].unique()[:3]  # 显示前3个产品
        else:
            products = [product_name] if isinstance(product_name, str) else product_name

        for product in products:
            fig, axes = plt.subplots(2, 2, figsize=(16, 12))
            fig.suptitle(f'产品 {product} 销售预测对比', fontsize=16, fontweight='bold')

            # 获取历史数据
            product_data = data[data['product'] == product].copy()
            product_data = product_data.sort_values('date')
            weekly_data = product_data.groupby('date')['quantity'].sum().reset_index()

            # 绘制历史数据
            axes[0, 0].plot(weekly_data['date'], weekly_data['quantity'],
                          'b-', label='历史数据', linewidth=2, alpha=0.7)
            axes[0, 0].set_title('历史销售数据')
            axes[0, 0].set_xlabel('日期')
            axes[0, 0].set_ylabel('销售数量')
            axes[0, 0].legend()
            axes[0, 0].grid(True, alpha=0.3)

            # 绘制各方法的预测结果
            colors = ['red', 'green', 'orange']
            methods = ['SARIMA', 'XGBoost', 'Prophet']

            for i, (method, color) in enumerate(zip(methods, colors)):
                ax_idx = (i + 1) // 2, (i + 1) % 2
                ax = axes[ax_idx]

                # 绘制历史数据
                ax.plot(weekly_data['date'], weekly_data['quantity'],
                       'b-', label='历史数据', linewidth=1, alpha=0.5)

                # 绘制预测数据
                if (method in self.all_results and
                    self.all_results[method]['forecast'] is not None):

                    method_forecast = self.all_results[method]['forecast']
                    product_forecast = method_forecast[method_forecast['product'] == product]

                    if not product_forecast.empty:
                        ax.plot(product_forecast['date'], product_forecast['predicted_quantity'],
                               color=color, label=f'{method}预测', linewidth=2, marker='o')

                        # 如果有置信区间，绘制阴影区域
                        if 'lower_bound' in product_forecast.columns:
                            ax.fill_between(product_forecast['date'],
                                          product_forecast['lower_bound'],
                                          product_forecast['upper_bound'],
                                          color=color, alpha=0.2)

                ax.set_title(f'{method} 预测结果')
                ax.set_xlabel('日期')
                ax.set_ylabel('销售数量')
                ax.legend()
                ax.grid(True, alpha=0.3)

            plt.tight_layout()

            if save_plots:
                filename = f'forecast_comparison_{product}.png'
                plt.savefig(filename, dpi=300, bbox_inches='tight')
                print(f"图表已保存为: {filename}")

            plt.show()

    def plot_comparison_metrics(self, save_plot=True):
        """绘制性能指标对比图"""
        if self.comparison_metrics is None or self.comparison_metrics.empty:
            print("没有可用的性能指标数据")
            return

        fig, axes = plt.subplots(1, 3, figsize=(18, 6))
        fig.suptitle('预测方法性能对比', fontsize=16, fontweight='bold')

        metrics = ['avg_mae', 'avg_rmse', 'avg_mape']
        metric_names = ['平均绝对误差 (MAE)', '均方根误差 (RMSE)', '平均绝对百分比误差 (MAPE %)']

        for i, (metric, name) in enumerate(zip(metrics, metric_names)):
            ax = axes[i]

            if metric in self.comparison_metrics.columns:
                # 过滤掉MAPE中的None值
                if metric == 'avg_mape':
                    data_to_plot = self.comparison_metrics.dropna(subset=[metric])
                else:
                    data_to_plot = self.comparison_metrics

                if not data_to_plot.empty:
                    bars = ax.bar(data_to_plot['method'], data_to_plot[metric],
                                 color=['#1f77b4', '#ff7f0e', '#2ca02c'][:len(data_to_plot)])
                    ax.set_title(name)
                    ax.set_ylabel('数值')

                    # 添加数值标签
                    for bar in bars:
                        height = bar.get_height()
                        ax.text(bar.get_x() + bar.get_width()/2., height,
                               f'{height:.2f}', ha='center', va='bottom')

                ax.grid(True, alpha=0.3)

        plt.tight_layout()

        if save_plot:
            filename = 'method_performance_comparison.png'
            plt.savefig(filename, dpi=300, bbox_inches='tight')
            print(f"性能对比图已保存为: {filename}")

        plt.show()

    def generate_summary_report(self, output_file='forecast_summary_report.txt'):
        """生成预测总结报告"""
        print("\n生成预测总结报告...")

        report = []
        report.append("=" * 60)
        report.append("电商销售预测总结报告")
        report.append("=" * 60)
        report.append(f"报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")

        # 各方法预测结果摘要
        report.append("1. 预测方法摘要")
        report.append("-" * 30)
        for method, results in self.all_results.items():
            if results['forecast'] is not None:
                forecast_df = results['forecast']
                total_products = forecast_df['product'].nunique()
                total_records = len(forecast_df)
                avg_prediction = forecast_df['predicted_quantity'].mean()

                report.append(f"{method}:")
                report.append(f"  - 成功预测产品数: {total_products}")
                report.append(f"  - 预测记录总数: {total_records}")
                report.append(f"  - 平均预测销量: {avg_prediction:.2f}")

                if results['evaluation']:
                    eval_count = len(results['evaluation'])
                    report.append(f"  - 完成评估产品数: {eval_count}")
                report.append("")

        # 性能对比
        if self.comparison_metrics is not None and not self.comparison_metrics.empty:
            report.append("2. 性能对比分析")
            report.append("-" * 30)
            report.append(self.comparison_metrics.to_string(index=False, float_format='%.2f'))
            report.append("")

            # 推荐最佳方法
            if 'avg_mae' in self.comparison_metrics.columns:
                best_method = self.comparison_metrics.loc[self.comparison_metrics['avg_mae'].idxmin()]
                report.append("3. 推荐方案")
                report.append("-" * 30)
                report.append(f"推荐使用: {best_method['method']}")
                report.append(f"平均绝对误差: {best_method['avg_mae']:.2f}")
                report.append("")

        # 使用建议
        report.append("4. 使用建议")
        report.append("-" * 30)
        report.append("• SARIMA: 适合数据稳定、有明显季节性的产品")
        report.append("• XGBoost: 适合特征丰富、影响因素多样的产品")
        report.append("• Prophet: 适合有节假日效应、需要快速部署的业务场景")
        report.append("")
        report.append("• 建议根据具体产品特点选择合适的预测方法")
        report.append("• 可以考虑集成多种方法来提高预测准确性")
        report.append("")
        report.append("=" * 60)

        # 保存报告
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report))

        print(f"总结报告已保存为: {output_file}")

        # 打印报告内容
        print("\n预测总结报告:")
        print('\n'.join(report))

        return report

def main():
    """主函数：运行完整的预测对比分析"""
    print("开始电商销售预测对比分析...")

    # 创建比较器
    comparison = ForecastComparison()

    # 创建示例数据
    from sales_forecasting import SalesForecaster
    forecaster = SalesForecaster()
    data = forecaster.load_data()  # 创建示例数据

    # 运行所有预测方法
    results = comparison.run_all_forecasts(data)

    # 比较方法性能
    comparison_metrics = comparison.compare_methods()

    # 生成可视化
    comparison.visualize_forecasts(data)
    comparison.plot_comparison_metrics()

    # 生成总结报告
    comparison.generate_summary_report()

    print("\n预测对比分析完成！")
    return comparison

if __name__ == "__main__":
    comparison = main()