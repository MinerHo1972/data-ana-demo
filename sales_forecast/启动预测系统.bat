@echo off
chcp 65001 >nul
title 4G销售数据预测系统

echo ==========================================
echo        4G销售数据预测系统
echo ==========================================
echo.

echo 正在启动预测系统...
echo.

REM 切换到脚本所在目录
cd /d "%~dp0"

REM 运行UI系统
python run_forecast_ui.py

if errorlevel 1 (
    echo.
    echo 启动失败！请检查：
    echo 1. Python是否正确安装
    echo 2. 依赖包是否安装完成
    echo 3. 运行: pip install pandas numpy matplotlib seaborn openpyxl
    echo.
    pause
)