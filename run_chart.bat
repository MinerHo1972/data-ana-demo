@echo off
echo 运行折线面积堆积图生成器
echo ========================
echo.

REM 检查Python是否存在
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Python，请先安装Python
    pause
    exit /b 1
)

echo 检查依赖包...
python -c "import numpy, pandas, matplotlib, seaborn" >nul 2>&1
if errorlevel 1 (
    echo 检测到缺少依赖包，正在自动安装...
    call install_requirements.bat
)

echo.
echo 启动折线面积堆积图生成器...
echo.

python stacked_area_line_chart.py

echo.
echo 程序执行完成
pause