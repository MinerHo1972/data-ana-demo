@echo off
echo 正在安装折线面积堆积图所需依赖...
echo.

REM 检查Python是否已安装
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Python，请先安装Python
    pause
    exit /b 1
)

echo Python版本:
python --version
echo.

REM 安装必要的包
echo 安装numpy...
python -m pip install numpy

echo 安装pandas...
python -m pip install pandas

echo 安装matplotlib...
python -m pip install matplotlib

echo 安装seaborn...
python -m pip install seaborn

echo.
echo 所有依赖安装完成！
echo 现在可以运行: python stacked_area_line_chart.py
echo.
pause