@echo off
title 4G销售数据预测系统
echo.
echo ========================================
echo    4G销售数据预测系统 v2.1.0
echo ========================================
echo.
echo 正在启动预测系统，请稍候...
echo 首次启动可能需要较长时间，请耐心等待...
echo.

cd /d "%~dp0"

if exist "dist\4G销售数据预测系统.exe" (
    echo 找到可执行文件，正在启动...
    echo.
    start "" "dist\4G销售数据预测系统.exe"
    echo 程序已启动！
) else (
    echo 错误：未找到可执行文件！
    echo 请确保文件 4G销售数据预测系统.exe 存在于 dist 目录中
    echo.
    pause
)

echo.
echo 如需技术支持，请查看 打包说明.md 文件
echo.
pause
